"""
Fase 8 — Unit test glue pipeline dashboard (normalisasi input).

Hanya menguji `normalize_input` (murni pandas, tanpa torch). Orkestrasi penuh
`run_analysis` (yang memuat IndoBERT) divalidasi terpisah secara manual karena
membutuhkan model ~500MB — di luar cakupan unit test cepat.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.dashboard.analysis_pipeline import (
    STANDARD_COLUMNS,
    has_predictions,
    normalize_input,
    run_analysis,
)


def test_normalize_menambah_kolom_opsional_yang_absen():
    df = pd.DataFrame({"review_text": ["bagus", "jelek"]})
    out = normalize_input(df)
    for col in STANDARD_COLUMNS:
        assert col in out.columns
    assert len(out) == 2


def test_normalize_membuang_teks_kosong_dan_na():
    df = pd.DataFrame({"review_text": ["bagus", "", "   ", None, "oke"]})
    out = normalize_input(df)
    assert out["review_text"].tolist() == ["bagus", "oke"]


def test_normalize_mempertahankan_kolom_yang_sudah_ada():
    df = pd.DataFrame(
        {
            "review_text": ["bagus"],
            "product_category": ["serum"],
            "rating": [5],
        }
    )
    out = normalize_input(df)
    assert out.loc[0, "product_category"] == "serum"
    assert out.loc[0, "rating"] == 5


def test_normalize_tidak_memutasi_input():
    df = pd.DataFrame({"review_text": ["bagus", ""]})
    _ = normalize_input(df)
    assert len(df) == 2  # input asli utuh


def test_normalize_kolom_teks_hilang_memunculkan_error_informatif():
    df = pd.DataFrame({"ulasan": ["bagus"]})
    with pytest.raises(ValueError, match="Kolom teks 'review_text'"):
        normalize_input(df)


def test_normalize_semua_kosong_memunculkan_error():
    df = pd.DataFrame({"review_text": ["", "   ", None]})
    with pytest.raises(ValueError, match="Tidak ada ulasan valid"):
        normalize_input(df)


def test_normalize_bukan_dataframe_memunculkan_typeerror():
    with pytest.raises(TypeError):
        normalize_input(["bagus", "jelek"])


# ── has_predictions & shortcut pra-prediksi (#2) ──────────────────────────────
def test_has_predictions_true_saat_lengkap():
    df = pd.DataFrame(
        {
            "review_text": ["a", "b"],
            "predicted_label": ["positive", "negative"],
            "confidence_score": [0.9, 0.8],
        }
    )
    assert has_predictions(df) is True


def test_has_predictions_false_saat_kolom_absen():
    df = pd.DataFrame({"review_text": ["a"], "predicted_label": ["positive"]})
    assert has_predictions(df) is False  # tanpa confidence_score


def test_has_predictions_false_saat_label_kosong():
    df = pd.DataFrame(
        {
            "review_text": ["a", "b"],
            "predicted_label": ["positive", None],
            "confidence_score": [0.9, 0.8],
        }
    )
    assert has_predictions(df) is False


def test_run_analysis_melewati_inferensi_saat_berlabel():
    # predictor=None & tanpa torch: jika shortcut bekerja, model tak pernah dimuat.
    df = pd.DataFrame(
        {
            "review_text": ["bagus", "jelek", "biasa"],
            "predicted_label": ["positive", "negative", "neutral"],
            "confidence_score": [0.99, 0.95, 0.70],
        }
    )
    result = run_analysis(df, predictor=None)
    assert result.inference_skipped is True
    assert result.n_reviews == 3
    assert result.recommendation.condition  # rule engine tetap jalan
