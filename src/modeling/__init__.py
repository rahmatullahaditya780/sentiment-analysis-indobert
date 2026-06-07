"""Paket modeling Fase 4 — fine-tuning IndoBERT (training, search, CV).

Hanya simbol ringan (config & data) yang diekspor di level paket; fungsi
training (trainer/hyperparameter_search/cross_validation) meng-impor
torch/transformers secara lazy, jadi impor langsung dari submodul-nya saat
dibutuhkan (umumnya di notebook Colab).
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
]
