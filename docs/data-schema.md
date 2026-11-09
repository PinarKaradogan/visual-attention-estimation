Faz 2.3 — Veri Şeması ve Zaman Sözleşmesi (v0.1)
Proje: Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi
Tarih: 9 Kasım 2026
Sorumlular: Pınar (ana), Bahar (kamera/öznitelik doğrulaması)
Durum: İnceleme taslağı — gerçek veri toplama ve saklama için izin verilmiş değildir.
1. Amaç ve kapsam
Bu belge architecture.md v0.2 ve 8 haftalık iç yol haritasına dayanarak modüller arasında taşınacak verinin alan adlarını, türlerini, birimlerini, anahtarlarını, geçerlilik durumlarını ve zaman çizelgesini tanımlar. İlgili modüller: VideoSource, FeatureExtractor, WindowBuilder, Classifier, TimelineResolver, LabelAligner, FeatureStore, ExperimentRunner ve SessionMetrics.
- Ana sınıflar: MATERYAL, TELEFON, DIS_YON (raporda DIŞ_YÖN).
- BELIRSIZ tahmin/karar özel çıktısıdır; dördüncü ana eğitim sınıfı değildir.
- 2.000 ms pencere / 1.000 ms kaydırma; tekil saniye kararları [başlangıç, bitiş) aralıklarıyla tanımlanır.
- Katılımcı bazlı LOSO: aynı participant_id'ye ait tüm oturumlar bir dış katlamada birlikte testte kalır.
- Ham video, kimlik eşleme bilgisi ve kişisel veriler GitHub'a gönderilmez. Özniteliklerin kalıcı saklanması etik/kurumsal karar sonrasına bağlıdır. Şimdilik yalnız sentetik örnek üretilir.
2. Kimlikler ve ortak alan kuralları
- participant_id: str; kişiyi doğrudan tanımlamayan, araştırmaya özgü rastgele/pseudonim kod. Gerçek kişi adları burada bulunmaz. Aynı kişi için tüm oturumlarda sabittir.
- session_id: str; oturumun benzersiz kodu; participant_id ile ilişkilidir.
- session_type: enum SCENARIO / FREE (20 dakika senaryolu, 10 dakika serbest).
- timestamp_ms, start_ms, end_ms: int ≥ 0; oturumun video zaman çizelgesinde milisaniye. Bütün zaman aralıkları yarı açık [start_ms, end_ms) ve end_ms > start_ms.
- schema_version: str (başlangıç 0.1.0); veri dosyası yapısını izler. feature_version, label_version, resolution_policy_version ayrıdır.
- Kayıp sayı için null kullanılır; 0 gerçek sayısal ölçüm anlamına gelir. İlgili durum bayrağı ayrıca tutulur.
- Tarih/saat gerekirse yalnız oturum üst verisinde ISO 8601 olarak tutulur; ölçüm süreleri duvar saati farkından hesaplanmaz.
3. Kayıt sözleşmeleri
Aşağıdaki tablolar mantıksal sözleşmedir; henüz çalışan kod ya da gerçek gönüllü veri dosyası değildir. Sonraki aşamada sentetik JSON/CSV ve Python dataclass'larına dönüştürülecek.
3.1 SessionRecord — oturum üst verisi
Alan	Tip / değer	Amaç
session_id	str, zorunlu, benzersiz	Oturum anahtarı
participant_id	str, zorunlu	LOSO gruplama anahtarı
session_type	SCENARIO / FREE	Oturum türü
duration_ms	int ≥ 0	Oturumun video zamanındaki gerçek süresi
source_mode	LIVE / FILE / SYNTHETIC	Video kaynağı
source_id	str	Kişisel veri veya tam dosya yolu içermeyen kaynak kodu
camera_setup_id	str veya null	Sabit kamera kurulum referansı
camera_position, camera_angle_note	str veya null	Konum/açı açıklaması; ölçülmediyse null
width_px, height_px	int veya null	Çözünürlük
nominal_fps, measured_fps	float veya null	Kaynak/gerçekte işlenen kare hızı, ayrı ayrı
dropped_by_source	int ≥ 0 veya null	Kamera/sürücünün düşürdüğü kareler; zaman damgası aralıklarındaki boşluklardan kestirilir
skipped_by_pipeline	int ≥ 0	İşleme yetişilemediği için bilerek atlanan kareler (LIVE); FILE modunda 0
schema_version	str	Şema sürümü


