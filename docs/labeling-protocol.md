# Faz 2.4 — Etiketleme Protokolü ve Karar Kuralları (Taslak v0.2)

**Proje:** Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi  
**Durum:** Taslak v0.2; açık kararlar ekipçe kapatıldı, Pınar'ın incelemesine açık. Kurallar onaylandığında `protocol_version` ile kilitlenir ve **sonuçlar görüldükten sonra değiştirilmez.**  
**Dayanak:** TÜBİTAK 2209-A başvurusu, son hali (v5): 2.2, 2.3, 2.4, 2.5, 2.7, Ek-1, Ek-2; `docs/architecture.md` 4.1–4.2; `docs/data-schema.md` 3.5–3.6.  
**Önemli:** Bu belge etik izin değildir. Etik kurul izin belgesi alınmadan hiçbir gönüllüden görüntü kaydedilmez ve etiketlenmez.

## 1. Amaç ve kapsam

Bu protokol, kayıtlı araştırma videolarında insan referans etiketlerinin nasıl üretileceğini ve bu etiketlerden model eğitimi ile oturum ölçümleri için kullanılan türetilmiş etiketlerin nasıl hesaplanacağını sabitler. Model ve insan etiketlerine **aynı kurallar** uygulanır.

- Ana sınıflar: `MATERYAL`, `TELEFON`, `DIS_YON` (raporda `DIŞ_YÖN`).
- `BELIRSIZ` (raporda `BELİRSİZ`): görsel kanıtın yetersiz olduğu kesitler için ayrı çıktı. **Dördüncü bir davranış sınıfı değildir**, sınıflandırmanın kapsama sınırıdır.
- Modelin `BELIRSIZ` çıktısı bu belgede değil, v5 2.5'te sabittir ve `architecture.md`'ye işlenir: M0, penceredeki karelerin %50'sinden azında yüz bulunduğunda veya kurallar çeliştiğinde; M1, en yüksek sınıf olasılığı θ'nın altında kaldığında `BELIRSIZ` verir. θ yalnız eğitim katılımcılarında, iç doğrulamada kapsama ≥ %85 olacak biçimde seçilir.
- Masada yokluk ve yorgunluk kapsam dışıdır.
- Etiketler gözlenebilir davranışı tanımlar. Bilişsel dikkat veya öğrenme kazanımı ölçüsü olarak yorumlanmaz.

## 2. Roller ve erişim

| Konu | Kural |
| --- | --- |
| Etiketleyiciler | Pınar ve Bahar. Videolar ikisi arasında bölünür. Etiketleme model çıktıları görülmeden yapılır. |
| Kayıt | Her etiket dosyası `annotator_id` (etiketleyici kodu) ve `label_round` ile kaydedilir; kimin hangi videoyu etiketlediği izlenebilir. |
| Video erişimi | v5 (2.8) erişimi proje yürütücüsü ve akademik danışmanla sınırlar. **Bahar'ın videolara erişimi, etik kurula yapılacak değişiklik bildiriminin onayına bağlıdır.** Onay gelene kadar Bahar video görmez ve etiketlemez; videolar şifreli harici depolamada kalır. |
| Diğer geliştirme | Videolara erişmeden sentetik veya açık lisanslı, kişisel veri içermeyen girdilerle yapılır. |
| Bulut / üçüncü taraf | Video ve etiket dosyaları hiçbir bulut hizmetine, API'ye veya GitHub'a gönderilmez. |

> **v5 ile fark:** v5'te etiketlemeyi tek başına proje yürütücüsü yapar (2.3). İki etiketleyicili düzen, etik değişiklik onayı alındığında uygulanır. Onay alınamazsa etiketlemenin tamamını Pınar yapar; bölüm 7'deki kurallar değişmez.

## 3. Etiketleme aracı: ELAN

