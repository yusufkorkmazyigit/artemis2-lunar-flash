# artemis2-lunar-flash: Proje Bağlam Dosyası

> Bu dosya Claude Project'in bilgi tabanı için yazıldı. Projeyle ilgili her oturumda önce bunu oku.
> Son güncelleme: 23 Ekim 2026 · Sahibi: Yusuf Korkmazyiğit
> Repo: https://github.com/yusufkorkmazyigit/artemis2-lunar-flash

---

## 1. Tek cümlede proje

Artemis II astronotları Ay'ın arka yüzündeki tam güneş tutulması sırasında beş soluk çarpma parlamasını **çıplak gözle** gördü. Bu proje, astronot sesini ve fotoğrafları zamana göre eşleyen açık bir veri seti ve web gezgini kuruyor, sonra bu indeksle **parlamalardan herhangi birinin kameraya da düşüp düşmediğini** araştırıyor.

**Ana araştırma sorusu:** Gözle görülen 5 parlamadan herhangi biri Nikon Z9/D5 karelerinde tespit edilebiliyor mu? Edilemiyorsa, her olay için hangi parlaklığın üstünde bir şey olmadığını (üst sınır) söyleyebiliyor muyuz?

---

## 2. Neden önemli

- **Bilim:** Ay'a ne sıklıkla küçük göktaşı çarptığı, gelecekteki Ay üsleri ve altyapısı için bir risk girdisi.
- **Veri:** NASA'ya göre Artemis II arşivi, 50 yılı aşkın sürede ağırlıklı olarak insanlar tarafından toplanan ilk gezegen bilimi veri seti. Astronotun *söylediği* ile kameranın *kaydettiği*ni birbirine bağlayan bir araç şu an yok.
- **Zamanlama:** Veri 7 Ekim 2026'da yayınlandı. Erken çalışan az kişi var.
- **Kariyer:** Almanya'da yüksek lisans başvurusu (Kış 2027/28) ve Airbus hedefi için somut, yayınlanabilir bir çıktı. Arşivde Airbus'ın Bremen'de yaptığı Avrupa Servis Modülü'nün (ESM) güneş paneli kanatlarındaki kameraların görüntüleri de var.

---

## 3. Ben kimim, nasıl çalışıyorum (proje için gerekli olan kadarı)

- Erciyes Üniversitesi (ERÜ) bilgisayar mühendisliği, uzatma senesi. Güz döneminde sadece bitirme projesi var, mezuniyet 2027 baharı.
- Python ve ML biliyorum. Erciyes Nötrino Araştırma Grubu'nda (ENRG) Çerenkov/sintilasyon sinyal ayrımı üzerine ML çalıştım; nadir sinyali gürültüden ayırma problemi bu projeyle doğrudan akraba.
- ENRG'nin Linux CPU/GPU sunucularının yöneticisiyim. Ağır veri işleme orada yapılacak.
- **Zaman bütçesi:** Haftada 1 gün. Bitirme projesi her zaman önce gelir. Hafta içi sabahları çalışıyorum.
- **Dil:** Benimle Türkçe konuş. Kod, yorumlar, commit mesajları, README ve veri seti dokümantasyonu İngilizce.

---

## 4. Arka plan: ne oldu?

