"""Testlere özel yardımcılar.

`simple_windows`, #29 testleri için geçici ve basit bir pencere özetleyicisidir; yalnızca
M0'ın kullandığı özetleri üretir. Asıl pencereleme P4-06'dır (#35, Bahar). #35 merge
edilince bu yardımcı onunla değiştirilecek; üretim kodunda kullanılmaz.
"""

from __future__ import annotations

from collections.abc import Sequence

import pytest

from visual_attention.core.constants import SECOND_MS, WINDOW_MS, WINDOW_STEP_MS
from visual_attention.core.labels import Label
from visual_attention.core.records import FeatureRecord, WindowRecord
from visual_attention.core.status import FaceStatus
from visual_attention.labeling import second_references, window_train_label
from visual_attention.methods import SessionData
from visual_attention.synthetic import SyntheticSession


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def simple_windows(
    features: Sequence[FeatureRecord],
    session_id: str,
    duration_ms: int,
    label_intervals=None,
) -> tuple[WindowRecord, ...]:
    windows = []
    feats = list(features)
    j = 0
    for i, end in enumerate(range(WINDOW_MS, duration_ms + 1, WINDOW_STEP_MS)):
        start = end - WINDOW_MS
        while j < len(feats) and feats[j].timestamp_ms < start:
            j += 1
        k = j
        inside = []
        while k < len(feats) and feats[k].timestamp_ms < end:
            inside.append(feats[k])
            k += 1
        n = len(inside)
        face = sum(r.face_status is FaceStatus.VALID for r in inside) / n if n else None
        overlaps = [float(r.hand_phone_overlap) for r in inside if r.hand_phone_overlap is not None]
        windows.append(
            WindowRecord(
                session_id=session_id,
                window_index=i,
                start_ms=start,
                end_ms=end,
                feature_version="test-window",
                available_frame_count=n,
                is_valid=n > 0,
                invalid_reason=None if n else "NO_FRAMES",
                face_detected_ratio=face,
                aggregates={
                    "head_yaw_deg_mean": _mean(
                        [r.head_yaw_deg for r in inside if r.head_yaw_deg is not None]
                    ),
                    "phone_score_mean": _mean(
                        [r.phone_score for r in inside if r.phone_score is not None]
                    ),
                    "hand_phone_overlap_ratio": _mean(overlaps) if overlaps else 0.0,
                },
                train_label=(
                    window_train_label(label_intervals, start, end) if label_intervals else None
                ),
            )
        )
    return tuple(windows)


def session_data(s: SyntheticSession) -> SessionData:
    refs = second_references(s.label_intervals, s.duration_ms)
    assert len(refs) == s.duration_ms // SECOND_MS
    return SessionData(
        session_id=s.session_id,
        duration_ms=s.duration_ms,
        windows=simple_windows(s.features, s.session_id, s.duration_ms, s.label_intervals),
        reference=tuple(Label(r.label) for r in refs),
    )


@pytest.fixture(scope="session")
def make_session_data():
    return session_data
