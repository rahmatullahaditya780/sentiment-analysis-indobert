# Fase 1 — Project Initialization & Environment Setup (Checkpoint 1)

## Tujuan
Mempersiapkan seluruh kebutuhan dasar pengembangan sistem agar proses coding, training model, dan deployment dapat berjalan secara terstruktur dan reproducible.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-1.1 | Sistem harus menyediakan struktur project modular. |
| FR-1.2 | Sistem harus menggunakan virtual environment Python. |
| FR-1.3 | Sistem harus menyediakan konfigurasi environment untuk development dan deployment. |
| FR-1.4 | Sistem harus menyediakan file dependency `requirements.txt`. |
| FR-1.5 | Sistem harus menyediakan struktur folder dataset, model, dan dashboard. |

## Non-Functional Requirements
| ID | Requirement |
|---|---|
| NFR-1.1 | Sistem harus dapat dijalankan minimal pada Python 3.10. |
| NFR-1.2 | Struktur project harus mudah dipelihara dan scalable. |
| NFR-1.3 | Sistem harus mendukung penggunaan GPU jika tersedia (Google Colab / lokal). |

## Struktur Folder (TRD v2)

```
project_root/
│
├── data/
│   ├── raw/             # Dataset mentah (SmSA, Kaggle, OmorfoShop)
│   ├── processed/       # Dataset setelah preprocessing & split
│   └── implementation/  # Dataset OmorfoShop hasil web scraping (CSV)
│
├── notebooks/           # Jupyter/Colab notebooks eksperimen
│
├── src/
│   ├── scraping/        # Scraper Playwright OmorfoShop (modul AKTIF — metode utama)
│   ├── shopee_api/      # Open Platform client (OPSIONAL/future: persona toko sendiri)
│   ├── preprocessing/   # Pipeline preprocessing teks
│   ├── modeling/        # Fine-tuning & hyperparameter tuning
│   ├── evaluation/      # Evaluasi metrik & cross-validation
│   ├── recommendation/  # Rule-based mapping engine
│   ├── dashboard/       # Komponen Streamlit
│   └── utils/           # Helper functions
│
├── models/              # Bobot model (best model, tokenizer)
│
├── outputs/
│   ├── charts/          # Visualisasi (confusion matrix, learning curve)
│   ├── reports/         # Laporan evaluasi (.json, .csv)
│   └── logs/            # Training log
│
├── planning/            # Dokumentasi fase & roadmap
├── app.py               # Entry point Streamlit
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Backend | Python 3.10+ |
| NLP Model | IndoBERT (`indolem/indobert-base-uncased`) |
| Transformer Library | HuggingFace Transformers |
| Machine Learning | Scikit-learn |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly, Matplotlib, WordCloud |
| Text Utilities | Regex (`re`) — cleaning teks |
| Web Scraping | Python + **Playwright (Chromium)** — render DOM halaman publik Shopee, sesi login persisten (metode utama) |
| Konversi Ekstensi | Python (Pandas) — konversi CSV hasil ekstensi browser → skema implementasi |
| (Opsional/future) API Client | `requests` + HMAC-SHA256 (OAuth2) — hanya untuk persona seller-toko-sendiri |
| Environment Eksperimen | Jupyter Notebook / Google Colab |
| Deployment | Streamlit Cloud / HuggingFace Spaces |

**Catatan:** Sastrawi **TIDAK** digunakan — preprocessing IndoBERT tidak memerlukan stemming/stopword removal.

## Checklist Selesai Fase

- [x] Struktur folder project sudah modular sesuai TRD v2.
- [x] Virtual environment Python berhasil dibuat dan diaktifkan (`.venv/`).
- [x] `requirements.txt` terisi dependensi runtime.
- [x] `requirements-dev.txt` terisi dependensi development (black, ruff, pytest, ipykernel).
- [x] Konfigurasi development dan deployment tersedia (`config/`).
- [x] `.env.example` tersedia dengan template variabel (termasuk Shopee Open Platform API — **opsional/future**, bukan metode utama).
- [x] Repository Git siap digunakan dengan `.gitignore` yang sesuai.
- [x] `app.py` placeholder tersedia sebagai entry point Streamlit.
- [x] Semua submodul `src/` tersedia dengan `__init__.py`.

## Hasil Implementasi

- Struktur folder modular tersedia sesuai TRD v2 (termasuk `notebooks/`, `src/` submodul, `models/`, `outputs/`).
- Virtual environment lokal tersedia pada `.venv/`.
- Dependensi runtime tercatat di `requirements.txt` (transformers, torch, streamlit, plotly, wordcloud, dll.).
- Dependensi development tercatat di `requirements-dev.txt` (black, ruff, pytest, ipykernel).
- Environment variables template di `.env.example` mencakup konfigurasi Shopee Open Platform API (**opsional/future** — dipertahankan untuk persona seller-toko-sendiri; metode utama = web scraping Playwright).
- `.gitignore` dikonfigurasi untuk mengabaikan `models/`, `outputs/logs/`, credentials Shopee.
- `app.py` placeholder Streamlit tersedia di root project.

## Gate ke Fase Berikutnya

Lanjut ke Fase 2 hanya jika semua checklist di atas sudah selesai dan tervalidasi.
