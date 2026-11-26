"""Sentetik "gerçek davranış" zaman çizelgesi.

SENTETİKTİR, GERÇEK VERİ DEĞİLDİR. Yalnızca yazılım testleri içindir; hiçbir sonuç, eşik
veya model bu çizelgeden türetilmez ve raporlanmaz.

Senaryolu oturumda kişi komutu duyduktan kısa bir süre sonra davranışını değiştirir. Bu
yüzden davranış sınırları senaryodaki komut zamanlarından bir tepki gecikmesi kadar
sonradır. Serbest oturumda komut yoktur; davranış dizisi rastgele çekilir.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from visual_attention.core.constants import SECOND_MS
from visual_attention.core.labels import MAIN_CLASSES, Label
from visual_attention.core.records import check_interval
from visual_attention.scenario.generator import Scenario


@dataclass(frozen=True, slots=True)
class BehaviorSegment:
    """Kişinin [start_ms, end_ms) aralığındaki gerçek davranışı (yalnız ana sınıflar)."""

    start_ms: int
    end_ms: int
    label: Label

    def __post_init__(self) -> None:
        check_interval(self.start_ms, self.end_ms, "davranış aralığı")
        if self.label not in MAIN_CLASSES:
            raise ValueError(f"Davranış yalnızca ana sınıf olabilir: {self.label}")

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


def label_at(segments: tuple[BehaviorSegment, ...], t_ms: int) -> Label:
    """t anındaki davranış (segmentler sıralı ve boşluksuz varsayılır)."""
    lo, hi = 0, len(segments) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        seg = segments[mid]
        if t_ms < seg.start_ms:
            hi = mid - 1
        elif t_ms >= seg.end_ms:
            lo = mid + 1
        else:
            return seg.label
    raise ValueError(f"{t_ms} ms davranış çizelgesinin dışında")


def scenario_behavior(
    scenario: Scenario,
    rng: random.Random,
    reaction_delay_ms: tuple[int, int] = (200, 1200),
) -> tuple[BehaviorSegment, ...]:
    """Senaryo bloklarını, her komuttan sonra tepki gecikmesi ekleyerek davranışa çevirir.

    Oturumun başı (0) ve sonu kaydırılmaz. Gecikme (0, 0) verilirse davranış sınırları
    komut zamanlarıyla birebir aynıdır.
    """
    lo, hi = reaction_delay_ms
    if lo < 0 or hi < lo:
        raise ValueError(f"Geçersiz tepki gecikmesi aralığı: {reaction_delay_ms}")
    blocks = scenario.blocks
    duration_ms = blocks[-1].end_s * SECOND_MS
    bounds = [0]
    for b in blocks[1:]:
        bounds.append(b.start_s * SECOND_MS + rng.randint(lo, hi))
    bounds.append(duration_ms)
    return tuple(BehaviorSegment(bounds[i], bounds[i + 1], b.label) for i, b in enumerate(blocks))


@dataclass(frozen=True)
class FreeSessionConfig:
    """Serbest oturum davranış süreleri (saniye, kapalı aralık)."""

    session_s: int = 600
    material_range_s: tuple[int, int] = (20, 120)
    phone_range_s: tuple[int, int] = (3, 40)
    away_range_s: tuple[int, int] = (2, 15)
    phone_probability: float = 0.5


def free_behavior(
    rng: random.Random,
    config: FreeSessionConfig | None = None,
) -> tuple[BehaviorSegment, ...]:
    """Yönlendirmesiz oturum: MATERYAL blokları arasına rastgele TELEFON/DIS_YON gelir."""
    cfg = config or FreeSessionConfig()
    total_ms = cfg.session_s * SECOND_MS
    segments: list[BehaviorSegment] = []
    t = 0
    material = True
    while t < total_ms:
        if material:
            label, rng_s = Label.MATERYAL, cfg.material_range_s
        elif rng.random() < cfg.phone_probability:
            label, rng_s = Label.TELEFON, cfg.phone_range_s
        else:
            label, rng_s = Label.DIS_YON, cfg.away_range_s
        dur = rng.randint(rng_s[0] * SECOND_MS, rng_s[1] * SECOND_MS)
        end = min(t + dur, total_ms)
        segments.append(BehaviorSegment(t, end, label))
        t = end
        material = not material
    return tuple(segments)
