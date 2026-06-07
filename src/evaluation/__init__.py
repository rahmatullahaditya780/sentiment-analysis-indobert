"""Paket evaluation Fase 5 — metrik, visualisasi, & ringkasan CV.

Hanya simbol ringan (config, metrik murni, ringkasan CV) yang diekspor di level
paket. Orkestrasi inferensi (`evaluator`) dan plotting (`visualizer`) meng-impor
torch/transformers/matplotlib secara lazy — impor langsung dari submodulnya saat
dibutuhkan (umumnya di notebook Colab).
"""

from src.evaluation.config import (
    CLASS_NAMES,
    CONFUSION_MATRIX_PNG,
    EVALUATION_FINAL_JSON,
    LEARNING_CURVE_PNG,
    MAX_OVERFITTING_GAP,
    TARGET_ACCURACY,
    TARGET_F1_MACRO,
    ensure_output_dirs,
)
from src.evaluation.cross_val_report import summarize_cv
from src.evaluation.metrics import (
    build_evaluation_report,
    compute_classification_metrics,
    confusion_matrix_counts,
    overfitting_gap,
    per_class_report,
)

__all__ = [
    "CLASS_NAMES",
    "CONFUSION_MATRIX_PNG",
    "EVALUATION_FINAL_JSON",
    "LEARNING_CURVE_PNG",
    "MAX_OVERFITTING_GAP",
    "TARGET_ACCURACY",
    "TARGET_F1_MACRO",
    "ensure_output_dirs",
    "summarize_cv",
    "build_evaluation_report",
    "compute_classification_metrics",
    "confusion_matrix_counts",
    "overfitting_gap",
    "per_class_report",
]