- Artemis II, Nisan 2026'da 4 astronotla Ay'ın çevresinden dolaştı: Reid Wiseman, Victor Glover, Christina Koch (NASA), Jeremy Hansen (CSA).
- Ay'ın arka yüzündeyken, planlı iletişim kesintisi sırasında yaklaşık **54 dakika süren bir tam güneş tutulması** yaşandı. Orion o sırada Ay'a yaklaşık 46.000 mil uzaktaydı.
- Bu karanlıkta astronotlar Ay yüzeyinde **5 iğne ucu gibi ışık parlaması** gördü. NASA'ya göre bunlar insan gözüyle görülmüş en soluk Ay parlamaları olabilir.
- NASA bilim ekibi kozmik ışın ve uzay aracı yansımalarını eledikten sonra gözlemleri doğruladı.
- **İşaretler:** 6 Nisan 2026 tarihli bir tablet ekran görüntüsünde, tutulmadaki Ay'ın **simüle edilmiş** bir görüntüsü üzerine elle çizilmiş notlar var. Wiseman mavi, Glover yeşil, Hansen kırmızı. Parlamalar #1–#5 olarak numaralı, yanlarında gözlemci noktaları var. Taban görüntü simülasyon olduğu için konumlar **yaklaşık**.
- Wiseman'ın notuna göre **#1, #2 ve #4 tutulmanın yaklaşık 10. dakikasında** oldu.
- Bir ses kaydında Hansen ve Wiseman aynı anda bir parlama gördüklerini söylüyor.
- NASA'nın yayınladığı materyalde **hiçbir parlamanın fotoğrafta ya da videoda yakalandığına dair bir bilgi yok.** Projenin boşluğu tam burası.
- NASA'nın yayınladığı işaretli parlama görselinin kimliği: `art002e016252` (impactflash_annotation).

---

## 5. Veri: PDS arşivi

Toplam **800 GB'ın biraz üstü**, NASA Planetary Data System'de (PDS), 3 düğümde 5 PDS4 paketi (bundle) halinde.

