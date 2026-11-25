"""Yerel öznitelik deposu (P4-05; architecture §4.2, data-schema §4).

Türetilmiş öznitelikler `local_data/derived_features/<feature_version>/<session_id>.csv`
dosyasına, yanında bir `.meta.json` ile yazılır. `local_data/` Git tarafından yok sayılır.

- Ham kare, görüntü veya tam landmark koordinatı yazılmaz; yalnız `FeatureRecord` alanları.
- Depo kökü `local_data` adlı bir klasörün altında olmalıdır (yanlışlıkla depoya veri yazmayı
  önlemek için); testler `allow_outside_local_data=True` ile geçici klasör kullanır.
- Var olan dosyanın üzerine `overwrite=True` verilmeden yazılmaz.
- Gerçek gönüllü öznitelikleri ancak etik izin ve veri minimizasyonu kararından sonra yazılır.
"""

from __future__ import annotations

import csv
import dataclasses
import json
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from visual_attention.core import FeatureRecord, ValidityFlags

DEFAULT_ROOT = Path("local_data/derived_features")
SCHEMA_VERSION = "0.2.0"

_FLAG_FIELDS = [f.name for f in dataclasses.fields(ValidityFlags)]
_RECORD_FIELDS = [f.name for f in dataclasses.fields(FeatureRecord) if f.name != "validity_flags"]
COLUMNS = _RECORD_FIELDS + _FLAG_FIELDS
_INT_FIELDS = {"frame_index", "timestamp_ms", "hand_count"}
_STR_FIELDS = {"session_id", "feature_version", "face_status", "hand_status", "phone_status"}
_BOOL_FIELDS = {"hand_phone_overlap", *_FLAG_FIELDS}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.+\-]+$")


def _to_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def _from_cell(name: str, cell: str) -> Any:
    if name in _STR_FIELDS:
        return cell
    if cell == "":
        return False if name in _FLAG_FIELDS else None
    if name in _BOOL_FIELDS:
        return cell == "1"
    if name in _INT_FIELDS:
        return int(cell)
    return float(cell)


class FeatureStore:
    def __init__(
        self, root: str | Path = DEFAULT_ROOT, *, allow_outside_local_data: bool = False
    ) -> None:
        self.root = Path(root)
        if not allow_outside_local_data and "local_data" not in self.root.resolve().parts:
            raise ValueError(f"Öznitelik deposu local_data/ altında olmalı: {self.root}")

    def path_for(self, feature_version: str, session_id: str) -> Path:
        for value in (feature_version, session_id):
            if not _SAFE_NAME.match(value):
                raise ValueError(f"Dosya adına uygun olmayan değer: {value!r}")
        return self.root / feature_version / f"{session_id}.csv"

    def write(
        self,
        records: Iterable[FeatureRecord],
        *,
        meta: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Tek oturumun kayıtlarını yazar ve dosya yolunu döndürür."""
        rows = list(records)
        if not rows:
            raise ValueError("Yazılacak kayıt yok")
        session_ids = {r.session_id for r in rows}
        versions = {r.feature_version for r in rows}
        if len(session_ids) != 1 or len(versions) != 1:
            raise ValueError("Kayıtlar tek oturum ve tek feature_version'a ait olmalı")
        session_id, feature_version = session_ids.pop(), versions.pop()
        path = self.path_for(feature_version, session_id)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Dosya zaten var (overwrite=True ile yazılır): {path}")
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)
            for r in rows:
                values = [getattr(r, name) for name in _RECORD_FIELDS]
                flags = [getattr(r.validity_flags, name) for name in _FLAG_FIELDS]
                writer.writerow([_to_cell(v) for v in values + flags])

        info = {
            "session_id": session_id,
            "feature_version": feature_version,
            "schema_version": SCHEMA_VERSION,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "n_records": len(rows),
            **(meta or {}),
        }
        path.with_suffix(".meta.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        return path

    def read(self, feature_version: str, session_id: str) -> list[FeatureRecord]:
        path = self.path_for(feature_version, session_id)
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != COLUMNS:
                raise ValueError(f"Beklenmeyen sütunlar: {reader.fieldnames}")
            records = []
            for row in reader:
                values = {name: _from_cell(name, row[name]) for name in COLUMNS}
                flags = ValidityFlags(**{name: values.pop(name) for name in _FLAG_FIELDS})
                records.append(FeatureRecord(validity_flags=flags, **values))
        return records

    def read_meta(self, feature_version: str, session_id: str) -> dict[str, Any]:
        path = self.path_for(feature_version, session_id).with_suffix(".meta.json")
        return json.loads(path.read_text(encoding="utf-8"))
