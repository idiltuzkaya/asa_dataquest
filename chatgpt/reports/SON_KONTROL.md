# Son teslim paketi kontrolü

Tamamlama: 19 Ekim 2026, Europe/Istanbul. Araştırma ve ilk hesaplar 18 Ekim'de yapıldı.

- Ana analiz: 89 kontrol başarılı. Bağımsız ikinci uygulama: 11.100 sayısal karşılaştırma başarılı.
- Son dosyalar: 27 yapısal/sayısal kontrol başarılı (`results/deliverable_validation.json`).
- Sunum: 6 sayfa, 4 yerel PowerPoint grafiği ve 4 gömülü veri çalışma kitabı. Son dosyanın SHA-256 değeri finalizer kaydıyla aynı. Grafikler sayısal veri içerir ve düzenlenebilir.
- PDF'nin altı sayfası görsel olarak incelendi. Konuşma notu düzeltmesinden sonraki son PDF renderlarının altısı da incelenen görüntülerle birebir aynı.
- Artifact Tool ile LibreOffice çizimlerinde font/işaretçi renk farkları var. PDF saçılım grafiği tek renk, yerel önizleme düşük doğurganlık noktalarını ayrıca renklendiriyor; gözlem sayısı, koordinatlar ve sonuçlar aynı. PDF'de 237 gerçek gözlem dışında sahte başlangıç noktası veya hatalı referans çizgisi bırakılmadı.
- Microsoft PowerPoint uygulamasında açıp çalıştırma yapılmadı. Sunum paket/import denetimleri ile Artifact Tool ve LibreOffice renderları kontrol edildi.
- Son konuşma notlarının altısı da `narration.json` ile eşleşiyor. Kaybolan referans çizgilerine ilişkin eski anlatım çıkarıldı.
- Video bütünüyle FFmpeg ile hatasız çözüldü; ses ve görüntü akışları mevcut, ses seviyesi sıfır değil. Örnek kare görsel olarak kontrol edildi. Sentetik telaffuzun insan tarafından dinlenerek onaylandığı iddia edilmiyor.
- Video sentetik sesli prova ve henüz yüklenmiş/gönderilmiş başvuru değildir.
- Önceki proje kodları, verileri ve raporları değişmedi; Git çalışma ağacı temiz. Finder'ın `.DS_Store` metadata dosyasında fark var, bu dosya bilimsel koruma kontrolünden ayrı tutuldu.
- Bağımsız aşamada sabitlenen 31 dosyanın hashleri değişmedi.

ZIP; ham veriyi, kendi kodumuzu, testleri, raporları, sonuçları, nihai sunum/video dosyalarını ve denetim kayıtlarını içerir. Geçici `.build`, bağımlılık klasörleri, yinelenen Dropbox ZIP'i ve sembolik bağlantılar arşive alınmaz. Tam çalışma klasörü yerelde korunur. `compare_prior.py` yeniden çalıştırılırken özgün komşu `asa_dataquest` deposuna ihtiyaç duyar.

Önceki kaynak manifestindeki “remote verification pending” ifadesi ilk kopyalama anını kaydeder. Sonraki `sources/dropbox_verification.json` altı dosyanın yeniden indirilerek doğrulandığını gösterir.

Ölçülen video süresi: 286.072 saniye (yaklaşık 4 dakika 46 saniye).