| Paket | Düğüm | İçerik | Koleksiyonlar | DOI |
|---|---|---|---|---|
| `artemis2_crew_camera` | Imaging (CIS) | Astronot el kameraları: Nikon D5 ×2, Nikon Z9 | `data_source`, `data_raw`, `data_processed`, `browse` | 10.17189/x52v-tb80 |
| `artemis2_orion_camera` | Imaging (CIS) | SAW 2/3/4 (güneş paneli GoPro'ları), CAB 2, OpNav, DCAM | `browse_source`, `data_raw_image`, `data_video` | 10.17189/hzev-nq50 |
| `artemis2_mission_audio` | Imaging (CIS) | Tablet (PCD) sesleri, ses döngüleri, deşifreler, astronot notları | `data_audio_pcd`, `data_audio_loops`, `data_transcripts_pcd`, `data_transcripts_loops`, `annotations` | 10.17189/4a29-dz64 |
| `artemis2_mission` | Geosciences (lider) | Dokümanlar, kapsül çevre verisi | `document`, `data_orion_environment` | 10.17189/36fx-pd80 |
| `artemis2_spice` | NAIF | Konum ve yönelim (SPICE kernel'ları) | `spice_kernels`, `document`, `miscellaneous` | 10.17189/7ezn-0294, **henüz yayınlanmadı** |

### 5.1 Düzen ve adlandırma
- Ürünler UTC metadata'sına göre uçuş günü klasörlerinde: `fd01` … `fd10`.
- Her ürün = 1 veri dosyası + 1 ayrı XML etiketi (PDS4 label).
- LID örneği: `urn:nasa:pds:artemis2_crew_camera:data_source:art002eXXXXXX_nkd5015_src.nef`
- Fotoğraf kimliği: `art002e` + 6 hane. Video: `art002m` + 10 hane.
- Dosya adı örüntüleri:
  - `art002eXXXXXX_nkd5015_raw_vXX.tif` (Nikon D5 SN 3500015, ham)
  - `art002eXXXXXX_saw3_src_vXX.jpg` (SAW Cam 3, kaynak)
  - `art002mXXXXXXXXXX_saw3_vid_vXX.mp4` (SAW Cam 3, video)
- **TUZAK:** Kimlikteki sıra numarası kataloğa giriş sırasını gösteriyor, çekim sırasını değil. Her zaman etiketteki `<start_date_time>` alanına göre sırala.

### 5.2 Kameralar
**Astronot kameraları (Nikon):**
| Kamera | Seri no | Ana lens | Not |
|---|---|---|---|
| D5-015 | 3500015 | 80–400 mm "Long Lens" (~%98) | |
| D5-017 | 3500017 | 12–24 mm "Short Lens" (~%57), Long Lens (~%29) | Rehberde hem 12–24 hem 14–24 geçiyor, tutarsız |
| **Z9-019** | 39200019 | 35 mm (~%74) | **Tutulma gözlemlerinin ana kamerası** |

Formatlar: kaynak = NEF · ham = TIFF (2B dizi) · kısmen işlenmiş = TIFF (3B dizi) · önizleme = PNG.

**Orion kameraları:**
- SAW Cam 2, 3, 4: güneş paneli kanatlarında modifiye GoPro Hero 4 Black. SAW 3 yakın geçişin ana kamerası. SAW 1'de bilimsel veri yok. Fotoğraflar 4000×3000'e kadar.
- CAB Cam 2: kabin içinde GoPro, 3 numaralı pencerede.
- DCAM: Malin Space Science Systems, tek renkli CMOS. OpNav: Pixelink PL-D725MU, tek renkli. İkisi de navigasyon sensörü; Ay ve Dünya görüntüleri ikincil.
- SAW 3 canlı yayın kodlayıcıları: 1280×720@30fps, 640×360@5fps, 1280×720@5fps, 640×360@1fps.
- **Tutulmada yayın düşük kare hızına inince kareler kaydedilmemiş.** Uçuştan sonra elde kalan tek video `art002m1200970119`: 2 dk 10 sn, 30 fps.

**Henüz arşivde olmayan:** iPhone 17 Pro Max görüntüleri (hazırlanıyordu).

### 5.3 Ses ve notlar
- PCD (tablet) sesleri: M4A, Peltor kulaklıklarla kaydedildi. Konuşmalar üst üste binebiliyor. PCD 4 görev ortasında arızalandı.
- Ses döngüleri: Houston kontrol odası kayıtları. Arşivdeki formatı rehberde belirtilmemiş.
- Deşifreler: `data_transcripts_pcd`, `data_transcripts_loops`.
- **Astronot notları:** her tablette önceden hazırlanmış bir OneNote dosyası vardı. Her Ay hedefi için birkaç yakınlaştırma seviyesinde görüntü sayfası içeriyordu. `.one` dosyası indirilip PDF/A'ya çevrildi, `annotations` koleksiyonunda duruyor.
- Rehberin **Tablo 18**'i Nikon görüntü kimliklerini WAV etiketleriyle eşliyor. Bu tablo ses-görüntü eşlemesi için altın değerinde, bul ve oku.

### 5.4 Zaman ve metadata
- Tabletler ve astronot kameraları **Orion saatine senkronize** edildi. Zamanlar UTC, etiketteki `<start_date_time>` alanında.
- Kamera ayarları rehberin Tablo 5'inde. Astronotlar HDR ve mozaik için pozlama basamaklama (bracketing) ve çoklu pozlama kullandı.
- Etiketler PDS sözlüklerini kullanıyor (Core, Imaging, Cartography, COTS Camera vb.). Anahtar kelimeler "Artemis 2 Product Label Keyword Definitions" dokümanında.
- Lens bozulması modeli: `artemis2_nikon_lens_distortion_correction.pdf`.
- Video stream metadata'sı yer tarafında çözülen kare hızını gösteriyor; gerçek kare hızı farklı olabilir.

### 5.5 Kalibrasyon ve sınırlamalar (yanlış pozitif kaynakları)
- **Bilimsel kalibrasyon yok.** Sadece D5'lerin geometrik lens bozulması ölçüldü. Sensör ya da pencere için renk kalibrasyonu yapılmadı.
- **Pencereler:** üç katmanlı, biri dökme akrilik. Uçuş öncesi karakterize edilmedi, görüntüyü bozabiliyor. En iyi pencere 2 numara.
- **Parlama ve yansıma:** yakın geçişte kabin yüzeylerinden güneş yansıması; derin uzay görüntülerinde güneş panellerinden yansıma.
- Kalibre edilmiş ya da türetilmiş ürün yok. Nikon dosyaları kısmen işlenmiş, Orion görüntüleri ham.
- Çevre verisi: iki HOBO MX1101 kaydedici (SN 1104, SN 1105), 60 saniyede bir sıcaklık, nem, çiğ noktası. SN 1105, FD09'da Dolap D'den F'ye taşındı.

### 5.6 Bağlantılar
- PDS Artemis II ana sayfası: https://pds-geosciences.wustl.edu/missions/artemis2/index.htm
- Mission paketi dizini: https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/
- Data User Guide: https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf
- Archive Explorer (crew camera): https://pds-imaging.jpl.nasa.gov/tools/atlas/archive-explorer?mission=artemis2&bundle=artemis2_crew_camera
- Archive Explorer (orion camera): https://pds-imaging.jpl.nasa.gov/tools/atlas/archive-explorer?mission=artemis2&bundle=artemis2_orion_camera
- Archive Explorer (mission audio): https://pds-imaging.jpl.nasa.gov/tools/atlas/archive-explorer?mission=artemis2&bundle=artemis2_mission_audio
- PDS Image Atlas: https://pds-imaging.jpl.nasa.gov/tools/atlas/search
- Ön bilimsel rapor: https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/
- NASA duyurusu: https://nasa.gov/blogs/missions/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images
- Kullanım hakları: NASA görüntüleri ABD'de genelde telifsiz, kaynak gösterilerek kullanılır. NASA logosu yapay zekâ üretimi görsellerin yanına konamaz, NASA onayı ima edilemez.

---

## 6. Plan: üç faz

### Faz 1: Gözlem indeksi ve gezgin (hedef: 14 Aralık 2026)
Astronotun her cümlesini, o anda çekilen fotoğraflara zaman üzerinden bağlayan açık veri seti ve basit bir web gezgini. **Sonucu garanti; tek başına portfolyo çıktısı.**

### Faz 2: Parlama avı (hedef: 10 Ocak 2027)
Her "flaş" anının çevresindeki Z9/D5 karelerinde geçici ışık noktası aramak ve yanlış pozitifleri elemek. Çıktı: her olay için "tespit" ya da "üst sınır", ardından 1 sayfalık bilimsel özet.

### Faz 3: Genişletme (SPICE yayınlanınca)
Kareleri Ay haritasına oturtmak (georeferencing), indeksi tüm uçuş gözlemlerine yaymak.

### Haftalık takvim (haftada 1 gün)
| Hafta | Tarih | Yapılacak | Bitti sayılır, eğer… |
|---|---|---|---|
| 1 | 26 Eki – 1 Kas | Data User Guide'ı oku (özellikle Tablo 5, 17, 18 ve Ek C dizin ağaçları). Archive Explorer'da tutulma gününün Z9 karelerine bak | Tutulma hangi uçuş gününde, hangi UTC aralığında, biliniyor |
| 2 | 2 – 8 Kas | PDS4 etiket ayrıştırıcı: kimlik, kamera, lens, pozlama, zaman → Parquet/CSV | Bir uçuş günü için temiz bir tablo |
| 3 | 9 – 15 Kas | Tutulma penceresindeki ürünleri listele, küçük alt kümeyi ENRG sunucusuna indir | Tutulma kareleri diskte, boyut biliniyor |
| 4 | 16 – 22 Kas | Deşifreleri ayrıştır → zaman damgalı cümle tablosu (eksikse Whisper) | Cümle tablosu var, "flaş" anları işaretli |
| 5 | 23 – 29 Kas | Cümle ↔ kare eşleme. Elle 10 örnek doğrula | 10 örnekte doğru |
| 6 | 30 Kas – 6 Ara | Hugging Face'e yükle, Zenodo DOI al, LinkedIn duyurusu | DOI'li veri seti |
| 7 | 7 – 13 Ara | Web gezgini. **Faz 1 tamam** | Paylaşılabilir link |
| 8 | 14 – 27 Ara | Faz 2: callout anlarını gözle incele, ardından fark alma ve nokta kaynak tespiti | Her olay için aday listesi |
| 9 | 28 Ara – 10 Oca | Yanlış pozitif eleme, istatistik, sonuç, özet | Özet gönderildi ya da taslak hazır |

Güz finalleri ve bitirme teslimleri Aralık–Ocak'a çakışırsa Faz 2 kayar. Faz 1 tek başına yeterli bir çıktı.

---

## 7. Teknik mimari (mühendislik standartları)

### 7.1 Repo yapısı (hedef)
```
artemis2-lunar-flash/
├── pyproject.toml          # paket + bağımlılıklar + ruff/pytest ayarları
├── README.md
├── configs/
│   └── default.yaml        # yollar, zaman pencereleri, eşikler
├── src/a2flash/
│   ├── __init__.py
│   ├── cli.py              # tek giriş noktası: a2flash <komut>
│   ├── pds/
│   │   ├── inventory.py    # koleksiyon envanteri (collection_*.csv) okuma
│   │   ├── labels.py       # PDS4 XML etiket ayrıştırma → satır
│   │   └── download.py     # seçici, kaldığı yerden devam eden indirme
│   ├── audio/
│   │   ├── transcripts.py  # deşifre ayrıştırma
│   │   └── whisper.py      # eksik deşifre için (opsiyonel)
│   ├── align/
│   │   └── timeline.py     # cümle ↔ kare zaman eşleme
│   ├── flash/
│   │   ├── preprocess.py   # NEF/TIFF okuma, bias/sıcak piksel maskesi
│   │   ├── detect.py       # fark alma, nokta kaynak tespiti
│   │   ├── vetting.py      # kozmik ışın, yansıma, sıcak piksel eleme
│   │   └── stats.py        # enjeksiyon-geri kazanım, yanlış alarm oranı, üst sınır
│   └── explorer/           # web gezgini
├── notebooks/              # keşif; kalıcı kod src/'ye taşınır
├── tests/                  # pytest: etiket örnekleri, zaman eşleme, tespit
├── data/raw/ data/interim/ data/processed/   # git'e girmez
└── docs/
    ├── PROJECT_CONTEXT.md  # bu dosya
    └── decisions.md        # karar günlüğü
```

### 7.2 Araçlar
- Python 3.11+, paket yönetimi `uv` (ya da pip + venv).
- Kod kalitesi: `ruff` (lint + format), tip ipuçları, `pytest`. GitHub Actions'ta her push'ta lint ve test.
- Etiket okuma: `lxml` (ya da `pds4_tools`). Veri tabloları: `pandas` + Parquet, sorgu için `duckdb`.
- Görüntü: `rawpy` (NEF), `tifffile`, `numpy`, `scipy`, `scikit-image`, `astropy` (istatistik ve gerekirse fotometri). `photutils` nokta kaynak tespiti için aday.
- Ses: `ffmpeg`, gerekirse `openai-whisper` / `faster-whisper` (ENRG GPU'sunda).
- Gezgin: hızlı başlangıç için Streamlit; kalıcı ve barındırması bedava olsun istenirse Parquet + DuckDB-WASM ile statik site (GitHub Pages).
- Yayın: Hugging Face Datasets (dataset card ile), Zenodo (GitHub release → DOI).

### 7.3 Mühendislik kuralları
- **Tekrarlanabilirlik:** her çıktı tek bir CLI komutuyla ham veriden yeniden üretilebilir. Rastgelelikte sabit seed.
- **Ham veriye dokunulmaz:** `data/raw` salt okunur; her adım `interim/` ya da `processed/`'a yazar.
- **İndirme:** sadece ihtiyaç duyulan ürünler, checksum kontrolü, kaldığı yerden devam, istek hızı sınırı (PDS sunucularına nazik ol).
- **Zaman:** her şey UTC, ISO 8601, timezone-aware. Sıralama asla dosya numarasına göre değil.
- **Kaynak izi:** her satır kendi LIDVID'ini taşır; veri setindeki her bilgi PDS'teki ürününe geri götürülebilir.
- **Karar günlüğü:** önemli her teknik karar `docs/decisions.md`'ye tarih ve gerekçeyle yazılır.
- Notebook'lar keşif içindir; çalışan kod `src/`'ye taşınır ve test edilir.

### 7.4 Faz 1 veri modeli (taslak)
- `frames`: lidvid, product_id, camera (d5_015 | d5_017 | z9_019 | saw2 | …), lens, focal_mm, exposure_s, iso, f_number, start_utc, flight_day, file_url, browse_url
- `utterances`: utt_id, source (pcd | loop), speaker (varsa), start_utc, end_utc, text, audio_lidvid
- `links`: utt_id, lidvid, dt_seconds (kare zamanı − cümle zamanı), rule (ör. ±60 s penceresi)
- `annotations`: page, target, observer, flash_no (1–5), notlar

### 7.5 Faz 2 yöntemi (taslak)
1. **Callout zamanları:** deşifre, ses ve notlardan her parlamanın "görüldü" anını çıkar. Belirsizliği aralık olarak kaydet (ör. "tutulmanın ~10. dakikası").
2. **Aday kareler:** her callout aralığına düşen, gece tarafını gören Z9/D5 kareleri. Pozlama süresi, lens ve kadraj Ay'ı kapsıyor mu, kontrol et.
3. **Ön işleme:** ham TIFF; sıcak piksel ve kusurlu piksel maskesi (aynı kameranın karanlık karelerinden); gerekiyorsa lens bozulması düzeltmesi.
4. **Tespit:** ardışık ya da yakın karelerde fark alma; nokta yayılım fonksiyonuna (PSF) uyan geçici kaynak araması; yalnızca bir karede görünen nokta = aday.
5. **Eleme (vetting):** kozmik ışın (tek piksel ya da keskin iz, PSF'e uymaz) · sıcak piksel (birçok karede aynı yerde) · pencere ve kabin yansıması (Ay diski dışında ya da kamera hareketiyle birlikte kayan) · aday konumu astronotların işaretlediği yaklaşık bölgeyle tutarlı mı?
6. **İstatistik:**
   - *Yanlış alarm oranı:* aynı yöntemi callout pencereleri dışındaki karelere uygula, kare başına kaç aday çıkıyor ölç.
   - *Tespit verimi:* gerçek karelere bilinen parlaklıkta yapay PSF kaynakları enjekte et, kaçının bulunduğunu ölç (enjeksiyon-geri kazanım).
   - *Üst sınır:* tespit yoksa, verimin %50'yi (ya da %90'ı) geçtiği parlaklık = o olay için üst sınır. Kalibrasyon olmadığı için birim sayısal değer (DN) ya da, karede yıldız varsa, katalog yıldızlarına göre göreli kadir.
7. **Bağlam:** yer tabanlı Ay çarpma parlaması gözlemleri (ör. ESA'nın NELIOTA projesi) parlamaların süresi ve parlaklığı için karşılaştırma verir. Sayıları kullanmadan önce literatürden doğrula.

### 7.6 İlk kod görevi (Hafta 2)
`src/a2flash/pds/labels.py`: tek bir PDS4 XML etiketini alıp düz bir sözlük döndüren `parse_label(path) -> dict`. Testi: arşivden indirilmiş 3 gerçek etiket (`tests/fixtures/`), beklenen alanlar ve UTC zaman. Sonra `a2flash index --bundle crew_camera --flight-day fdXX` komutu bir uçuş gününün etiketlerini Parquet'e yazar.

---

## 8. Hedef çıktılar ve yayın

| Çıktı | Nerede | Ne zaman |
|---|---|---|
| Açık veri seti | Hugging Face + Zenodo DOI | Aralık 2026 |
| Web gezgini | GitHub Pages ya da Streamlit | Aralık 2026 |
| Bilimsel özet | **LPSC 2027** (15–19 Mart 2027, The Woodlands, Teksas; özet son tarihi henüz açıklanmadı, genelde Ocak başı) | Ocak 2027 |
| Yedek | **Europlanet Science Congress 2027** (Avrupa), ya da arXiv ön baskısı + blog | 2027 |
| Duyuru | Her kilometre taşında kısa LinkedIn paylaşımı | Sürekli |

LPSC sitesi: https://www.hou.usra.edu/meetings/lpsc2027/

---

## 9. Kararlar günlüğü

- **20 Eki 2026:** Repo açıldı (`master` dalı).
- **20 Eki 2026:** İlk fikir (5 etiketli parlamayla dedektör eğitmek) bırakıldı, çünkü parlamalar kameraya çekilmiş değil, gözle görülmüş. Yeni yön: ses ↔ görüntü indeksi + parlama araması.
- **20 Eki 2026:** ABC (Yapay Arı Kolonisi) bu projeye zorla entegre edilmeyecek. Doğal bir yeri çıkarsa değerlendirilir.
- **20 Eki 2026:** Haftada 1 gün, yaklaşık 9 hafta. Bitirme projesi önceliklidir.
- **22 Eki 2026:** Proje, Almanya yüksek lisans başvurusu ve Airbus hedefi için ana portfolyo projesi.

---

## 10. Açık sorular

- [ ] Tutulma hangi uçuş gününde, hangi UTC aralığında? (Rehber + Archive Explorer)
- [ ] Tutulma sırasında Z9'un pozlama ayarları neydi? Uzun pozlama var mı?
- [ ] Deşifrelerde zaman damgası var mı, yoksa ses dosyası başlangıcı + ofsetten mi hesaplanacak?
- [ ] Tablo 18 (Nikon kimlikleri ↔ WAV etiketleri) nerede, hangi biçimde?
- [ ] Crew camera paketinin ham dizin adresi (pds-imaging altında)
- [ ] SPICE paketi ne zaman yayınlanacak?
- [ ] Emrah Tıraş hoca projeyi ENRG çatısı altında destekler mi? (Konferans özetinde kurum ve ortak yazar)
- [ ] LPSC 2027 özet son tarihi ve katılmadan sunum imkânı

---

## 11. Riskler ve B planları

| Risk | B planı |
|---|---|
| Parlama hiçbir karede yok | Üst sınır sonucunu yaz. Faz 1 veri seti ve gezgin zaten ana çıktı |
| LPSC son tarihi kaçar ya da Teksas'a gidilemez | Europlanet 2027, ya da arXiv + blog |
| İndirme yavaş, disk yetmiyor | Sadece tutulma penceresi, işlem ENRG sunucusunda |
| Deşifreler eksik ya da zamansız | Whisper, zamanı ses etiketinden al |
| Zaman yetmiyor | Faz 1'de dur. Bitmiş Faz 1, yarım Faz 2'den değerli |

---

## 12. Kaynaklar

- NASA, "NASA Releases Artemis II Lunar Science Data, Images" (7 Ekim 2026): https://nasa.gov/blogs/missions/2026/10/07/nasa-releases-artemis-ii-lunar-science-data-images
- NASA Science, "Artemis II Preliminary Lunar Science Report": https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/
- Artemis II Lunar Science Data User Guide (PDF): https://pds-geosciences.wustl.edu/artemis2/urn-nasa-pds-artemis2_mission/document/artemis2_data_user_guide.pdf
- PDS Geosciences, Artemis II: https://pds-geosciences.wustl.edu/missions/artemis2/index.htm
