Faz 1.3 — Etik ve Hukuki Hazırlık Kontrol Listesi
Proje: Masa Başında Kâğıt Tabanlı Çalışmada Görsel Dikkat Durumunun ve Odak Süresinin Bilgisayarlı Görü ile Kestirimi
Ekip: Bahar ve Pınar
Tarih: 9 Kasım 2026 (güncelleme: 25 Kasım 2026, #30 — öneri v5 uyumu)
Durum: Etik kurul başvurusu yapıldı, karar bekleniyor (öneri v5 §2.8). Bu belge etik kurul onayı, hukuk görüşü veya izin belgesi değildir.
İlgili iş paketi: Faz 1 / İP1 (8 haftalık iç yol haritası)
1. Araştırma bağlamı ve sınırlar
- 8–10 yetişkin gönüllü; kişi başına 20 dakika senaryolu ve 10 dakika serbest oturum.
- Tek kamera; baş pozu, göz açıklık oranı (yardımcı gösterge), el/bilek göstergeleri (yazma hareketi, telefona uzanma, telefonu tutma) ve görünür telefon ipuçları (v5 §2.4).
- Ses kaydı alınmaz; kimlik tanıma yapılmaz (v5 §2.8).
- Ana sınıflar: MATERYAL, TELEFON, DIŞ_YÖN; BELİRSİZ ana sınıf değil, özel çıktıdır.
- M0 kural tabanlı yaklaşım, M1 Random Forest; katılımcı bazlı LOSO.
- Araştırma zihinsel dikkati veya öğrenme başarısını doğrudan ölçtüğünü iddia etmez. Odak süresi, çalışma materyaline görünür yönelimin zamansal kestirimidir.
- Araştırma videosu/öznitelikleri ve kimlik eşlemesi GitHub'a yüklenmez.
2. Etik izin / muafiyet kararı (öncelikli ve engelleyici)
- [ ] Danışmana araştırmanın katılımcı, video, öznitelik, veri saklama ve analiz protokolü yazılı iletildi.
- [ ] Yetkili etik kurulun/birimin hangisi olduğu resmî olarak teyit edildi.
- [ ] Onay, muafiyet veya başka kurum değerlendirmesi gerekliliği yazılı netleştirildi.
- [x] Gerekliyse başvuru formu, araştırma protokolü, katılımcı belgeleri ve ekler yetkili birime sunuldu. (v5 §2.8: başvuru yapıldı, süreç başlatıldı.)
- [ ] Resmî cevap, tarihi, referans numarası ve varsa koşulları özel ve erişim kontrollü yerde saklandı; GitHub'a kişisel verili belge yüklenmedi.
- [ ] İzin kapsamı ile fiilî kamera, kayıt, analiz, katılımcı ve saklama akışı eşleştirildi.
Karar beklenirken: Gerçek gönüllülerin tanınabilir görüntüleri araştırma amacıyla kaydedilmeyecek; sentetik/kişisel veri içermeyen testlerle geliştirme devam edecek.
3. Katılımcı bilgilendirmesi ve gönüllü onamı
- [ ] Katılımcıların 18 yaş veya üzerinde olması doğrulanacak; yaş doğrulama için gereksiz kimlik fotokopisi tutulmayacak.
- [ ] Amaç, deney görevleri, toplam süre (30 dk), kamera açısı, kaydedilecek veriler ve olası rahatsızlıklar açıklanacak.
- [ ] Katılımın gönüllü olduğu, katılmama/ayrılma durumunda yaptırım bulunmadığı belirtilecek.
- [ ] Araştırmadan çekilme yöntemi ve çekilmenin önceden toplanan veriler üzerindeki etkisi açıklanacak.
- [ ] Katılımcı onam/bilgilendirme formu danışman ve gerekiyorsa etik kurul tarafından değerlendirilecek.
- [ ] Kullanılan onam formunun sürümü ve onam alındığına dair kayıt güvenli biçimde tutulacak.
- [ ] Oturum esnasında üçüncü kişilerin görüntüye veya ses kaydına tesadüfen girmesini önleyecek düzen kurulacak.
4. KVKK aydınlatma ve hukuki dayanak
- [ ] Veri sorumlusu (kurum/kişi), varsa temsilci ve başvuru/iletişim kanalı kurum tarafından belirlendi.
- [ ] Her veri türü için amaç, toplama yöntemi ve KVKK m.5/m.6 uyarınca hukuki dayanak doğrulandı.
- [ ] Aktarım olup olmadığı, varsa alıcı grupları ve amaçları belirlendi.
- [ ] KVKK m.11 kapsamındaki ilgili kişi hakları aydınlatma metnine eklendi.
- [ ] Aydınlatma metni veri işlemeden önce sunulacak şekilde hazırlandı ve kurumsal değerlendirmeden geçti.
- [ ] İşleme açık rızaya dayanıyorsa ayrı açık rıza metni ve ayrı beyan düzenlendi; açık rıza gerekip gerekmediği otomatik varsayılmadı.
- [ ] Yüz görüntüleri/işaret noktaları ve olası biyometrik veri niteliği, gerçek işleme amacı ve yöntemi açısından yetkili birimce değerlendirildi.
- [ ] Değişen amaç, kamera açısı, dış aktarım veya teknoloji için yeniden değerlendirme tetikleyicisi tanımlandı.
Not: Yüz görüntüsü kişisel veri olabilir; her yüz görüntüsünün otomatik olarak özel nitelikli biyometrik veri olduğu varsayılmaz. Ancak yüz/özellik işleme tekniklerinin hukuki sınıflandırılması projeye özgü yapılmalıdır.
5. Veri minimizasyonu ve güvenliği
- [ ] Veri envanteri hazırlandı: ham video, zaman damgası, etiket, baş/yüz/göz göstergeleri, telefon ipuçları, katılımcı kodu, varsa onam kayıtları.
- [ ] Ses kaydı kapalı; gerekiyorsa gerekçe ve yeni değerlendirme şart.
- [ ] Kamera görüş alanı yalnızca gerekli çalışma alanıyla sınırlandırıldı.
- [ ] Gerçek isim yerine participant_id kullanılıyor; kimlik eşleme listesi ayrı ve erişimi kısıtlı.
- [ ] Ham videolar, etiketler, türetilmiş özellikler ve yedekler için erişim yetkisi belirlendi.
- [ ] Depolama ortamı ve taşınabilir cihaz güvenliği (erişim koruması, mümkünse şifreleme) doğrulandı.
- [ ] Dış bulut, çevrim içi servis, üçüncü taraf API veya yurt dışı aktarımı varsa ayrıca hukuki ve etik inceleme yapıldı.
- [ ] .gitignore ve yayın öncesi kontrol: ham kayıt, görüntü, onam, kimlik eşleme, kişisel verili CSV/JSON GitHub'a gitmiyor.
- [ ] Sentetik test verilerinin sentetik olduğu açıkça belirtiliyor; gerçek araştırma verisi gibi raporlanmıyor.
5.1 Öneri v5'e göre erişim, saklama ve test telefonu
- Video erişimi: v5'e göre yalnız proje yürütücüsü (Pınar) ve akademik danışman. Videolar şifreli harici depolamada tutulur; üçüncü taraf API veya bulut hizmetine gönderilmez (v5 §2.8).
- İki etiketleyici: Ders projesinde etiketlemeyi Pınar ve Bahar birlikte yapacaktır. Bu, v5'teki erişim tanımının dışındadır; bu nedenle:
  - [ ] Bahar'ın araştırmacı ve video erişimi olan kişi olarak eklenmesi için etik kurula değişiklik bildirimi gerekip gerekmediği danışmanla netleştirilecek; gerekiyorsa bildirim yapılacak.
  - [ ] Aydınlatma metnindeki "verilere erişecek kişiler" bilgisi buna göre güncellenecek.
  - [ ] Onay gelene kadar Bahar videolara erişmez ve etiketleme yapmaz; onay alınamazsa etiketlemenin tamamını Pınar yapar (labeling-protocol.md §2).
- Saklama ve silme (v5 §2.8, bütçe kalemleri): birincil kopya şifrelenebilir harici SSD'de, yedek ayrı fiziksel diskte (harici HDD) şifreli; kimlik eşleme listesi videolardan ayrı, şifreli USB bellekte. Ham videolar etik kurulun onayladığı süre içinde ve en geç proje bitiminden 6 ay sonra güvenli biçimde silinir; yalnızca etiketler ve yüz görüntüsü içermeyen türetilmiş öznitelikler saklanır.
- Test telefonu (v5 §2.2): Masada proje yürütücüsü tarafından sağlanan, kişisel içerik bulunmayan bir test telefonu bulunur; katılımcının kendi telefonu kullanılmaz.
  - [ ] Pınar'ın kendi telefonu kullanılacaksa v5 koşulu sağlanmalıdır: kişisel içerik görünmeyecek ayrı/boş bir kullanıcı profili ya da sıfırlanmış yedek cihaz; bildirimler kapalı; her oturumdan önce ekran kontrolü. Bu koşul sağlanamıyorsa yedek bir cihaz bulunur.
- İzin öncesi geliştirme: Yalnız sentetik veri ve açık lisanslı, kişisel veri içermeyen örnekler (v5 İP2); bunlar araştırma verisi gibi raporlanmaz.

6. Saklama, çekilme, silme ve olay yönetimi
- [ ] Her veri kategorisi için saklama gerekçesi ve saklama süresi veri sorumlusunca belirlendi; süre rastgele atanmadı.
- [ ] İzin verilen güvenli silme/yok etme/anonimleştirme yöntemi ve yedeklere uygulanması açıklandı.
- [ ] Katılımcının çekilme ve veri hakları talebini ileteceği iletişim noktası belirlendi.
- [ ] Veri talebi alındığında sorumlunun inceleme/yanıt süreci, ilgili mevzuata uygun biçimde tanımlandı.
- [ ] Veri silme/imha işlemlerine dair gerekli kayıtların nasıl tutulacağı belirlendi.
- [ ] Kayıp cihaz, yanlış paylaşım veya yetkisiz erişim halinde kurumun olay bildirim/yanıt süreci belirlendi.
Hukuki dikkat: Çekilme, her koşulda bütün verilerin derhal silinmesiyle eşanlamlı değildir; veri işleme şartları, ilgili kişi hakları ve uygulanabilir imha hükümleri dikkate alınır.
7. Araştırma protokolüne özel etik riskler
Risk	Kontrol / azaltma önlemi	Sorumlu	Durum
Kamera karşısında rahatsızlık	Açık bilgilendirme, durdurma/çekilme hakkı, makul oturum süresi	Ortak	Açık
Üçüncü kişinin kadraja girmesi	Kayıt alanını kontrol etme, mümkünse izole ortam	Bahar	Açık
Telefonda özel içeriğin görünmesi	Katılımcının kendi telefonu kullanılmaz; kişisel içeriksiz test telefonu (v5 §2.2), bildirimler kapalı, oturum öncesi ekran kontrolü	Pınar	Açık
İkinci etiketleyicinin onaysız video erişimi	Etik değişiklik onayı gelene kadar Bahar video görmez; erişim listesi aydınlatma metniyle uyumlu tutulur	Pınar	Açık
Kayıt anında ekip üyesinin odada bulunması	Kayıt sırasında kimlerin bulunacağı başvuru ve aydınlatma metniyle karşılaştırılır	Pınar	Açık
Yanlış dikkat/başarı çıkarımı	Sadece görünür yönelim hakkında iddia; birey performansı puanlamama	Ortak	Açık
Etiketleyiciye kimlik ifşası	Kodlu katılımcı, sınırlı erişim, gereksiz kimlik bilgisini gizleme	Pınar	Açık
Katılımcıya ait görüntünün GitHub'a sızması	.gitignore, PR kontrolü, ayrı güvenli depolama	Pınar	Açık
İzin sürecinin gecikmesi	Gerçek kayıt yok; sentetik teknik testlere devam	Ortak	Açık


8. Danışmana yöneltilecek karar soruları
1. Yetkili etik kurul/birim hangisi? Resmî onay veya muafiyet değerlendirmesi gerekiyor mu?
2. Başvuru kim tarafından yapılacak ve hangi evraklar gerekli?
3. Kurum/veri sorumlusu kim olacak; KVKK irtibat noktası ne olacak?
4. Araştırmanın veri işleme hukuki dayanağı nedir; ayrı açık rıza gerekecek mi?
5. Yüz işaret noktalarının işlenmesi özel nitelikli veri açısından nasıl değerlendirilmeli?
6. Ham video zorunlu mu, yoksa mümkün olan kısımlarda yalnız öznitelik saklanabilir mi?
7. Ham video, özellikler, onam ve kimlik eşlemesi için saklama süreleri nedir?
8. Veri saklama ortamı, yetkili erişim, yedekleme ve imha politikası nasıl kurulmalı?
9. Kullanılacak katılımcı bilgilendirme/onam formları hangi birimce onaylanacak?
10. Etik değerlendirme beklenirken hangi sentetik veya kişisel veri içermeyen teknik pilotlara izin var?
9. Karar günlüğü
Tarih	Konu	Karar / belge referansı	Kararı veren	Durum
2026-11-09	Etik izin / muafiyet	Henüz doğrulanmadı	Danışman ve yetkili birim	BEKLİYOR
2026-11-09	Veri sorumlusu ve hukuki dayanak	Henüz belirlenmedi	Yetkili kurum	BEKLİYOR
2026-11-09	Saklama ve silme süreleri	Henüz belirlenmedi	Yetkili kurum	BEKLİYOR
2026-11-09	Gerçek gönüllü kayıtları	İzin/uygunluk netleşene kadar başlamama	Proje ekibi önleyici karar	UYGULANACAK
2026-11-25	Etik kurul başvurusu	Başvuru yapıldı (v5 §2.8); karar bekleniyor	Etik kurul	BEKLİYOR
2026-11-25	İki etiketleyici (Bahar'ın video erişimi)	Değişiklik bildirimi gerekip gerekmediği danışmanla görüşülüyor	Danışman ve etik kurul	BEKLİYOR
2026-11-25	Test telefonu	Kişisel içeriksiz test telefonu (v5 §2.2); Pınar'ın telefonu ancak bu koşulla	Proje ekibi	UYGULANACAK
2026-11-25	Kayıt penceresi	2–5 Aralık 2026, yalnız izin belgesi alınmışsa	Proje ekibi	UYGULANACAK


10. Faz 1.3 çıkış kapısı
- [ ] Danışman görüşmesi yapıldı ve kararlar kayıt altına alındı.
- [ ] Yetkili kurul ve başvuru/karar süreci netleşti.
- [ ] Etik durum dürüstçe bekliyor, başvuruldu, onaylandı veya muafiyet teyit edildi şeklinde belgelendi.
- [ ] Veri envanteri, rol/sorumluluklar ve güvenlik taslağı hazırlandı.
- [ ] Katılımcı aydınlatma/onam dokümanlarının hazırlanmasından sorumlular belirlendi.
- [ ] Gerçek kayıt için gerekli izinler sağlanmadan görüntü toplanmaması kuralı korundu.
Önemli ayrım: Faz 1.3'ün hazırlık/dokümantasyon çıktısı tamamlanabilir; bu, gerçek gönüllü kaydı için izin verildiği anlamına gelmez. Gerçek veri toplama kapısı ayrıca doğrulanır.
11. Resmî ve kurumsal kaynaklar (9 Kasım 2026 erişim taraması)
1. KVKK — Aydınlatma yükümlülüğü: https://www.kvkk.gov.tr/Icerik/2033/Aydinlatma-Yukumlulugu-
2. KVKK — Aydınlatma yükümlülüğü duyurusu: https://www.kvkk.gov.tr/Icerik/6765/AYDINLATMA-YUKUMLULUGUNUN-YERINE_GETIRILMESI-HAKKINDA-KAMUOYU-DUYURUSU (bağlantı başlığı değişirse KVKK sitesinde ara)
3. KVKK — 2026/347 ilke kararı (Resmî Gazete 24.03.2026): https://www.lexpera.com.tr/resmi-gazete/metin/kisisel-verileri-koruma-kurulunun-18-02-2026-tarihli-ve-2026-347-sayili-karari-33203
4. KVKK — Biyometrik veri kapsamı bakımından 2020/915 kararı: https://www.kvkk.gov.tr/Icerik/6872/2020-915
5. KVKK — Silme, yok etme ve anonimleştirme: https://www.kvkk.gov.tr/Icerik/2038/kisisel-verilerin-silinmesi-yok-edilmesi-veya-anonim-hale-getirilmesi
6. KVKK — Silme/yok etme/anonimleştirme yönetmeliği: https://www.kvkk.gov.tr/Icerik/5441/KISISEL-VERILERIN-SILINMESI-YOK-EDILMESI-VEYA-ANONIM-HALE-GETIRILMESI-HAKKINDA-YONETMELIK
7. Fırat Üniversitesi — Etik kurullar formları: https://etikkurullar.firat.edu.tr/tr/page/9327
8. Fırat Üniversitesi — Etik kurullar iletişim: https://etikkurullar.firat.edu.tr/page/9201
9. TÜBİTAK 2209-A program sayfası: https://tubitak.gov.tr/tr/burslar/lisans-onlisans/destek-programlari/2209-universite-ogrencileri-arastirma-projeleri-destekleme-programi
Revizyon notu: Bu liste proje içi hazırlık/checklist belgesidir; kurumsal etik karar, resmî başvuru ekleri, katılımcı onamı ve KVKK aydınlatma metinlerinin yerine geçmez. Karar noktaları netleşince güncellenmelidir.
