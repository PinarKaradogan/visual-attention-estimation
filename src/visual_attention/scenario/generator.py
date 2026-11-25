"""Senaryolu oturum üreticisi (rapor §2.2, Ek-1).

Kural (scn-0.1.0):
- Oturum 1200 sn.
- Kişi başına n TELEFON (5–30 sn) ve n DIS_YON (2–20 sn) kesintisi; varsayılan n = 6.
  Risk B planında n = 8'e çıkarılır (oturum süresi sabit).
- Kesintiler tohumlu rastgele sıralanır; aralarında ve başta/sonda en az 60 sn MATERYAL
  bloğu bulunur.
- Kesinti süreleri 2–5 sn eşik aralığını kapsar (2, 3 ve 5 sn duyarlılık eşiklerinin
  her birinin hemen altında ve üstünde örnek olsun diye):
  * tam olarak bir kesinti 3 sn'den kısa (2 sn); birden fazla olursa ≥ 3 sn olay sayısı
    gereksiz düşer,
  * en az bir kesinti 3–4 sn (3 ≤ süre < 5).
- Süre aralıkları B planında da v5'teki gibi kalır (5–30 / 2–20 sn); oturum 1200 sn'ye
  sığmayan çekilişler reddedilip yeniden çekilir.
- Tohum, ana tohum ve katılımcı kodundan deterministik türetilir; aynı girdi her
  makinede aynı senaryoyu verir.

Senaryo komut zamanlarını verir. Referans etiketler komut zamanından değil, videonun
insan tarafından incelenmesinden gelir; bu çıktı yalnızca kayıt yönergesi ve sentetik
test verisi içindir.
"""

from __future__ import annotations

import csv
import hashlib
import random
from dataclasses import dataclass, field
from pathlib import Path

from visual_attention.core.labels import Label

SCENARIO_VERSION = "scn-0.2.0"

COMMANDS = {
    Label.MATERYAL: "Kâğıda dön",
    Label.TELEFON: "Telefonu al ve ekranı kaydır",
    Label.DIS_YON: "Duvardaki işarete bak",
}
"""Operatörün söyleyeceği sabit komut cümleleri; ilk blokta "Çalışmaya başla" kullanılır."""

FIRST_COMMAND = "Çalışmaya başla"

TASKS = {
    Label.MATERYAL: "Kitap/defter üzerinde okuma, yazma, not alma veya soru çözme",
    Label.TELEFON: "Görünür telefonda kısa etkileşim",
    Label.DIS_YON: "Çalışma alanı dışındaki sabit hedefe bakma",
}


@dataclass(frozen=True)
class ScenarioConfig:
    session_s: int = 1200
    events_per_class: int = 6
    phone_range_s: tuple[int, int] = (5, 30)
    away_range_s: tuple[int, int] = (2, 20)
    min_material_s: int = 60
    max_below_3s: int = 1  # 3 sn'den kısa kesinti tam olarak bu kadar
    min_3_to_5s: int = 1  # 3 ≤ süre < 5 olan kesinti en az bu kadar
    max_attempts: int = 1000


@dataclass(frozen=True)
class ScenarioBlock:
    start_s: int
    end_s: int
    label: Label

    @property
    def duration_s(self) -> int:
        return self.end_s - self.start_s

    @property
    def task(self) -> str:
        return TASKS[self.label]


@dataclass(frozen=True)
class Scenario:
    participant_id: str
    seed: int
    blocks: tuple[ScenarioBlock, ...]
    base_seed: int = 0
    config: ScenarioConfig = field(default_factory=ScenarioConfig)
    version: str = SCENARIO_VERSION

    def to_labels(self) -> list[Label]:
        """1 sn çözünürlüklü komut zaman çizelgesi (sentetik veri ve testler için)."""
        return [b.label for b in self.blocks for _ in range(b.duration_s)]

    @property
    def interruptions(self) -> list[ScenarioBlock]:
        return [b for b in self.blocks if b.label is not Label.MATERYAL]


def participant_seed(base_seed: int, participant_id: str) -> int:
    digest = hashlib.sha256(f"{base_seed}:{participant_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def generate_scenario(
    participant_id: str,
    base_seed: int,
    config: ScenarioConfig | None = None,
) -> Scenario:
    cfg = config or ScenarioConfig()
    seed = participant_seed(base_seed, participant_id)
    rng = random.Random(seed)
    for _ in range(cfg.max_attempts):
        blocks = _try_build(rng, cfg)
        if blocks is not None:
            scenario = Scenario(participant_id, seed, tuple(blocks), base_seed, cfg)
            validate_scenario(scenario)
            return scenario
    raise ValueError(f"{cfg.max_attempts} denemede kurallara uyan senaryo üretilemedi: {cfg}")


