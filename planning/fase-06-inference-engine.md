# Fase 6 — Sentiment Inference Engine (Checkpoint 6)

## Tujuan
Membangun engine untuk melakukan prediksi sentimen secara batch (dari CSV maupun ulasan yang diambil via Shopee Open Platform API), serta menerapkan model pada dataset OmorfoShop untuk menghasilkan insight bisnis.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-6.1 | Sistem harus menerima input teks ulasan tunggal dan melakukan prediksi sentimen. |
| FR-6.2 | Sistem harus menampilkan label sentimen (Positif/Negatif/Netral) beserta confidence score. |
| FR-6.3 | Sistem harus mendukung batch prediction dari file CSV. |
| FR-6.4 | Sistem harus menghasilkan output prediction time untuk monitoring performa inferensi. |
| FR-6.5 | Sistem harus menerapkan model pada dataset OmorfoShop (±1.200 ulasan) untuk menghasilkan distribusi sentimen. |
| FR-6.6 | Sistem harus dapat menerima ulasan yang diambil via Open Platform API (`get_rating`) dan meneruskannya ke pipeline inferensi secara otomatis. |

## Prediction Output

| Output | Deskripsi | Format |
|---|---|---|
| Sentiment Label | Kelas prediksi: Positif / Negatif / Netral | String |
| Confidence Score | Probabilitas keyakinan model (softmax output) | Float (0–1) |
| Prediction Time | Waktu inferensi per prediksi atau per batch | Float (detik) |
| Batch Result CSV | Hasil prediksi dataset OmorfoShop | CSV `[review_text, predicted_label, confidence_score]` |

## Arsitektur Inference Engine

```
Input (single text ATAU batch CSV ATAU API result)
  ↓
Preprocessing Pipeline (Case Fold → Clean → Tokenize)
  ↓
IndoBERT Model (load dari models/best_model/)
  ↓
Softmax Output → Label + Confidence Score
  ↓
Output: label prediksi, confidence score, prediction time
```

**Penting:** Preprocessing saat inferensi harus **identik** dengan preprocessing saat training (gunakan modul `src/preprocessing/` yang sama).

## Deliverables Checkpoint 6

- [x] Real-time inference untuk input tunggal berjalan. *(`SentimentPredictor.predict`, terverifikasi lokal CPU)*
- [x] Batch prediction dari CSV berjalan. *(`SentimentPredictor.predict_batch`, terverifikasi)*
- [x] Confidence score ditampilkan untuk setiap prediksi. *(softmax max prob + `scores` per kelas)*
- [ ] Dataset OmorfoShop berhasil dianalisis dan distribusi sentimen tersedia. *(jalur `analyze_omorfo_reviews` SIAP & terverifikasi dengan data sintetis; menunggu data live Shopee API — template `data/implementation/omorfo_reviews_TEMPLATE.csv` masih 0 baris)*
- [x] Prediction time direkam per prediksi/batch. *(`prediction_time` per prediksi; `total/avg_prediction_time` di `.attrs` batch)*
- [x] Inference module siap diintegrasikan ke dashboard (Fase 8). *(API kelas + fungsi sudah diekspor dari `src.modeling`)*

## Implementasi Kode

- `src/modeling/inference.py`
  - `SentimentPredictor` — `predict(text)` (real-time) & `predict_batch(data, text_column='review_text')` (batch CSV/list/API)
    - load lazy `models/best_model/` (torch/transformers), auto-deteksi device (cpu/cuda)
    - preprocessing inferensi **identik training**: `src.preprocessing.cleaner.preprocess_text` (case fold + clean, tanpa stemming/stopword)
    - pemetaan id→label diambil dari `config.json` model (fallback `ID2LABEL` Fase 4) — konsisten: negative=0, neutral=1, positive=2
  - `PredictionResult` — dataclass: `text`, `label`, `confidence`, `prediction_time`, `scores` (prob per kelas)
  - `analyze_omorfo_reviews(input_csv, ...)` — terapkan model ke dataset OmorfoShop (FR-6.5) → tulis CSV + ringkasan distribusi (dipakai rule-based Fase 7)
- Input: teks string ATAU DataFrame/list dengan kolom `review_text`
- Output batch: `outputs/reports/omorfo_predictions.csv` (`OMORFO_PREDICTIONS_CSV`)

## Status Implementasi

Kerangka engine **selesai & terverifikasi lokal** (torch 2.12 CPU, transformers 5.10). Tersisa satu item gate yang **terblokir data**: analisis dataset OmorfoShop nyata menunggu kredensial Shopee Open Platform API (deferred-paralel). Jalur kodenya sudah siap — begitu CSV live tersedia, jalankan `analyze_omorfo_reviews(<csv>)`.

## Gate ke Fase Berikutnya

Lanjut ke Fase 7 hanya jika prediksi sentimen konsisten, confidence score tersedia, dan distribusi sentimen OmorfoShop sudah dihasilkan. **Saat ini:** prediksi & confidence ✅; distribusi OmorfoShop ⏳ (menunggu data live Shopee API).
