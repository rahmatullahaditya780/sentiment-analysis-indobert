"""
Fase 6 — Sentiment Inference Engine.

Engine inferensi real-time (teks tunggal) & batch (CSV / hasil Shopee Open
Platform API) yang memuat best model Fase 4 dari `models/best_model/` dan
menghasilkan label sentimen + confidence score + prediction time.

Alur (planning/fase-06-inference-engine.md):

    Input (teks tunggal / batch CSV / hasil API)
      -> Preprocessing Pipeline (case fold -> clean)   [identik dengan training]
      -> Tokenisasi IndoBERT (max_length=128)
      -> IndoBERT (models/best_model/)
      -> Softmax -> label + confidence score
      -> Output: label, confidence, prediction_time

PENTING: preprocessing saat inferensi WAJIB identik dengan saat training. Best
model dilatih atas `clean_*.csv` yang sudah melewati `preprocess_text` (case
folding + cleaning regex, TANPA stemming/stopword). Karena itu engine ini
menerapkan `preprocess_text` yang sama atas setiap input mentah sebelum
tokenisasi — lihat src/preprocessing/cleaner.py.

Strategi impor
--------------
- pandas dipakai langsung (ringan, jalan lokal).
- `torch`/`transformers` di-impor LAZY di dalam method yang membutuhkannya,
  supaya modul tetap bisa diimpor lokal untuk inspeksi/unit test tanpa
  dependency berat. Inferensi nyata berjalan di lingkungan dengan model
  ter-load (lokal CPU cukup untuk batch ±1.200 ulasan, atau Colab GPU).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.modeling.config import (
    BEST_MODEL_DIR,
    DEFAULT_MAX_LENGTH,
    ID2LABEL,
    REPORTS_DIR,
)
from src.preprocessing.cleaner import preprocess_text

# ── Output standar Fase 6 (deliverable Checkpoint 6) ──────────────────────────
OMORFO_PREDICTIONS_CSV = REPORTS_DIR / "omorfo_predictions.csv"

# Kolom default untuk input batch (selaras template OmorfoShop & dashboard).
DEFAULT_TEXT_COLUMN = "review_text"


@dataclass
class PredictionResult:
    """Hasil prediksi satu teks (FR-6.1, FR-6.2, FR-6.4)."""

    text: str
    label: str
    confidence: float
    prediction_time: float  # detik
    # Probabilitas per kelas {label: prob} — berguna untuk dashboard & audit.
    scores: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "predicted_label": self.label,
            "confidence_score": round(self.confidence, 4),
            "prediction_time": round(self.prediction_time, 6),
            "scores": {k: round(v, 4) for k, v in self.scores.items()},
        }


class SentimentPredictor:
    """Engine inferensi sentimen berbasis best model IndoBERT (Fase 4).

    Contoh
    ------
    >>> predictor = SentimentPredictor().load()
    >>> res = predictor.predict("barangnya bagus banget, pengiriman cepat")
    >>> res.label, res.confidence
    ('positive', 0.98)

    >>> df = predictor.predict_batch(reviews_df)  # kolom 'review_text'
    >>> df[["review_text", "predicted_label", "confidence_score"]]
    """

    def __init__(
        self,
        model_dir: str | Path = BEST_MODEL_DIR,
        *,
        max_length: int = DEFAULT_MAX_LENGTH,
        device: str | None = None,
    ) -> None:
        self.model_dir = Path(model_dir)
        self.max_length = max_length
        self._device = device  # None -> auto-deteksi saat load
        self._model = None
        self._tokenizer = None
        self._id2label: dict[int, str] = ID2LABEL

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def load(self) -> "SentimentPredictor":
        """Muat best model + tokenizer dari `model_dir`. Set mode eval.

        Pemetaan id->label diambil dari `config.json` model (sumber kebenaran),
        dengan fallback ke `ID2LABEL` Fase 4. Keduanya seharusnya identik
        (urutan kanonik alfabetis: negative=0, neutral=1, positive=2).
        """
        try:
            import torch
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )
        except ImportError as exc:  # pragma: no cover - tergantung environment
            raise ImportError(
                "Paket `torch`/`transformers` belum terpasang. Inferensi butuh "
                "keduanya: pip install torch transformers"
            ) from exc

        if not self.model_dir.exists():
            raise FileNotFoundError(
                f"Best model tidak ditemukan: {self.model_dir}. Selesaikan "
                "training Fase 4 dan letakkan artefak di models/best_model/."
            )

        self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
        self._model = AutoModelForSequenceClassification.from_pretrained(
            str(self.model_dir)
        )
        self._model.eval()

        if self._device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model.to(self._device)

        # Gunakan pemetaan label milik model bila tersedia & lengkap.
        cfg_id2label = getattr(self._model.config, "id2label", None)
        if cfg_id2label:
            self._id2label = {int(k): v for k, v in cfg_id2label.items()}

        return self

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self.load()
        return self._tokenizer

    @property
    def device(self) -> str:
        if self._device is None:
            self.load()
        return self._device

    # ── Inti inferensi ────────────────────────────────────────────────────────
    def _predict_proba(self, texts: list[str], batch_size: int = 32, progress_cb=None):
        """Jalankan forward pass batch-per-batch -> array probabilitas (N, C).

        Teks diasumsikan SUDAH dibersihkan (`preprocess_text`). Mengembalikan
        numpy array float (n_texts, num_labels).

        `progress_cb` (opsional): callable(done:int, total:int) dipanggil setelah
        tiap batch — dipakai dashboard Fase 8 untuk progress bar inferensi.
        Default None (kompatibel mundur).
        """
        import numpy as np
        import torch

        model = self.model  # memicu load() bila perlu
        tokenizer = self.tokenizer
        device = self.device

        total = len(texts)
        all_proba: list = []
        with torch.no_grad():
            for start in range(0, total, batch_size):
                batch = texts[start : start + batch_size]
                enc = tokenizer(
                    batch,
                    padding="max_length",
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt",
                ).to(device)
                logits = model(**enc).logits
                proba = torch.softmax(logits, dim=-1)
                all_proba.append(proba.cpu().numpy())
                if progress_cb is not None:
                    progress_cb(min(start + batch_size, total), total)

        if not all_proba:
            return np.empty((0, len(self._id2label)), dtype=float)
        return np.concatenate(all_proba, axis=0)

    def predict(self, text: str) -> PredictionResult:
        """Prediksi sentimen satu teks mentah (real-time, FR-6.1/6.2/6.4)."""
        clean = preprocess_text(text)
        start = time.perf_counter()
        proba = self._predict_proba([clean])[0]
        elapsed = time.perf_counter() - start

        pred_id = int(proba.argmax())
        scores = {self._id2label[i]: float(p) for i, p in enumerate(proba)}
        return PredictionResult(
            text=text,
            label=self._id2label[pred_id],
            confidence=float(proba[pred_id]),
            prediction_time=elapsed,
            scores=scores,
        )

    def predict_batch(
        self,
        data: pd.DataFrame | list[str],
        *,
        text_column: str = DEFAULT_TEXT_COLUMN,
        batch_size: int = 32,
        keep_columns: bool = True,
        progress_cb=None,
    ) -> pd.DataFrame:
        """Prediksi batch dari DataFrame atau list teks (FR-6.3).

        Parameter
        ---------
        data : DataFrame berisi kolom `text_column`, atau list[str] teks mentah.
        text_column : nama kolom teks (default 'review_text').
        keep_columns : jika True dan input DataFrame, kolom asli dipertahankan.
        progress_cb : callable(done, total) opsional untuk progress bar (Fase 8).

        Mengembalikan DataFrame dengan tambahan kolom:
        `predicted_label`, `confidence_score`. Total & rata-rata prediction time
        diset sebagai atribut `.attrs` ('total_prediction_time',
        'avg_prediction_time') untuk monitoring (FR-6.4).
        """
        if isinstance(data, pd.DataFrame):
            if text_column not in data.columns:
                raise ValueError(
                    f"Kolom teks '{text_column}' tidak ada. Kolom tersedia: "
                    f"{list(data.columns)}"
                )
            out = data.copy() if keep_columns else data[[text_column]].copy()
            raw_texts = data[text_column].astype(str).tolist()
        else:
            raw_texts = [str(t) for t in data]
            out = pd.DataFrame({text_column: raw_texts})

        clean_texts = [preprocess_text(t) for t in raw_texts]

        start = time.perf_counter()
        proba = self._predict_proba(
            clean_texts, batch_size=batch_size, progress_cb=progress_cb
        )
        elapsed = time.perf_counter() - start

        if len(proba) == 0:
            out["predicted_label"] = []
            out["confidence_score"] = []
        else:
            pred_ids = proba.argmax(axis=-1)
            out["predicted_label"] = [self._id2label[int(i)] for i in pred_ids]
            out["confidence_score"] = [
                round(float(proba[row, idx]), 4) for row, idx in enumerate(pred_ids)
            ]

        out.attrs["total_prediction_time"] = round(elapsed, 4)
        out.attrs["avg_prediction_time"] = (
            round(elapsed / len(raw_texts), 6) if raw_texts else 0.0
        )
        return out


# ── Penerapan ke dataset OmorfoShop (FR-6.5) ──────────────────────────────────
def analyze_omorfo_reviews(
    input_csv: str | Path,
    *,
    predictor: SentimentPredictor | None = None,
    text_column: str = DEFAULT_TEXT_COLUMN,
    output_csv: str | Path = OMORFO_PREDICTIONS_CSV,
    write: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """Terapkan model ke dataset OmorfoShop & hasilkan distribusi sentimen.

    Membaca `input_csv` (mis. data/implementation/omorfo_reviews_*.csv atau hasil
    Shopee Open Platform API yang sudah dinormalisasi), memprediksi tiap ulasan,
    menulis hasil ke `output_csv` (kolom minimal: review_text, predicted_label,
    confidence_score), dan mengembalikan (DataFrame hasil, ringkasan distribusi).

    Ringkasan distribusi dipakai langsung oleh rule-based engine Fase 7.
    """
    input_csv = Path(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(
            f"Dataset OmorfoShop tidak ditemukan: {input_csv}. Sediakan CSV hasil "
            "Shopee API (get_rating) atau gunakan template di data/implementation/."
        )

    df = pd.read_csv(input_csv)
    predictor = predictor or SentimentPredictor().load()
    result = predictor.predict_batch(df, text_column=text_column)

    counts = result["predicted_label"].value_counts()
    total = int(counts.sum())
    distribution = {
        label: {
            "count": int(counts.get(label, 0)),
            "proportion": (
                round(float(counts.get(label, 0)) / total, 4) if total else 0.0
            ),
        }
        for label in ID2LABEL.values()
    }
    summary = {
        "source": str(input_csv),
        "n_reviews": total,
        "distribution": distribution,
        "total_prediction_time": result.attrs.get("total_prediction_time"),
        "avg_prediction_time": result.attrs.get("avg_prediction_time"),
    }

    if write:
        output_csv = Path(output_csv)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_csv, index=False)
        summary["output_csv"] = str(output_csv)

    return result, summary
