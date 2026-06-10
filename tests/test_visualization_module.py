"""
Fase 8 — Unit test Module 4 (frekuensi word cloud + distribusi kategori).

Menguji helper murni: `build_frequencies` (penyaringan stopword/pendek) dan
`build_category_distribution` (figure & penanganan kolom absen). Render gambar
word cloud divalidasi manual saat menjalankan dashboard.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.dashboard.visualization_module import (
    build_category_distribution,
    build_frequencies,
)


def test_frequencies_membuang_stopword_dan_kata_pendek():
    texts = ["produk ini bagus bagus", "yang oke di toko"]
    freq = build_frequencies(texts)
    # 'ini','yang','di','produk','toko' = stopword; 'oke' < 3? (3 huruf -> lolos)
    assert "bagus" in freq and freq["bagus"] == 2
    assert "ini" not in freq
    assert "yang" not in freq
    assert "produk" not in freq


def test_frequencies_abaikan_non_string():
    freq = build_frequencies(["bagus mantap", None, 123, float("nan")])
    assert freq.get("bagus") == 1
    assert freq.get("mantap") == 1


def test_frequencies_kosong_saat_semua_tersaring():
    assert build_frequencies(["yang di ke", "aku kamu"]) == {}


def test_category_distribution_none_tanpa_kolom():
    df = pd.DataFrame({"predicted_label": ["positive", "negative"]})
    assert build_category_distribution(df) is None


def test_category_distribution_none_kategori_kosong():
    df = pd.DataFrame({"predicted_label": ["positive"], "product_category": [pd.NA]})
    assert build_category_distribution(df) is None


def test_category_distribution_membangun_figure():
    df = pd.DataFrame(
        {
            "predicted_label": ["positive", "negative", "positive", "neutral"],
            "product_category": ["serum", "serum", "pelembap", "pelembap"],
        }
    )
    fig = build_category_distribution(df)
    assert isinstance(fig, go.Figure)
    assert fig.layout.barmode == "stack"
    assert len(fig.data) >= 2  # minimal positif & negatif
