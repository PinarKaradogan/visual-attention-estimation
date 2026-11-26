"""LOSO değerlendirmesi: her katlamada eğit, test kişisinin oturumlarını 1 sn'ye çevir, ölç.

Akış (v5 §2.7): pencere tahmini → TimelineResolver (trp-0.1.0) → 1 sn karar → insan 1 sn
referansıyla karşılaştırma. Senaryolu ve serbest oturum sonuçları ayrı satırlardır; serbest
oturum hataları ayrı raporlanır.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from visual_attention.core.labels import Label
from visual_attention.core.records import WindowRecord
from visual_attention.methods.baselines import WindowModel
from visual_attention.methods.loso import check_no_leakage, loso_folds, participant_of
from visual_attention.methods.scoring import coverage, macro_f1
from visual_attention.metrics.session import SessionErrors, compare_sessions
from visual_attention.timeline.resolver import resolve_timeline


@dataclass(frozen=True)
class SessionData:
    """Bir oturumun model girdisi (pencereler) ve insan 1 sn referansı."""

    session_id: str
    duration_ms: int
    windows: tuple[WindowRecord, ...]
    reference: tuple[Label, ...]

    @property
    def participant_id(self) -> str:
        return participant_of(self.session_id)

    @property
    def session_type(self) -> str:
        return self.session_id.partition("_")[2]

    def __post_init__(self) -> None:
        if any(w.session_id != self.session_id for w in self.windows):
            raise ValueError(f"{self.session_id}: başka oturuma ait pencere var")


@dataclass(frozen=True)
class SessionResult:
    model_id: str
    test_participant: str
    session_id: str
    session_type: str
    macro_f1: float | None
    coverage: float | None
    errors: SessionErrors
    predicted: tuple[Label, ...]
    params: dict[str, object] = field(default_factory=dict)

    @property
    def belirsiz_ratio(self) -> float:
        return self.errors.predicted.belirsiz_ratio


def evaluate_session(model: WindowModel, session: SessionData) -> tuple[Label, ...]:
    """Eğitilmiş modeli bir oturuma uygular; 1 sn karar etiketlerini döndürür."""
    preds = model.predict(session.windows)
    decisions = resolve_timeline(preds, session.duration_ms)
    labels = tuple(d.label for d in decisions)
    if len(labels) != len(session.reference):
        raise ValueError(
            f"{session.session_id}: karar {len(labels)} sn, referans {len(session.reference)} sn"
        )
    return labels


def run_loso(
    sessions: Sequence[SessionData],
    model_factory: Callable[[], WindowModel],
) -> list[SessionResult]:
    """Dış LOSO: her kişi için yeni model eğitilir, yalnızca o kişinin oturumlarında ölçülür."""
    by_person: dict[str, list[SessionData]] = {}
    for s in sessions:
        by_person.setdefault(s.participant_id, []).append(s)

    results: list[SessionResult] = []
    for fold in loso_folds(by_person):
        train_windows = [
            w for p in fold.train_participants for s in by_person[p] for w in s.windows
        ]
        check_no_leakage(
            fold.test_participant, {participant_of(w.session_id) for w in train_windows}
        )
        model = model_factory()
        model.fit(train_windows)
        params = dict(getattr(model, "params", {}))
        for s in sorted(by_person[fold.test_participant], key=lambda x: x.session_id):
            pred = evaluate_session(model, s)
            results.append(
                SessionResult(
                    model_id=model.model_id,
                    test_participant=fold.test_participant,
                    session_id=s.session_id,
                    session_type=s.session_type,
                    macro_f1=macro_f1(s.reference, pred, covered_only=True),
                    coverage=coverage(s.reference, pred),
                    errors=compare_sessions(s.reference, pred),
                    predicted=pred,
                    params=params,
                )
            )
    return results
