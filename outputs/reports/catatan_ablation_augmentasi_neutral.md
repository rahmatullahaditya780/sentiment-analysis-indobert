# Catatan Ablation Study — Augmentasi Back-Translation Kelas Neutral

**Tanggal:** 2026-06-09
**Status temuan:** Augmentasi **tidak diadopsi** (tidak memberi perbaikan).
**Model final/produksi:** **BASELINE** (`models/best_model`, `evaluation_final.json`).

---

## 1. Latar belakang & hipotesis

Kelas **neutral** adalah kelas minoritas (7,2% korpus; support test = 150). Pada run
baseline, neutral F1 = 0,8169 — terendah di antara tiga kelas. Hipotesis: menambah
sampel neutral via **back-translation** (Fase 4b) akan menaikkan F1 kelas neutral
tanpa mengorbankan kelas lain.

Untuk menguji secara jujur (A/B), validation & test set **tetap asli** (distribusi
nyata); hanya training set yang diaugmentasi (`clean_train_augmented.csv`). Output run
augmented ditulis ke path terpisah (`models/best_model_augmented`,
`evaluation_final_augmented.json`) agar artefak baseline tidak tertimpa.

## 2. Hasil (test set, n = 2.064)

| Metrik          | Baseline | Augmented |   Delta   |
|-----------------|---------:|----------:|----------:|
| **f1_macro**    |   0,9031 |    0,8983 | **−0,0048** |
| accuracy        |   0,9419 |    0,9380 |   −0,0039 |
| negative F1     |   0,9270 |    0,9272 |   +0,0002 |
| **neutral F1**  |   **0,8169** | **0,8065** | **−0,0104** |
| positive F1     |   0,9653 |    0,9613 |   −0,0040 |

**Hipotesis tidak terbukti.** Neutral F1 justru **turun ~1 poin**, dan macro F1 ikut
turun tipis. Baseline lebih unggul di hampir semua metrik agregat.

## 3. Analisis: pergeseran trade-off, bukan perbaikan

Pada kelas neutral, augmentasi menggeser keseimbangan precision/recall — bukan
meningkatkan pemahaman kelas:

| Kelas neutral | Baseline | Augmented |  Delta  |
|---------------|---------:|----------:|--------:|
| precision     |   0,8657 |    0,7812 | −0,0845 |
| recall        |   0,7733 |    0,8333 | +0,0600 |

- **Recall naik** (0,77 → 0,83): model menangkap lebih banyak neutral (116 → 125 benar).
- **Precision anjlok** (0,87 → 0,78): tetapi non-neutral yang salah diprediksi sebagai
  neutral melonjak **18 → 35** (dari confusion matrix; kolom prediksi "neutral").

Efek bersih pada F1 **negatif**. Augmentasi membuat model lebih agresif (*trigger-happy*)
memprediksi neutral, bukan benar-benar lebih akurat membedakannya.

Confusion matrix (kolom = prediksi):

```
Baseline                          Augmented
          neg  neu  pos                     neg  neu  pos
negative  660    9   26           negative  656   15   24
neutral    27  116    7           neutral    20  125    5
positive   42    9 1168           positive   44   20 1155
```

## 4. Overfitting (kedua run masih > target 5%)

| Run       | train F1 | val F1 |   gap   | gate (≤0,05) |
|-----------|---------:|-------:|--------:|:------------:|
| Baseline  |   0,9745 | 0,8879 |  0,0866 |  WARN (fail) |
| Augmented |   0,9732 | 0,8995 |  0,0737 |  WARN (fail) |

Augmentasi sedikit memperkecil gap (0,087 → 0,074) tetapi **tidak menebus** turunnya
F1. Gap overfitting bersifat **WARNING non-blokir** pada gate Fase 5
(`scripts/validate_phase5_gate.py`) — metrik utama (macro F1 ≥ 0,85) tetap penentu, dan
kedua run lulus dengan margin lebar.

Learning curve augmented mengonfirmasi: val loss datar (epoch 1 = 0,3604 → epoch 2 =
0,3642) sementara train loss turun (0,49 → 0,24) — divergensi mulai epoch 2; titik
optimal val loss bahkan di epoch 1. Ini konsisten dengan keputusan 2-epoch.

## 5. Catatan validitas — 5-fold CV

Blok `cross_validation` di `evaluation_final_augmented.json` adalah **salinan dari
baseline** (`source: cross_validation_report.json`). CV **sengaja di-skip** untuk model
augmented (hemat GPU). Karena itu **jangan klaim CV memvalidasi model augmented** —
CV hanya berlaku untuk pipeline baseline.

## 6. Keputusan & rekomendasi

1. **Gunakan model BASELINE sebagai model final/produksi** (Fase 6 dst). Macro F1
   0,9031 dan neutral F1 0,8169 lebih unggul.
2. **Laporkan augmentasi sebagai ablation study yang gagal/jujur** — eksperimen yang
   dicoba namun tidak diadopsi karena tidak memberi perbaikan. Hasil negatif yang
   ter-dokumentasi rapi (A/B rigor + penjelasan trade-off) memperkuat kredibilitas
   skripsi, bukan melemahkannya.
3. Gap overfitting dicatat sebagai keterbatasan untuk dibahas di skripsi (lihat juga
   `planning/fase-05-*`).

## 7. Artefak terkait

| Artefak                  | Baseline                          | Augmented                                   |
|--------------------------|-----------------------------------|---------------------------------------------|
| Laporan evaluasi         | `evaluation_final.json`           | `evaluation_final_augmented.json`           |
| Confusion matrix         | `charts/confusion_matrix.png`     | `charts/confusion_matrix_aug.png`           |
| Learning curve           | `charts/learning_curve.png`       | `charts/learning_curve_aug.png`             |
| Training log (loss/epoch)| `logs/training_log.csv`           | `logs/training_log_aug.csv`                 |
| Model                    | `models/best_model`               | `models/best_model_augmented`               |
