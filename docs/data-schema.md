# Faz 2.3 — Veri Şeması ve Zaman Sözleşmesi (v0.2)

**Proje:** Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi

**Tarih:** 9 Kasım 2026

**Sorumlular:** Pınar (ana), Bahar (kamera/öznitelik doğrulaması)

**Durum:** v0.2 — TÜBİTAK 2209-A önerisi v5 ve `docs/labeling-protocol.md` ile uyumlu hale getirildi (#23). Gerçek veri toplama ve saklama için izin verilmiş değildir.

## 1. Amaç ve kapsam

Bu belge `architecture.md` v0.3, `labeling-protocol.md` ve TÜBİTAK 2209-A önerisi v5'e dayanarak modüller arasında taşınacak verinin **alan adlarını, türlerini, birimlerini, anahtarlarını, geçerlilik durumlarını ve zaman çizelgesini** tanımlar. İlgili modüller: `VideoSource`, `FeatureExtractor`, `WindowBuilder`, `Classifier`, `TimelineResolver`, `LabelAligner`, `FeatureStore`, `ExperimentRunner` ve `SessionMetrics`.

- Ana sınıflar: `MATERYAL`, `TELEFON`, `DIS_YON` (raporda `DIŞ_YÖN`).
- `BELIRSIZ` tahmin/karar özel çıktısıdır; dördüncü ana eğitim sınıfı değildir.
- 2.000 ms pencere / 1.000 ms kaydırma; tekil saniye kararları `[başlangıç, bitiş)` aralıklarıyla tanımlanır.
- Katılımcı bazlı LOSO: aynı `participant_id`'ye ait **tüm** oturumlar bir dış katlamada birlikte testte kalır.
- Ham video, kimlik eşleme bilgisi ve kişisel veriler GitHub'a gönderilmez. Özniteliklerin kalıcı saklanması etik/kurumsal karar sonrasına bağlıdır. Şimdilik yalnız sentetik örnek üretilir.

## 2. Kimlikler ve ortak alan kuralları

- `participant_id`: `str`; kişiyi doğrudan tanımlamayan, araştırmaya özgü rastgele/pseudonim kod. Gerçek kişi adları burada bulunmaz. Aynı kişi için tüm oturumlarda sabittir.
- `session_id`: `str`; oturumun benzersiz kodu; `participant_id` ile ilişkilidir.
- `session_type`: enum `SCENARIO` / `FREE` (20 dakika senaryolu, 10 dakika serbest).
- `timestamp_ms`, `start_ms`, `end_ms`: `int` ≥ 0; **oturumun video zaman çizelgesinde** milisaniye. Bütün zaman aralıkları **yarı açık** `[start_ms, end_ms)` ve `end_ms > start_ms`.
- `schema_version`: `str` (bu sürüm `0.2.0`); veri dosyası yapısını izler. `feature_version`, `label_version`, `resolution_policy_version` ayrıdır.
- Kayıp sayı için `null` kullanılır; `0` gerçek sayısal ölçüm anlamına gelir. İlgili durum bayrağı ayrıca tutulur.
- Tarih/saat gerekirse yalnız oturum üst verisinde ISO 8601 olarak tutulur; **ölçüm süreleri duvar saati farkından hesaplanmaz**.

## 3. Kayıt sözleşmeleri

Aşağıdaki tablolar **mantıksal sözleşmedir**; henüz çalışan kod ya da gerçek gönüllü veri dosyası değildir. Sonraki aşamada sentetik JSON/CSV ve Python dataclass'larına dönüştürülecek.

### 3.1 `SessionRecord` — oturum üst verisi

| Alan | Tip / değer | Amaç |
| --- | --- | --- |
| `session_id` | str, zorunlu, benzersiz | Oturum anahtarı |
| `participant_id` | str, zorunlu | LOSO gruplama anahtarı |
| `session_type` | `SCENARIO` / `FREE` | Oturum türü |
| `duration_ms` | int ≥ 0 | Oturumun video zamanındaki gerçek süresi |
| `source_mode` | `LIVE` / `FILE` / `SYNTHETIC` | Video kaynağı |
| `source_id` | str | Kişisel veri veya tam dosya yolu içermeyen kaynak kodu |
| `camera_setup_id` | str veya null | Sabit kamera kurulum referansı |
| `camera_position`, `camera_angle_note` | str veya null | Konum/açı açıklaması; ölçülmediyse `null` |
| `width_px`, `height_px` | int veya null | Çözünürlük |
| `nominal_fps`, `measured_fps` | float veya null | Kaynak/gerçekte işlenen kare hızı, ayrı ayrı |
| `dropped_by_source` | int ≥ 0 veya null | Kamera/sürücünün düşürdüğü kareler; zaman damgası aralıklarındaki boşluklardan kestirilir |
| `skipped_by_pipeline` | int ≥ 0 | İşleme yetişilemediği için bilerek atlanan kareler (`LIVE`); `FILE` modunda 0 |
| `schema_version` | str | Şema sürümü |

Gerçek kişiye ait isim, iletişim ve kimlik eşlemesi bu şemada **bulunmaz**. Kamera kurulumu mümkün olduğunca oturumlar arasında sabit tutulur; değişirse ayrıca kaydedilir.

### 3.2 `FrameRecord` — kare akışı (kalıcı saklama zorunlu değil)

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `session_id` | str | Oturum referansı |
| `frame_index` | int ≥ 0 | Kaynak kare sırası; atlanan kareler sırada boşluk olarak görünür |
| `timestamp_ms` | int ≥ 0 | Oturum-başlangıçlı **video zaman damgası** |
| `frame` | bellekte görüntü nesnesi | **GitHub'a ve FeatureStore'a ham kare yazılmaz** |
| `source_status` | enum / hata kodu | OK, READ_ERROR, SKIPPED vb. |

**Zaman kaynağı:** `FILE` modunda konteynerin/video akışının kare sunum zamanı (presentation timestamp) kullanılır; dosyanın işlendiği duvar/CPU zamanı kullanılmaz. `LIVE` modunda kamera/sürücü gerçek yakalama zaman damgası sağlamıyorsa oturum başlangıcına göre monotonik saatle kare **okuma zamanı** ölçülür (işleme bitiş zamanı değil). Bu değer OpenCV tamponu nedeniyle gerçek yakalama zamanı olmayabilir. Her iki modun `timestamp_ms` alanı oturum başlangıcına göre tanımlanır; ölçüm kaynağı ve olası gecikme kaydedilir.

**Araştırma kaydı ilkesi:** Araştırma oturumları önce video dosyasına kaydedilir ve öznitelikler bu dosyadan `FILE` modunda çıkarılır. İnsan etiketleri de aynı dosya üzerinde yapıldığından öznitelikler ve etiketler tek bir video zaman çizelgesini paylaşır. `LIVE` modu yalnız demo/yerel arayüz içindir; `LIVE` modunda ölçülen zaman, OpenCV tamponu nedeniyle kare yakalama değil **okuma** zamanı olabilir ve bu sınırlılık raporda belirtilir. Kayıt mümkünse sabit kare hızıyla yapılır; değilse kare zaman damgaları ayrıca saklanır.

**Kare politikası:** `LIVE` için işleme yetişilemiyorsa en son kareyi tercih eden sınırlı kuyruk ve atlanan kare sayacı; `FILE` için varsayılan tüm kareleri işleme. Bunlar Faz 3'te ölçülecek uygulama kararlarıdır. Video zamanı sabit ardışık FPS varsayımıyla türetilmez; değişken kare aralıkları korunur.

### 3.3 `FeatureRecord` — türetilmiş ölçüm

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `session_id`, `frame_index`, `timestamp_ms` | str, int, int | Kaynak izlenebilirliği |
| `feature_version` | str | Çıkarıcı/öznitelik kümesi sürümü |
| `head_yaw_deg`, `head_pitch_deg`, `head_roll_deg` | float veya null | Baş yönelimi, **derece**, kişiye göre: `pitch > 0` baş aşağı eğik (kâğıda bakma yönü), `yaw > 0` baş kişinin sağına dönük, `roll > 0` baş kişinin sağ omzuna yatık. MediaPipe yüz dönüşüm matrisinden hesaplanır (burun yönünden pitch/yaw, yüzün yukarı yönünden roll); ayrıntı `features/face.py` |
| `eye_aspect_ratio_left`, `eye_aspect_ratio_right` | float veya null | Göz açıklık oranı (EAR); yardımcı göstergedir, bakış noktası ölçülmez (v5 2.4) |
| `hand_count` | int 0–2 veya null | Algılanan el sayısı; el bileşeni çalışmadıysa `null` |
| `left_wrist_x`, `left_wrist_y`, `right_wrist_x`, `right_wrist_y` | float [0,1] veya null | Bilek konumu, görüntü genişliği/yüksekliğine göre normalize; el yoksa `null`. Yazma hareketi pencere düzeyinde bu alanların değişkenliğinden hesaplanır |
| `hand_phone_distance_norm` | float ≥ 0 veya null | Ele ait en yakın işaret noktası ile telefon kutusu merkezi arasındaki uzaklık / görüntü köşegeni; telefona uzanma göstergesi. El veya telefon yoksa `null` |
| `hand_phone_overlap` | bool veya null | En az bir el işaret noktası telefon kutusunun içinde mi; telefonu tutma göstergesi. El veya telefon yoksa `null` |
| `phone_score` | float [0,1] veya null | "cell phone" sınıfı için en yüksek tespit güveni (MediaPipe Object Detector, EfficientDet-Lite0) |
| `phone_box_x`, `phone_box_y`, `phone_box_w`, `phone_box_h` | float [0,1] veya null | En güvenli telefon kutusu, normalize; telefon yoksa `null` |
| `face_status` | `VALID`, `NOT_DETECTED`, `LOW_CONFIDENCE`, `OCCLUDED` | “Yüz yok” ve “düşük güven” ayrılır |
| `phone_status` | `VISIBLE`, `NOT_VISIBLE`, `OCCLUDED`, `NOT_EVALUATED` | “Görünmüyor” doğrudan “ortamda yok” değildir |
| `hand_status` | `VALID`, `NOT_DETECTED`, `OCCLUDED`, `NOT_EVALUATED` | Bağımsız el bileşeni için |
| `validity_flags` | adlandırılmış booleans (`head_pose_valid`, `eye_features_valid`, `hand_features_valid`, `phone_features_valid`) | Yalnız alan bazlı geçerlilik; bileşen durumu için **esas kaynak** `face_status` / `phone_status` / `hand_status` alanlarıdır |

**Sınır:** Telefonun yalnız görünmesi `TELEFON` sınıfını kanıtlamaz; el göstergeleriyle birlikte yorumlanır. Tam yüz ve el landmark koordinatları varsayılan depolama şemasına **alınmamıştır**; yalnız yukarıdaki türetilmiş alanlar tutulur. El alan adları P4-03 (el/bilek öznitelikleri) uygulamasında ekipçe gözden geçirilir; değişiklik önce bu belgede yapılır. Bu alanların saklanabilirliği, veri minimizasyonu ve etik/kurumsal izin henüz netleşmemiştir. `FeatureRecord` şimdilik bellekte/sentetik testlerde kullanılabilir.

### 3.4 `WindowRecord` — 2 saniyelik özet

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `session_id`, `window_index` | str, int | Oturum ve pencere |
| `start_ms`, `end_ms` | int, int | `[start,end)`; varsayılan pencere uzunluğu 2.000 ms |
| `aggregates` | sürümlü sayısal alanlar | Her sayısal `FeatureRecord` alanı için `<alan>_mean`, `<alan>_std` (değişkenlik) ve `<alan>_delta` (son geçerli değer − ilk geçerli değer); boolean alanlar için oran (`<alan>_ratio`). Geçerli değer yoksa `null` |
| `face_detected_ratio` | float [0,1] veya null | Penceredeki karelerden `face_status = VALID` olanların oranı; M0'ın %50 `BELIRSIZ` kuralı bunu kullanır |
| `available_frame_count` | int ≥ 0 | Penceredeki işlenen geçerli kare sayısı |
| `coverage_ratio` | float [0,1] veya null | Kanıt kapsaması, hesaplama tanımı belgelenmeli |
| `is_valid`, `invalid_reason` | bool, str veya null | Geçerlilik kararı; boş pencere geçersizdir |
| `train_label` | `MATERYAL` / `TELEFON` / `DIS_YON` / `GECIS` / `UNUSED` veya null | İnsan etiketinden hesaplanan M1 eğitim hedefi (`labeling-protocol.md` 5.3); `GECIS` ve `UNUSED` eğitime girmez; etiket yoksa (canlı mod) `null` |
| `feature_version` | str | Girdi uyumu |

Pencereler `[0,2000)`, `[1000,3000)`, `[2000,4000)` ... şeklindedir. Eksik değerler `null` kalır; eksik kanıt hiçbir zaman `MATERYAL` sayılmaz. **Asgari kare sayısı ve kapsama eşiği henüz belirlenmedi**; kamera ölçümüne göre ekipçe sabitlenecek. Bir pencereyi salt kare sayısı ile geçerli varsaymayız.

### 3.5 `HumanLabelInterval` ve `SecondReference`

| Kayıt | Temel alanlar | Açıklama |
| --- | --- | --- |
| `HumanLabelInterval` | `session_id`, `annotator_id` (etiketleyici kodu, ör. `A1`), `label_round` (`r1` / `r2` / `final`), `start_ms`, `end_ms`, `label`, `label_version` | İnsan gözlemcinin ELAN'daki zaman aralığı etiketi; `label` ∈ `MATERYAL` / `TELEFON` / `DIS_YON` / `BELIRSIZ` |
| `SecondReference` | `session_id`, `second_start_ms`, `label`, `validity`, `annotator_id`, `label_round`, `label_version`, `agreement_status` | `LabelAligner`'ın ürettiği tekil 1 saniye referansı; `label` ∈ `MATERYAL` / `TELEFON` / `DIS_YON` / `BELIRSIZ` / `GECIS` (kodda `core.labels.Label`); `validity` belirsizliğin kaynağını ayırır: `LABELED` / `UNCERTAIN` / `UNLABELED` |

İnsan referans sınıfları `MATERYAL`, `TELEFON`, `DIS_YON`; ELAN'daki `BELIRSIZ` etiketi (`validity` = `UNCERTAIN`) ve hiçbir aralığa düşmeyen süre (`validity` = `UNLABELED`) 1 sn referansta `Label.BELIRSIZ` olur; model tarafıyla aynı değer kullanıldığı için metrikler iki tarafa aynı kuralla uygulanır (ana sınıf değildir). Bir saniyede bir ana sınıf 500 ms'den fazlasını kaplıyorsa saniye o sınıfı alır; belirsiz + etiketsiz süre 500 ms veya fazlaysa `BELIRSIZ`; aksi halde (ör. 500/500) `GECIS` (`labeling-protocol.md` 5.2). `agreement_status`, tekrar setindeki saniyelerde `r1` ile `r2` karşılaştırmasını gösterir: `AGREE` / `DISAGREE` / `NOT_IN_RETEST`. Etiket güvenirliği, videonun en az %25'inin aynı etiketleyici tarafından en az 4 hafta sonra kör olarak yeniden etiketlenmesiyle (test–tekrar test) Cohen's Kappa ile ölçülür.

### 3.6 `Prediction` ve `SecondDecision`

| Kayıt | Temel alanlar | Açıklama |
| --- | --- | --- |
| `Prediction` | `session_id`, `window_index`, `start_ms`, `end_ms`, `model_id` (`M0` / `M1` / `MAJORITY`), `label`, `score_or_null`, `reason` | Pencere tahmini; `BELIRSIZ` gerekçeleri: `LOW_FACE_RATIO`, `RULE_CONFLICT` (M0), `LOW_CONFIDENCE` (M1) |
| `SecondDecision` | `session_id`, `second_start_ms`, `label`, `source_window_start_ms`, `source_window_end_ms`, `resolution_policy_version`, `coverage_ratio`, `reason` | Tekil saniye kararı |

`TimelineResolver` için ekipçe kilitlenen politika (`architecture.md` 4.1, `resolution_policy_version` = `trp-0.1.0`): tamamlanmış 2 sn pencerenin tahmini son 1 sn'ye atanır; ilk saniye yalnızca ilk geçerli pencereyle bootstrap edilir; tahmini olmayan saniye `BELIRSIZ` olur. Her `session_id + second_start_ms` için tek karar vardır; saniyeler çifte sayılmaz.

### 3.6.1 `InterruptionEvent` — görünür kesinti

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `session_id` | str | Oturum |
| `label` | `TELEFON` / `DIS_YON` | Kesintinin sınıfı |
| `start_ms`, `end_ms` | int, int | `[start,end)`, 1 sn dilim sınırlarında; süre ≥ eşik (varsayılan 3000 ms) |
| `source` | `MODEL` / `REFERENCE` | Model saniye kararlarından mı, insan referansından mı üretildi |
| `model_id`, `threshold_ms` | str veya null, int | Kaynak model (`REFERENCE` için `null`) ve kullanılan eşik (duyarlılık analizinde 2000 / 5000) |

Kural (`labeling-protocol.md` bölüm 6): aynı sınıftan ardışık en az 3 sn; farklı sınıflar art arda ayrı durumdur; `BELIRSIZ` / `GECIS` saniyesi kesintiyi böler; yumuşatma yoktur. Olay F1 için model ve referans olayları aynı sınıfta ve başlangıç farkı ±2 sn içindeyse bire bir eşleşir. Odak oranının paydasına `BELIRSIZ` ve `GECIS` saniyeleri girmez.

### 3.7 `ExperimentRecord` — tekrarlanabilir LOSO

Zorunlu izleme alanları: `experiment_id`, `created_at`, `git_commit`, `schema_version`, `feature_version`, `label_version`, `resolution_policy_version`, `test_participant_id`, `train_participant_ids`, `model_id`, `model_params`, `metrics`, `artifact_path`, `notes`.

**LOSO değişmezi:** `test_participant_id` hiçbir zaman `train_participant_ids` içinde bulunamaz. Aynı kişinin `SCENARIO` ve `FREE` oturumları aynı dış test katlamasında kalır. M0 eşikleri ve M1 eğitim/ön işleme yalnız eğitim kişileriyle belirlenir.

## 4. Dosya/klasör yaklaşımı ve veri güvenliği

Önerilen, **henüz yetkilendirilmemiş gerçek veri için kullanılmayacak** mantıksal yollar:

```text
# GitHub'a girebilen: şema, kod, test ve gerçek kişi içermeyen sentetik örnekler
docs/data-schema.md
tests/fixtures/synthetic_sessions.json

# Yalnız gerekli kurum kararı sonrası, erişim kontrollü yerel depolama
local_data/raw_video/          # ham kayıt; GitHub'a ASLA gönderme
local_data/derived_features/   # izin kapsamındaki seçilmiş öznitelikler
local_data/labels/             # katılımcı kodlarına bağlı insan etiketleri
local_data/identity_mapping/   # ayrı tutulur, yetkisi sınırlandırılır
local_data/experiments/        # sonuçlar kişisel veriden arındırılmadan paylaşılmaz
```

Önerilen `.gitignore` girdisi: `local_data/`, `.venv/`, `.env`, `installed-packages.txt`; ancak gerçek kişi verilerini yalnızca `.gitignore` ile korumak yeterli değildir (erişim ve şifreleme/transfer politikaları da gerekir). Gerçek gönüllü görüntüleri için **etik/kurumsal uygunluk ve katılımcı süreçleri tamamlanmadan kayıt yok**.

## 5. Doğrulama ve kabul testleri (Faz 2.3)

1. **Şema:** zorunlu kimlik/zaman alanları ve sürümler mevcut; `end_ms > start_ms`.
2. **Zaman:** kareler oturum içinde monoton artan video zaman damgası taşır; dosya modunda işlem süresi ile karıştırılmaz.
3. **Pencere:** `[0,2000)` ve `[1000,3000)` doğrulanır; sınırdaki kare tek pencereye doğru yarı açık aralık kuralıyla atanır.
4. **Tekil saniye:** her `session_id + second_start_ms` için tek `SecondDecision`; örtüşme süreyi ikiye katlamaz.
5. **Eksik kanıt:** `NOT_VISIBLE` ile `NOT_EVALUATED`, `NOT_DETECTED` ile `LOW_CONFIDENCE` ayrılır; eksik veriden zorla ana sınıf üretilmez.
6. **Etiket:** insan etiketleri aynı video zaman çizelgesine hizalanır; 500/500 eşitlik `GECIS`, belirsiz/etiketsiz durumlar açık işaretlenir; `train_label` kuralı sınır değerlerinde (999/1001 ms, 1000/1000) doğru çalışır.
7. **Kesinti:** aynı sınıf 3 sn kesinti sayılır; 2 sn `TELEFON` + 2 sn `DIS_YON` sayılmaz; araya giren `BELIRSIZ` böler; ±2 sn bire bir eşleştirme.
8. **LOSO:** bir katılımcı aynı fold'da train ve testte olamaz.
9. **Güvenlik:** sentetik örnekler gerçek kişisel veri içermez; gerçek verinin Git'e girmemesi kontrol edilir.

Faz 2'de en az bir küçük sentetik fixture ve test eklenmesi planlanır; **bu belge tek başına testlerin çalıştığı anlamına gelmez**.

## 6. Açık kararlar ve sorumluları

| Karar | Önerilen sahip | Tamamlanma zamanı |
| --- | --- | --- |
| ~~`head_pitch_deg` ve diğer açıların işaret yönü~~ | Bahar | **Kapandı (#32):** şablondan ve canlı kontrolle doğrulandı, §3.3 |
| ~~Sabit `eye_features` alan listesi~~ | Bahar | **Kapandı (v0.2):** göz açıklık oranı (EAR), sol/sağ |
| Pencere asgari kare/kapsama eşiği | Bahar + Pınar | Kamera ölçümü / Faz 2.4 |
| ~~İnsan etiketinden M1 pencere hedefi~~ | Ortak | **Kapandı:** milisaniyelik çoğunluk kuralı, `train_label` (`labeling-protocol.md` 5.3) |
| ~~`TimelineResolver` başlangıç politikası~~ | Pınar + Bahar | **Kapandı:** `architecture.md` 4.1, politika 1.0 |
| ~~BELİRSİZ ve boş referans saniyelerinin metrikte ele alınışı~~ | Ortak | **Kapandı:** kesintiyi böler, odak oranı paydasına girmez (`labeling-protocol.md` 6) |
| El öznitelik alan adlarının uygulamada doğrulanması | Pınar (P4-03) | Faz 4 |
| Depolanabilir türetilmiş öznitelikler, erişim, saklama ve imha | Danışman/kurum + ortak | İzin kararı sonrası |
| Gerçek kamera çözünürlük/FPS, kare düşmesi ve kurulum sabitliği | Bahar | Donanım testleri |

**Bahar'ın ölçüm notu:** Dahili HP True Vision FHD kamera için raporladığı yaklaşık değerler: 720p ≈ 30 FPS, 1080p ≈ 30 FPS, 640×480 ≈ 13,3 FPS. Bunlar ekip içi ön ölçümlerdir; harici kamera performansı anlamına gelmez.

## 7. Faz 2.3 çıkış kriteri

- [ ] Alanların tipleri ve sürümleri ekipçe gözden geçirildi.
- [ ] Oturum, kare, öznitelik, pencere, insan etiketi ve tekil saniye kayıtları ortak zaman sözleşmesine uyuyor.
- [ ] LOSO katılımcı ayrımı açıkça doğrulandı.
- [ ] Sentetik fixture ve şema/zaman testi eklendi veya ayrı test Issue'sunda açıkça izlendi.
- [ ] Etik karara bağlı veri saklama alanları **onay alınmış gibi gösterilmedi**.
- [ ] Bahar ve Pınar GitHub PR incelemesini tamamladı.

**Referanslar:** `docs/architecture.md` v0.3 (özellikle 4.1–4.4); `docs/labeling-protocol.md` (bölüm 5, 6, 10); TÜBİTAK 2209-A önerisi v5 (2.4, 2.5, 2.7).

## Revizyon kaydı

- **v0.1 (9 Kasım 2026):** İlk şema ve zaman sözleşmesi.
- **v0.2 (25 Kasım 2026, #23):** v5 ve etiketleme protokolüyle uyum: `FeatureRecord`'a göz açıklık oranı, el/bilek ve telefon alanları; `WindowRecord`'a özet alanları, `face_detected_ratio`, `train_label`; `HumanLabelInterval` / `SecondReference`'a `label_round` ve `GECIS`; `Prediction` için `BELIRSIZ` gerekçe kodları ve `MAJORITY` tabanı; yeni `InterruptionEvent`; çift etiketleme yerine test–tekrar test; kapanan açık kararlar işaretlendi.
