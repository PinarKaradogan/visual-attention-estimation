"""Pencereleme: FeatureRecord akışından 2 sn / 1 sn kaydırmalı WindowRecord'lar (P4-06).

Kaynak: öneri v5 §2.4, data-schema §3.4, labeling-protocol §5.3.

- Pencereler `[t, t + 2000)`, `t = 0, 1000, 2000, ...`; yalnız oturuma tamamen sığan
  pencereler üretilir (TimelineResolver oturumu aşan pencereyi reddeder).
- Kare, zaman damgasına göre yarı açık aralık kuralıyla pencerelere düşer: tam 2000 ms'deki
  kare `[0, 2000)`'e değil, `[1000, 3000)` ve `[2000, 4000)`'e girer.
- `aggregates`: her sayısal alan için `_mean`, `_std` (popülasyon standart sapması) ve
  `_delta` (son geçerli değer − ilk geçerli değer); boolean alan için `_ratio`; ayrıca
  `phone_visible_ratio` ve `hand_detected_ratio` (değerlendirilmeyen karede `None`).
  Geçerli değer yoksa `None`.
- `face_detected_ratio`: penceredeki karelerden `face_status = VALID` olanların oranı.
- `coverage_ratio`: kare sayısı / (2 sn × kaynak FPS), en fazla 1; FPS bilinmiyorsa `None`.
- Boş pencere geçersizdir (`EMPTY`). Asgari kare/kapsama eşiği kilitli kararlarda olmadığı
  için uygulanmaz; kapsama raporlanır.
- İnsan etiketi verilirse `train_label` protokol §5.3 kuralıyla (`window_train_label`)
  doldurulur. Pencereleme hiçbir zaman sınıf üretmez; eksik kanıt MATERYAL sayılmaz.
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Iterable, Sequence

from visual_attention.core import (
    WINDOW_MS,
    WINDOW_STEP_MS,
    FaceStatus,
    FeatureRecord,
    HandStatus,
    HumanLabelInterval,
    PhoneStatus,
    WindowRecord,
)
from visual_attention.labeling import window_train_label

NUMERIC_FIELDS = (
    "head_yaw_deg",
    "head_pitch_deg",
    "head_roll_deg",
    "eye_aspect_ratio_left",
    "eye_aspect_ratio_right",
    "hand_count",
    "left_wrist_x",
    "left_wrist_y",
    "right_wrist_x",
    "right_wrist_y",
    "hand_phone_distance_norm",
    "phone_score",
    "phone_box_x",
    "phone_box_y",
    "phone_box_w",
    "phone_box_h",
)
BOOLEAN_FIELDS = ("hand_phone_overlap",)
EMPTY = "EMPTY"


def _summary(values: Sequence[float]) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    mean = sum(values) / len(values)
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    return mean, std, values[-1] - values[0]


def _status_ratio(records: Sequence[FeatureRecord], field: str, positive, not_evaluated):
    evaluated = [getattr(r, field) for r in records if getattr(r, field) is not not_evaluated]
    if not evaluated:
        return None
    return sum(s is positive for s in evaluated) / len(evaluated)


def aggregate(records: Sequence[FeatureRecord]) -> dict[str, float | None]:
    """Zaman sırasındaki kayıtlardan pencere özetleri (data-schema §3.4)."""
    out: dict[str, float | None] = {}
    for name in NUMERIC_FIELDS:
        values = [float(v) for r in records if (v := getattr(r, name)) is not None]
        out[f"{name}_mean"], out[f"{name}_std"], out[f"{name}_delta"] = _summary(values)
    for name in BOOLEAN_FIELDS:
        values = [v for r in records if (v := getattr(r, name)) is not None]
        out[f"{name}_ratio"] = sum(values) / len(values) if values else None
    out["phone_visible_ratio"] = _status_ratio(
        records, "phone_status", PhoneStatus.VISIBLE, PhoneStatus.NOT_EVALUATED
    )
    out["hand_detected_ratio"] = _status_ratio(
        records, "hand_status", HandStatus.VALID, HandStatus.NOT_EVALUATED
    )
    return out


def build_windows(
    records: Iterable[FeatureRecord],
    session_duration_ms: int,
    *,
    nominal_fps: float | None = None,
    label_intervals: Sequence[HumanLabelInterval] | None = None,
    window_ms: int = WINDOW_MS,
    step_ms: int = WINDOW_STEP_MS,
) -> list[WindowRecord]:
    """Bir oturumun kayıtlarını pencerelere böler.

    Args:
        records: Tek oturuma ve tek `feature_version`'a ait FeatureRecord'lar (sırası önemsiz).
        session_duration_ms: Oturumun video zamanındaki süresi.
        nominal_fps: Kaynak kare hızı; `coverage_ratio` için (bilinmiyorsa None).
        label_intervals: İnsan etiket aralıkları; verilirse `train_label` doldurulur.
        window_ms, step_ms: Duyarlılık analizi için (ör. 3 sn pencere); varsayılan 2000/1000.
    """
    if session_duration_ms <= 0:
        raise ValueError("session_duration_ms pozitif olmalı")
    if window_ms <= 0 or step_ms <= 0:
        raise ValueError("window_ms ve step_ms pozitif olmalı")
    rows = sorted(records, key=lambda r: r.timestamp_ms)
    if not rows:
        raise ValueError("Pencerelenecek kayıt yok")
    sessions = {r.session_id for r in rows}
    versions = {r.feature_version for r in rows}
    if len(sessions) != 1 or len(versions) != 1:
        raise ValueError("Kayıtlar tek oturum ve tek feature_version'a ait olmalı")
    session_id, feature_version = sessions.pop(), versions.pop()
    if rows[-1].timestamp_ms >= session_duration_ms:
        raise ValueError("Kare zamanı oturum süresini aşıyor")

    times = [r.timestamp_ms for r in rows]
    expected = window_ms / 1000 * nominal_fps if nominal_fps and nominal_fps > 0 else None
    windows: list[WindowRecord] = []
    for index, start in enumerate(range(0, session_duration_ms - window_ms + 1, step_ms)):
        end = start + window_ms
        inside = rows[bisect.bisect_left(times, start) : bisect.bisect_left(times, end)]
        n = len(inside)
        face_ratio = sum(r.face_status is FaceStatus.VALID for r in inside) / n if n else None
        windows.append(
            WindowRecord(
                session_id=session_id,
                window_index=index,
                start_ms=start,
                end_ms=end,
                feature_version=feature_version,
                available_frame_count=n,
                is_valid=n > 0,
                invalid_reason=None if n else EMPTY,
                aggregates=aggregate(inside),
                face_detected_ratio=face_ratio,
                coverage_ratio=min(1.0, n / expected) if expected else None,
                train_label=window_train_label(label_intervals, start, end)
                if label_intervals is not None
                else None,
            )
        )
    return windows
