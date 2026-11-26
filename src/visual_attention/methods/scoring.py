"""Kişi başına makro-F1 (v5 §2.7).

Makro-F1 yalnızca ilgili kişinin referansında bulunan ana sınıflar üzerinden hesaplanır.

İki kullanım:
- **Rapor (değerlendirme):** referansı ana sınıf olan ve modelin ana sınıf dediği
  birimler kullanılır; modelin BELIRSIZ dediği birimler F1'e girmez, kapsama ve BELIRSIZ
  oranı olarak ayrıca raporlanır (`covered_only=True`).
- **Eşik seçimi (eğitim):** modelin BELIRSIZ dediği birimler hata sayılır
  (`covered_only=False`). Böylece seçim, zor örneklerde BELIRSIZ deyip F1'i şişiren
  eşiklere kaymaz.
"""

from __future__ import annotations

from collections.abc import Sequence

from visual_attention.core.labels import MAIN_CLASSES, Label


def macro_f1(
    reference: Sequence[Label],
    predicted: Sequence[Label],
    *,
    covered_only: bool = True,
) -> float | None:
    """Referansta görülen ana sınıfların F1 ortalaması. Hesaplanacak birim yoksa None."""
    if len(reference) != len(predicted):
        raise ValueError(f"Uzunluklar farklı: {len(reference)} ve {len(predicted)}")
    pairs = [(r, p) for r, p in zip(reference, predicted, strict=True) if r in MAIN_CLASSES]
    if covered_only:
        pairs = [(r, p) for r, p in pairs if p in MAIN_CLASSES]
    if not pairs:
        return None
    classes = sorted({r for r, _ in pairs})
    scores = []
    for c in classes:
        tp = sum(1 for r, p in pairs if r == c and p == c)
        fp = sum(1 for r, p in pairs if r != c and p == c)
        fn = sum(1 for r, p in pairs if r == c and p != c)
        scores.append(2 * tp / (2 * tp + fp + fn))
    return sum(scores) / len(scores)


def coverage(reference: Sequence[Label], predicted: Sequence[Label]) -> float | None:
    """Referansı ana sınıf olan birimlerde modelin ana sınıf (BELIRSIZ değil) verme oranı."""
    pairs = [p for r, p in zip(reference, predicted, strict=True) if r in MAIN_CLASSES]
    if not pairs:
        return None
    return sum(1 for p in pairs if p in MAIN_CLASSES) / len(pairs)
