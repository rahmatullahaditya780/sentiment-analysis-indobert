"""
Fase 8 — Unit test Module 1 (helper parsing CSV unggahan).

Hanya menguji `read_uploaded_csv` (murni, tanpa Streamlit/torch). Fungsi
`render_*` membungkus widget Streamlit dan divalidasi manual saat menjalankan
dashboard.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.dashboard.input_module import read_uploaded_csv


def test_baca_csv_utf8_valid():
    raw = "review_text,rating\nbarang bagus,5\njelek sekali,1\n".encode("utf-8")
    df = read_uploaded_csv(raw)
    assert list(df.columns) == ["review_text", "rating"]
    assert len(df) == 2


def test_baca_csv_latin1_fallback():
    raw = "review_text\nkualitas oké\n".encode("latin-1")
    df = read_uploaded_csv(raw)
    assert len(df) == 1


def test_kolom_teks_hilang_memunculkan_error():
    raw = "ulasan,rating\nbagus,5\n".encode("utf-8")
    with pytest.raises(ValueError, match="Kolom teks 'review_text'"):
        read_uploaded_csv(raw)


def test_csv_kosong_memunculkan_error():
    with pytest.raises(ValueError):
        read_uploaded_csv(b"")


def test_mengembalikan_dataframe_pandas():
    raw = "review_text\nbagus\n".encode("utf-8")
    assert isinstance(read_uploaded_csv(raw), pd.DataFrame)
