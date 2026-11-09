Project Charter — Görsel Dikkat Araştırması
Durum: Taslak — Bahar ve Pınar'ın ortak onayı bekleniyor
Tarih: 9 Kasım 2026
İç plan: 5 Kasım–30 Aralık 2026 (8 hafta).
Ekip: Bahar ve Pınar
1. Proje başlığı
Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi
2. Amaç ve bilimsel iddia sınırı
Tek kamera kullanarak kâğıt tabanlı masa başı çalışma sırasında gözlenebilir yönelim durumunu sınıflandırmak ve çalışma materyaline yönelim süresi ile kesintileri zamansal olarak tahmin etmek. Bu çalışma kişinin zihinsel dikkatini, anlama düzeyini veya öğrenme başarısını doğrudan ölçtüğünü iddia etmez.
3. Önceden belirlenen araştırma kapsamı
- Üç ana sınıf: MATERYAL, TELEFON, DIŞ_YÖN.
- Özel çıktı: BELİRSİZ (dördüncü ana sınıf değildir).
- Katılımcılar: 8–10 yetişkin gönüllü (gerekli izinler tamamlandıktan sonra).
- Oturum: Kişi başına 20 dakika senaryolu + 10 dakika serbest çalışma; toplam 240–300 dakika.
- Görüntü/öznitelik: Tek kamera; baş pozu, seçili yüz/göz göstergeleri ve görünür telefon ipuçları.
- Zamanlama: 2 saniyelik analiz penceresi, 1 saniyelik kaydırma.
- Yöntemler: M0 kural tabanlı; M1 Random Forest.
- Doğrulama: Katılımcı bazlı Leave-One-Subject-Out (LOSO). Aynı kişinin tüm oturumları ilgili test katlamasında tutulur.
- Ölçümler: Macro-F1, sınıf bazlı F1, Cohen’s Kappa, BELİRSİZ oranı, yönelim süresi hatası (MAE), kesinti sayısı hatası.
- Özel zaman kuralı: Örtüşen 2 saniyelik pencereler birbiriyle toplanmaz; süre 1 saniyelik tekil zaman adımlarıyla hesaplanır. Kesinti değerlendirmesinde kesintisiz en az 3 saniye kuralı test edilir.
4. Planlanan teslimatlar
1. Yazılı protokol, etik/hukuki değerlendirme kayıtları, veri ve etiketleme kılavuzu.
2. Kamera/video → öznitelik → pencereleme → M0/M1 → oturum metriği işlem hattı.
3. İzinli ve etiketlenmiş gönüllü verileriyle, bağımsız çift etiketleme ve uyum analizi (toplam sürenin en az %25'i).
4. Katılımcı bazlı LOSO ile yöntem karşılaştırması, metrikler ve sınırlılık raporu.
5. Yerel çalışan araştırma prototipi, testler, deney kayıtları, README ve sunum.
5. Etik ve güvenlik bağımlılıkları
- Danışmanla yetkili kurul ve etik izin/muafiyet değerlendirme yolu netleştirilecek.
- Aydınlatma/onam, veri saklama, erişim, silme ve gönüllü çekilmesi işlemleri kurum kararlarına göre belirlenecek.
- Bu süreçler tamamlanmadan tanınabilir gönüllü görüntüsü kaydedilmeyecek.
- Gönüllü videoları, kimlik eşleme bilgileri ve kişisel veri içeren türetilmiş dosyalar GitHub'a konmayacak.
- İzinler beklenirken sentetik veya kullanım izni bulunan kişisel veri içermeyen girdilerle teknik geliştirme sürdürülebilir; bu veriler gerçek gönüllü verisi gibi raporlanmaz.
6. Ekip sorumlulukları
Alan	Bahar	Pınar
Kamera ve görüntü, baş/yüz/telefon ipuçları	Ana sorumlu	Test/doğrulama
Zaman pencereleri ve süre hesabı	Entegrasyon	Ana sorumlu
Etiketleme	Kayıt kalite kontrol	Ana sorumlu
CI ve test	Modül testleri	Kurulum ve koordinasyon
Yerel arayüz	Entegrasyon	Ana sorumlu
M0, M1, LOSO ve bilimsel rapor	Ortak	Ortak


7. Çalışma ve karar sistemi
- Tek private GitHub repository, main ve feature/, fix/, test/, docs/ branch'leri.
- Her iş için Issue; küçük branch + test + Pull Request; karşılıklı inceleme ve başarılı CI sonrası merge.
- GitHub Projects: Backlog → Ready → In Progress → In Review → Done; gerekirse Blocked.
- Başlangıçta kişi başına en çok iki eşzamanlı aktif Issue.
- Haftalık durum değerlendirmesinde çıktılar, riskler ve kabul testleri kayıt altına alınır.
8. Faz 1 tamamlanma ölçütleri
- [ ] Bahar ve Pınar kapsamı birlikte gözden geçirip onayladı.
- [ ] Etik süreç gerçek durumuyla kayıt altına alındı; izin alınmış varsayılmadı.
- [ ] Başlangıç işleri sahip, bağımlılık, test ve kabul kriterleri bulunan Issue'lara ayrıldı.
- [ ] Teknik fizibilite riskleri takip edilebilir biçimde kaydedildi.
9. Açık kararlar / doğrulanacak bilgiler
- [ ] Proje önerisiyle bu taslak arasında kapsam uyuşmazlığı olup olmadığı (orijinal öneri belgesi üzerinden teyit).
- [ ] Yetkili etik kurul / muafiyet süreci, kurum ve danışman yönlendirmesi.
- [ ] Aydınlatma/onam metinlerinin onaylı sürümü ve veri saklama-silme takvimi.
- [ ] Kameranın konumu, ışık koşulları ve iki bilgisayarın yeterliliği (fizibilite testiyle).
- [ ] Etiketlemede belirsizlik ve geçiş kurallarının ayrıntılı tanımı (Faz 2 protokolü).
10. Onay kaydı
- Bahar: Bekleniyor — Tarih: ___
- Pınar: Bekleniyor — Tarih: ___
