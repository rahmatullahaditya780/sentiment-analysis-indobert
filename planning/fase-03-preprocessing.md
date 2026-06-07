# Fase 3 — Data Preprocessing (Checkpoint 3)

## Tujuan
Membersihkan dan mempersiapkan data teks agar dapat diproses oleh IndoBERT.

> **PENTING:** Pipeline ini **TIDAK** melakukan stemming maupun stopword removal. IndoBERT menggunakan subword embeddings (WordPiece) yang mempertahankan konteks semantik secara utuh — stemming/stopword removal justru akan merusak representasi konteks.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-3.1 | Sistem harus melakukan case folding (mengubah seluruh teks menjadi huruf kecil). |
| FR-3.2 | Sistem harus melakukan text cleaning: menghapus URL, emoji, simbol, dan tanda baca berlebih. |
| FR-3.3 | Sistem **TIDAK BOLEH** melakukan stemming atau stopword removal. |
| FR-3.4 | Sistem harus melakukan tokenization menggunakan IndoBERT tokenizer (`indolem/indobert-base-uncased`). |
| FR-3.5 | Sistem harus melakukan truncation otomatis pada teks yang melebihi `max_length` (128 token). |
| FR-3.6 | Sistem harus melakukan padding agar semua input memiliki panjang seragam (`max_length = 128`). |
| FR-3.7 | Sistem harus menyimpan hasil preprocessing dalam format yang siap untuk training. |

## Pipeline Preprocessing

```
Raw Text
  ↓
Step 1: Case Folding
  → Ubah semua teks ke huruf kecil
  ↓
Step 2: Text Cleaning
  → Hapus URL, emoji, simbol, tanda baca berlebih
  → Gunakan regex; TANPA stemming & stopword removal
  ↓
Step 3: Tokenization
  → IndoBERT Tokenizer (WordPiece subword)
  → Format: [CLS] tokens [SEP]
  ↓
Step 4: Padding & Truncation
  → max_length = 128 token
  → Teks < 128 → padding; teks > 128 → truncation
  ↓
Processed Dataset (siap untuk training / inference)
```

## Validation Requirements

| Requirement | Validasi |
|---|---|
| Token max length | ≤ 128 — sesuai rata-rata panjang ulasan e-commerce Indonesia |
| Empty text | Tidak boleh ada — teks kosong setelah cleaning harus dihapus |
| Missing label | Tidak boleh ada — setiap baris harus memiliki label sentimen yang valid |
| Stemming/Stopword Removal | **TIDAK dilakukan** — wajib diverifikasi bahwa pipeline tidak menggunakan Sastrawi atau NLTK stopwords |

## Deliverables Checkpoint 3

- [ ] Pipeline preprocessing selesai dan terdokumentasi di `src/preprocessing/`.
- [ ] Verifikasi bahwa stemming/stopword removal tidak dilakukan.
- [ ] Dataset training/validation/test berhasil dipreprocess.
- [ ] Tokenization dengan IndoBERT tokenizer berhasil (output: `input_ids`, `attention_mask`).
- [ ] Dataset siap untuk Fase 4 training.
- [ ] Tidak ada baris dengan teks kosong atau label kosong.

## Implementasi Kode

- `src/preprocessing/pipeline.py` — Class `PreprocessingPipeline` dengan step case fold, clean, tokenize
- `src/preprocessing/cleaner.py` — Regex-based text cleaner (URL, emoji, simbol)
- `src/preprocessing/tokenizer_wrapper.py` — Wrapper IndoBERT tokenizer dengan padding & truncation
- Output: dataset HuggingFace `Dataset` format atau CSV dengan kolom `input_ids`, `attention_mask`, `label`

## Gate ke Fase Berikutnya

Lanjut ke Fase 4 hanya jika output preprocessing siap dipakai langsung untuk training IndoBERT.
