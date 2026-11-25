"""Komut satırı: katılımcı başına senaryo çizelgesi üretir.

Örnek:
    python -m visual_attention.scenario --participants P01-P10 --seed 2026

Çizelgeler varsayılan olarak Git dışındaki local_data/scenarios/ klasörüne yazılır.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from visual_attention.metrics import summarize_session
from visual_attention.scenario.generator import (
    ScenarioConfig,
    generate_scenario,
    write_scenario_csv,
)


def parse_participants(spec: str) -> list[str]:
    """'P01-P10' veya 'P01,P02,P05' biçimini açar."""
    if "-" in spec and "," not in spec:
        a, b = spec.split("-")
        prefix = a.rstrip("0123456789")
        width = len(a) - len(prefix)
        return [
            f"{prefix}{i:0{width}d}"
            for i in range(int(a[len(prefix) :]), int(b[len(prefix) :]) + 1)
        ]
    return [p.strip() for p in spec.split(",") if p.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--participants", required=True, help="Örn. P01-P10 veya P01,P02")
    ap.add_argument("--seed", type=int, required=True, help="Ana tohum (protokole yazılır)")
    ap.add_argument("--events-per-class", type=int, default=6, help="B planında 8")
    ap.add_argument("--out", type=Path, default=Path("local_data/scenarios"))
    args = ap.parse_args(argv)

    cfg = ScenarioConfig(events_per_class=args.events_per_class)
    for pid in parse_participants(args.participants):
        s = generate_scenario(pid, args.seed, cfg)
        write_scenario_csv(s, args.out / f"{pid}_scenario.csv")
        summary = summarize_session(s.to_labels())
        total = sum(b.duration_s for b in s.interruptions)
        print(
            f"{pid}: {len(s.blocks)} blok, kesinti {total} sn, "
            f">=3 sn kesinti {summary.interruption_count}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
