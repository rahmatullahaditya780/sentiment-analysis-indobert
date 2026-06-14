# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Gambaran Proyek

**Sentara** (slug teknis: `sistem analisis sentimen berbasis IndoBERT`) adalah sistem analisis sentimen untuk ulasan produk e-commerce OmorfoShop. Ini adalah proyek skripsi yang mengimplementasikan pipeline lengkap untuk mengumpulkan, memproses, melatih, dan menganalisis sentimen dari ulasan produk berbahasa Indonesia.

Proyek menggunakan **IndoBERT** (`indolem/indobert-base-uncased`) sebagai model ML inti. Data training menggabungkan tiga sumber publik: SmSA (IndoNLU), PRDECT-ID (snapshot), dan Review Product Shopee (Kaggle, mdhimaspamungkas). Data implementasi diambil dari OmorfoShop Official Store via **endpoint JSON internal Shopee** (`fetch('/api/v2/item/get_ratings')` dieksekusi dari dalam sesi browser ber-login — lihat catatan di bawah). DOM scraping Playwright (`src/scraping/scrape_omorfo_reviews.py`) diblokir anti-bot Shopee → diturunkan jadi fallback. Modul `src/shopee_api/` (Open Platform API) tetap opsi *future work* (persona seller-toko-sendiri). Lihat `planning/trd-revisi-pengambilan-data-implementasi.md` & catatan revisi 2026-06-10.

Proyek mengikuti sistem pengembangan berbasis **10 fase dengan gate ketat**. Fase 1–6 sudah lulus gate (IndoBERT fine-tuned: F1 macro test **0.9031**, CV **0.9016 ± 0.010**; model **baseline 3-epoch** final — augmentasi back-translation & re-train 2-epoch diuji tapi terbukti lebih buruk). Fase 6 selesai: **3.739 ulasan OmorfoShop nyata** (5 produk terlaris) dianalisis → distribusi **88,5% positif / 10,6% negatif / 0,8% netral** (= Excellent Performance). Fase 7 lulus gate (rule engine 5 kondisi compound + trend analysis, 24 unit test). Fase 8 kode selesai + **peningkatan pasca-gate Fase 8.5** (Module 7 Insight Analitik: mismatch rating↔sentimen, keyword drill-down, perbandingan per produk; multi-URL auto-fetch berkelanjutan dengan kuota dibagi rata & simpanan sesi; polish UX & sentralisasi konstanta), boot HTTP 200. **Fase 9 (Testing & Validation) BERJALAN:** unit testing **selesai & terdokumentasi** — **199 unit test** hijau (ditambah 31 test `src/preprocessing/` yang sebelumnya tak ada; laporan `outputs/reports/phase9_unit_test_report.md`); integration test end-to-end **model IndoBERT nyata selesai** (jalur CSV: 16 test `tests/integration/`, marker `integration`, jalan via `pytest -m integration`; artefak `outputs/reports/phase9_integration_report.json`). **Tersisa di Fase 9:** usability testing, expert validation praktisi OmorfoShop, dan verifikasi **manual** fetch nyata Shopee jalur CDP (perlu Chrome ber-login di desktop).

## Arsitektur Tingkat Tinggi

```
Fase 1:  Project Initialization & Environment Setup  ✅ SELESAI
Fase 2:  Data Collection & Data Management           ✅ SELESAI (OmorfoShop deferred-paralel)
Fase 3:  Data Preprocessing                          ✅ SELESAI
Fase 4:  Model Training & Fine-Tuning                ✅ SELESAI (F1 macro 0.8971; CV 0.9016 ± 0.010)
Fase 5:  Model Evaluation                            ✅ SELESAI (F1 macro test 0.9031 ≥ 0.85)
Fase 6:  Sentiment Inference Engine                  ✅ SELESAI (3.739 ulasan OmorfoShop → 88,5% pos / 10,6% neg / 0,8% net)
Fase 7:  Rule-Based Marketing Recommendation         ✅ SELESAI (5 kondisi compound + trend; 24 unit test)
Fase 8:  Dashboard Development (Streamlit)           🔄 KODE SELESAI (7 modul, +Fase 8.5) — pending verifikasi manual fetch Shopee
Fase 9:  Testing & Validation                        🔄 BERJALAN (unit 199 test ✅ + integrasi E2E model nyata ✅; sisa: usability, expert validation, fetch CDP manual)
Fase 10: Deployment & Documentation                  ⏳ Belum mulai
```

