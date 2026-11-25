"""Oturum düzeyi ölçümler (rapor §2.7, H4).

Girdi her zaman 1 sn'lik, örtüşmeyen etiket dizisidir (TimelineResolver çıktısı veya
LabelAligner'ın referansı). Model ve referans aynı fonksiyonlardan geçer; böylece
"aynı ardışık-zaman kuralı" iki tarafa da aynen uygulanır.

Sürüm 0.1 kararları (docs/labeling-protocol.md'de kilitlenecek):
- Yumuşatma uygulanmaz.
- Kesinti = aynı MATERYAL dışı sınıfın kesintisiz >= 3 sn sürmesi. Araya giren
  BELIRSIZ veya GECIS saniyesi koşuyu böler.
- BELIRSIZ ve GECIS saniyeleri geçerli süre sayılmaz (odak oranının paydasına girmez).
- Olay eşleştirme: aynı sınıf, başlangıç farkı <= ±2 sn, bire bir, en küçük fark önce.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from visual_attention.core.constants import EVENT_TOLERANCE_S, INTERRUPTION_MIN_S, SECOND_MS
from visual_attention.core.labels import NON_MATERIAL_CLASSES, Label
from visual_attention.core.records import SecondDecision


@dataclass(frozen=True, slots=True)
class Interruption:
    label: Label
    start_s: int
    end_s: int  # yarı açık

    @property
    def duration_s(self) -> int:
        return self.end_s - self.start_s


@dataclass(frozen=True, slots=True)
class SessionSummary:
    total_seconds: int
    valid_seconds: int
    focus_seconds: int
    focus_ratio: float | None
    belirsiz_seconds: int
    belirsiz_ratio: float
    gecis_seconds: int
    interruptions: tuple[Interruption, ...]

    @property
    def interruption_count(self) -> int:
        return len(self.interruptions)


@dataclass(frozen=True, slots=True)
class EventMatch:
    tp: int
    fp: int
    fn: int
    precision: float | None
    recall: float | None
    f1: float | None


@dataclass(frozen=True, slots=True)
class SessionErrors:
    reference: SessionSummary
    predicted: SessionSummary
    focus_abs_error_s: int
    interruption_count_abs_error: int
    events: EventMatch


def labels_from_decisions(decisions: Sequence[SecondDecision]) -> list[Label]:
    """SecondDecision listesini boşluksuz etiket dizisine çevirir ve sözleşmeyi doğrular."""
    ordered = sorted(decisions, key=lambda d: d.second_start_ms)
    for i, d in enumerate(ordered):
        if d.second_start_ms != i * SECOND_MS:
            raise ValueError(
                f"Zaman çizelgesi boşluklu veya yinelenen: {i}. sıra, {d.second_start_ms} ms"
            )
    return [d.label for d in ordered]


def extract_interruptions(
    labels: Sequence[Label],
    min_duration_s: int = INTERRUPTION_MIN_S,
) -> list[Interruption]:
    """Aynı MATERYAL dışı sınıfın en az `min_duration_s` süren kesintisiz koşularını bulur."""
    if min_duration_s < 1:
        raise ValueError("min_duration_s >= 1 olmalı")
    events: list[Interruption] = []
    run_label: Label | None = None
    run_start = 0
    for i, lab in enumerate([*labels, None]):
        if lab == run_label:
            continue
        if run_label in NON_MATERIAL_CLASSES and i - run_start >= min_duration_s:
            events.append(Interruption(run_label, run_start, i))
        run_label, run_start = lab, i
    return events


def summarize_session(
    labels: Sequence[Label],
    min_interruption_s: int = INTERRUPTION_MIN_S,
) -> SessionSummary:
    total = len(labels)
    belirsiz = sum(1 for lab in labels if lab is Label.BELIRSIZ)
    gecis = sum(1 for lab in labels if lab is Label.GECIS)
    valid = total - belirsiz - gecis
    focus = sum(1 for lab in labels if lab is Label.MATERYAL)
    return SessionSummary(
        total_seconds=total,
        valid_seconds=valid,
        focus_seconds=focus,
        focus_ratio=focus / valid if valid else None,
        belirsiz_seconds=belirsiz,
        belirsiz_ratio=belirsiz / total if total else 0.0,
        gecis_seconds=gecis,
        interruptions=tuple(extract_interruptions(labels, min_interruption_s)),
    )


def event_f1(
    reference: Sequence[Interruption],
    predicted: Sequence[Interruption],
    tolerance_s: int = EVENT_TOLERANCE_S,
) -> EventMatch:
    """Kesinti olaylarını bire bir eşleştirip olay düzeyi precision/recall/F1 hesaplar.

    Olay olmayan tarafta ilgili oran tanımsızdır (None). İki tarafta da olay yoksa F1
    tanımsızdır; serbest oturumlarda bu durum "tanımsız" olarak raporlanır.
    """
    candidates = sorted(
        (abs(r.start_s - p.start_s), ri, pi)
        for ri, r in enumerate(reference)
        for pi, p in enumerate(predicted)
        if r.label == p.label and abs(r.start_s - p.start_s) <= tolerance_s
    )
    used_r: set[int] = set()
    used_p: set[int] = set()
    for _, ri, pi in candidates:
        if ri not in used_r and pi not in used_p:
            used_r.add(ri)
            used_p.add(pi)
    tp = len(used_r)
    n_ref, n_pred = len(reference), len(predicted)
    return EventMatch(
        tp=tp,
        fp=n_pred - tp,
        fn=n_ref - tp,
        precision=tp / n_pred if n_pred else None,
        recall=tp / n_ref if n_ref else None,
        f1=2 * tp / (n_ref + n_pred) if (n_ref + n_pred) else None,
    )


def compare_sessions(
    reference: Sequence[Label],
    predicted: Sequence[Label],
    min_interruption_s: int = INTERRUPTION_MIN_S,
    tolerance_s: int = EVENT_TOLERANCE_S,
) -> SessionErrors:
    """Referans ve model zaman çizelgelerinden oturum hatalarını hesaplar."""
    if len(reference) != len(predicted):
        raise ValueError(
            f"Uzunluklar farklı: referans {len(reference)} sn, tahmin {len(predicted)} sn"
        )
    ref = summarize_session(reference, min_interruption_s)
    pred = summarize_session(predicted, min_interruption_s)
    return SessionErrors(
        reference=ref,
        predicted=pred,
        focus_abs_error_s=abs(ref.focus_seconds - pred.focus_seconds),
        interruption_count_abs_error=abs(ref.interruption_count - pred.interruption_count),
        events=event_f1(ref.interruptions, pred.interruptions, tolerance_s),
    )
