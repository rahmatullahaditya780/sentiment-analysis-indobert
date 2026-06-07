# Fase 2 — Data Collection & Data Management (Checkpoint 2)

## Tujuan
Mengumpulkan dan mengelola seluruh dataset yang digunakan dalam penelitian: dataset publik (training & evaluasi) dan dataset implementasi (OmorfoShop via Shopee Open Platform API).

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-2.1 | Sistem harus dapat membaca dataset CSV dari SmSA dan Indonesian E-Commerce Review. |
| FR-2.2 | Sistem harus dapat mengambil ulasan OmorfoShop Official Store melalui Shopee Open Platform API (REST v2.0) menggunakan autentikasi OAuth2 dan endpoint `get_rating`. |
| FR-2.3 | Sistem harus dapat menggabungkan dataset SmSA dan E-Commerce Review menjadi unified dataset. |
| FR-2.4 | Sistem harus dapat melakukan validasi struktur dan harmonisasi label sentimen. |
| FR-2.5 | Sistem harus dapat mendeteksi dan menghapus data duplikat. |
| FR-2.6 | Sistem harus dapat melakukan stratified split (80% train / 10% validation / 10% test). |
| FR-2.7 | Sistem harus dapat mendeteksi class imbalance dan menerapkan strategi penanganan jika selisih > 15%. |
| FR-2.8 | Sistem harus dapat menyimpan seluruh dataset hasil cleaning dalam format CSV. |

## Dataset Training & Evaluasi (Dataset Publik)

| Dataset | Sumber | Jumlah Estimasi | Label | Format |
|---|---|---|---|---|
| SmSA (IndoNLU) | github.com/IndoNLP/indonlu | 4.000–5.000 ulasan | Positif / Negatif / Netral | TSV `[text, label]` |
| Indonesian E-Commerce Review | Kaggle (rizqinugroho) | 5.000–7.000 ulasan | Positif / Negatif / Netral (dari rating) | CSV `[review_text, rating, sentiment_label]` |
| **Total Unified Dataset** | — | **9.000–12.000 ulasan** | 3 kelas seragam | CSV `[review_text, sentiment_label]` |

## Dataset Implementasi (OmorfoShop)

| Atribut | Detail |
|---|---|
| Sumber | OmorfoShop Official Store — Shopee |
| Jumlah | ±1.200 ulasan produk |
| Periode Pengumpulan | Juni 2025 – Juni 2026 |
| Metode | Shopee Open Platform API (OAuth2, endpoint `get_rating`) |
| Tujuan | Implementasi model & penyusunan rekomendasi pemasaran (**BUKAN** untuk training) |
| Privasi | Identitas pelanggan tidak disimpan (data minimization) |

## Atribut Dataset per Sumber

### SmSA Dataset
| Atribut | Tipe | Keterangan |
|---|---|---|
| text | String | Teks ulasan/kalimat |
| label | String | Sentimen: positive / negative / neutral |

### Indonesian E-Commerce Review
| Atribut | Tipe | Keterangan |
|---|---|---|
| review_text | String | Teks ulasan produk |
| rating | Integer | Rating bintang 1–5 |
| sentiment_label | String | Label sentimen (dipetakan dari rating jika belum ada) |

### Dataset Implementasi OmorfoShop
| Atribut | Tipe | Keterangan |
|---|---|---|
| review_id | String | ID unik ulasan (dari Shopee) |
| review_text | String | Teks ulasan pelanggan |
| rating | Integer | Rating bintang 1–5 |
| product_name | String | Nama produk yang diulas |
| product_category | String | Kategori produk (misal: Pelembap, Serum Tubuh) |
| date_review | Date | Tanggal ulasan ditulis |

## Penanganan Class Imbalance

Wajib diimplementasi jika selisih distribusi kelas > 15%.

| Strategi | Kondisi | Implementasi |
|---|---|---|
| Stratified Sampling | Semua kondisi | `stratified_train_test_split` dari scikit-learn |
| Class Weight Adjustment | Selisih kelas > 15% | Parameter `class_weight` pada fine-tuning IndoBERT |
| F1 Macro sebagai Metrik Utama | Semua kondisi | Macro-average F1 agar sensitivitas semua kelas seimbang |
| Data Augmentation (opsional) | Selisih kelas > 25% | Back-translation atau paraphrase sederhana |

**Target Distribusi Dataset Training:**

| Kelas | Target |
|---|---|
| Positif | 35–40% |
| Negatif | 30–35% |
| Netral | 25–30% |

## Stratified Split

