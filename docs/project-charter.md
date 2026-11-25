# Project Charter — Görsel Dikkat Araştırması (v2)

**Durum:** v2 — TÜBİTAK 2209-A önerisi v5'e ve iki geliştiricili gerçek çalışma düzenine göre güncellendi (#30). Bahar ve Pınar'ın onayı bekleniyor.
**Tarih:** 25 Kasım 2026 (v1: 9 Kasım 2026)
**Dayanak:** TÜBİTAK 2209-A araştırma önerisi, son hali (v5) — kapsamın asıl kaynağı; çelişkide v5 geçerlidir.
**Ekip:** Pınar Karadoğan (proje yürütücüsü, proje yönlendirmesi) ve Bahar
**Akademik danışman:** Prof. Dr. Bilal Alataş — Fırat Üniversitesi, Yazılım Mühendisliği Bölümü
**Bağlam:** Bu çalışma Proje Yönetimi dersi kapsamında iki kişi tarafından yürütülen bir ders projesidir. Kapsam, v5 önerisindeki kapsamın tamamıdır; hiçbir modül, sınıf, metrik veya analiz çıkarılmaz.

## 1. Proje başlığı

Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi

## 2. Amaç ve bilimsel iddia sınırı

Yetişkin üniversite öğrencilerinin kâğıt tabanlı bireysel çalışması sırasında görsel dikkat durumunu tek kameradan yerel cihazda sınıflandıran ve odak süresini kişi-bağımsız olarak kestiren bir yöntem geliştirmek ve bu yöntemin doğruluğunu nicel olarak belirlemek (v5 §1.2).

Bu çalışma kişinin bilişsel dikkatini, anlama düzeyini veya öğrenme başarısını ölçtüğünü iddia etmez. Göz bakış noktasının hassas ölçüldüğü iddia edilmez. Masada yokluk ve yorgunluk kapsam dışıdır.

## 3. Araştırma kapsamı (v5)

- **Sınıflar:** MATERYAL, TELEFON, DIŞ_YÖN. BELİRSİZ ayrı bir çıktıdır, dördüncü dikkat durumu sınıfı değildir.
- **Katılımcılar:** 8–10 yetişkin gönüllü (etik izin belgesinden sonra). Kişi başına 20 dk senaryolu + 10 dk serbest oturum; toplam 240–300 dk.
- **Senaryo:** Kişiye özel, tohumlu rastgele 6 TELEFON (5–30 sn) + 6 DIŞ_YÖN (2–20 sn) kesintisi; aralarda ≥ 60 sn MATERYAL (v5 §2.2, Ek-1).
- **Öznitelikler:** Baş pozu (yaw/pitch/roll), göz açıklık oranı (yardımcı), el/bilek göstergeleri (yazma hareketi, telefona uzanma, telefonu tutma), telefon varlık/güven puanı (v5 §2.4).
- **Zaman:** 2 sn pencere, 1 sn kaydırma; süre her 1 sn adımı yalnız bir kez sayılarak hesaplanır.
- **Yöntemler:** M0 kural tabanlı, M1 Random Forest ve çoğunluk-sınıf tabanı; aynı LOSO katlamalarında (v5 §2.5).
- **Değerlendirme:** Kişi-bazlı makro-F1, sınıf bazlı F1, karışıklık matrisi, BELİRSİZ oranı ve kapsama–hata eğrisi; odak süresi MAE, kesinti sayısı hatası, kesinti olayı F1 (±2 sn), Bland–Altman; M1–M0 için Hodges–Lehmann, katılımcı düzeyinde bootstrap %95 GA ve keşifsel Wilcoxon; grup çıkarma analizi; 2/5 sn kesinti ve 3 sn pencere duyarlılık analizleri (v5 §2.7).
- **Etiket güvenirliği:** Test–tekrar test; videonun ≥ %25'i, ilk etiketlemeden ≥ 4 hafta sonra, kör olarak yeniden etiketlenir; Cohen κ (v5 §2.3).
- **Yerel prototip:** Ham görüntüyü cihaz dışına çıkarmayan, GPU'suz ≥ 10 FPS çalışan açık kaynak prototip (v5 H5).

## 4. Hedefler ve teslimatlar (v5)

