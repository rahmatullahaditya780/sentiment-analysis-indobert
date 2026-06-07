# Catatan Revisi dan Saran Non-Fase

Gunakan file ini untuk menyimpan saran revisi, catatan tambahan, atau temuan yang tidak cocok dimasukkan ke daftar fase.

## Format Catatan
| Tanggal | Sumber | Fase Terkait | Kategori | Prioritas | Status | Catatan | Tindak Lanjut |
|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | Dosen/Penguji/Tim | Umum | Revisi | Tinggi/Sedang/Rendah | Open/Done | Isi catatan | Aksi yang harus dilakukan |

## Aturan Isi
- Satu baris untuk satu catatan.
- Jika catatan menyentuh lebih dari satu fase, isi kolom `Fase Terkait` dengan `Umum`.
- Jika catatan tidak membutuhkan aksi, tetap simpan agar jejak keputusan tidak hilang.

## Daftar Catatan

| Tanggal | Sumber | Fase Terkait | Kategori | Prioritas | Status | Catatan | Tindak Lanjut |
|---|---|---|---|---|---|---|---|
| 2026-06-07 | TRD v2 | Umum | Revisi Arsitektur | Tinggi | Open | Metode pengambilan ulasan diubah dari web scraping menjadi Shopee Open Platform API (REST v2.0, OAuth2, Model A). Dataset implementasi OmorfoShop kini diambil via `get_item_list` + `get_rating`. | Implementasikan `src/shopee_api/` di Fase 2 |
| 2026-06-07 | TRD v2 | Fase 2 | Revisi Dataset | Tinggi | Open | Dataset training berubah: Shopee scraping diganti Indonesian E-Commerce Review (Kaggle, rizqinugroho). Unified dataset sekarang SmSA + Kaggle (9K–12K ulasan). Dataset OmorfoShop hanya untuk implementasi (bukan training). | Unduh dataset Kaggle, update source_manifest.yaml |
| 2026-06-07 | TRD v2 | Fase 2 | Tambahan | Tinggi | Open | Split dataset wajib 80/10/10 dengan stratifikasi (stratified_train_test_split). Penanganan class imbalance wajib jika selisih distribusi kelas > 15%: gunakan class_weight + F1 macro. | Implementasikan di Fase 2 |
| 2026-06-07 | TRD v2 | Fase 3 | Revisi Pipeline | Tinggi | Open | TRD lama memisahkan 'Cleaning Text' dan 'Remove URL & Symbol' menjadi dua langkah. TRD v2 mengkonsolidasikan keduanya. Wajib: NO stemming, NO stopword removal. | Implementasikan pipeline baru di `src/preprocessing/` |
| 2026-06-07 | TRD v2 | Fase 4 | Tambahan | Tinggi | Open | Ditambahkan: focused random search (5–8 kombinasi, 30% data), 5-fold cross-validation, hyperparameter lengkap (dropout=0.1, weight_decay=0.01, warmup_steps=500). | Implementasikan di `src/modeling/` |
| 2026-06-07 | TRD v2 | Fase 7 | Revisi Mayor | Tinggi | Open | Rule-based mapping berubah dari 1 kondisi (positif saja) menjadi 5 kondisi compound (positif AND negatif). Ditambahkan: Mixed/Unstable Performance (netral > 35%). | Implementasikan di `src/recommendation/` |
| 2026-06-07 | TRD v2 | Fase 8 | Revisi Mayor | Tinggi | Open | Dashboard Module 6: URL Scraper diganti Open Platform Connector (OAuth2 + product selector dropdown). Ditambahkan Module 5: Settings & Configuration (filter produk, filter waktu, confidence threshold). | Implementasikan di `src/dashboard/` |
| 2026-06-07 | TRD v2 | Umum | Tambahan | Sedang | Open | Ditambahkan section Risk & Mitigation di TRD v2: GPU lokal tidak support CUDA (→ Colab), Streamlit Cloud batas memori 1GB (→ HF Spaces alternatif), Shopee API token refresh 4 jam. | Implementasikan mitigasi sesuai fase terkait |
| 2026-06-07 | TRD v2 | Umum | Revisi Struktur | Sedang | Open | Struktur folder diperbarui: `artifacts/` → `models/` + `outputs/`, `scripts/` → masuk ke `src/` submodul, ditambahkan `notebooks/` dan `data/implementation/`. | Folder sudah dibuat; migrasi kode menyusul |
| 2026-06-07 | Eksekusi | Fase 2 | Bug Kritis | Tinggi | Done | Korpus lama `phase2_sentiment_corpus*.csv` memiliki label SmSA TERBALIK (review positif ter-label `negative`) dan builder-nya hilang (file 0 byte → tidak reproducible). | Korpus dibangun ulang via `data_management.py` + `phase2_dataset_builder.py` (mapping benar 0=pos,1=neu,2=neg). File lama perlu dihapus manual. |
| 2026-06-07 | Keputusan User | Fase 2 | Revisi Dataset | Tinggi | Done | Dataset training = **gabung 3 sumber** (SmSA + PRDECT-ID + Kaggle rizqinugroho), bukan hanya SmSA+Kaggle. PRDECT-ID disimpan sebagai snapshot raw. | Unified corpus 17.962 baris (Kaggle pending). Update TRD agar konsisten. |
| 2026-06-07 | Eksekusi | Fase 2 | Risiko Data | Tinggi | Open | Kelas `neutral` hanya ~7,2% (1.489 dari 20.608; mayoritas SmSA, PRDECT-ID tak punya neutral, Kaggle Shopee hanya +143). Imbalance spread 51,9% (> ambang 15%). | Wajib `class_weight` di Fase 4; pertimbangkan augmentasi back-translation untuk neutral. |
| 2026-06-07 | Keputusan User | Fase 2/8 | Status | Sedang | Open | Kredensial Shopee Open Platform sedang proses pendaftaran. | Modul `src/shopee_api/` dibangun penuh; tes live menyusul. Sementara fallback CSV `data/implementation/omorfo_reviews_TEMPLATE.csv`. |
| 2026-06-07 | Keputusan User | Fase 4 | Status | Sedang | Open | Training IndoBERT di Google Colab (GPU lokal AMD tak support CUDA). | Kode modeling = modul + `notebooks/fase04_training.ipynb`. |
| 2026-06-07 | Eksekusi | Fase 1 | Cleanup | Rendah | Done | `requirements.txt`: buang `selenium` (sisa scraping), tambah `datasets`, `accelerate`, `evaluate`, `kagglehub`. | Selesai. |
| 2026-06-07 | Eksekusi | Fase 2 | Revisi Dataset | Tinggi | Done | Dataset Kaggle rizqinugroho **tidak tersedia lagi** → diganti Review Product Shopee (mdhimaspamungkas, 2.646 baris terpakai). Unified corpus final = **20.608 baris** (SmSA 12.679 + PRDECT-ID 5.283 + Kaggle Shopee 2.646), split 16.485/2.059/2.064. Menggantikan estimasi lama 9K–12K & angka 17.962 (Kaggle pending). | Selesai; semua doc (CLAUDE.md, fase-02/04, roadmap) disinkronkan. |
