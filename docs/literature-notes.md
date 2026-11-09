# Faz 1.2 — Literatür taraması ve bilimsel yöntem gerekçesi

**Proje:** Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi  
**Tarih:** 9 Kasım 2026  
**Durum:** Kaynak taraması ve yöntem sentezi tamamlandı; ekip/danışman incelemesine açık.  
**Dayanak:** 8 haftalık iç yol haritası; bilimsel kapsam değiştirilmemiştir.  
**Tarama türü:** Hedefli, anlatısal literatür incelemesi. Sistematik derleme veya bütün yayınların tarandığı iddia edilmez. Bu notlar veriyle doğrulanmış proje sonuçları değildir.

## 1. Araştırma sorusu ve kapsam sınırı

Araştırma sorusu: **Tek RGB kamera ile elde edilen baş pozu, seçilmiş yüz/göz göstergeleri ve görünür telefon etkileşimi ipuçları kullanılarak, kâğıt tabanlı masa başı çalışma sırasında gözlenebilir yönelim durumu (MATERYAL / TELEFON / DIŞ_YÖN) ve materyale yönelim süresi, daha önce görülmemiş katılımcılarda ne ölçüde kestirilebilir?**

Üç ana sınıf **MATERYAL, TELEFON, DIŞ_YÖN**. **BELİRSİZ** dördüncü davranış sınıfı değil; yetersiz veya çelişen kanıtta verilen özel çıktıdır. Baş pozu tek başına bakış noktasını veya bilişsel dikkati kanıtlamaz. Öğrenme, konsantrasyon, niyet, psikolojik durum ve gerçek bilişsel odak iddiasında bulunulmaz. “Odak süresi”nin operasyonel karşılığı, **materyale görünür yönelim için kestirilen süredir**.

Sabit tasarım: 8–10 yetişkin; katılımcı başına 20 dk senaryolu + 10 dk serbest oturum; tek kamera; 2 sn analiz penceresi / 1 sn kaydırma; M0 kural tabanlı, M1 Random Forest; katılımcı bazlı LOSO; Macro-F1, sınıf F1, Cohen Kappa, BELİRSİZ oranı, yönelim süresi ve kesinti hataları. Önce etik ve hukuki süreç; izin olmadan tanınabilir gönüllü videosu kaydedilmez.

## 2. Tarama yaklaşımı

Kaynaklar, çalışma başlığının doğrudan eşleşmesinden çok tasarım risklerini kapsaması için beş eksende incelendi: (A) göz/bakış ve baş pozu, (B) eğitimde gözlenebilir dikkat ve geçerlilik, (C) telefon davranışı, (D) katılımcı-bağımsız doğrulama ve (E) etiket güvenilirliği/teknik araçlar. Öncelik hakemli yayınlar, birincil araştırma sayfaları ve resmî kütüphane dokümantasyonudur. Erişilebilen özet ve tam metin bölümleri kontrol edilmiştir; bütün makalelerin tüm ekleri veya kodları yeniden üretilmemiştir.

Örnek aramalar (İngilizce): `appearance-based gaze estimation in the wild`, `student attention head pose gaze facial features classroom`, `webcam distraction phone use head pose`, `leave one subject out validation human activity recognition`, `Cohen kappa prevalence agreement`, `MediaPipe Face Landmarker output`.

## 3. Kaynak bazlı eleştirel inceleme

### [S1] Zhang ve ark., 2015 — Appearance-Based Gaze Estimation in the Wild
- **Tür:** CVPR araştırma makalesi; DOI: 10.1109/CVPR.2015.7299081.
- **Gerçek bulgu:** MPIIGaze, 15 kişinin günlük dizüstü bilgisayar kullanımından 213.659 görüntü içerir; kişi/aydınlatma farklılıkları ve veri kümesi dışı genelleme önemlidir.
- **Bizim için:** Işık, gözlük, kamera konumu ve katılımcı farklılığını sistematik risk olarak kaydet.
- **Aktarım sınırı:** Ekran bakışı tahmini ile masadaki kâğıda bakma aynı görev değildir; bu veri kümesinin performansı bizim projemizin performansı olamaz.
- https://openaccess.thecvf.com/content_cvpr_2015/html/Zhang_Appearance-Based_Gaze_Estimation_2015_CVPR_paper.html