| Hedef | Hedef değer | Teslimat |
| --- | --- | --- |
| H1 – Veri seti | ≥ 8 katılımcı; ≥ 240 dk geçerli video; TELEFON ve DIŞ_YÖN için ayrı ayrı ≥ 40 olay | Ç1: Sahte kodlu, nihai referans etiketli kayıt kümesi ve olay sayısı raporu |
| H2 – Etiket güvenirliği | Genel κ ≥ 0,70; sınıf bazlı κ ≥ 0,60; tekrar etiketlenen video ≥ %25 | Ç2: Etiketleme kılavuzu v1.0 ve test–tekrar test raporu |
| H3 – Sınıflandırma | M1 makro-F1 ≥ 0,70; M1 − M0 ≥ 0,05, katılımcıların ≥ 2/3'ünde pozitif | Ç3: M0, M1 ve taban karşılaştırma raporu |
| H4 – Oturum metrikleri | Odak süresi MAE ≤ 60 sn; kesinti olay F1 ≥ 0,60 | Ç4: Oturum hata raporu (Bland–Altman dahil) |
| H5 – Yerel prototip | ≥ 10 FPS; karar gecikmesi ≤ 3 sn; yüz tespiti ≥ %90 kare; BELİRSİZ ≤ %15; 20 dk çökmesiz | Ç5: Açık kaynak prototip v1.0 ve FPS/gecikme raporu |
| H3–H4 | — | Ç6: Kongre bildirisi gönderimi |

## 5. İki takvim

Öneri v5, çalışmayı tek yürütücüyle 12 ayda beş iş paketiyle planlar. Ders projesi ise iki geliştiriciyle 25 Kasım – 5 Aralık 2026 arasında yürütülür. Kapsam aynıdır; yalnızca süre ve iş bölümü farklıdır.

| Ders iç planı (faz) | Tarih | v5 iş paketi karşılığı |
| --- | --- | --- |
| Faz 1 — Hazırlık, kapsam, etik ve risk | 5–11 Kas | İP1 |
| Faz 2 — Mimari, veri şeması, etiketleme protokolü, CI, v5 uyumu | 12–26 Kas | İP1 |
| Faz 3 — Çekirdek veri işleme (kayıt tipleri, senaryo, ELAN dönüştürücü, sentetik veri) | 25–28 Kas | İP2, İP3 hazırlığı |
| Faz 4 — Görüntü ve öznitelik hattı (video, yüz, telefon, el, birleştirici, pencereleme) | 25–30 Kas | İP2 |
| Faz 5 — Deney altyapısı ve kayda hazırlık (M0, LOSO, uçtan uca deneme, ELAN ortak deneme) | 28 Kas – 1 Ara | İP4 hazırlığı |
| Faz 6 — Veri toplama ve etiketleme (etik izin geldiyse) | 2–5 Ara | İP3 |
| Faz 6 paralel — M1, değerlendirme, prototip, FPS, README | 2–5 Ara | İP4, İP5 |
| Teslim sonrası — Test–tekrar test etiketlemesi ve κ | Ocak 2027 başı | İP3 (≥ 4 hafta kuralı) |

**Not:** Test–tekrar test etiketlemesi ilk etiketlemeden en az 4 hafta sonra yapılmalıdır; bu süre teslim tarihine göre kısaltılmaz (labeling-protocol.md §7). Tekrar setindeki videolar ilk sırada etiketlenir.

## 6. Roller ve sorumluluklar

| Alan | Pınar | Bahar |
| --- | --- | --- |
| Proje yönlendirmesi, görev dağılımı, pano ve merge sırası | Ana sorumlu | — |
| Belgeler (charter, etik, risk, kayıt protokolü) | Ana sorumlu | İnceleme |
| Etiketleme protokolü | İnceleme ve onay | Ana sorumlu (v0.2) |
| Zaman çizelgesi, oturum metrikleri, kayıt tipleri | Ana sorumlu | İnceleme |
| Senaryo üreticisi, ELAN dönüştürücü, sentetik veri | Ana sorumlu | İnceleme |
| Video okuma, yüz, telefon, el öznitelikleri, birleştirici, pencereleme | İnceleme | Ana sorumlu |
| M0, çoğunluk tabanı, LOSO; M1, metrikler ve istatistik | Ana sorumlu | İnceleme |
| Canlı prototip, FPS/gecikme ölçümü, README, yeniden üretim | İnceleme (FPS kendi bilgisayarında) | Ana sorumlu |
| Kayıt oturumları ve etiketleme | Birlikte | Birlikte (video erişimi etik değişiklik onayına bağlı) |
| Kayıt protokolü ve etik süreç | Danışman gözetiminde, Pınar | — |

