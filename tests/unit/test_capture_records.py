"""FrameRecord ve FrameTimingTracker testleri (yalnız sentetik değerler)."""

import numpy as np
import pytest

from visual_attention.capture import FrameRecord, FrameTimingTracker, SourceStatus


def test_frame_record_defaults_and_status_coercion():
    rec = FrameRecord("S1", 0, 0, np.zeros((2, 2, 3), np.uint8), "READ_ERROR")
    assert rec.source_status is SourceStatus.READ_ERROR
    assert FrameRecord("S1", 1, 40, None).source_status is SourceStatus.OK


@pytest.mark.parametrize(("index", "ts"), [(-1, 0), (0, -1)])
def test_frame_record_rejects_negative_values(index, ts):
    with pytest.raises(ValueError):
        FrameRecord("S1", index, ts, None)


def test_frame_record_repr_hides_frame():
    rec = FrameRecord("S1", 0, 0, np.zeros((480, 640, 3), np.uint8))
    assert "frame=" not in repr(rec)


def test_tracker_regular_stream_has_no_drops():
    t = FrameTimingTracker(nominal_fps=10)
    assert all(t.add(i * 100) for i in range(11))
    assert t.dropped == 0
    assert t.measured_fps == pytest.approx(10.0)


def test_tracker_estimates_dropped_frames_from_gaps():
    t = FrameTimingTracker(nominal_fps=10)
    for ts in [0, 100, 400, 500, 700]:  # 400'de 2, 700'de 1 kare eksik
        t.add(ts)
    assert t.dropped == 3


def test_tracker_small_jitter_is_not_a_drop():
    t = FrameTimingTracker(nominal_fps=10)
    for ts in [0, 100, 249, 349]:  # 149 ms < 1,5 × 100 ms
        t.add(ts)
    assert t.dropped == 0


def test_tracker_rejects_non_increasing_timestamps():
    t = FrameTimingTracker(nominal_fps=10)
    assert t.add(100)
    assert not t.add(100)
    assert not t.add(50)
    assert t.add(200)
    assert t.measured_fps == pytest.approx(10.0)


def test_tracker_without_nominal_fps_cannot_estimate_drops():
    t = FrameTimingTracker(nominal_fps=None)
    t.add(0)
    t.add(500)
    assert t.dropped is None
    assert t.measured_fps == pytest.approx(2.0)
    assert FrameTimingTracker(10).measured_fps is None
