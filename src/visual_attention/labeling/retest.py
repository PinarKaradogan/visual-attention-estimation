"""Test–tekrar test alt kümesinin seçimi (docs/labeling-protocol.md §7.1).

Her katılımcının her oturumundan oturum süresinin %25'i kadar kesintisiz bir kesit seçilir.
Başlangıç sabit tohumla (2209) rastgele çekilir. Kesitte ilk etiketlere göre TELEFON veya
DIS_YON yoksa kesit 30 sn'lik adımlarla ileri kaydırılır; sona gelince başa dönülür.
İki sınıfın da bulunduğu ilk konum kullanılır; hiç bulunamazsa ilk konumda kalınır ve not
edilir. Tohum, tohum + oturum kodundan SHA-256 ile türetilir (makineden bağımsız).
"""

from __future__ import annotations

import csv
import hashlib
import random
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from visual_attention.core import SECOND_MS, HumanLabelInterval, Label

RETEST_SEED = 2209
RETEST_FRACTION = 0.25
SHIFT_STEP_S = 30
REQUIRED_CLASSES = (Label.TELEFON, Label.DIS_YON)


@dataclass(frozen=True, slots=True)
class RetestSegment:
    session_id: str
    start_ms: int
    end_ms: int
    shifts: int
    classes_found: bool
    seed: int

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


def session_seed(base_seed: int, session_id: str) -> int:
    digest = hashlib.sha256(f"{base_seed}:{session_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _has_required_classes(intervals: list[HumanLabelInterval], start_ms: int, end_ms: int) -> bool:
    present = {
        iv.label for iv in intervals if min(iv.end_ms, end_ms) - max(iv.start_ms, start_ms) > 0
    }
    return all(lab in present for lab in REQUIRED_CLASSES)


def select_retest_segment(
    session_id: str,
    session_duration_ms: int,
    first_round_intervals: Iterable[HumanLabelInterval],
    base_seed: int = RETEST_SEED,
    fraction: float = RETEST_FRACTION,
    shift_step_s: int = SHIFT_STEP_S,
) -> RetestSegment:
    """Bir oturum için tekrar etiketlenecek kesiti seçer (saniye ızgarasında)."""
    if session_duration_ms < SECOND_MS:
        raise ValueError("Oturum en az 1 sn olmalı")
    if not 0 < fraction <= 1:
        raise ValueError("fraction (0, 1] aralığında olmalı")
    duration_s = session_duration_ms // SECOND_MS
    segment_s = max(1, round(duration_s * fraction))
    max_start_s = duration_s - segment_s
    seed = session_seed(base_seed, session_id)
    initial_s = random.Random(seed).randint(0, max_start_s)

    ivs = [iv for iv in first_round_intervals if iv.session_id == session_id]
    positions = max_start_s + 1
    steps = -(-positions // shift_step_s)  # tüm konumları bir kez dolaşacak kadar adım
    for k in range(steps):
        start_s = (initial_s + k * shift_step_s) % positions
        start_ms, end_ms = start_s * SECOND_MS, (start_s + segment_s) * SECOND_MS
        if _has_required_classes(ivs, start_ms, end_ms):
            return RetestSegment(session_id, start_ms, end_ms, k, True, seed)
    start_ms = initial_s * SECOND_MS
    return RetestSegment(session_id, start_ms, start_ms + segment_s * SECOND_MS, 0, False, seed)


def write_retest_plan(segments: Iterable[RetestSegment], path: Path) -> None:
    """Seçilen kesitlerin kaydı (§7.1: oturum, başlangıç, bitiş, kaydırma sayısı)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["session_id", "start_ms", "end_ms", "duration_ms", "shifts",
                    "classes_found", "base_seed", "seed"])  # fmt: skip
        for s in segments:
            w.writerow([s.session_id, s.start_ms, s.end_ms, s.duration_ms, s.shifts,
                        s.classes_found, RETEST_SEED, s.seed])  # fmt: skip
