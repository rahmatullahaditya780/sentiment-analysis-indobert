"""
Fase 5 — Konfigurasi evaluasi model.

Modul ringan (tanpa torch/transformers/sklearn) berisi:
- Re-export pemetaan label kanonik <-> id dari Fase 4 (agar urutan kelas pada
  confusion matrix & laporan konsisten dengan training).
- Lokasi artefak input (best model + report Fase 4) dan output Fase 5
  (evaluation_final.json, confusion_matrix.png, learning_curve.png).
- Target gate evaluasi (accuracy & macro F1 >= 85%, gap overfitting <= 5%).

Nilai mengikuti `planning/fase-05-evaluation.md` dan CLAUDE.md.
"""

from __future__ import annotations

from pathlib import Path

# Pemetaan label & path bersama dipinjam dari Fase 4 supaya tidak ada drift.
from src.modeling.config import (  # noqa: F401  (re-export)
    BEST_MODEL_DIR,
    CV_REPORT_JSON,
    FINAL_METRICS_JSON as PHASE4_FINAL_METRICS_JSON,
    ID2LABEL,
    LABEL2ID,
    NUM_LABELS,
    PROCESSED_DIR,
    DataConfig,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"
LOGS_DIR = PROJECT_ROOT / "outputs" / "logs"

# ── Output standar Fase 5 (deliverable Checkpoint 5) ──────────────────────────
EVALUATION_FINAL_JSON = REPORTS_DIR / "evaluation_final.json"
CONFUSION_MATRIX_PNG = CHARTS_DIR / "confusion_matrix.png"
LEARNING_CURVE_PNG = CHARTS_DIR / "learning_curve.png"

# ── Sumber log training untuk learning curve ──────────────────────────────────
# Loss per epoch dicatat HF Trainer di trainer_state.json checkpoint terbaik;
# fallback ke training_log.csv bila diekspor manual dari notebook Colab.
TRAINER_STATE_JSON = BEST_MODEL_DIR / "trainer_state.json"
TRAINING_LOG_CSV = LOGS_DIR / "training_log.csv"

# ── Urutan kelas kanonik (id 0..N-1) untuk label sumbu matriks/laporan ────────
CLASS_NAMES: list[str] = [ID2LABEL[i] for i in range(NUM_LABELS)]

# ── Target gate Fase 5 ────────────────────────────────────────────────────────
TARGET_ACCURACY = 0.85
TARGET_F1_MACRO = 0.85  # metrik UTAMA
MAX_OVERFITTING_GAP = 0.05  # |train_f1 - val_f1| <= 5%


def ensure_output_dirs() -> None:
    """Pastikan folder output Fase 5 ada (idempoten)."""
    for d in (REPORTS_DIR, CHARTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