## Struktur Folder (TRD v2)

```
project_root/
│
├── data/
│   ├── raw/             # Dataset mentah (SmSA TSV, PRDECT-ID CSV, Kaggle Shopee CSV)
│   │   ├── smsa/        # train_preprocess.tsv, validation_preprocess.tsv, test_preprocess.tsv
│   │   ├── prdect_id/   # prdect_snapshot.csv
│   │   ├── kaggle/      # data.csv (Review Product Shopee)
│   │   └── source_manifest.yaml
│   ├── processed/       # Dataset setelah preprocessing & split (CSV)
│   └── implementation/  # Dataset OmorfoShop hasil web scraping (CSV)
│
├── notebooks/           # Jupyter/Colab notebooks untuk eksperimen
│
├── src/
│   ├── scraping/        # Scraper Playwright OmorfoShop (modul AKTIF — metode utama)
│   ├── shopee_api/      # Open Platform client (OPSIONAL/future: persona toko sendiri)
│   ├── preprocessing/   # Pipeline preprocessing teks (case fold → clean → tokenize)
│   ├── modeling/        # Fine-tuning IndoBERT & focused random search
│   ├── evaluation/      # Metrik evaluasi & 5-fold cross-validation
│   ├── recommendation/  # Rule-based mapping engine (5 kondisi pemasaran)
│   ├── dashboard/       # Komponen Streamlit (modul-modul UI)
│   └── utils/           # Helper functions bersama
│
├── models/              # Bobot model terlatih (best model + tokenizer) — di-gitignore
│
├── outputs/
│   ├── charts/          # Visualisasi (confusion matrix, learning curve, word cloud)
│   ├── reports/         # Laporan evaluasi (.json, .csv, hyperparameter log)
│   └── logs/            # Training log — di-gitignore
│
├── planning/            # Dokumentasi fase & roadmap
│   ├── 01-roadmap-proyek.md
│   ├── 02-catatan-revisi.md
│   └── fase-NN-*.md
│
├── app.py               # Entry point Streamlit (Fase 8)
├── requirements.txt     # Dependensi runtime
├── requirements-dev.txt # Dependensi development (black, ruff, pytest, ipykernel)
└── .env.example         # Template environment variables
```

## Sumber Data

| Dataset | Sumber | Jumlah (aktual) | Fungsi |
|---|---|---|---|
| SmSA | github.com/IndoNLP/indonlu | 12.679 | Training & Evaluasi |
| PRDECT-ID (snapshot) | data.mendeley.com/datasets/574v66hf2v | 5.283 | Training & Evaluasi |
| Review Product Shopee | Kaggle (mdhimaspamungkas) | 2.646 | Training & Evaluasi |
| OmorfoShop (endpoint JSON internal) | Halaman publik Shopee (sesi browser ber-login) | 3.739 (terkumpul) | Implementasi saja |

**Unified dataset** (SmSA + PRDECT-ID + Kaggle Shopee): **20.608 ulasan**, split **80/10/10** stratified (seed=42) → train **16.485** / validation **2.059** / test **2.064**. Distribusi kelas: positif 59,1% / negatif 33,7% / neutral 7,2% (spread > 15% → wajib `class_weight` di Fase 4).

## Alur Data

