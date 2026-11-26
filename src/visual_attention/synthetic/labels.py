"""Sentetik insan etiketi (ELAN TSV biçiminde).

SENTETİKTİR, GERÇEK VERİ DEĞİLDİR. Gerçek etiketleyicinin davranışını kabaca taklit eder:
sınırları birkaç yüz milisaniye kaydırır ve ara sıra kısa BELIRSIZ aralıklar işaretler.
Amaç ELAN okuyucunun, 1 sn referansın ve pencere eğitim hedefinin gerçek biçimdeki
dosyalarla uçtan uca sınanmasıdır.
"""

from __future__ import annotations

import csv
import random
from collections.abc import Iterable
from pathlib import Path

from visual_attention.core.labels import Label
from visual_attention.core.reference import HumanLabelInterval
from visual_attention.core.status import LabelRound
from visual_attention.labeling.elan import ELAN_COLUMNS
from visual_attention.synthetic.behavior import BehaviorSegment

MIN_SYNTHETIC_INTERVAL_MS = 200


def synthetic_label_intervals(
    behavior: tuple[BehaviorSegment, ...],
    session_id: str,
    rng: random.Random,
    *,
    annotator_id: str = "A1",
    label_round: LabelRound = LabelRound.R1,
    label_version: str,
    boundary_jitter_ms: int = 300,
    belirsiz_spans: int = 1,
    belirsiz_range_ms: tuple[int, int] = (1000, 3000),
) -> tuple[HumanLabelInterval, ...]:
    """Davranış çizelgesinden boşluksuz, çakışmasız etiket aralıkları üretir.

    - Her iç sınır [-jitter, +jitter] ms kaydırılır; aralıklar en az
      MIN_SYNTHETIC_INTERVAL_MS kalır. Oturum başı ve sonu kaydırılmaz.
    - `belirsiz_spans` adet BELIRSIZ aralık, yeterince uzun MATERYAL aralıklarının içine
      yerleştirilir (gerçekte kişinin yüzü bir an kapandığında olduğu gibi).
    """
    if boundary_jitter_ms < 0 or belirsiz_spans < 0:
        raise ValueError("Kaydırma ve BELIRSIZ sayısı negatif olamaz")
    bounds = [seg.start_ms for seg in behavior] + [behavior[-1].end_ms]
    for i in range(1, len(bounds) - 1):
        low = bounds[i - 1] + MIN_SYNTHETIC_INTERVAL_MS
        high = bounds[i + 1] - MIN_SYNTHETIC_INTERVAL_MS
        shifted = bounds[i] + rng.randint(-boundary_jitter_ms, boundary_jitter_ms)
        bounds[i] = min(max(shifted, low), high)

    spans: list[tuple[int, int, Label]] = [
        (bounds[i], bounds[i + 1], seg.label) for i, seg in enumerate(behavior)
    ]

    lo, hi = belirsiz_range_ms
    for _ in range(belirsiz_spans):
        margin = 2 * MIN_SYNTHETIC_INTERVAL_MS
        candidates = [
            i
            for i, (s, e, lab) in enumerate(spans)
            if lab is Label.MATERYAL and e - s >= hi + 2 * margin
        ]
        if not candidates:
            break
        i = rng.choice(candidates)
        s, e, lab = spans[i]
        dur = rng.randint(lo, hi)
        b_start = rng.randint(s + margin, e - margin - dur)
        spans[i : i + 1] = [
            (s, b_start, lab),
            (b_start, b_start + dur, Label.BELIRSIZ),
            (b_start + dur, e, lab),
        ]

    return tuple(
        HumanLabelInterval(
            session_id=session_id,
            annotator_id=annotator_id,
            label_round=label_round,
            start_ms=s,
            end_ms=e,
            label=lab,
            label_version=label_version,
        )
        for s, e, lab in spans
    )


def elan_filename(session_id: str, label_round: LabelRound, annotator_id: str) -> str:
    """Protokoldeki adlandırma: <katılımcı>_<oturum>_<tur>_<etiketleyici>.tsv."""
    return f"{session_id}_{LabelRound(label_round).value}_{annotator_id}.tsv"


def write_elan_tsv(intervals: Iterable[HumanLabelInterval], path: str | Path) -> Path:
    """Aralıkları ELAN dışa aktarım biçiminde (TAB ayraçlı, başlıklı) yazar.

    Yalnızca testlerde geçici klasöre yazmak içindir; sentetik dosyalar Git'e ve
    local_data/'ya konmaz.
    """
    out = Path(path)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(ELAN_COLUMNS)
        for iv in intervals:
            w.writerow((iv.start_ms, iv.end_ms, iv.label.value))
    return out
