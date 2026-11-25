"""Model tarafı kayıtları: öznitelik, pencere, tahmin ve saniye kararı.

Karşılık geldiği belge: docs/data-schema.md v0.2 (§3.3, §3.4, §3.6).
Tüm zaman aralıkları oturum video zamanında, milisaniye ve yarı açık [start, end).
Eksik ölçüm `None` ile gösterilir; 0 gerçek bir sayısal ölçümdür.

`FrameRecord` burada değil, `capture` modülündedir (P4-01).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from visual_attention.core.constants import SECOND_MS
from visual_attention.core.labels import MODEL_OUTPUTS, Label
from visual_attention.core.status import FaceStatus, HandStatus, PhoneStatus, TrainLabel

# ---------------------------------------------------------------------------
# Ortak doğrulama yardımcıları
# ---------------------------------------------------------------------------


def check_interval(start_ms: int, end_ms: int, what: str = "aralık") -> None:
    """Yarı açık [start, end) aralığını doğrular."""
    if start_ms < 0 or end_ms <= start_ms:
        raise ValueError(f"Geçersiz {what}: [{start_ms}, {end_ms})")


def check_unit(value: float | None, name: str) -> None:
    """Değer None ya da [0, 1] aralığında olmalı."""
    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} [0, 1] aralığında olmalı: {value}")


def coerce_enum(obj: object, name: str, enum_type: type) -> None:
    """Dize olarak verilen durum değerini enum'a çevirir (dondurulmuş kayıtlar için)."""
    value = getattr(obj, name)
    if value is not None and not isinstance(value, enum_type):
        object.__setattr__(obj, name, enum_type(value))


# ---------------------------------------------------------------------------
# Öznitelik (§3.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ValidityFlags:
    """Alan bazlı geçerlilik. Bileşen durumu için esas kaynak *_status alanlarıdır."""

    head_pose_valid: bool = False
    eye_features_valid: bool = False
    hand_features_valid: bool = False
    phone_features_valid: bool = False


_UNIT_FEATURE_FIELDS = (
    "left_wrist_x",
    "left_wrist_y",
    "right_wrist_x",
    "right_wrist_y",
    "phone_score",
    "phone_box_x",
    "phone_box_y",
    "phone_box_w",
    "phone_box_h",
)


@dataclass(frozen=True, slots=True)
class FeatureRecord:
    """Bir karenin türetilmiş öznitelikleri. Ham kare ve tam landmark koordinatları tutulmaz."""

    session_id: str
    frame_index: int
    timestamp_ms: int
    feature_version: str
    face_status: FaceStatus
    hand_status: HandStatus
    phone_status: PhoneStatus
    validity_flags: ValidityFlags = field(default_factory=ValidityFlags)
    # Yüz ve baş pozu (derece; pozitif yön tanımı P4-02'de belgelenir)
    head_yaw_deg: float | None = None
    head_pitch_deg: float | None = None
    head_roll_deg: float | None = None
    eye_aspect_ratio_left: float | None = None
    eye_aspect_ratio_right: float | None = None
    # El ve bilek (normalize [0, 1])
    hand_count: int | None = None
    left_wrist_x: float | None = None
    left_wrist_y: float | None = None
    right_wrist_x: float | None = None
    right_wrist_y: float | None = None
    hand_phone_distance_norm: float | None = None
    hand_phone_overlap: bool | None = None
    # Telefon (normalize [0, 1])
    phone_score: float | None = None
    phone_box_x: float | None = None
    phone_box_y: float | None = None
    phone_box_w: float | None = None
    phone_box_h: float | None = None

    def __post_init__(self) -> None:
        coerce_enum(self, "face_status", FaceStatus)
        coerce_enum(self, "hand_status", HandStatus)
        coerce_enum(self, "phone_status", PhoneStatus)
        if self.frame_index < 0:
            raise ValueError("frame_index negatif olamaz")
        if self.timestamp_ms < 0:
            raise ValueError("timestamp_ms negatif olamaz")
        if not self.feature_version:
            raise ValueError("feature_version boş olamaz")
        if self.hand_count is not None and not 0 <= self.hand_count <= 2:
            raise ValueError(f"hand_count 0–2 olmalı: {self.hand_count}")
        if self.hand_phone_distance_norm is not None and self.hand_phone_distance_norm < 0:
            raise ValueError("hand_phone_distance_norm negatif olamaz")
        for name in _UNIT_FEATURE_FIELDS:
            check_unit(getattr(self, name), name)


# ---------------------------------------------------------------------------
# Pencere (§3.4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WindowRecord:
    """Bir 2 sn pencerenin özeti.

    `aggregates` anahtarları: sayısal alanlar için `<alan>_mean`, `<alan>_std`,
    `<alan>_delta`; boolean alanlar için `<alan>_ratio`. Geçerli değer yoksa `None`.
    """

    session_id: str
    window_index: int
    start_ms: int
    end_ms: int
    feature_version: str
    available_frame_count: int
    is_valid: bool
    aggregates: Mapping[str, float | None] = field(default_factory=dict)
    face_detected_ratio: float | None = None
    coverage_ratio: float | None = None
    invalid_reason: str | None = None
    train_label: TrainLabel | None = None

    def __post_init__(self) -> None:
        coerce_enum(self, "train_label", TrainLabel)
        check_interval(self.start_ms, self.end_ms, "pencere")
        if self.window_index < 0:
            raise ValueError("window_index negatif olamaz")
        if self.available_frame_count < 0:
            raise ValueError("available_frame_count negatif olamaz")
        if not self.feature_version:
            raise ValueError("feature_version boş olamaz")
        check_unit(self.face_detected_ratio, "face_detected_ratio")
        check_unit(self.coverage_ratio, "coverage_ratio")
        if not self.is_valid and not self.invalid_reason:
            raise ValueError("Geçersiz pencerede invalid_reason yazılmalı")


# ---------------------------------------------------------------------------
# Tahmin ve saniye kararı (§3.6)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Prediction:
    """Bir 2 sn pencere için model tahmini (M0, M1 veya MAJORITY).

    BELIRSIZ gerekçeleri (`reason`): LOW_FACE_RATIO, RULE_CONFLICT (M0), LOW_CONFIDENCE (M1).
    """

    session_id: str
    window_index: int
    start_ms: int
    end_ms: int
    model_id: str
    label: Label
    score: float | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        check_interval(self.start_ms, self.end_ms, "pencere aralığı")
        if self.window_index < 0:
            raise ValueError("window_index negatif olamaz")
        coerce_enum(self, "label", Label)
        if self.label not in MODEL_OUTPUTS:
            raise ValueError(
                f"Model tahmini {self.label} olamaz; GECIS yalnızca insan referansındadır"
            )


@dataclass(frozen=True, slots=True)
class SecondDecision:
    """Tekil 1 sn dilim için nihai karar. (session_id, second_start_ms) benzersizdir."""

    session_id: str
    second_start_ms: int
    label: Label
    resolution_policy_version: str
    source_window_start_ms: int | None = None
    source_window_end_ms: int | None = None
    reason: str = ""

    @property
    def second_index(self) -> int:
        return self.second_start_ms // SECOND_MS
