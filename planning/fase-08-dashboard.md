# Fase 8 — Dashboard Development (Checkpoint 8)

## Tujuan
Membangun dashboard interaktif berbasis Streamlit yang mengintegrasikan semua komponen sistem analisis sentimen dan rekomendasi pemasaran.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-8.1 | Dashboard harus menampilkan hasil klasifikasi sentimen beserta confidence score. |
| FR-8.2 | Dashboard harus menyediakan **input berlapis** sebagai metode utama: (a) Upload CSV, (b) Input **URL produk Shopee** untuk pengambilan otomatis via **browser ber-login (mode lokal/desktop)**. |
| FR-8.3 | Dashboard harus mendukung upload file CSV untuk analisis batch. |
| FR-8.4 | Dashboard harus menampilkan visualisasi distribusi sentimen (pie chart dan bar chart). |
| FR-8.5 | Dashboard harus menampilkan rekomendasi strategi pemasaran berbasis rule-based mapping (5 kondisi). |
| FR-8.6 | Dashboard harus menampilkan word cloud untuk kata dominan per kategori sentimen. |
| FR-8.7 | Dashboard harus menampilkan trend sentimen dari waktu ke waktu jika data memiliki kolom `date_review`. |
| FR-8.8 | Dashboard harus menyediakan Settings & Configuration (filter kategori produk, rentang waktu, confidence threshold). |
| FR-8.9 | Dashboard harus menampilkan indikator status **scraping/pengambilan** yang informatif (berjalan / berhasil + jumlah ulasan / gagal + pesan error + panduan fallback ke jalur lain). |
| FR-8.10 | Dashboard harus **memvalidasi format URL produk Shopee** sebelum memulai scraping dan menampilkan pesan error informatif jika URL tidak valid. |
| FR-8.11 | Dashboard harus menampilkan progress bar dan jumlah ulasan yang berhasil dikumpulkan selama scraping berlangsung. |
| FR-8.12 | Dashboard harus membatasi jumlah ulasan yang diambil maksimal ±1.200 ulasan per produk. |
| FR-8.13 | Dashboard harus menerapkan jeda antar-aksi (rate limiting) saat scraping untuk menghindari pemblokiran Shopee. |
| FR-8.14 | Dashboard harus **mendeteksi lingkungan** (cloud vs lokal) dan menonaktifkan/menyembunyikan jalur URL Auto-Fetch saat berjalan di cloud (tanpa browser/display), mengarahkan pengguna ke CSV Upload. |

## Dashboard Modules

### Module 1 — Input Interface (berlapis, 2 tab)
| Tab | Komponen | Deskripsi |
|---|---|---|
| **CSV Upload** | File uploader + Analyze | Upload CSV ulasan untuk analisis batch (jalan di cloud & lokal) |
| **URL Auto-Fetch** *(badge: Lokal saja)* | URL input, Fetch button, Progress bar & counter, Preview 5 baris | Pengambilan otomatis via **endpoint JSON internal** Shopee (`fetch('/api/v2/item/get_ratings')`) dalam sesi browser ber-login (`scrape_omorfo_api.py`, dijalankan via subprocess); nonaktif saat di cloud (FR-8.14) |

### Module 2 — Sentiment Analysis Results
| Komponen | Deskripsi |
|---|---|
| Sentiment Label | Label prediksi: Positif / Negatif / Netral |
| Confidence Score | Persentase keyakinan model |
| Pie Chart | Distribusi persentase ketiga kelas sentimen |
| Bar Chart | Perbandingan jumlah ulasan per kelas |
| Trend Chart | Grafik tren sentimen dari waktu ke waktu (jika ada `date_review`) |

### Module 3 — Marketing Recommendation Panel
| Komponen | Deskripsi |
|---|---|
| Kondisi Pemasaran | Kondisi saat ini (Excellent/Good/Moderate/Poor/Mixed) beserta kriteria yang terpenuhi |
| Rekomendasi Strategi | Daftar strategi pemasaran spesifik berdasarkan rule-based mapping |
| Business Insight | Interpretasi distribusi sentimen dalam bahasa yang mudah dipahami praktisi |

