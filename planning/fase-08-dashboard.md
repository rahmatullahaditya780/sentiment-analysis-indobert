# Fase 8 — Dashboard Development (Checkpoint 8)

## Tujuan
Membangun dashboard interaktif berbasis Streamlit yang mengintegrasikan semua komponen sistem analisis sentimen dan rekomendasi pemasaran.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-8.1 | Dashboard harus menampilkan hasil klasifikasi sentimen beserta confidence score. |
| FR-8.2 | Dashboard harus menyediakan **input berlapis** sebagai metode utama: (a) Upload CSV, (b) Import CSV hasil ekstensi browser, (c) Input **URL produk Shopee** untuk pengambilan otomatis via **browser ber-login (mode lokal/desktop)**. |
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
| FR-8.14 | Dashboard harus **mendeteksi lingkungan** (cloud vs lokal) dan menonaktifkan/menyembunyikan jalur URL Auto-Fetch saat berjalan di cloud (tanpa browser/display), mengarahkan pengguna ke CSV/ekstensi. |

## Dashboard Modules

### Module 1 — Input Interface (berlapis, 3 tab)
| Tab | Komponen | Deskripsi |
|---|---|---|
| **CSV Upload** | File uploader + Analyze | Upload CSV ulasan untuk analisis batch (jalan di cloud & lokal) |
| **Extension Import** | File uploader + konverter | Upload CSV hasil ekstensi browser → dipetakan ke skema implementasi (jalan di cloud & lokal) |
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
| Tiered Router | Memilih jalur (CSV / Ekstensi / URL Auto-Fetch) sesuai pilihan pengguna & lingkungan (cloud vs lokal) |
| JSON Fetch Engine | In-browser `fetch('/api/v2/item/get_ratings')` (same-origin, lolos anti-bot DataDome) dari sesi login persisten, paginasi `offset`, dedup `cmtid` — dijalankan via **subprocess** (`fetch_worker.py`) agar bebas konflik asyncio Streamlit; **lokal saja** (reuse `src/scraping/scrape_omorfo_api.py`) |
| Extension Converter | Konversi CSV ekstensi browser → skema implementasi (reuse `src/utils/convert_extension_csv.py`) |
| Progress Streaming | Worker subprocess memancarkan progress **NDJSON** ke stdout → diteruskan ke `st.progress` + counter (FR-8.11); cap ≤1.200 (FR-8.12) & jeda rate-limit (FR-8.13) via argumen worker |
| Data Normalizer | Output seragam `[review_id, review_text, rating, product_name, product_category, date_review]` |
| Error/Fallback Handler | Deteksi login-wall / 0-ulasan / timeout → pesan informatif + arahkan ke jalur lain (CSV/ekstensi) |

> **Catatan deployment (hasil riset Streamlit Cloud free):** RAM 1 GB/app, Chromium hanya headless, IP datacenter kena anti-bot, filesystem ephemeral → **jalur URL Auto-Fetch hanya aktif di app lokal/desktop**. Versi cloud mengandalkan CSV + ekstensi. Detail di `planning/trd-revisi-pengambilan-data-implementasi.md` §C.
>
> **Catatan metode (selaras CLAUDE.md & TRD revisi):** jalur URL Auto-Fetch memakai **endpoint JSON internal** Shopee dari dalam sesi browser ber-login (`scrape_omorfo_api.py`), **bukan** render-DOM (`scrape_omorfo_reviews.py`, diblokir anti-bot → fallback) maupun Shopee Open Platform API. Lihat catatan revisi 2026-06-10.

## UI Requirements

| Requirement | Target |
|---|---|
| Responsive UI | Desktop-friendly (1280px+), Streamlit default responsif |
| Loading Time | < 5 detik (gunakan `st.session_state` untuk cache model) |
| Model Loading | `st.session_state` agar model tidak di-load ulang setiap interaksi |
| Real-time Update | Hasil analisis diperbarui setelah tombol ditekan |
| Navigasi | `st.sidebar` untuk navigasi antar module |

## Deliverables Checkpoint 8

- [ ] Dashboard dapat dijalankan lokal dengan `streamlit run app.py`.
- [ ] Module 1 — Input Interface berlapis berjalan (CSV Upload + Extension Import + URL Auto-Fetch).
- [ ] Module 2 — Sentiment Analysis Results berjalan (pie, bar, trend chart).
- [ ] Module 3 — Marketing Recommendation Panel berjalan (5 kondisi pemasaran).
- [ ] Module 4 — Visualization berjalan (word cloud per kelas sentimen).
- [ ] Module 5 — Settings & Configuration berjalan (filter & threshold).
- [ ] Module 6 — Shopee Review Collector berlapis berjalan (router CSV/Ekstensi/URL Auto-Fetch).
- [ ] JSON Fetch Engine: pengambilan via endpoint JSON internal dalam sesi browser ber-login berhasil di mode lokal (paginasi `offset` + dedup, maks ±1.200 ulasan), dijalankan via subprocess dengan progress NDJSON.
- [ ] Deteksi lingkungan (FR-8.14): jalur URL Auto-Fetch nonaktif otomatis di cloud, fallback ke CSV/ekstensi.
- [ ] Rate limiting + error/fallback handling (login-wall/0-ulasan/timeout) terimplementasi.
- [ ] Model loading menggunakan `st.session_state` (performa optimal).

## Implementasi Kode

- `src/dashboard/input_module.py` — Module 1 (input berlapis: CSV upload, extension import, URL auto-fetch)
- `src/dashboard/results_module.py` — Module 2 (sentiment results & charts)
- `src/dashboard/recommendation_module.py` — Module 3 (marketing panel)
- `src/dashboard/visualization_module.py` — Module 4 (word cloud, distribution)
- `src/dashboard/settings_module.py` — Module 5 (filter & threshold)
- `src/dashboard/shopee_connector.py` — Module 6 (tiered router: `validate_shopee_url`, `detect_environment`, `auto_fetch_reviews`; reuse `src/scraping/scrape_omorfo_api.py` (JSON) & `src/utils/convert_extension_csv.py`)
- `src/dashboard/fetch_worker.py` — entrypoint subprocess JSON fetch (emit progress NDJSON → CSV); mengisolasi `sync_playwright` dari proses Streamlit
- `src/dashboard/analysis_pipeline.py` — glue one-click (`predict_batch → analyze_trend → classify → map_to_recommendation`), dipakai ketiga jalur input
- `app.py` — Entry point Streamlit (integrasikan semua modul; cache `SentimentPredictor` di `st.session_state`)

## Gate ke Fase Berikutnya

Lanjut ke Fase 9 hanya jika semua 6 modul dashboard berjalan stabil dan data tampil sesuai ekspektasi.
