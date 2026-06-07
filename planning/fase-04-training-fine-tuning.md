# Fase 4 — Model Training & Fine-Tuning (Checkpoint 4)

## Tujuan
Melatih model IndoBERT untuk klasifikasi sentimen menggunakan unified dataset gabungan tiga sumber (SmSA + PRDECT-ID + Review Product Shopee), total 20.608 ulasan.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-4.1 | Sistem harus memuat model IndoBERT (`indolem/indobert-base-uncased`) dari Hugging Face. |
| FR-4.2 | Sistem harus mendukung fine-tuning model menggunakan dataset training. |
| FR-4.3 | Sistem harus mendukung training multi-epoch (3–5 epoch). |
| FR-4.4 | Sistem harus menerapkan early stopping dengan `patience = 2` epoch. |
| FR-4.5 | Sistem harus menerapkan learning rate scheduler (linear decay with warmup). |
| FR-4.6 | Sistem harus menjalankan focused random search untuk validasi hyperparameter (5–8 kombinasi). |
| FR-4.7 | Sistem harus menjalankan 5-fold cross-validation pada full training set setelah konfigurasi final dipilih. |
| FR-4.8 | Sistem harus menyimpan model terbaik secara otomatis berdasarkan macro F1-score pada validation set. |

## Spesifikasi Arsitektur Model

| Komponen | Spesifikasi |
|---|---|
| Model ID (Hugging Face) | `indolem/indobert-base-uncased` |
| Arsitektur | 12-layer Bidirectional Transformer Encoder |
| Hidden Size | 768 dimensions |
| Attention Heads | 12 heads |
| Total Parameters | ~124,5 juta parameter |
| Vocabulary Size | 32.000 tokens (WordPiece) |
| Max Sequence Length (native) | 512 tokens (digunakan 128 untuk fine-tuning) |
| Pre-training Corpus | 220 juta kata (Wikipedia Indonesia, News, Web Corpus) |
| Pre-training Tasks | Masked Language Modeling (MLM) + Next Sentence Prediction (NSP) |

## Hyperparameter

| Parameter | Nilai | Justifikasi |
|---|---|---|
| Learning Rate | 2e-5 | Optimal untuk fine-tuning BERT pada dataset bahasa Indonesia |
| Batch Size | 16 | Seimbang antara stabilitas training dan memory constraint |
| Number of Epochs | 3–5 | Dikontrol oleh early stopping |
| Max Sequence Length | 128 | Sesuai rata-rata panjang ulasan e-commerce Indonesia |
| Dropout Rate | 0.1 | Regularisasi standar BERT |
| Weight Decay | 0.01 | Mencegah overfitting tanpa mengorbankan stabilitas |
| Warmup Steps | 500 | Stabilisasi training di awal epoch |
| Optimizer | AdamW | Standar untuk model transformer |

## Proses Focused Random Search

Dilakukan pada **30% training set** dengan 5–8 kombinasi acak.

**Ruang Pencarian:**

| Hyperparameter | Search Range |
|---|---|
| Learning Rate | {1e-5, 2e-5, 3e-5, 5e-5} |
| Batch Size | {8, 16, 32} |
| Number of Epochs | {3, 4, 5} |

**Tahapan:**

1. **Baseline Testing** — Latih dengan konfigurasi baseline (LR: 2e-5, BS: 16, Epoch: 3). Catat F1 macro, training time, validation loss.
2. **Focused Random Search** — 5–8 eksperimen dengan kombinasi acak dari ruang pencarian (30% training set).
3. **Performance Comparison** — Bandingkan berdasarkan F1 macro, stabilitas (validation loss curve), efisiensi komputasi.
4. **Final Config Selection** — Pilih konfigurasi dengan F1 tertinggi. Jika selisih < 1%, prioritaskan yang paling efisien.
5. **Full Training** — Latih dengan konfigurasi terpilih pada full training set.
6. **Dokumentasi** — Tabel perbandingan, learning curves, justifikasi.

## Training Flow

```
Load Dataset (training set 80%)
  ↓
Load IndoBERT (indolem/indobert-base-uncased)
  ↓
Focused Random Search (5–8 kombinasi, 30% data)
  ↓
Pilih Konfigurasi Terbaik
  ↓
Full Fine-Tuning (full training set)
  ├─ Early Stopping (patience = 2 epoch)
  └─ LR Scheduler (linear decay with warmup = 500 steps)
  ↓
Validation (validation set 10%)
  ↓
5-Fold Cross-Validation (full training set)
  ↓
Save Best Model (berdasarkan macro F1)
```

## 5-Fold Cross-Validation

| Parameter | Nilai |
|---|---|
| Metode | 5-Fold Stratified Cross-Validation |
| Dataset | Full Training Set (80%) |
| Metrik | Macro F1-Score per fold |
| Output | Mean F1 ± Std Dev |

## Model Output

| Output | Format | Keterangan |
|---|---|---|
| Model Weight | `.bin` | Bobot IndoBERT setelah fine-tuning |
| Tokenizer | `tokenizer/` | IndoBERT tokenizer untuk inferensi |
| Hyperparameter Log | `.csv` | Seluruh eksperimen focused random search |
| Training Log | `.csv` | Loss per epoch untuk training dan validation |
| Cross-Validation Report | `.json` | Mean F1 ± Std Dev dari 5-fold CV |
| Metrics Final | `.json` | Accuracy, Precision, Recall, F1 pada test set |

## Deliverables Checkpoint 4

- [ ] IndoBERT berhasil di-fine-tune dengan konfigurasi optimal.
- [ ] Focused random search selesai dan terdokumentasi (5–8 eksperimen).
- [ ] 5-Fold cross-validation selesai dan report tersedia di `outputs/reports/`.
- [ ] Best model tersimpan di `models/` (model weight + tokenizer).
- [ ] Training log dan hyperparameter log tersedia di `outputs/reports/`.
- [ ] Early stopping dan LR scheduler terimplementasi.

## Implementasi Kode

- `src/modeling/trainer.py` — Main fine-tuning loop dengan early stopping & LR scheduler
- `src/modeling/hyperparameter_search.py` — Focused random search
- `src/modeling/cross_validation.py` — 5-fold stratified cross-validation
- Notebook Colab: `notebooks/fase04_training.ipynb` (untuk eksekusi di GPU Colab)
- Output: `models/best_model/`, `outputs/reports/hyperparameter_log.csv`, `outputs/logs/training_log.csv`

## Catatan

- GPU lokal (AMD Radeon Vega 7) tidak didukung PyTorch CUDA → gunakan **Google Colab** untuk training.
- Simpan notebook training di `notebooks/` agar mudah dibuka di Colab.

## Gate ke Fase Berikutnya

Lanjut ke Fase 5 hanya jika model terlatih stabil, checkpoint terbaik sudah dipilih, dan semua log tersedia.