Akademik danışman kayıt protokolü ve etik süreçte gözetim sağlar (v5 §3.1).

## 7. Çalışma sistemi

- **Depo:** `PinarKaradogan/visual-attention-estimation`; tek kaynak `main`.
- **Görev:** Her iş bir GitHub Issue'dur. Başlık kodu fazı gösterir (ör. `P3-01.1`). Açıklamada amaç, kapsam (madde madde), kabul ölçütü ve bağımlılık (`#no`) bulunur.
- **Bağımlılık zinciri:** Birbirinin girdisi olan işler aynı kişiye atanır. İki zincirin kesiştiği noktalar Issue'larda açıkça yazılır.
- **Branch:** Güncel `main`'den `feature/<issue-no>-kisa-tanim`.
- **Commit:** Atomik; `tür: #issue-no açıklama` (tür: feat, fix, docs, test, ci, refactor, chore).
- **PR:** `main`'e; açıklamada `Closes #issue-no`, yapılan değişiklikler ve test durumu. İnceleyici diğer ekip üyesidir. Onay ve yeşil CI sonrası PR'ı açan kişi merge eder; bağımlı olduğu iş main'de değilse merge edilmez.
- **Pano (GitHub Projects — Development Board):**
  - **Backlog:** Bağımlılığı henüz merge edilmemiş işler.
  - **Ready:** Bağımlılığı merge edildi; kartı Pınar taşır.
  - **In Progress:** Kişi başına en fazla 2 kart.
  - **In Review:** PR açık.
  - **Done:** Merge edildi (otomatik).
  - **Blocked:** 2 saati aşan engel.
- **Kontroller:** CI her PR'da pip check, Ruff ve pytest çalıştırır.
- **Veri güvenliği:** Ham video, etiket dosyaları, kimlik eşlemesi ve kişisel veri içeren türevler hiçbir zaman Git'e veya buluta gitmez (`local_data/` Git dışındadır).
- **İletişim:** Günlük kısa durum yazışması (dün / bugün / engel).

## 8. Etik ve güvenlik bağımlılıkları

- Etik kurul başvurusu yapıldı; karar bekleniyor (v5 §2.8). İzin belgesi alınmadan hiçbir gönüllüden görüntü kaydedilmez.
- İzin beklenirken geliştirme yalnızca sentetik veri ve açık lisanslı, kişisel veri içermeyen örneklerle yapılır; bu sonuçlar gerçek gönüllü sonucu gibi raporlanmaz.
- Ayrıntılar: `docs/ethics-checklist.md`.

## 9. Açık kararlar

- [x] Proje önerisiyle kapsam uyumu — v5 esas alındı (#23, #30).
- [x] Etiketleme belirsizlik ve geçiş kuralları — `docs/labeling-protocol.md` v0.2.
- [ ] Etik kurul kararı (bekleniyor).
- [ ] Bahar'ın video erişimi için etik kurula değişiklik bildirimi ve aydınlatma metninin güncellenmesi (danışmanla görüşülüyor).
- [ ] Kamera konumu, ışık ve iki bilgisayarın yeterliliği — teknik pilot ve FPS ölçümüyle.
- [ ] Aydınlatma/onam metinlerinin onaylı sürümü ve saklama-silme takvimi (üniversitenin ilgili birimleriyle).

## 10. Onay kaydı

- Pınar: Bekleniyor — Tarih: ___
- Bahar: Bekleniyor — Tarih: ___

## Revizyon kaydı

- **v1 (9 Kasım 2026):** İlk charter; 8 haftalık iç plan.
- **v2 (25 Kasım 2026, #30):** Öneri v5'e göre kapsam, hedefler ve teslimatlar; iki takvim; iki geliştiricili roller; Issue, bağımlılık zinciri ve pano tabanlı çalışma sistemi; etik durum güncellendi.
