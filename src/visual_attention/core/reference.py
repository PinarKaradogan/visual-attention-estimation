"""İnsan referansı tarafı kayıtları: etiket aralığı, 1 sn referans ve kesinti olayı.

Karşılık geldiği belgeler: docs/data-schema.md v0.2 (§3.5, §3.6.1) ve
docs/labeling-protocol.md (§5–7).
"""

from __future__ import annotations

from dataclasses import dataclass

from visual_attention.core.constants import INTERRUPTION_MIN_S, SECOND_MS
from visual_attention.core.labels import MODEL_OUTPUTS, NON_MATERIAL_CLASSES, Label
from visual_attention.core.records import check_interval, coerce_enum
from visual_attention.core.status import AgreementStatus, EventSource, LabelRound, LabelValidity

HUMAN_INTERVAL_LABELS: tuple[Label, ...] = MODEL_OUTPUTS
"""ELAN kontrollü sözlüğü: MATERYAL, TELEFON, DIS_YON, BELIRSIZ (GECIS etiketlenmez)."""


@dataclass(frozen=True, slots=True)
class HumanLabelInterval:
    """İnsan gözlemcinin ELAN'daki bir zaman aralığı etiketi."""

    session_id: str
    annotator_id: str
    label_round: LabelRound
    start_ms: int
    end_ms: int
    label: Label
    label_version: str

    def __post_init__(self) -> None:
        coerce_enum(self, "label_round", LabelRound)
        coerce_enum(self, "label", Label)
        check_interval(self.start_ms, self.end_ms, "etiket aralığı")
        if not self.annotator_id:
            raise ValueError("annotator_id boş olamaz")
        if self.label not in HUMAN_INTERVAL_LABELS:
            raise ValueError(f"ELAN etiketi {self.label} olamaz; GECIS hesaplanır, etiketlenmez")

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


@dataclass(frozen=True, slots=True)
class SecondReference:
    """LabelAligner'ın ürettiği tekil 1 sn referans.

    BELIRSIZ saniyelerde `validity` kaynağı ayırır: UNCERTAIN (ELAN'da BELIRSIZ) veya
    UNLABELED (hiçbir aralığa düşmeyen süre). Ana sınıf ve GECIS saniyeleri LABELED'dır.
    """

    session_id: str
    second_start_ms: int
    label: Label
    validity: LabelValidity
    annotator_id: str
    label_round: LabelRound
    label_version: str
    agreement_status: AgreementStatus = AgreementStatus.NOT_IN_RETEST

    def __post_init__(self) -> None:
        coerce_enum(self, "label", Label)
        coerce_enum(self, "validity", LabelValidity)
        coerce_enum(self, "label_round", LabelRound)
        coerce_enum(self, "agreement_status", AgreementStatus)
        if self.second_start_ms < 0 or self.second_start_ms % SECOND_MS:
            raise ValueError(f"second_start_ms saniye sınırında olmalı: {self.second_start_ms}")
        uncertain = self.label is Label.BELIRSIZ
        if uncertain == (self.validity is LabelValidity.LABELED):
            raise ValueError(f"label={self.label} ile validity={self.validity} uyumsuz")

    @property
    def second_index(self) -> int:
        return self.second_start_ms // SECOND_MS


@dataclass(frozen=True, slots=True)
class InterruptionEvent:
    """Görünür kesinti: aynı MATERYAL dışı sınıfın aralıksız en az eşik süresi kadar sürmesi."""

    session_id: str
    label: Label
    start_ms: int
    end_ms: int
    source: EventSource
    model_id: str | None = None
    threshold_ms: int = INTERRUPTION_MIN_S * SECOND_MS

    def __post_init__(self) -> None:
        coerce_enum(self, "label", Label)
        coerce_enum(self, "source", EventSource)
        check_interval(self.start_ms, self.end_ms, "kesinti")
        if self.label not in NON_MATERIAL_CLASSES:
            raise ValueError(f"Kesinti sınıfı TELEFON veya DIS_YON olmalı: {self.label}")
        if self.start_ms % SECOND_MS or self.end_ms % SECOND_MS:
            raise ValueError("Kesinti sınırları 1 sn dilim sınırlarında olmalı")
        if self.threshold_ms <= 0:
            raise ValueError("threshold_ms pozitif olmalı")
        if self.end_ms - self.start_ms < self.threshold_ms:
            raise ValueError("Kesinti süresi eşikten kısa olamaz")
        if (self.source is EventSource.MODEL) != (self.model_id is not None):
            raise ValueError("model_id yalnızca MODEL kaynaklı olaylarda verilir")

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms
