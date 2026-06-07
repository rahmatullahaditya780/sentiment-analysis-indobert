# Fase 5 — Model Evaluation (Checkpoint 5)

## Tujuan
Mengukur performa model klasifikasi sentimen menggunakan test set yang belum pernah dilihat selama training.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-5.1 | Sistem harus menghitung accuracy pada test set. |
| FR-5.2 | Sistem harus menghitung precision (macro-average) untuk setiap kelas sentimen. |
| FR-5.3 | Sistem harus menghitung recall (macro-average) untuk setiap kelas sentimen. |
| FR-5.4 | Sistem harus menghitung F1-score dengan pendekatan **macro-average** sebagai metrik evaluasi **UTAMA**. |
| FR-5.5 | Sistem harus menampilkan confusion matrix untuk setiap kelas. |
| FR-5.6 | Sistem harus menghasilkan learning curve (training loss vs. validation loss per epoch). |

## Evaluation Metrics

| Metrik | Pendekatan | Fungsi |
|---|---|---|
| Accuracy | Overall | Proporsi prediksi benar dari total sampel |
| Precision | Macro-average | Ketepatan prediksi per kelas, dirata-rata secara setara |
| Recall | Macro-average | Sensitivitas per kelas |
| **F1-Score** | **Macro-average (UTAMA)** | Rata-rata harmonis precision & recall; lebih sensitif terhadap class imbalance |
| Confusion Matrix | Per kelas | Distribusi prediksi benar/salah tiap kelas |
| Learning Curve | Per epoch | Training loss vs. validation loss untuk deteksi overfitting |

## Validation Requirements (Target)

| Requirement | Target |
|---|---|
| Accuracy | ≥ 85% |
| Macro F1-Score | ≥ 85% — metrik utama |
| Overfitting | Selisih training F1 dan validation F1 ≤ 5% |
| Learning Curve | Wajib disertakan untuk membuktikan stabilitas dan konvergensi training |

## Deliverables Checkpoint 5

- [ ] Semua metrik evaluasi tersedia: accuracy, precision macro, recall macro, F1 macro.
- [ ] Confusion matrix selesai dibuat untuk setiap kelas (Positif, Negatif, Netral).
- [ ] Learning curve (training loss vs. validation loss per epoch) tersedia.
- [ ] Cross-validation report tersedia (mean F1 ± std dev dari 5-fold — dari Fase 4).
- [ ] Final evaluation report selesai (`outputs/reports/evaluation_final.json`).
- [ ] Visualisasi tersimpan di `outputs/charts/` (confusion matrix, learning curve).

## Implementasi Kode

- `src/evaluation/config.py` — Path artefak input/output & target gate; re-export pemetaan label kanonik dari Fase 4 (urutan kelas konsisten)
- `src/evaluation/metrics.py` — Fungsi murni: accuracy, precision/recall/F1 macro, per-kelas, confusion matrix, cek overfitting, perakit `evaluation_final.json`
- `src/evaluation/evaluator.py` — Orkestrasi: muat best model Fase 4, inferensi test set, rakit laporan (impor torch/transformers lazy)
- `src/evaluation/visualizer.py` — Plot confusion matrix & learning curve (loss per epoch dari `trainer_state.json`/`training_log.csv`), export ke `outputs/charts/`
- `src/evaluation/cross_val_report.py` — Ringkas hasil 5-fold CV dari Fase 4 (`cross_validation_report.json`)
- Notebook Colab: `notebooks/fase05_evaluation.ipynb` (eksekusi inferensi & visualisasi di GPU Colab)
- Gate: `scripts/validate_phase5_gate.py` (lapis A kerangka + lapis B deliverable, target F1 macro & accuracy ≥ 0.85)
- Output: `outputs/reports/evaluation_final.json`, `outputs/charts/confusion_matrix.png`, `outputs/charts/learning_curve.png`

## Catatan

- GPU lokal (AMD Radeon Vega 7) tidak didukung PyTorch CUDA → inferensi evaluasi dijalankan di **Google Colab** (sama seperti training Fase 4).
- Dependency berat (`torch`/`transformers`/`sklearn`/`matplotlib`) di-impor **lazy** di dalam fungsi; modul tetap bisa di-import lokal untuk cek kerangka tanpa instalasi penuh.
- Status saat ini: kerangka siap (gate lapis A hijau); lapis B terisi setelah notebook Colab dijalankan & artefak diunduh.

## Gate ke Fase Berikutnya

Lanjut ke Fase 6 hanya jika F1 macro ≥ 85% pada test set dan semua artefak evaluasi tersedia.