### [S2] Zhang ve ark., 2019 — MPIIGaze: Real-World Dataset and Deep Appearance-Based Gaze Estimation
- **Tür:** IEEE TPAMI; DOI: 10.1109/TPAMI.2017.2778103 (çevrim içi yayın 2017; cilt 2019).
- **Gerçek bulgu:** Kısıtsız koşullarda tek RGB kameradan bakış tahmininin veri ve değerlendirme güçlüklerini ele alır.
- **Bizim için:** İnce göz takip ölçümü vadetmek yerine kaba yönelim ve eksik kanıt politikasını koru.
- **Aktarım sınırı:** Eğitimli görüntü tabanlı gaze modeli bu projenin M0/M1 sınıflayıcılarıyla aynı şey değildir.
- https://pubmed.ncbi.nlm.nih.gov/29990057/

### [S3] Predicting Students’ Attention in the Classroom from Kinect Facial and Body Features, 2017
- **Tür:** EURASIP Journal on Image and Video Processing; DOI: 10.1186/s13640-017-0228-8.
- **Gerçek bulgu:** Çalışma, gözlemci temelli etiketlerin tutarlılığı, sınırlı katılımcı sayısı, kişiye bağlı davranış farklılıkları ve yüzün/ellerin örtülmesi nedeniyle çıkarım hataları olduğunu açıkça tartışıyor.
- **Bizim için:** Ayrı etiketleme kılavuzu, en az %25 çift etiketleme, kayıp yüz işaretleri ve kişi-bazlı sonuçlar gerekli.
- **Aktarım sınırı:** Kinect'in derinlik/gövde verisi tek sıradan RGB kameraya birebir taşınamaz.
- https://link.springer.com/article/10.1186/s13640-017-0228-8

### [S4] Attentive or Not? Toward a Machine Learning Approach to Assessing Students’ Visible Engagement in Classroom Instruction, 2020
- **Tür:** Educational Psychology Review; DOI: 10.1007/s10648-019-09514-z.
- **Gerçek bulgu:** Görünür öğrenme katılımı göstergeleri için insan puanlaması ve baş pozu, bakış, yüz ifadesi temelli otomatik yaklaşımın pilot değerlendirmesi sunulur; görünür davranış ile bilişsel katılım ayrımı tartışılır.
- **Bizim için:** İddia, görünen yönelimi modellemekle sınırlı; insan etiketlerinin neyi temsil ettiği önceden tarif edilmeli.
- **Aktarım sınırı:** Çalışma sınıf içi etkinliği inceler; kâğıt üzerinde bağımsız masa başı çalışma ile aynı protokol değildir.
- https://link.springer.com/article/10.1007/s10648-019-09514-z

### [S5] Webcam-based Eye Tracking to Detect Mind Wandering and Comprehension Errors, 2023
- **Tür:** Deneysel araştırma; PubMed PMID 36627435.
- **Gerçek bulgu:** Webcam tabanlı göz izlemeyi okuduğunu anlama ve düşünce kayması göstergeleriyle ilişkilendiren iki çalışma; aydınlatma ve gözlüğün etkisi de incelenir.
- **Bizim için:** Kamera temelli göz ölçümünün bağlama, kalibrasyona ve ortama hassas olduğunu hatırlatır.
- **Aktarım sınırı:** Bu çalışmada ek deneysel etiketler/çıktılar bulunmaktadır; yalnız yönelim videosuyla 'mind wandering' teşhisi çıkarılamaz.
- https://pubmed.ncbi.nlm.nih.gov/36627435/

