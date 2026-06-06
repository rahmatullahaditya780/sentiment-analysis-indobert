# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Gambaran Proyek

**sistem-analisis-sentimen** adalah sistem analisis sentimen untuk ulasan produk e-commerce. Ini adalah proyek skripsi yang mengimplementasikan pipeline lengkap untuk mengumpulkan, memproses, melatih, dan menganalisis sentimen dari ulasan produk berbahasa Indonesia.

Proyek menggunakan **IndoBERT** (varian BERT untuk bahasa Indonesia) sebagai model ML inti, dan mengikuti sistem pengembangan berbasis 10 fase dengan gate ketat. Saat ini berada di Fase 2 (Pengumpulan Data & Manajemen Data), dengan dataset dari Shopee (via web scraping) dan SMSA (dataset sentimen Indonesia).

## Arsitektur Tingkat Tinggi

Proyek mengikuti **arsitektur berbasis fase dengan gate ketat** — setiap fase hanya bisa dimulai setelah checklist fase sebelumnya selesai 100%:

```
Fase 1: Inisialisasi Proyek (SELESAI)
  └─ Setup environment, dependensi, struktur konfigurasi

Fase 2: Pengumpulan Data & Manajemen Data (BERJALAN)
  ├─ Pengumpulan data mentah (Shopee, SMSA)
  ├─ Pelacakan manifest/metadata dataset
  ├─ Utilitas validasi kolom
  └─ Persiapan dataset (balancing, cleaning)

Fase 3: Preprocessing Data (SELANJUTNYA)
  └─ Normalisasi teks, tokenisasi untuk IndoBERT

Fase 4–10: Training Model → Inferensi → Dashboard → Deployment
```

### Direktori Utama

- **`src/`** — Utilitas inti
  - `data_management.py` — Loading data, validasi, manajemen skema
  - `phase2_dataset_builder.py` — Konstruksi dataset dari berbagai sumber
  - `__init__.py` — Definisi package

- **`scripts/`** — Pipeline yang bisa dijalankan
  - `init_phase2_data.py` — Inisialisasi struktur folder fase 2
  - `build_phase2_corpus.py` — Menggabungkan dataset menjadi corpus terpadu
  - `scrape_shopee_reviews.py` — Web scraper untuk ulasan Shopee
  - `validate_phase2_gate.py` — Validasi gate sebelum masuk fase 3

- **`data/`** — Data di berbagai tahap
  - `raw/` — Dataset mentah dan source manifest (`shopee/`, `smsa/`)
  - `interim/` — Hasil pemrosesan sementara
  - `processed/` — Dataset final siap training
  - `external/` — Data pendukung dari sumber eksternal

- **`artifacts/`** — Output model dan analisis
  - `models/` — Checkpoint model terlatih
  - `checkpoints/` — Checkpoint training
  - `reports/` — Laporan analisis dan statistik

- **`config/`** — Konfigurasi per environment
  - `development.yaml` — Dev (debug=true, path lokal)
  - `deployment.yaml` — Produksi (debug=false, konfigurasi server)

- **`planning/`** — Dokumentasi fase dan roadmap
  - `01-roadmap-proyek.md` — Roadmap utama dengan status gate global
  - `fase-NN-*.md` — Dokumentasi detail tiap fase beserta checklistnya
  - `02-catatan-revisi.md` — Catatan revisi di luar fase

## Alur Data & Konsep Kunci

### Struktur Dataset Fase 2

Sistem bekerja dengan tiga sumber data:
1. **Shopee** — Ulasan hasil web scraping (`data/raw/shopee/`)
2. **SMSA** — Dataset Sentimen Indonesia (`data/raw/smsa/`)
   - `train_preprocess.tsv` — Data training
   - `test_preprocess.tsv` — Data test
   - `validation_preprocess.tsv` — Data validasi

### Source Manifest

Berada di `data/raw/source_manifest.yaml`, melacak metadata tiap dataset:
- Nama dan tipe sumber
- URL/referensi
- Lisensi dan hak penggunaan
- Tanggal pengumpulan, versi
- Catatan khusus tentang keterbatasan

### Validasi Dataset

Sebelum lanjut ke Fase 3, dataset harus lulus validasi di `validate_phase2_gate.py`:
- Semua kolom wajib harus ada di corpus gabungan
- Source manifest harus lengkap
- Corpus gabungan disimpan di `data/processed/phase2_sentiment_corpus.csv`

### Keseimbangan Kelas

