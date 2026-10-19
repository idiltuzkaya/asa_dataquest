# Önceki çalışma: kod ve yorum denetimi

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