Gerçek kişiye ait isim, iletişim ve kimlik eşlemesi bu şemada bulunmaz. Kamera kurulumu mümkün olduğunca oturumlar arasında sabit tutulur; değişirse ayrıca kaydedilir.
3.2 FrameRecord — kare akışı (kalıcı saklama zorunlu değil)
Alan	Tip	Açıklama
session_id	str	Oturum referansı
frame_index	int ≥ 0	Kaynak kare sırası; atlanan kareler sırada boşluk olarak görünür
timestamp_ms	int ≥ 0	Oturum-başlangıçlı video zaman damgası
frame	bellekte görüntü nesnesi	GitHub'a ve FeatureStore'a ham kare yazılmaz
source_status	enum / hata kodu	OK, READ_ERROR, SKIPPED vb.


Zaman kaynağı: FILE modunda konteynerin/video akışının kare sunum zamanı (presentation timestamp) kullanılır; dosyanın işlendiği duvar/CPU zamanı kullanılmaz. LIVE modunda kamera/sürücü gerçek yakalama zaman damgası sağlamıyorsa oturum başlangıcına göre monotonik saatle kare okuma zamanı ölçülür (işleme bitiş zamanı değil). Bu değer OpenCV tamponu nedeniyle gerçek yakalama zamanı olmayabilir. Her iki modun timestamp_ms alanı oturum başlangıcına göre tanımlanır; ölçüm kaynağı ve olası gecikme kaydedilir.

Araştırma kaydı ilkesi: Araştırma oturumları önce video dosyasına kaydedilir ve öznitelikler bu dosyadan FILE modunda çıkarılır. İnsan etiketleri de aynı dosya üzerinde yapıldığından öznitelikler ve etiketler tek bir video zaman çizelgesini paylaşır. LIVE modu yalnız demo/yerel arayüz içindir; LIVE modunda ölçülen zaman, OpenCV tamponu nedeniyle kare yakalama değil okuma zamanı olabilir ve bu sınırlılık raporda belirtilir. Kayıt mümkünse sabit kare hızıyla yapılır; değilse kare zaman damgaları ayrıca saklanır.

Kare politikası: LIVE için işleme yetişilemiyorsa en son kareyi tercih eden sınırlı kuyruk ve atlanan kare sayacı; FILE için varsayılan tüm kareleri işleme. Bunlar Faz 3'te ölçülecek uygulama kararlarıdır. Video zamanı sabit ardışık FPS varsayımıyla türetilmez; değişken kare aralıkları korunur.
3.3 FeatureRecord — türetilmiş ölçüm
Alan	Tip	Açıklama
session_id, frame_index, timestamp_ms	str, int, int	Kaynak izlenebilirliği
feature_version	str	Çıkarıcı/öznitelik kümesi sürümü
head_yaw_deg, head_pitch_deg, head_roll_deg	float veya null	Baş yönelimi, derece; pozitif yön tanımı açık karar
eye_features	adlandırılmış sınırlı sayısal alanlar veya null	Tam alan listesi Faz 2.3/2.4 ekip kararıyla kilitlenecek
phone_cues	yapılandırılmış işaretler	Telefon görünürlük/etkileşim ipuçları; tespit aracı henüz seçilmedi
face_status	VALID, NOT_DETECTED, LOW_CONFIDENCE, OCCLUDED	“Yüz yok” ve “düşük güven” ayrılır
phone_status	VISIBLE, NOT_VISIBLE, OCCLUDED, NOT_EVALUATED	“Görünmüyor” doğrudan “ortamda yok” değildir
hand_status	VALID, NOT_DETECTED, OCCLUDED, NOT_EVALUATED	Bağımsız el bileşeni için
validity_flags	adlandırılmış booleans (head_pose_valid, eye_features_valid)	Yalnız alan bazlı geçerlilik; bileşen durumu için esas kaynak face_status / phone_status / hand_status alanlarıdır


