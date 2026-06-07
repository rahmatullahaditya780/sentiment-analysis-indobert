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

- [ ] Real-time inference untuk input tunggal berjalan.
- [ ] Batch prediction dari CSV berjalan.
- [ ] Confidence score ditampilkan untuk setiap prediksi.
- [ ] Dataset OmorfoShop berhasil dianalisis dan distribusi sentimen tersedia.
- [ ] Prediction time direkam per prediksi/batch.
- [ ] Inference module siap diintegrasikan ke dashboard (Fase 8).

## Implementasi Kode

- `src/modeling/inference.py` — `SentimentPredictor` class: `predict(text)` dan `predict_batch(df)`
- Input: teks string ATAU DataFrame dengan kolom `review_text`
- Output: label, confidence score, prediction time
- Output batch: `outputs/reports/omorfo_predictions.csv`

## Gate ke Fase Berikutnya

Lanjut ke Fase 7 hanya jika prediksi sentimen konsisten, confidence score tersedia, dan distribusi sentimen OmorfoShop sudah dihasilkan.
