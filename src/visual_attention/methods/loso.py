"""Kişi-bazlı katlamalar: dış LOSO ve eğitim kişileri içinde iç GroupKFold (v5 §2.7).

- Her dış katlamada bir katılımcının senaryolu ve serbest oturumlarının tümü testte kalır.
- Kural eşikleri, θ ve hiperparametreler yalnızca eğitim kişileriyle, kişi gruplu iç
  doğrulamayla seçilir; aynı kişinin pencereleri iki tarafa bölünmez.
- Katılımcı kodu oturum kodundan okunur: "<katılımcı>_<SCENARIO|FREE>".
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from sklearn.model_selection import GroupKFold

DEFAULT_INNER_SPLITS = 5


def participant_of(session_id: str) -> str:
    """'P03_SCENARIO' → 'P03'."""
    pid, sep, _ = session_id.partition("_")
    if not sep or not pid:
        raise ValueError(f"Oturum kodu '<katılımcı>_<oturum>' biçiminde olmalı: {session_id!r}")
    return pid


@dataclass(frozen=True, slots=True)
class Fold:
    test_participant: str
    train_participants: tuple[str, ...]

    def __post_init__(self) -> None:
        check_no_leakage(self.test_participant, self.train_participants)


def check_no_leakage(test_participant: str, train_participants: Iterable[str]) -> None:
    """LOSO değişmezi: test kişisi hiçbir zaman eğitimde olamaz."""
    if test_participant in set(train_participants):
        raise ValueError(f"Sızıntı: test katılımcısı {test_participant} eğitim kümesinde")


def loso_folds(participant_ids: Iterable[str]) -> list[Fold]:
    """Her katılımcı bir kez test olur; sıra kod sırasıdır (deterministik)."""
    pids = sorted(set(participant_ids))
    if len(pids) < 2:
        raise ValueError("LOSO için en az 2 katılımcı gerekli")
    return [Fold(p, tuple(q for q in pids if q != p)) for p in pids]


def inner_group_folds(
    groups: Sequence[str],
    n_splits: int = DEFAULT_INNER_SPLITS,
) -> list[tuple[list[int], list[int]]]:
    """Eğitim kişileri içinde kişi gruplu iç katlamalar (satır indeksleri).

    Kat sayısı kişi sayısını aşamaz. Tek kişi varsa iç doğrulama yapılamaz; o kişi hem
    seçimde hem doğrulamada kullanılır ve bu durum çağırana bırakılır (tek katlama).
    """
    unique = sorted(set(groups))
    if not unique:
        raise ValueError("İç katlama için en az bir satır gerekli")
    if len(unique) == 1:
        idx = list(range(len(groups)))
        return [(idx, idx)]
    k = min(n_splits, len(unique))
    splitter = GroupKFold(n_splits=k)
    dummy = [[0]] * len(groups)
    out: list[tuple[list[int], list[int]]] = []
    for train_idx, val_idx in splitter.split(dummy, groups=list(groups)):
        tr = [int(i) for i in train_idx]
        va = [int(i) for i in val_idx]
        val_groups = {groups[i] for i in va}
        check_no_leakage_many(val_groups, {groups[i] for i in tr})
        out.append((tr, va))
    return out


def check_no_leakage_many(val_groups: set[str], train_groups: set[str]) -> None:
    shared = val_groups & train_groups
    if shared:
        raise ValueError(f"İç katlamada aynı kişi iki tarafta: {sorted(shared)}")
