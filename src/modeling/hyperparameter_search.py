"""
Fase 4 — Focused random search (FR-4.6).

Tahapan (planning Fase 4):
1. Baseline testing      — konfigurasi baseline (LR 2e-5, BS 16, 3 epoch).
2. Focused random search — 5-8 kombinasi acak dari SearchSpace, dilatih pada
                           30% training set (stratified).
3. Perbandingan          — berdasarkan f1_macro, lalu efisiensi.
4. Pemilihan final       — f1 tertinggi; jika selisih < 1%, pilih paling efisien.

Hasil setiap eksperimen dicatat ke `outputs/reports/hyperparameter_log.csv`.

Impor torch/transformers/datasets bersifat lazy (via trainer & data). Eksekusi
nyata di Google Colab.
"""

from __future__ import annotations

import csv
import random
import time
from pathlib import Path

import pandas as pd

from src.modeling.config import (
    BASELINE_CONFIG,
    HYPERPARAM_LOG_CSV,
    DataConfig,
    SearchSpace,
    TrainingConfig,
    ensure_output_dirs,
)
from src.modeling.data import (
    build_hf_dataset,
    compute_class_weights,
    stratified_subset,
)
from src.modeling.trainer import train_model

_LOG_FIELDS = [
    "run_name",
    "learning_rate",
    "batch_size",
    "num_epochs",
    "f1_macro",
    "accuracy",
    "eval_loss",
    "train_seconds",
]


def sample_configs(space: SearchSpace, seed: int = 42) -> list[TrainingConfig]:
    """Hasilkan n_trials konfigurasi acak unik dari ruang pencarian.

    Deterministik via `seed`. Baseline TIDAK termasuk di sini (dievaluasi
    terpisah sebagai pembanding).
    """
    rng = random.Random(seed)
    configs: list[TrainingConfig] = []
    seen: set[tuple] = set()
    # Batasi percobaan agar tak loop tak terbatas bila ruang kecil.
    attempts = 0
    while len(configs) < space.n_trials and attempts < space.n_trials * 20:
        attempts += 1
        cfg = space.sample(rng)
        key = (cfg.learning_rate, cfg.batch_size, cfg.num_epochs)
        if key in seen:
            continue
        seen.add(key)
        cfg.run_name = f"search-{len(configs) + 1:02d}"
        configs.append(cfg)
    return configs


def _row_from_result(config: TrainingConfig, metrics: dict, train_seconds: float) -> dict:
    return {
        "run_name": config.run_name,
        "learning_rate": config.learning_rate,
        "batch_size": config.batch_size,
        "num_epochs": config.num_epochs,
        "f1_macro": round(metrics.get("eval_f1_macro", float("nan")), 4),
        "accuracy": round(metrics.get("eval_accuracy", float("nan")), 4),
        "eval_loss": round(metrics.get("eval_loss", float("nan")), 4),
        "train_seconds": round(train_seconds, 1),
    }


def write_log(rows: list[dict], path: Path = HYPERPARAM_LOG_CSV) -> Path:
    """Tulis hasil seluruh eksperimen ke CSV (overwrite)."""
    ensure_output_dirs()
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_LOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def select_best(rows: list[dict], tolerance: float = 0.01) -> dict:
    """Pilih baris terbaik: f1_macro tertinggi.

    Jika selisih f1 antar kandidat teratas < tolerance (default 1%),
    pilih yang paling efisien (train_seconds terendah).
    """
    if not rows:
        raise ValueError("Tidak ada hasil eksperimen untuk dipilih.")
    best_f1 = max(r["f1_macro"] for r in rows)
    contenders = [r for r in rows if best_f1 - r["f1_macro"] < tolerance]
    return min(contenders, key=lambda r: r["train_seconds"])


def run_focused_search(
    train_df: pd.DataFrame,
    eval_df: pd.DataFrame,
    space: SearchSpace | None = None,
    data_cfg: DataConfig | None = None,
    work_dir: str | Path = "outputs/_search",
    seed: int = 42,
    include_baseline: bool = True,
) -> tuple[list[dict], dict]:
    """Jalankan baseline + focused random search pada subset 30%.

    Mengembalikan (rows_log, best_row). Menulis hyperparameter_log.csv.
    Dipanggil dari notebook Colab dengan dataframe bersih hasil Fase 3.
    """
    space = space or SearchSpace()
    data_cfg = data_cfg or DataConfig()
    work_dir = Path(work_dir)

    # Subset stratified 30% untuk pencarian (FR-4.6).
    search_df = stratified_subset(
        train_df, frac=space.search_subset_frac, label_column=data_cfg.label_column, seed=seed
    )
    class_weights = compute_class_weights(search_df, data_cfg.label_column)
    eval_ds = build_hf_dataset(eval_df, text_column=data_cfg.text_column)

    configs: list[TrainingConfig] = []
    if include_baseline:
        configs.append(BASELINE_CONFIG)
    configs.extend(sample_configs(space, seed=seed))

    rows: list[dict] = []
    for cfg in configs:
        train_ds = build_hf_dataset(search_df, text_column=data_cfg.text_column)
        start = time.perf_counter()
        _, metrics = train_model(
            cfg,
            train_dataset=train_ds,
            eval_dataset=eval_ds,
            class_weights=class_weights,
            output_dir=work_dir / cfg.run_name,
        )
        elapsed = time.perf_counter() - start
        rows.append(_row_from_result(cfg, metrics, elapsed))

    write_log(rows)
    best = select_best(rows)
    return rows, best
