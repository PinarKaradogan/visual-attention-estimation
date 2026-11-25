"""Kayıtlı videodan kare okuma (FILE modu, data-schema §3.2).

- Zaman damgası, kaynağın kare sunum zamanından (OpenCV `CAP_PROP_POS_MSEC`, okunan karenin
  kendi zamanı) alınır. Dosyanın işlendiği duvar/CPU saati kullanılmaz; sabit FPS
  varsayımıyla zaman türetilmez.
- Tüm kareler sırayla işlenir: `skipped_by_pipeline` her zaman 0'dır.
- Kesin artmayan zaman damgası düzeltilmez; kare `TIMESTAMP_ERROR` olarak işaretlenir.
- `dropped_by_source`, zaman damgası boşluklarından kestirilir.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from visual_attention.capture.base import VideoSource
from visual_attention.capture.records import (
    CaptureStats,
    FrameRecord,
    FrameTimingTracker,
    SourceMode,
    SourceStatus,
)


class FileVideoSource(VideoSource):
    def __init__(self, path: str | Path, session_id: str, source_id: str = "file") -> None:
        """
        Args:
            path: Yerel video dosyası (`local_data/` altında; GitHub'a girmez).
            session_id: Oturum kodu (ör. `P01_SCENARIO`).
            source_id: Kayıtlarda görünecek kaynak kodu. Kişisel veri veya tam dosya yolu
                içermemelidir; bu yüzden dosya adı varsayılan olarak kullanılmaz.
        """
        super().__init__(session_id)
        self._path = Path(path)
        self._cap = None
        self._stats = CaptureStats(source_mode=SourceMode.FILE, source_id=source_id)
        self._tracker: FrameTimingTracker | None = None

    @property
    def stats(self) -> CaptureStats:
        return self._stats

    def open(self) -> None:
        if self._cap is not None:
            return
        import cv2

        if not self._path.is_file():
            raise FileNotFoundError(f"Video dosyası bulunamadı: {self._path.name}")
        cap = cv2.VideoCapture(str(self._path))
        if not cap.isOpened():
            cap.release()
            raise OSError(f"Video dosyası açılamadı: {self._path.name}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._stats.nominal_fps = fps if fps and fps > 0 else None
        self._stats.width_px = width or None
        self._stats.height_px = height or None
        self._stats.skipped_by_pipeline = 0
        self._tracker = FrameTimingTracker(self._stats.nominal_fps)
        self._cap = cap

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def frames(self) -> Iterator[FrameRecord]:
        import cv2

        self.open()
        assert self._cap is not None and self._tracker is not None
        index = 0
        while True:
            ok, frame = self._cap.read()
            if not ok:
                break  # dosya sonu
            timestamp_ms = max(0, round(self._cap.get(cv2.CAP_PROP_POS_MSEC)))
            status = SourceStatus.OK
            if not self._tracker.add(timestamp_ms):
                status = SourceStatus.TIMESTAMP_ERROR
                self._stats.timestamp_errors += 1
            self._stats.frames_read += 1
            self._stats.measured_fps = self._tracker.measured_fps
            self._stats.dropped_by_source = self._tracker.dropped
            yield FrameRecord(self.session_id, index, timestamp_ms, frame, status)
            index += 1
