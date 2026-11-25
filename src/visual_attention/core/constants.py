"""Önceden sabitlenmiş zaman parametreleri (rapor §2.4, §2.7).

Bu değerler sonuçlara bakılarak değiştirilmez. Duyarlılık analizi (2/5 sn kesinti,
3 sn pencere) fonksiyon parametreleriyle yapılır; varsayılanlar burada kalır.
"""

SECOND_MS = 1_000
"""Süre hesabının temel birimi: örtüşmeyen 1 saniyelik dilim."""

WINDOW_MS = 2_000
"""Analiz penceresi uzunluğu."""

WINDOW_STEP_MS = 1_000
"""Pencere kaydırma adımı."""

INTERRUPTION_MIN_S = 3
"""Görünür kesinti: MATERYAL dışı bir durumun kesintisiz en az 3 sn sürmesi."""

EVENT_TOLERANCE_S = 2
"""Kesinti olayı F1 için başlangıç toleransı (±2 sn)."""

RESOLUTION_POLICY_VERSION = "trp-0.1.0"
"""TimelineResolver politikasının sürümü; deney kayıtlarına yazılır."""