Sınır: Telefonun yalnız görünmesi TELEFON sınıfını kanıtlamaz. Tam yüz landmark koordinatları varsayılan depolama şemasına alınmamıştır. Bu alanların saklanabilirliği, veri minimizasyonu ve etik/kurumsal izin henüz netleşmemiştir. FeatureRecord şimdilik bellekte/sentetik testlerde kullanılabilir.
3.4 WindowRecord — 2 saniyelik özet
Alan	Tip	Açıklama
session_id, window_index	str, int	Oturum ve pencere
start_ms, end_ms	int, int	[start,end); varsayılan pencere uzunluğu 2.000 ms
aggregates	sürümlü sayısal alanlar	FeatureRecord özetlerinden hesaplanır
available_frame_count	int ≥ 0	Penceredeki işlenen geçerli kare sayısı
coverage_ratio	float [0,1] veya null	Kanıt kapsaması, hesaplama tanımı belgelenmeli
is_valid, invalid_reason	bool, str veya null	Geçerlilik kararı
feature_version	str	Girdi uyumu


Pencereler [0,2000), [1000,3000), [2000,4000) ... şeklindedir. Asgari kare sayısı ve kapsama eşiği henüz belirlenmedi; Faz 2.4 öncesi test ve kamera verilerine göre ekipçe sabitlenecek. Bir pencereyi salt kare sayısı ile geçerli varsaymayız.
3.5 HumanLabelInterval ve SecondReference
Kayıt	Temel alanlar	Açıklama
HumanLabelInterval	session_id, annotator_id (kod), start_ms, end_ms, label, label_version	İnsan gözlemcinin zaman aralığı etiketi
SecondReference	session_id, second_start_ms, label, validity, label_version, agreement_status	LabelAligner'ın ürettiği tekil 1 saniye referansı


İnsan referans sınıfları MATERYAL, TELEFON, DIS_YON; karar verilemeyen zaman aralıkları ayrı UNCERTAIN/`UNLABELED` durumuyla yönetilir (ana sınıf değildir). Bir saniyede birden fazla insan etiketi, çatışma, kısmi kapsama veya belirsizlik varsa ilgili bayraklar tutulur. Etiket çakışmalarının çözüm ve uzlaşı kuralı Faz 2.4'te sabitlenecek. En az %25 bağımsız çift etiketleme ve Cohen's Kappa yol haritası gereğidir.
3.6 Prediction ve SecondDecision
Kayıt	Temel alanlar	Açıklama
Prediction	session_id, window_index, start_ms, end_ms, model_id (M0/`M1`), label, score_or_null, reason	Pencere tahmini
SecondDecision	session_id, second_start_ms, label, source_window_start_ms, source_window_end_ms, resolution_policy_version, coverage_ratio, reason	Tekil saniye kararı


TimelineResolver için mimari v0.2'deki taslak politika: tamamlanmış 2 sn pencerenin tahmini son 1 sn'ye atanır; ilk saniye yalnızca ilk geçerli pencereyle bootstrap edilir. Her session_id + second_start_ms için tek karar vardır; saniyeler çifte sayılmaz. Politika Faz 2.4'te onaylanana kadar deney sonuçlarında sabit yöntem diye sunulmaz.
3.7 ExperimentRecord — tekrarlanabilir LOSO
Zorunlu izleme alanları: experiment_id, created_at, git_commit, schema_version, feature_version, label_version, resolution_policy_version, test_participant_id, train_participant_ids, model_id, model_params, metrics, artifact_path, notes.

LOSO değişmezi: test_participant_id hiçbir zaman train_participant_ids içinde bulunamaz. Aynı kişinin SCENARIO ve FREE oturumları aynı dış test katlamasında kalır. M0 eşikleri ve M1 eğitim/ön işleme yalnız eğitim kişileriyle belirlenir.
4. Dosya/klasör yaklaşımı ve veri güvenliği
Önerilen, henüz yetkilendirilmemiş gerçek veri için kullanılmayacak mantıksal yollar:
# GitHub'a girebilen: şema, kod, test ve gerçek kişi içermeyen sentetik örnekler
docs/data-schema.md
tests/fixtures/synthetic_sessions.json

# Yalnız gerekli kurum kararı sonrası, erişim kontrollü yerel depolama
local_data/raw_video/          # ham kayıt; GitHub'a ASLA gönderme
local_data/derived_features/   # izin kapsamındaki seçilmiş öznitelikler
local_data/labels/             # katılımcı kodlarına bağlı insan etiketleri
local_data/identity_mapping/   # ayrı tutulur, yetkisi sınırlandırılır
local_data/experiments/        # sonuçlar kişisel veriden arındırılmadan paylaşılmaz