- **Araç:** ELAN (ücretsiz, çevrimdışı çalışır, video buluta gitmez, zaman aralıklarını milisaniye olarak dışa aktarır).
- **Katman (tier):** Her video için tek bir `davranis` katmanı. Değerler kontrollü sözlükten seçilir: `MATERYAL`, `TELEFON`, `DIS_YON`, `BELIRSIZ`. Serbest metin değer girilmez.
- **Not katmanı:** `not` katmanı yalnız belirsiz kesitlerin gerekçesi için kullanılır (ör. `yuz_ortulu`, `kadraj_disi`, `telefon_etkilesimi_belirsiz`). Kişiyi tanımlayan bilgi yazılmaz.
- **Etiketlenmemiş boşluk:** Hiçbir aralığa düşmeyen süre `UNLABELED` sayılır. Kayıt sonu dahil hiçbir boşluk otomatik `MATERYAL` sayılmaz.
- **Dışa aktarma:** Sekme ayrımlı metin; sütunlar `start_ms`, `end_ms`, `label`. Dosya adı yalnız sahte kod, oturum, tur ve etiketleyici kodu içerir: `P03_SCENARIO_r1_A1.tsv`. Etiketleyici kodları (`A1`, `A2`) ile kişiler arasındaki eşleme yalnız ekipte tutulur.
- **Saklama:** `.eaf` proje dosyaları ve dışa aktarımlar `local_data/labels/` altında durur (Git tarafından yok sayılır). `.eaf` dosyası video yolunu içerdiğinden paylaşılmaz.

## 4. Sınıf tanımları ve karar kuralları (v5 Ek-2'nin ayrıntılı hali)

### 4.1 Tanımlar

