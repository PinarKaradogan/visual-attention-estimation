"""LiveVideoSource ve LatestFrameBuffer testleri.

Gerçek kamera kullanılmaz: kamera yerine sahte bir yakalama nesnesi ve sahte saat verilir.
"""

import itertools
import threading
import time

import cv2
import numpy as np
import pytest

from visual_attention.capture import LatestFrameBuffer, LiveVideoSource, SourceMode


class FakeCapture:
    """`n_frames` kare verir, sonra hep okuma hatası döner."""

    def __init__(self, n_frames: int, fps: float = 10.0, opened: bool = True):
        self._remaining = n_frames
        self._fps = fps
        self._opened = opened
        self.released = False
        self.props: dict[int, float] = {}

    def isOpened(self):  # noqa: N802 - OpenCV arayüzü
        return self._opened

    def set(self, prop, value):
        self.props[prop] = value
        return True

    def get(self, prop):
        return {
            cv2.CAP_PROP_FPS: self._fps,
            cv2.CAP_PROP_FRAME_WIDTH: self.props.get(cv2.CAP_PROP_FRAME_WIDTH, 64),
            cv2.CAP_PROP_FRAME_HEIGHT: self.props.get(cv2.CAP_PROP_FRAME_HEIGHT, 48),
        }.get(prop, 0.0)

    def read(self):
        if self._remaining <= 0:
            return False, None
        self._remaining -= 1
        return True, np.zeros((48, 64, 3), np.uint8)

    def release(self):
        self.released = True


def stepping_clock(step_s: float = 0.1):
    """Her çağrıda `step_s` ilerleyen, iş parçacığı güvenli sahte saat."""
    counter = itertools.count()
    lock = threading.Lock()

    def clock():
        with lock:
            return next(counter) * step_s

    return clock


# --- LatestFrameBuffer ---------------------------------------------------------------


def test_buffer_keeps_newest_and_counts_skipped():
    buf = LatestFrameBuffer(maxlen=1)
    for i in range(3):
        buf.put(i)
    assert buf.skipped == 2
    assert buf.get(timeout=0) == 2
    assert buf.get(timeout=0) is None


def test_buffer_with_larger_capacity_is_fifo():
    buf = LatestFrameBuffer(maxlen=2)
    for i in range(3):
        buf.put(i)
    assert buf.skipped == 1
    assert [buf.get(0), buf.get(0)] == [1, 2]


def test_buffer_get_waits_for_producer():
    buf = LatestFrameBuffer()
    threading.Timer(0.05, buf.put, args=("kare",)).start()
    assert buf.get(timeout=2.0) == "kare"


def test_buffer_rejects_zero_capacity():
    with pytest.raises(ValueError):
        LatestFrameBuffer(maxlen=0)


# --- LiveVideoSource -----------------------------------------------------------------


def make_source(capture, **kwargs):
    return LiveVideoSource(
        0,
        "S1",
        capture_factory=lambda _index: capture,
        clock=stepping_clock(),
        max_consecutive_failures=3,
        **kwargs,
    )


def test_live_source_timestamps_and_indices_are_monotonic():
    capture = FakeCapture(n_frames=20)
    with make_source(capture, buffer_size=32) as source:
        records = list(source)

    assert [r.frame_index for r in records] == list(range(20))
    # Sahte saat: t0 = 0 sn, her okuma 0,1 sn ilerler.
    assert [r.timestamp_ms for r in records] == [(i + 1) * 100 for i in range(20)]
    stats = source.stats
    assert stats.source_mode is SourceMode.LIVE
    assert stats.source_id == "camera0"
    assert stats.frames_read == 20
    assert stats.skipped_by_pipeline == 0
    assert stats.dropped_by_source == 0
    assert stats.measured_fps == pytest.approx(10.0)
    assert stats.read_errors == 3
    assert capture.released


def test_live_source_slow_consumer_skips_old_frames():
    capture = FakeCapture(n_frames=50)
    received = []
    with make_source(capture, buffer_size=1) as source:
        for record in source:
            received.append(record)
            time.sleep(0.2)  # işleme yetişemiyor

    indices = [r.frame_index for r in received]
    assert indices == sorted(set(indices))
    assert indices[-1] == 49  # en yeni kare her zaman işlenir
    stats = source.stats
    assert stats.skipped_by_pipeline > 0
    assert len(received) + stats.skipped_by_pipeline == stats.frames_read == 50


def test_live_source_applies_requested_resolution():
    capture = FakeCapture(n_frames=1)
    with make_source(capture, width=1280, height=720) as source:
        list(source)
    assert (source.stats.width_px, source.stats.height_px) == (1280, 720)


def test_live_source_camera_not_opened_raises():
    capture = FakeCapture(n_frames=0, opened=False)
    with pytest.raises(OSError):
        make_source(capture).open()
    assert capture.released
