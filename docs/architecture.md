# Faz 2.1 — Yazılım Mimarisi (Taslak v0.1)

**Proje:** Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi  
**Sorumlular:** Bahar + Pınar  
**Durum:** İnceleme bekliyor; kamera modeli ve etik/kurumsal süreç henüz kesinleşmedi.  
**Dayanak:** 8 haftalık iç yol haritası, Faz 2 (12–18 Kasım 2026).

## 1. Amaç ve değişmeyen sınırlar

Tek kameradan alınan görüntüler üzerinde **gözlenebilir çalışma yönelimini** analiz eden, yerel çalışacak ve M0 (kural tabanlı) ile M1 (Random Forest) yaklaşımlarını karşılaştırmaya elverişli bir araştırma prototipi geliştirmek. Sistem zihinsel dikkati veya öğrenme başarısını doğrudan ölçtüğünü iddia etmez.

- Üç ana sınıf: `MATERYAL`, `TELEFON`, `DIS_YON` (raporlarda `DIŞ_YÖN`).
- Özel çıktı: `BELIRSIZ` (raporlarda `BELİRSİZ`); **dördüncü eğitim sınıfı olarak yorumlanmaz**.
- Analiz: 2 saniyelik pencere, 1 saniyelik kaydırma.
- Yöntemler: M0 kural tabanlı, M1 Random Forest.
- Değerlendirme: participant_id bazlı LOSO; tüm oturumlar aynı katlamada kalır.
- Ölçümler: Macro-F1, sınıf bazlı F1, Cohen's Kappa (etiket uyumu), BELİRSİZ oranı, yönelim süresi MAE ve kesinti sayısı hatası.
- Kesinti eşiği: kesintisiz >=3 saniye (tam operasyonel tanımı etiketleme protokolünde sabitlenecek).

## 2. Mantıksal işlem hattı

```text
Harici kamera / izinli video / sentetik veri kaynağı
        |
        v
[VideoSource] --> kare + monotonic zaman damgası + kaynak durumu
        |
        v
[FeatureExtractor] --> baş pozu / seçili yüz-göz / görünür telefon ipuçları
        |             + eksik/güvenilmez kanıt bayrakları
        v
[WindowBuilder] --> 2 sn pencereler, 1 sn adım; özet özellikler
        |
        v
[Classifier] --> M0 veya M1 --> MATERYAL / TELEFON / DIŞ_YÖN / BELİRSİZ
        |
        v
[SessionMetrics] --> tekil saniyelerde yönelim süresi, >=3 sn kesinti
        |
        +--> [LocalUI] oturum özeti / açıklayıcı hata mesajları
        +--> [Evaluation] LOSO, kişi bazlı metrikler, deney günlüğü
```

`BELIRSIZ`, verinin eksik/kararsız olduğu ya da karar kanıtının yetersiz kaldığı durum için ayrı çıkıştır; telefonun görüntüde bulunması **tek başına aktif telefon kullanımını kanıtlamaz**.

## 3. Modül sözleşmeleri (tasarım önerisi)

| Modül | Girdi | Çıktı | Başlıca hata/istisna |
|---|---|---|---|
| `VideoSource` | kamera kimliği / video yolu / sentetik veri | `FrameRecord(timestamp_ms, frame, source_id)` | açılamayan kaynak, kare kaybı |
| `FeatureExtractor` | `FrameRecord` | `FeatureRecord(timestamp_ms, head_pose, eye_features, phone_cues, validity_flags)` | yüz yok, örtülme, düşük güven |
| `WindowBuilder` | zaman sıralı `FeatureRecord` | `WindowRecord(start_ms, end_ms, aggregates, coverage)` | boş pencere, düzensiz zaman damgası |
| `Classifier` | `WindowRecord` + model konfigürasyonu | `Prediction(label, confidence_or_score, reason)` | eksik kanıt -> `BELIRSIZ` |
| `SessionMetrics` | zaman damgalı tahmin/karar akışı | süre, kesinti sayısı, BELİRSİZ oranı | çifte sayım, zaman boşlukları |
| `Evaluation` | kişi ve oturum kimliğiyle referans etiketleri, tahminler | LOSO sonuçları / metrikler | train-test kişi sızıntısı |
| `LocalUI` | durum, tahmin ve ölçümler | yerel ekran / rapor | kaynak veya model hatası |

**Sözleşme ilkesi:** Çekirdek işlem hattı OpenCV/MediaPipe/video donanımına doğrudan bağımlı olmayacak. `VideoSource` ve `FeatureExtractor` testlerde sahte (fake) uygulamalarla değiştirilebilir olacak.

## 4. Zaman ve süre kuralları

