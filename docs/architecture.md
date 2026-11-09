# Faz 2.1 — Yazılım Mimarisi (İnceleme revizyonu v0.2)

**Proje:** Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi  
**Sorumlular:** Bahar + Pınar  
**Durum:** Bahar incelemesi sonrası revizyon; 8 ve 9 numaralı yorumlar için mimari akış eklendi. Nihai ekip onayı, kamera ve etik/kurumsal süreç bekleniyor.  
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
| `FeatureExtractor` | `FrameRecord` | `FeatureRecord(timestamp_ms, head_pose, eye_features, phone_cues, validity_flags)` | yüz yok, örtülme, düşük güven |
| `WindowBuilder` | zaman sıralı `FeatureRecord` | `WindowRecord(start_ms, end_ms, aggregates, coverage)` | boş pencere, düzensiz zaman damgası |
| `Classifier` | `WindowRecord` + model konfigürasyonu | `Prediction(label, confidence_or_score, reason)` | eksik kanıt -> `BELIRSIZ` |
| `TimelineResolver` | pencere tahminleri + zaman sınırları + kapsama/kalite | `SecondDecision(second_start_ms, label, provenance)` | çelişen tahmin, boş/eksik dilim -> `BELIRSIZ` |
| `SessionMetrics` | tekil saniye kararları | süre, kesinti sayısı, BELİRSİZ oranı | çifte sayım, zaman boşlukları |
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
- En az 3 saniye kesintinin tanımı, geçiş/histerezis ve `BELIRSIZ` aralıklarının nasıl ele alınacağı `docs/labeling-protocol.md` içinde karar olarak kilitlenecek.

## 4.1 Pencereden tekil saniyeye geçiş (`TimelineResolver`) — yorum 8

**Sorun:** `[0,2)` ve `[1,3)` pencerelerinin kararları aynı saniyeye temas edebilir; pencere etiketlerinin sürelerini toplamak geçersizdir. `Classifier`, yalnızca **pencere tahmini** üretir. Süre ve kesinti hesabı `TimelineResolver` sonrasında yapılır.

**Bu mimari revizyonda önerilen, kodlanmadan önce `labeling-protocol.md` ile doğrulanacak deterministik başlangıç politikası:**

1. Oturum zamanı `[0,1000)`, `[1000,2000)` ... şeklinde **örtüşmeyen** 1.000 ms dilimlere ayrılır. Her dilim için **en fazla bir** `SecondDecision` saklanır.
2. Tamamlanmış `[t-2000,t)` penceresinin tahmini, öncelikle **son** `[t-1000,t)` dilimine atanır. Böylece `[0,2)` penceresi `[1,2)` saniyesini, `[1,3)` penceresi `[2,3)` saniyesini kararlaştırır. Aynı saniyeyi iki pencere oylamaz; aşağıdaki başlangıç kuralı hariç hiçbir saniye yeniden yazılmaz.
3. Oturumun ilk `[0,1)` saniyesi, ancak ilk `[0,2)` penceresi yeterli kanıtla geçerli olduğunda onun etiketiyle **başlangıç (bootstrap)** olarak doldurulur; aksi halde `BELIRSIZ` kalır. Böylece başlangıç saniyesi atlanmaz.
4. Eksik/kalitesiz pencere veya yeterli kanıt bulunmaması ilgili tekil saniyeye `BELIRSIZ` verir. Bir saniyeye başka bir pencerenin güvenilir tahminini kaydırarak boşluk kapatılmaz. Sonunda tam pencere üretilemeyen parça raporda **kapsanmayan süre** olarak ayrıca gösterilir; otomatik `MATERYAL` sayılmaz.
5. Saniye dilimleri `second_start_ms` ile tekil anahtarlanır; örtüşen pencere tahminleri **doğrudan toplanmaz**. `MATERYAL` yönelim süresi, `MATERYAL` kabul edilmiş tekil saniyelerin sayısından hesaplanır. Kesinti için ardışık, geçerli `MATERYAL` dışı dilimler kullanılır; `BELIRSIZ` kesintiyi otomatik doğrulamaz (kesintiyi ayıran/askıya alan nihai politika etiketleme protokolünde sabitlenecek).
6. Her karar `source_window_start_ms`, `source_window_end_ms`, `resolution_policy_version`, `coverage` ve `reason` alanlarıyla izlenebilir olur.

**Örnek:** `P0=[0,2):MATERYAL`, `P1=[1,3):TELEFON`, `P2=[2,4):MATERYAL` ⇒ tekil saniyeler `[0,1)=MATERYAL` (bootstrap), `[1,2)=MATERYAL`, `[2,3)=TELEFON`, `[3,4)=MATERYAL`. Toplam yönelim süresi 3 sn'dir; pencere süreleri toplanmaz. Bu yalnızca tasarım örneğidir, gerçek veri sonucu değildir.

**Faz 2 otomatik testleri:** saniye başına tek kayıt; çelişen iki pencerede deterministik sonuç; boş pencere/belirsizlik; 3 sn kesinti sınırı; 2 sn pencerelerin iki kez sayılmaması; oturum başlangıcı ve kapanışı. Bu politika çalışma başlamadan önce ekipçe sürümlenerek kilitlenmelidir; aksi halde süre MAE karşılaştırması değişebilir.

## 4.2 İnsan etiketi, öznitelik deposu ve M0/M1 eğitim yolu — yorum 9

