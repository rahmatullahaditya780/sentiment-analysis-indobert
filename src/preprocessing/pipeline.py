"""
Fase 3 — Pipeline preprocessing teks (orkestrasi).

Menggabungkan tahap cleaning (case folding + regex) dengan tokenizer IndoBERT
menjadi satu alur yang konsisten dipakai di training (Fase 4) maupun inference
(Fase 6).

    Raw text -> case folding -> text cleaning -> [tokenization IndoBERT]

Tahap cleaning beroperasi penuh dengan pandas (ringan, jalan lokal). Tahap
tokenization bersifat opsional & lazy (butuh `transformers`, dijalankan di Colab).

PENTING: TIDAK ada stemming/stopword removal (FR-3.3). Tidak ada impor Sastrawi
maupun NLTK di seluruh paket `src/preprocessing/`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.preprocessing.cleaner import preprocess_text
from src.preprocessing.tokenizer_wrapper import (
    DEFAULT_MAX_LENGTH,
    DEFAULT_MODEL_NAME,
    IndoBERTTokenizerWrapper,
)
from src.utils.label_harmonizer import CANONICAL_LABELS


@dataclass
class CleaningStats:
    """Ringkasan statistik tahap cleaning satu split."""

    rows_in: int
    rows_out: int
    dropped_empty_text: int
    dropped_missing_label: int
    dropped_invalid_label: int
    dropped_duplicate: int

    def as_dict(self) -> dict:
        return {
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "dropped_empty_text": self.dropped_empty_text,
            "dropped_missing_label": self.dropped_missing_label,
            "dropped_invalid_label": self.dropped_invalid_label,
            "dropped_duplicate": self.dropped_duplicate,
        }


class PreprocessingPipeline:
    """Pipeline preprocessing teks untuk korpus sentimen."""

    def __init__(
        self,
        text_column: str = "text",
        label_column: str = "label",
        model_name: str = DEFAULT_MODEL_NAME,
        max_length: int = DEFAULT_MAX_LENGTH,
        drop_duplicates: bool = True,
    ) -> None:
        self.text_column = text_column
        self.label_column = label_column
        self.max_length = max_length
        self.drop_duplicates = drop_duplicates
        self.tokenizer = IndoBERTTokenizerWrapper(model_name, max_length)
        self._last_stats: CleaningStats | None = None

    # ── Tahap cleaning (lokal) ────────────────────────────────────────────────
    def clean_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bersihkan teks + buang baris invalid.

        Validasi (lihat fase-03): tidak boleh ada teks kosong, label hilang,
        atau label di luar skema kanonik. Baris semacam itu dibuang.
        """
        rows_in = len(df)
        out = df.copy()

        # Label hilang
        missing_mask = out[self.label_column].isna()
        dropped_missing = int(missing_mask.sum())
        out = out[~missing_mask]

        # Case folding + cleaning teks
        out[self.text_column] = out[self.text_column].map(preprocess_text)

        # Teks kosong setelah cleaning
        empty_mask = out[self.text_column].str.len() == 0
        dropped_empty = int(empty_mask.sum())
        out = out[~empty_mask]

        # Label di luar skema kanonik
        invalid_mask = ~out[self.label_column].isin(CANONICAL_LABELS)
        dropped_invalid = int(invalid_mask.sum())
        out = out[~invalid_mask]

        # Duplikat (text, label) — bisa muncul setelah cleaning menyamakan teks
        dropped_dup = 0
        if self.drop_duplicates:
            before = len(out)
            out = out.drop_duplicates(subset=[self.text_column, self.label_column])
            dropped_dup = before - len(out)

        out = out.reset_index(drop=True)
        self._last_stats = CleaningStats(
            rows_in=rows_in,
            rows_out=len(out),
            dropped_empty_text=dropped_empty,
            dropped_missing_label=dropped_missing,
            dropped_invalid_label=dropped_invalid,
            dropped_duplicate=dropped_dup,
        )
        return out

    @property
    def last_stats(self) -> CleaningStats | None:
        return self._last_stats

    # ── Tahap tokenization (Colab) ────────────────────────────────────────────
    def tokenize_texts(self, texts, return_tensors: str | None = None) -> dict:
        """Tokenisasi list teks bersih -> input_ids & attention_mask."""
        return self.tokenizer.tokenize(texts, return_tensors=return_tensors)

    def token_length_stats(self, texts) -> dict:
        """Statistik panjang token (butuh `transformers`). Berguna untuk audit."""
        enc = self.tokenizer.tokenize(texts)
        lengths = [sum(mask) for mask in enc["attention_mask"]]
        n = len(lengths)
        return {
            "n": n,
            "min": min(lengths) if n else 0,
            "max": max(lengths) if n else 0,
            "mean": round(sum(lengths) / n, 2) if n else 0,
            "truncated_at_max": sum(1 for length in lengths if length >= self.max_length),
        }
