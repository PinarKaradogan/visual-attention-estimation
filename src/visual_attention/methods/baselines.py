"""Pencere modelleri için ortak arayüz, çoğunluk-sınıf tabanı ve M0 kural tabanlı yöntem.

Kaynak: öneri v5 §2.6 (yöntem tablosu, BELİRSİZ kuralı), §2.7 (LOSO); docs/data-schema.md
§3.4 (`WindowRecord.aggregates` adları) ve §3.6 (`Prediction` gerekçe kodları).

Çoğunluk tabanı: eğitim pencerelerinde en sık ana sınıfı öğrenir, her pencereye onu verir.

M0 (şeffaf eşik sistemi), kurallar sırayla uygulanır:
1. Pencere geçersizse → BELIRSIZ (INVALID_WINDOW); eksik kanıt MATERYAL sayılmaz.
2. Yüz tespit oranı < 0,5 → BELIRSIZ (LOW_FACE_RATIO). 0,5 raporda sabittir, öğrenilmez.
3. Telefon kuralı: telefon puanı ortalaması ≥ τ_telefon VE elin telefon kutusunda olma
   oranı ≥ τ_örtüşme.
4. Dış yön kuralı: |baş yaw ortalaması| ≥ τ_yaw.
5. İkisi birden tutarsa → BELIRSIZ (RULE_CONFLICT); yalnız biri tutarsa o sınıf;
   hiçbiri tutmazsa → MATERYAL.

Üç eşik (τ_yaw, τ_telefon, τ_örtüşme) yalnızca eğitim kişilerinden seçilir: aday değerler
eğitim pencerelerinin yüzdeliklerinden üretilir; kişi gruplu iç katlamalarda doğrulama
kişilerinin kişi başına makro-F1 ortalaması en yüksek olan üçlü seçilir. Test kişisi bu
aşamada görülmez.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from visual_attention.core.labels import MAIN_CLASSES, Label
from visual_attention.core.records import Prediction, WindowRecord
from visual_attention.methods.loso import DEFAULT_INNER_SPLITS, inner_group_folds, participant_of

MAJORITY_MODEL_ID = "MAJORITY"
M0_MODEL_ID = "M0"
M0_VERSION = "m0-0.1.0"

FACE_RATIO_MIN = 0.5
"""v5 §2.6: yüz tespit oranı pencerenin %50'sinin altındaysa BELIRSIZ (sabit)."""

YAW_KEY = "head_yaw_deg_mean"
PHONE_KEY = "phone_score_mean"
OVERLAP_KEY = "hand_phone_overlap_ratio"

REASON_INVALID = "INVALID_WINDOW"
REASON_LOW_FACE = "LOW_FACE_RATIO"
REASON_CONFLICT = "RULE_CONFLICT"
REASON_RULE = "RULE"
REASON_MAJORITY = "MAJORITY"

QUANTILES = tuple(q / 10 for q in range(1, 10))


class WindowModel(Protocol):
    model_id: str

    def fit(self, windows: Sequence[WindowRecord]) -> None: ...

    def predict(self, windows: Sequence[WindowRecord]) -> list[Prediction]: ...


def trainable(windows: Sequence[WindowRecord]) -> list[WindowRecord]:
    """Eğitim hedefi ana sınıf olan pencereler (GECIS, UNUSED ve etiketsizler hariç)."""
    return [w for w in windows if w.train_label is not None and w.train_label.is_trainable]


