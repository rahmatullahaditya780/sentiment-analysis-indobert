"""
Fase 8 — Unit test model_info (sumber kebenaran metrik model).

Menguji pembacaan laporan evaluasi nyata (ter-track git), fallback saat file
hilang/korup, dan format desimal koma Indonesia.
"""

from __future__ import annotations

import pytest

from src.dashboard.model_info import (
    DEFAULT_METRICS,
    EVALUATION_FINAL_JSON,
    fmt_id,
    load_model_metrics,
)


def test_membaca_laporan_evaluasi_nyata():
    metrics = load_model_metrics()
    # Laporan Fase 5 ter-track git; nilai final sinkron CLAUDE.md.
    assert metrics["f1_macro"] == pytest.approx(0.9031)
    assert metrics["cv_mean"] == pytest.approx(0.9016)
    assert metrics["cv_std"] == pytest.approx(0.010, abs=1e-3)
    assert metrics["target_f1"] == pytest.approx(0.85)


def test_fallback_saat_file_hilang(tmp_path):
    missing = tmp_path / "tidak_ada.json"
    metrics = load_model_metrics(eval_path=missing, cv_path=missing)
    assert metrics == DEFAULT_METRICS


def test_fallback_parsial_saat_satu_file_korup(tmp_path):
    korup = tmp_path / "korup.json"
    korup.write_text("{bukan json", encoding="utf-8")
    metrics = load_model_metrics(eval_path=EVALUATION_FINAL_JSON, cv_path=korup)
    # File evaluasi sah tetap terbaca; hanya bagian CV memakai fallback.
    assert metrics["f1_macro"] == pytest.approx(0.9031)
    assert metrics["cv_mean"] == DEFAULT_METRICS["cv_mean"]


def test_fmt_id_desimal_koma():
    assert fmt_id(0.9031) == "0,9031"
    assert fmt_id(0.85, 2) == "0,85"
    assert fmt_id(0.010, 3) == "0,010"
