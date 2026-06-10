# Fase 8 — Kerangka Persiapan Eksekusi

> Dokumen pendamping operasional untuk [`fase-08-dashboard.md`](fase-08-dashboard.md)
> (spesifikasi/FR). File ini menjawab pertanyaan **"apa yang harus disiapkan dan
> dengan urutan apa"** sebelum & selama menulis kode dashboard. Bukan spesifikasi
> baru — semua FR & modul tetap mengacu ke dokumen spesifikasi.

---

## 1. Status Pra-syarat (Gate Masuk)

Fase 8 boleh dimulai karena gate Fase 7 sudah lulus. Aset hulu yang **wajib ada**
sebelum dashboard bisa hidup — semuanya sudah terverifikasi tersedia per 2026-06-10:

| Aset | Lokasi | Status | Dipakai oleh |
|---|---|---|---|
| Best model IndoBERT + tokenizer | `models/best_model/` (config, model.safetensors, tokenizer.*) | ✅ Ada | Module 2 (inference) |
| Hasil prediksi OmorfoShop | `outputs/reports/omorfo_predictions.csv` | ✅ Ada (3.739 baris) | Seed demo / fallback tampilan |
| Data implementasi mentah | `data/implementation/omorfo_reviews.csv` | ✅ Ada | Contoh CSV Upload |
| Rule engine Fase 7 | `src/recommendation/` (`recommend()`) | ✅ Lulus gate | Module 3 |
| Inference engine Fase 6 | `src/modeling/inference.py` (`SentimentPredictor`) | ✅ Terverifikasi | Module 2 |
| JSON fetch engine | `src/scraping/scrape_omorfo_api.py` (`fetch_ratings`, `run_hybrid`) | ✅ Ada | Module 6 |
| Dependensi dashboard | `requirements.txt` (streamlit, plotly, matplotlib, wordcloud) | ✅ Lengkap | Semua modul |

**Tidak ada dependensi baru yang perlu di-`pip install`.** Semua sudah tercantum.

---

## 2. Inventaris Titik Integrasi (Kontrak Publik yang Dipakai Ulang)

Dashboard adalah **lapisan integrasi**, bukan logika baru. Empat antarmuka publik
yang harus di-*wire*, jangan ditulis ulang:

### 2.1 Inference (Module 2)
```python
from src.modeling.inference import SentimentPredictor
pred = SentimentPredictor()                       # load model dari models/best_model/
df = pred.predict_batch(df, text_column="review_text")
# → menambah kolom: predicted_label, confidence_score
# → df.attrs: total_prediction_time, avg_prediction_time
```
- `torch`/`transformers` di-impor **lazy** → cache instance di `st.session_state`
  (FR UI: "Model Loading"). Load sekali, pakai berkali-kali.

### 2.2 Recommendation (Module 3)
```python
from src.recommendation import recommend
rec = recommend(df_predictions, save=False)       # MarketingRecommendation
rec.as_dict()  # {condition, interpretation, business_insight, strategies[], distribution{}}
```
- Sudah meng-orkestrasi distribusi → 5 kondisi compound → strategi → trend.
- Trend otomatis aktif bila ada kolom `date_review`.

### 2.3 JSON Fetch (Module 6 — lokal saja)
```python
from src.scraping.scrape_omorfo_api import fetch_ratings, run_hybrid
# Output DataFrame berskema: review_id, review_text, rating,
#                            product_name, product_category, date_review
```
- Memakai `sync_playwright` → **wajib dijalankan via subprocess** (`fetch_worker.py`)
  agar tidak bentrok dengan event-loop asyncio Streamlit.
- Cap ≤1.200 (`max_reviews`), rate-limit (`delay`) via argumen worker.

### 2.4 Skema kolom standar (kontrak data antar-modul)
```
review_id | review_text | rating | product_name | product_category | date_review
```
Setelah inference bertambah: `predicted_label`, `confidence_score`.
**Semua modul harus berbicara dalam skema ini** — Data Normalizer (Module 6)
bertugas menyeragamkan input CSV agar cocok.