| Subset | Proporsi | Estimasi Jumlah |
|---|---|---|
| Training Set | 80% | 7.200–9.600 ulasan |
| Validation Set | 10% | 900–1.200 ulasan |
| Testing Set | 10% | 900–1.200 ulasan |

## Proses Pengerjaan

1. **Import Dataset Publik** — Unduh SmSA dari IndoNLU GitHub & Indonesian E-Commerce Review dari Kaggle (CSV).
2. **Verifikasi Manual** — Periksa 5–10% data acak untuk memastikan konsistensi label.
3. **Harmonisasi Label** — Seragamkan: `'positive'/'1'` → Positif, `'negative'/'-1'` → Negatif, `'neutral'/'0'` → Netral.
4. **Deduplication** — Hapus data duplikat untuk mencegah data leakage.
5. **Merge Dataset** — Gabungkan SmSA dan Kaggle menjadi satu file CSV unified.
6. **Stratified Split** — Bagi dataset 80/10/10 menggunakan `stratified_train_test_split`.
7. **Cek Class Imbalance** — Hitung distribusi, terapkan strategi jika selisih > 15%.
8. **Pengambilan Ulasan OmorfoShop via Open Platform API** — Autentikasi OAuth2, `get_item_list` → `get_rating` (pagination, maks 1.200 ulasan).
9. **Export Dataset Implementasi** — Simpan dataset OmorfoShop sebagai CSV terpisah di `data/implementation/`.

## Deliverables Checkpoint 2

> Keputusan 2026-06-07: dataset training = **gabung 3 sumber** (SmSA + PRDECT-ID + Kaggle).
> Shopee API kredensial **sedang proses daftar** → modul dibangun, tes live menyusul, sementara fallback CSV.

- [~] Dataset publik berhasil diunduh dan diverifikasi — SmSA ✔, PRDECT-ID ✔ (snapshot). **Kaggle rizqinugroho PENDING download.**
- [x] Label sentimen harmonisasi selesai (`src/utils/label_harmonizer.py`; SmSA 0/1/2, PRDECT string, Kaggle rating).
- [x] Dataset bebas duplikat (deduplication berbasis teks ternormalisasi; 198 duplikat dibuang).
- [x] Unified dataset tersimpan di `data/processed/unified_corpus.csv` (**17.962 baris**; akan +Kaggle).
- [x] Stratified split 80/10/10 selesai → `train.csv` (14.369), `validation.csv` (1.795), `test.csv` (1.798).
- [~] Strategi class imbalance **terdokumentasi** (`outputs/reports/phase2_split_stats.json`; spread 47.3%, perlu `class_weight`). Implementasi di Fase 4.
- [ ] Dataset OmorfoShop berhasil diambil via Open Platform API (±1.200 ulasan) — **PENDING kredensial** (fallback CSV: `data/implementation/omorfo_reviews_TEMPLATE.csv`).
- [ ] Dataset OmorfoShop tersimpan di `data/implementation/` format CSV — **PENDING**.
- [x] `data/raw/source_manifest.yaml` diperbarui dengan metadata semua sumber.
- [~] Modul `src/shopee_api/` dibangun: OAuth2 (`auth.py`), `get_item_list`/`get_rating`+pagination (`client.py`), normalizer (`normalizer.py`). **Tes live menyusul saat kredensial keluar.**

### Catatan eksekusi Fase 2 (2026-06-07)
- Korpus lama (`phase2_sentiment_corpus*.csv`) **ditinggalkan**: builder hilang (file 0 byte) dan label SmSA terbalik (review positif ter-label `negative`). File lama belum dihapus dari disk — perlu dihapus manual.
- Sisa scraping lama (`data/raw/shopee/chrome_profile_pw/`, `shopee_state.json`, dll.) masih ada di disk — perlu dihapus manual (sudah di-gitignore).
- **Risiko:** kelas `neutral` hanya ~7.5% (hanya dari SmSA; PRDECT-ID tak punya neutral). Menambah Kaggle (rating=3) diharapkan menaikkan proporsi neutral.

## Implementasi Kode

- `src/shopee_api/` — Shopee Open Platform client (OAuth2, HMAC-SHA256, pagination)
- `src/utils/` — Utilitas harmonisasi label, deduplication, stratified split
- Output: `data/processed/train.csv`, `data/processed/validation.csv`, `data/processed/test.csv`, `data/implementation/omorfo_reviews.csv`

## Gate ke Fase Berikutnya

Lanjut ke Fase 3 hanya jika semua checklist di atas selesai dan tervalidasi.
