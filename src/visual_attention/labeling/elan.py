"""ELAN dışa aktarımlarını okuma ve doğrulama (docs/labeling-protocol.md §3–4).

Dosya biçimi: sekme ayrımlı metin, başlık satırı `start_ms`, `end_ms`, `label`.
Dosya adı: `<katılımcı>_<oturum>_<tur>_<etiketleyici>.tsv`, ör. `P03_SCENARIO_r1_A1.tsv`.

Kurallar:
- Etiket yalnız kontrollü sözlükten olabilir: MATERYAL, TELEFON, DIS_YON, BELIRSIZ.
- Aralıklar çakışamaz (tek `davranis` katmanı).
- 0,5 sn'den kısa aralık hata değil, uyarıdır (protokol §4.2 madde 4).
- Hiçbir aralığa düşmeyen süre UNLABELED sayılır; burada doldurulmaz.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from visual_attention.core import HUMAN_INTERVAL_LABELS, HumanLabelInterval, Label, LabelRound

MIN_INTERVAL_MS = 500
"""Etiketlenecek en kısa aralık (protokol §4.2 madde 4)."""

ELAN_COLUMNS = ("start_ms", "end_ms", "label")

_FILENAME = re.compile(
    r"^(?P<participant>P\d{2,})_(?P<session>SCENARIO|FREE)_"
    r"(?P<round>r1|r2|final)_(?P<annotator>A\d+)\.tsv$"
)


class SessionType(StrEnum):
    SCENARIO = "SCENARIO"
    FREE = "FREE"


@dataclass(frozen=True, slots=True)
class ElanFileInfo:
    """Dosya adından çıkarılan bilgiler. Kişiyi tanımlayan bilgi içermez."""

    participant_id: str
    session_type: SessionType
    label_round: LabelRound
    annotator_id: str

    @property
    def session_id(self) -> str:
        return f"{self.participant_id}_{self.session_type}"


@dataclass(frozen=True, slots=True)
class ElanFile:
    info: ElanFileInfo
    intervals: tuple[HumanLabelInterval, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)


def parse_elan_filename(path: str | Path) -> ElanFileInfo:
    name = Path(path).name
    m = _FILENAME.match(name)
    if m is None:
        raise ValueError(
            f"Dosya adı protokole uymuyor: {name} (beklenen ör. P03_SCENARIO_r1_A1.tsv)"
        )
    return ElanFileInfo(
        participant_id=m["participant"],
        session_type=SessionType(m["session"]),
        label_round=LabelRound(m["round"]),
        annotator_id=m["annotator"],
    )


def read_elan_tsv(path: str | Path, label_version: str) -> ElanFile:
    """ELAN dışa aktarımını okur, doğrular ve başlangıca göre sıralı aralıklar döndürür.

    Raises:
        ValueError: Dosya adı, başlık, sayı biçimi, etiket ya da aralık çakışması hatalıysa.
    """
    info = parse_elan_filename(path)
    with Path(path).open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        if header is None or tuple(h.strip() for h in header) != ELAN_COLUMNS:
            raise ValueError(f"Başlık {ELAN_COLUMNS} olmalı: {header}")
        rows = [(i, row) for i, row in enumerate(reader, start=2) if any(c.strip() for c in row)]

    intervals: list[HumanLabelInterval] = []
    for line, row in rows:
        if len(row) != 3:
            raise ValueError(f"{line}. satır 3 sütun olmalı: {row}")
        try:
            start_ms, end_ms = int(row[0]), int(row[1])
        except ValueError as e:
            raise ValueError(f"{line}. satırda milisaniye tam sayı olmalı: {row}") from e
        label = row[2].strip()
        if label not in {lab.value for lab in HUMAN_INTERVAL_LABELS}:
            raise ValueError(f"{line}. satırda kontrollü sözlük dışı etiket: {label!r}")
        intervals.append(
            HumanLabelInterval(
                session_id=info.session_id,
                annotator_id=info.annotator_id,
                label_round=info.label_round,
                start_ms=start_ms,
                end_ms=end_ms,
                label=Label(label),
                label_version=label_version,
            )
        )

    intervals.sort(key=lambda iv: iv.start_ms)
    warnings = validate_intervals(intervals)
    return ElanFile(info=info, intervals=tuple(intervals), warnings=tuple(warnings))


def validate_intervals(intervals: list[HumanLabelInterval]) -> list[str]:
    """Sıralı aralıklarda çakışmayı reddeder; kısa aralıklar için uyarı listesi döndürür."""
    warnings: list[str] = []
    for prev, cur in zip(intervals, intervals[1:], strict=False):
        if cur.start_ms < prev.end_ms:
            raise ValueError(
                f"Aralıklar çakışıyor: [{prev.start_ms}, {prev.end_ms}) {prev.label} ve "
                f"[{cur.start_ms}, {cur.end_ms}) {cur.label}"
            )
    for iv in intervals:
        if iv.duration_ms < MIN_INTERVAL_MS:
            warnings.append(
                f"{iv.duration_ms} ms'lik kısa aralık: [{iv.start_ms}, {iv.end_ms}) {iv.label}"
            )
    return warnings
