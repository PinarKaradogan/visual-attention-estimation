"""Testler için sahte video kaynağı (SYNTHETIC modu).

Verilen zaman damgalarıyla siyah kareler üretir; kare kaybı (zaman ve sıra boşlukları),
okuma hatası ve bozuk zaman damgası senaryoları kurulabilir. Gerçek kişi görüntüsü içermez.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import numpy as np

from visual_attention.capture.base import VideoSource
from visual_attention.capture.records import (
    CaptureStats,
    FrameRecord,
    FrameTimingTracker,
    SourceMode,
    SourceStatus,
)


class FakeVideoSource(VideoSource):
    def __init__(
        self,
        session_id: str,
        timestamps_ms: Sequence[int],
        *,
        frame_indices: Sequence[int] | None = None,
        read_error_indices: Sequence[int] = (),
        nominal_fps: float | None = None,
        frame_shape: tuple[int, int, int] = (48, 64, 3),
    ) -> None:
        """
        Args:
            timestamps_ms: Her karenin video zamanı; testte bozuk sıra da verilebilir.
            frame_indices: Kaynak kare sırası; verilmezse 0, 1, 2, ...
            read_error_indices: Bu konumlardaki kareler `READ_ERROR` ve `frame=None` olur.
            nominal_fps: Kare kaybı kestirimi için hedeflenen FPS.
        """
        super().__init__(session_id)
        self._timestamps = list(timestamps_ms)
        self._indices = list(frame_indices) if frame_indices is not None else None
        if self._indices is not None and len(self._indices) != len(self._timestamps):
            raise ValueError("frame_indices ve timestamps_ms aynı uzunlukta olmalı")
        self._errors = set(read_error_indices)
        self._frame = np.zeros(frame_shape, dtype=np.uint8)
        self._frame.flags.writeable = False
        self._stats = CaptureStats(
            source_mode=SourceMode.SYNTHETIC,
            source_id="fake",
            width_px=frame_shape[1],
            height_px=frame_shape[0],
            nominal_fps=nominal_fps,
        )

    @classmethod
    def regular(cls, session_id: str, n_frames: int, fps: float = 30.0) -> FakeVideoSource:
        """Kayıpsız, sabit aralıklı `n_frames` karelik kaynak."""
        timestamps = [round(i * 1000 / fps) for i in range(n_frames)]
        return cls(session_id, timestamps, nominal_fps=fps)

    @property
    def stats(self) -> CaptureStats:
        return self._stats

    def frames(self) -> Iterator[FrameRecord]:
        tracker = FrameTimingTracker(self._stats.nominal_fps)
        for pos, timestamp_ms in enumerate(self._timestamps):
            index = self._indices[pos] if self._indices is not None else pos
            if pos in self._errors:
                self._stats.read_errors += 1
                yield FrameRecord(
                    self.session_id, index, timestamp_ms, None, SourceStatus.READ_ERROR
                )
                continue
            status = SourceStatus.OK
            if not tracker.add(timestamp_ms):
                status = SourceStatus.TIMESTAMP_ERROR
                self._stats.timestamp_errors += 1
            self._stats.frames_read += 1
            self._stats.measured_fps = tracker.measured_fps
            self._stats.dropped_by_source = tracker.dropped
            yield FrameRecord(self.session_id, index, timestamp_ms, self._frame, status)
