from pathlib import Path
import json,subprocess,importlib.metadata
import pandas as pd
R=Path(__file__).resolve().parents[1]; RP=R/'reports';RP.mkdir(exist_ok=True)
s=json.loads((R/'results/summary.json').read_text());cmp=json.loads((R/'results/comparison_summary.json').read_text());q=pd.read_csv(R/'results/tables/country_outlook_2050.csv');d=pd.read_csv(R/'results/tables/scenario_decomposition.csv');sens=pd.read_csv(R/'results/tables/threshold_horizon_sensitivity.csv')
def table(df):
 cols=list(df.columns); lines=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
 for row in df.itertuples(index=False,name=None):lines.append('| '+' | '.join(str(x) for x in row)+' |')
 return '\n'.join(lines)
t=s['turkiye'][0]; low=q.TFR.lt(2.1);grow=q.total_change.gt(0)
refs='''1. United Nations DESA, Population Division (2024). [World Population Prospects 2024](https://population.un.org/wpp/). Yarışma Dropbox paketindeki Medium, OtherVariants, codebook ve supplement. CC BY 3.0 IGO. Ham dosya hashleri `sources/input_manifest.json`.
2. UN DESA (2024). [WPP2024 Methodology, Tablo II.4 ve s.55–56](https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/files/documents/2024/Jul/undesa_pd_2024_wpp2024_methodology-report_web.pdf). Senaryo varsayımları ve ayrıştırma zinciri. Arama dizinindeki ilgili bölüm okundu; PDF'nin doğrudan indirilmesi 403/404 ile engellendi. Tam raporun tamamının okunduğu iddia edilmiyor.
3. UN DESA. [Demographic Components of Future Population Growth: 2015 Revision](https://www.un.org/development/desa/pd/content/demographic-components-future-population-growth-2015-revision). Yöntemin daha eski uygulaması ve Andreev, Kantorová ve Bongaarts (2013) atfı. 2015 sayıları bu analizde kullanılmadı.
4. UNSD. [M49 ülke/bölge sınıflandırması](https://unstats.un.org/unsd/methodology/m49/). Coğrafi etiketlerin hukuki statü anlamına gelmediği notu ve Northern America üyeliği kontrolü.
5. ASA (2022). [Ethical Guidelines for Statistical Practice](https://www.amstat.org/your-career/ethical-guidelines-for-statistical-practice). Varsayım, sınırlılık, veri kaynağı ve katkıların açıklanması.
6. ASA (1 Mayıs 2026). [International Data Quest duyurusu](https://magazine.amstat.org/blog/2026/05/01/dataquest/). Üç değerlendirme kategorisi ve ülke/uluslararası değerlendirme yapısı. Yazı önceki yarışmanın World Development Indicators verisinden de söz ediyor; bu yarışmanın veri seçimi için güncel Dropbox rehberini esas aldık.
7. Ceylan Yozgatlıgil. [Türkiye 2026 kayıt duyurusu](https://tr.linkedin.com/posts/ceylan-yozgatligil-a1111112_asa-international-data-questturkiye-2026-activity-7500088083418148864-dxm2). Beş dakikalık video bilgisi. Duyurudaki 30 Ekim tarihi ile kullanıcının ilettiği e-postadaki 31 Ekim arasında fark var; bu çalışmada doğrudan iletilen e-posta esas alındı.
8. [İdil Tuzkaya'nın deposu](https://github.com/idiltuzkaya/asa_dataquest), public HEAD `3f7b4edb0c542bbb65a93490eb7b5cbc41a7600e`. Yerel ek çalışma `cef9c2f`. Önceki çalışmanın katkıları denetim raporunda ayrı ele alındı.
'''
(RP/'KAYNAKLAR.md').write_text('# Kaynaklar ve erişim durumu\n\nErişim: 18 Ekim 2026 (Europe/Istanbul).\n\n'+refs)
report=f'''# ASA Data Quest 2026: bağımsız analiz ve sonuçlar

Bu çalışma 18 Ekim 2026 tarihinde `chatgpt` altında ham veriden yeniden kuruldu. Önceki kod ve sayısal tablolar, bağımsız sonuçların hashleri sabitlendikten sonra incelendi. İlk aşamada GitHub README özeti görüldüğü için çalışma tamamen kör sayılmaz. Başarılı hesap kontrolleri geleceğin kesin bilindiği anlamına gelmez.

## 1. Yarışma ne istiyor?

Veriden araştırma sorusu üretmek, istatistiksel olarak savunulabilir bulgular çıkarmak, görselleştirmek ve etik sonuçlarını açıkça anlatmak gerekiyor. Paylaşılan e-postaya göre giriş ve kaynakça dışında **4 içerik sayfası** ile video bağlantısı teslim edilecek. Bu pakette bu nedenle kapak + 4 içerik + kaynakça = 6 sayfa bulunuyor. Türkiye ve uluslararası değerlendirme için sunum İngilizce, açıklama raporları Türkçe hazırlandı.

E-postaya göre son tarih **31 Ekim 2026 gün sonu**, değerlendirme 1–15 Kasım. Daha eski açık duyuruda 30 Ekim ve 5 dakikalık video bilgisi bulunuyor; 31 Ekim'i e-postadan aldık ve videoyu 5 dakikanın altında hedefledik. Formun gerçek URL'si, mentor Excel'i ve takım kimlikleri bu konuşmada yok. Bu eksikler analizi engellemez, ancak nihai başvurunun tamamlandığı söylenemez. E-posta yanıtı veya başvuru gönderilmedi.

## 2. Araştırma sorusu

**2023'te düşük doğurganlığa sahip ülke ve bölgeler neden 2050'ye kadar büyüyebilir? Yaş yapısı, ölüm oranları ve göç varsayımları bu görünümü nasıl değiştirir; büyüme yönü ne kadar belirsizdir?**

2050 yakın dönem planlama ufku olarak seçildi; 2075 ve 2100 duyarlılık analizidir. Bu seçim keşifseldir, ön kayıtlı hipotez testi değildir. Türkiye yerel bağlam için örnektir; küresel sonucu yalnız Türkiye üzerinden genellemiyoruz. Yeni bir nüfus tahmin modeli eğitmedik; BM'nin mevcut modellerini karşılaştırıyoruz. Bu nedenle model tahmin başarısı veya nedensel politika etkisi iddia etmiyoruz.

## 3. Ham veri denetimi

- Dropbox'tan yeniden indirilen 6 dosya yerel kaynaklarla SHA-256 düzeyinde aynı.
- Medium: 84.360 satır, 67 sütun; 555 konum. 237 ülke/bölge ve 318 örtüşen toplulaştırılmış grup.
- 1950–2100 ülke paneli: 35.787 satır. 1950–2023 tarihsel tahmin; 2024–2100 projeksiyon.
- 2101'de yalnız 1 Ocak nüfusu var. Genel gösterge analizinden çıkarıldı, sınır stok kontrolünde kullanıldı.
- OtherVariants: 662.919 satır, 18 etiket. `Mean` nüfus serisi içermiyor; her etiket aynı değişken/yıl/konum kapsamına sahip değil. Bu 18 etiketin hepsi bağımsız olasılıklı örneklem veya eşdeğer senaryo değildir.
- Supplement: 236 ülke/bölge × 151 yıl. Holy See yok; 151 eksik satır korunuyor. Beş ek gösterge uydurulmadı.
- Ülke seçimi ISO3 varlığı ve `Country/Area` etiketiyle ayrı ayrı yapıldı ve aynı küme verdi. Altı coğrafi bölge ve dünya toplamları kaynak toplamlarıyla uyuşuyor. Northern America'nın kaynakta bulunmayan 918 üst kodu, yalnız ilgili beş üye için açıkça ele alındı.
- Nüfus ve akış birimi **bin kişi**. Grafiklerde milyon için 1.000'e, milyar için 1.000.000'a bölündü.
- `DoublingTime` eksikleri doldurulmadı. Negatif/sıfır büyüme ve çok düşük pozitif büyüme için raporlanmama durumu ayrıştırılabilir; bir yayın eşiğinin nedeni bu veri tek başına kullanılarak kanıtlanamaz.

Önemli veri sınırlılığı: `PopChange = Births − Deaths + NetMigrations` eşitliği kaynakta tam kapanmıyor. En büyük fark **4,862 bin kişi**, Ukraine 1989. Farkın nedenini belgesiz biçimde yalnız yuvarlamaya bağlamadık. Buna karşılık `Jan(t+1) − Jan(t) = PopChange` stok eşitliği sayısal hassasiyetle kapanıyor. Ayrıştırma, akış toplamı yerine stokları kullanıyor. Tüm farklar `annual_identity_residuals.csv` içinde saklandı.

## 4. Yöntem

Başlangıç P₀ = 1 Ocak 2024 nüfusu. Hedef Pₜ = 1 Ocak 2050 nüfusu. 2050 başı ile 2050 sonu aynı değildir.

Kendi hesaplarımız şu ardışık stok farklarını kullanır:

| Bileşen | Hesap |
| --- | --- |
| Momentum | Momentum(t) − P₀ |
| Mortalite | Instant replacement zero migration(t) − Momentum(t) |
| Doğurganlık | Zero migration(t) − Instant replacement zero migration(t) |
| Göç | Medium(t) − Zero migration(t) |
| Toplam | Medium(t) − P₀ |

Dört bileşenin toplamı net değişimdir. Başlangıç nüfusuna bölmek, bileşenleri başlangıcın yüzde puanları olarak verir; birbirini götüren bileşenlerde net değişime oranla oluşabilecek aşırı/kararsız payları önler. Bu matematiksel eşitliğin kapanması nedensellik kanıtı değildir.

BM senaryolarının resmi tanımı yenilenme düzeyini NRR=1 ile ilişkilendirir. Her ülkeye ve yıla sabit 2,1 çocuk dayatıldığı anlamına gelmez. Ana sınıflandırmadaki TFR<2,1 yaygın yaklaşık eşiktir; NRR<1 ile ayrıca kontrol edildi. Senaryo farkları uygulanan sıraya bağlı olabilir. Mortaliteyi aynı tutup doğurganlık ile göçün sırasını değiştiren, gerçekten kapanan ikinci bir yol da hesaplandı. Eksik faktöriyel senaryolar nedeniyle tam Shapley ayrıştırması iddia edilmedi.

## 5. Bulgular

**2023 TFR<2,1 olan 130 ülke/bölgenin 64'ü (%49,2), Medium senaryoda 1 Ocak 2050'de başlangıcından daha kalabalık.** Bu 64 birimin 2023 nüfusu, düşük doğurganlıklı grubun nüfusunun %57,7'sini oluşturuyor. Ülke sayısı ve nüfus ağırlığı farklı sorulara yanıt verir.

![Doğurganlık ve büyüme](../results/figures/02_fertility_growth.png)

Daha önemli belirsizlik sonucu: Bu 64 ülke/bölgeden yalnız **6'sının** 2050 için kendi BM %95 tahmin aralığı bütünüyle başlangıç nüfusunun üstünde. Diğer **58'inde** aralık başlangıç nüfusunu kapsıyor. Bu, 58'inin kesin küçüleceği anlamına gelmez. Ayrıca 64'e ait bir güven aralığı değildir: ülke aralıkları marjinaldir; ortak örneklem yolları olmadan büyüyen ülke sayısının eşzamanlı belirsizliği hesaplanamaz. Başlangıç nüfusundaki tarihsel tahmin hatası burada ayrıca modellenmedi.

### Türkiye

| 1 Ocak 2024'ten 1 Ocak 2050'ye | Milyon kişi |
| --- | ---: |
| Başlangıç | {t['baseline']/1000:.3f} |
| Momentum katkısı | +{t['momentum']/1000:.3f} |
| Mortalite katkısı | +{t['mortality']/1000:.3f} |
| Doğurganlık katkısı | {t['fertility']/1000:.3f} |
| Göç katkısı | {t['migration']/1000:.3f} |
| Net değişim | +{t['total_change']/1000:.3f} |
| Medium hedef nüfus | {t['Medium']/1000:.3f} |
| BM %95 tahmin aralığı | {t['Lower 95 PI']/1000:.3f}–{t['Upper 95 PI']/1000:.3f} |

Türkiye için Medium değişimi **+%{t['total_change']/t['baseline']*100:.2f}**. 1 Ocak 2100 hedefi ise 65,667 milyon, başlangıca göre −%24,84. Aynı ülke yakın ve uzak ufukta farklı işaret verebilir. Pozitif momentum, yüzyıl boyunca kaçınılmaz büyüme anlamına gelmez. Bu WPP2024 veri sürümündeki tahminlerdir; güncel TÜİK gözlemi olarak sunulamaz.

![Türkiye belirsizliği](../results/figures/04_turkiye_uncertainty.png)

Dünya 1 Temmuz Medium serisinin tepe yılı {s['world_peak_july_year']}, tepe nüfusu {s['world_peak_billions']:.3f} milyar. Tarih etiketi açık yazıldığı sürece 1 Ocak serisiyle yapılan önceki özetin farklı başlangıç/yıl sonu nüfusları hata değildir.

### Duyarlılık

{table(sens[sens.year.eq(2050)][['definition','minimum_population_thousands','low_fertility','low_and_growing']].rename(columns={'definition':'Tanım','minimum_population_thousands':'Asgari nüfus (bin)','low_fertility':'Uygun düşük grup','low_and_growing':'Büyüyen'}))}

Aynı 2023 TFR<2,1 kohortunda büyüyenlerin sayısı 2050'de 64, 2075'te 46, 2100'de 28. Kohortu hedef yılda yeniden seçmedik. NRR<1 tanımı 2050 için 66/130 sonucu verir; aynı payda aynı üyeler demek değildir. En az bir milyon nüfuslu ülkelerde TFR<2,1 sonucu 39/81 (%48,1). Düşük doğurganlık ile yakın dönem büyümenin birlikte görülebilmesi tek eşik veya küçük bölgelere bağlı değil; kesin sayılar tanıma bağlı.

Türkiye'nin 2050 göç katkısı, doğurganlık/göç sırası değiştirilince yaklaşık 0,464 milyon değişiyor. Bu iki bileşenin ayrı paylarının model yolu seçimine duyarlı olduğunu gösterir. Grafik/tablolar bu farkı görünür kılar.

## 6. İstatistiksel yorumun sınırları

Ülke-yıllarını bağımsız rastgele örneklem sayıp çok küçük p değerleri üretmedik. Projeksiyonların düzgünleşmesi bilinen model yapısının bir sonucudur; gerçek dünyada bir müdahalenin etkisini kanıtlamaz. BM'nin yayımladığı %80/%95 aralıklar model varsayımlarına koşulludur. High/Low deterministik doğurganlık senaryoları bu aralıkların yerine geçmez. Ülkelerin alt/üst sınırları toplanarak dünya aralığı üretilmedi. Momentum ve bileşen farklarına, ortak simülasyon örneklemleri bulunmadığı için uydurma güven aralığı çizilmedi.

Doğurganlık, yaşam beklentisi ve medyan yaşın nüfus ağırlıklı ülke ortalaması resmi dünya göstergesinin aynısı değildir. Bu çalışmada dünya göstergesi gerektiğinde BM World satırı kullanılır. Yaş grupları, istihdam ve mali veriler olmadan emeklilik yükü veya işgücü etkisi ölçülmüş gibi gösterilmez.

## 7. Etik ve kullanım

Ülkeler/bölgeler küçük bir toplulukla büyük bir devleti aynı sayım birimi içinde tutar; bunun sonuçlara etkisi ayrıca raporlandı. Coğrafi sınıflamalar hukuki statü değerlendirmesi değildir. Göç ve doğum tercihleri burada politik hedef veya nüfusların değeri için ölçü değildir. Veri revizyonu, savaş/göç koşullarında ölçüm zorluğu ve model yanlılığı sonuçları etkileyebilir. Yapay zekâ kod, kontrol ve metin üretiminde kullanıldı; takımın yöntem ve sonuçları anlaması, katkıları açıklaması ve yarışma kurallarına uygunluğu kontrol etmesi gerekir.

## 8. Doğrulama ve yeniden üretim

Bağımsız ana hat 89 veri/h hesap kontrolünden geçti. İkinci uygulama `csv`, `gzip` ve `Decimal` ile 747.279 satırı tarayıp 11.100 bileşen değerini ve üç ufuktaki kohort sayılarını doğruladı. Önceki temiz dosyayla 59 ortak sayısal sütunda 2.111.433 değer aynı; eksik deseninde fark yok. Önceki ana log ayrıştırması kendi 2101 sınır tarihinde tekrar hesaplanınca en büyük hata 2,22e−16. Önceki dört betik ayrı kopyada çalıştırıldı ve 27 CSV/JSON tablo byte düzeyinde yeniden üretildi.

Bu kontroller ham verinin geleceğe ilişkin varsayımlarını kanıtlamaz. Desteklenmeyen “her şey kesin doğru” sözü yerine hangi kontrolün neyi kapsadığı kaydedildi. Ayrıntılı yorum/kod sorunları için [DENETIM.md](DENETIM.md), çalıştırma için [README](../README.md), kaynaklar için [KAYNAKLAR.md](KAYNAKLAR.md).
'''
(RP/'RAPOR_TR.md').write_text(report.replace('veri/h hesap','veri ve hesap'))
audit='''# Önceki çalışma: kod ve yorum denetimi

## Sonuç

Veri temizliği ve ana senaryo ayrıştırması yeniden üretilebiliyor. Sorunların çoğu hesap değerlerinden ziyade bu değerlerin sunuluşunda. Özgün dosyalara müdahale edilmedi. Arkadaşın public deposu (`3f7b4ed`) ile yerelde eklenen analiz/sunum (`cef9c2f`) ayrı ele alındı; yerel ek işin yazarlığı Git'ten tek başına kesinleştirilemez.

## Öncelikli bulgular

### 1. “Tam 2,1 çocuk” senaryo açıklaması yanlış (yüksek öncelik)

Yerel `analysis/04_figures.py` F2 ve `slides/build_deck.js` yöntem sayfası / konuşma metni, instant replacement koşulunu “every woman had exactly 2.1 children” şeklinde açıklıyor. BM'nin replacement senaryosu NRR=1 esaslıdır. Türkiye IRZM 2050 satırında TFR=2,0641 ve NRR=1,0000. Ayrıca kullanılan seri sıfır göçü de varsayıyor. Düzeltme: “replacement-level fertility, projected mortality, zero net migration” ve yenilenmenin yaklaşık 2,1 ile aynı olmadığı notu. Kişisel doğum sayısı da TFR'nin anlamı değildir.

### 2. Alternatif etkiler tek bir kapanan zincir oluşturmuyor (yüksek öncelik)

`analysis/03_decomposition.py` içindeki `alt` değişkeninde doğurganlık MED/IR, göç IR/IRZM, mortalite MED/CM alınmış. İlk iki oran tutarlı biçimde yer değiştirebilir, ancak üçüncüsünü eski momentumla birlikte toplamak toplam log büyümeyi vermez. Bu oranların ayrı karşılaştırma olarak kullanılması mümkündür; birlikte “ikinci zincir” denmesi ve %97'yi bütün yöntem dayanıklılığı gibi sunmak doğru değil. Ülke bazında toplamdan en büyük sapma Lesotho'da 0,167415 log birimi. Düzeltilen gerçek zincirde mortalite IRZM/MOM kalır; büyüklükçe baskın bileşen 232/237 (%97,89) ülkede aynı. Bu sonuç yalnız doğurganlık/göç sırası duyarlılığıdır; tüm olası sıralara ilişkin kanıt değildir.

### 3. “Büyüme zaten kesinleşti” sonucu senaryodan güçlü (yüksek öncelik)

`slides/VIDEO_SCRIPT.md` ve deck'in ana anlatısı “already baked in” ve “locked into growth” ifadeleriyle sonuca kaçınılmazlık yüklüyor. Momentum senaryosu varsayımsal bir koşuldur. Türkiye'de momentum pozitifken 2100 Medium toplamı negatiftir. Yeni anlatım yakın dönem kohort sonucu ve belirsizlik aralığı etrafında kuruluyor. 2050 Medium'da büyüyen 64 düşük doğurganlık biriminin 58'inde %95 aralık başlangıcı kapsıyor.

### 4. Yayınlanmış kod iddiası erişilen depoyla uyuşmuyor (orta)

18 Ekim 2026 kontrolünde public remote HEAD `3f7b4ed`; yerel `cef9c2f` ana ayrıştırma ve sunumu ekliyor. Sunumdaki “all code is public” ifadesi bu kontrol anında desteklenmiyor. Uzak depoya hiçbir şey gönderilmedi. Yeni pakette “reproducible code included in project package” kullanıldı; yayınlandığı söylenmiyor.

### 5. 0,29 tüm tarihsel dönemin özeti değil (orta)

`eda/02_eda_analysis.py` boundary hesabı 2014–2023 ve 2024–2033'ü karşılaştırıyor. Rapor 0,29 değerini 1950–2023'ün genel özelliği gibi açıklıyor. Tam tarihsel dönemde medyan |ΔLEx|=0,3493; 2014–2023'te 0,29435. Doğru pencere adları kullanılmalı. Mann–Whitney ülke-yıl p değeri bağımsızlık varsayımını karşılamaz; “descriptive” notu p değerini etki büyüklüğüne dönüştürmez. Model kaynaklı düzgünlüğü ölçmek için betimsel farklar yeterli.

### 6. Yaşam beklentisi dağılımı monoton daralmıyor (orta)

`eda/EDA_REPORT.md` SD'nin “decreased monotonically” olduğunu söylüyor. Ham veride yıllık SD 27 kez artıyor; ilk artış 1954. Başlangıç ve bitiş SD'sinin düşmesi monotonluk anlamına gelmez. Düzeltme: “uzun vadede azaldı, ara yıllarda artışlar var.”

### 7. “Göç tek pozitif etken” filtresi mortaliteyi dışarıda bırakıyor (orta)

`analysis/03_decomposition.py` içindeki `mig_only`, momentum ve doğurganlığa bakıyor, mortaliteye bakmıyor. Seçilen 49 birimin tamamında mortalite katkısı da pozitif. Ana hesap hatası değil, değişken/iddia kapsamı hatası. Düzeltme: “momentum ve doğurganlığın pozitif olmadığı yerlerde pozitif göç katkısı” veya dört bileşenin tümünü kontrol etmek.

### 8. Varyans payı nedensel açıklama oranı değil (orta)

`cov(component,total)/var(total)` payları toplamı 1 eden betimsel tahsislerdir. Etkileşimli, korelasyonlu bileşenlerde nedensel önem oranı veya dış örneklem açıklama gücü değildir; negatif olabilir. Yalnız `r`/HC3 p değerlerine dayanarak “belirsizliği esasen nüfus büyüklüğü belirler” demek de fazla güçlüdür. Yeni yarışma anlatımında bu iddialara gerek yok.

### 9. Gösterge ve metadata dili düzeltmeleri (düşük/orta)

- Public README “237 sovereign nations” diyor; doğrusu 237 countries and areas. 195 ülke listesi dışında kalan bütün birimleri tek tip “overseas territories/dependencies” olarak adlandırmak da isabetli değil.
- Slayt 1'de “17 alternative variants” yazıyor; dosyada 18 etiket var. `Mean` nüfus içermediği için sadece nüfus serilerini sayıyorsa bunun açıkça yazılması gerekir. “318 aggregate rows” yerine 318 aggregate locations denmeli.
- 2024 başlangıç nüfusu 2026 sunumunda “today” olarak adlandırılmamalı.
- Ana eski analiz 1 Ocak 2024 → 1 Ocak 2101, yani 2100 sonunu kullanıyor; bu tutarlı ve yanlış değil. Yeni çalışma 1 Ocak 2050'yi ana ufuk seçiyor. Farklı tarihli sonuçlar doğrudan hata diye karşılaştırılmadı.
- f02 “only DoublingTime missing” başlığı supplement'in beş sütunundaki Holy See eksiklerini dışarıda bırakıyor. “main-file indicators” kapsamı belirtilmeli.
- Nüfus ağırlıklı ülke TFR/LEx/medyan yaş ortalamaları dünya göstergeleri değildir. Orijinal grafikler ağırlığı kısmen yazıyor; yine de resmi seriyle aynıymış gibi yorumlanmamalı. Örnek: 2023 TFR ağırlıklı ortalama 2,181735; UN World 2,2505.
- Temizlik betiği bazı demografik kimlikleri denetliyor; bütün muhasebe eşitliklerinin kapandığı söylenemez. Kaynak akış-kapanış farkı ayrıca raporlandı.
- KDE tepe sayısını Hartigan testi gibi yorumlamamak; aynı kesitte seçilen k için küme kararlılığı iddia etmemek gerekir. Yalnız öneri aşamasındaki karmaşık araştırma soruları tamamlanmış sonuç değildir.
- Ekonomik yük/işgücü/çekim kapasitesi gibi konular için veri setinde bulunmayan değişkenler gerekir. Bu sonuçlar WPP göstergelerinden tek başına çıkarılamaz.

## Yeniden üretim kanıtı

- Dropbox ve önceki raw girdiler aynı.
- Temiz panelde 59 ortak sayısal sütun × 35.787 satır = 2.111.433 değer eşleşti.
- Amerika bölgelerini açıkça birleştirince bölge sınıfı farkı 0.
- Ana eski log ayrıştırması 2101 sınırında bağımsız yeniden hesaplandı: maksimum fark 2,22e−16.
- Eski temizlik, EDA, ayrıştırma, figür betikleri `audit_original` kopyasında başarılı çalıştı; 27 CSV/JSON çıktı byte düzeyinde aynı.
- Eski sunumun kaynak kodu ve PDF içeriği incelendi; altı sayfa görsel olarak kontrol edildi; ana analizde kullanılan grafikler izole kopyada yeniden üretildi. Paket bağımlılıkları mevcut makinede doğrulandı; her işletim sistemi/uygulama için garanti verilmez.

Makine çıktıları: `results/comparison_summary.json`, `results/tables/comparison_clean_values.csv`, `results/prior_raw_comparison.json`. Bağımsız aşama zaman/hash kaydı: `sources/independent_freeze.json`.
'''
(RP/'DENETIM.md').write_text(audit)
checklist='''# Teslim öncesi kontrol

Hazır: ham veri kopyaları ve hash doğrulaması, bağımsız analiz, ayrı doğrulayıcı, önceki kod karşılaştırması, dört içerik sayfalı İngilizce sunum, PDF, konuşma metni ve kayıt provası.

Takımın tamamlayacağı bilgiler/işlemler:

- Takım adı, tüm üyeler, üniversite ve lisans/yüksek lisans kategorisi kapağa eklenmeli. Bu bilgiler verilmediği için uydurulmadı.
- Takım üyeleri yöntemi, senaryo farkını, 64/130 ile 6/64 ayrımını ve Türkiye aralığını açıklayabilmeli.
- Sunum/video dili ve yapay zekâ kullanımına ilişkin yerel kurallar gerçek başvuru formundan veya mentordan kontrol edilmeli. Resmi ayrıntılı rubrik paylaşılmadı; puanlama ağırlıkları uydurulmadı.
- Hazırlanan 5 dakikanın altındaki sentetik sesli prova, takımın kişisel sunum kaydı değildir. Yarışma şartına uygun ekip kaydı ve erişilebilir video linki üretilmeli.
- E-postada “Sunum ve video gönderim formu” metni var, gerçek URL yok. Link geldikten sonra doğru formda dosya ve erişilebilir video bağlantısı teslim edilmeli.
- E-postaya göre 31 Ekim 2026 gün sonu son tarih. Eski ilan 30 Ekim dediği için mümkünse 30 Ekim'e kadar hazır olmak ve organizatörün güncel e-postasını saklamak uygun.
- Videonun toplam süresi 5 dakikayı geçmemeli. Linki oturum kapalı bir tarayıcıda açarak izinleri kontrol edin.
- Mentor Excel dosyası verilmedi; kişilere veya uygunluk saatlerine ilişkin tahmin yapılmadı.
- Bağlantıları aldığınızı teyit eden kısa e-postayı siz gönderin. Bu çalışma kimseye mesaj göndermedi, form doldurmadı, GitHub'a push yapmadı.

Önerilen teyit metni: “Merhaba Ceylan Hocam, veri seti ve ilgili bağlantıları aldık. Bilgilendirme için teşekkür ederiz. İyi çalışmalar.”
'''
(RP/'TESLIM_KONTROL.md').write_text(checklist)
readme='''# ASA Data Quest 2026 — bağımsız ChatGPT çalışması

Önce [Türkçe sonuç raporunu](reports/RAPOR_TR.md), sonra [önceki çalışma denetimini](reports/DENETIM.md) okuyun. [Teslim kontrolü](reports/TESLIM_KONTROL.md) eksik takım/form bilgilerini açıklar.

## Ana dosyalar

- `slides/ASA2026_Demographic_Momentum.pptx`: kapak + 4 içerik + kaynakça, düzenlenebilir grafikler.
- `slides/ASA2026_Demographic_Momentum.pdf`: aynı sunumun paylaşılabilir sürümü.
- `slides/VIDEO_SCRIPT_EN.md` ve `slides/VIDEO_SCRIPT_TR.md`: konuşma/kayıt metinleri.
- `slides/rehearsal.mp4`: 5 dakikanın altındaki sentetik sesli prova, başvuru yapılmış video değildir.
- `src/analyze.py`: sıfırdan yazılan veri kontrolü ve analiz.
- `tests/verify_independent.py`: pandas kullanmayan ikinci doğrulama.
- `src/compare_prior.py`: önceki projeyle bağımsız karşılaştırma.
- `results/tables`: ham birimleri koruyan CSV tabloları; `results/figures`: PNG/PDF grafikler.
- `sources`: rehber metinleri, hash kayıtları, kaynak erişim notları.
- `audit_original`: eski kodun sadece denetim için kullanılan izole kopyası; bağımsız çözümün kodu değildir.

## Yeniden çalıştırma

Python 3.12+ önerilir. Bu makinede kullanılan tam sürümler `logs/environment.json` dosyasında.

```sh
cd /Users/buraksahinkucuk/Desktop/asa/chatgpt
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/analyze.py
.venv/bin/python tests/verify_independent.py
```

Karşılaştırma özgün `../asa_dataquest` klasörü bulunduğunda çalışır:

```sh
.venv/bin/python src/compare_prior.py
.venv/bin/python src/write_reports.py
```

Sunumun üretimi Codex'in yerel Artifact Tool çalışma ortamını kullanır. `src/build_slides.mjs` ve `src/build_video.py` kaynakları pakettedir; Python analizi bu özel Node kütüphanesine ihtiyaç duymaz. Grafik verileri `slides/chart_data.json` içinde de bulunur. Sunum PDF dışa aktarımı ve slayt renderları ayrıca kaydedilir. Yeniden sunum üretirken mevcut dosyanın üzerine yazmamak için `DECK_OUTPUT=yeni_sunum.pptx` ortam değişkeni kullanın. Video üretimi macOS `say`, FFmpeg ve Pillow gerektirir; analiz bunlara ihtiyaç duymaz. Son paket kontrolleri `results/deliverable_validation.json` içindedir.

## Sayıların anlamı

Başlangıç: 1 Ocak 2024. Ana hedef: 1 Ocak 2050. TFR sınıflaması: 2023. Ülke sayısı ülke ve bölgeleri kapsar. Raw nüfus ve katkı birimi bin kişi; tablolardaki `pct_base` alanları başlangıç nüfusunun yüzdesidir. 1950–2023 tahmin, 2024 sonrası projeksiyondur. Senaryo etkileri nedensel politika etkisi değildir.

Veri kaynağı UN WPP2024 ve yarışma supplement'i (CC BY 3.0 IGO). Arkadaşın önceki deposuna ve AI katkısına raporlarda atıf vardır. Bu klasör dışında dosya değiştirilmedi; dışarıya hiçbir teslim/push yapılmadı.
'''
(R/'README.md').write_text(readme)
(R/'requirements.txt').write_text('\n'.join(f'{p}=={importlib.metadata.version(p)}' for p in ['numpy','pandas','matplotlib'])+'\n')
(RP/'BASVURU_OZETI_EN.md').write_text('''# Abstract

Low fertility does not imply immediate population decline, but deterministic growth projections can conceal uncertainty. Using UN World Population Prospects 2024, we isolate 237 countries and areas and compare population on 1 January 2024 with 1 January 2050. Of 130 places with a 2023 total fertility rate below 2.1, 64 grow under the Medium projection. Only six of those 64 have a marginal 95% prediction interval entirely above the baseline. A sequential comparison of UN scenarios separates population change into momentum, mortality, fertility and migration contrasts. For Türkiye, positive momentum and mortality contrasts outweigh negative fertility and migration contrasts through 2050, yielding 91.31 million people, while the 95% interval spans 74.57–107.92 million. Alternative fertility definitions, minimum population filters and longer horizons test sensitivity. The decomposition is conditional on the UN model and scenario ordering, not a causal policy estimate. Source verification and a second implementation support reproducibility. We emphasize uncertainty, reproductive autonomy and respectful interpretation of migration.
''')
print('Reports written')
