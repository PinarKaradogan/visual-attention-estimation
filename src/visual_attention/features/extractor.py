"""Öznitelik birleştirici: yüz, telefon ve el bileşenlerinden tek FeatureRecord (P4-05).

- Yüz bileşeni zorunludur. `FaceStatus`'ta "değerlendirilmedi" değeri olmadığı için yüz
  kapatılırsa `face_status` yanlış yazılmış olurdu.
- Telefon ve el bileşenleri kapatılabilir; kapalı bileşenin durumu NOT_EVALUATED, alanları
  `None` olur.
- El bileşeni aynı karenin telefon çıktısını alır (uzanma ve tutma göstergeleri için).
- `OK` olmayan kareler işlenmez; bir bileşen kareyi atlarsa (ör. zaman ilerlemediyse) kare
  için kayıt üretilmez, böylece kayıtlar bileşenler arasında eksik kalmaz.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from visual_attention.capture import FrameRecord, SourceStatus
from visual_attention.core import FeatureRecord, HandStatus, PhoneStatus, ValidityFlags
from visual_attention.features.face import FACE_FEATURE_VERSION, FaceFeatureExtractor
from visual_attention.features.hand import HAND_FEATURE_VERSION, HandFeatureExtractor
from visual_attention.features.phone import PHONE_FEATURE_VERSION, PhoneFeatureExtractor

EXTRACTOR_VERSION = "feat-0.1.0"


def build_feature_version(phone_enabled: bool, hand_enabled: bool) -> str:
    """Birleştirici ve açık bileşen sürümlerinden `feature_version` (kapalı bileşen "off")."""
    parts = [
        EXTRACTOR_VERSION,
        FACE_FEATURE_VERSION,
        PHONE_FEATURE_VERSION if phone_enabled else "phone-off",
        HAND_FEATURE_VERSION if hand_enabled else "hand-off",
    ]
    return "+".join(parts)


class FeatureExtractor:
    """Üç bileşeni kare kare çalıştırır.

    Kullanım:

        with FeatureExtractor.from_models("models") as extractor:
            for record in extractor.process(source):
                ...
    """

    def __init__(self, face: Any, phone: Any | None = None, hand: Any | None = None) -> None:
        """
        Args:
            face: `extract(frame)` sağlayan yüz bileşeni (zorunlu).
            phone: `extract(frame)` sağlayan telefon bileşeni; None ise kapalı.
            hand: `extract(frame, phone_features)` sağlayan el bileşeni; None ise kapalı.
        """
        if face is None:
            raise ValueError("Yüz bileşeni zorunlu")
        self.face = face
        self.phone = phone
        self.hand = hand
        self.feature_version = build_feature_version(phone is not None, hand is not None)

    @classmethod
    def from_models(
        cls,
        models_dir: str | Path = "models",
        *,
        phone: bool = True,
        hand: bool = True,
        mirrored: bool = False,
    ) -> FeatureExtractor:
        root = Path(models_dir)
        return cls(
            face=FaceFeatureExtractor(root / "face_landmarker.task"),
            phone=PhoneFeatureExtractor(root / "efficientdet_lite0.tflite") if phone else None,
            hand=HandFeatureExtractor(root / "hand_landmarker.task", mirrored=mirrored)
            if hand
            else None,
        )

    def _components(self) -> list[Any]:
        return [c for c in (self.face, self.phone, self.hand) if c is not None]

    def open(self) -> None:
        for component in self._components():
            if hasattr(component, "open"):
                component.open()

    def close(self) -> None:
        for component in self._components():
            if hasattr(component, "close"):
                component.close()

    def __enter__(self) -> FeatureExtractor:
        self.open()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def extract(self, frame: FrameRecord) -> FeatureRecord | None:
        """Bir karenin birleşik öznitelikleri; işlenmeyen karede None."""
        if frame.source_status is not SourceStatus.OK or frame.frame is None:
            return None
        face = self.face.extract(frame)
        if face is None:
            return None
        phone = None
        if self.phone is not None:
            phone = self.phone.extract(frame)
            if phone is None:
                return None
        hand = None
        if self.hand is not None:
            hand = self.hand.extract(frame, phone)
            if hand is None:
                return None

        fields: dict[str, Any] = {
            "head_yaw_deg": face.head_yaw_deg,
            "head_pitch_deg": face.head_pitch_deg,
            "head_roll_deg": face.head_roll_deg,
            "eye_aspect_ratio_left": face.eye_aspect_ratio_left,
            "eye_aspect_ratio_right": face.eye_aspect_ratio_right,
        }
        fields.update(phone.as_fields() if phone else {"phone_status": PhoneStatus.NOT_EVALUATED})
        fields.update(hand.as_fields() if hand else {"hand_status": HandStatus.NOT_EVALUATED})
        return FeatureRecord(
            session_id=frame.session_id,
            frame_index=frame.frame_index,
            timestamp_ms=frame.timestamp_ms,
            feature_version=self.feature_version,
            face_status=face.face_status,
            validity_flags=ValidityFlags(
                head_pose_valid=face.head_pose_valid,
                eye_features_valid=face.eye_features_valid,
                hand_features_valid=hand is not None,
                phone_features_valid=phone is not None,
            ),
            **fields,
        )

    def process(self, frames: Iterable[FrameRecord]) -> Iterator[FeatureRecord]:
        """Kare akışını işler; işlenmeyen kareleri atlar."""
        for frame in frames:
            record = self.extract(frame)
            if record is not None:
                yield record
