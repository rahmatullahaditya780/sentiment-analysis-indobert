"""
Fase 8 — Smoke test render halaman multipage (AppTest).

Memastikan tiap fungsi halaman di `src/dashboard/pages.py` dapat dirender tanpa
exception saat ada hasil analisis di session_state. Memakai DataFrame berlabel
sintetis (mengaktifkan shortcut pra-prediksi) sehingga TIDAK memuat IndoBERT —
cepat & mandiri (tak bergantung file output).
"""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

PAGE_FUNCS = [
    "page_beranda",
    "page_detail",
    "page_visualisasi",
    "page_rekomendasi",
    "page_pengaturan",
    "page_ekspor",
    "page_tentang",
]

# Script AppTest: bangun hasil dari df berlabel sintetis (inferensi dilewati),
# lalu render satu halaman.
_SCRIPT = """
import pandas as pd, streamlit as st
from src.dashboard.analysis_pipeline import run_analysis
from src.dashboard import pages

df = pd.DataFrame({{
    "review_text": ["bagus sekali", "jelek mengecewakan", "biasa saja", "mantap original"],
    "predicted_label": ["positive", "negative", "neutral", "positive"],
    "confidence_score": [0.98, 0.91, 0.66, 0.95],
    "product_category": ["serum", "serum", "sabun", "sabun"],
    "date_review": ["2025-01-10", "2025-02-15", "2025-03-20", "2025-04-25"],
    # rating baris-2 = 5 + label negatif -> fixture mismatch (Module 7 tereksekusi).
    "rating": [5, 5, 3, 1],
    "product_name": ["Serum A", "Serum A", "Sabun B", "Sabun B"],
}})
st.session_state["result"] = run_analysis(df)
pages.{fn}()
"""


@pytest.mark.parametrize("fn", PAGE_FUNCS)
def test_halaman_render_tanpa_exception(fn):
    at = AppTest.from_string(_SCRIPT.format(fn=fn), default_timeout=60).run()
    assert at.exception == [], f"{fn} melempar exception: {at.exception}"


@pytest.mark.parametrize("fn", PAGE_FUNCS)
def test_halaman_render_tanpa_data(fn):
    # Tanpa hasil di session_state: halaman hasil harus menampilkan panduan,
    # bukan crash.
    script = "from src.dashboard import pages\npages.%s()" % fn
    at = AppTest.from_string(script, default_timeout=60).run()
    assert at.exception == [], f"{fn} (tanpa data) melempar exception: {at.exception}"
