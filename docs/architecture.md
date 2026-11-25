# Faz 2.1 — Yazılım Mimarisi (v0.3)

**Proje:** Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi  
**Sorumlular:** Bahar + Pınar  
**Durum:** v0.3 — TÜBİTAK 2209-A önerisi v5 ve `docs/labeling-protocol.md` ile uyumlu hale getirildi (#23). Kamera ve etik/kurumsal süreç bekleniyor.  
**Dayanak:** TÜBİTAK 2209-A önerisi v5 (kapsamın asıl kaynağı; çelişkide v5 geçerlidir), `docs/labeling-protocol.md`, `docs/data-schema.md`.

## 1. Amaç ve değişmeyen sınırlar

Tek kameradan alınan görüntüler üzerinde **gözlenebilir çalışma yönelimini** analiz eden, yerel çalışacak ve M0 (kural tabanlı) ile M1 (Random Forest) yaklaşımlarını karşılaştırmaya elverişli bir araştırma prototipi geliştirmek. Sistem zihinsel dikkati veya öğrenme başarısını doğrudan ölçtüğünü iddia etmez.

- Üç ana sınıf: `MATERYAL`, `TELEFON`, `DIS_YON` (raporlarda `DIŞ_YÖN`).
- Özel çıktı: `BELIRSIZ` (raporlarda `BELİRSİZ`); **dördüncü eğitim sınıfı olarak yorumlanmaz**.
- Analiz: 2 saniyelik pencere, 1 saniyelik kaydırma.
- Yöntemler: M0 kural tabanlı, M1 Random Forest.
- Değerlendirme: participant_id bazlı LOSO; tüm oturumlar aynı katlamada kalır.
- Karşılaştırma tabanı: her pencereye en sık sınıfı atayan çoğunluk-sınıf tabanı (aynı LOSO katlamaları).
- Ölçümler: kişi-bazlı makro-F1, sınıf bazlı F1, precision/recall, karışıklık matrisi, BELİRSİZ oranı ve kapsama–hata eğrisi, odak süresi MAE, kesinti sayısı hatası, kesinti olayı F1 (±2 sn), Bland–Altman uyumu; etiket güvenirliği için test–tekrar test Cohen's Kappa.
- Kesinti: aynı `MATERYAL` dışı sınıfın aralıksız en az 3 saniye sürmesi (bkz. 4.4).

## 2. Mantıksal işlem hattı

```text
Harici kamera / izinli video / sentetik veri kaynağı
        |
        v
[VideoSource] --> kare + monotonic zaman damgası + kaynak durumu
        |
        v
[FeatureExtractor]
   +- FaceFeatures  (MediaPipe Face Landmarker)  --> baş pozu, göz açıklık oranı
   +- HandFeatures  (MediaPipe Hand Landmarker)  --> bilek konumu; yazma hareketi,
   |                                                  telefona uzanma, telefonu tutma göstergeleri
   +- PhoneFeatures (MediaPipe Object Detector,  --> telefon varlığı ve güven puanı
                     EfficientDet-Lite0, "cell phone")
        |             + bileşen bazlı durum ve eksik/güvenilmez kanıt bayrakları
        v
[WindowBuilder] --> 2 sn pencereler, 1 sn adım; özet özellikler
        |
        v
[Classifier] --> M0 veya M1 --> pencere bazlı Prediction
        |
        v
[TimelineResolver] --> benzersiz 1 sn dilimlere tek etiket / BELİRSİZ
        |                     (çakışan pencere tahminleri için belirlenmiş çözüm)
        v
[SessionMetrics] --> tekil saniyelerde yönelim süresi, >=3 sn kesinti
        |
        +--> [LocalUI] oturum özeti / açıklayıcı hata mesajları
        +--> [Evaluation] tahmin + insan etiketi karşılaştırması, LOSO

PARALEL, SADECE İZİNLİ ARAŞTIRMA / ÇEVRİMDIŞI EĞİTİM YOLU
[İzinli video] -> [VideoSource] -> [FeatureExtractor]
                                    |
                                    v
                     [Onaylı öznitelik deposu (sürüm bilgili)]
                                    |
                   [İnsan etiketleri] -> [LabelAligner: 1 sn referans]
                                    |
                                    v
                      [WindowBuilder: 2 sn / 1 sn]
                                    |
                                    v
                    [LOSO ExperimentRunner: eğitim/test]
                                    |
                        +-----------+-----------+
                        v                       v
                [M0 eşik belirleme]     [M1 Random Forest eğitim]
                        |                       |
                        +-----------+-----------+
                                    v
                      [Classifier -> TimelineResolver]
                                    |
                                    v
                     [Evaluation / deney kayıtları]
```

`BELIRSIZ`, verinin eksik/kararsız olduğu ya da karar kanıtının yetersiz kaldığı durum için ayrı çıkıştır; telefonun görüntüde bulunması **tek başına aktif telefon kullanımını kanıtlamaz**.

## 3. Modül sözleşmeleri (tasarım önerisi)

| Modül | Girdi | Çıktı | Başlıca hata/istisna |
|---|---|---|---|
| `VideoSource` | kamera kimliği / video yolu / sentetik veri | `FrameRecord(timestamp_ms, frame, source_id)` | açılamayan kaynak, kare kaybı |
| `FeatureExtractor` | `FrameRecord` | `FeatureRecord` (baş pozu, göz açıklık oranı, el/bilek ve telefon alanları, `face_status` / `hand_status` / `phone_status`; bkz. `data-schema.md` 3.3) | yüz/el yok, örtülme, düşük güven |
| `WindowBuilder` | zaman sıralı `FeatureRecord` | `WindowRecord(start_ms, end_ms, aggregates, coverage)` | boş pencere, düzensiz zaman damgası |
| `Classifier` | `WindowRecord` + model konfigürasyonu | `Prediction(label, confidence_or_score, reason)` | eksik kanıt / kural çelişkisi / düşük olasılık -> `BELIRSIZ` (bkz. 4.3) |
| `TimelineResolver` | pencere tahminleri + zaman sınırları + kapsama/kalite | `SecondDecision(second_start_ms, label, provenance)` | çelişen tahmin, boş/eksik dilim -> `BELIRSIZ` |
| `SessionMetrics` | tekil saniye kararları | odak süresi ve oranı, `InterruptionEvent` listesi, kesinti sayısı, BELİRSİZ oranı | çifte sayım, zaman boşlukları |
| `LabelAligner` | izinli insan etiket aralıkları (oturum video zamanında) | 1 sn referans zaman çizelgesi + eksik/uyuşmazlık işaretleri | hizasız zaman, çakışan ya da anlaşılmayan etiket |
| `FeatureStore` | seçilmiş öznitelik kayıtları + kaynak/sürüm bilgisi | erişim kontrollü, katılımcıya/oturuma bağlı öznitelik seti | yetkisiz erişim, sürüm tutarsızlığı |
| `ExperimentRunner` | 1 sn referanslar, pencereler, katılımcı kimlikleri, eğitim konfigürasyonu | M0/M1 için katılımcı bazlı LOSO katlamaları | aynı katılımcının iki tarafa düşmesi |
| `Evaluation` | kişi ve oturum kimliğiyle referans etiketleri, tekil saniye tahminleri | LOSO sonuçları / metrikler | train-test kişi sızıntısı, hizalama hatası |
| `LocalUI` | durum, tahmin ve ölçümler | yerel ekran / rapor | kaynak veya model hatası |

**Sözleşme ilkesi:** Çekirdek işlem hattı OpenCV/MediaPipe/video donanımına doğrudan bağımlı olmayacak. `VideoSource` ve `FeatureExtractor` testlerde sahte (fake) uygulamalarla değiştirilebilir olacak.

## 4. Zaman ve süre kuralları

- Pencereler örnek: `[0,2)`, `[1,3)`, `[2,4)` saniye. Her penceredeki tahmin **2 saniye süre eklenerek** toplanmaz.
- Nihai süre hesabı **tekil 1 saniyelik zaman dilimlerinin** yalnızca bir kez değerlendirilmesiyle yapılır.
- Eksik kare/kayıp yüz için otomatik olarak MATERYAL veya TELEFON kararı verilmez; belirsizlik ve veri kapsama oranı raporlanır.
- Kesinti tanımı, olay eşleştirme ve `BELIRSIZ` / `GECIS` saniyelerinin ele alınışı `docs/labeling-protocol.md` (bölüm 5–6) içinde kilitlenmiştir; özeti 4.4'tedir.

## 4.1 Pencereden tekil saniyeye geçiş (`TimelineResolver`) — yorum 8

**Sorun:** `[0,2)` ve `[1,3)` pencerelerinin kararları aynı saniyeye temas edebilir; pencere etiketlerinin sürelerini toplamak geçersizdir. `Classifier`, yalnızca **pencere tahmini** üretir. Süre ve kesinti hesabı `TimelineResolver` sonrasında yapılır.

**Ekipçe kilitlenen deterministik politika (`resolution_policy_version` = `1.0`):**

1. Oturum zamanı `[0,1000)`, `[1000,2000)` ... şeklinde **örtüşmeyen** 1.000 ms dilimlere ayrılır. Her dilim için **en fazla bir** `SecondDecision` saklanır.
2. Tamamlanmış `[t-2000,t)` penceresinin tahmini, öncelikle **son** `[t-1000,t)` dilimine atanır. Böylece `[0,2)` penceresi `[1,2)` saniyesini, `[1,3)` penceresi `[2,3)` saniyesini kararlaştırır. Aynı saniyeyi iki pencere oylamaz; aşağıdaki başlangıç kuralı hariç hiçbir saniye yeniden yazılmaz.
3. Oturumun ilk `[0,1)` saniyesi, ancak ilk `[0,2)` penceresi yeterli kanıtla geçerli olduğunda onun etiketiyle **başlangıç (bootstrap)** olarak doldurulur; aksi halde `BELIRSIZ` kalır. Böylece başlangıç saniyesi atlanmaz.
4. Eksik/kalitesiz pencere veya yeterli kanıt bulunmaması ilgili tekil saniyeye `BELIRSIZ` verir. Bir saniyeye başka bir pencerenin güvenilir tahminini kaydırarak boşluk kapatılmaz. Sonunda tam pencere üretilemeyen parça raporda **kapsanmayan süre** olarak ayrıca gösterilir; otomatik `MATERYAL` sayılmaz.
5. Saniye dilimleri `second_start_ms` ile tekil anahtarlanır; örtüşen pencere tahminleri **doğrudan toplanmaz**. `MATERYAL` yönelim süresi, `MATERYAL` kabul edilmiş tekil saniyelerin sayısından hesaplanır. Kesinti için aynı sınıftan ardışık, geçerli `MATERYAL` dışı dilimler kullanılır; araya giren `BELIRSIZ` saniyesi kesintiyi böler (bkz. 4.4). Yumuşatma uygulanmaz.
6. Her karar `source_window_start_ms`, `source_window_end_ms`, `resolution_policy_version`, `coverage` ve `reason` alanlarıyla izlenebilir olur.

**Örnek:** `P0=[0,2):MATERYAL`, `P1=[1,3):TELEFON`, `P2=[2,4):MATERYAL` ⇒ tekil saniyeler `[0,1)=MATERYAL` (bootstrap), `[1,2)=MATERYAL`, `[2,3)=TELEFON`, `[3,4)=MATERYAL`. Toplam yönelim süresi 3 sn'dir; pencere süreleri toplanmaz. Bu yalnızca tasarım örneğidir, gerçek veri sonucu değildir.

**Otomatik testler:** saniye başına tek kayıt; çelişen iki pencerede deterministik sonuç; boş pencere/belirsizlik; 3 sn kesinti sınırı; 2 sn pencerelerin iki kez sayılmaması; oturum başlangıcı ve kapanışı. Politika sonuçlara bakılarak değiştirilmez.

## 4.2 İnsan etiketi, öznitelik deposu ve M0/M1 eğitim yolu — yorum 9

**İki ayrı veri kolu:** (a) video karelerinden **model öznitelikleri**, (b) insan gözleminden **referans davranış etiketleri**. İnsan etiketleri modelin tahmini değildir. İki kol oturumun aynı **video zaman ekseninde** birleştirilir. Zaman damgasının kesin üretim kuralı (canlı/kayıtlı video farkı), Bahar'ın 1. yorumuyla Faz 2.3 veri şemasında netleştirilecektir.

1. **İzinli veri edinimi:** Etik/kurumsal uygunluk ve bilgilendirme tamamlanmadan gönüllü video kaydı yapılmaz. Prototip testleri fake `VideoSource` / sentetik kayıtlarla yürür.
2. **Bir kez öznitelik çıkarımı:** İzinli videolar yerelde işlenerek her zaman adımı için yalnızca araştırmada gerekli, etik onayla uyumlu **seçilmiş türetilmiş öznitelikler** oluşturulur. *Tüm yüz landmark koordinatlarının saklanacağı varsayılmıyor.* Saklanacak alanlar, gerekçe, sürüm, erişim ve imha kuralları etik kontrol ve veri şemasında ayrıca onaylanacak. Kodlanmış öznitelikler otomatik olarak anonim sayılmaz.
3. **İnsan etiketleri:** Etiketleyiciler (Pınar ve Bahar; videolar aralarında bölünür, Bahar'ın video erişimi etik değişiklik onayına bağlıdır) gözlenen davranışı ELAN'da oturum-zaman aralıklarıyla işaretler. `LabelAligner` bu aralıkları `[s,s+1)` tekil saniyelerine hizalar (yarıdan fazla kaplayan sınıf; eşitlikte `GECIS`). Belirsiz, kapsanmayan ve geçiş saniyeleri açıkça işaretlenir. Etiket güvenirliği test–tekrar test ile ölçülür; kurallar `labeling-protocol.md` bölüm 5 ve 7'dedir.
4. **Pencere kurma ve eğitim hedefi:** Onaylı öznitelik dizisinden `[0,2)`, `[1,3)` ... pencereler elde edilir. Eğitim hedefi (`train_label`) insan etiketlerinin **milisaniyelik** aralıklarından hesaplanır: 1000 ms'den fazlasını kaplayan sınıf pencereyi alır; hiçbir sınıf yarıyı geçmezse `GECIS` olur ve eğitimden çıkarılır; `BELIRSIZ` + etiketsiz süre 1000 ms veya fazlaysa pencere kullanılmaz (`labeling-protocol.md` 5.3). Bu kural kilitlidir, sonuçlara bakılarak değiştirilmez.
5. **Katılımcı-bazlı LOSO:** Her dış katlamada bir katılımcının **tüm** oturumları testte tutulur. `FeatureStore` yalnız izin verilen işlenmiş kayıtları sağlar; imputation, eşikler, özellik seçimi ve M1 ayarları **sadece eğitim katılımcılarından** öğrenilir. M0 ve M1 aynı katlamalar üzerinde sınanır.
6. **Eğitim/değerlendirme:** M0 için eğitim katılımcıları üzerinden eşik belirleme; M1 için yine yalnız eğitim katılımcılarının pencereleri üzerinde `RandomForest.fit`. Test kişisinde pencere tahminleri `TimelineResolver` ile tekil saniye tahminlerine dönüştürülür ve 1 sn insan referanslarıyla karşılaştırılır. Makro-F1 (yalnız ilgili katılımcının referansında bulunan sınıflar üzerinden), sınıf bazlı F1, BELİRSİZ oranı, odak süresi MAE, kesinti sayısı hatası ve kesinti olayı F1 kişi bazında raporlanır; serbest oturum sonuçları senaryolu oturumlardan ayrı verilir. BELİRSİZ dördüncü ana eğitim sınıfı değildir. M1–M0 farkları katılımcı düzeyinde eşleştirilmiş analiz edilir (fark dağılımı, medyan, Hodges–Lehmann, katılımcı düzeyinde bootstrap %95 GA, keşifsel Wilcoxon). İç ayarlar eğitim kişilerinde GroupKFold ile seçilir.
7. **Tekrarlanabilirlik:** Veri/etiket sürümleri, erişim kontrollü öznitelik yolu, `feature_version`, `resolution_policy_version`, kod commit'i, fold, model parametreleri ve metrikler deney günlüğüne kaydedilir. `FeatureStore` fiziksel dosya şeması ve saklanacak tam alanlar Faz 2.3'te kesinleşir.

## 4.3 BELİRSİZ karar kuralları (v5 2.5; analiz başlamadan sabittir)

| Yöntem | `BELIRSIZ` koşulu | `Prediction.reason` |
| --- | --- | --- |
| M0 – Kural tabanlı | Penceredeki karelerin %50'sinden azında yüz bulunduysa (`face_detected_ratio < 0,5`) | `LOW_FACE_RATIO` |
| M0 – Kural tabanlı | Kurallar birbiriyle çelişiyorsa (birden fazla sınıfın koşulu sağlanıyorsa) | `RULE_CONFLICT` |
| M1 – Random Forest | En yüksek sınıf olasılığı θ'nın altındaysa | `LOW_CONFIDENCE` |

- θ yalnız eğitim katılımcılarında, kişi gruplu iç doğrulamada (GroupKFold) kapsama ≥ %85 olacak biçimde seçilir; test kişisi θ seçiminde kullanılmaz.
- Her iki yöntem için kapsama–hata eğrisi ve BELİRSİZ oranı birlikte raporlanır.
- M0 eşikleri de yalnız eğitim katılımcılarında belirlenir.

## 4.4 Kesinti ve olay eşleştirme (özet; ayrıntı `labeling-protocol.md` bölüm 6)

1. Kesinti: 1 saniyelik zaman çizelgesinde aynı sınıftan (`TELEFON` veya `DIS_YON`) ardışık en az 3 saniye. Farklı sınıflar art arda gelirse ayrı durumdur (2 sn `TELEFON` + 2 sn `DIS_YON` kesinti değildir). Bu, v5'teki "MATERYAL dışındaki davranış" tanımının ekip yorumudur.
2. Araya giren `BELIRSIZ` veya `GECIS` saniyesi kesintiyi böler.
3. Yumuşatma yoktur; model tahminine ve insan referansına aynı kural uygulanır.
4. Olay F1: Model kesintisi, referans kesintisiyle aynı sınıftaysa ve başlangıç farkı ±2 sn içindeyse doğru sayılır; eşleştirme bire birdir.
5. Eşik 3 sn önceden sabittir; 2 ve 5 sn yalnız duyarlılık analizindedir. Ayrıca 3 sn pencere ile duyarlılık analizi yapılır.
6. Odak oranı: odak süresi / geçerli süre; `BELIRSIZ` ve `GECIS` saniyeleri paydaya girmez.

**Güvenlik sınırı:** Ham kare/video, kişi eşleme listesi ve kişisel veri içeren türevler GitHub'a veya üçüncü taraf buluta gönderilmez. Özniteliklerin diske yazılması, etik/kurumsal karar ve veri minimizasyonu onayından sonra uygulanır; öncesinde sadece sentetik veriler saklanır.

## 5. Kişi bağımsız deney ilkeleri

1. Her `participant_id` için tüm oturumlar aynı test fold'unda tutulur.
2. Eşik, eksik değer doldurma, ölçekleme ve M1 hiperparametre seçimleri yalnız eğitim katılımcılarından yapılır.
3. M0 ve M1 aynı dış test kişisi, aynı geçerli veri kesiti ve önceden belirlenen metriklerle karşılaştırılır.
4. Etiket güvenirliği, videonun en az %25'inin en az 4 hafta arayla ve kör olarak aynı etiketleyici tarafından yeniden etiketlenmesiyle (test–tekrar test) Cohen's Kappa ile ayrıca raporlanır. Bu tasarım etiketleyiciler arası uyumu değil, zamansal tutarlılığı ölçer.
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
      timeline/             # Pınar: TimelineResolver
      labeling/             # Pınar + Bahar: LabelAligner
      storage/              # Ortak: kontrollü FeatureStore
      training/             # Ortak: LOSO ExperimentRunner
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

- **Harici kamera:** v5'e göre proje bütçesiyle Full HD (1920×1080, 30 kare/sn, otomatik odak, tripod bağlantılı) harici USB web kamerası alınır; o zamana kadar danışmanın web kamerası kullanılır, dizüstü kamerası yalnız arıza yedeğidir. `VideoSource` arayüzü sabitlenip kamera adaptörü sonra uygulanabilir. FPS ölçümü (≥ 10 FPS, GPU'suz) önerideki bilgisayarda yapılır. Bahar, dahili **HP True Vision FHD** kamerayla 640×480 çözünürlükte yaklaşık **13 FPS** ölçtüğünü bildirmiştir; bu ölçümün koşulları ve tekrar doğrulaması risk kaydında tutulacak, harici kamera için sonuç varsayılmayacaktır.
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
- [x] Kamera/video okuma kütüphanesi ve MediaPipe kullanım sürümü değerlendirildi (OpenCV; MediaPipe Face/Hand Landmarker ve Object Detector, `requirements.txt`).
- [x] Çıktıların uygulama içi kodları (`DIS_YON`, `BELIRSIZ`) ile rapor etiketleri eşleştirildi.
- [ ] Zaman damgası türü, pencere kapsaması ve eksik veri eşiği `data-schema.md` içinde netleştirildi.
- [x] Telefon kullanımı için asgari görünür kanıt kuralı `labeling-protocol.md` içinde tanımlandı (4.1–4.2).
- [x] M0/M1 için BELİRSİZ karar mekanizması ve karşılaştırma kuralları sabitlendi (4.3).
- [x] Pencere eğitim hedefi, kesinti tanımı ve olay eşleştirme kilitlendi (4.2 madde 4, 4.4).
- [ ] Harici kameranın modeli ve teknik testleri geldiğinde risk kaydı güncellendi.

## 9.1 Bahar incelemesinden kalan takip maddeleri (sonraki PR / Faz 2.3–2.5)

Aşağıdakiler **bu revizyonda tamamlanmış sayılmamıştır**; ilgili Issue'lara aktarılmalıdır:

1. Canlı ve dosya video zaman damgalarının aynı oturum-başlangıçlı **video zamanı** sözleşmesiyle ifade edilmesi; kayıtlı video için işlem saati kullanılmaması.
2. `FrameRecord.frame_index`, gerçek FPS, atlanan kare sayısı ve pencere asgari kapsama/kare sayısı.
3. Canlı modda en yeni kareyi tercih eden gecikme politikası ile kayıtlı video modunda tüm kareleri işleme politikasının ayrıştırılması.
4. Kamera konumu/açısı, çözünürlük ve kurulumun oturum meta verisine alınması ve protokol boyunca sabitlenmesi.
5. Yüz/baş, el ve telefon ipuçlarının takılıp çıkarılabilir ayrı çıkarım bileşenleri olması. *(v0.3: akışa üç alt bileşen olarak eklendi; telefon için EfficientDet-Lite0 seçildi.)*
6. Baş pozu derece ve işaret yönü, sabit göz alanları ve `feature_version` sözleşmesi.
7. `telefon yok` / `telefon görünmüyor` ve `yüz yok` / `düşük güven` durumlarının ayrı geçerlilik bayrakları.

**Çakışma notu:** Zaman damgası ve `feature_version` terimleri 4.2'de birer sözleşme ihtiyacı olarak geçer; uygulama ayrıntıları ve alanların nihai tanımları bu takip maddelerinin tamamlanmasını gerektirir.

## 10. Faz 2.1 kabul kriteri

- [ ] Kaynaktan arayüze mantıksal akış belgede açık.
- [ ] Tüm modüllerin girdileri/çıktıları ve eksik veri davranışı yazılı.
- [ ] `TimelineResolver` ile pencereden saniyeye geçiş tanımlanmış; süreyi çift saymama ilkesi korunmuş.
- [ ] İnsan etiketi hizalaması, öznitelik deposu ve M0/M1 eğitim/LOSO yolu belgelenmiş.
- [ ] Kişi bazlı LOSO ve veri güvenliği sınırları korunmuş.
- [ ] İki ekip üyesi mimari taslağını inceleyip geri bildirim verdi.

## Revizyon kaydı

- **v0.2 (9 Kasım 2026):** Bahar incelemesindeki yorum 8 için `TimelineResolver` ve saniyelik karar taslağı; yorum 9 için `LabelAligner` / `FeatureStore` / `ExperimentRunner` ile eğitim-değerlendirme yolu eklendi. Yorum 1–7 takip listesine ayrıldı. **Ekip onayı ve politika kilitleme bekleniyor.**
- **v0.3 (25 Kasım 2026, #23):** TÜBİTAK 2209-A önerisi v5 ve `labeling-protocol.md` ile uyum: el/bilek alt bileşeni ve araçlar; BELİRSİZ kuralları (4.3); kesinti ve olay eşleştirme (4.4); pencere eğitim hedefi ve `TimelineResolver` politikası kilitlendi; çift etiketleme yerine test–tekrar test; ölçüm ve istatistik listesi v5'e göre genişletildi; kamera bilgisi güncellendi.
