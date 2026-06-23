# Sentara — Sistem Analisis Sentimen Ulasan E-Commerce Berbasis IndoBERT

🔗 **Demo online (Streamlit Cloud):** https://sentara-c2fcqdukr2vh7grrkdbyzr.streamlit.app/
*(versi cloud: input CSV Upload saja; URL Auto-Fetch hanya di versi lokal)*

Sentara adalah sistem analisis sentimen untuk ulasan produk e-commerce
(studi kasus **OmorfoShop** di Shopee). Sistem mengklasifikasikan ulasan
berbahasa Indonesia menjadi **Positif / Negatif / Netral** menggunakan
**IndoBERT** yang telah di-*fine-tune*, lalu menerjemahkan distribusi sentimen
menjadi **rekomendasi strategi pemasaran** berbasis aturan dan menyajikannya di
**dashboard** yang ramah pengguna non-teknis.

> Proyek skripsi. Pipeline lengkap: pengumpulan data → praproses → fine-tuning →
> evaluasi → inferensi → rekomendasi → dashboard → pengujian → deployment.

## Sorotan Hasil

| Metrik | Nilai |
|---|---|
| **F1 macro (test)** | **0.9031** (target ≥ 0.85) |
| Akurasi (test) | 0.9419 |
| 5-fold Cross-Validation (F1 macro) | 0.9016 ± 0.010 |
| Data implementasi dianalisis | 3.739 ulasan OmorfoShop nyata |
| Distribusi sentimen OmorfoShop | 88,5% positif / 10,6% negatif / 0,8% netral |
| Validasi praktisi (seller Shopee) | Skor 4,15 / 5 = **"Layak"** |