### [S6] Distraction Detection of Lectures in E-Learning Using Machine Learning Based on Human Facial Features and Postural Information, 2022
- **Tür:** Araştırma makalesi; PubMed PMID 36415749.
- **Gerçek bulgu:** Sıradan webcam ile yüz, bakış ve duruş özellikleri; Random Forest ve XGBoost dahil modellerin karşılaştırılması. Özetindeki %90 üzeri recall **kişiye özel eğitim** koşulundadır.
- **Bizim için:** M1 Random Forest, açıkça yorumlanabilir tablosal özniteliklerle uygulanabilir bir başlangıç adayıdır.
- **Aktarım sınırı:** Kişiye özgü yüksek sonuçlar, kişiden bağımsız LOSO performansına kanıt sayılamaz.
- https://pubmed.ncbi.nlm.nih.gov/36415749/

### [S7] Digital Detection of Attention and Distraction Behaviors, 2024
- **Tür:** Procedia Computer Science araştırma makalesi.
- **Gerçek bulgu:** Yüz, baş açısı, iris ve el-yüz ilişkisi gibi davranış özellikleriyle lojistik regresyon, karar ağacı ve Random Forest karşılaştırılır; bildirilen doğruluklar sırasıyla %79, %86, %89'dur.
- **Bizim için:** Baş pozu yanında güvenilirlik bayrakları ve seçili ek görsel kanıtları birleştirme yaklaşımı; M1 seçimi için ek gerekçe.
- **Aktarım sınırı:** Farklı veri ve doğrulama koşulları; doğruluklar kendi deneyimiz için hedef/vaat değildir.
- https://www.sciencedirect.com/science/article/pii/S1877050924023573

### [S8] Biometrics and Behavior Analysis for Detecting Distractions in e-Learning, 2024
- **Tür:** SIIE konferans bildirisi; DOI: 10.1109/SIIE63180.2024.10604582.
- **Gerçek bulgu:** Webcam baş pozu sapmalarından telefon kullanımına işaret edebilecek olayları işaretleme ve insan incelemesi yaklaşımı. Bildirilen >%90 duyarlılık o çalışmanın kendi protokolüne aittir.
- **Bizim için:** Baş yönelimi tek başına 'telefon kullanıyor' etiketi değil, **telefonla ilgili ek doğrulama gerektiren ipucu** olmalı.
- **Aktarım sınırı:** Telefonun kadrajda görünmesi aktif kullanımın kanıtı değildir; e-öğrenme ortamı farklıdır.
- https://discovery.ucl.ac.uk/id/eprint/10196332/

### [S9] AI-Based Multimodal Biometrics for Detecting Smartphone Distractions: Application to Online Learning, 2025
- **Tür:** EC-TEL konferans bildirisi; DOI: 10.1007/978-3-032-03870-8_3.
- **Gerçek bulgu:** Baş pozu ile diğer fizyolojik sinyallerin birleştirilmesiyle telefonla ilişkili dikkat dağılımı araştırılır; raporlanan başarı seçilen sensörler ve senaryoya bağlıdır.
- **Bizim için:** Telefonla etkileşim, kâğıt materyale aşağı bakışla karışabilir; sınıf ayrımında çoklu kanıt ilkesi önemlidir.
- **Aktarım sınırı:** Bizim kapsamımız EEG/kalp hızı veya çoklu biyometrik sensör içermiyor.
- https://discovery.ucl.ac.uk/id/eprint/10211697/

### [S10] How Validation Methodology Influences Human Activity Recognition Mobile Systems, 2022
- **Tür:** Hakemli makale; PMC8954513.
- **Gerçek bulgu:** Rastgele pencere/k-katlı ayırma, aynı katılımcının örnekleri eğitim ve teste girdiğinde performansı yapay yükseltebilir; kişi-bazlı ayırma daha gerçekçi yeni-kişi sınamasıdır.
- **Bizim için:** LOSO bir tercih değil, araştırmanın yeni kişi genellenebilirliği sorusuna uygun test protokolüdür.
- **Aktarım sınırı:** Çalışma mobil sensör etkinlik tanımadır; bizim kamera sistemi için raporlanan yüzdeler doğrudan geçerli değil.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8954513/

