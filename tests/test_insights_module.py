"""
Fase 8 — Unit test Module 7 (insight analitik murni).

Cakupan: deteksi mismatch rating<->sentimen (coerce, kolom absen), ringkasan
mismatch, ringkasan kondisi per produk (konsisten rule engine Fase 7), dan
contoh ulasan representatif (urut confidence).
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.dashboard.insights_module import (
    MISMATCH_NEG,
    MISMATCH_POS,
    detect_mismatch,
    mismatch_summary,
    summarize_by_product,
    top_examples,
)
from src.recommendation.rule_engine import MarketingConditionClassifier

_DF = pd.DataFrame(
    {
        "review_text": [
            "bagus tapi pengiriman lama sekali kecewa",  # bintang 5, negatif
            "mantap sesuai deskripsi",  # bintang 5, positif (wajar)
            "lumayan",  # bintang 3, netral (diabaikan)
            "ternyata bagus juga",  # bintang 1, positif (mismatch)
            "jelek banget",  # bintang 1, negatif (wajar)
        ],
        "rating": [5, "5", 3, 1, 1],  # campur int & string -> wajib coerce
        "predicted_label": ["negative", "positive", "neutral", "positive", "negative"],
        "confidence_score": [0.97, 0.99, 0.55, 0.80, 0.90],
        "product_name": ["Serum A", "Serum A", "Serum A", "Sabun B", "Sabun B"],
    }
)


# ── detect_mismatch ───────────────────────────────────────────────────────────
def test_mismatch_rating_tinggi_sentimen_negatif():
    out = detect_mismatch(_DF)
    neg = out[out["mismatch_type"] == MISMATCH_NEG]
    assert len(neg) == 1
    assert neg.iloc[0]["review_text"].startswith("bagus tapi")


def test_mismatch_rating_rendah_sentimen_positif():
    out = detect_mismatch(_DF)
    pos = out[out["mismatch_type"] == MISMATCH_POS]
    assert len(pos) == 1
    assert pos.iloc[0]["review_text"] == "ternyata bagus juga"


def test_mismatch_rating_tengah_diabaikan():
    out = detect_mismatch(_DF)
    assert "lumayan" not in set(out["review_text"])
    assert len(out) == 2


def test_mismatch_rating_string_dicoerce():
    df = pd.DataFrame(
        {"rating": ["4", "x"], "predicted_label": ["negative", "negative"]}
    )
    out = detect_mismatch(df)
    assert len(out) == 1  # "x" -> NaN -> diabaikan


def test_mismatch_kolom_absen_kosong():
    df = pd.DataFrame({"predicted_label": ["negative"]})
    out = detect_mismatch(df)
    assert out.empty
    assert "mismatch_type" in out.columns


# ── mismatch_summary ──────────────────────────────────────────────────────────
def test_summary_hitung_rate():
    s = mismatch_summary(_DF)
    assert s["n_rated"] == 5
    assert s["n_mismatch"] == 2
    assert s["rate"] == pytest.approx(0.4)
    assert s["counts"] == {MISMATCH_NEG: 1, MISMATCH_POS: 1}


def test_summary_tanpa_kolom_rating():
    s = mismatch_summary(pd.DataFrame({"predicted_label": ["positive"]}))
    assert s == {
        "n_rated": 0,
        "n_mismatch": 0,
        "rate": 0.0,
        "counts": {MISMATCH_NEG: 0, MISMATCH_POS: 0},
    }


# ── summarize_by_product ──────────────────────────────────────────────────────
def test_per_produk_none_tanpa_kolom():
    assert summarize_by_product(pd.DataFrame({"predicted_label": ["positive"]})) is None


def test_per_produk_dua_baris_proporsi_dan_kondisi():
    out = summarize_by_product(_DF)
    assert out is not None
    assert len(out) == 2
    serum = out[out["product"] == "Serum A"].iloc[0]
    assert serum["n_reviews"] == 3
    assert serum["positive"] + serum["neutral"] + serum["negative"] == pytest.approx(
        1.0
    )
    # Kondisi wajib identik dengan rule engine pada subset yang sama.
    subset = _DF[_DF["product_name"] == "Serum A"]
    expected = MarketingConditionClassifier().classify(subset).condition
    assert serum["condition"] == expected


def test_per_produk_min_reviews():
    out = summarize_by_product(_DF, min_reviews=3)
    assert list(out["product"]) == ["Serum A"]  # Sabun B (n=2) tersembunyi


# ── top_examples ──────────────────────────────────────────────────────────────
def test_contoh_urut_confidence_menurun():
    out = top_examples(_DF, label="positive", n=2)
    assert list(out["confidence_score"]) == [0.99, 0.80]


def test_contoh_n_melebihi_tersedia():
    out = top_examples(_DF, label="neutral", n=10)
    assert len(out) == 1


def test_contoh_label_tidak_ada():
    assert top_examples(_DF, label="tidak_ada").empty
