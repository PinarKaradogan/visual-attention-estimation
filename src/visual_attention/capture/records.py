"""Kare ve kaynak kayıtları (docs/data-schema.md §3.1–3.2).

Zaman her zaman oturum başından itibaren video zamanıdır (ms). Kareler yalnız bellekte
tutulur; hiçbir kare diske, GitHub'a veya FeatureStore'a yazılmaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np


class SourceMode(StrEnum):
    FILE = "FILE"
    """Kayıtlı video; araştırma oturumları bu modda işlenir."""
    LIVE = "LIVE"
    """Canlı kamera; yalnız demo ve yerel arayüz için."""
    SYNTHETIC = "SYNTHETIC"
    """Testler için sahte kaynak."""


class SourceStatus(StrEnum):
    OK = "OK"
    READ_ERROR = "READ_ERROR"
    """Kaynak kare veremedi; `frame` None'dır."""
    TIMESTAMP_ERROR = "TIMESTAMP_ERROR"
    """Zaman damgası bir önceki kareden büyük değil; düzeltilmeden işaretlenir."""


@dataclass(frozen=True, slots=True, eq=False)
class FrameRecord:
    """Kaynaktan okunan tek kare.

    `frame_index` kaynağın kare sırasıdır: canlı modda işlenemeyen kareler sırada boşluk
    olarak görünür. `frame` BGR biçimli numpy dizisidir.
    """

    session_id: str
    frame_index: int
    timestamp_ms: int
    frame: np.ndarray | None = field(repr=False)
    source_status: SourceStatus = SourceStatus.OK

    def __post_init__(self) -> None:
        if self.frame_index < 0:
            raise ValueError("frame_index negatif olamaz")
        if self.timestamp_ms < 0:
            raise ValueError("timestamp_ms negatif olamaz")
        if not isinstance(self.source_status, SourceStatus):
            object.__setattr__(self, "source_status", SourceStatus(self.source_status))


@dataclass(slots=True)
class CaptureStats:
    """Bir kaynağın oturum boyunca biriken bilgileri.

    `SessionRecord`'ın (data-schema §3.1) kaynakla ilgili alanlarını doldurmak için
    kullanılır. `measured_fps` video zamanındaki kare hızıdır (işlem hızı değil).
    """

    source_mode: SourceMode
    source_id: str
    width_px: int | None = None
    height_px: int | None = None
    nominal_fps: float | None = None
    measured_fps: float | None = None
    frames_read: int = 0
    dropped_by_source: int | None = None
    skipped_by_pipeline: int = 0
    read_errors: int = 0
    timestamp_errors: int = 0


class FrameTimingTracker:
    """Zaman damgalarını izler: kesin artışı denetler, ölçülen FPS'i ve kare kaybını kestirir.

    Kare kaybı, ardışık iki zaman damgası arasındaki boşluk beklenen aralığın 1,5 katını
    aştığında `round(boşluk / aralık) - 1` olarak sayılır. Hedeflenen FPS bilinmiyorsa kayıp
    kestirilemez (`None`).
    """

    GAP_FACTOR = 1.5

    def __init__(self, nominal_fps: float | None) -> None:
        self._interval_ms = 1000.0 / nominal_fps if nominal_fps and nominal_fps > 0 else None
        self._first: int | None = None
        self._last: int | None = None
        self._count = 0
        self._dropped = 0

    def add(self, timestamp_ms: int) -> bool:
        """Zaman damgasını ekler. Önceki damgadan büyük değilse False döner ve sayılmaz."""
        if self._last is not None and timestamp_ms <= self._last:
            return False
        if self._last is not None and self._interval_ms is not None:
            gap = timestamp_ms - self._last
            if gap > self.GAP_FACTOR * self._interval_ms:
                self._dropped += round(gap / self._interval_ms) - 1
        if self._first is None:
            self._first = timestamp_ms
        self._last = timestamp_ms
        self._count += 1
        return True

    @property
    def dropped(self) -> int | None:
        return self._dropped if self._interval_ms is not None else None

    @property
    def measured_fps(self) -> float | None:
        if self._count < 2 or self._first is None or self._last is None:
            return None
        return (self._count - 1) * 1000.0 / (self._last - self._first)
