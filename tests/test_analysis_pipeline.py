"""
Fase 8 — Unit test glue pipeline dashboard (normalisasi input).

Hanya menguji `normalize_input` (murni pandas, tanpa torch). Orkestrasi penuh
`run_analysis` (yang memuat IndoBERT) divalidasi terpisah secara manual karena
membutuhkan model ~500MB — di luar cakupan unit test cepat.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.dashboard.analysis_pipeline import STANDARD_COLUMNS, normalize_input


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
