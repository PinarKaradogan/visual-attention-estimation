"""Tüm video kaynaklarının ortak arayüzü.

Kullanım:

    with FileVideoSource(path, session_id="P01_SCENARIO") as source:
        for record in source:
            ...
    stats = source.stats
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from types import TracebackType

from visual_attention.capture.records import CaptureStats, FrameRecord


class VideoSource(ABC):
    def __init__(self, session_id: str) -> None:
        if not session_id:
            raise ValueError("session_id boş olamaz")
        self.session_id = session_id

    @property
    @abstractmethod
    def stats(self) -> CaptureStats:
        """Kaynak ve kare akışı bilgileri; okuma ilerledikçe güncellenir."""

    @abstractmethod
    def frames(self) -> Iterator[FrameRecord]:
        """Kareleri zaman sırasıyla verir."""

    def open(self) -> None:  # noqa: B027 - alt sınıflar gerekirse ezer
        """Kaynağı açar. Varsayılan: bir şey yapmaz."""

    def close(self) -> None:  # noqa: B027 - alt sınıflar gerekirse ezer
        """Kaynağı kapatır. Varsayılan: bir şey yapmaz."""

    def __iter__(self) -> Iterator[FrameRecord]:
        return self.frames()

    def __enter__(self) -> VideoSource:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