### Module 4 — Visualization
| Komponen | Deskripsi |
|---|---|
| Word Cloud Positif | Kata-kata dominan dari ulasan bersentimen positif |
| Word Cloud Negatif | Kata-kata dominan dari ulasan bersentimen negatif |
| Word Cloud Netral | Kata-kata dominan dari ulasan bersentimen netral |
| Distribution Chart | Grafik distribusi sentimen per kategori produk |

### Module 5 — Settings & Configuration
| Fitur | Deskripsi |
|---|---|
| Filter Kategori Produk | Pilih kategori produk tertentu (misal: Pelembap, Serum Tubuh) untuk analisis terfokus |
| Filter Rentang Waktu | Pilih rentang tanggal untuk distribusi sentimen pada periode tertentu |
| Threshold Adjustment | Sesuaikan batas confidence threshold model |

### Module 6 — Shopee Review Collector (Berlapis)
| Komponen | Deskripsi & Spesifikasi |
|---|---|
| Tiered Router | Memilih jalur (CSV / URL Auto-Fetch) sesuai pilihan pengguna & lingkungan (cloud vs lokal) |
| JSON Fetch Engine | In-browser `fetch('/api/v2/item/get_ratings')` (same-origin, lolos anti-bot DataDome) dari sesi login persisten, paginasi `offset`, dedup `cmtid` — dijalankan via **subprocess** (`fetch_worker.py`) agar bebas konflik asyncio Streamlit; **lokal saja** (reuse `src/scraping/scrape_omorfo_api.py`) |
| Progress Streaming | Worker subprocess memancarkan progress **NDJSON** ke stdout → diteruskan ke `st.progress` + counter (FR-8.11); cap ≤1.200 (FR-8.12) & jeda rate-limit (FR-8.13) via argumen worker |
| Data Normalizer | Output seragam `[review_id, review_text, rating, product_name, product_category, date_review]` |
| Error/Fallback Handler | Deteksi login-wall / 0-ulasan / timeout → pesan informatif + arahkan ke jalur CSV Upload |

> **Catatan deployment (hasil riset Streamlit Cloud free):** RAM 1 GB/app, Chromium hanya headless, IP datacenter kena anti-bot, filesystem ephemeral → **jalur URL Auto-Fetch hanya aktif di app lokal/desktop**. Versi cloud mengandalkan CSV Upload (data dikumpulkan lokal lebih dulu via URL Auto-Fetch). Detail di `planning/trd-revisi-pengambilan-data-implementasi.md` §C.
>
> **Catatan metode (selaras CLAUDE.md & TRD revisi):** jalur URL Auto-Fetch memakai **endpoint JSON internal** Shopee dari dalam sesi browser ber-login (`scrape_omorfo_api.py`), **bukan** render-DOM (`scrape_omorfo_reviews.py`, diblokir anti-bot → fallback) maupun Shopee Open Platform API. Lihat catatan revisi 2026-06-10.

## UI Requirements

| Requirement | Target |
|---|---|
| Responsive UI | Desktop-friendly (1280px+), Streamlit default responsif |
| Loading Time | < 5 detik (gunakan `st.session_state` untuk cache model) |
| Model Loading | `st.session_state` agar model tidak di-load ulang setiap interaksi |
| Real-time Update | Hasil analisis diperbarui setelah tombol ditekan |
| Navigasi | **Multipage** `st.navigation` — sidebar bergrup (Menu / Hasil Analisis / Lainnya) |
| Tema | `.streamlit/config.toml` (palet prototipe, primary `#FF4B4B`) |

### Struktur Multipage (selaras `Design/Sentara_Prototype.html`)

