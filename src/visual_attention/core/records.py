"""docs/data-schema.md §3.6 kayıtlarının Python karşılıkları.

Tüm zaman aralıkları oturum video zamanında, milisaniye ve yarı açık [start, end).
"""

from __future__ import annotations

from dataclasses import dataclass

from visual_attention.core.labels import MODEL_OUTPUTS, Label


@dataclass(frozen=True, slots=True)
class Prediction:
    """Bir 2 sn pencere için M0/M1 tahmini."""

    session_id: str
    window_index: int
    start_ms: int
    end_ms: int
    model_id: str
    label: Label
    score: float | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError(f"Geçersiz pencere aralığı: [{self.start_ms}, {self.end_ms})")
        if self.window_index < 0:
            raise ValueError("window_index negatif olamaz")
        if not isinstance(self.label, Label):
            object.__setattr__(self, "label", Label(self.label))
        if self.label not in MODEL_OUTPUTS:
            raise ValueError(
                f"Model tahmini {self.label} olamaz; GECIS yalnızca insan referansındadır"
            )


@dataclass(frozen=True, slots=True)
class SecondDecision:
    """Tekil 1 sn dilim için nihai karar. (session_id, second_start_ms) benzersizdir."""

    session_id: str
    second_start_ms: int
    label: Label
    resolution_policy_version: str
    source_window_start_ms: int | None = None
    source_window_end_ms: int | None = None
    reason: str = ""

    @property
    def second_index(self) -> int:
        return self.second_start_ms // 1_000