### [S11] Landis ve Koch, 1977 — The Measurement of Observer Agreement for Categorical Data
- **Tür:** Biometrics; PMID 843571.
- **Gerçek bulgu:** Kategorik gözlemciler arası anlaşma için şansa göre düzeltilmiş kappa yaklaşımını açıklar.
- **Bizim için:** İki bağımsız etiketçinin aynı zaman birimleri üzerindeki Cohen's Kappa değerini ve sınıf uyuşmazlıklarını raporla.
- **Aktarım sınırı:** Kappa tek başına etiketin nesnel olarak doğru olduğunu göstermez.
- https://pubmed.ncbi.nlm.nih.gov/843571/

### [S12] Zec ve ark., 2017 — High Agreement and High Prevalence: The Paradox of Cohen’s Kappa
- **Tür:** The Open Nursing Journal; DOI: 10.2174/1874434601711010211.
- **Gerçek bulgu:** Dengesiz sınıf dağılımında yüksek gözlenen anlaşmaya karşın kappa düşük çıkabilir.
- **Bizim için:** Kappa yanında ham anlaşma oranı, sınıf dağılımı ve uyuşmazlık tablosu göster; κ < 0,70 sinyalini otomatik başarısızlık hükmü sayma.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC5712640/

### [T1] Google MediaPipe Face Landmarker — Resmî teknik dokümantasyon
- **Tür:** Teknik kaynak, hakemli çalışma değil.
- **Doğrulanmış olanak:** Yüz işaret noktaları, isteğe bağlı yüz dönüşüm matrisleri ve yüz ifadesi katsayıları; Python'da görüntü, video ve canlı akış çalışma modları.
- **Bizim için:** Teknik fizibilite aday aracı. RGB kamera destekler; 3D işaret noktalarından doğrudan güvenilir metrik bakış konumu veya zihinsel dikkat üretildiği varsayılmaz.
- **Kontrol:** Windows/Python paket sürümleri, gerçek FPS, profil/siperlenme ve masa açısı Faz 2–3'te ölçülecek.
- https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker

### [T2] scikit-learn LeaveOneGroupOut — Resmî teknik dokümantasyon
- **Tür:** Teknik kaynak, hakemli çalışma değil.
- **Doğrulanmış olanak:** `groups=participant_id` ile her katlamada bir grubu tamamen dışarıda tutan ayrım.
- **Bizim için:** Aynı kişinin senaryolu ve serbest oturumlarını aynı test katlamasında tut.
- https://scikit-learn.org/stable/modules/cross_validation.html

## 4. Karşılaştırmalı sentez

| Araştırma alanı | Literatürün desteklediği | Desteklemediği | Proje karşılığı |
|---|---|---|---|
| Baş/göz pozu | Kaba gözlenebilir yönelim ipuçları ve kişi/ışık etkileri [S1,S2,S3] | Tek başına kesin dikkat veya kesin masa üzerindeki hedef | Baş, göz, güven ve kayıp bayrakları |
| Eğitimde görünür davranış | İnsan etiketleriyle otomatik görünür katılım göstergelerinin karşılaştırılması [S3,S4] | Bilişsel dikkat ve öğrenme başarısının doğrudan okunması | Operasyonel sınıf tanımları, sınırlı iddialar |
| Telefon | Baş pozu ve ek ipuçlarıyla telefon olaylarını araştırmak [S8,S9] | Telefon göründü = kullanıldı | Etkileşim kanıtı, gerektiğinde BELİRSİZ |
| Model | Tablosal görsel özniteliklerle RF denenebilir [S6,S7] | RF'nin mutlaka M0'ı geçmesi | M0 ve M1 adil karşılaştırma |
| Genelleme | Kişi bazlı LOSO gerekir [S10,T2] | Rastgele pencerelerle yeni kişi başarısı | Katılımcı grup ayrımı ve eğitim içi ayarlar |
| Etiketleme | Kappa + anlaşma + dağılım ve uyuşmazlık [S3,S11,S12] | Kappa tek başına gerçeklik kanıtı | Önceden belirlenmiş kılavuz ve çift etiketleme |

## 5. Önceden belirlenmiş yöntem kararları (Charter ile uyumlu)

