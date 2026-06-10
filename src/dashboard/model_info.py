"""
Fase 8 — Sumber kebenaran metrik model untuk tampilan dashboard.

Membaca metrik final dari laporan Fase 5 (`outputs/reports/evaluation_final.json`
dan `cross_validation_report.json`) sehingga angka F1 yang tampil di halaman
Input/Ekspor/Tentang tidak lagi hardcoded dan tak bisa drift dari laporan.

Murni (tanpa Streamlit). Bila file laporan hilang/korup (mis. deployment tanpa
folder outputs), jatuh ke `DEFAULT_METRICS` — dashboard tidak boleh crash.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

from src.modeling.config import CV_REPORT_JSON, REPORTS_DIR

EVALUATION_FINAL_JSON = REPORTS_DIR / "evaluation_final.json"

# Fallback = nilai final Fase 5 (sinkron CLAUDE.md), dipakai bila laporan absen.
DEFAULT_METRICS: dict[str, float] = {
    "f1_macro": 0.9031,
    "cv_mean": 0.9016,
    "cv_std": 0.010,
    "target_f1": 0.85,
}


@functools.lru_cache(maxsize=4)
def load_model_metrics(
    eval_path: str | Path = EVALUATION_FINAL_JSON,
    cv_path: str | Path = CV_REPORT_JSON,
) -> dict[str, float]:
    """Muat metrik model dari laporan evaluasi; fallback ke DEFAULT_METRICS.

    Kunci hasil: f1_macro, cv_mean, cv_std, target_f1. Tiap sumber dibaca
    independen — bila salah satu file rusak, hanya kunci terkait yang memakai
    fallback. Hasil di-cache per proses (laporan tidak berubah saat runtime).
    """
    metrics = dict(DEFAULT_METRICS)

    try:
        data = json.loads(Path(eval_path).read_text(encoding="utf-8"))
        metrics["f1_macro"] = float(data["metrics"]["f1_macro"])
    except (OSError, ValueError, KeyError, TypeError):
        pass

    try:
        data = json.loads(Path(cv_path).read_text(encoding="utf-8"))
        metrics["cv_mean"] = float(data["f1_macro_mean"])
        metrics["cv_std"] = float(data["f1_macro_std"])
    except (OSError, ValueError, KeyError, TypeError):
        pass

    return metrics


def fmt_id(value: float, digits: int = 4) -> str:
    """Format angka desimal gaya Indonesia (koma): 0.9031 -> "0,9031"."""
    return f"{value:.{digits}f}".replace(".", ",")