```
USER INPUT
  ├─ [CSV Batch Upload]
  └─ [Input URL Produk] → Web Scraping (Playwright, browser ber-login, lokal)
         ↓
  PREPROCESSING MODULE
  Case Folding → Text Cleaning (regex) → Tokenization (IndoBERT, max_length=128)
  TANPA stemming / stopword removal — merusak konteks IndoBERT
         ↓
  INDOBERT MODEL (indolem/indobert-base-uncased, fine-tuned)
         ↓
  SENTIMENT CLASSIFICATION: Positif / Negatif / Netral + Confidence Score
         ↓
  RULE-BASED MAPPING ENGINE (5 kondisi: Excellent/Good/Moderate/Poor/Mixed)
         ↓
  DASHBOARD VISUALIZATION (Streamlit: Charts + Word Cloud + Recommendation Panel)
```

## Pola Implementasi Utama

### Import Antar Modul

Semua skrip/modul mengimpor dari `src` menggunakan resolusi path root proyek:

```python
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
```

### Sistem Gate Fase

Setiap fase memiliki:
1. File `planning/fase-NN-*.md` dengan deliverable dan checklist
2. Checklist harus 100% selesai sebelum fase berikutnya dimulai
3. Output fase tersimpan di `outputs/` dan/atau `data/processed/`

Status gate saat ini ada di `planning/01-roadmap-proyek.md`.

## Hyperparameter IndoBERT (Fase 4)

| Parameter | Nilai | Keterangan |
|---|---|---|
| Model | `indolem/indobert-base-uncased` | HuggingFace Hub |
| Learning Rate | 2e-5 | Optimal untuk BERT bahasa Indonesia |
| Batch Size | 16 | Seimbang memori/stabilitas |
| Epochs | 3–5 | + early stopping (patience=2) |
| Max Sequence Length | 128 | Sesuai rata-rata ulasan e-commerce |
| Dropout Rate | 0.1 | Regularisasi standar BERT |
| Weight Decay | 0.01 | Mencegah overfitting |
| Warmup Steps | 500 | Stabilisasi awal training |
| Optimizer | AdamW | Standar transformer |

Focused random search: 5–8 kombinasi pada 30% training set → validasi dengan 5-fold cross-validation pada full training set.

## Rule-Based Mapping (Fase 7) — 5 Kondisi Pemasaran

| Kondisi | Kriteria (Compound) |
|---|---|
| Excellent Performance | Positif ≥ 50% AND Negatif ≤ 20% |
| Good Performance | Positif 40–49% AND Negatif 20–30% |
| Moderate Performance | Positif 30–39% AND Negatif 30–40% |
| Poor Performance | Positif < 30% AND Negatif > 40% |
| Mixed/Unstable | Netral > 35% ATAU trend berubah signifikan |

## Alur Kerja Pengembangan

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Unix/Mac
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Perintah Umum

```bash
streamlit run app.py            # Jalankan dashboard

ruff check .                    # Linting
black --check .                 # Cek format
black .                         # Format otomatis
pytest                          # Jalankan semua tes
```

### Environment Variables

Salin `.env.example` ke `.env` dan isi:

```
APP_ENV=development
APP_NAME=sentara
STREAMLIT_SERVER_PORT=8501
MODEL_NAME=indolem/indobert-base-uncased
MODEL_MAX_LENGTH=128
SHOPEE_PARTNER_ID=<dari Shopee Open Platform>
SHOPEE_PARTNER_KEY=<secret key untuk HMAC-SHA256>
SHOPEE_SHOP_ID=<shop ID OmorfoShop>
SHOPEE_REDIRECT_URL=http://localhost:8501
```

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Model AI | IndoBERT (`indolem/indobert-base-uncased`) |
| Transformer Library | HuggingFace Transformers ≥4.40 |
| Machine Learning | PyTorch ≥2.2, Scikit-learn ≥1.4 |
| Dashboard | Streamlit ≥1.35 |
| Data Processing | Pandas ≥2.2, NumPy ≥1.26 |
| Visualization | Plotly ≥5.22, Matplotlib ≥3.9, WordCloud |
| Web Scraping | Playwright (Chromium) — render DOM, sesi login persisten |
| Eksperimen | Jupyter Notebook / Google Colab |
| Deployment | Streamlit Cloud / HuggingFace Spaces |

