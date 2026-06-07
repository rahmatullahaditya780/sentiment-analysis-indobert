# Fase 8 — Dashboard Development (Checkpoint 8)

## Tujuan
Membangun dashboard interaktif berbasis Streamlit yang mengintegrasikan semua komponen sistem analisis sentimen dan rekomendasi pemasaran.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-8.1 | Dashboard harus menampilkan hasil klasifikasi sentimen beserta confidence score. |
| FR-8.2 | Dashboard harus menyediakan Item Selector (dropdown produk dari Open Platform API `get_item_list`) sebagai metode input utama. |
| FR-8.3 | Dashboard harus mendukung upload file CSV untuk analisis batch. |
| FR-8.4 | Dashboard harus menampilkan visualisasi distribusi sentimen (pie chart dan bar chart). |
| FR-8.5 | Dashboard harus menampilkan rekomendasi strategi pemasaran berbasis rule-based mapping (5 kondisi). |
| FR-8.6 | Dashboard harus menampilkan word cloud untuk kata dominan per kategori sentimen. |
| FR-8.7 | Dashboard harus menampilkan trend sentimen dari waktu ke waktu jika data memiliki kolom `date_review`. |
| FR-8.8 | Dashboard harus menyediakan Settings & Configuration (filter kategori produk, rentang waktu, confidence threshold). |
| FR-8.9 | Dashboard harus menampilkan indikator status pengambilan data API yang informatif (berjalan/berhasil/gagal + fallback ke CSV). |
| FR-8.10 | Dashboard harus memvalidasi keberadaan dan masa berlaku access token, melakukan refresh otomatis (token berlaku 4 jam), dan menampilkan pesan informatif jika autentikasi gagal. |
| FR-8.11 | Dashboard harus menampilkan progress bar dan jumlah ulasan yang berhasil dikumpulkan selama pagination API. |
| FR-8.12 | Dashboard harus membatasi jumlah ulasan yang diambil maksimal 1.000 ulasan terbaru per produk. |
| FR-8.13 | Dashboard harus menghormati rate limit Shopee Open Platform API dan menangani error dengan retry + jeda antar request. |

## Dashboard Modules

### Module 1 — Input Interface
| Komponen | Deskripsi |
|---|---|
| Product Selector | Dropdown berisi daftar produk toko OmorfoShop dari `get_item_list` (Open Platform API) |
| Fetch Button | Tombol "Ambil Ulasan" untuk memicu `get_rating` setelah produk dipilih |
| Progress Bar & Counter | Indikator progres real-time (contoh: 450/1000 ulasan) |
| Preview Table | Tampilkan 5 baris pertama ulasan sebelum analisis untuk verifikasi |
| CSV Upload | Upload file CSV berisi multiple ulasan untuk analisis batch |
| Analyze Button | Tombol untuk memicu proses analisis sentimen |

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

### Module 6 — Shopee Open Platform Connector
| Komponen | Deskripsi & Spesifikasi |
|---|---|
| OAuth2 Authenticator | Autentikasi OAuth2 ke Open Platform, auto-refresh token (berlaku 4 jam), simpan di `st.session_state` |
| API Client | `get_item_list` (daftar produk) + `get_rating` (ulasan) via REST v2.0 |
| Pagination Handler | Loop otomatis `get_rating` (offset + page_size maks 50 per request, maks 20 iterasi, hingga 1.000 ulasan atau `has_next_page=false`) |
| Rate & Quota Manager | Jeda antar request + retry (exponential backoff) jika menerima error/limit API |
| Data Normalizer | Konversi JSON `get_rating` (`comment`, `rating_star`, `ctime`) ke DataFrame (`review_text`, `rating`, `date_review`) |
| Error Handler | Tangkap error API (token expired, signature error, rate limit, timeout) — tampilkan pesan informatif + panduan fallback ke CSV |

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
- [ ] Module 1 — Input Interface berjalan (Product Selector + CSV Upload).
- [ ] Module 2 — Sentiment Analysis Results berjalan (pie, bar, trend chart).
- [ ] Module 3 — Marketing Recommendation Panel berjalan (5 kondisi pemasaran).
- [ ] Module 4 — Visualization berjalan (word cloud per kelas sentimen).
- [ ] Module 5 — Settings & Configuration berjalan (filter & threshold).
- [ ] Module 6 — Open Platform Connector berjalan (OAuth2, `get_item_list`, `get_rating`, pagination).
- [ ] Auto token refresh, rate/quota handling, dan error handling terimplementasi.
- [ ] Pengambilan ulasan via `get_rating` berhasil untuk produk terpilih (maks. 1.000 ulasan).
- [ ] Model loading menggunakan `st.session_state` (performa optimal).
- [ ] Fallback ke input CSV berjalan jika API tidak tersedia.

## Implementasi Kode

- `src/dashboard/input_module.py` — Module 1 (product selector, CSV upload)
- `src/dashboard/results_module.py` — Module 2 (sentiment results & charts)
- `src/dashboard/recommendation_module.py` — Module 3 (marketing panel)
- `src/dashboard/visualization_module.py` — Module 4 (word cloud, distribution)
- `src/dashboard/settings_module.py` — Module 5 (filter & threshold)
- `src/dashboard/shopee_connector.py` — Module 6 (Open Platform API)
- `app.py` — Entry point Streamlit (integrasikan semua modul)

## Gate ke Fase Berikutnya

Lanjut ke Fase 9 hanya jika semua 6 modul dashboard berjalan stabil dan data tampil sesuai ekspektasi.