UI/UX mengikuti prototipe pada fidelity **sedang** (struktur + palet + komponen;
bukan pixel-perfect — navbar/avatar & shadow persis dihindari karena butuh CSS
injeksi rapuh). Navigasi 8 halaman:

| Grup | Halaman | Isi |
|---|---|---|
| Menu | Dashboard | Stat cards + donut + tren + word cloud gabungan |
| Menu | Input & Pengambilan Data | 2 tab input + kartu preprocessing & metrik model |
| Hasil Analisis | Detail Ulasan | Segmented filter + tabel (ProgressColumn skor + bintang) |
| Hasil Analisis | Visualisasi & Word Cloud | Word cloud per kelas + distribusi per kategori |
| Hasil Analisis | Rekomendasi Strategi | Panel 5 kondisi + tabel acuan threshold |
| Lainnya | Pengaturan | Filter kategori/tanggal/confidence (berlaku global) |
| Lainnya | Ekspor Laporan | Unduh CSV berlabel (**PDF/PNG → Fase 10**) |
| Lainnya | Tentang & Bantuan | Profil sistem, cara pakai, info skripsi |

Filter di **Pengaturan** berlaku ke seluruh halaman hasil **tanpa inferensi
ulang** (`ui_common.resolve_view` → `recompute_from_predictions`). Penyelarasan
ke keputusan final: **tanpa jalur Import Ekstensi** (2 tier), label metode =
"endpoint JSON internal", angka nyata (F1 0,9031; 3.739 ulasan).

## Deliverables Checkpoint 8

- [x] Dashboard dapat dijalankan lokal dengan `streamlit run app.py`. *(boot headless terverifikasi: health HTTP 200)*
- [x] Module 1 — Input Interface berlapis berjalan (CSV Upload + URL Auto-Fetch).
- [x] Module 2 — Sentiment Analysis Results berjalan (pie, bar, trend chart).
- [x] Module 3 — Marketing Recommendation Panel berjalan (5 kondisi pemasaran).
- [x] Module 4 — Visualization berjalan (word cloud per kelas sentimen).
- [x] Module 5 — Settings & Configuration berjalan (filter & threshold).
- [x] Module 6 — Shopee Review Collector berlapis berjalan (router CSV/URL Auto-Fetch).
- [~] JSON Fetch Engine: subprocess + progress NDJSON + cap ≤1.200 + dedup **terimplementasi & teruji plumbing-nya**; *fetch nyata ke Shopee menunggu **verifikasi manual** di desktop ber-sesi-login (di luar cakupan test otomatis).*
- [x] Deteksi lingkungan (FR-8.14): jalur URL Auto-Fetch nonaktif otomatis di cloud, fallback ke CSV Upload.
- [x] Rate limiting (`--delay`) + error/fallback handling (login-wall/0-ulasan/timeout/jaringan/ID) terimplementasi (`classify_fetch_error`).
- [x] Model loading menggunakan `st.session_state` (performa optimal).

> **Status implementasi (build order langkah 1–9):** seluruh modul kode + 80 unit
> test lulus, lint/format bersih, boot dashboard hijau. Satu-satunya item yang
> belum tertutup penuh adalah **fetch nyata ke Shopee** yang memerlukan sesi
> browser ber-login — perlu dijalankan manual oleh pengguna di desktop sebelum
> gate Fase 8 ditutup resmi.

## Implementasi Kode

