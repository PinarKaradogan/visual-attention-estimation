"""Pencereleme testleri (yalnız sentetik FeatureRecord'lar)."""

import math

import pytest

from visual_attention.core import (
    FaceStatus,
    FeatureRecord,
    HandStatus,
    HumanLabelInterval,
    PhoneStatus,
    TrainLabel,
    WindowRecord,
)
from visual_attention.windowing import EMPTY, build_windows


def rec(ts, *, face=FaceStatus.VALID, pitch=None, phone=PhoneStatus.NOT_VISIBLE, score=0.0,
        hand=HandStatus.NOT_DETECTED, overlap=None, session="S1", version="v1"):  # fmt: skip
    return FeatureRecord(
        session_id=session,
        frame_index=ts // 100,
        timestamp_ms=ts,
        feature_version=version,
        face_status=face,
        hand_status=hand,
        phone_status=phone,
        head_pitch_deg=pitch,
        phone_score=score,
        hand_phone_overlap=overlap,
    )


def every(step_ms, until_ms, **kw):
    return [rec(t, **kw) for t in range(0, until_ms, step_ms)]


def interval(start, end, label):
    return HumanLabelInterval("S1", "A1", "r1", start, end, label, "lbl-0.1")


# --- Pencere ızgarası ve sınırlar ----------------------------------------------------


def test_window_grid_two_seconds_with_one_second_step():
    windows = build_windows(every(100, 5000), 5000)
    assert [(w.start_ms, w.end_ms) for w in windows] == [
        (0, 2000),
        (1000, 3000),
        (2000, 4000),
        (3000, 5000),
    ]
    assert [w.window_index for w in windows] == [0, 1, 2, 3]
    assert all(w.available_frame_count == 20 for w in windows)


def test_only_complete_windows_are_built():
    windows = build_windows(every(100, 4500), 4500)
    assert windows[-1].end_ms == 4000


def test_frame_on_boundary_goes_to_later_windows():
    records = [rec(1999), rec(2000)]
    w = {x.start_ms: x for x in build_windows(records, 4000)}
    assert w[0].available_frame_count == 1  # yalnız 1999
    assert w[1000].available_frame_count == 2
    assert w[2000].available_frame_count == 1  # yalnız 2000


def test_empty_window_is_invalid_and_has_no_ratios():
    empty = build_windows([rec(100)], 6000)[3]  # [3000, 5000)
    assert not empty.is_valid and empty.invalid_reason == EMPTY
    assert empty.face_detected_ratio is None
    assert empty.aggregates["head_pitch_deg_mean"] is None


def test_irregular_and_unsorted_timestamps():
    records = [rec(1900), rec(30), rec(1250), rec(990), rec(2100)]
    w = build_windows(records, 3000)
    assert [x.available_frame_count for x in w] == [4, 3]


def test_input_validation():
    with pytest.raises(ValueError):
        build_windows([], 2000)
    with pytest.raises(ValueError):
        build_windows([rec(0, session="A"), rec(100, session="B")], 2000)
    with pytest.raises(ValueError):
        build_windows([rec(0, version="a"), rec(100, version="b")], 2000)
    with pytest.raises(ValueError):
        build_windows([rec(2500)], 2000)


# --- Özetler ------------------------------------------------------------------------


def test_face_detected_ratio():
    records = [rec(t, face=FaceStatus.VALID if t < 1500 else FaceStatus.NOT_DETECTED)
               for t in range(0, 2000, 100)]  # fmt: skip
    w = build_windows(records, 2000)[0]
    assert w.face_detected_ratio == pytest.approx(15 / 20)


def test_mean_std_delta_skip_missing_values():
    pitches = [10.0, None, 20.0, 30.0]
    records = [rec(t, pitch=p) for t, p in zip((0, 500, 1000, 1500), pitches, strict=True)]
    agg = build_windows(records, 2000)[0].aggregates
    assert agg["head_pitch_deg_mean"] == pytest.approx(20.0)
    assert agg["head_pitch_deg_std"] == pytest.approx(math.sqrt(200 / 3))
    assert agg["head_pitch_deg_delta"] == pytest.approx(20.0)  # son − ilk geçerli


def test_boolean_and_status_ratios():
    records = [
        rec(0, phone=PhoneStatus.VISIBLE, score=0.8, hand=HandStatus.VALID, overlap=True),
        rec(500, phone=PhoneStatus.VISIBLE, score=0.6, hand=HandStatus.VALID, overlap=False),
        rec(1000, phone=PhoneStatus.NOT_VISIBLE, hand=HandStatus.NOT_DETECTED),
        rec(1500, phone=PhoneStatus.NOT_EVALUATED, hand=HandStatus.NOT_EVALUATED, score=None),
    ]
    agg = build_windows(records, 2000)[0].aggregates
    assert agg["hand_phone_overlap_ratio"] == pytest.approx(0.5)
    assert agg["phone_visible_ratio"] == pytest.approx(2 / 3)  # değerlendirilmeyen hariç
    assert agg["hand_detected_ratio"] == pytest.approx(2 / 3)
    assert agg["phone_score_mean"] == pytest.approx((0.8 + 0.6 + 0.0) / 3)


def test_coverage_ratio_from_nominal_fps():
    w = build_windows(every(100, 2000), 2000, nominal_fps=20)[0]  # 20 kare / 40 beklenen
    assert w.coverage_ratio == pytest.approx(0.5)
    assert build_windows(every(100, 2000), 2000, nominal_fps=5)[0].coverage_ratio == 1.0
    assert build_windows(every(100, 2000), 2000)[0].coverage_ratio is None


def test_sensitivity_window_length():
    windows = build_windows(every(100, 5000), 5000, window_ms=3000)
    assert [(w.start_ms, w.end_ms) for w in windows] == [(0, 3000), (1000, 4000), (2000, 5000)]


# --- Eğitim hedefi ------------------------------------------------------------------


def test_train_label_from_human_intervals():
    labels = [
        interval(0, 1400, "MATERYAL"),
        interval(1400, 3000, "TELEFON"),
        interval(3000, 4000, "BELIRSIZ"),
    ]
    w = build_windows(every(100, 4000), 4000, label_intervals=labels)
    assert [x.train_label for x in w] == [
        TrainLabel.MATERYAL,  # [0,2000): 1400 ms MATERYAL
        TrainLabel.TELEFON,  # [1000,3000): 1600 ms TELEFON
        TrainLabel.UNUSED,  # [2000,4000): 1000 ms BELIRSIZ = yarı
    ]


def test_no_labels_means_no_train_label():
    assert all(w.train_label is None for w in build_windows(every(100, 3000), 3000))


def test_missing_evidence_is_never_materyal():
    # Hiç etiket yok: pencere eğitimde kullanılmaz, MATERYAL sayılmaz.
    w = build_windows(every(100, 2000), 2000, label_intervals=[])[0]
    assert w.train_label is TrainLabel.UNUSED


# --- WindowRecord kuralları (#39 notları) -------------------------------------------


def test_window_record_aggregates_are_read_only_and_hashable():
    w = build_windows(every(100, 2000), 2000)[0]
    with pytest.raises(TypeError):
        w.aggregates["head_pitch_deg_mean"] = 1.0
    hash(w)


def test_valid_empty_window_is_rejected():
    with pytest.raises(ValueError):
        WindowRecord("S1", 0, 0, 2000, "v1", available_frame_count=0, is_valid=True)
