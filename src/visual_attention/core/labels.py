"""Görsel dikkat durumu sınıfları.

Kod içi değerler ASCII'dir; raporlarda `display_name` kullanılır.

- Ana sınıflar: MATERYAL, TELEFON, DIS_YON.
- BELIRSIZ: görsel kanıtın yetersiz olduğu kesit. Dördüncü bir dikkat durumu sınıfı
  değildir; sınıflandırmanın kapsama sınırıdır (öneri v5 §1.2, Ek-2).
- GECIS: yalnızca insan referansında görülür. 1 sn'lik referansta iki sınıfın 500/500
  eşit kapladığı saniyedir (docs/labeling-protocol.md §5.2). Modeller GECIS üretmez.

BELIRSIZ ve GECIS saniyeleri geçerli süre sayılmaz: odak oranının paydasına girmez ve
bir kesintiyi böler.
"""

from __future__ import annotations

from enum import StrEnum


class Label(StrEnum):
    MATERYAL = "MATERYAL"
    TELEFON = "TELEFON"
    DIS_YON = "DIS_YON"
    BELIRSIZ = "BELIRSIZ"
    GECIS = "GECIS"

    @property
    def display_name(self) -> str:
        return _DISPLAY[self]

    @property
    def is_main_class(self) -> bool:
        return self in MAIN_CLASSES


_DISPLAY = {
    Label.MATERYAL: "MATERYAL",
    Label.TELEFON: "TELEFON",
    Label.DIS_YON: "DIŞ_YÖN",
    Label.BELIRSIZ: "BELİRSİZ",
    Label.GECIS: "GEÇİŞ",
}

MAIN_CLASSES: tuple[Label, ...] = (Label.MATERYAL, Label.TELEFON, Label.DIS_YON)
NON_MATERIAL_CLASSES: tuple[Label, ...] = (Label.TELEFON, Label.DIS_YON)
MODEL_OUTPUTS: tuple[Label, ...] = (*MAIN_CLASSES, Label.BELIRSIZ)
"""M0 ve M1'in üretebileceği değerler; GECIS bunlara dahil değildir."""
