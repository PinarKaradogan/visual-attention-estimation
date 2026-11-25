"""Canlı kameradan kare okuma (LIVE modu; yalnız demo ve yerel arayüz için).

- Arka plandaki okuyucu iş parçacığı kamerayı sürekli okur. Zaman damgası, oturum
  başlangıcına göre monotonik saatle ölçülen kare **okuma** zamanıdır; OpenCV tamponu
  nedeniyle gerçek yakalama zamanı olmayabilir (data-schema §3.2).
- İşleme yetişemezse en yeni kare tercih edilir: tampon doluyken gelen yeni kare en eskisinin
  yerini alır ve atılan kare `skipped_by_pipeline` sayacına eklenir. Atılan kareler
  `frame_index` sırasında boşluk olarak görünür.
- Araştırma oturumları bu modda değil, kayıtlı videodan FILE modunda işlenir.
"""

from __future__ import annotations

import sys
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from typing import Any

from visual_attention.capture.base import VideoSource
from visual_attention.capture.records import (
    CaptureStats,
    FrameRecord,
    FrameTimingTracker,
    SourceMode,
    SourceStatus,
)


class LatestFrameBuffer:
    """İş parçacığı güvenli, sınırlı "en yeni kare" tamponu.

    Tampon doluyken `put` en eski öğeyi atar ve `skipped` sayacını artırır.
    """

    def __init__(self, maxlen: int = 1) -> None:
        if maxlen < 1:
            raise ValueError("maxlen >= 1 olmalı")
        self._items: deque[Any] = deque(maxlen=maxlen)
        self._cond = threading.Condition()
        self._skipped = 0

    def put(self, item: Any) -> None:
        with self._cond:
            if len(self._items) == self._items.maxlen:
                self._skipped += 1
            self._items.append(item)
            self._cond.notify()

    def get(self, timeout: float | None = None) -> Any | None:
        """En eski bekleyen öğeyi verir; süre dolarsa None döner."""
        with self._cond:
            if not self._items and not self._cond.wait_for(lambda: bool(self._items), timeout):
                return None
            return self._items.popleft()

    @property
    def skipped(self) -> int:
        with self._cond:
            return self._skipped

    def __len__(self) -> int:
        with self._cond:
            return len(self._items)


def _default_capture(camera_index: int) -> Any:
    import cv2

    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    return cv2.VideoCapture(camera_index, backend)


class LiveVideoSource(VideoSource):
    def __init__(
        self,
        camera_index: int,
        session_id: str,
        *,
        width: int | None = None,
        height: int | None = None,
        buffer_size: int = 1,
        max_consecutive_failures: int = 30,
        capture_factory: Callable[[int], Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """
        Args:
            camera_index: OpenCV kamera numarası.
            width, height: İstenen çözünürlük; kamera desteklemezse gerçek değer kaydedilir.
            buffer_size: Bekleyen en fazla kare sayısı (varsayılan 1: yalnız en yeni kare).
            max_consecutive_failures: Bu kadar ardışık okuma hatasında okuma durur.
            capture_factory: Testler için kamera yerine geçen nesne üreticisi.
            clock: Saniye döndüren monotonik saat (testlerde değiştirilebilir).
        """
        super().__init__(session_id)
        self._camera_index = camera_index
        self._width = width
        self._height = height
        self._max_failures = max_consecutive_failures
        self._capture_factory = capture_factory or _default_capture
        self._clock = clock
        self._buffer = LatestFrameBuffer(buffer_size)
        self._stats = CaptureStats(source_mode=SourceMode.LIVE, source_id=f"camera{camera_index}")
        self._cap: Any = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    @property
    def stats(self) -> CaptureStats:
        with self._lock:
            self._stats.skipped_by_pipeline = self._buffer.skipped
            return self._stats

    def open(self) -> None:
        if self._cap is not None:
            return
        import cv2

        cap = self._capture_factory(self._camera_index)
        if not cap.isOpened():
            cap.release()
            raise OSError(f"Kamera açılamadı: {self._camera_index}")
        if self._width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        if self._height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        fps = cap.get(cv2.CAP_PROP_FPS)
        self._stats.nominal_fps = fps if fps and fps > 0 else None
        self._stats.width_px = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or None
        self._stats.height_px = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or None
        self._cap = cap
        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, name="LiveVideoSource", daemon=True)
        self._thread.start()

    def _read_loop(self) -> None:
        tracker = FrameTimingTracker(self._stats.nominal_fps)
        t0 = self._clock()
        index = 0
        failures = 0
        while not self._stop.is_set():
            ok, frame = self._cap.read()
            if not ok:
                failures += 1
                with self._lock:
                    self._stats.read_errors += 1
                if failures >= self._max_failures:
                    break
                time.sleep(0.01)
                continue
            failures = 0
            timestamp_ms = max(0, round((self._clock() - t0) * 1000))
            status = SourceStatus.OK
            with self._lock:
                if not tracker.add(timestamp_ms):
                    status = SourceStatus.TIMESTAMP_ERROR
                    self._stats.timestamp_errors += 1
                self._stats.frames_read += 1
                self._stats.measured_fps = tracker.measured_fps
                self._stats.dropped_by_source = tracker.dropped
            self._buffer.put(FrameRecord(self.session_id, index, timestamp_ms, frame, status))
            index += 1

    def frames(self) -> Iterator[FrameRecord]:
        """Okuyucu durana ve tampon boşalana kadar en yeni kareleri verir."""
        self.open()
        while True:
            record = self._buffer.get(timeout=0.1)
            if record is not None:
                yield record
            elif self._thread is None or not self._thread.is_alive():
                if not len(self._buffer):
                    return

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None
