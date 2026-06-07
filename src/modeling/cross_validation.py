"""
Fase 4 — 5-Fold Stratified Cross-Validation (FR-4.7).

Setelah konfigurasi final dipilih dari focused random search, konfigurasi itu
divalidasi dengan 5-fold stratified CV pada FULL training set untuk mengukur
stabilitas (mean macro F1 +/- std dev).

Output: `outputs/reports/cross_validation_report.json`.

Impor torch/transformers/datasets/sklearn bersifat lazy. Eksekusi nyata di
Google Colab.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.modeling.config import (
    CV_REPORT_JSON,
    DEFAULT_SEED,
    DataConfig,
    TrainingConfig,
    ensure_output_dirs,
)
from src.modeling.data import build_hf_dataset, compute_class_weights
from src.modeling.trainer import train_model


def run_cross_validation(
    train_df: pd.DataFrame,
    config: TrainingConfig,
    n_splits: int = 5,
    data_cfg: DataConfig | None = None,
    work_dir: str | Path = "outputs/_cv",
    seed: int = DEFAULT_SEED,
    report_path: Path = CV_REPORT_JSON,
) -> dict:
    """Jalankan 5-fold stratified CV memakai `config` final.

    Mengembalikan dict report (mean/std f1_macro per fold) dan menulisnya ke
    `report_path`. Setiap fold: train di k-1 lipatan, validasi di sisanya.
    """
    import numpy as np
    from sklearn.model_selection import StratifiedKFold

    data_cfg = data_cfg or DataConfig()
    work_dir = Path(work_dir)

    X = train_df.reset_index(drop=True)
    y = X[data_cfg.label_column].to_numpy()
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    fold_scores: list[dict] = []
    for fold, (tr_idx, va_idx) in enumerate(skf.split(X, y), start=1):
        tr_df = X.iloc[tr_idx]
        va_df = X.iloc[va_idx]

        class_weights = compute_class_weights(tr_df, data_cfg.label_column)
        tr_ds = build_hf_dataset(tr_df, text_column=data_cfg.text_column)
        va_ds = build_hf_dataset(va_df, text_column=data_cfg.text_column)

        _, metrics = train_model(
            config,
            train_dataset=tr_ds,
            eval_dataset=va_ds,
            class_weights=class_weights,
            output_dir=work_dir / f"fold{fold}",
        )
        fold_scores.append(
            {
                "fold": fold,
                "f1_macro": round(float(metrics.get("eval_f1_macro", float("nan"))), 4),
                "accuracy": round(float(metrics.get("eval_accuracy", float("nan"))), 4),
            }
        )

    f1_values = [s["f1_macro"] for s in fold_scores]
    report = {
        "config": config.as_dict(),
        "n_splits": n_splits,
        "seed": seed,
        "folds": fold_scores,
        "f1_macro_mean": round(float(np.mean(f1_values)), 4),
        "f1_macro_std": round(float(np.std(f1_values)), 4),
    }

    ensure_output_dirs()
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