Model inti: [`indolem/indobert-base-uncased`](https://huggingface.co/indolem/indobert-base-uncased)
(fine-tuned). Detail metrik di [`outputs/reports/evaluation_final.json`](outputs/reports/evaluation_final.json).

## Fitur Utama

- **Dua jalur input:** unggah CSV ulasan, atau *URL Auto-Fetch* otomatis dari
  Shopee (hanya versi lokal — lihat [Deployment](#deployment)).
- **Klasifikasi sentimen IndoBERT** + skor keyakinan (*confidence*) per ulasan.
- **Rekomendasi pemasaran berbasis aturan** (4 kondisi) dengan *playbook* langkah
  konkret per kondisi.
- **Dashboard Streamlit** adaptif: ringkasan verdict, grafik distribusi, kata
  yang sering muncul (word cloud), analisis tren, dan drill-down per produk.

## Prasyarat

- Python **3.11** (disarankan; 3.10–3.12 didukung).
- ~2 GB ruang disk untuk dependensi + model.
- Model IndoBERT fine-tuned (~500 MB): lihat [Menyiapkan Model](#menyiapkan-model).

## Instalasi

```bash
# 1. Clone repository
git clone <url-repo> sentara
cd sentara

# 2. Buat & aktifkan virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Unix/Mac

# 3. Pasang dependensi
pip install -r requirements.txt
pip install -r requirements-dev.txt   # opsional (test, lint, format)

# 4. Salin template environment
copy .env.example .env          # Windows
cp .env.example .env            # Unix/Mac
```

## Menyiapkan Model

Bobot model **tidak** disertakan di repo (`models/` di-gitignore karena ~500 MB).
Pilih salah satu:

- **Lokal (rekomendasi untuk dev/training):** letakkan artefak hasil fine-tuning
  Fase 4 (config, tokenizer, bobot) di `models/best_model/`. Engine inferensi
  ([`src/modeling/inference.py`](src/modeling/inference.py)) memuat dari folder ini.
- **Dari HuggingFace Hub (untuk cloud):** upload bobot ke repo HF Hub Anda, lalu
  set `MODEL_HUB_ID=<username>/<repo>` di `.env`/secrets. Bila `models/best_model/`
  tidak ada **dan** `MODEL_HUB_ID` terisi, model otomatis diunduh & di-cache dari Hub.

## Menjalankan Dashboard

```bash
streamlit run app.py
```

Dashboard terbuka di `http://localhost:8501`. Panduan pemakaian langkah demi
langkah untuk pengguna non-teknis ada di
[`docs/panduan-pengguna.md`](docs/panduan-pengguna.md).

## Cara Membaca Hasil

**Sentimen per ulasan:** Positif / Negatif / Netral + *confidence* (0–1, makin
tinggi makin yakin).

**4 kondisi pemasaran** (rule engine, [`src/recommendation/`](src/recommendation/)):

| Kondisi | Kriteria |
|---|---|
| **Sangat Baik** | Positif ≥ 50% DAN Negatif ≤ 20% |
| **Baik** | Positif 40–49% DAN Negatif 20–30% |
| **Perlu Perbaikan** | Positif < 30% DAN Negatif > 40% |
| **Beragam / Tidak Stabil** | Netral > 35% ATAU tren berubah signifikan (atau di luar tier mana pun) |

Tiap kondisi memunculkan *playbook* strategi: judul + langkah konkret + contoh
penerapan. Penjelasan istilah ada di glosarium dalam dashboard (menu
**Tentang & Bantuan**) dan di [User Guide](docs/panduan-pengguna.md).

## Sumber Data

| Dataset | Sumber | Jumlah | Fungsi |
|---|---|---|---|
| SmSA | [IndoNLU](https://github.com/IndoNLP/indonlu) | 12.679 | Training & evaluasi |
| PRDECT-ID | [Mendeley](https://data.mendeley.com/datasets/574v66hf2v) | 5.283 | Training & evaluasi |
| Review Product Shopee | [Kaggle (mdhimaspamungkas)](https://www.kaggle.com/datasets/mdhimaspamungkas/) | 2.646 | Training & evaluasi |
| OmorfoShop | Ulasan publik Shopee (endpoint JSON internal) | 3.739 | Implementasi |

Korpus gabungan training: **20.608 ulasan**, split 80/10/10 *stratified*
(seed=42). Dataset publik tidak di-*re-host* — gunakan link sumber asli.

## Struktur Proyek (ringkas)

```
sistem/
├── app.py                  # Entry point Streamlit (dashboard)
├── src/
│   ├── scraping/           # Pengambilan ulasan OmorfoShop (endpoint JSON internal)
│   ├── preprocessing/      # Case fold → clean → tokenisasi IndoBERT
│   ├── modeling/           # Fine-tuning, hyperparameter search, inferensi
│   ├── evaluation/         # Metrik, confusion matrix, cross-validation
│   ├── recommendation/     # Rule engine 4 kondisi + playbook strategi
│   ├── dashboard/          # Modul-modul UI Streamlit + glue pipeline
│   └── utils/              # Helper bersama (label harmonizer, logging)
├── data/                   # raw/ (dataset training) + implementation/ (OmorfoShop)
├── models/                 # Bobot model (gitignored)
├── outputs/                # charts/, reports/, logs/ (logs gitignored)
├── planning/               # Dokumentasi 10 fase + roadmap
├── docs/                   # User guide
└── tests/                  # Unit (207) + integrasi (15)
```

Praproses **tidak** memakai stemming/stopword removal — keduanya merusak
representasi konteks IndoBERT.

## Pengujian

```bash
pytest                      # 207 unit + 15 integrasi (integrasi butuh model nyata)
ruff check .                # Linting
black --check .             # Cek format
```

## Deployment

Sistem disiapkan untuk **Streamlit Community Cloud** dan **HuggingFace Spaces**.
Di cloud, hanya **Tier 1 (CSV Upload)** yang aktif; **URL Auto-Fetch (Tier 2)**
otomatis dinonaktifkan karena lingkungan cloud *headless* tidak mendukung sesi
browser ber-login (FR-8.14, `detect_environment` di
[`src/dashboard/shopee_connector.py`](src/dashboard/shopee_connector.py)).

| Komponen | Versi Cloud | Versi Lokal/Desktop |
|---|---|---|
| CSV Upload | ✅ Aktif | ✅ Aktif |
| URL Auto-Fetch (mode CDP) | ❌ Nonaktif | ✅ Aktif |
| Sumber model | HF Hub (`MODEL_HUB_ID`) | `models/best_model/` |

### A. Streamlit Community Cloud

1. Push repo ke GitHub.
2. Buat app baru di [share.streamlit.io](https://share.streamlit.io), pilih repo
   & main file `app.py`, Python **3.11**.
3. Isi **Secrets** dengan isi [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)
   (minimal `MODEL_HUB_ID`).

> ⚠️ Batas RAM gratis ~1 GB berisiko *out-of-memory* dengan IndoBERT ~500 MB. Bila
> crash, gunakan HuggingFace Spaces.

### B. HuggingFace Spaces (RAM lebih lega — mitigasi OOM)

1. Buat Space baru (SDK: **Streamlit**).
2. Salin blok YAML front-matter dari [`README_HF.md`](README_HF.md) ke `README.md`
   milik Space, lalu push kode.
3. Set Space Secret `MODEL_HUB_ID`. `packages.txt` & `requirements.txt` otomatis dipasang.

> Versi Python untuk HF Spaces diatur via `python_version` di front-matter
> `README_HF.md`; untuk Streamlit Cloud dipilih di UI deploy. (Tidak memakai
> `runtime.txt` karena kedua platform tidak membacanya.)

Latar belakang keputusan deployment & matriks fitur lengkap ada di
[`planning/fase-10-deployment-dokumentasi.md`](planning/fase-10-deployment-dokumentasi.md).

## Logging

Logging terpusat ([`src/utils/logging_setup.py`](src/utils/logging_setup.py))
menulis ke stderr (tampil di log cloud) dan `outputs/logs/app.log` (lokal,
gitignored). Atur level via `LOG_LEVEL` (default `INFO`).

## Lisensi & Atribusi

Proyek skripsi untuk keperluan akademik. Dataset publik tunduk pada lisensi
masing-masing sumber (lihat tabel [Sumber Data](#sumber-data)). Model dasar
IndoBERT milik [IndoLEM](https://huggingface.co/indolem).
