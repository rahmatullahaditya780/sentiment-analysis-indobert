"""
Fase 5 — Perhitungan metrik evaluasi (FR-5.1 s/d FR-5.5).

Fungsi murni: menerima label & prediksi (array/list of int id) lalu
mengembalikan dict metrik. Tidak memuat model — orkestrasi inferensi ada di
`evaluator.py`. `sklearn` diimpor lazy agar modul tetap ringan saat di-import.

Metrik UTAMA gate: macro F1 (FR-5.4, target >= 0.85).
"""

from __future__ import annotations

import json

from src.evaluation.config import (
    CLASS_NAMES,
    EVALUATION_FINAL_JSON,
    MAX_OVERFITTING_GAP,
    NUM_LABELS,
    ensure_output_dirs,
)


def compute_classification_metrics(y_true, y_pred) -> dict:
    """Hitung accuracy + precision/recall/F1 macro (FR-5.1 s/d FR-5.4).

    `y_true`/`y_pred`: iterable id kelas (0..NUM_LABELS-1).
    Mengembalikan dict dengan kunci: accuracy, precision_macro,
    recall_macro, f1_macro (semua float).
    """
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision), 4),
        "recall_macro": round(float(recall), 4),
        "f1_macro": round(float(f1), 4),
    }


def per_class_report(y_true, y_pred) -> dict:
    """Precision/recall/F1/support per kelas (untuk audit ketidakseimbangan).

    Kunci dict adalah nama kelas kanonik (positive/negative/neutral).
    """
    from sklearn.metrics import precision_recall_fscore_support

    labels = list(range(NUM_LABELS))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average=None, zero_division=0
    )
    report: dict[str, dict] = {}
    for idx, name in enumerate(CLASS_NAMES):
        report[name] = {
            "precision": round(float(precision[idx]), 4),
            "recall": round(float(recall[idx]), 4),
            "f1": round(float(f1[idx]), 4),
            "support": int(support[idx]),
        }
    return report


def confusion_matrix_counts(y_true, y_pred) -> list[list[int]]:
    """Confusion matrix sebagai list-of-list (FR-5.5).

    Baris = kelas aktual, kolom = kelas prediksi, urutan id 0..N-1
    (lihat CLASS_NAMES). Cocok untuk JSON & input visualizer.
    """
    from sklearn.metrics import confusion_matrix

    cm = confusion_matrix(y_true, y_pred, labels=list(range(NUM_LABELS)))
    return cm.astype(int).tolist()


def overfitting_gap(train_f1: float, val_f1: float) -> dict:
    """Selisih macro F1 train vs validation (target gap <= 5%).

    Mengembalikan dict: train_f1, val_f1, gap, passed.
    """
    gap = round(abs(float(train_f1) - float(val_f1)), 4)
    return {
        "train_f1_macro": round(float(train_f1), 4),
        "val_f1_macro": round(float(val_f1), 4),
        "gap": gap,
        "passed": gap <= MAX_OVERFITTING_GAP,
    }


def build_evaluation_report(
    y_true,
    y_pred,
    *,
    cv_summary: dict | None = None,
    overfitting: dict | None = None,
    extra: dict | None = None,
    write: bool = True,
) -> dict:
    """Rakit laporan evaluasi final dan (opsional) tulis ke JSON.

    Menggabungkan metrik test set, laporan per-kelas, confusion matrix, dan —
    bila tersedia — ringkasan 5-fold CV (Fase 4) serta cek overfitting.
    Output: `outputs/reports/evaluation_final.json` (deliverable Checkpoint 5).
    """
    report: dict = {
        "metrics": compute_classification_metrics(y_true, y_pred),
        "per_class": per_class_report(y_true, y_pred),
        "confusion_matrix": {
            "labels": CLASS_NAMES,
            "matrix": confusion_matrix_counts(y_true, y_pred),
        },
        "n_test_samples": int(len(y_true)),
    }
    if cv_summary is not None:
        report["cross_validation"] = cv_summary
    if overfitting is not None:
        report["overfitting"] = overfitting
    if extra:
        report.update(extra)

    if write:
        ensure_output_dirs()
        EVALUATION_FINAL_JSON.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    return report
