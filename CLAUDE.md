# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Gambaran Proyek

**Sentara** (slug teknis: `sistem analisis sentimen berbasis IndoBERT`) adalah sistem analisis sentimen untuk ulasan produk e-commerce OmorfoShop. Ini adalah proyek skripsi yang mengimplementasikan pipeline lengkap untuk mengumpulkan, memproses, melatih, dan menganalisis sentimen dari ulasan produk berbahasa Indonesia.

Proyek menggunakan **IndoBERT** (`indolem/indobert-base-uncased`) sebagai model ML inti. Data training menggabungkan tiga sumber publik: SmSA (IndoNLU), PRDECT-ID (snapshot), dan Review Product Shopee (Kaggle, mdhimaspamungkas). Data implementasi diambil dari OmorfoShop Official Store via **web scraping halaman produk publik (Playwright)** — sesuai proposal. Modul `src/shopee_api/` (Open Platform API) diturunkan menjadi opsi *future work* khusus persona seller-toko-sendiri (lihat `planning/trd-revisi-pengambilan-data-implementasi.md`).

Proyek mengikuti sistem pengembangan berbasis **10 fase dengan gate ketat**. Fase 2 (Data Collection) dan Fase 3 (Data Preprocessing) sudah lulus gate; saat ini siap memulai Fase 4 (Model Training & Fine-Tuning). Pengambilan data implementasi OmorfoShop via scraping dikerjakan paralel — bukan dependensi Fase 3–5 (data implementasi baru dipakai mulai Fase 6).

## Arsitektur Tingkat Tinggi

```
Fase 1:  Project Initialization & Environment Setup  ✅ SELESAI
Fase 2:  Data Collection & Data Management           ✅ SELESAI (OmorfoShop deferred-paralel)
Fase 3:  Data Preprocessing                          ✅ SELESAI
Fase 4:  Model Training & Fine-Tuning                🔄 SIAP MULAI
Fase 5:  Model Evaluation                            ⏳ Belum mulai
Fase 6:  Sentiment Inference Engine                  ⏳ Belum mulai
Fase 7:  Rule-Based Marketing Recommendation         ⏳ Belum mulai
Fase 8:  Dashboard Development (Streamlit)           ⏳ Belum mulai
Fase 9:  Testing & Validation                        ⏳ Belum mulai
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
| OmorfoShop (via web scraping) | Halaman publik Shopee (Playwright) | ±1.200 (PENDING) | Implementasi saja |

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
- Data implementasi via **web scraping halaman publik** (Playwright, sesi ber-login) — sesuai proposal; hanya ulasan publik, tanpa identitas pelanggan, jeda rate-limit. Input dashboard **berlapis**: CSV upload / import ekstensi / URL auto-fetch (lokal saja). Lihat `planning/trd-revisi-pengambilan-data-implementasi.md`.
- GPU lokal (AMD Radeon Vega 7) tidak didukung PyTorch CUDA → gunakan **Google Colab** untuk training Fase 4.
- Model IndoBERT (~500MB) → siapkan **HuggingFace Spaces** sebagai alternatif jika Streamlit Cloud melebihi batas memori ~1GB.
- F1 macro-average adalah metrik evaluasi **utama** (target ≥ 85%).

## Status Implementasi Saat Ini

| Modul | Status |
|---|---|
| `src/scraping/` | Dibangun (scraper Playwright, sesi login persisten) — metode utama; perlu tambah iterasi filter rating + orkestrasi multi-produk |
| `src/shopee_api/` | Dibangun (OAuth2/client/normalizer) — **opsional/future** (persona seller-toko-sendiri), bukan metode utama |
| `src/preprocessing/` | Selesai (cleaner regex, tokenizer_wrapper IndoBERT, PreprocessingPipeline) — Fase 3 lulus gate |
| `src/modeling/` | Skeleton kosong — dikerjakan Fase 4 |
| `src/evaluation/` | Skeleton kosong — dikerjakan Fase 5 |
| `src/recommendation/` | Skeleton kosong — dikerjakan Fase 7 |
| `src/dashboard/` | Skeleton kosong — dikerjakan Fase 8 |
| `data/raw/{smsa,prdect_id,kaggle}/` | Ada (3 sumber training mentah) |
| `data/processed/unified_corpus.csv` + `train/validation/test.csv` | Ada (20.608 baris, split 80/10/10 stratified seed=42) — input Fase 3 |
| `data/processed/clean_{train,validation,test}.csv` | Ada (16.477/2.059/2.064 baris, hasil cleaning Fase 3) — input Fase 4 training |
| `data/implementation/omorfo_reviews_TEMPLATE.csv` | Template skema. Data aktual via scraping/ekstensi (`omorfo_reviews_extension.csv` = 20 ulasan awal) |
| `app.py` | Placeholder — dikerjakan Fase 8 |
