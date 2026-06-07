"""
Fase 3 — Wrapper IndoBERT tokenizer (WordPiece subword).

Membungkus `transformers.AutoTokenizer` untuk `indolem/indobert-base-uncased`
dengan konfigurasi padding & truncation seragam (FR-3.4 s/d FR-3.6):

    [CLS] token... [SEP]  ->  input_ids + attention_mask, max_length=128

Catatan eksekusi
----------------
`transformers`/`torch` TIDAK terpasang di environment lokal (training & inference
dijalankan di Google Colab, lihat CLAUDE.md). Karena itu impor `transformers`
dilakukan secara LAZY di dalam `load()` — modul ini tetap bisa diimpor untuk
keperluan unit test/inspeksi tanpa dependency berat. Tokenization aktual atas
seluruh korpus dilakukan saat Fase 4 di Colab via `dataset.map(...)`.
"""

from __future__ import annotations

import os
from typing import Sequence

DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "indolem/indobert-base-uncased")
DEFAULT_MAX_LENGTH = int(os.getenv("MODEL_MAX_LENGTH", "128"))


class IndoBERTTokenizerWrapper:
    """Wrapper tipis di atas IndoBERT tokenizer dengan padding/truncation tetap."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        max_length: int = DEFAULT_MAX_LENGTH,
    ) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self._tokenizer = None  # diisi lewat load()

    # ── Lifecycle ────────────────────────────────────────────────────────────
    def load(self) -> "IndoBERTTokenizerWrapper":
        """Muat tokenizer dari HuggingFace Hub. Butuh `transformers` terpasang."""
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover - tergantung environment
            raise ImportError(
                "Paket `transformers` belum terpasang. Tokenization dijalankan di "
                "Google Colab (Fase 4). Untuk verifikasi lokal: "
                "pip install transformers"
            ) from exc
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        return self

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self.load()
        return self._tokenizer

    # ── Tokenization ─────────────────────────────────────────────────────────
    def tokenize(
        self,
        texts: str | Sequence[str],
        return_tensors: str | None = None,
    ) -> dict:
        """Tokenisasi teks -> dict berisi `input_ids` & `attention_mask`.

        FR-3.5/FR-3.6: truncation otomatis dan padding ke `max_length`.
        """
        if isinstance(texts, str):
            texts = [texts]
        return self.tokenizer(
            list(texts),
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors=return_tensors,
        )

    def tokenize_dataset(self, dataset, text_column: str = "text"):
        """Map tokenisasi ke HuggingFace `datasets.Dataset` (dipakai di Fase 4)."""

        def _batch(batch):
            enc = self.tokenizer(
                batch[text_column],
                padding="max_length",
                truncation=True,
                max_length=self.max_length,
            )
            return enc

        return dataset.map(_batch, batched=True)