## Catatan Penting

- **TIDAK** menggunakan Sastrawi (stemming) atau NLTK stopwords — merusak representasi konteks IndoBERT.
- Data implementasi diambil via **endpoint JSON internal Shopee** (`scrape_omorfo_api.py`: `fetch('/api/v2/item/get_ratings')` dari dalam sesi browser ber-login — lolos anti-bot yang memblokir DOM scraping). Hanya ulasan publik, tanpa identitas pelanggan, jeda rate-limit. **Bab metodologi skripsi WAJIB diselaraskan**: sumber = "ulasan publik via endpoint JSON internal situs dari sesi browser sah" (bukan render-DOM, bukan Open Platform API). Input dashboard tetap **berlapis**: CSV / ekstensi / auto-fetch. Lihat `planning/trd-revisi-pengambilan-data-implementasi.md` & catatan revisi 2026-06-10.
- GPU lokal (AMD Radeon Vega 7) tidak didukung PyTorch CUDA → gunakan **Google Colab** untuk training Fase 4.
- Model IndoBERT (~500MB) → siapkan **HuggingFace Spaces** sebagai alternatif jika Streamlit Cloud melebihi batas memori ~1GB.
- F1 macro-average adalah metrik evaluasi **utama** (target ≥ 85%).

## Status Implementasi Saat Ini

| Modul | Status |
|---|---|
| `src/scraping/` | Selesai. **Metode aktual: `scrape_omorfo_api.py`** (endpoint JSON internal via in-browser fetch, mode hybrid-multi) — 3.739 ulasan terkumpul. `scrape_omorfo_reviews.py`/`scrape_omorfo_batch.py` (DOM, diblokir anti-bot) = fallback |
| `src/shopee_api/` | Dibangun (OAuth2/client/normalizer) — **opsional/future** (persona seller-toko-sendiri), bukan metode utama |
| `src/preprocessing/` | Selesai (cleaner regex, tokenizer_wrapper IndoBERT, PreprocessingPipeline) — Fase 3 lulus gate |
| `src/modeling/` | Selesai (trainer, hyperparameter_search, cross_validation, augmentation, inference) — Fase 4 lulus gate; Fase 6 inference terverifikasi lokal |
| `src/evaluation/` | Selesai (metrics, evaluator, visualizer, cross_val_report) — Fase 5 lulus gate (F1 macro 0.9031) |
| `src/recommendation/` | Selesai (rule_engine 5 kondisi compound, strategy_mapper, trend_analyzer) — Fase 7 lulus gate, 24 unit test |
| `src/dashboard/` | Selesai (analysis_pipeline glue + input/results/recommendation/visualization/settings/insights module + model_info + shopee_connector + cdp_fetch_worker/fetch_worker/login_worker) — Fase 8 + 8.5, 7 modul. Multi-URL auto-fetch berkelanjutan (kuota dibagi rata `split_quota`, simpanan sesi `fetch_cache` per shopid.itemid). Fetch nyata Shopee = verifikasi manual |
| `data/raw/{smsa,prdect_id,kaggle}/` | Ada (3 sumber training mentah) |
| `data/processed/unified_corpus.csv` + `train/validation/test.csv` | Ada (20.608 baris, split 80/10/10 stratified seed=42) — input Fase 3 |
| `data/processed/clean_{train,validation,test}.csv` | Ada (16.477/2.059/2.064 baris, hasil cleaning Fase 3) — input Fase 4 training |
| `data/implementation/omorfo_reviews.csv` | **3.739 ulasan nyata** (5 produk terlaris, 5 kategori) via endpoint JSON internal — input Fase 6/7. `omorfo_reviews_minoritas.csv` = 669 ulasan bintang 1–4 (bukti deteksi negatif). `*_TEMPLATE.csv`/`*_extension.csv` = artefak awal |
| `app.py` | Selesai (entry Streamlit: cache predictor di `st.session_state`, tab CSV/URL, sidebar filter, render 4 modul hasil) — Fase 8 |
