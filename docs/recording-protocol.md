# Faz 2.8 — Kayıt Protokolü (v1.0, #31)

Proje: Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi
Ekip: Pınar (proje yürütücüsü, kayıt sorumlusu) ve Bahar
Tarih: 27 Kasım 2026
İlgili iş paketi: v5 İP1 (kayıt kurulumu) ve İP3 (veri toplama); ders planı Faz 2 ve Faz 6 (bkz. project-charter.md §5)
Kaynak: TÜBİTAK 2209-A önerisi v5 §2.1–2.2, §2.8, Ek-1, Ek-3 ve risk tablosu; docs/ethics-checklist.md; docs/labeling-protocol.md; docs/data-schema.md §3.1; 26–27 Kasım kamera denemeleri (#13).

> **Bu protokol etik kurul onayı değildir.** Etik kurul kararı ve onaylı onam formu olmadan hiçbir gönüllü kaydı yapılmaz (§2).

## 1. Amaç ve kapsam

Bu belge 2–5 Aralık 2026 kayıtlarının adım adım uygulama kılavuzudur. Amacı, her oturumun aynı koşullarda, etik kurallara uygun ve sonradan işlenebilir biçimde kaydedilmesidir.

- **Katılımcı:** 18 yaş ve üzeri 8–10 gönüllü üniversite öğrencisi (v5 §2.1). Katılım ders notunu veya değerlendirmeyi etkilemez.
- **Oturumlar:** Kişi başına **20 dakika senaryolu** (1200 sn) ve **10 dakika serbest** oturum; toplam yaklaşık 30 dakika kayıt (v5 §2.2, Ek-3).
- **Sınıflar:** MATERYAL, TELEFON, DIŞ_YÖN; BELİRSİZ ayrı bir çıktıdır (v5 §2; labeling-protocol.md §4).
- **Kayıt:** Yalnızca görüntü. **Ses kaydı alınmaz** (v5 §2.8).
- **Davranış sınırları:** Komut zamanından değil, etiketleme sırasında görsel incelemeyle belirlenir (v5 §2.2). Komut çizelgesi yalnızca oturumu yönlendirir.

## 2. Etik ön koşullar (kayıttan önce hepsi işaretlenir)

- [ ] Etik kurul onay belgesi alındı (ethics-checklist.md §9). **Yoksa kayıt yapılmaz.**
- [ ] Onaylı aydınlatma metni ve ayrı yazılı açık rıza formu basıldı (v5 Ek-3).
- [ ] Katılımcının 18 yaş ve üzeri olduğu sözlü beyanla doğrulanır; kimlik fotokopisi alınmaz.
- [ ] Şifreli harici depolama hazır: birincil kopya şifreli harici SSD, yedek ayrı şifreli disk, kimlik eşleme listesi ayrı şifreli USB bellekte (v5 §2.8; ethics-checklist.md §5.1). Şifreleme için BitLocker To Go ya da ücretsiz VeraCrypt kullanılabilir.
- [ ] Test telefonu hazır: kişisel içerik görünmeyen ayrı/boş kullanıcı profili ya da sıfırlanmış yedek cihaz, bildirimler kapalı (v5 §2.2; ethics-checklist.md §5.1). Katılımcının kendi telefonu kullanılmaz.
- [ ] Bahar'ın video erişimi için danışman/kurul kararı alındı. Karar gelene kadar Bahar kayıt odasında kadraj dışında kalır, videoları görmez ve etiketleme yapmaz (ethics-checklist.md §5.1; R20).

## 3. Ekipman ve kurulum

### 3.1 Ekipman

| Öğe | Değer | Not |
| --- | --- | --- |
| Kamera | Logitech C310, harici USB | v5'teki asgari özelliklerden sapma: 720p, sabit odak, tripod bağlantısı yok (R22) |
| Kayıt çözünürlüğü ve hızı | **640×480, 30 kare/sn** | 27.11 denemesi: 640×480'de 29,1 FPS, 1280×720'de 6,2 FPS (kamera MJPG'yi kabul etmiyor). v5 §2.2'ye göre değer teknik pilotta belirlenir; v5 B planı "çözünürlüğü kontrollü düşürme" ile uyumludur. |
| Bilgisayar | Pınar'ın dizüstü bilgisayarı (i7-12650H, 16 GB) | v5 §3.3 |
| Kayıt yazılımı | **OBS Studio** (ücretsiz, açık kaynak) | §8 |
| Test telefonu | Proje yürütücüsünün sağladığı kişisel içeriksiz cihaz | §2 |
| Çalışma materyali | Kitap veya basılı metin, defter, kalem, kısa soru kâğıdı | Her katılımcıya aynı materyal; kişisel bilgi yazdırılmaz |
| DIŞ_YÖN hedefi | Duvarda renkli bir etiket (yaklaşık 5 cm) | §3.3 |
| Diğer | Kronometre gerekmez (OBS kayıt süresini gösterir); basılı senaryo çizelgesi; maskeleme bandı | — |

### 3.2 Kamera konumu ve ışık

Kesin konum **2 Aralık'ta kayıt ortamında, ilk kayıttan önce teknik pilotla** belirlenir (v5 §2.2; §4). 27.11 ev denemelerinden çıkan başlangıç önerisi:

- Kamera katılımcının **tam karşısında**, yaklaşık **70 cm** uzakta, **çene–ağız hizasında**, yüze doğru hafif yukarı bakar. Alçak konumda yazarken, sol göz hizasının üstünde ise okurken ve sağa dönüşte yüz kayboldu.
- Kadrajda **yüz, masadaki eller ve kâğıt birlikte** görünür. Masadaki eller denemede %98–100 bulundu.
- Arka planda kişi, ekran, ayna veya kişisel eşya bulunmaz (v5 §2.8; ethics-checklist.md §3).
- Işık önden ya da yandan, sabit ve yeterli olmalı; kamera pencereye karşı konmaz. Tavan ışığı açık tutulur.
- Belirlenen konum masada ve kamerada **bantla işaretlenir** ve tüm oturumlarda değiştirilmez. Değişirse oturum kaydına sapma olarak yazılır (§10).

### 3.3 DIŞ_YÖN hedefi

- Rapor açı vermez; yalnızca "çalışma alanı dışındaki sabit hedef" der (v5 Ek-1). Bu protokolde hedef **göz hizasında ve yaklaşık 30–35° yanda** olur: çalışma alanının açıkça dışında ama yüz tam profile dönmeden.
- Hedef pencere, ekran veya kişi değildir. Konumu teknik pilotta, yüz tespiti ≥ %90 kalacak biçimde sabitlenir ve bantla işaretlenir.

## 4. Gün başı teknik kontrol

Her kayıt gününün başında, **gönüllü gelmeden önce**, kurulumu yapan kişi (Pınar) kendisi üzerinde aşağıdaki kontrolü yapar. Görüntü kaydedilmez; yalnızca sayısal özet üretilir.

```
.venv\Scripts\activate
git checkout test/camera-checks
set PYTHONPATH=src
python scripts\camera_checks.py --camera 1 --only info framing --width 640 --height 480
git checkout main
```

**Geçme ölçütü:** Ölçülen kamera hızı ≥ 25 FPS; framing satırlarının her birinde (okuma, yazma, telefon, duvardaki işaret) **yüz ≥ %90** (v5 H5) ve el ≥ %90. Tutmazsa kamera veya ışık düzeltilir ve kontrol tekrarlanır. Geçilmeden kayıt yapılmaz. Sonuç oturum kaydına yazılır (§10). `test/camera-checks` dalında commit yapılmaz.

## 5. Roller

| Rol | Kim | Görev |
| --- | --- | --- |
| Kayıt sorumlusu (operatör) | Pınar | Onam, kurulum kontrolü, OBS'yi başlatma/durdurma, komutları okuma, oturum kaydı, dosya güvenliği |
| Teknik destek | Bahar | Gün başı kontrolüne ve kod tarafına destek. Video erişim kararı gelene kadar kayıt sırasında **kadraj dışında** kalır ve kayıtları izlemez (§2). |

**Operatörün yeri:** Kameranın görüş alanının dışında olmalı; OBS önizlemesinde görünmediği doğrulanır. Katılımcının DIŞ_YÖN hedefi yönünde de durmaz. Katılımcının arkasında durmak **uygun değildir**, çünkü kamera karşıdan baktığı için arka plana girer. Uygun yer, katılımcının yan-arkasında ve kadraj dışında bir noktadır; teknik pilotta belirlenir. Operatör komutlar dışında konuşmaz.

## 6. Senaryolu oturum (20 dakika)

### 6.1 Hazırlık

1. Senaryolar bir kez üretilir ve basılır (yalnızca katılımcı kodu içerir, kişisel veri içermez):
   ```
   python -m visual_attention.scenario --participants P01-P10 --seed 2026
   ```
   Çıktı `local_data/scenarios/` altındadır (Git dışı). Gönüllü sayısı 1 Aralık'ta ≤ 8 ise B planı uygulanır ve senaryolar `--events-per-class 8` ile yeniden üretilir; v5 süre aralıkları korunur.
2. Katılımcı kodları kayıt sırasına göre verilir: ilk gelen P01, sonraki P02 ve böyle devam eder. Ad ile kod arasındaki eşleme yalnızca şifreli USB'deki listeye yazılır.
3. Test telefonu masada, katılımcının rahat uzanabileceği bir yerde ve ekranı aşağı dönük durur.

### 6.2 Katılımcıya açıklama (kayıttan önce, okunacak metin)

> "Yaklaşık 20 dakika kitap ve defter üzerinde çalışacaksınız. Okuyabilir, not alabilir ya da sorulara bakabilirsiniz. Ara sıra size kısa komutlar vereceğim: telefonu alıp ekranı kaydırmanızı ya da duvardaki işarete bakmanızı isteyeceğim. 'Kâğıda dön' dediğimde çalışmaya devam edin. Telefon bir test telefonudur ve kişisel içerik yoktur. Kamera yalnızca görüntü kaydeder, ses kaydedilmez. İstediğiniz an durdurabilirsiniz."

### 6.3 Akış

1. OBS'de kaydı başlat. Kayıt süresi OBS'nin alt çubuğunda görünür.
2. **00:00'da** ilk komutu oku: **"Çalışmaya başla."**
3. Basılı çizelgedeki her bloğun **başlangıç saniyesinde** o bloğun komutunu oku. Komut cümleleri sabittir ve kelimesi kelimesine okunur:

   | Blok | Komut |
   | --- | --- |
   | TELEFON | "Telefonu al ve ekranı kaydır." |
   | DIŞ_YÖN | "Duvardaki işarete bak." |
   | MATERYAL (kesinti sonrası) | "Kâğıda dön." |

4. Komutun geciktiği ya da katılımcının farklı davrandığı yerler çizelgenin `actual_note` sütununa elle not edilir (ör. "05:53 komut 2 sn geç").
5. 20:00'de (1200 sn) kaydı durdur. Kesinti yoksa toplam kayıt süresi 1200 sn ile birkaç saniye fazlası arasındadır.

## 7. Serbest oturum (10 dakika)

1. Senaryolu oturumdan sonra 2–3 dakika ara verilir.
2. Katılımcıya: "Şimdi 10 dakika serbestçe çalışın, size komut vermeyeceğim. Telefon masada; dilediğiniz gibi davranabilirsiniz."
3. Test telefonu masada kalır (v5 §2.2). Operatör konuşmaz ve kadraj dışında kalır.
4. 10:00'da kaydı durdur.

## 8. Kayıt yazılımı (OBS Studio) ve dosyalar

### 8.1 Sesin kaynağında kapatılması (iki kilit)

1. **Windows:** Ayarlar → Gizlilik ve güvenlik → Mikrofon → "Mikrofon erişimi" **kapalı**. Kayıt günleri boyunca kapalı kalır. C310'un dahili mikrofonu da bu ayarla kapanır.
2. **OBS:** Ayarlar → Ses → bütün "Masaüstü ses" ve "Mikrofon/Yardımcı ses" aygıtları **Devre dışı**. Kaynaklar listesinde ses kaynağı bulunmaz.
3. **Her kayıttan sonra kontrol:** Video dosyasına sağ tıkla → Özellikler → Ayrıntılar. "Ses" bölümü **boş** olmalı. Boş değilse dosya bir sonraki oturumdan önce güvenli biçimde silinir, ayar düzeltilir ve oturum kaydına yazılır.

Sesin sonradan silinmesi yeterli değildir; ses hiç toplanmaz (v5 §2.8, veri minimizasyonu).

### 8.2 Bir kerelik OBS kurulumu (yaklaşık 15 dakika)

1. OBS Studio'yu resmi siteden (obsproject.com) indirip kur.
2. Ayarlar → Video: Temel (tuval) çözünürlüğü **640×480**, Çıkış çözünürlüğü **640×480**, FPS **30**.
3. Kaynaklar → + → **Video Yakalama Aygıtı** → aygıt: C310 → Çözünürlük/FPS türü: Özel → **640×480**, FPS **30**.
4. Ayarlar → Çıkış → Kayıt: kayıt yolu **şifreli harici SSD'deki** proje klasörü; kayıt biçimi **mkv** (çökme durumunda dosya bozulmaz); kodlayıcı donanım (NVENC) ya da x264; kalite "Yüksek kalite, orta dosya boyutu".
5. Ayarlar → Gelişmiş → Kayıt: **"Otomatik olarak mp4'e dönüştür"** açık (ELAN ve işlem hattı mp4 okur). "Dosya varsa üzerine yaz" **kapalı**.
6. Bu ayarlar "Kayıt-640x480" adlı bir **Profil** olarak saklanır ve her oturumda aynı profil kullanılır.

### 8.3 Dosya adları

- Biçim: `P01_SCENARIO.mp4` ve `P01_FREE.mp4`. Dosya adında ad, öğrenci numarası, tarih veya saat **bulunmaz** (labeling-protocol.md §9).
- OBS'de oturumdan önce Ayarlar → Gelişmiş → Kayıt → Dosya adı biçimi doğrudan `P01_SCENARIO` yapılır. Ya da dosya kayıt biter bitmez bu adla yeniden adlandırılır.

## 9. Veri güvenliği

- Ham videolar **yalnızca şifreli harici depolamada** tutulur. Dizüstü bilgisayarın diskinde, `local_data/` içinde, GitHub'da, bulutta veya mesajlaşma uygulamalarında **bulunmaz** (v5 §2.8; R13).
- Aynı gün içinde ikinci şifreli diske yedek alınır; dosya boyutları karşılaştırılır.
- Kimlik eşleme listesi (ad ↔ P kodu) ve imzalı onam formları videolardan ayrı tutulur: liste şifreli USB'de, formlar kilitli bir dosyada.
- Videolara yalnızca proje yürütücüsü ve akademik danışman erişir. Bahar'ın erişimi danışman/kurul kararına bağlıdır (§2).
- Öznitelik çıkarma videoyu doğrudan şifreli diskten okur. Yalnızca yüz görüntüsü içermeyen türetilmiş öznitelikler `local_data/derived_features/` altına yazılır (Git dışı).
- Ham videolar etik kurulun onayladığı süre içinde ve en geç proje bitiminden 6 ay sonra güvenli biçimde silinir (v5 §2.8).
- Her PR'dan önce `git status` ile video, etiket veya oturum kaydı dosyası eklenmediği kontrol edilir.

## 10. Oturum kaydı ve sapmalar

Her oturum için bir satır, `local_data/sessions/session_log.csv` dosyasına yazılır (Git dışı). Alanlar data-schema.md §3.1 `SessionRecord` ile uyumludur:

| Alan | Örnek | Not |
| --- | --- | --- |
| `session_id` | P01_SCENARIO | |
| `participant_id` | P01 | Gerçek ad yazılmaz |
| `session_type` | SCENARIO / FREE | |
| `recording_day` | 1 | Gün numarası (1–4); tarih yazılmaz |
| `camera_setup_id` | CAM-A | Teknik pilotta belirlenen kurulum; değişirse CAM-B |
| `camera_position`, `camera_angle_note` | "karşıda, 70 cm, çene hizası" | |
| `width_px`, `height_px`, `nominal_fps` | 640, 480, 30 | OBS profili |
| `day_check_face_min_pct`, `day_check_fps` | 95.2, 29.1 | §4 gün başı kontrolü |
| `light_note` | "tavan + masa lambası" | |
| `glasses` | evet / hayır | v5'te kaydedilen ama alt grup analizine alınmayan unsur |
| `scenario_version`, `seed` | scn-0.2.0, 2026 | Senaryolu oturumda |
| `consent_recorded` | evet | Form ayrıca saklanır |
| `audio_track_absent` | evet | §8.1 kontrolü |
| `backup_done` | evet | §9 |
| `deviations` | "07:15'te katılımcı öksürdü" | Kamera kayması, kesinti, yeniden başlatma |

**Sapma durumları:**

- **Katılımcı durdurmak isterse:** Kayıt hemen durdurulur. Kayıt, katılımcının çekilme hakkı ve onam formundaki koşula göre silinir ya da saklanır. Durum oturum kaydına yazılır.
- **Teknik arıza (kamera kopması, OBS çökmesi):** Kayıt yeniden başlatılır ve kesinti oturum kaydına yazılır. İlk 2 dakika içindeyse oturum aynı senaryoyla baştan alınır. Daha sonra olduysa kalan kısım için not düşülür; davranış sınırları zaten etiketlemede belirlenir.
- **Kamera yerinden oynarsa:** Bant işaretine geri konur, §4 kontrolü tekrarlanır ve sapma yazılır.
- **Kamera arızası:** v5 B planına göre dizüstü bilgisayarın dahili kamerası yedek olarak kullanılır. Yeni bir `camera_setup_id` verilir ve gün başı kontrolü bu kamerayla tekrarlanır.

## 11. Günlük plan ve kayıt sonrası

**Günlük plan:** 2–5 Aralık arasında günde 2–3 gönüllü. Kişi başı yaklaşık 50 dakika: onam 10 dk, açıklama 3 dk, senaryolu oturum 20 dk, ara 3 dk, serbest oturum 10 dk, dosya kontrolü ve yedek 4 dk.

**Kayıt sonrası:**

1. Dosya adı, ses kontrolü ve yedek (§8–9) tamamlanır.
2. Öznitelik çıkarma (P4-05, Bahar'ın aracı; video şifreli diskten okunur):
   ```
   set PYTHONPATH=src
   python -m visual_attention.features --video <şifreli-disk>\P01_SCENARIO.mp4 --session-id P01_SCENARIO
   ```
3. ELAN etiketlemesi labeling-protocol.md'ye göre yapılır. Test–tekrar test setindeki videolar ilk etiketlenir. Tekrar seçimi tohum 2209 ile yapılır, ≥ 4 hafta sonra kör tekrar (labeling-protocol.md §7).

## 12. Kontrol listesi (oturum başına, basılı)

- [ ] Etik onay var; onam formu imzalandı; 18+ sözlü beyan
- [ ] Gün başı kontrolü geçti (yüz ≥ %90, ≥ 25 FPS)
- [ ] Windows mikrofonu kapalı; OBS'de ses aygıtı yok; profil "Kayıt-640x480"
- [ ] Kayıt yolu şifreli harici SSD; dosya adı `Pxx_SCENARIO`
- [ ] Kamera bant işaretinde; arka planda kişi veya ekran yok; operatör kadraj dışında
- [ ] Test telefonu: bildirimler kapalı, ekranda kişisel içerik yok
- [ ] Senaryolu oturum kaydedildi; `actual_note` dolduruldu
- [ ] Serbest oturum kaydedildi (`Pxx_FREE`)
- [ ] İki dosyada da ses yok; yedek alındı; oturum kaydı satırı yazıldı

## Revizyon kaydı

| Sürüm | Tarih | Değişiklik | Kaynak |
| --- | --- | --- | --- |
| v1.0 | 2026-11-27 | İlk sürüm: 640×480/30 FPS, OBS ile iki kilitli ses kapatma, kamera ve DIŞ_YÖN hedefi için başlangıç önerisi, gün başı kontrolü, oturum kaydı | #31; 26–27 Kasım kamera denemeleri |
