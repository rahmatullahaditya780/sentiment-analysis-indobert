"""
Fase 8 — Unit test Module 3 (helper gaya kondisi).

Hanya helper murni `condition_style`; `render` membungkus widget Streamlit dan
divalidasi manual saat menjalankan dashboard.
"""

from __future__ import annotations

from src.dashboard.recommendation_module import condition_style
from src.recommendation.config import CONDITIONS, EXCELLENT, POOR


def test_setiap_kondisi_punya_gaya_lengkap():
    for cond in CONDITIONS:
        style = condition_style(cond)
        assert {"color", "icon", "status"} <= style.keys()


def test_excellent_hijau_poor_merah():
    assert condition_style(EXCELLENT)["status"] == "success"
    assert condition_style(POOR)["status"] == "error"


def test_kondisi_tak_dikenal_pakai_default():
    style = condition_style("Kondisi Antah Berantah")
    assert {"color", "icon", "status"} <= style.keys()
