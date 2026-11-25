"""İnsan etiket aralıklarından 1 sn referans ve pencere eğitim hedefi (protokol §5).

Her iki çıktı da milisaniyelik aralıklardan doğrudan hesaplanır; biri diğerinden türetilmez.
Hiçbir aralığa düşmeyen süre UNLABELED sayılır ve hiçbir zaman MATERYAL kabul edilmez.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from visual_attention.core import (
    MAIN_CLASSES,
    SECOND_MS,
    HumanLabelInterval,
    Label,
    LabelValidity,
    SecondReference,
    TrainLabel,
)

SECOND_MAJORITY_MS = 500
"""Saniye için "yarıdan fazla" eşiği (§5.2)."""


@dataclass(frozen=True, slots=True)
class Coverage:
    """Bir zaman aralığında her etiketin kapladığı süre (ms)."""

    span_ms: int
    by_label: dict[Label, int]

    @property
    def uncertain_ms(self) -> int:
        return self.by_label.get(Label.BELIRSIZ, 0)

    @property
    def unlabeled_ms(self) -> int:
        return self.span_ms - sum(self.by_label.values())

    @property
    def unknown_ms(self) -> int:
        """BELIRSIZ + UNLABELED."""
        return self.uncertain_ms + self.unlabeled_ms

    def majority_class(self, more_than_ms: int) -> Label | None:
        """`more_than_ms`'den fazla kaplayan ana sınıf (varsa)."""
        for lab in MAIN_CLASSES:
            if self.by_label.get(lab, 0) > more_than_ms:
                return lab
        return None


def coverage(intervals: Iterable[HumanLabelInterval], start_ms: int, end_ms: int) -> Coverage:
    """[start_ms, end_ms) içinde etiketlerin kapladığı süre. Aralıklar çakışmamalıdır."""
    if end_ms <= start_ms:
        raise ValueError(f"Geçersiz aralık: [{start_ms}, {end_ms})")
    by_label: dict[Label, int] = {}
    for iv in intervals:
        overlap = min(iv.end_ms, end_ms) - max(iv.start_ms, start_ms)
        if overlap > 0:
            by_label[iv.label] = by_label.get(iv.label, 0) + overlap
    return Coverage(span_ms=end_ms - start_ms, by_label=by_label)


def second_references(
    intervals: Sequence[HumanLabelInterval],
    session_duration_ms: int,
) -> list[SecondReference]:
    """Oturumun her [s, s+1000) saniyesi için tekil referans (§5.2).

    - Bir ana sınıf 500 ms'den fazla → o sınıf (LABELED).
    - BELIRSIZ + UNLABELED ≥ 500 ms → BELIRSIZ; `validity`, hangisi uzunsa UNCERTAIN
      (ELAN'da BELIRSIZ) veya UNLABELED (etiketlenmemiş süre).
    - Diğer durumlar (ör. 500/500) → GECIS (LABELED).

    Saniye sayısı `ceil(süre / 1000)`'dir; son eksik saniyenin oturum dışındaki kısmı
    UNLABELED sayılır (TimelineResolver ile aynı saniye ızgarası).
    """
    if session_duration_ms <= 0:
        raise ValueError("session_duration_ms pozitif olmalı")
    ivs = list(intervals)
    if not ivs:
        raise ValueError("En az bir etiket aralığı gerekli")
    first = ivs[0]
    for iv in ivs:
        if (iv.session_id, iv.annotator_id, iv.label_round) != (
            first.session_id,
            first.annotator_id,
            first.label_round,
        ):
            raise ValueError("Aralıklar tek oturum, tek etiketleyici ve tek tura ait olmalı")
        if iv.end_ms > session_duration_ms:
            raise ValueError(f"Etiket oturum süresini aşıyor: [{iv.start_ms}, {iv.end_ms})")

    refs: list[SecondReference] = []
    for sec in range(math.ceil(session_duration_ms / SECOND_MS)):
        start = sec * SECOND_MS
        cov = coverage(ivs, start, start + SECOND_MS)
        majority = cov.majority_class(SECOND_MAJORITY_MS)
        if majority is not None:
            label, validity = majority, LabelValidity.LABELED
        elif cov.unknown_ms >= SECOND_MAJORITY_MS:
            label = Label.BELIRSIZ
            validity = (
                LabelValidity.UNCERTAIN
                if cov.uncertain_ms >= cov.unlabeled_ms
                else LabelValidity.UNLABELED
            )
        else:
            label, validity = Label.GECIS, LabelValidity.LABELED
        refs.append(
            SecondReference(
                session_id=first.session_id,
                second_start_ms=start,
                label=label,
                validity=validity,
                annotator_id=first.annotator_id,
                label_round=first.label_round,
                label_version=first.label_version,
            )
        )
    return refs


def window_train_label(
    intervals: Iterable[HumanLabelInterval],
    start_ms: int,
    end_ms: int,
) -> TrainLabel:
    """Bir pencerenin M1 eğitim hedefi (§5.3). Pencereleme (P4-06) bu fonksiyonu kullanır.

    1. BELIRSIZ + UNLABELED ≥ pencerenin yarısı → UNUSED (eğitimde kullanılmaz).
    2. Bir ana sınıf yarıdan fazla → o sınıf.
    3. Aksi halde → GECIS (eğitimden çıkarılır).
    """
    cov = coverage(intervals, start_ms, end_ms)
    half = cov.span_ms / 2
    if cov.unknown_ms >= half:
        return TrainLabel.UNUSED
    for lab in MAIN_CLASSES:
        if cov.by_label.get(lab, 0) > half:
            return TrainLabel(lab.value)
    return TrainLabel.GECIS
