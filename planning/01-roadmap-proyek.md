# Roadmap Proyek Sistem Analisis Sentimen Ulasan Produk E-Commerce

## Tujuan
Dokumen ini menjadi acuan utama pengembangan sistem berdasarkan TRD v2, mulai dari inisialisasi sampai dokumentasi akhir.

## Aturan Gate Antar Fase
Setiap fase hanya boleh dilanjutkan jika **seluruh checklist** fase saat ini sudah terpenuhi.

### Format Status
- `Belum mulai`
- `Berjalan`
- `Siap dicek`
- `Selesai`

## Status Fase Saat Ini

| Fase | Nama | Status |
|---|---|---|
| 1 | Project Initialization & Environment Setup | **Selesai** |
| 2 | Data Collection & Data Management | **Selesai** (korpus training; OmorfoShop deferred-paralel) |
| 3 | Data Preprocessing | **Selesai** |
| 4 | Model Training & Fine-Tuning | **Selesai** (F1 macro test 0.8971; CV 0.9016 ± 0.010) |
| 5 | Model Evaluation | **Gate LULUS** (F1 macro test 0.9031; CV 0.9016 ± 0.010). Model **baseline 3-epoch = final**; re-train 2-epoch sudah diuji & terbukti lebih buruk (overfit gap dicatat sebagai keterbatasan, non-blokir) |
| 6 | Sentiment Inference Engine | **Selesai** (real-time + batch terverifikasi; **3.739 ulasan OmorfoShop nyata** dianalisis → distribusi 88,5% positif / 10,6% negatif / 0,8% netral = kondisi "Sangat Baik") |
| 7 | Rule-Based Marketing Recommendation | **Selesai** (rule engine 4 kondisi compound + trend analysis; 24 unit test) |
| 8 | Dashboard Development | **Gate LULUS** — kode selesai + verifikasi manual fetch CDP nyata oleh pengguna (tanpa masalah). Dirombak di Fase 9: Dashboard+Input menyatu jadi **Beranda** adaptif, kondisi pemasaran 4 (label Indonesia), UI/UX ramah awam |
| 9 | Testing & Validation | **Gate LULUS** — unit 207 + integrasi 15 (model nyata, termasuk fetch CDP) hijau; **usability** (2 peserta, SUS 55,0; `phase9_usability_report.md`); **expert validation** (seller Forta Beauty Shopee, 4,15 "Layak"; `phase9_validation_report.md`); **bug fixing** selesai (5→4 kondisi + Beranda + UI/UX awam, commit `aebaf7c`). Gate ke Fase 10 terbuka |
| 10 | Deployment & Documentation | Belum mulai |

## Checklist Gate Global

- [x] Struktur folder project sudah modular (sesuai TRD v2).
- [x] Environment Python aktif dan terdokumentasi.
- [x] requirements.txt terisi dependensi yang diperlukan.
- [x] Dataset publik berhasil diunduh & diverifikasi — SmSA ✔, PRDECT-ID ✔, Kaggle Shopee ✔.
- [DEFERRED] Dataset OmorfoShop via **web scraping halaman publik** (Playwright) — IN PROGRESS (awal: `omorfo_reviews_extension.csv`, 20 ulasan). Data implementasi, bukan dependensi Fase 3–5. Lihat `planning/trd-revisi-pengambilan-data-implementasi.md`.
- [x] Unified dataset tersedia dengan split 80/10/10 (20.608 baris; stratified, seed=42).
- [x] Data flow antar fase terdokumentasi (Fase 2→3: `clean_*.csv` sebagai input Fase 4).
- [x] Output tiap fase tersimpan sebagai artefak di `outputs/` (`phase2_split_stats.json`, `phase3_preprocessing_stats.json`, `phase4_final_metrics.json`, `cross_validation_report.json`, `hyperparameter_log.csv`).
- [ ] Setiap fase punya checklist selesai sebelum pindah.
- [ ] File catatan revisi diperbarui setiap ada perubahan signifikan.

## Ringkasan Output per Fase

| Fase | Output Utama |
|---|---|
| 1 | Struktur project, virtual env, requirements.txt |
| 2 | Unified dataset 20.608 ulasan (SmSA+PRDECT+Kaggle Shopee), split 80/10/10; dataset OmorfoShop ±1.200 deferred |
| 3 | Pipeline preprocessing (tanpa stemming), dataset siap training |
| 4 | Best model IndoBERT, hyperparameter log, 5-fold CV report, training log |
| 5 | Metrik evaluasi (accuracy, F1 macro ≥85%), confusion matrix, learning curve |
| 6 | Inference engine (real-time & batch), hasil prediksi dataset OmorfoShop |
| 7 | Rule engine 5 kategori, rekomendasi strategi pemasaran |
| 8 | Dashboard Streamlit 7 modul (6 modul TRD — input 2 tier CSV/URL Auto-Fetch mode CDP, jalur ekstensi dihapus — + Module 7 Insight Analitik: mismatch rating↔sentimen, keyword drill-down, perbandingan per produk; multi-URL fetch berkelanjutan dengan kuota dibagi rata & simpanan sesi) |
| 9 | Testing report, bug fix, validation report dari praktisi OmorfoShop |
| 10 | Dashboard online, repo GitHub, dokumentasi lengkap |

## Cara Memakai
1. Kerjakan file `fase-NN-*.md` secara berurutan.
2. Tandai seluruh checklist fase sebelum pindah ke fase berikutnya.
3. Catat setiap perubahan signifikan di `02-catatan-revisi.md`.
4. Simpan output setiap fase di `outputs/reports/` atau `data/processed/`.
