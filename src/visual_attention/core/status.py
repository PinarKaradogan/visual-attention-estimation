"""Kayıtlarda kullanılan sabit durum değerleri (docs/data-schema.md v0.2, §3.3–3.6.1)."""

from __future__ import annotations

from enum import StrEnum


class FaceStatus(StrEnum):
    """Yüz bileşeninin bir karedeki durumu. "Yüz yok" ile "düşük güven" ayrıdır."""

    VALID = "VALID"
    NOT_DETECTED = "NOT_DETECTED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    OCCLUDED = "OCCLUDED"


class HandStatus(StrEnum):
    """El bileşeninin bir karedeki durumu."""

    VALID = "VALID"
    NOT_DETECTED = "NOT_DETECTED"
    OCCLUDED = "OCCLUDED"
    NOT_EVALUATED = "NOT_EVALUATED"


class PhoneStatus(StrEnum):
    """Telefon bileşeninin bir karedeki durumu. NOT_VISIBLE "ortamda yok" demek değildir."""

    VISIBLE = "VISIBLE"
    NOT_VISIBLE = "NOT_VISIBLE"
    OCCLUDED = "OCCLUDED"
    NOT_EVALUATED = "NOT_EVALUATED"


class TrainLabel(StrEnum):
    """Pencerenin M1 eğitim hedefi (labeling-protocol.md §5.3).

    GECIS ve UNUSED eğitime girmez.
    """

    MATERYAL = "MATERYAL"
    TELEFON = "TELEFON"
    DIS_YON = "DIS_YON"
    GECIS = "GECIS"
    UNUSED = "UNUSED"

    @property
    def is_trainable(self) -> bool:
        return self not in (TrainLabel.GECIS, TrainLabel.UNUSED)


class LabelValidity(StrEnum):
    """1 sn referansta belirsizliğin kaynağı (labeling-protocol.md §5.2)."""

    LABELED = "LABELED"
    UNCERTAIN = "UNCERTAIN"
    UNLABELED = "UNLABELED"


class LabelRound(StrEnum):
    """Etiket turu: ilk (r1), tekrar (r2), nihai referans (final)."""

    R1 = "r1"
    R2 = "r2"
    FINAL = "final"


class AgreementStatus(StrEnum):
    """Tekrar setindeki saniyelerde r1–r2 karşılaştırması."""

    AGREE = "AGREE"
    DISAGREE = "DISAGREE"
    NOT_IN_RETEST = "NOT_IN_RETEST"


class EventSource(StrEnum):
    """Kesinti olayının üretildiği zaman çizelgesi."""

    MODEL = "MODEL"
    REFERENCE = "REFERENCE"