**5.1 Etiketler:** MATERYAL = görünür yönelim kâğıt/çalışma materyaline; TELEFON = telefonla etkileşime dair yeterli gözlenebilir işaret; DIŞ_YÖN = bunların dışında görünür yönelim. Yalnız görünür telefon TELEFON sayılmaz. Belirsizliği, yüz/telefon örtülmesini, geçiş anlarını ve çelişen kanıtları ayrı kural setinde tanımla. Bunlar ilkeler; kesin örnekler Faz 2 `labeling-protocol.md` ile kilitlenecek.

**5.2 Model karşılaştırması:** M0 kural tabanlı öznitelik/eşik; M1 aynı erişilebilir özniteliklerden RF. Her LOSO fold'unda eşikler, imputasyon, normalizasyon, özellik seçimi ve model hiperparametreleri sadece eğitim katılımcılarından öğrenilir. Eğitimdeki üç ana sınıfa göre performans hesaplanırken BELİRSİZ kararlarının nasıl skorlanacağı önceden açıkça belirtilir; zorla tek sınıfa atama yapılmaz.

**5.3 Analiz zamanlaması:** [t,t+2 sn) penceresi, 1 sn kaydırma. Örtüşen pencerelerin süreleri doğrudan toplanmaz; süre/kesinti hesapları birbiriyle çakışmayan tekil 1 sn zaman adımları/timeline üzerinden yapılır. Kısmi pencerelerin sınır davranışı test edilir.

**5.4 Doğrulama:** `participant_id` ile LOSO; kişinin iki oturumu da yalnızca o fold'un testinde. Fold bazlı sınıf F1, Macro-F1, belirsiz oranı, materyal süresi MAE ve kesinti sayısı hatası; ortalama yanında kişi-bazlı dağılım verilir. Metriklerin tanımı ve BELİRSİZ işleme kuralı deney protokolünde sabitlenir.

**5.5 Etiket güvenilirliği:** Toplam izinli sürenin en az %25'i, bütün kişiler ve ana sınıflar temsil edilecek şekilde iki kişi tarafından birbirinden bağımsız etiketlenir. İlk ham etiketler saklanır; Kappa, ham anlaşma, sınıf dağılımı, uyuşmazlıklar raporlanır; sonra uzlaşı sürümü üretilir. Sınıf ve kişi kapsaması raporda doğrulanır.

**5.6 Örneklem:** 8–10 kişi, 240–300 dk kayıt, temel olarak fizibilite ölçekli araştırmadır; nüfus geneline güçlü genelleme, istatistiksel üstünlük veya belirli Macro-F1 garantisi sunmaz. Güven aralıkları/katılımcı varyansı ve başarısız örnekler görünür tutulur.

**5.7 Etik:** Tek kamera ve yerel prototip, kişisel verisiz GitHub. Yüz videosu ve kişinin kimlik eşlemesi Git'e yüklenmez; gerekli izin/muafiyet değerlendirmesi tamamlanmadan tanınabilir gönüllü verisi kaydedilmez. Sentetik testler gerçek bilimsel sonuç gibi raporlanmaz.

## 6. Literatürdeki boşluk ve özgünlük gerekçesi

İncelenen çalışmalar çoğunlukla sınıf içi katılım, ekran bazlı e-öğrenme, webcam bakış izlemesi veya farklı sensörlerle telefon davranışlarını ele alıyor. **Bu seçilmiş kaynak kümesinde**, şu birleşimi doğrudan aynı protokol altında değerlendiren bir çalışma tespit edilmedi: **kâğıt temelli bireysel masa çalışması + tek RGB kamera + üç görünür yönelim sınıfı ve açık BELİRSİZ + M0/RF karşılaştırması + katılımcı bazlı LOSO + süre/kesinti hatası**.

Bu, dünyada böyle çalışma olmadığı veya mutlak özgünlük ispatı **değildir**. Özgünlük iddiamız yeni yapay zekâ algoritması değil; dar görev tanımı, protokol, kanıt sınırları ve kişi-bağımsız/temporal karşılaştırmanın birlikte ve tekrarlanabilir şekilde raporlanmasıdır. İlgili yakın çalışmaların tam metin/takip atıf taraması danışmanla gözden geçirilebilir.

