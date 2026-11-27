Faz 1.4 — Teknik Fizibilite ve Risk Kaydı
Proje: Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi
Ekip: Bahar ve Pınar
Hazırlanma tarihi: 9 Kasım 2026 (güncelleme: 25 Kasım 2026, #30 — öneri v5 uyumu ve iki geliştiricili plan; 27 Kasım 2026, #31 — R22 ve kamera ölçümleri)
İlgili faz / iş paketi: Faz 1 — Hazırlık, kapsam ve analiz / İP1
Durum: Başlangıç risk envanteri hazır; ölçüm sonuçları, donanım bilgileri ve ekip teyidi bekleniyor.
Kaynak: TÜBİTAK 2209-A önerisi v5 (§3.2 Risk Yönetimi, kapsamın asıl kaynağı); docs/project-charter.md v2; docs/ethics-checklist.md; docs/labeling-protocol.md; Gorsel_Dikkat_Projesi_8_Haftalik_Yol_Haritasi(1).docx.
Önemli: Bu belge risklerin ön değerlendirmesidir; gerçekleştirilmeyen testler yapılmış gibi işaretlenmez. Teknik fizibilite henüz doğrulanmış değildir. Gerçek gönüllülerden tanınabilir görüntü kaydı, gerekli etik/kurumsal değerlendirme ve katılımcı süreçleri tamamlanmadan başlatılmaz.

1. Sabit araştırma kapsamı
- Tek kamerayla kâğıt tabanlı masa başı çalışma esnasında gözlenebilir yönelimin incelenmesi.
- Ana sınıflar: MATERYAL, TELEFON, DIŞ_YÖN; BELİRSİZ ana sınıf değil, özel çıktıdır.
- 8–10 yetişkin gönüllü; kişi başına 20 dakika senaryolu ve 10 dakika serbest oturum (yalnız gerekli izinlerden sonra).
- Baş pozu, göz açıklık oranı, el/bilek göstergeleri (yazma, telefona uzanma, telefonu tutma) ve görünür telefon ipuçları (v5 §2.4).
- 2 saniyelik analiz penceresi, 1 saniyelik kaydırma; yönelim süreleri tekil zaman adımları üzerinden hesaplanır.
- M0 kural tabanlı yaklaşım; M1 Random Forest; çoğunluk-sınıf tabanı; katılımcı bazlı LOSO.
- Kişi-bazlı makro-F1, sınıf bazlı F1, BELİRSİZ oranı, odak süresi MAE, kesinti sayısı hatası, kesinti olayı F1 (±2 sn), Bland–Altman; etiket güvenirliği için test–tekrar test Cohen κ.
- Yerel prototip için hedef en az 10 FPS (GPU kullanılmadan, yalnız işlemciyle; v5 H5); henüz ölçülmüş performans değildir.
- Zihinsel dikkat veya öğrenme başarısının doğrudan ölçüldüğü iddia edilmez.
2. Risk puanlama ve durum standardı
Olasılık (O) ve etki (E) 1–5 arasında başlangıç tahmini puanlardır: 1=düşük, 3=orta, 5=çok yüksek. Skor = O × E. Öncelik için operasyonel eşikler: 1–5 düşük, 6–11 orta, 12–25 yüksek. Bu eşikler araştırma sonucu veya TÜBİTAK'ın resmî ölçeği değil, ekibin iş takibi içindir.

Durum değerleri: Açık, Test planlandı, Test edildi, Azaltıldı, Engellendi, Kapandı. Her satırdaki skor, birincil sorumlunun gözden geçirmesiyle güncellenir.
3. Risk envanteri
ID	Risk ve etkisi	O	E	Skor	Sorumlu	Erken uyarı	Önlem / alternatif	Kanıt / doğrulama	Durum
R01	Kamera açısında yüz, çalışma materyali veya telefonun sık örtülmesi; sınıf ayrımında belirsizlik	4	4	16	Bahar	Yüz/telefon ipucu kaybı; kadraj dışında kalma	Tek kamera için farklı masa/konum kurulumları; görüş alanını sınırlandırma; kayıp kanıtı ayrı işaretleme	İzinli veya kişisel veri içermeyen sahne testi; kadraj kontrol formu, kayıp oranı	Açık
R02	Düşük / değişken ışıkta yüz-göz işaretlerinin kararsızlığı	3	4	12	Bahar	Baş pozu/göz özniteliklerinde sıçrama, artan kayıp tespit	Sabit ışık ve yansımayı azaltma; koşul bazlı başarısızlık analizi	Koşul bazlı algılama/kayıp raporu	Açık
R03	Telefonun yalnız görünür olmasının kullanım sanılması veya kullanımın örtülmesi	4	5	20	Bahar + Pınar	Telefon ipucuyla etiketin uyuşmaması	Telefon varlığı ile aktif kullanım kanıtını ayırma; eksik kanıtta BELİRSİZ; etiket kılavuzunda örnekler	Sentetik senaryo örnekleri, daha sonra izinli etiketli veriyle hata analizi	Açık
R04	Yüz kaybı/eksik öznitelik durumunda zorla ana sınıf atanması	3	5	15	Pınar	Kayıp özellik varken güvenli görünen sınıf tahmini	Eksik değer bayrağı; BELİRSİZ çıkışı ve izlenebilir gerekçe	Birim testleri: eksik yüz/göz/telefon kanıtı	Açık
R05	İki saniyelik örtüşen pencerelerin iki kez sayılması; odak süresi hatası	3	5	15	Pınar	Toplam yönelim süresinin oturum süresini aşması	Bir saniyelik tekil zaman adımı hesabı; sınır koşulu testleri	Sentetik zaman çizelgesi ve beklenen süre karşılaştırması	Açık
R06	Kesinti süresinin ≥3 sn kuralında geçiş/sınır hataları	3	4	12	Pınar	2,9/3,0/3,1 sn örneklerinde tutarsız sayım	Açık zaman damgası ve süre tanımı; sınır testleri	Sentetik test tablosu, test raporu	Açık
R07	Yerel bilgisayarda yetersiz hız / gecikme; 10 FPS hedefinin altında kalma	3	4	12	Bahar	Düşük FPS, yüksek gecikme, işlemci yoğunluğu	Çözünürlük/işleme frekansı denemeleri; profil çıkarma; hafif bileşenler; v5 B planı: çözünürlüğü kontrollü düşürme ve seyrek tespit	Resmî ölçüm v5'teki bilgisayarda (Pınar, i7-12650H) GPU kullanılmadan; Bahar'ın ön ölçümü ≈ 26 FPS (yalnız işlemci, kamerasız)	Açık
R08	İki ekip bilgisayarında kamera, Python veya paket uyumsuzluğu	3	3	9	Pınar + Bahar	Tek makinede çalışan örneğin diğerinde hata vermesi	Sabitlenmiş bağımlılıklar, sürüm/env kayıtları; iki bilgisayarda kurulum testi	Kurulum günlüğü ve smoke test çıktıları	Açık
R09	Etiket kuralının yoruma açık olması; düşük test–tekrar test uyumu (κ < 0,70)	4	5	20	Pınar	Tekrar etiketlemede uyuşmazlık; ortak denemede farklı kararlar	Ayrıntılı etiket kılavuzu (labeling-protocol.md v0.2), örnekler, uyuşmazlık günlüğü; v5 B planı: karışan kesitler kılavuza eklenir, şüpheli segmentler kör olarak yeniden işaretlenir	≥ %25 test–tekrar test (aynı etiketleyici, ≥ 4 hafta ara, kör); genel ve sınıf bazlı Cohen κ; ilk ve düzeltilmiş uyum birlikte raporlanır	Açık
R10	Sınıf dengesizliği (özellikle TELEFON / DIŞ_YÖN); yanıltıcı yüksek accuracy	3	4	12	Pınar + Bahar	Çok az örnek/oturum segmenti	Senaryolu blok dağılım kontrolü; sınıf bazlı F1 ve macro-F1	Etiketli veri sonrası sınıf/süre dağılım raporu	Açık
R11	LOSO'da aynı katılımcının hem eğitim hem testte kalması; veri sızıntısı	3	5	15	Pınar + Bahar	Katılımcı ID'leri kümelerde kesişiyor	Katılımcı bazlı fold üretimi; eğitim içinde önişleme/eşik ayarı; otomatik ayrım testi	Train/test participant_id kesişimi sıfır	Açık
R12	Etik izin belgesinin gecikmesi; 2–5 Aralık kayıt penceresinin kaçması	4	5	20	Ortak	1 Aralık itibarıyla izin belgesi yok	İzin olmadan kayıt yok; v5 B planı: işlem hattı sentetik ve açık lisanslı videolarla tamamlanır, kayıtlar izin gelince kademeli yapılır ve etiketleme ilk kayıttan başlar; takvim danışmanla güncellenir	Etik durum kaydı (ethics-checklist.md §9)	Açık
R13	Ham video/etiket/kimlik eşlemesinin kazara GitHub'a veya buluta gitmesi	3	5	15	Pınar + Bahar	Takip edilen data dosyaları / yanlış commit	.gitignore, PR veri kontrolü; ayrı korumalı depolama; erişim kısıtları	git status, test amaçlı sahte dosyalarla ignore doğrulaması	Açık
R14	Az katılımcıdan yeni kişilere genelleme zayıflığı	4	4	16	Ortak	LOSO fold sonuçları arasında yüksek değişim	Katılımcı bazlı sonuç/hata dağılımını raporlama; iddiayı sınırlama	Fold bazlı macro-F1/F1, BELİRSİZ oranı ve sınırlılıklar	Açık
R15	Bağımlı işlerin, iki kişilik ekipte gecikmesi	3	3	9	Ortak	Bloke Issue ve yığılan PR	Günlük kontrol; görev başına sahibi, bağımlılığı ve kabul ölçütü; Blocked sütunu	Projects panosu; günlük durum notları	Açık
R16	İki etiketleyicinin kuralları farklı yorumlaması; veri tutarsızlığı	3	4	12	Pınar + Bahar	Ortak denemede sınıf veya sınır farkları	Etiketleme öncesi zorunlu ortak deneme (#37); protokoldeki örnekler; tekrarı ilk etiketleyen yapar	Ortak deneme notu; uyuşmazlık günlüğü	Açık
R17	PR'ların bağımlılık sırasına aykırı merge edilmesi; çakışma ve bozuk main	3	4	12	Pınar	Bağımlılığı main'de olmayan PR'ın merge'ü; CI kırmızı	Bağımlılık zinciri kuralı (bağımlı işler aynı kişide); Ready sütununa yalnız bağımlılığı merge edilmiş işler; merge öncesi CI	Pano geçmişi; CI sonuçları	Açık
R18	Elde tutulan telefonun nesne tespitinde kaçırılması; TELEFON sınıfında düşük recall	3	4	12	Bahar	Canlı denemede elde telefonun düşük güvenle ya da hiç algılanmaması	Telefon tespiti el göstergeleriyle birlikte yorumlanır (v5 §2.4); #33'te canlı deneme (kayıtsız); güven eşiği yalnız eğitimde ayarlanır	#33 PR notu; sınıf bazlı F1	Açık
R19	Test–tekrar test etiketlemesinin teslim tarihinden sonraya kalması	5	3	15	Pınar	İlk etiketleme 2–5 Aralık'ta; ≥ 4 hafta kuralı	Kural kısaltılmaz; tekrar setindeki videolar ilk etiketlenir; tekrar etiketleme Ocak başında yapılıp sonuçlar eklenir	labeling-protocol.md §7; etiket sürüm kayıtları (r1/r2/final)	Açık
R20	Bahar'ın video erişimi için etik değişiklik onayının gelmemesi	3	4	12	Pınar	Danışman/kurul yanıtı olumsuz ya da gecikmeli	Onay gelene kadar Bahar video görmez; etiketlemenin tamamı Pınar'da (≈ 25 sa ilk etiketleme); Bahar'ın iş yükü kod tarafına kaydırılır	ethics-checklist.md §5.1 ve §9	Açık
R21	10 günlük takvimde iş yükü yoğunluğu; kapsam baskısı	4	4	16	Pınar	Ready'de bekleyen ya da Blocked'da kalan kartlar	Kapsam daraltılmaz; bağımlılık zinciri, günlük durum notu, kritik yol (#26 → #32, #35 → #29) önceliği; v5 B planı (önerinin kendi önlemi): analiz önceliği senaryolu oturumlar, serbest oturum keşifsel düzeyde raporlanır, gerekirse prototip arayüzü komut satırı oturum özetine sadeleştirilir, H1–H5 ölçütleri değişmez	Pano ve PR akışı	Açık
R22	Kamera v5 asgari özelliklerini karşılamıyor (Logitech C310: 720p, sabit odak, tripod bağlantısı yok); 720p'de yalnız ≈ 6 FPS ve baş eğilince/yana dönünce yüz kaybı	5	3	15	Pınar	Gün başı kontrolünde yüz < %90 ya da kamera hızı < 25 FPS	Kayıt 640×480 / 30 FPS (v5 §2.2 teknik pilot kararı; v5 B planı: çözünürlüğü kontrollü düşürme); kamera tam karşıda ve çene hizasında, yeri bantla sabit; gün başı kontrolü (recording-protocol.md §4); sapma raporda açıkça belirtilir; arızada dahili kamera yedek (v5 B planı)	camera_checks 27.11 özetleri (640×480'de 29,1 FPS; 720p'de 6,2 FPS; masadaki eller %98–100); 2 Aralık teknik pilot sonucu	Açık


Puanlar: Gerçek saha ölçümlerine değil ön değerlendirmeye dayanır. Ekip gözden geçirmesiyle değiştirilebilir; yüksek skor ≠ riskin gerçekleştiği anlamına gelmez.
4. Fizibilite ölçüm protokolü
F1 — Kamera ve kadraj (Bahar; Faz 1 plan, Faz 2–3 uygulama)
- [ ] Kullanılacak kamera türü, çözünürlük, FPS kapasitesi ve bağlantı yöntemi kaydedildi.
- [ ] Önerilen kamera konumu, masanın görünürlüğü, yüz/baş görünürlüğü ve telefon ipuçları için değerlendirme ölçütleri yazıldı.
- [ ] Normal ışık / zayıf ışık / yan ışık koşulları tanımlandı.
- [ ] Kısmi örtülme, gözlük, başın dönmesi ve materyale aşağı bakma gibi koşullar risk listesine işlendi.
- [ ] İzinli veya kişisel veri içermeyen örnek üzerinde görünürlük/kayıp ölçümü yapıldı (henüz yapılmadı).
Kabul kanıtı: Kamera konumu ve koşul matrisi + görsel işaret kaybı/kalite raporu. Yüzün görülmediği karelerde güvenilir sınıf üretildiği varsayılmaz.
F2 — Bilgisayar ve yerel performans (Bahar + Pınar)
Her bilgisayar için doldur:
Alan	Bahar bilgisayarı	Pınar bilgisayarı
İşletim sistemi	Windows 11 Pro for Workstations (build 26200)	Ölçülecek
Python sürümü	Proje ortamı Python 3.11.9 (.venv), PR #11'de doğrulandı	Proje ortamı: Python 3.11.9 (.venv); doğrulanacak
CPU / RAM	AMD Ryzen 7 7840HS (8 çekirdek / 16 izlek) / 16 GB	Intel Core i7-12650H (12. nesil, 2,30 GHz) / 16 GB, 3200 MT/sn (v5 §3.3)
GPU (varsa)	NVIDIA RTX 4050 Laptop 6 GB + AMD Radeon 780M (dahili)	NVIDIA RTX 4050 Laptop 6 GB (v5 §3.3; FPS ölçümünde kullanılmaz)
Kamera aygıtı / çözünürlük	HP True Vision FHD (dahili, ekran üstü); 640×480, 1280×720, 1920×1080; ham yakalama ~30 FPS (720p/1080p), 13,3 FPS (640×480)	Logitech C310 (harici USB); kamera MJPG'yi kabul etmiyor (YUY2): 1280×720'de 6,2 FPS, 640×480'de 29,1 FPS (27.11, görüntü kaydedilmedi)
Ortalama FPS	Ölçülecek (işlem hattı henüz yok)	İşlem kapasitesi ≈ 12,1 FPS (720p girdi, kare başı ortanca 82,6 ms, p95 104 ms; GPU kullanılmadan; 27.11 kamera kontrolü). Prototip H5 ölçümü ayrıca yapılacak
Gecikme (ms)	Ölçülecek (işlem hattı henüz yok)	Ölçülecek
Kamera açma/smoke test	Geçti (OpenCV ile açıldı, kare okundu)	Geçti (26–27.11 kamera kontrolleri)


Ölçüm standardı: Aynı test videosu veya kişisel veri içermeyen sentetik giriş ve aynı işlem hattıyla karşılaştırma. FPS = işlenen kare / geçen süre; gecikme, girişten çıktı üretimine kadar ölçülür. Isınma dönemi ve test süresi raporda belirtilir. 10 FPS bir hedeftir, mevcut başarı değildir.
F3 — Etiketlenebilirlik ve geçişler (Pınar)
- [ ] MATERYAL, TELEFON, DIŞ_YÖN için görünür davranış tanımları Faz 2 etiket kılavuzuna görev olarak aktarıldı.
- [ ] BELİRSİZ için eksik yüz, telefon kanıtı, örtülme ve geçiş koşulları listelendi.
- [ ] “Telefon görünüyor fakat kullanılmıyor” örneği aktif TELEFON etiketi sayılmıyor.
- [ ] İki etiketleyicinin farklı karara varabileceği örnekler uyuşmazlık listesine eklendi.
- [x] Test–tekrar test takvimi belirlendi: ≥ %25, aynı etiketleyici, ≥ 4 hafta ara (labeling-protocol.md §7); henüz gerçekleştirilmedi.
Kabul kanıtı: docs/labeling-protocol.md v0.2; izin sonrası r1/r2 etiket kayıtları ve κ raporu.
F4 — Pencereleme, süre ve kesinti (Pınar)
- [ ] 2 sn pencere / 1 sn adım ve eksik zaman damgası kuralları birim test kapsamına alındı.
- [ ] Örtüşen pencerelerin süreleri birbiriyle topl anmayacak; tekil zaman adımları sayılacak.
- [ ] ≥3 sn kesinti ve geçiş sınırı için sentetik örnekler hazırlandı.
- [ ] Her oturum için ölçülen toplam sürenin oturum süresini aşmaması test edilecek.
Kabul kanıtı: pytest testleri ve beklenen/gerçekleşen zaman çıktıları (Faz 2–3).
F5 — Veri güvenliği ve etik kapısı (ortak)
- [ ] docs/ethics-checklist.md içindeki izin/muafiyet durumu güncellendi.
- [ ] Tanınabilir gönüllü video kaydı ancak gerekli kurum kararı ve katılımcı süreçleri tamamlandıktan sonra başlayacak.
- [ ] Gerçek kişisel verili dosyalar GitHub veya üçüncü taraf bulut sistemlerine yüklenmeyecek.
- [ ] Kimlik eşlemesi ayrı ve erişimi kısıtlı saklanacak; saklama/silme koşulları kurumla netleşecek.
Kabul kanıtı: Tarihli etik durum kaydı, depo veri güvenliği kontrolü; gerçek kayıt için resmî izin durumu.
5. Faz 1.4 çıkış ölçütleri
- [x] Teknik, bilimsel, etik ve ekip kaynaklı risklerin ilk envanteri yazıldı.
- [x] Her risk için sorumlu, erken uyarı, önlem ve doğrulama kanıtı tanımlandı.
- [x] Kamera, aydınlatma, iki bilgisayar, etiketleme ve zaman hesabı için ölçüm planı hazırlandı.
- [ ] Bahar kamera/donanım risklerini gözden geçirdi.
- [ ] Pınar etiketleme/zaman/altyapı risklerini gözden geçirdi.
- [ ] İki bilgisayarın özellikleri tabloya işlendi.
- [ ] Testlerin yapılmış olanları kanıtla güncellendi, yapılmayanlar açık bırakıldı.
- [ ] Yüksek riskler Projects Issues ile bağlandı ve Faz 2 görevleri planlandı.
Faz 1.4'ün tamamlandı sayılması: Risk kayıtlarının iki ekip üyesince doğrulanması, ilk ölçüm bilgilerinin girilmesi ve açık/engelleyici riskler için takip görevi oluşturulması. Bunun için bütün uzun vadeli risklerin çözülmüş olması gerekmez.
6. Faz 2 ve Faz 3'e aktarılacak işler
Görev	Sorumlu	Hedef faz	Önkoşul	Kabul ölçütü
Kamera ve capture giriş/çıkış sözleşmesi	Bahar	Faz 2	Kamera seçimi	Girdi, çıktı, hata durumu belgeli
Python sürümü, venv, bağımlılıkların sabitlenmesi	Bahar + Pınar	Faz 2	Bilgisayar envanteri	İki bilgisayarda kurulum ve smoke test
Veri şeması (participant_id, session_type, timestamp, etiket, geçerlilik)	Pınar	Faz 2	Kapsam	Şema doğrulama testi
Etiketleme karar kılavuzu	Pınar	Faz 2	Risk R03/R04/R09	3 sınıf + BELİRSİZ için örnekler
pytest / Ruff / CI	Pınar (koordinasyon), Bahar (modül testleri)	Faz 2	Repo ve bağımlılıklar	PR üzerinde otomatik kontrol
Görsel özellikler ve telefon ipuçları	Bahar	Faz 3	Capture, etik uygun giriş	Kayıp kanıtlarıyla çıktı
Zaman pencereleri, odak/kesinti hesapları	Pınar	Faz 3	Veri şeması	Sentetik süre ve sınır testleri
Etiket güvenilirliği / LOSO / M0–M1	Ortak	Faz 3	Gerekli izin, izinli veri	Kişi bazlı metrikler ve sürüm kaydı


7. Açık karar ve test günlüğü
Tarih	Karar / gözlem	Kaynak / kanıt	Sorumlu	Sonraki işlem
2026-11-09	Risk envanteri ilk sürümü oluşturuldu; teknik ölçüm yapılmadı	Bu belge	Pınar + Bahar inceleyecek	Donanım envanterini ve kamera koşullarını doldur
2026-11-09	Bahar bilgisayarı: dahili kamerayla ham yakalama ölçüldü; 720p/1080p ~30 FPS, 640×480 yalnız 13,3 FPS (3 sn ölçüm, görüntü kaydedilmedi). Düşük çözünürlükteki yavaşlamanın otomatik pozlama/ışıktan kaynaklandığı tahmin ediliyor, doğrulanmadı.	OpenCV 4 + DirectShow, kişisel veri saklanmadı	Bahar	R02/R07 için ışık koşullu tekrar ölçümü; dahili kameranın kâğıt ve elleri görüp görmediği R01 kadraj testinde incelenecek (gerekirse harici USB kamera)
2026-11-25	Risk kaydı öneri v5'e ve 10 günlük iki geliştiricili plana göre güncellendi; R16–R21 eklendi, R07/R09/R12 güncellendi	#30	Pınar	Bahar incelemesi
2026-11-27	Pınar bilgisayarı ve C310 ile kamera kontrolleri (görüntü kaydedilmedi): 640×480'de 29,1 FPS, 720p'de 6,2 FPS (MJPG kabul edilmedi); işlem kapasitesi ≈ 12,1 FPS; masadaki eller %98–100; telefon yokken yanlış algılama %0, elde %49–76; baş eğilince ve yana dönünce yüz kaybı kamera konumuna bağlı (alçakta yazarken %0, sol göz üstünde okurken %12,5)	camera_checks özetleri; #13	Pınar	R22 eklendi; kesin kamera yeri 2 Aralık teknik pilotunda (recording-protocol.md §3–4)


Test kayıt şablonu (her test için kopyala)
Test ID:
Tarih:
Sorumlu:
Makine / işletim sistemi:
Kamera ve çözünürlük:
Girdi türü: sentetik / lisanslı kişisel verisiz / izinli gerçek
Koşul: ışık, açı, örtülme vb.
Deney kodu (commit):
Ölçüm / birim:
Beklenen:
Gerçekleşen:
Sonuç: geçer / kalır / ölçülemedi
Kanıt yolu (kişisel veri içermeyen):
İlgili risk ID:
Aksiyon / Issue:
8. Bağlantılı belgeler
- docs/project-charter.md — sabit araştırma kapsamı.
- docs/literature-notes.md — bilimsel dayanak ve iddia sınırları.
- docs/ethics-checklist.md — etik/KVKK bağımlılıkları.
- docs/architecture.md v0.3, docs/data-schema.md v0.2, docs/labeling-protocol.md v0.2 — öneri v5 ile uyumlu.
Son not: Başlangıç risk puanları ekip tahminidir. Fizibiliteyi doğrulayan şey dosyanın hazırlanması değil, ölçüm/test kanıtlarının belgeye işlenmesidir.
