Faz 1.4 — Teknik Fizibilite ve Risk Kaydı
Proje: Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi
Ekip: Bahar ve Pınar
Hazırlanma tarihi: 9 Kasım 2026
İlgili faz / iş paketi: Faz 1 — Hazırlık, kapsam ve analiz / İP1
Durum: Başlangıç risk envanteri hazır; ölçüm sonuçları, donanım bilgileri ve ekip teyidi bekleniyor.
Kaynak: Gorsel_Dikkat_Projesi_8_Haftalik_Yol_Haritasi(1).docx (özellikle s. 2–3, 5–7); docs/project-charter.md; docs/ethics-checklist.md.
Önemli: Bu belge risklerin ön değerlendirmesidir; gerçekleştirilmeyen testler yapılmış gibi işaretlenmez. Teknik fizibilite henüz doğrulanmış değildir. Gerçek gönüllülerden tanınabilir görüntü kaydı, gerekli etik/kurumsal değerlendirme ve katılımcı süreçleri tamamlanmadan başlatılmaz.

1. Sabit araştırma kapsamı
- Tek kamerayla kâğıt tabanlı masa başı çalışma esnasında gözlenebilir yönelimin incelenmesi.
- Ana sınıflar: MATERYAL, TELEFON, DIŞ_YÖN; BELİRSİZ ana sınıf değil, özel çıktıdır.
- 8–10 yetişkin gönüllü; kişi başına 20 dakika senaryolu ve 10 dakika serbest oturum (yalnız gerekli izinlerden sonra).
- Baş pozu, seçili yüz/göz göstergeleri ve görünür telefon ipuçları.
- 2 saniyelik analiz penceresi, 1 saniyelik kaydırma; yönelim süreleri tekil zaman adımları üzerinden hesaplanır.
- M0 kural tabanlı yaklaşım; M1 Random Forest; katılımcı bazlı LOSO.
- Macro-F1, sınıf bazlı F1, Cohen's Kappa, BELİRSİZ oranı, süre MAE ve kesinti sayısı hatası.
- Yerel prototip için hedef en az 10 FPS; henüz ölçülmüş performans değildir.
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
R07	Yerel bilgisayarda yetersiz hız / gecikme; 10 FPS hedefinin altında kalma	3	4	12	Bahar	Düşük FPS, yüksek gecikme, işlemci yoğunluğu	Çözünürlük/işleme frekansı denemeleri; profil çıkarma; hafif bileşenler	İki makinede FPS, gecikme ve ortam bilgisi	Açık
R08	İki ekip bilgisayarında kamera, Python veya paket uyumsuzluğu	3	3	9	Pınar + Bahar	Tek makinede çalışan örneğin diğerinde hata vermesi	Sabitlenmiş bağımlılıklar, sürüm/env kayıtları; iki bilgisayarda kurulum testi	Kurulum günlüğü ve smoke test çıktıları	Açık
R09	Etiket kuralının yoruma açık olması; düşük gözlemciler arası uyum	4	5	20	Pınar	Çift etiketlerde uyuşmazlık; κ < 0,70 erken uyarı	Ayrıntılı etiket kılavuzu, örnekler, bağımsız çift etiketleme; uyuşmazlık günlüğü	İzin sonrası tüm katılımcı/ana sınıfları kapsayan ≥%25 çift etiketleme; Cohen's Kappa	Açık
R10	Sınıf dengesizliği (özellikle TELEFON / DIŞ_YÖN); yanıltıcı yüksek accuracy	3	4	12	Pınar + Bahar	Çok az örnek/oturum segmenti	Senaryolu blok dağılım kontrolü; sınıf bazlı F1 ve macro-F1	Etiketli veri sonrası sınıf/süre dağılım raporu	Açık
R11	LOSO'da aynı katılımcının hem eğitim hem testte kalması; veri sızıntısı	3	5	15	Pınar + Bahar	Katılımcı ID'leri kümelerde kesişiyor	Katılımcı bazlı fold üretimi; eğitim içinde önişleme/eşik ayarı; otomatik ayrım testi	Train/test participant_id kesişimi sıfır	Açık
R12	Etik süreç gecikmesi veya gönüllü kaydı ön koşullarının tamamlanmaması	4	5	20	Ortak	Hafta 3'te resmî karar yok	Kayıt başlatmama; sentetik/izinli teknik geliştirmeyi sürdürme; takvimi danışmanla güncelleme	Etik durum kaydı; kurumsal yazışma referansı (kişisel verisiz)	Açık
R13	Ham video/etiket/kimlik eşlemesinin kazara GitHub'a veya buluta gitmesi	3	5	15	Pınar + Bahar	Takip edilen data dosyaları / yanlış commit	.gitignore, PR veri kontrolü; ayrı korumalı depolama; erişim kısıtları	git status, test amaçlı sahte dosyalarla ignore doğrulaması	Açık
R14	Az katılımcıdan yeni kişilere genelleme zayıflığı	4	4	16	Ortak	LOSO fold sonuçları arasında yüksek değişim	Katılımcı bazlı sonuç/hata dağılımını raporlama; iddiayı sınırlama	Fold bazlı macro-F1/F1, BELİRSİZ oranı ve sınırlılıklar	Açık
R15	Bağımlı işlerin, iki kişilik ekipte gecikmesi	3	3	9	Ortak	Bloke Issue ve yığılan PR	Haftalık kontrol; görev başına sahibi, bağımlılığı ve kabul ölçütü	Projects panosu; haftalık karar notları	Açık


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
İşletim sistemi	Ölçülecek	Ölçülecek
Python sürümü	Ölçülecek	Ölçülecek
CPU / RAM	Ölçülecek	Ölçülecek
GPU (varsa)	Ölçülecek	Ölçülecek
Kamera aygıtı / çözünürlük	Ölçülecek	Ölçülecek
Ortalama FPS	Ölçülecek	Ölçülecek
Gecikme (ms)	Ölçülecek	Ölçülecek
Kamera açma/smoke test	Beklemede	Beklemede