- `src/dashboard/input_module.py` — Module 1 (input berlapis: CSV upload, URL auto-fetch)
- `src/dashboard/results_module.py` — Module 2 (sentiment results & charts)
- `src/dashboard/recommendation_module.py` — Module 3 (marketing panel)
- `src/dashboard/visualization_module.py` — Module 4 (word cloud, distribution)
- `src/dashboard/settings_module.py` — Module 5 (filter & threshold)
- `src/dashboard/shopee_connector.py` — Module 6 (tiered router: `validate_shopee_url`, `detect_environment`, `auto_fetch_reviews`; reuse `src/scraping/scrape_omorfo_api.py` (JSON))
- `src/dashboard/fetch_worker.py` — entrypoint subprocess JSON fetch (emit progress NDJSON → CSV); mengisolasi `sync_playwright` dari proses Streamlit
- `src/dashboard/analysis_pipeline.py` — glue one-click (`predict_batch → analyze_trend → classify → map_to_recommendation`), dipakai kedua jalur input; `recompute_from_predictions` (filter tanpa re-inferensi) + shortcut data pra-prediksi
- `src/dashboard/ui_common.py` — state lintas-halaman (`get_predictor`, `analyze_with_progress`, `resolve_view`)
- `src/dashboard/pages.py` — 8 fungsi halaman multipage (menyusun ulang komponen modul)
- `app.py` — Entry point Streamlit (`st.navigation` 8 halaman; cache `SentimentPredictor` di `st.session_state`)
- `.streamlit/config.toml` — tema (palet prototipe)

> **Catatan Ekspor:** halaman Ekspor saat ini hanya **unduh CSV berlabel**.
> Ekspor **PDF & PNG** dijadwalkan ke **Fase 10** (Deployment & Dokumentasi),
> bukan bagian FR-8.x.

## Peningkatan Pasca-Gate (Fase 8.5, 2026-06-10)

Tiga paket peningkatan di atas spek awal (semua modul FR-8.x sudah lengkap
sebelumnya); 154 unit test hijau, boot HTTP 200:

- **WP0 Fondasi:** palet sentimen tunggal (`ui_common.SENTIMENT_HEX` re-export
  `results_module.SENTIMENT_COLORS`, nilai = prototipe); `model_info.py` baca
  F1/CV dari `outputs/reports/*.json` (hapus angka hardcoded);
  `condition_criteria()` digenerate dari `THRESHOLDS` Fase 7 (hapus duplikat
  teks ambang); word cloud & frekuensi di-cache `st.cache_data` (kunci tuple
  string, `max_entries=16`).
- **WP1 Polish UX:** pencarian kata + paginasi 25/50/100 di Detail Ulasan;
  empty state beralasan (`column_state` absen/kosong/ok) untuk chart
  kategori/tren/word cloud; badge filter global di `resolve_view`; expander
  Troubleshooting di Tentang; tooltip jeda & maks ulasan (FR-8.12).
- **Multi-URL auto-fetch berkelanjutan:** tab URL mendukung ≤5 baris
  URL+kategori; anggaran "Maks total ulasan" dibagi rata antar produk
  (`split_quota`, mis. 1.200 utk 2 URL → 600+600); hasil tiap produk
  tersimpan di sesi (`fetch_cache` per `shopid.itemid`) sehingga menambah
  link baru **tidak mengulang fetch** produk lama (`plan_fetches` menandai
  skip utk produk tersimpan/duplikat; kuota link baru tetap total÷semua
  link); panel "Produk tersimpan sesi ini" dengan hapus per-produk;
  gabungan di-dedup `review_id` (`combine_fetch_results`).
- **WP2 Module 7 — Insight Analitik (`insights_module.py`):** deteksi
  ketidaksesuaian rating↔sentimen (bintang ≥4 + teks negatif / bintang ≤2 +
  teks positif — bukti nilai tambah IndoBERT di atas rating numerik, tampil di
  Dashboard + toggle di Detail); kata kunci teratas per kelas + drill-down
  ulasan per kata (Visualisasi); perbandingan kondisi pemasaran per produk via
  rule engine Fase 7 (Visualisasi + Rekomendasi); bukti ulasan representatif
  ber-confidence tertinggi (Rekomendasi).

## Gate ke Fase Berikutnya

Lanjut ke Fase 9 hanya jika semua 6 modul dashboard berjalan stabil dan data tampil sesuai ekspektasi. Status: kode + 100 unit test lulus (termasuk 16 test render halaman multipage); tersisa **verifikasi manual fetch nyata Shopee**.
