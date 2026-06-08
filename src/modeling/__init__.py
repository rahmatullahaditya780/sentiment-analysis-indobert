"""Paket modeling — fine-tuning IndoBERT (Fase 4) & inference engine (Fase 6).

Hanya simbol ringan (config, data, kelas inference) yang diekspor di level
paket; fungsi training (trainer/hyperparameter_search/cross_validation) dan
inferensi (inference) meng-impor torch/transformers secara lazy, jadi impor
langsung dari submodul-nya saat dibutuhkan (umumnya di notebook Colab).
"""

from src.modeling.config import (
    BASELINE_CONFIG,
    ID2LABEL,
    LABEL2ID,
    NUM_LABELS,
    DataConfig,
    SearchSpace,
    TrainingConfig,
    ensure_output_dirs,
)
from src.modeling.data import (
    compute_class_weights,
    encode_labels,
    label_distribution,
    load_clean_split,
    stratified_subset,
)
from src.modeling.inference import (
    OMORFO_PREDICTIONS_CSV,
    PredictionResult,
    SentimentPredictor,
    analyze_omorfo_reviews,
)

__all__ = [
    "BASELINE_CONFIG",
    "ID2LABEL",
    "LABEL2ID",
    "NUM_LABELS",
    "DataConfig",
    "SearchSpace",
    "TrainingConfig",
    "ensure_output_dirs",
    "compute_class_weights",
    "encode_labels",
    "label_distribution",
    "load_clean_split",
    "stratified_subset",
    "OMORFO_PREDICTIONS_CSV",
    "PredictionResult",
    "SentimentPredictor",
    "analyze_omorfo_reviews",
]
