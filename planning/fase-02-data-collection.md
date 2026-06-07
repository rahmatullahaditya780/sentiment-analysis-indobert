# Fase 2 — Data Collection & Data Management (Checkpoint 2)

## Tujuan
Mengumpulkan dan mengelola seluruh dataset yang digunakan dalam penelitian: dataset publik (training & evaluasi) dan dataset implementasi (OmorfoShop via Shopee Open Platform API).

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-2.1 | Sistem harus dapat membaca dataset dari SmSA (TSV), PRDECT-ID (CSV), dan Review Product Shopee (Kaggle CSV). |
| FR-2.2 | Sistem harus dapat mengambil ulasan OmorfoShop Official Store melalui Shopee Open Platform API (REST v2.0) menggunakan autentikasi OAuth2 dan endpoint `get_rating`. |
| FR-2.3 | Sistem harus dapat menggabungkan dataset SmSA dan E-Commerce Review menjadi unified dataset. |
| FR-2.4 | Sistem harus dapat melakukan validasi struktur dan harmonisasi label sentimen. |
| FR-2.5 | Sistem harus dapat mendeteksi dan menghapus data duplikat. |
| FR-2.6 | Sistem harus dapat melakukan stratified split (80% train / 10% validation / 10% test). |
| FR-2.7 | Sistem harus dapat mendeteksi class imbalance dan menerapkan strategi penanganan jika selisih > 15%. |
| FR-2.8 | Sistem harus dapat menyimpan seluruh dataset hasil cleaning dalam format CSV. |

## Dataset Training & Evaluasi (Dataset Publik)

| Dataset | Sumber | Jumlah Aktual | Label | Format |
|---|---|---|---|---|
| SmSA (IndoNLU) | github.com/IndoNLP/indonlu | 12.679 ulasan | Positif / Negatif / Netral | TSV `[text, label]` |
| PRDECT-ID (snapshot) | data.mendeley.com/datasets/574v66hf2v | 5.283 ulasan | Positif / Negatif | CSV `[text, label]` |
| Review Product Shopee | Kaggle (mdhimaspamungkas) | 2.646 ulasan | Positif / Negatif / Netral (dari rating) | CSV `[username, rating, comment]` |
| **Total Unified Dataset** | — | **20.608 ulasan** | 3 kelas seragam | CSV `[text, label, source]` |

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

### PRDECT-ID (snapshot)
| Atribut | Tipe | Keterangan |
|---|---|---|
| text | String | Teks ulasan produk |
| label | String | Sentimen: positive / negative (tidak ada neutral) |

### Review Product Shopee (Kaggle, mdhimaspamungkas)
| Atribut | Tipe | Keterangan |
|---|---|---|
| username | String | Nama pengguna pengulas (tidak dipakai) |
| rating | Integer | Rating bintang 1–5 → dipetakan ke label (1–2 negative, 3 neutral, 4–5 positive) |
| comment | String | Teks ulasan; baris dengan comment kosong (316) di-drop saat loading |

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

| Subset | Proporsi | Jumlah Aktual |
|---|---|---|
| Training Set | 80% | 16.485 ulasan |
| Validation Set | 10% | 2.059 ulasan |
| Testing Set | 10% | 2.064 ulasan |

## Proses Pengerjaan

1. **Import Dataset Publik** — Unduh SmSA dari IndoNLU GitHub (TSV), PRDECT-ID (snapshot CSV), & Review Product Shopee dari Kaggle (CSV).
2. **Verifikasi Manual** — Periksa 5–10% data acak untuk memastikan konsistensi label.
3. **Harmonisasi Label** — Seragamkan: `'positive'/'1'` → Positif, `'negative'/'-1'` → Negatif, `'neutral'/'0'` → Netral.
4. **Deduplication** — Hapus data duplikat untuk mencegah data leakage.
5. **Merge Dataset** — Gabungkan SmSA, PRDECT-ID, dan Kaggle Shopee menjadi satu file CSV unified.
6. **Stratified Split** — Bagi dataset 80/10/10 menggunakan `stratified_train_test_split`.
7. **Cek Class Imbalance** — Hitung distribusi, terapkan strategi jika selisih > 15%.
8. **Pengambilan Ulasan OmorfoShop via Open Platform API** — Autentikasi OAuth2, `get_item_list` → `get_rating` (pagination, maks 1.200 ulasan).
9. **Export Dataset Implementasi** — Simpan dataset OmorfoShop sebagai CSV terpisah di `data/implementation/`.

