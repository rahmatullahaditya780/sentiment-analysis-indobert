"""
Fase 5 — Visualisasi evaluasi (FR-5.5 & FR-5.6).

Dua artefak gambar wajib:
- Confusion matrix (heatmap) -> outputs/charts/confusion_matrix.png
- Learning curve (training vs validation loss per epoch) -> learning_curve.png

`matplotlib` diimpor lazy (backend non-interaktif "Agg") agar aman dijalankan
headless di Colab/CI. Fungsi mengembalikan path file yang ditulis.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.evaluation.config import (
    CLASS_NAMES,
    CONFUSION_MATRIX_PNG,
    LEARNING_CURVE_PNG,
    TRAINER_STATE_JSON,
    TRAINING_LOG_CSV,
    ensure_output_dirs,
)


def plot_confusion_matrix(
    matrix,
    *,
    class_names: list[str] | None = None,
    normalize: bool = False,
    out_path: str | Path = CONFUSION_MATRIX_PNG,
    title: str = "Confusion Matrix — Test Set",
) -> Path:
    """Render confusion matrix sebagai heatmap beranotasi (FR-5.5).

    `matrix`: list-of-list / array (baris aktual, kolom prediksi) urutan id.
    `normalize=True` menampilkan proporsi per baris (recall per kelas).
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    cm = np.asarray(matrix, dtype=float)
    names = class_names or CLASS_NAMES
    if normalize:
        row_sums = cm.sum(axis=1, keepdims=True)
        cm = np.divide(cm, row_sums, where=row_sums != 0)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.set_yticklabels(names)
    ax.set_xlabel("Prediksi")
    ax.set_ylabel("Aktual")
    ax.set_title(title)

    fmt = ".2f" if normalize else "d"
    thresh = cm.max() / 2 if cm.size else 0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            ax.text(
                j,
                i,
                format(val if normalize else int(val), fmt),
                ha="center",
                va="center",
                color="white" if val > thresh else "black",
            )

    fig.tight_layout()
    out_path = Path(out_path)
    ensure_output_dirs()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_learning_curve(
    *,
    epochs: list | None = None,
    train_loss: list | None = None,
    val_loss: list | None = None,
    out_path: str | Path = LEARNING_CURVE_PNG,
    title: str = "Learning Curve — Training vs Validation Loss",
) -> Path:
    """Plot training loss vs validation loss per epoch (FR-5.6).

    Jika seri tidak diberikan, dibaca otomatis via `load_loss_history()`
    (trainer_state.json best model, fallback training_log.csv).
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if train_loss is None or val_loss is None:
        history = load_loss_history()
        epochs = history["epochs"]
        train_loss = history["train_loss"]
        val_loss = history["val_loss"]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(epochs, train_loss, marker="o", label="Training loss")
    ax.plot(epochs, val_loss, marker="s", label="Validation loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    out_path = Path(out_path)
    ensure_output_dirs()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def load_loss_history() -> dict:
    """Baca riwayat loss per epoch untuk learning curve.

    Prioritas: `trainer_state.json` (log_history HF Trainer) di best model;
    fallback ke `training_log.csv` (kolom: epoch, train_loss, val_loss).
    Mengembalikan dict {epochs, train_loss, val_loss}.
    """
    if TRAINER_STATE_JSON.exists():
        return _history_from_trainer_state(TRAINER_STATE_JSON)
    if TRAINING_LOG_CSV.exists():
        return _history_from_csv(TRAINING_LOG_CSV)
    raise FileNotFoundError(
        "Riwayat loss tidak ditemukan. Butuh salah satu dari: "
        f"{TRAINER_STATE_JSON} atau {TRAINING_LOG_CSV} (ekspor dari Colab)."
    )


def _history_from_trainer_state(path: Path) -> dict:
    """Ekstrak train/eval loss per epoch dari log_history HF Trainer."""
    state = json.loads(Path(path).read_text(encoding="utf-8"))
    log = state.get("log_history", [])
    by_epoch: dict[float, dict] = {}
    for entry in log:
        epoch = entry.get("epoch")
        if epoch is None:
            continue
        bucket = by_epoch.setdefault(epoch, {})
        if "loss" in entry:
            bucket["train_loss"] = entry["loss"]
        if "eval_loss" in entry:
            bucket["val_loss"] = entry["eval_loss"]
    epochs = sorted(e for e, v in by_epoch.items() if "train_loss" in v and "val_loss" in v)
    return {
        "epochs": [round(e, 2) for e in epochs],
        "train_loss": [by_epoch[e]["train_loss"] for e in epochs],
        "val_loss": [by_epoch[e]["val_loss"] for e in epochs],
    }


def _history_from_csv(path: Path) -> dict:
    """Baca training_log.csv (kolom: epoch, train_loss, val_loss)."""
    import pandas as pd

    df = pd.read_csv(path).sort_values("epoch")
    return {
        "epochs": df["epoch"].tolist(),
        "train_loss": df["train_loss"].tolist(),
        "val_loss": df["val_loss"].tolist(),
    }
