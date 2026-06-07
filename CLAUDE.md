# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Gambaran Proyek

**Sentara** (slug teknis: `sentara`) adalah sistem analisis sentimen untuk ulasan produk e-commerce OmorfoShop. Ini adalah proyek skripsi yang mengimplementasikan pipeline lengkap untuk mengumpulkan, memproses, melatih, dan menganalisis sentimen dari ulasan produk berbahasa Indonesia.

Proyek menggunakan **IndoBERT** (`indolem/indobert-base-uncased`) sebagai model ML inti. Data training menggunakan dataset publik SmSA (IndoNLU) dan Indonesian E-Commerce Review (Kaggle). Data implementasi diambil dari OmorfoShop Official Store via **Shopee Open Platform API (REST v2.0, OAuth2)** — bukan web scraping.

Proyek mengikuti sistem pengembangan berbasis **10 fase dengan gate ketat**. Saat ini berada di Fase 2 (Data Collection & Data Management).

## Arsitektur Tingkat Tinggi

```
Fase 1:  Project Initialization & Environment Setup  ✅ SELESAI
Fase 2:  Data Collection & Data Management           🔄 BERJALAN
Fase 3:  Data Preprocessing                          ⏳ Belum mulai
Fase 4:  Model Training & Fine-Tuning                ⏳ Belum mulai
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
│   ├── raw/             # Dataset mentah (SmSA TSV, Kaggle CSV)
│   │   ├── smsa/        # train_preprocess.tsv, validation_preprocess.tsv, test_preprocess.tsv
│   │   └── source_manifest.yaml
│   ├── processed/       # Dataset setelah preprocessing & split (CSV)
│   └── implementation/  # Dataset OmorfoShop hasil Shopee Open Platform API
│
├── notebooks/           # Jupyter/Colab notebooks untuk eksperimen
│
├── src/
│   ├── scraping/        # Scraping statis OmorfoShop (legacy/backup saja)
│   ├── shopee_api/      # Shopee Open Platform client (OAuth2, get_item_list, get_rating)
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

| Dataset | Sumber | Jumlah | Fungsi |
|---|---|---|---|
| SmSA | github.com/IndoNLP/indonlu | 4.000–5.000 | Training & Evaluasi |
| Indonesian E-Commerce Review | Kaggle (rizqinugroho) | 5.000–7.000 | Training & Evaluasi |
| OmorfoShop (via Open Platform API) | Shopee API `get_rating` | ±1.200 | Implementasi saja |

**Unified dataset** (SmSA + Kaggle): 9.000–12.000 ulasan, split **80/10/10** (train/val/test) dengan stratifikasi.

## Alur Data

```
USER INPUT
  ├─ [CSV Batch Upload]
  └─ [Pilih Produk] → Open Platform API (get_item_list + get_rating)
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
| API Client | `requests` + HMAC-SHA256 (Shopee Open Platform) |
| Eksperimen | Jupyter Notebook / Google Colab |
| Deployment | Streamlit Cloud / HuggingFace Spaces |

## Catatan Penting

- **TIDAK** menggunakan Sastrawi (stemming) atau NLTK stopwords — merusak representasi konteks IndoBERT.
- Shopee data **hanya via Open Platform API resmi** (OAuth2) — bukan web scraping — patuh ToS Shopee.
- GPU lokal (AMD Radeon Vega 7) tidak didukung PyTorch CUDA → gunakan **Google Colab** untuk training Fase 4.
- Model IndoBERT (~500MB) → siapkan **HuggingFace Spaces** sebagai alternatif jika Streamlit Cloud melebihi batas memori ~1GB.
- F1 macro-average adalah metrik evaluasi **utama** (target ≥ 85%).

## Status Implementasi Saat Ini

| Modul | Status |
|---|---|
| `src/shopee_api/` | Skeleton kosong — dikerjakan Fase 2 |
| `src/preprocessing/` | Skeleton kosong — dikerjakan Fase 3 |
| `src/modeling/` | Skeleton kosong — dikerjakan Fase 4 |
| `src/evaluation/` | Skeleton kosong — dikerjakan Fase 5 |
| `src/recommendation/` | Skeleton kosong — dikerjakan Fase 7 |
| `src/dashboard/` | Skeleton kosong — dikerjakan Fase 8 |
| `data/raw/smsa/` | Ada (train/validation/test TSV dari IndoNLU) |
| `data/processed/phase2_sentiment_corpus_balanced.csv` | Ada (dibuat manual, perlu reverifikasi dengan sumber baru) |
| `app.py` | Placeholder — dikerjakan Fase 8 |