## 7. Kritik sınırlamalar ve risk -> test eşlemesi

| Risk | Dayanak | Önleyici deney/kayıt |
|---|---|---|
| Aşağı bakan baş: materyal mi telefon mu? | [S1,S8,S9] | Telefon aktif kullanım işareti yoksa otomatik TELEFON atama; çelişkide BELİRSİZ |
| Kayıp yüz/göz, gözlük, ışık | [S1,S3,S5,T1] | Kamera açı/ışık fizibilitesi; eksik özellik oranı; kontrollü hata testi |
| Etiket belirsizliği | [S3,S4,S11,S12] | Yazılı etiketleme kararları, %25 çift etiket, Kappa + anlaşma |
| Kişi sızıntısı | [S10,T2] | `train.participant_id ∩ test.participant_id == ∅` otomatik testi |
| Ölçümün fazla iddia edilmesi | [S4,S5] | Çıktı adı 'görünür materyal yönelim süresi'; öğrenme başarısı iddiası yok |
| Örtüşen pencerelerin çift sayımı | Proje protokolü | 1 sn tekil timeline, 2 sn/1 sn sınır testleri |
| Başarı metriğinin sınıf dengesine bağımlılığı | Metodolojik çıkarım | Macro-F1 + sınıf F1 + kişi bazlı rapor ve confusion matrix |
| Küçük örneklem | [S3] ve protokol | Genelleme sınırlaması, fold dağılımları, sonuçların temkinli yorumlanması |

## 8. Faz 2'ye devredilen açık teknik kararlar (literatür eksiği değil)

1. Telefon için asgari 'aktif etkileşim' kanıtlarının etiketleme örnekleri (el, ekran yönelimi, bakış/baş ipucu, örtülme).
2. Masa materyali için kamera açısına göre koordinat sınırları ve belirsizlik politikası.
3. BELİRSİZ tahminlerin Macro-F1 hesaplamasına etkisi; ana sonuçta 'coverage + conditional F1' mi yoksa önceden tanımlı ceza politikası mı? Seçim değerlendirme protokolünde sabitlenmeli.
4. İnsan etiketlerinin zaman çözünürlüğü, geçiş anı etiketleme, görüntü kaybı işaretleri.
5. M0 eşikleri ve M1 hiperparametre arama sınırları: yalnız eğitim grubunda.
6. Süre ve kesinti referansının tekil adımlarda nasıl üretileceği ve `>=3 saniye` kesinti sınırları.
7. Dışarıda görülen telefonun pasif varlığı ve telefon tamamen kadraj dışında etkileşim durumlarının gerçekçi değerlendirilebilirliği.

Bu sorular araştırmanın kapsamını genişletmeyi gerektirmez; Faz 2 dokümantasyonunda önceden karara bağlanmalıdır.

## 9. Literatür tamamlanma ve ekip kontrolü

- [x] Baş pozu / göz göstergeleri için temel ve eleştirel kaynaklar tarandı.
- [x] Eğitimde gözlenebilir dikkat / bilişsel dikkat ayrımı yazıldı.
- [x] Telefon etkileşimiyle ilişkili en yakın yayınlar tarandı.
- [x] Yeni kişi genellemesi ve LOSO'ya dair metodoloji incelendi.
- [x] Etiket güvenilirliği ve kappa sınırlılıkları belgelendi.
- [x] Teknik araçlar hakemli araştırmalardan ayrı gösterildi.
- [x] Bulgular karar, risk, test ve açık soru haline getirildi.
- [ ] Bahar'ın kaynakları ve yorumları gözden geçirmesi.
- [ ] Danışmanla bilimsel iddia/özgünlük sınırının son kontrolü (uygunsa).

**Çalışma durumu:** Faz 1.2'nin araştırma ve ilk sentez çıktısı hazırlanmıştır; iki kişilik ekip incelemesi tamamlanmadan 'ekipçe onaylandı' sayılmaz. Bu metin hakem değerlendirmesi geçmiş bir sistematik literatür derlemesi değil, kaynaklandırılmış tasarım dayanağıdır.