**İki ayrı veri kolu:** (a) video karelerinden **model öznitelikleri**, (b) insan gözleminden **referans davranış etiketleri**. İnsan etiketleri modelin tahmini değildir. İki kol oturumun aynı **video zaman ekseninde** birleştirilir. Zaman damgasının kesin üretim kuralı (canlı/kayıtlı video farkı), Bahar'ın 1. yorumuyla Faz 2.3 veri şemasında netleştirilecektir.

1. **İzinli veri edinimi:** Etik/kurumsal uygunluk ve bilgilendirme tamamlanmadan gönüllü video kaydı yapılmaz. Prototip testleri fake `VideoSource` / sentetik kayıtlarla yürür.
2. **Bir kez öznitelik çıkarımı:** İzinli videolar yerelde işlenerek her zaman adımı için yalnızca araştırmada gerekli, etik onayla uyumlu **seçilmiş türetilmiş öznitelikler** oluşturulur. *Tüm yüz landmark koordinatlarının saklanacağı varsayılmıyor.* Saklanacak alanlar, gerekçe, sürüm, erişim ve imha kuralları etik kontrol ve veri şemasında ayrıca onaylanacak. Kodlanmış öznitelikler otomatik olarak anonim sayılmaz.
3. **İnsan etiketleri:** Bağımsız etiketleyiciler gözlenen davranışı oturum-zaman aralıklarıyla işaretler. `LabelAligner` bu aralıkları `[s,s+1)` tekil saniyelerine hizalar. Örtüşen, belirsiz, kapsanmayan ve uyuşmazlık bulunan saniyeler açıkça işaretlenir; nihai uzlaşı ve çift etiketleme kuralları `labeling-protocol.md` içinde tanımlanır.
4. **Pencere kurma:** Onaylı öznitelik dizisinden `[0,2)`, `[1,3)` ... pencereler elde edilir. M1'in eğitim hedefi için pencerenin iki saniyelik referans etiketlerinin nasıl birleştirileceği **henüz açık metodolojik karar**dır (ör. yalnız iki saniye aynı, geçerli ana etiketse sınıfa dahil et; aksi halde eğitimden çıkar / belirsiz işaretle). Bu kural sonuçlara bakılarak sonradan değiştirilmez; Faz 2.4'te kilitlenir.
5. **Katılımcı-bazlı LOSO:** Her dış katlamada bir katılımcının **tüm** oturumları testte tutulur. `FeatureStore` yalnız izin verilen işlenmiş kayıtları sağlar; imputation, eşikler, özellik seçimi ve M1 ayarları **sadece eğitim katılımcılarından** öğrenilir. M0 ve M1 aynı katlamalar üzerinde sınanır.
6. **Eğitim/değerlendirme:** M0 için eğitim katılımcıları üzerinden eşik belirleme; M1 için yine yalnız eğitim katılımcılarının pencereleri üzerinde `RandomForest.fit`. Test kişisinde pencere tahminleri `TimelineResolver` ile tekil saniye tahminlerine dönüştürülür ve 1 sn insan referanslarıyla karşılaştırılır. Macro-F1, sınıf bazlı F1, belirsiz oranı, süre MAE ve kesinti hatası kişi bazında raporlanır. BELİRSİZ dördüncü ana eğitim sınıfı değildir; referansla eşleştirme ve metrik kapsamı ayrıca sabitlenecektir.
7. **Tekrarlanabilirlik:** Veri/etiket sürümleri, erişim kontrollü öznitelik yolu, `feature_version`, `resolution_policy_version`, kod commit'i, fold, model parametreleri ve metrikler deney günlüğüne kaydedilir. `FeatureStore` fiziksel dosya şeması ve saklanacak tam alanlar Faz 2.3'te kesinleşir.

**Güvenlik sınırı:** Ham kare/video, kişi eşleme listesi ve kişisel veri içeren türevler GitHub'a veya üçüncü taraf buluta gönderilmez. Özniteliklerin diske yazılması, etik/kurumsal karar ve veri minimizasyonu onayından sonra uygulanır; öncesinde sadece sentetik veriler saklanır.

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

- **Harici kamera:** Model, bağlantı, çözünürlük ve gerçek FPS bilinmiyor. `VideoSource` arayüzü sabitlenip kamera adaptörü sonra uygulanabilir. Bahar, dahili **HP True Vision FHD** kamerayla 640×480 çözünürlükte yaklaşık **13 FPS** ölçtüğünü bildirmiştir; bu ölçümün koşulları ve tekrar doğrulaması risk kaydında tutulacak, harici kamera için sonuç varsayılmayacaktır.
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

## 9.1 Bahar incelemesinden kalan takip maddeleri (sonraki PR / Faz 2.3–2.5)

Aşağıdakiler **bu revizyonda tamamlanmış sayılmamıştır**; ilgili Issue'lara aktarılmalıdır:

1. Canlı ve dosya video zaman damgalarının aynı oturum-başlangıçlı **video zamanı** sözleşmesiyle ifade edilmesi; kayıtlı video için işlem saati kullanılmaması.
2. `FrameRecord.frame_index`, gerçek FPS, atlanan kare sayısı ve pencere asgari kapsama/kare sayısı.
3. Canlı modda en yeni kareyi tercih eden gecikme politikası ile kayıtlı video modunda tüm kareleri işleme politikasının ayrıştırılması.
4. Kamera konumu/açısı, çözünürlük ve kurulumun oturum meta verisine alınması ve protokol boyunca sabitlenmesi.
5. Yüz/baş, el ve telefon ipuçlarının takılıp çıkarılabilir ayrı çıkarım bileşenleri olması; telefonda başlangıçta boş adaptör.
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
