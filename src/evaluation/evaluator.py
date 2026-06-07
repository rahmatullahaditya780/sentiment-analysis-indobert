"""
Fase 5 — Orkestrasi evaluasi: muat best model, prediksi test set, rakit laporan.

Menjembatani best model Fase 4 (`models/best_model/`) dengan metrik murni di
`metrics.py`. Semua impor `torch`/`transformers` bersifat LAZY supaya modul bisa
diimpor lokal tanpa dependency berat. Eksekusi nyata di Google Colab (GPU).

Alur: load_best_model -> predict_split(test) -> build_evaluation_report.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.evaluation.config import (
    BEST_MODEL_DIR,
    DataConfig,
    LABEL2ID,
)
from src.evaluation.metrics import build_evaluation_report


def load_best_model(model_dir: str | Path = BEST_MODEL_DIR):
    """Muat best model + tokenizer hasil Fase 4 dari `model_dir`.

    Mengembalikan tuple (model, tokenizer). Model di-set ke mode eval.
    """
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_dir = Path(model_dir)
    if not model_dir.exists():
        raise FileNotFoundError(
            f"Best model tidak ditemukan: {model_dir}. Selesaikan training Fase 4 "
            "dan unduh artefak dari Colab dulu."
        )
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model.eval()
    return model, tokenizer


def predict_split(
    df: pd.DataFrame,
    model,
    tokenizer,
    *,
    text_column: str = "text",
    max_length: int = 128,
    batch_size: int = 32,
):
    """Prediksi label untuk setiap baris `df`.

    Mengembalikan tuple (y_true, y_pred, y_proba) sebagai numpy array.
    `y_true` di-encode dari kolom label kanonik via LABEL2ID. Inferensi
    dilakukan batch-per-batch tanpa gradien.
    """
    import numpy as np
    import torch

    texts = df[text_column].astype(str).tolist()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    all_logits: list = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = tokenizer(
                batch,
                padding="max_length",
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            ).to(device)
            logits = model(**enc).logits
            all_logits.append(logits.cpu().numpy())

    logits = np.concatenate(all_logits, axis=0)
    y_proba = _softmax(logits)
    y_pred = y_proba.argmax(axis=-1)
    y_true = df["label"].map(LABEL2ID).to_numpy()
    return y_true, y_pred, y_proba


def evaluate_test_set(
    *,
    data_cfg: DataConfig | None = None,
    model_dir: str | Path = BEST_MODEL_DIR,
    cv_summary: dict | None = None,
    overfitting: dict | None = None,
    max_length: int = 128,
    write: bool = True,
) -> dict:
    """Evaluasi end-to-end best model pada test set (clean_test.csv).

    Memuat model, menjalankan inferensi, lalu menulis evaluation_final.json.
    `cv_summary` & `overfitting` opsional disisipkan ke laporan (lihat
    cross_val_report.summarize_cv & metrics.overfitting_gap).
    """
    from src.modeling.data import load_clean_split

    data_cfg = data_cfg or DataConfig()
    test_df = load_clean_split("test", data_cfg)

    model, tokenizer = load_best_model(model_dir)
    y_true, y_pred, _ = predict_split(
        test_df,
        model,
        tokenizer,
        text_column=data_cfg.text_column,
        max_length=max_length,
    )
    return build_evaluation_report(
        y_true,
        y_pred,
        cv_summary=cv_summary,
        overfitting=overfitting,
        write=write,
    )


def _softmax(logits):
    """Softmax stabil per-baris (tanpa dependency torch)."""
    import numpy as np

    shifted = logits - logits.max(axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=-1, keepdims=True)
