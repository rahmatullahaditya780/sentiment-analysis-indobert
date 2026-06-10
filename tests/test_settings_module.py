"""
Fase 8 â€” Unit test Module 5 (apply_filters murni).

Render sidebar membungkus widget Streamlit (validasi manual); di sini hanya
logika filter kategori/tanggal/confidence yang diuji.
"""

from __future__ import annotations

import pandas as pd

from src.dashboard.settings_module import apply_filters, filter_by_keyword, paginate

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


# â”€â”€ filter_by_keyword â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_KW_DF = pd.DataFrame(
    {
        "review_text": [
            "Pengiriman cepat banget",
            "kemasan rapi, PENGIRIMAN aman",
            "produk bagus (original)",
            "biasa saja",
        ],
        "predicted_label": ["positive", "positive", "positive", "neutral"],
    }
)


def test_keyword_case_insensitive():
    out = filter_by_keyword(_KW_DF, "pengiriman")
    assert len(out) == 2


def test_keyword_karakter_regex_aman():
    out = filter_by_keyword(_KW_DF, "(original)")
    assert len(out) == 1
    assert out.iloc[0]["review_text"] == "produk bagus (original)"


def test_keyword_kosong_passthrough():
    assert filter_by_keyword(_KW_DF, "").equals(_KW_DF)
    assert filter_by_keyword(_KW_DF, "   ").equals(_KW_DF)
    assert filter_by_keyword(_KW_DF, None).equals(_KW_DF)


def test_keyword_kolom_absen_passthrough():
    df = pd.DataFrame({"lain": [1, 2]})
    assert filter_by_keyword(df, "apa").equals(df)


# â”€â”€ paginate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_paginate_halaman_pertama_dan_total():
    df = pd.DataFrame({"x": range(10)})
    sub, n_pages = paginate(df, page=1, page_size=4)
    assert list(sub["x"]) == [0, 1, 2, 3]
    assert n_pages == 3


def test_paginate_halaman_parsial_terakhir():
    df = pd.DataFrame({"x": range(10)})
    sub, n_pages = paginate(df, page=3, page_size=4)
    assert list(sub["x"]) == [8, 9]
    assert n_pages == 3


def test_paginate_clamp_di_luar_rentang():
    df = pd.DataFrame({"x": range(10)})
    sub_atas, _ = paginate(df, page=99, page_size=4)
    assert list(sub_atas["x"]) == [8, 9]  # clamp ke halaman terakhir
    sub_bawah, _ = paginate(df, page=0, page_size=4)
    assert list(sub_bawah["x"]) == [0, 1, 2, 3]  # clamp ke halaman pertama


def test_paginate_df_kosong():
    sub, n_pages = paginate(pd.DataFrame({"x": []}), page=1, page_size=25)
    assert sub.empty
    assert n_pages == 1
