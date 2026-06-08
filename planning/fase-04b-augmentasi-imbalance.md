# Fase 4b — Augmentasi Data Imbalance (Back-Translation Kelas Netral)

## Latar Belakang

Proposal (`Proposal_Revisi_Final.docx`, hal. strategi imbalance) menetapkan 4 strategi
penanganan ketidakseimbangan kelas, dengan pemicu berjenjang:

| Strategi | Ambang pemicu | Status run baseline |
|---|---|---|
| Stratified sampling | selalu | ✅ diterapkan |
| Class weight adjustment | selisih > 15% | ✅ diterapkan (sklearn `balanced`) |
| **Data augmentation (back-translation/paraphrase)** | **selisih > 25% (ekstrem)** | ❌ **belum** (celah) |
| F1-macro sebagai metrik utama | selalu | ✅ diterapkan |

**Masalah:** distribusi kelas aktual training adalah positif **59,1%** / negatif **33,7%** /
neutral **7,2%** → selisih ~**52%**, jauh melampaui ambang "ekstrem >25%" yang menurut
proposal **seharusnya memicu data augmentation**. Pada run baseline, augmentasi tidak
dilakukan, sehingga kelas minoritas `neutral` lemah:

| Kelas | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| positive | 0,973 | 0,958 | 0,965 | 1219 |
| negative | 0,905 | 0,950 | 0,927 | 695 |
| **neutral** | 0,866 | **0,773** | **0,817** | 150 |

Recall neutral hanya 0,773 (≈23% ulasan netral salah klasifikasi). Konsisten dengan uji
inference real-time: "produk biasa aja sih, standar" (intuitif netral) diprediksi *negative*.

## Tujuan Fase 4b

Merealisasikan strategi #3 proposal (back-translation) untuk menutup celah, lalu re-train
& bandingkan A/B dengan baseline. **Tidak menimpa** model/laporan baseline (reproducibility).

## Metode

- **Back-translation** ID → pivot → ID (pivot berlapis: `en`, lalu `de` untuk menutup
  kekurangan target). Menghasilkan parafrase natural, bukan duplikat.
- **Target moderat:** kelas neutral dari 1.190 → ~3.000 sampel (~15% dari train). Sisanya
  tetap diandalkan ke class weight (augmentasi + weight saling melengkapi).
- **Dedupe:** varian yang (setelah normalisasi) identik dengan sumber/varian lain dibuang.
- **Preprocessing identik training:** hasil back-translation dilewatkan `preprocess_text`
  (case fold + cleaning regex) agar distribusinya sama dengan korpus latih.
- **Hanya train yang diaugmentasi.** Validation & test TETAP asli → evaluasi jujur terhadap
  distribusi nyata.

## Implementasi Kode

- `src/modeling/augmentation.py`
  - `back_translate(text, pivot)` — satu teks, retry + backoff (deep-translator GoogleTranslator).
  - `augment_neutral(target_count=3000, pivots=['en','de'])` — generate + dedupe + tulis
    `data/processed/clean_train_augmented.csv`. Cache resume di `_bt_neutral_cache.csv`
    (run panjang yang terputus bisa dilanjutkan tanpa mengulang API call yang sudah berhasil).
- `src/modeling/config.py` → `DataConfig.use_augmented_train` (flag). Bila True, split `train`
  otomatis menunjuk `clean_train_augmented.csv` (fallback ke `clean_train.csv` bila belum ada).
- `notebooks/fase04_05_colab.ipynb` → sel toggle `USE_AUGMENTED_TRAIN`. Saat aktif, output
  diarahkan ke path **terpisah** agar baseline aman:
  - model → `models/best_model_augmented/`
  - report → `outputs/reports/evaluation_final_augmented.json`
  - sel "Perbandingan Baseline vs Augmented" mencetak delta F1 per-kelas (fokus neutral).

## Hasil Aktual Augmentasi (2026-06-08)

`clean_train_augmented.csv` berhasil dibuat & terverifikasi:

| Aspek | Nilai |
|---|---|
| Neutral asli → augmented | 1.190 → **3.000** (+1.810 varian) |
| Sumber varian | back-translation EN 1.156 + DE 654 |
| Total baris train | 16.477 → **18.287** |
| Distribusi train baru | positif 53,2% / negatif 30,4% / **neutral 16,4%** (dari 7,2%) |
| Duplikat persis | 0 |
| Teks kosong | 0 |
| Kebocoran ke val/test | **0** (evaluasi tetap jujur) |
| Class weight neutral | 4,615 → **2,032** (augmentasi menurunkan ketergantungan ke weight) |

Verifikasi penuh ada di histori commit; class weight dihitung ulang otomatis dari train aktif.

## Cara Menjalankan

1. **Generate data augmented (lokal, CPU, butuh internet):**
   ```bash
   python -m src.modeling.augmentation
   ```
   Output: `data/processed/clean_train_augmented.csv` (+ cache). Idempoten/resumable.
2. **Re-train (Google Colab GPU):** buka `notebooks/fase04_05_colab.ipynb`, pastikan
   `USE_AUGMENTED_TRAIN = True`, lalu Runtime ▸ Run all.
3. **Bandingkan:** sel terakhir mencetak tabel delta F1 baseline vs augmented. Unduh
   `artefak_fase5.zip` (berisi kedua report).

## Kriteria Keberhasilan

- Recall & F1 kelas **neutral** naik dibanding baseline (0,817) **tanpa** menurunkan F1 macro
  secara berarti (target macro tetap ≥ 0,85).
- Gap overfitting (F1 train − val) tetap ≤ 5% (augmentasi tidak boleh memicu overfit duplikat).

## Keputusan Promosi

Jika run augmented unggul (neutral F1 naik, macro stabil), promosikan
`models/best_model_augmented/` → `models/best_model/` dan jadikan `evaluation_final_augmented.json`
laporan final. Jika tidak unggul, pertahankan baseline & dokumentasikan bahwa class weight saja
sudah memadai (augmentasi tidak memberi gain) — keduanya hasil yang defensible di sidang.

## Catatan untuk Laporan/Sidang

Apa pun hasilnya, Fase 4b menutup celah proposal: strategi #3 (back-translation) yang dijanjikan
pada selisih >25% kini benar-benar diuji secara empiris, lengkap dengan tabel perbandingan A/B
sebagai bukti. Ini mengubah "celah janji vs implementasi" menjadi "eksperimen terkontrol".