## Deliverables Checkpoint 2

> Keputusan 2026-06-07: dataset training = **gabung 3 sumber** (SmSA + PRDECT-ID + Kaggle Shopee).
> Dataset Kaggle rizqinugroho (tidak tersedia lagi) **diganti** dengan Review Product Shopee (mdhimaspamungkas) → sudah terintegrasi.
> Shopee Open Platform API kredensial **sedang proses daftar** → modul dibangun, tes live menyusul, sementara fallback CSV.

- [x] Dataset publik berhasil diunduh dan diverifikasi — SmSA ✔, PRDECT-ID ✔ (snapshot), Kaggle Shopee ✔ (Review Product Shopee, 2.646 baris terpakai).
- [x] Label sentimen harmonisasi selesai (`src/utils/label_harmonizer.py`; SmSA 0/1/2, PRDECT string, Kaggle rating 1–5).
- [x] Dataset bebas duplikat (deduplication berbasis teks ternormalisasi).
- [x] Unified dataset tersimpan di `data/processed/unified_corpus.csv` (**20.608 baris**: SmSA 12.679 + PRDECT-ID 5.283 + Kaggle Shopee 2.646).
- [x] Stratified split 80/10/10 selesai → `train.csv` (16.485), `validation.csv` (2.059), `test.csv` (2.064).
- [x] Strategi class imbalance **terdokumentasi** (`outputs/reports/phase2_split_stats.json`; spread 51.9%, `needs_handling=true`, perlu `class_weight`). Implementasi di Fase 4.
- [x] `data/raw/source_manifest.yaml` diperbarui dengan metadata semua sumber.
- [DEFERRED] Dataset OmorfoShop via Open Platform API (±1.200 ulasan) — **PENDING kredensial** (fallback CSV: `data/implementation/omorfo_reviews_TEMPLATE.csv`). **Bukan dependensi Fase 3** (data implementasi, dipakai mulai Fase 6). Dikejar paralel.
- [DEFERRED] Dataset OmorfoShop tersimpan di `data/implementation/` format CSV — menyusul setelah kredensial keluar.
- [~] Modul `src/shopee_api/` dibangun: OAuth2 (`auth.py`), `get_item_list`/`get_rating`+pagination (`client.py`), normalizer (`normalizer.py`). **Tes live menyusul saat kredensial keluar.**

### Catatan eksekusi Fase 2 (2026-06-07)
- Korpus lama (`phase2_sentiment_corpus*.csv`) **ditinggalkan & dihapus**: builder hilang (file 0 byte) dan label SmSA terbalik (review positif ter-label `negative`). Dihapus dari git + disk 2026-06-07.
- Sisa scraping lama (`data/raw/shopee/chrome_profile_pw/`, `shopee_state.json`, dll.) masih ada di disk — perlu dihapus manual (sudah di-gitignore).
- **Risiko (dibawa ke Fase 3/4):** kelas `neutral` hanya ~7.2% (1.489 dari 20.608; mayoritas dari SmSA, PRDECT-ID tak punya neutral, Kaggle Shopee hanya +143). Spread > 15% → **wajib `class_weight`** saat training + F1 macro sebagai metrik utama; pertimbangkan augmentasi back-translation untuk kelas neutral.

### Status gate Fase 2
**LULUS untuk lanjut ke Fase 3.** Seluruh deliverable korpus training (input Fase 3) selesai. Item `OmorfoShop via Shopee API` di-*defer* sebagai pekerjaan paralel karena (a) terblokir kredensial eksternal dan (b) bukan dependensi preprocessing — data implementasi baru dipakai di Fase 6.

## Implementasi Kode

- `src/shopee_api/` — Shopee Open Platform client (OAuth2, HMAC-SHA256, pagination)
- `src/utils/` — Utilitas harmonisasi label, deduplication, stratified split
- Output: `data/processed/train.csv`, `data/processed/validation.csv`, `data/processed/test.csv`, `data/implementation/omorfo_reviews.csv`

## Gate ke Fase Berikutnya

Lanjut ke Fase 3 hanya jika semua checklist di atas selesai dan tervalidasi.