---

## 3. Arsitektur File & Alur Data

```
app.py  (entry, set_page_config, sidebar nav, cache SentimentPredictor)
  │
  ├─ src/dashboard/input_module.py        Module 1  (2 tab: CSV / URL Auto-Fetch)
  ├─ src/dashboard/analysis_pipeline.py   GLUE: predict_batch → recommend  (dipakai kedua jalur)
  ├─ src/dashboard/results_module.py      Module 2  (pie / bar / trend chart)
  ├─ src/dashboard/recommendation_module.py Module 3 (panel 5 kondisi)
  ├─ src/dashboard/visualization_module.py  Module 4 (word cloud per kelas)
  ├─ src/dashboard/settings_module.py     Module 5  (filter kategori/waktu/threshold)
  ├─ src/dashboard/shopee_connector.py    Module 6  (router + validate_url + detect_env)
  └─ src/dashboard/fetch_worker.py        subprocess JSON fetch (emit progress NDJSON)
```

**Alur data utama (one-click):**
```
[CSV Upload] ─┐
              ├─→ DataFrame (skema standar)
[URL Fetch] ──┘        │
                       ▼
        analysis_pipeline.run(df):
           SentimentPredictor.predict_batch(df)   →  +predicted_label, +confidence
           recommend(df_pred)                     →  MarketingRecommendation
                       │
        ┌──────────────┼───────────────┬───────────────────┐
        ▼              ▼               ▼                   ▼
   Module 2       Module 3        Module 4            Module 5
   (charts)     (rekomendasi)   (word cloud)     (filter mengubah df → re-run)
```

---

## 4. Urutan Eksekusi (Build Order Berbasis Dependensi)

Dibangun **bottom-up**: glue & data dulu, lalu tampilan, lalu fitur lokal-saja yang
paling berisiko terakhir. Tiap langkah bisa dijalankan & dilihat hasilnya sebelum lanjut.

| # | Langkah | File | Output yang terlihat | FR / Deliverable |
|---|---|---|---|---|
| 0 | **Pra-flight** (Bag. 6) — pastikan model load & predict 1 baris | — | sanity check di REPL | — |
| 1 | **Glue pipeline** — `predict_batch → recommend` atas CSV statis | `analysis_pipeline.py` | DataFrame + rec object | inti FR-8.1/8.5 |
| 2 | **CSV Upload** + render hasil minimal di `app.py` | `input_module.py`, `app.py` | upload → tabel berlabel | FR-8.3, deliv. Module 1 (CSV) |
| 3 | **Sentiment Results** — pie, bar, (trend bila ada `date_review`) | `results_module.py` | 2–3 chart Plotly | FR-8.4, FR-8.7, Module 2 |
| 4 | **Recommendation Panel** — kondisi + strategi + insight | `recommendation_module.py` | panel teks dari `rec` | FR-8.5, Module 3 |
| 5 | **Visualization** — word cloud per kelas + distribusi/kategori | `visualization_module.py` | 3 word cloud + chart | FR-8.6, Module 4 |
| 6 | **Settings** — filter kategori/waktu + threshold (re-run pipeline) | `settings_module.py` | sidebar filter live | FR-8.8, Module 5 |
| 7 | **Env detection + URL validator** (tanpa fetch nyata dulu) | `shopee_connector.py` | badge "Lokal saja", validasi URL | FR-8.10, FR-8.14 |
| 8 | **fetch_worker subprocess** + progress NDJSON → `st.progress` | `fetch_worker.py`, `shopee_connector.py` | progress bar + counter | FR-8.9/8.11/8.12/8.13, Module 6 |
| 9 | **Error/fallback handler** (login-wall / 0-ulasan / timeout) | `shopee_connector.py` | pesan + arahan ke CSV | FR-8.9, deliverable error handling |