def _prediction(w: WindowRecord, model_id: str, label: Label, reason: str) -> Prediction:
    return Prediction(
        session_id=w.session_id,
        window_index=w.window_index,
        start_ms=w.start_ms,
        end_ms=w.end_ms,
        model_id=model_id,
        label=label,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Çoğunluk-sınıf tabanı
# ---------------------------------------------------------------------------


class MajorityBaseline:
    model_id = MAJORITY_MODEL_ID

    def __init__(self) -> None:
        self.label: Label | None = None

    def fit(self, windows: Sequence[WindowRecord]) -> None:
        counts = Counter(Label(w.train_label.value) for w in trainable(windows))
        if not counts:
            raise ValueError("Çoğunluk tabanı için eğitim hedefi olan pencere yok")
        # Eşitlikte sabit sıra: MATERYAL, TELEFON, DIS_YON
        self.label = max(MAIN_CLASSES, key=lambda c: (counts.get(c, 0), -MAIN_CLASSES.index(c)))

    def predict(self, windows: Sequence[WindowRecord]) -> list[Prediction]:
        if self.label is None:
            raise RuntimeError("Önce fit çağrılmalı")
        return [_prediction(w, self.model_id, self.label, REASON_MAJORITY) for w in windows]

    @property
    def params(self) -> dict[str, object]:
        return {"label": None if self.label is None else self.label.value}


# ---------------------------------------------------------------------------
# M0
# ---------------------------------------------------------------------------

# Vektör hesapta sınıf kodları
_MAT, _TEL, _DIS, _BEL = 0, 1, 2, 3
_CODE_TO_LABEL = {_MAT: Label.MATERYAL, _TEL: Label.TELEFON, _DIS: Label.DIS_YON}
_LABEL_TO_CODE = {v: k for k, v in _CODE_TO_LABEL.items()}


@dataclass(frozen=True, slots=True)
class M0Thresholds:
    yaw_deg: float
    phone_score: float
    overlap_ratio: float
    face_ratio_min: float = FACE_RATIO_MIN


def _nan(v: float | None) -> float:
    return np.nan if v is None else float(v)


@dataclass(frozen=True)
class _Arrays:
    valid: np.ndarray
    face: np.ndarray
    yaw: np.ndarray
    phone: np.ndarray
    overlap: np.ndarray

    @classmethod
    def of(cls, windows: Sequence[WindowRecord]) -> _Arrays:
        return cls(
            valid=np.array([w.is_valid for w in windows], dtype=bool),
            face=np.array([_nan(w.face_detected_ratio) for w in windows]),
            yaw=np.abs(np.array([_nan(w.aggregates.get(YAW_KEY)) for w in windows])),
            phone=np.array([_nan(w.aggregates.get(PHONE_KEY)) for w in windows]),
            overlap=np.array([_nan(w.aggregates.get(OVERLAP_KEY)) for w in windows]),
        )


def _apply_rules(a: _Arrays, t: M0Thresholds) -> tuple[np.ndarray, np.ndarray]:
    """(sınıf kodları, gerekçe kodları: 0 kural, 1 geçersiz, 2 yüz, 3 çelişki)."""
    with np.errstate(invalid="ignore"):
        no_face = ~(a.face >= t.face_ratio_min)  # NaN da düşük sayılır
        phone_rule = (a.phone >= t.phone_score) & (a.overlap >= t.overlap_ratio)
        away_rule = a.yaw >= t.yaw_deg
    codes = np.full(len(a.valid), _MAT, dtype=np.int8)
    codes[phone_rule] = _TEL
    codes[away_rule] = _DIS
    conflict = phone_rule & away_rule
    reasons = np.zeros(len(a.valid), dtype=np.int8)
    for mask, reason in ((conflict, 3), (no_face, 2), (~a.valid, 1)):
        codes[mask] = _BEL
        reasons[mask] = reason
    return codes, reasons


_REASONS = {0: REASON_RULE, 1: REASON_INVALID, 2: REASON_LOW_FACE, 3: REASON_CONFLICT}


def _candidates(values: np.ndarray, extra: tuple[float, ...] = ()) -> list[float]:
    finite = values[np.isfinite(values)]
    qs = np.quantile(finite, QUANTILES).tolist() if finite.size else []
    return sorted({round(float(v), 6) for v in (*extra, *qs)})


def _per_person_macro_f1(
    ref: np.ndarray, pred: np.ndarray, person: np.ndarray, n_persons: int
) -> np.ndarray:
    """Her kişi için makro-F1 (BELIRSIZ hata sayılır; yalnız kişide görülen sınıflar)."""
    f1_sum = np.zeros(n_persons)
    n_cls = np.zeros(n_persons)
    for c in (_MAT, _TEL, _DIS):
        is_ref = ref == c
        is_pred = pred == c
        tp = np.bincount(person, weights=is_ref & is_pred, minlength=n_persons)
        fp = np.bincount(person, weights=~is_ref & is_pred, minlength=n_persons)
        fn = np.bincount(person, weights=is_ref & ~is_pred, minlength=n_persons)
        present = np.bincount(person, weights=is_ref, minlength=n_persons) > 0
        denom = 2 * tp + fp + fn
        f1 = np.divide(2 * tp, denom, out=np.zeros(n_persons), where=denom > 0)
        f1_sum += np.where(present, f1, 0.0)
        n_cls += present
    return np.divide(f1_sum, n_cls, out=np.full(n_persons, np.nan), where=n_cls > 0)


class M0RuleModel:
    model_id = M0_MODEL_ID

    def __init__(
        self,
        thresholds: M0Thresholds | None = None,
        inner_splits: int = DEFAULT_INNER_SPLITS,
    ) -> None:
        self.thresholds = thresholds
        self.inner_splits = inner_splits
        self.selection_score: float | None = None

    def fit(self, windows: Sequence[WindowRecord]) -> None:
        train = trainable(windows)
        if not train:
            raise ValueError("M0 için eğitim hedefi olan pencere yok")
        a = _Arrays.of(train)
        ref = np.array([_LABEL_TO_CODE[Label(w.train_label.value)] for w in train], dtype=np.int8)
        groups = [participant_of(w.session_id) for w in train]
        persons = sorted(set(groups))
        person_idx = np.array([persons.index(g) for g in groups])
        folds = inner_group_folds(groups, self.inner_splits)
        val_persons = [sorted({person_idx[i] for i in va}) for _, va in folds]

        best: tuple[float, M0Thresholds] | None = None
        for yaw in _candidates(a.yaw):
            for phone in _candidates(a.phone):
                for overlap in _candidates(a.overlap, extra=(0.0,)):
                    t = M0Thresholds(yaw, phone, overlap)
                    pred, _ = _apply_rules(a, t)
                    per_person = _per_person_macro_f1(ref, pred, person_idx, len(persons))
                    fold_scores = [np.nanmean(per_person[vp]) for vp in val_persons]
                    score = float(np.mean(fold_scores))
                    if best is None or score > best[0]:
                        best = (score, t)
        assert best is not None
        self.selection_score, self.thresholds = best

    def predict(self, windows: Sequence[WindowRecord]) -> list[Prediction]:
        if self.thresholds is None:
            raise RuntimeError("Önce fit çağrılmalı ya da eşik verilmeli")
        codes, reasons = _apply_rules(_Arrays.of(windows), self.thresholds)
        return [
            _prediction(
                w,
                self.model_id,
                _CODE_TO_LABEL.get(int(c), Label.BELIRSIZ),
                _REASONS[int(r)],
            )
            for w, c, r in zip(windows, codes, reasons, strict=True)
        ]

    @property
    def params(self) -> dict[str, object]:
        t = self.thresholds
        return {
            "version": M0_VERSION,
            "yaw_deg": None if t is None else t.yaw_deg,
            "phone_score": None if t is None else t.phone_score,
            "overlap_ratio": None if t is None else t.overlap_ratio,
            "face_ratio_min": FACE_RATIO_MIN,
            "selection_macro_f1": self.selection_score,
        }
