# ASA Data Quest 2026 — bağımsız ChatGPT çalışması

> GitHub yayını: [busahinku/asa_dataquest — chatgpt-analysis](https://github.com/busahinku/asa_dataquest/tree/chatgpt-analysis/chatgpt). Kurulum ve yayın kapsamı: [GITHUB_YAYINI.md](reports/GITHUB_YAYINI.md). Önceki raporlardaki yayın durumu denetim tarihine aittir.

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
cd chatgpt  # Klonlanan deponun kökünden
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/analyze.py
.venv/bin/python tests/verify_independent.py
```

Karşılaştırma, eski komşu `../asa_dataquest` klasörünü veya yayımlanan deponun üst klasörünü kullanır:

```sh
.venv/bin/python src/compare_prior.py
.venv/bin/python src/write_reports.py
```

Sunumun üretimi Codex'in yerel Artifact Tool çalışma ortamını kullanır. `src/build_slides.mjs` ve `src/build_video.py` kaynakları pakettedir; Python analizi bu özel Node kütüphanesine ihtiyaç duymaz. Grafik verileri `slides/chart_data.json` içinde de bulunur. Sunum PDF dışa aktarımı ve slayt renderları ayrıca kaydedilir. Yeniden sunum üretirken mevcut dosyanın üzerine yazmamak için `DECK_OUTPUT=yeni_sunum.pptx` ortam değişkeni kullanın. Video üretimi macOS `say`, FFmpeg ve Pillow gerektirir; analiz bunlara ihtiyaç duymaz. Son paket kontrolleri `results/deliverable_validation.json` içindedir.

## Sayıların anlamı

Başlangıç: 1 Ocak 2024. Ana hedef: 1 Ocak 2050. TFR sınıflaması: 2023. Ülke sayısı ülke ve bölgeleri kapsar. Raw nüfus ve katkı birimi bin kişi; tablolardaki `pct_base` alanları başlangıç nüfusunun yüzdesidir. 1950–2023 tahmin, 2024 sonrası projeksiyondur. Senaryo etkileri nedensel politika etkisi değildir.

Veri kaynağı UN WPP2024 ve yarışma supplement'i (CC BY 3.0 IGO). Arkadaşın önceki deposuna ve AI katkısına raporlarda atıf vardır. Bu klasör dışında dosya değiştirilmedi; dışarıya hiçbir teslim/push yapılmadı.