> **Catatan urutan:** langkah 1–6 jalan **100% di mesin manapun** (cloud/lokal) karena
> hanya butuh model + pandas. Langkah 7–9 (URL Auto-Fetch) adalah jalur **lokal-saja**
> yang paling rapuh (Playwright + anti-bot) → sengaja dikerjakan terakhir agar mayoritas
> deliverable sudah aman lebih dulu. Demo cloud cukup bersandar pada CSV Upload.

---

## 5. Keputusan Desain yang Sudah Terkunci (jangan diperdebatkan ulang saat ngoding)

- **Caching model:** `st.session_state["predictor"]` (bukan `@st.cache_resource` agar
  kontrol lifecycle eksplisit) — sesuai catatan UI Requirements.
- **Subprocess untuk fetch:** wajib, alasan asyncio (lihat 2.3). Komunikasi via **NDJSON
  di stdout** (satu objek JSON per baris: `{"type":"progress","done":N,"total":M}` /
  `{"type":"done","path":...}` / `{"type":"error","msg":...}`).
- **Deteksi lingkungan:** cloud bila tak ada display/browser → sembunyikan tab URL
  Auto-Fetch, tampilkan badge & arahkan ke CSV (FR-8.14). Heuristik: cek env var
  Streamlit Cloud / ketiadaan Chrome user-data-dir.
- **Sumber data implementasi = endpoint JSON internal** (`scrape_omorfo_api.py`), BUKAN
  DOM-render (diblokir) maupun Open Platform API. Konsisten CLAUDE.md & TRD revisi.
- **Cap 1.200 ulasan/produk & rate-limit** dilakukan di worker, bukan di UI.

---

## 6. Checklist Pra-flight (jalankan sekali sebelum langkah 1)

```bash
# 1. Lingkungan aktif & deps lengkap
.venv\Scripts\activate
pip install -r requirements.txt          # harus no-op kalau sudah sinkron

# 2. Model bisa di-load & predict (sanity)
python -c "from src.modeling.inference import SentimentPredictor; \
p=SentimentPredictor(); print(p.predict('barang bagus banget').as_dict())"

# 3. Rule engine jalan atas predictions yang ada
python -c "import pandas as pd; from src.recommendation import recommend; \
df=pd.read_csv('outputs/reports/omorfo_predictions.csv'); \
print(recommend(df).as_dict()['condition'])"

# 4. Placeholder dashboard tampil
streamlit run app.py
```

Jika keempat langkah hijau → mulai langkah 1 (glue pipeline).

---

## 7. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Playwright bentrok asyncio Streamlit | URL Auto-Fetch crash | Subprocess `fetch_worker.py` (sudah dikunci di desain) |
| Anti-bot (DataDome) blokir di IP cloud | Fetch gagal di Streamlit Cloud | FR-8.14: jalur dinonaktifkan di cloud, andalkan CSV |
| Load model ~500MB tiap interaksi | UI lambat / OOM | Cache `st.session_state`, load lazy sekali |
| CSV user beda skema kolom | Pipeline error | Data Normalizer + validasi kolom (pesan jelas, tunjuk template) |
| Word cloud Indonesia penuh stopword | Visual kurang informatif | Daftar stopword ringan **khusus tampilan** (bukan untuk model) |
| Trend chart minim sampel/periode | Grafik menyesatkan | Reuse guard `MIN_PERIOD_SIZE=30` dari Fase 7 |

---

## 8. Definition of Done Fase 8

Mengacu ke **Deliverables Checkpoint 8** di [`fase-08-dashboard.md`](fase-08-dashboard.md#deliverables-checkpoint-8).
Gate ke Fase 9 terbuka bila keenam modul berjalan stabil, `streamlit run app.py`
mulus di lokal, dan jalur CSV Upload terbukti jalan end-to-end di lingkungan cloud-like.