- Pencereler örnek: `[0,2)`, `[1,3)`, `[2,4)` saniye. Her penceredeki tahmin **2 saniye süre eklenerek** toplanmaz.
- Nihai süre hesabı **tekil 1 saniyelik zaman dilimlerinin** yalnızca bir kez değerlendirilmesiyle yapılır.
- Eksik kare/kayıp yüz için otomatik olarak MATERYAL veya TELEFON kararı verilmez; belirsizlik ve veri kapsama oranı raporlanır.
- En az 3 saniye kesintinin tanımı, geçiş/histerezis ve `BELIRSIZ` aralıklarının nasıl ele alınacağı `docs/labeling-protocol.md` içinde karar olarak kilitlenecek.

## 5. Kişi bağımsız deney ilkeleri

1. Her `participant_id` için tüm oturumlar aynı test fold'unda tutulur.
2. Eşik, eksik değer doldurma, ölçekleme ve M1 hiperparametre seçimleri yalnız eğitim katılımcılarından yapılır.
3. M0 ve M1 aynı dış test kişisi, aynı geçerli veri kesiti ve önceden belirlenen metriklerle karşılaştırılır.
4. Etiket uyumu en az %25 bağımsız çift etiketleme ve Cohen's Kappa ile ayrıca raporlanır.
5. Deney kaydı: commit, model ayarları, veri/etiket sürümü, fold kimliği, metrikler ve sınırlılıklar.

## 6. Önerilen başlangıç klasörleri

```text
visual-attention-estimation/
  .github/
    workflows/             # Faz 2.5 CI
    pull_request_template.md
  docs/
    project-charter.md
    literature-notes.md
    ethics-checklist.md
    risk-register.md
    architecture.md
    data-schema.md           # Faz 2.3
    labeling-protocol.md     # Faz 2.4
  src/
    visual_attention/
      capture/              # Bahar
      features/             # Bahar
      windowing/            # Pınar
      classification/       # Ortak
      metrics/              # Pınar
      evaluation/           # Ortak
      ui/                   # Sonraki faz
  tests/
    unit/
    integration/
  requirements.txt          # Faz 2.2'de sabitlenecek
  README.md
  .gitignore
```

Bu klasörler **öneridir**, henüz oluşturulmuş veya çalışan kod olarak gösterilmez.

## 7. Kamera ve etik bağımlılıkları

- **Harici kamera:** Model, bağlantı, çözünürlük ve gerçek FPS bilinmiyor. `VideoSource` arayüzü sabitlenip kamera adaptörü sonra uygulanabilir.
- **Gerçek gönüllü görüntüsü:** Gerekli etik/kurumsal uygunluk ve bilgilendirme süreçleri tamamlanmadan kaydedilmez.
- **Geliştirme/test:** Sentetik zaman damgaları, sahte özellik akışları ve izinli/kişisel veri içermeyen girdiler kullanılabilir.
- **Güvenlik:** Ham videolar, kimlik eşleme dosyaları ve kişisel veri içeren türevler GitHub'a yüklenmez; buluta otomatik gönderim yapılmaz.

## 8. Ekip ve Faz 2 çıktıları

| İş | Ana sorumlu | Kanıt |
|---|---|---|
| Mimari ve arayüz sözleşmeleri | Ortak | Bu dosyanın PR incelemesi |
| Python/venv ve kurulum | İki bilgisayarda ortak | README/kurulum kontrol kayıtları |
| Veri şeması ve pencere kuralları | Pınar | `data-schema.md`, sentetik test |
| Etiketleme kılavuzu | Pınar + Bahar | `labeling-protocol.md` |
| Kamera ve çıkarım adaptörü tasarımı | Bahar | Modül sözleşmesi, cihaz gelince test |
| pytest, Ruff, CI | Pınar koordine | İlk PR'da çalışan kontroller |

## 9. Açık kararlar / doğrulama listesi

- [ ] Bahar ve Pınar modül sınırlarını onayladı.
- [ ] Kamera/video okuma kütüphanesi ve MediaPipe kullanım sürümü Faz 2.2'de değerlendirildi.
- [ ] Çıktıların uygulama içi kodları (`DIS_YON`, `BELIRSIZ`) ile rapor etiketleri eşleştirildi.
- [ ] Zaman damgası türü, pencere kapsaması ve eksik veri eşiği `data-schema.md` içinde netleştirildi.
- [ ] Telefon kullanımı için asgari görünür kanıt kuralı `labeling-protocol.md` içinde tanımlandı.
- [ ] M0/M1 için BELİRSİZ karar mekanizması ve karşılaştırma kuralları yöntem belgesinde sabitlendi.
- [ ] Harici kameranın modeli ve teknik testleri geldiğinde risk kaydı güncellendi.

## 10. Faz 2.1 kabul kriteri

- [ ] Kaynaktan arayüze mantıksal akış belgede açık.
- [ ] Tüm modüllerin girdileri/çıktıları ve eksik veri davranışı yazılı.
- [ ] Zaman penceresi ve süreyi çift saymama ilkesi korunmuş.
- [ ] Kişi bazlı LOSO ve veri güvenliği sınırları korunmuş.
- [ ] İki ekip üyesi mimari taslağını inceleyip geri bildirim verdi.
