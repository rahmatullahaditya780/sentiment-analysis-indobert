"""
Fase 4 — Pemuatan data & penyiapan dataset untuk fine-tuning IndoBERT.

Membaca dataset bersih hasil Fase 3 (`clean_{train,validation,test}.csv`),
mengencode label kanonik ke id, menghitung class weight (wajib karena
imbalance kelas > 15%, lihat CLAUDE.md), dan membangun `datasets.Dataset`
yang sudah ditokenisasi IndoBERT.

Strategi impor
--------------
- pandas/numpy dipakai langsung (ringan, jalan lokal).
- `datasets` dan `transformers` di-impor LAZY di dalam fungsi yang
  membutuhkannya, supaya modul tetap bisa diimpor lokal tanpa dependency
  berat (training aktual di Google Colab).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.modeling.config import (
    DEFAULT_MAX_LENGTH,
    DEFAULT_MODEL_NAME,
    DEFAULT_SEED,
    LABEL2ID,
    DataConfig,
)


def load_clean_split(split: str, data_cfg: DataConfig | None = None) -> pd.DataFrame:
    """Muat clean_{split}.csv dan tambahkan kolom `label_id` (int).

    split: "train" | "validation" | "test".
    """
    data_cfg = data_cfg or DataConfig()
    path = data_cfg.clean_path(split)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset bersih tidak ditemukan: {path}. Jalankan preprocessing Fase 3 dulu."
        )
    df = pd.read_csv(path)
    missing = {data_cfg.text_column, data_cfg.label_column} - set(df.columns)
    if missing:
        raise ValueError(f"Kolom wajib hilang di {path.name}: {missing}")
    df = encode_labels(df, data_cfg.label_column)
    return df


def encode_labels(df: pd.DataFrame, label_column: str = "label") -> pd.DataFrame:
    """Tambahkan kolom `label_id` hasil mapping label kanonik -> id.

    Raise bila ada label di luar skema kanonik (positive/negative/neutral).
    """
    unknown = set(df[label_column].unique()) - set(LABEL2ID)
    if unknown:
        raise ValueError(f"Label di luar skema kanonik: {unknown}")
    out = df.copy()
    out["label_id"] = out[label_column].map(LABEL2ID).astype(int)
    return out


def compute_class_weights(df: pd.DataFrame, label_column: str = "label") -> list[float]:
    """Hitung class weight (balanced) sesuai urutan id di LABEL2ID.

    Memakai skema sklearn 'balanced': w_c = n_samples / (n_classes * count_c).
    Wajib dipakai di loss training karena spread distribusi kelas > 15%.
    Mengembalikan list float terurut berdasarkan id (index 0..NUM_LABELS-1).
    """
    counts = df[label_column].map(LABEL2ID).value_counts().to_dict()
    n_samples = len(df)
    n_classes = len(LABEL2ID)
    weights: list[float] = []
    for idx in range(n_classes):
        count = counts.get(idx, 0)
        if count == 0:
            # Kelas tak muncul: beri bobot netral 1.0 agar tak membagi nol.
            weights.append(1.0)
        else:
            weights.append(n_samples / (n_classes * count))
    return weights


def label_distribution(df: pd.DataFrame, label_column: str = "label") -> dict[str, float]:
    """Proporsi tiap label kanonik (untuk audit/log)."""
    counts = df[label_column].value_counts(normalize=True)
    return {label: round(float(counts.get(label, 0.0)), 4) for label in LABEL2ID}


def stratified_subset(
    df: pd.DataFrame,
    frac: float,
    label_column: str = "label",
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Ambil subset stratified per kelas (dipakai focused random search 30%).

    Mempertahankan proporsi kelas asli. Deterministik via `seed`.
    """
    if not 0 < frac <= 1:
        raise ValueError(f"frac harus di (0, 1], dapat {frac}")
    if frac == 1:
        return df.reset_index(drop=True)
    out = (
        df.groupby(label_column, group_keys=False)
        .apply(lambda g: g.sample(frac=frac, random_state=seed))
        .reset_index(drop=True)
    )
    return out


# ── Penyiapan HuggingFace Dataset (Colab) ─────────────────────────────────────
def build_hf_dataset(
    df: pd.DataFrame,
    tokenizer=None,
    text_column: str = "text",
    model_name: str = DEFAULT_MODEL_NAME,
    max_length: int = DEFAULT_MAX_LENGTH,
):
    """Bangun `datasets.Dataset` tertokenisasi siap dipakai HF Trainer.

    Kolom hasil: input_ids, attention_mask, labels. Butuh `datasets` &
    `transformers` (dijalankan di Colab). Jika `tokenizer` tidak diberikan,
    di-load otomatis dari `model_name`.
    """
    try:
        from datasets import Dataset
    except ImportError as exc:  # pragma: no cover - tergantung environment
        raise ImportError(
            "Paket `datasets` belum terpasang. Penyiapan dataset dijalankan di "
            "Google Colab (Fase 4). Lokal: pip install datasets transformers"
        ) from exc

    if "label_id" not in df.columns:
        df = encode_labels(df)

    if tokenizer is None:
        from src.preprocessing.tokenizer_wrapper import IndoBERTTokenizerWrapper

        tokenizer = IndoBERTTokenizerWrapper(model_name, max_length).tokenizer

    ds = Dataset.from_pandas(
        df[[text_column, "label_id"]].rename(columns={"label_id": "labels"}),
        preserve_index=False,
    )

    def _tokenize(batch):
        return tokenizer(
            batch[text_column],
            padding="max_length",
            truncation=True,
            max_length=max_length,
        )

    ds = ds.map(_tokenize, batched=True)
    ds = ds.remove_columns([text_column])
    ds.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])
    return ds