| Etiket | Dahil | Dahil değil |
| --- | --- | --- |
| `MATERYAL` | Kitap/deftere bakma, okuma, yazma, not alma, soru çözme; sayfa çevirme ve kalem alma gibi materyalle ilgili kısa hareketler | Telefonla aktif etkileşim; materyalden belirgin biçimde dışarı bakma |
| `TELEFON` | Kamerada görünen telefonla aktif, gözlenebilir etkileşim: telefona bakarak tutma, ekrana dokunma, yazma, kaydırma | Masada duran ve kullanılmayan telefon; elde tutulan ama bakılmayan ve dokunulmayan telefon |
| `DIS_YON` | Başın veya bakışın çalışma materyalinden belirgin biçimde dışarı çevrilmesi (sabit hedefe, yana, yukarı bakma) | Materyal içinde satır/sayfa değiştirirken oluşan küçük baş hareketleri |
| `BELIRSIZ` | Yetersiz görüş, ağır örtülme, yüzün ya da elin kadraj dışında kalması, güvenilir sınıf kanıtının olmaması | Kanıt yeterli olduğu halde etiketleyicinin kararsız kalması (bu durumda 4.2'deki öncelik kuralı uygulanır) |

### 4.2 Öncelik ve özel durumlar

1. **Telefon görünüyor ama etkileşim belli değil:** Görülen davranış etiketlenir (ör. kişi kâğıda bakıyorsa `MATERYAL`). Davranış da görülemiyorsa `BELIRSIZ`.
2. **Telefon elde, bakış başka yöne:** Bakış ve baş belirgin biçimde materyal dışındaysa ve telefonla etkileşim yoksa `DIS_YON`.
3. **Telefon ile dışa bakış art arda:** Ayrı aralıklar olarak etiketlenir. Birleştirilmez.
4. **Kısa dışa bakışlar:** Süresine bakılmaksızın, açıkça görülen her `DIS_YON` aralığı etiketlenir. 3 saniyelik kesinti eşiği etiketlemede değil, hesaplamada (bölüm 6) uygulanır. Böylece 2 ve 5 sn duyarlılık analizi aynı etiketlerle yapılabilir. Etiketlenecek en kısa aralık **0,5 sn**'dir; daha kısa davranışlar çevresindeki aralığın etiketini alır.
5. **Sınırlar:** Davranışın başlangıç ve bitişi senaryo komut zamanından değil, **görsel incelemeyle** belirlenir (v5, 2.2). Başlangıç, yeni davranışın açıkça görüldüğü ilk karedir. Bitiş, sonraki davranışın açıkça görüldüğü ilk karedir. ELAN'da kare kare ilerleme kullanılır.

## 5. Zaman çözünürlükleri ve türetilmiş etiketler

Üç ayrı zaman ölçeği vardır. Hepsi insan etiketlerinin **milisaniyelik aralıklarından** hesaplanır, birbirinden türetilmez.

### 5.1 Aralık etiketi (`HumanLabelInterval`)

ELAN'dan gelen `[start_ms, end_ms)` aralıkları. Oturum video zamanı, oturum başlangıcından itibaren milisaniye cinsindendir (`data-schema.md` 3.2).

### 5.2 Tekil saniye referansı (`SecondReference`)

Her `[s, s+1000)` saniyesi için:

- Bir ana sınıf saniyenin **500 ms'sinden fazlasını** kaplıyorsa saniye o sınıfı alır.
- `BELIRSIZ` ve `UNLABELED` toplamı **500 ms veya fazlaysa** saniye `BELIRSIZ` olur.
- Hiçbir koşul sağlanmıyorsa (ör. 500/500 eşitlik) saniye `GECIS` olarak işaretlenir.

Cohen κ (v5, 2.3) ve oturum ölçümleri (bölüm 6) bu 1 saniyelik zaman çizelgesi üzerinden hesaplanır. `GECIS` ve `BELIRSIZ` saniyeleri κ hesabında ayrıca raporlanır, ana sınıf uyumuna katılmaz.

### 5.3 Pencere etiketi (M1 eğitim hedefi)

Her 2 saniyelik `[t, t+2000)` penceresi için (1 sn kaydırma):

1. `BELIRSIZ` + `UNLABELED` toplamı **1000 ms veya fazlaysa** pencere **kullanılmaz**.
2. Aksi halde bir ana sınıf **1000 ms'den fazlasını** kaplıyorsa pencere o sınıfı alır.
3. Hiçbir sınıf yarıyı geçmiyorsa (ör. 1000/1000 eşitlik ya da üç sınıfın karışması) pencere `GECIS` olur ve **eğitimden çıkarılır**.

> **Neden milisaniye?** Hesap 1 saniyelik referanslardan yapılırsa 2 saniyelik pencerede "yarıdan fazla" kuralı "iki saniye de aynı mı" sorusuna dönüşür ve kısa geçişler kaybolur.

Bu kural `architecture.md` 4.2 madde 4'teki açık kararı kapatır.

## 6. Görünür kesinti tanımı ve olay eşleştirme

v5 2.7, kesintiyi "MATERYAL dışındaki gözlenebilir davranışın kesintisiz en az 3 saniye sürmesi" olarak tanımlar. Bu protokol tanımı **aynı sınıf** şartıyla uygular:

1. **Kesinti:** 1 saniyelik zaman çizelgesinde **aynı sınıftan** (`TELEFON` veya `DIS_YON`) ardışık en az 3 saniye.
2. **Farklı sınıflar art arda:** Ayrı durumlardır. Örneğin 2 sn `TELEFON` ve hemen ardından 2 sn `DIS_YON` kesinti sayılmaz.
3. **`BELIRSIZ` / `GECIS` araya girerse:** Kesinti bölünür. Belirsiz saniye bir kesintiyi doğrulamaz ve kesintiye eklenmez.
4. **Yumuşatma yok:** Tekil saniyeler yeniden yazılmaz; `TimelineResolver` politikası (`architecture.md` 4.1) korunur. v5'teki "aynı ardışık-zaman ve yumuşatma kuralı" ifadesi, model ve referansa aynı "yumuşatmasız" kuralın uygulanması olarak okunur.
5. **Eşik:** 3 sn önceden sabittir. 2 ve 5 sn yalnız duyarlılık analizinde kullanılır.
6. **Olay eşleştirme (kesinti olayı F1):** Modelin bulduğu kesinti, referanstaki bir kesintiyle **aynı sınıftaysa** ve **başlangıçları arasındaki fark ±2 sn içindeyse** doğru sayılır. Eşleştirme bire birdir: her referans olayı en fazla bir model olayıyla eşleşir. Birden fazla aday varsa başlangıç farkı en küçük olan seçilir.
7. **Odak süresi:** 1 saniyelik zaman çizelgesindeki `MATERYAL` saniyelerinin toplamı. Pencere süreleri toplanmaz.
8. **Odak oranı:** Odak süresi / geçerli oturum süresi. Geçerli süre, `BELIRSIZ` ve `GECIS` saniyeleri çıkarılmış süredir; bu saniyeler paydaya girmez ve ayrıca raporlanır.

## 7. Etiketleme güvenirliği: test–tekrar test (v5, 2.3)

1. **Alt küme (tekrar seti):** Tabakalama katılımcı × oturum düzeyindedir. **Her katılımcının her oturumundan**, oturum süresinin %25'i kadar **kesintisiz bir kesit** seçilir: senaryolu oturumda 5 dk, serbest oturumda 2,5 dk. Böylece toplam videonun %25'i tekrar edilir ve tüm katılımcılar temsil edilir.
   - **Başlangıç:** Kesitin başlangıcı sabit tohumla rastgele seçilir. **Tohum: `2209`.** Başlangıç, kesit oturum içinde kalacak biçimde `[0, oturum_süresi − kesit_süresi]` aralığından çekilir.
   - **Sınıf temsili:** Kesitte ilk etiketlere göre `TELEFON` **veya** `DIS_YON` yoksa kesit 30 sn'lik adımlarla ileri kaydırılır; oturum sonuna gelince başa dönülür. İki sınıfın da bulunduğu ilk konum kullanılır.
   - **Bulunamazsa:** Oturumda iki sınıftan biri hiç yoksa (ör. serbest oturumda telefon kullanılmadıysa) kesit ilk rastgele başlangıçta bırakılır ve bu durum not edilir.
   - Seçilen kesitler (oturum, başlangıç, bitiş, kaydırma sayısı) kayıt altına alınır. Tekrar setindeki videolar ilk etiketlemede önce etiketlenir; böylece 4 haftalık süre en erken dolar.
2. **Etiketleyici:** Bir videoyu ilk kim etiketlediyse tekrarını da o yapar (etiketleyici-içi test–tekrar test).
3. **Ortak deneme (zorunlu):** Etiketlemeye başlamadan önce iki etiketleyici aynı kısa videoyu ayrı ayrı etiketler. Farklar karar kılavuzuna göre konuşulur, gerekirse kılavuz güncellenir. Bu deneme izin öncesi yalnız açık lisanslı veya sentetik videoyla yapılır ve araştırma verisine katılmaz.
4. **Süre:** İkinci etiketleme, ilk etiketlemeden **en az 4 hafta (28 gün)** sonra yapılır. Bu süre teslim tarihine göre kısaltılmaz; gerekirse tekrar etiketleme teslimden sonra yapılır ve sonuçları sonradan eklenir.
5. **Körleme:** İlk etiketler ve model çıktıları ikinci tur boyunca görülmez. İlk tur dosyaları ayrı klasöre taşınır, ikinci turdaki video sırası karıştırılır.
6. **Ölçüm:** 1 saniyelik çözünürlükte genel ve sınıf bazlı Cohen κ, yüzde uyum ve olay düzeyi uyum (±1 sn). Hedef: genel κ ≥ 0,70, sınıf bazlı κ ≥ 0,60.
7. **Uyuşmazlık:** İki tur arasındaki farklar karar kılavuzu esas alınarak yeniden incelenir. Kılavuzla çözülemeyen kesitler nihai referanstan çıkarılır ve gerekçesiyle listelenir.
8. **Sürümler:** İlk etiketler (`r1`), tekrar etiketleri (`r2`) ve nihai referans etiketler (`final`) ayrı sürümler olarak saklanır.
9. **Hedef altında kalırsa:** Kılavuz güncellenir, ilgili kesitler yeniden işaretlenir; ilk ve düzeltilmiş uyum birlikte raporlanır.
10. **Sınırlılık:** Bu tasarım etiketlerin **zamansal tutarlılığını** ölçer, etiketleyiciler arası uyumu ölçmez. Sonuçlar bu sınırlılıkla raporlanır.

## 8. Kılavuz sürümleri ve pilot

| Sürüm | Zaman | İçerik |
| --- | --- | --- |
| v0.1 (bu belge) | Faz 2.4 | Karar kuralları ve hesaplama tanımları |
| v0.9 | İP1 | Pilot kayıtla sınanmış kılavuz; örnek görüntüler eklenir |
| v1.0 | İP3 | Etiketleme deneyimine göre son hali |

- Teknik pilot, etik izinden sonra proje yürütücüsü ve bir gönüllüyle yapılır (v5, 2.2).
- İzin öncesi ELAN alıştırması yalnız açık lisanslı ya da sentetik videolarla yapılır. Bu videolar araştırma verisi gibi raporlanmaz.
- Kılavuzdaki örnek görüntüler gerçek gönüllü yüzü içermez; şema çizimi veya izinli, kişisel veri içermeyen görüntü kullanılır.

## 9. Veri güvenliği

- Dosya adlarında yalnız sahte katılımcı kodu (`P01`…) bulunur. Gerçek ad, öğrenci numarası veya tarih-saat bilgisi kullanılmaz.
- Kimlik eşleme listesi etiket ve videolardan ayrı, şifreli ortamda saklanır.
- `local_data/` klasörü Git tarafından yok sayılır. PR öncesi `git status` ile etiket/video dosyası eklenmediği kontrol edilir.

## 10. Veri şemasıyla ilişki ve gereken güncellemeler

| Şema kaydı | Bu protokoldeki karşılığı | `data-schema.md` için gereken değişiklik |
| --- | --- | --- |
| `HumanLabelInterval` | 5.1 | `annotator_id` (etiketleyici kodu) kalır; yanına `label_round` (`r1` / `r2` / `final`) eklenir |
| `SecondReference` | 5.2 | İnsan etiketindeki `BELIRSIZ`, şemadaki `UNCERTAIN` durumuna karşılık gelir; `GECIS` değeri eklenmeli; `agreement_status` alanı test–tekrar test karşılaştırmasını göstermeli |
| Pencere etiketi | 5.3 | `WindowRecord` için `train_label` (`MATERYAL` / `TELEFON` / `DIS_YON` / `GECIS` / `UNUSED`) |
| Kesinti olayı | 6 | `InterruptionEvent(session_id, label, start_ms, end_ms, source)` |

Bu değişiklikler ayrı bir PR'da `data-schema.md` üzerinde yapılır.

## 11. Ekipçe kapatılan kararlar

- [x] Etiketlenecek en kısa aralık: **0,5 sn** (4.2 madde 4).
- [x] Telefon elde ama bakış başka yöndeyse: **`DIS_YON`** (4.2 madde 2).
- [x] 1 saniyelik referansta 500/500 eşitlik: **`GECIS`** (5.2).
- [x] Tekrar seti: her katılımcının her oturumundan, tohum `2209` ile rastgele başlangıçlı, sürenin %25'i kadar kesintisiz kesit; `TELEFON` veya `DIS_YON` yoksa kesit kaydırılır (7.1).
- [x] `GECIS` saniyeleri, `BELIRSIZ` gibi odak oranının paydasına girmez (6.8).
- [x] Etiketlemeyi iki kişi yapar; tekrarı ilk etiketleyen yapar; etiketleme öncesi ortak deneme zorunludur (2, 7.2, 7.3).

## 12. Otomatik testler (sentetik veriyle, Issue #17 ile uyumlu)

- 5.2 ve 5.3: Sınırdaki aralıklar (ör. 999/1001 ms, 1000/1000 eşitlik, yarı belirsiz pencere) doğru etiketleniyor.
- 6: 3 sn aynı sınıf kesinti sayılıyor; 2 sn `TELEFON` + 2 sn `DIS_YON` sayılmıyor; araya giren `BELIRSIZ` kesintiyi bölüyor; 2,9 / 3,0 / 3,1 sn sınırları.
- 6.6: ±2 sn içinde ve aynı sınıftaki olay eşleşiyor, farklı sınıf eşleşmiyor; bir referans olayı iki kez eşleşmiyor.
- 6.7–6.8: Odak süresi oturum süresini aşmıyor; örtüşen pencereler iki kez sayılmıyor; `BELIRSIZ` ve `GECIS` saniyeleri odak oranının paydasına girmiyor.
- 7: Aynı etiket dizisinde κ = 1; ilk ve tekrar etiket dosyaları birbirine karışmıyor; tekrar etiketi ilk etiketleyiciyle aynı `annotator_id`'yi taşıyor.
- 7.1: Aynı tohumla tekrar seti seçimi her çalıştırmada aynı sonucu veriyor; kesit oturum sınırını aşmıyor; `TELEFON`/`DIS_YON` yoksa kaydırma ve başa dönme doğru çalışıyor; sınıf hiç yoksa ilk başlangıç korunuyor.

## Revizyon kaydı

- **v0.1 (25 Kasım 2026):** TÜBİTAK başvurusunun son hali (v5) ve ekip yöntem kararlarına göre ilk taslak. Pencere etiketi, BELİRSİZ, kesinti ve test–tekrar test kuralları yazıldı.
- **v0.2 (25 Kasım 2026, #19):** İki etiketleyicili düzen (Bahar'ın video erişimi etik değişiklik onayına bağlı), tekrarı ilk etiketleyenin yapması, zorunlu ortak deneme, tekrar seti seçim kuralı (tohum `2209`), `GECIS`'in odak oranı paydasından çıkarılması, `annotator_id` + `label_round`; açık kararlar kapatıldı.
