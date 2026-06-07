"""
Fase 5 — Ringkasan 5-fold Cross-Validation (deliverable Checkpoint 5).

CV dijalankan di Fase 4 (`src/modeling/cross_validation.py`) dan hasilnya
tersimpan di `outputs/reports/cross_validation_report.json`. Modul ini hanya
MEMBACA & MERINGKAS report itu (mean F1 +/- std) untuk disisipkan ke laporan
evaluasi final — tidak melatih ulang.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.evaluation.config import CV_REPORT_JSON


def summarize_cv(report_path: str | Path = CV_REPORT_JSON) -> dict:
    """Baca cross_validation_report.json dan kembalikan ringkasannya.

    Mengembalikan dict: n_splits, f1_macro_mean, f1_macro_std, dan daftar
    f1 per fold. Raise FileNotFoundError bila report belum ada (CV Fase 4
    belum dijalankan di Colab).
    """
    report_path = Path(report_path)
    if not report_path.exists():
        raise FileNotFoundError(
            f"Report CV tidak ditemukan: {report_path}. Jalankan 5-fold CV Fase 4 dulu."
        )
    data = json.loads(report_path.read_text(encoding="utf-8"))
    folds = data.get("folds", [])
    return {
        "n_splits": data.get("n_splits", len(folds)),
        "f1_macro_mean": data.get("f1_macro_mean"),
        "f1_macro_std": data.get("f1_macro_std"),
        "f1_per_fold": [f.get("f1_macro") for f in folds],
        "source": str(report_path.name),
    }