Dataset seimbang saat ini (`phase2_sentiment_corpus_balanced.csv`):
- Positif: 37,50% (6.810 baris)
- Negatif: 32,50% (5.902 baris)
- Netral: 30,00% (5.448 baris)
- **Total: 18.160 baris**

## Alur Kerja Pengembangan

### Setup

```bash
# Buat dan aktifkan virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Unix/Mac

# Install dependensi
pip install -r requirements.txt
pip install -r requirements-dev.txt   # Untuk tools pengembangan
```

### Perintah Umum

```bash
# Validasi gate Fase 2 sebelum masuk Fase 3
python scripts/validate_phase2_gate.py

# Inisialisasi struktur data Fase 2
python scripts/init_phase2_data.py

# Bangun corpus gabungan dari berbagai sumber
python scripts/build_phase2_corpus.py

# Pengecekan kualitas kode
ruff check .        # Linting cepat
black --check .     # Cek format kode

# Format kode otomatis
black .

# Jalankan tes
pytest
pytest tests/test_nama_file.py   # Jalankan satu file tes
```

### Environment Variables

Dikonfigurasi di `.env` (dari `.env.example`):
```
APP_ENV=development|production
APP_NAME=sistem-analisis-sentimen
STREAMLIT_SERVER_PORT=8501    # Untuk dashboard Fase 8
MODEL_NAME=indobert-base-p2
```

## Dependensi & Stack

`requirements.txt` belum diisi — paket akan ditambahkan seiring kemajuan fase (rencana: HuggingFace Transformers, PyTorch, Pandas, NumPy, PyYAML, Streamlit).

`requirements-dev.txt` (isi terkonfirmasi):
- **black** — Code formatter
- **ruff** — Linter cepat
- **pytest** — Framework testing
- **ipykernel** — Dukungan Jupyter

## Pola Implementasi Utama

### Import Utilitas

Semua skrip fase mengimpor dari `src` menggunakan resolusi path root proyek:
```python
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from src.data_management import load_data, validate_columns
```

### Sistem Gate Fase

Setiap fase memiliki:
1. File markdown di `planning/fase-NN-*.md` dengan daftar deliverable
2. Checklist yang harus 100% selesai sebelum fase berikutnya
3. Skrip validasi di `scripts/` untuk memverifikasi syarat gate
4. Artefak output tersimpan di `artifacts/` dengan laporan

Status gate saat ini ada di `planning/01-roadmap-proyek.md`.

### Pola Konfigurasi

Dua environment di `config/`:
- Development: path lokal, debugging aktif
- Deployment: binding server, optimisasi
- Keduanya mengacu pada: model `indobert-base-p2`, max length 128, batch size 16

## Status Implementasi

| File | Status |
|---|---|
| `scripts/validate_phase2_gate.py` | Sudah diimplementasikan |
| `src/data_management.py` | Skeleton kosong (diimpor oleh validate script — harus diimplementasikan lebih dulu) |
| `src/phase2_dataset_builder.py` | Skeleton kosong |
| `scripts/init_phase2_data.py` | Skeleton kosong |
| `scripts/build_phase2_corpus.py` | Skeleton kosong |
| `scripts/scrape_shopee_reviews.py` | Skeleton kosong |

**Catatan:** Dataset seimbang (`data/processed/phase2_sentiment_corpus_balanced.csv`) sudah ada meskipun skrip build masih kosong — dibuat secara manual di luar skrip.

**Shopee scraper membutuhkan:** Setup browser automation (Playwright, Chrome profile di `data/raw/shopee/chrome_profile_pw/`).

**Kemajuan gate:** Semua item checklist di `planning/fase-NN-*.md` harus dicentang sebelum pindah ke fase berikutnya. Status gate saat ini ada di `planning/01-roadmap-proyek.md`.

## Fase Mendatang (Pekerjaan Selanjutnya)

- **Fase 3**: Preprocessing data (normalisasi, tokenisasi)
- **Fase 4**: Fine-tuning IndoBERT dengan dataset seimbang
- **Fase 5**: Evaluasi model dan komputasi metrik
- **Fase 6**: Inference engine untuk prediksi sentimen real-time
- **Fase 7**: Rekomendasi pemasaran berbasis aturan
- **Fase 8**: Dashboard Streamlit (akan menggunakan direktori `app/`)
- **Fase 9**: Testing dan validasi menyeluruh
- **Fase 10**: Deployment dan dokumentasi final
