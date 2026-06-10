"""
Fase 8 — Unit test Module 2 (chart builders).

Menguji builder figure murni (`go.Figure`) tanpa Streamlit: struktur trace,
nilai, dan penanganan tren tak-tersedia.
"""

from __future__ import annotations

import plotly.graph_objects as go

from src.dashboard.results_module import (
    build_distribution_bar,
    build_distribution_pie,
    build_trend_chart,
)

_DIST = {
    "n_reviews": 100,
    "proportion": {"positive": 0.7, "negative": 0.2, "neutral": 0.1},
    "counts": {"positive": 70, "negative": 20, "neutral": 10},
}


def test_pie_membangun_figure_dengan_tiga_nilai():
    fig = build_distribution_pie(_DIST)
    assert isinstance(fig, go.Figure)
    pie = fig.data[0]
    assert list(pie.values) == [0.7, 0.2, 0.1]
    assert list(pie.labels) == ["Positif", "Negatif", "Netral"]


def test_bar_membangun_figure_dengan_count_benar():
    fig = build_distribution_bar(_DIST)
    bar = fig.data[0]
    assert list(bar.y) == [70, 20, 10]
    assert list(bar.x) == ["Positif", "Negatif", "Netral"]


def test_trend_none_saat_tidak_tersedia():
    assert build_trend_chart({"available": False}) is None
    assert build_trend_chart({}) is None
    assert build_trend_chart({"available": True, "periods": []}) is None


def test_palet_sentimen_satu_sumber():
    """ui_common.SENTIMENT_HEX wajib objek yang sama — penjaga anti-divergen."""
    from src.dashboard import results_module, ui_common

    assert ui_common.SENTIMENT_HEX is results_module.SENTIMENT_COLORS


def test_trend_membangun_dua_garis_saat_ada_periode():
    meta = {
        "available": True,
        "periods": [
            {"period": "2025-01-31", "positive": 0.8, "negative": 0.1},
            {"period": "2025-02-28", "positive": 0.6, "negative": 0.3},
        ],
    }
    fig = build_trend_chart(meta)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    names = {tr.name for tr in fig.data}
    assert names == {"Positif", "Negatif"}
