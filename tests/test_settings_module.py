"""
Fase 8 — Unit test Module 5 (apply_filters murni).

Render sidebar membungkus widget Streamlit (validasi manual); di sini hanya
logika filter kategori/tanggal/confidence yang diuji.
"""

from __future__ import annotations

import pandas as pd

from src.dashboard.settings_module import apply_filters

_DF = pd.DataFrame(
    {
        "review_text": ["a", "b", "c", "d"],
        "predicted_label": ["positive", "negative", "positive", "neutral"],
        "confidence_score": [0.99, 0.60, 0.85, 0.40],
        "product_category": ["serum", "serum", "pelembap", "pelembap"],
        "date_review": ["2025-01-10", "2025-02-15", "2025-03-20", "2025-04-25"],
    }
)


def test_tanpa_filter_mengembalikan_semua():
    out = apply_filters(_DF)
    assert len(out) == 4


def test_filter_kategori():
    out = apply_filters(_DF, categories=["serum"])
    assert set(out["product_category"]) == {"serum"}
    assert len(out) == 2


def test_filter_confidence():
    out = apply_filters(_DF, min_confidence=0.8)
    assert len(out) == 2
    assert (out["confidence_score"] >= 0.8).all()


def test_filter_rentang_tanggal_inklusif():
    import datetime as dt

    out = apply_filters(_DF, date_range=(dt.date(2025, 2, 1), dt.date(2025, 3, 31)))
    assert len(out) == 2  # Feb & Mar


def test_filter_gabungan():
    out = apply_filters(_DF, categories=["serum"], min_confidence=0.8)
    assert len(out) == 1
    assert out.iloc[0]["review_text"] == "a"


def test_tidak_memutasi_input():
    _ = apply_filters(_DF, categories=["serum"])
    assert len(_DF) == 4


def test_kolom_absen_diabaikan():
    df = pd.DataFrame({"review_text": ["a"], "predicted_label": ["positive"]})
    out = apply_filters(df, categories=["serum"], min_confidence=0.9)
    assert len(out) == 1  # filter diabaikan karena kolom tak ada
