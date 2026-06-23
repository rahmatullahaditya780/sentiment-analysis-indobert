---
title: Sentara - Analisis Sentimen OmorfoShop
emoji: 📊
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
python_version: "3.11"
pinned: false
license: mit
---

# Sentara di HuggingFace Spaces

File ini adalah **template README untuk HuggingFace Spaces** (bukan README repo
GitHub). Saat membuat Space baru (SDK: Streamlit), salin blok YAML front-matter di
atas ke `README.md` milik Space tersebut — HF Spaces membaca konfigurasi (judul,
SDK, `app_file`, versi Python) dari blok itu.

## Yang wajib disiapkan sebelum Space berjalan

1. **Bobot model di HuggingFace Hub.** Space tidak menyimpan `models/best_model/`
   (~500MB). Upload bobot IndoBERT fine-tuned ke repo model HF Hub Anda, lalu set
   Space Secret `MODEL_HUB_ID = <username>/<repo-model>`.
2. **Secret `LOG_LEVEL`** (opsional, default `INFO`).
3. `packages.txt` & `requirements.txt` di repo Space akan otomatis dipasang.

## Catatan fitur di cloud

- Hanya **Tier 1 (CSV Upload)** yang aktif. Tier 2 (URL Auto-Fetch mode CDP)
  otomatis dinonaktifkan di lingkungan cloud headless (lihat FR-8.14;
  `detect_environment` di `src/dashboard/shopee_connector.py`).
- RAM Space gratis lebih lega dari batas ~1GB Streamlit Community Cloud, sehingga
  lebih aman untuk IndoBERT ~500MB (mitigasi R-02).

Lihat **README.md** utama untuk instalasi lokal, struktur proyek, dan panduan
deployment lengkap.
