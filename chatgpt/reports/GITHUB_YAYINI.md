# GitHub yayını — 19 Ekim 2026

Kullanıcının açık push talebi üzerine çalışma `busahinku/asa_dataquest` fork'una, `chatgpt-analysis` dalına hazırlanmıştır. Bağlı hesabın `idiltuzkaya/asa_dataquest` deposuna yazma yetkisi yoktur. Arkadaşın deposuna doğrudan yazılmamıştır.

Dal, önceki yerel `cef9c2f` ayrıştırma/sunum commit'ini ve `chatgpt/` altındaki bağımsız çalışma paketini içerir. Ham veri, kod, testler, raporlar, denetim çıktıları, grafikler, PPTX/PDF ve sentetik prova videosu sürümlenir. Büyük dağıtım ZIP'i release eki olarak sunulur. Geçici build dosyaları, bağımlılıklar, Finder metadata dosyaları, makineye özel sembolik bağlantılar ve aynı ham verinin ikinci kopyası olan Dropbox ZIP'i Git'e eklenmez.

Önceki raporlardaki “push yapılmadı” ve “kod henüz public değil” ifadeleri ilk denetim anını anlatır. Bu yayın yarışma formunun gönderildiği anlamına gelmez. Özgün yerel depo korunmuştur.

Depoyu klonlayınca bağımsız analiz:

```sh
git clone -b chatgpt-analysis https://github.com/busahinku/asa_dataquest.git
cd asa_dataquest/chatgpt
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/analyze.py
.venv/bin/python tests/verify_independent.py
.venv/bin/python src/compare_prior.py
```

`compare_prior.py` hem eski komşu klasör düzenini hem depodaki `chatgpt/` düzenini algılar. Bağımsız analiz kodu ve dondurulmuş sonuçlar değiştirilmedi. `check_deliverables.py` yerel araçlar (FFmpeg ve pdfinfo) gerektirir; özgün komşu proje bulunmadığında onun dosya koruma kontrollerini atlar. Diğer kontrolleri çalıştırır.