def _try_build(rng: random.Random, cfg: ScenarioConfig) -> list[ScenarioBlock] | None:
    events = [(Label.TELEFON, rng.randint(*cfg.phone_range_s)) for _ in range(cfg.events_per_class)]
    events += [(Label.DIS_YON, rng.randint(*cfg.away_range_s)) for _ in range(cfg.events_per_class)]
    durations = [d for _, d in events]
    if not _threshold_coverage_ok(durations, cfg):
        return None

    n_material = len(events) + 1
    slack = cfg.session_s - sum(durations) - n_material * cfg.min_material_s
    if slack < 0:
        return None
    rng.shuffle(events)
    extra = _random_composition(rng, slack, n_material)

    blocks: list[ScenarioBlock] = []
    t = 0
    for i in range(n_material):
        m = cfg.min_material_s + extra[i]
        blocks.append(ScenarioBlock(t, t + m, Label.MATERYAL))
        t += m
        if i < len(events):
            label, d = events[i]
            blocks.append(ScenarioBlock(t, t + d, label))
            t += d
    return blocks


def _threshold_coverage_ok(durations: list[int], cfg: ScenarioConfig) -> bool:
    below_3 = sum(d < 3 for d in durations)
    between_3_5 = sum(3 <= d < 5 for d in durations)
    return below_3 == cfg.max_below_3s and between_3_5 >= cfg.min_3_to_5s


def _random_composition(rng: random.Random, total: int, parts: int) -> list[int]:
    """`total`'ı `parts` negatif olmayan tam sayıya rastgele böler."""
    cuts = sorted(rng.randint(0, total) for _ in range(parts - 1))
    bounds = [0, *cuts, total]
    return [bounds[i + 1] - bounds[i] for i in range(parts)]


def validate_scenario(s: Scenario) -> None:
    """Senaryonun rapor §2.2 kurallarına uyduğunu doğrular; aksi hâlde ValueError."""
    cfg = s.config
    if not s.blocks or s.blocks[0].start_s != 0 or s.blocks[-1].end_s != cfg.session_s:
        raise ValueError("Senaryo 0'dan oturum sonuna kadar uzanmalı")
    for a, b in zip(s.blocks, s.blocks[1:], strict=False):
        if a.end_s != b.start_s:
            raise ValueError(f"Bloklar arasında boşluk/çakışma: {a} {b}")
        if a.label is not Label.MATERYAL and b.label is not Label.MATERYAL:
            raise ValueError("İki kesinti arasında MATERYAL bloğu olmalı")
    if s.blocks[0].label is not Label.MATERYAL or s.blocks[-1].label is not Label.MATERYAL:
        raise ValueError("Oturum MATERYAL ile başlamalı ve bitmeli")
    ranges = {Label.TELEFON: cfg.phone_range_s, Label.DIS_YON: cfg.away_range_s}
    counts = {Label.TELEFON: 0, Label.DIS_YON: 0}
    for blk in s.blocks:
        if blk.label is Label.MATERYAL:
            if blk.duration_s < cfg.min_material_s:
                raise ValueError(f"MATERYAL bloğu {cfg.min_material_s} sn'den kısa: {blk}")
            continue
        lo, hi = ranges[blk.label]
        if not lo <= blk.duration_s <= hi:
            raise ValueError(f"{blk.label} süresi [{lo}, {hi}] dışında: {blk}")
        counts[blk.label] += 1
    if any(c != cfg.events_per_class for c in counts.values()):
        raise ValueError(f"Sınıf başına {cfg.events_per_class} kesinti beklenir: {counts}")
    if not _threshold_coverage_ok([b.duration_s for b in s.interruptions], cfg):
        raise ValueError("Kesinti süreleri 2–5 sn eşik aralığını kapsamıyor")


def fmt_mmss(seconds: int) -> str:
    return f"{seconds // 60:02d}.{seconds % 60:02d}"


def write_scenario_csv(s: Scenario, path: Path) -> None:
    """Kayıt sırasında operatörün izleyeceği çizelge (rapor Ek-1 biçimi)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["participant_id", "scenario_version", "base_seed", "seed", "block_no",
                    "start", "end", "start_s", "end_s", "duration_s", "label", "task",
                    "command", "actual_note"])  # fmt: skip
        for i, b in enumerate(s.blocks):
            command = FIRST_COMMAND if i == 0 else COMMANDS[b.label]
            w.writerow([s.participant_id, s.version, s.base_seed, s.seed, i + 1,
                        fmt_mmss(b.start_s), fmt_mmss(b.end_s), b.start_s, b.end_s,
                        b.duration_s, b.label.display_name, b.task, command, ""])  # fmt: skip
