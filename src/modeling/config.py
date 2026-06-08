"""
Fase 4 — Konfigurasi training & fine-tuning IndoBERT.

Modul ringan (tanpa torch/transformers) berisi:
- Pemetaan label kanonik <-> id (deterministik, dipakai model & evaluasi).
- `TrainingConfig` — satu set hyperparameter untuk satu eksperimen.
- `SearchSpace` — ruang pencarian focused random search (FR-4.6).
- Lokasi output standar (models/, outputs/reports/, outputs/logs/).

Nilai default mengikuti tabel hyperparameter di
`planning/fase-04-training-fine-tuning.md` dan CLAUDE.md.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.label_harmonizer import CANONICAL_LABELS

# ── Pemetaan label <-> id ─────────────────────────────────────────────────────
# Urutan deterministik (alfabetis) agar id stabil lintas run & lintas mesin.
# Dipakai untuk num_labels model, encoding target, dan dekode prediksi.
LABEL2ID: dict[str, int] = {label: idx for idx, label in enumerate(sorted(CANONICAL_LABELS))}
ID2LABEL: dict[int, str] = {idx: label for label, idx in LABEL2ID.items()}
NUM_LABELS: int = len(LABEL2ID)

# ── Path standar proyek ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
BEST_MODEL_DIR = MODELS_DIR / "best_model"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
LOGS_DIR = PROJECT_ROOT / "outputs" / "logs"

# Nama file output standar (deliverable Checkpoint 4)
HYPERPARAM_LOG_CSV = REPORTS_DIR / "hyperparameter_log.csv"
TRAINING_LOG_CSV = LOGS_DIR / "training_log.csv"
CV_REPORT_JSON = REPORTS_DIR / "cross_validation_report.json"
FINAL_METRICS_JSON = REPORTS_DIR / "phase4_final_metrics.json"

# Model & tokenizer (selaras dengan Fase 3)
DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "indolem/indobert-base-uncased")
DEFAULT_MAX_LENGTH = int(os.getenv("MODEL_MAX_LENGTH", "128"))

# Reproduktibilitas (seragam dengan split Fase 2)
DEFAULT_SEED = 42


@dataclass
class TrainingConfig:
    """Hyperparameter satu eksperimen fine-tuning IndoBERT.

    Default mengikuti konfigurasi baseline planning Fase 4
    (LR 2e-5, batch 16, 3 epoch).
    """

    learning_rate: float = 2e-5
    batch_size: int = 16
    num_epochs: int = 3
    max_length: int = DEFAULT_MAX_LENGTH
    dropout_rate: float = 0.1
    weight_decay: float = 0.01
    warmup_steps: int = 500
    early_stopping_patience: int = 2
    model_name: str = DEFAULT_MODEL_NAME
    seed: int = DEFAULT_SEED
    # Tag bebas untuk membedakan baris di log (mis. "baseline", "search-03").
    run_name: str = "baseline"

    def as_dict(self) -> dict:
        return {
            "run_name": self.run_name,
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "num_epochs": self.num_epochs,
            "max_length": self.max_length,
            "dropout_rate": self.dropout_rate,
            "weight_decay": self.weight_decay,
            "warmup_steps": self.warmup_steps,
            "early_stopping_patience": self.early_stopping_patience,
            "model_name": self.model_name,
            "seed": self.seed,
        }


# Konfigurasi baseline eksplisit (Tahap 1 focused random search).
BASELINE_CONFIG = TrainingConfig(run_name="baseline")


@dataclass
class SearchSpace:
    """Ruang pencarian focused random search (planning Fase 4).

    Sampling dilakukan pada 30% training set untuk 5-8 kombinasi.
    """

    learning_rate: tuple[float, ...] = (1e-5, 2e-5, 3e-5, 5e-5)
    batch_size: tuple[int, ...] = (8, 16, 32)
    num_epochs: tuple[int, ...] = (3, 4, 5)
    # Proporsi training set yang dipakai untuk pencarian (FR-4.6).
    search_subset_frac: float = 0.30
    n_trials: int = 6  # dalam rentang 5-8

    def sample(self, rng) -> TrainingConfig:
        """Ambil satu kombinasi acak sebagai TrainingConfig.

        `rng` adalah instance `random.Random` agar deterministik bila di-seed.
        """
        return TrainingConfig(
            learning_rate=rng.choice(self.learning_rate),
            batch_size=rng.choice(self.batch_size),
            num_epochs=rng.choice(self.num_epochs),
        )


@dataclass
class DataConfig:
    """Kolom & lokasi dataset bersih hasil Fase 3."""

    text_column: str = "text"
    label_column: str = "label"
    processed_dir: Path = field(default=PROCESSED_DIR)
    # Bila True, split "train" memakai clean_train_augmented.csv (hasil
    # back-translation kelas minoritas, lihat src/modeling/augmentation.py).
    # Validation & test TETAP memakai data asli agar evaluasi jujur terhadap
    # distribusi nyata.
    use_augmented_train: bool = False

    def clean_path(self, split: str) -> Path:
        """Path ke clean_{split}.csv (split: train/validation/test).

        Jika `use_augmented_train` aktif, split "train" diarahkan ke
        clean_train_augmented.csv (fallback ke clean_train.csv bila belum ada).
        """
        if split == "train" and self.use_augmented_train:
            aug = self.processed_dir / "clean_train_augmented.csv"
            if aug.exists():
                return aug
        return self.processed_dir / f"clean_{split}.csv"


def ensure_output_dirs() -> None:
    """Pastikan folder output Fase 4 ada (idempoten)."""
    for d in (MODELS_DIR, BEST_MODEL_DIR, REPORTS_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
