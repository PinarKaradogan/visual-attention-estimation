"""TimelineResolver — örtüşen pencere tahminlerinden tekil saniye kararlarına geçiş.

Politika trp-0.1.0 (docs/architecture.md §4.1):

1. Oturum, örtüşmeyen 1 sn dilimlere bölünür; her dilim için tam olarak bir karar üretilir.
2. Tamamlanmış [t-2000, t) penceresinin tahmini yalnızca son [t-1000, t) dilimine atanır.
   Böylece hiçbir saniye iki kez oylanmaz ve süre iki kez sayılmaz.
3. İlk [0, 1000) dilimi, [0, 2000) penceresi bir ana sınıf verdiyse onun etiketiyle
   doldurulur (bootstrap); aksi hâlde BELIRSIZ kalır.
4. Pencere tahmini olmayan dilim BELIRSIZ olur (UNCOVERED). Komşu pencerenin kararı
   boşluğu kapatmak için kaydırılmaz; eksik kanıt hiçbir zaman MATERYAL sayılmaz.

Aynı fonksiyon hem model tahminlerine hem de pencere düzeyinde referansa uygulanabilir.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from enum import StrEnum

from visual_attention.core.constants import (
    RESOLUTION_POLICY_VERSION,
    SECOND_MS,
    WINDOW_MS,
)
from visual_attention.core.labels import Label
from visual_attention.core.records import Prediction, SecondDecision


class DecisionReason(StrEnum):
    WINDOW = "WINDOW"
    BOOTSTRAP = "BOOTSTRAP"
    WINDOW_BELIRSIZ = "WINDOW_BELIRSIZ"
    UNCOVERED = "UNCOVERED"


def resolve_timeline(
    predictions: Iterable[Prediction],
    session_duration_ms: int,
) -> list[SecondDecision]:
    """Bir oturumun pencere tahminlerini 1 sn'lik zaman çizelgesine çevirir.

    Args:
        predictions: Tek oturuma ve tek modele ait pencere tahminleri (sırası önemsiz).
        session_duration_ms: Oturumun video zamanındaki süresi. Son eksik saniye de bir
            dilim olarak üretilir (kapsanmıyorsa UNCOVERED).

    Returns:
        second_start_ms'e göre sıralı, boşluksuz SecondDecision listesi.

    Raises:
        ValueError: Pencere uzunluğu 2 sn değilse, saniye sınırına oturmuyorsa,
            oturum süresini aşıyorsa, farklı oturum/model karışmışsa veya aynı
            saniyeyi iki pencere hedefliyorsa.
    """
    if session_duration_ms <= 0:
        raise ValueError("session_duration_ms pozitif olmalı")

    preds = list(predictions)
    n_seconds = math.ceil(session_duration_ms / SECOND_MS)
    session_id = _single_value(preds, "session_id")
    _single_value(preds, "model_id")

    by_target_second: dict[int, Prediction] = {}
    for p in preds:
        if p.end_ms - p.start_ms != WINDOW_MS:
            raise ValueError(f"Pencere {WINDOW_MS} ms olmalı: {p}")
        if p.start_ms % SECOND_MS != 0:
            raise ValueError(f"Pencere saniye sınırında başlamalı: {p}")
        if p.end_ms > session_duration_ms:
            raise ValueError(f"Pencere oturum süresini aşıyor: {p}")
        target = (p.end_ms - SECOND_MS) // SECOND_MS
        if target in by_target_second:
            raise ValueError(f"{target}. saniyeyi birden fazla pencere hedefliyor")
        by_target_second[target] = p

    decisions: list[SecondDecision] = []
    for sec in range(n_seconds):
        pred = by_target_second.get(sec)
        reason = DecisionReason.WINDOW
        if pred is None and sec == 0:
            first = by_target_second.get(1)
            if first is not None and first.start_ms == 0 and first.label.is_main_class:
                pred, reason = first, DecisionReason.BOOTSTRAP

        if pred is None:
            decisions.append(
                SecondDecision(
                    session_id=session_id or "",
                    second_start_ms=sec * SECOND_MS,
                    label=Label.BELIRSIZ,
                    resolution_policy_version=RESOLUTION_POLICY_VERSION,
                    reason=DecisionReason.UNCOVERED,
                )
            )
            continue

        if pred.label is Label.BELIRSIZ:
            reason = DecisionReason.WINDOW_BELIRSIZ
        decisions.append(
            SecondDecision(
                session_id=pred.session_id,
                second_start_ms=sec * SECOND_MS,
                label=pred.label,
                resolution_policy_version=RESOLUTION_POLICY_VERSION,
                source_window_start_ms=pred.start_ms,
                source_window_end_ms=pred.end_ms,
                reason=reason,
            )
        )
    return decisions


def _single_value(preds: list[Prediction], field: str) -> str | None:
    values = {getattr(p, field) for p in preds}
    if len(values) > 1:
        raise ValueError(f"Tahminlerde birden fazla {field} var: {sorted(values)}")
    return next(iter(values), None)