Ölçüm standardı: Aynı test videosu veya kişisel veri içermeyen sentetik giriş ve aynı işlem hattıyla karşılaştırma. FPS = işlenen kare / geçen süre; gecikme, girişten çıktı üretimine kadar ölçülür. Isınma dönemi ve test süresi raporda belirtilir. 10 FPS bir hedeftir, mevcut başarı değildir.
F3 — Etiketlenebilirlik ve geçişler (Pınar)
- [ ] MATERYAL, TELEFON, DIŞ_YÖN için görünür davranış tanımları Faz 2 etiket kılavuzuna görev olarak aktarıldı.
- [ ] BELİRSİZ için eksik yüz, telefon kanıtı, örtülme ve geçiş koşulları listelendi.
- [ ] “Telefon görünüyor fakat kullanılmıyor” örneği aktif TELEFON etiketi sayılmıyor.
- [ ] İki etiketleyicinin farklı karara varabileceği örnekler uyuşmazlık listesine eklendi.
- [ ] İzinli gerçek veride ≥%25 bağımsız çift etiketleme ve Cohen's Kappa takvimi belirlendi (henüz gerçekleştirilmedi).
Kabul kanıtı: Faz 2 docs/labeling-protocol.md için senaryo/karar listesi; izin sonrası çift etiketleme kayıtları.
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
—	—	—	—	—


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
- docs/architecture.md, docs/data-schema.md, docs/labeling-protocol.md — Faz 2'de hazırlanacak; henüz tamamlanmadı.
Son not: Başlangıç risk puanları ekip tahminidir. Fizibiliteyi doğrulayan şey dosyanın hazırlanması değil, ölçüm/test kanıtlarının belgeye işlenmesidir.