Önerilen .gitignore girdisi: local_data/, .venv/, .env, installed-packages.txt; ancak gerçek kişi verilerini yalnızca .gitignore ile korumak yeterli değildir (erişim ve şifreleme/transfer politikaları da gerekir). Gerçek gönüllü görüntüleri için etik/kurumsal uygunluk ve katılımcı süreçleri tamamlanmadan kayıt yok.
5. Doğrulama ve kabul testleri (Faz 2.3)
1. Şema: zorunlu kimlik/zaman alanları ve sürümler mevcut; end_ms > start_ms.
2. Zaman: kareler oturum içinde monoton artan video zaman damgası taşır; dosya modunda işlem süresi ile karıştırılmaz.
3. Pencere: [0,2000) ve [1000,3000) doğrulanır; sınırdaki kare tek pencereye doğru yarı açık aralık kuralıyla atanır.
4. Tekil saniye: her session_id + second_start_ms için tek SecondDecision; örtüşme süreyi ikiye katlamaz.
5. Eksik kanıt: NOT_VISIBLE ile NOT_EVALUATED, NOT_DETECTED ile LOW_CONFIDENCE ayrılır; eksik veriden zorla ana sınıf üretilmez.
6. Etiket: insan etiketleri aynı video zaman çizelgesine hizalanır; belirsiz/geçiş durumları açık işaretlenir.
7. LOSO: bir katılımcı aynı fold'da train ve testte olamaz.
8. Güvenlik: sentetik örnekler gerçek kişisel veri içermez; gerçek verinin Git'e girmemesi kontrol edilir.
Faz 2'de en az bir küçük sentetik fixture ve test eklenmesi planlanır; bu belge tek başına testlerin çalıştığı anlamına gelmez.
6. Açık kararlar ve sorumluları
Karar	Önerilen sahip	Tamamlanma zamanı
head_pitch_deg ve diğer açıların işaret yönü	Bahar	Faz 2.3–2.4
Sabit eye_features alan listesi	Bahar	Faz 2.3–2.4
Pencere asgari kare/kapsama eşiği	Bahar + Pınar	Kamera ölçümü / Faz 2.4
İnsan etiketinden M1 pencere hedefi: iki saniye uzlaşı mı, son saniye mi?	Ortak	Faz 2.4, eğitimden önce
TimelineResolver başlangıç politikası ve geçiş gecikmesi	Pınar + Bahar	Faz 2.4
BELİRSİZ ve boş referans saniyelerinin metrikte ele alınışı	Ortak	Faz 2.4
Depolanabilir türetilmiş öznitelikler, erişim, saklama ve imha	Danışman/kurum + ortak	İzin kararı sonrası
Gerçek kamera çözünürlük/FPS, kare düşmesi ve kurulum sabitliği	Bahar	Donanım testleri


Bahar'ın ölçüm notu: Dahili HP True Vision FHD kamera için raporladığı yaklaşık değerler: 720p ≈ 30 FPS, 1080p ≈ 30 FPS, 640×480 ≈ 13,3 FPS. Bunlar ekip içi ön ölçümlerdir; harici kamera performansı anlamına gelmez.
7. Faz 2.3 çıkış kriteri
- Alanların tipleri ve sürümleri ekipçe gözden geçirildi.
- Oturum, kare, öznitelik, pencere, insan etiketi ve tekil saniye kayıtları ortak zaman sözleşmesine uyuyor.
- LOSO katılımcı ayrımı açıkça doğrulandı.
- Sentetik fixture ve şema/zaman testi eklendi veya ayrı test Issue'sunda açıkça izlendi.
- Etik karara bağlı veri saklama alanları onay alınmış gibi gösterilmedi.
- Bahar ve Pınar GitHub PR incelemesini tamamladı.
Referanslar: docs/architecture.md v0.2 (özellikle 4.1, 4.2, 9.1); 8 Haftalık Proje Yol Haritası (Faz 2 ve test/veri yönetimi bölümleri). Bu belge karar taslağıdır; etiketleme/eşik yöntemleri docs/labeling-protocol.md ile nihai hâle getirilecektir.
