"""
Fase 9 — Integration test end-to-end dengan **model IndoBERT nyata**.

Berbeda dari unit test (yang memakai DataFrame pra-label / mock), test ini
menjalankan rantai inti sistem secara utuh memakai best model Fase 4 di
`models/best_model/` atas **ulasan OmorfoShop mentah nyata**:

    CSV mentah (data/implementation/omorfo_reviews.csv)
      -> normalisasi + preprocessing (Fase 3)
      -> inferensi IndoBERT  (Fase 6: predicted_label, confidence_score)
      -> rule engine          (Fase 7: kondisi pemasaran + strategi + trend)
      -> render 8 halaman dashboard (Fase 8, via AppTest)
      -> ekspor CSV berlabel

Memvalidasi FR-9.2 (aliran data antar-module benar dari ujung ke ujung) dan
sekaligus FR-9.1 untuk jalur inferensi yang tak terjangkau unit test cepat.

Lambat (~30-40 dtk: memuat model ~500MB sekali). Ditandai `integration` dan
DIKECUALIKAN dari `pytest` default (lihat pytest.ini). Jalankan eksplisit:

    pytest -m integration -v

Jika best model belum ada (mis. lingkungan cloud; model di-gitignore), seluruh
modul di-skip dengan alasan jelas — bukan gagal.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.dashboard.analysis_pipeline import AnalysisResult, run_analysis
from src.modeling.config import BEST_MODEL_DIR, REPORTS_DIR
from src.recommendation import CONDITIONS
from src.utils.label_harmonizer import CANONICAL_LABELS

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_REVIEWS_CSV = PROJECT_ROOT / "data" / "implementation" / "omorfo_reviews.csv"
REPORT_JSON = REPORTS_DIR / "phase9_integration_report.json"

PAGE_FUNCS = [
    "page_beranda",
    "page_detail",
    "page_visualisasi",
    "page_rekomendasi",
    "page_pengaturan",
    "page_ekspor",
    "page_tentang",
]


# ── Prasyarat: best model & data implementasi tersedia ───────────────────────
@pytest.fixture(scope="module", autouse=True)
def _require_assets():
    if not Path(BEST_MODEL_DIR).exists():
        pytest.skip(
            f"Best model tidak ditemukan di {BEST_MODEL_DIR} — integration test "
            "butuh artefak Fase 4 (di-gitignore). Lewati di lingkungan tanpa model."
        )
    if not RAW_REVIEWS_CSV.exists():
        pytest.skip(f"Data implementasi tak ditemukan: {RAW_REVIEWS_CSV}")


@pytest.fixture(scope="module")
def predictor():
    """Muat best model IndoBERT sekali untuk seluruh modul (mahal)."""
    from src.modeling.inference import SentimentPredictor

    return SentimentPredictor().load()


@pytest.fixture(scope="module")
def raw_sample() -> pd.DataFrame:
    """Sampel ulasan OmorfoShop **mentah nyata** dengan keragaman rating.

    Mengambil baris rating tinggi (>=4) & rendah (<=2) langsung dari dataset
    implementasi — teks otentik, tanpa label (inferensi benar-benar berjalan).
    """
    full = pd.read_csv(RAW_REVIEWS_CSV)
    assert "predicted_label" not in full.columns, "Dataset mentah tak boleh berlabel"
    pos = full[full["rating"] >= 4].head(18)
    neg = full[full["rating"] <= 2].head(8)
    sample = pd.concat([pos, neg], ignore_index=True)
    assert len(sample) >= 20, "Sampel terlalu kecil untuk E2E yang bermakna"
    return sample


@pytest.fixture(scope="module")
def e2e_result(predictor, raw_sample) -> AnalysisResult:
    """Jalankan pipeline lengkap **sekali** atas sampel mentah (inferensi nyata)."""
    return run_analysis(raw_sample, predictor=predictor, use_trend=True)


# ── 1. Inferensi nyata satu teks (sanity preprocessing -> IndoBERT -> softmax) ─
def test_predict_teks_positif_jelas(predictor):
    res = predictor.predict("barangnya bagus banget, pengiriman cepat, sangat puas")
    assert res.label == "positive"
    assert 0.5 < res.confidence <= 1.0


def test_predict_teks_negatif_jelas(predictor):
    res = predictor.predict("barang rusak, kemasan jelek, sangat mengecewakan")
    assert res.label == "negative"
    assert 0.5 < res.confidence <= 1.0


# ── 2. Pipeline end-to-end atas data mentah nyata ─────────────────────────────
def test_e2e_inferensi_benar_benar_berjalan(e2e_result, raw_sample):
    assert e2e_result.inference_skipped is False  # bukan jalur shortcut pra-label
    assert e2e_result.n_reviews == len(raw_sample)
    assert e2e_result.total_prediction_time > 0.0


def test_e2e_kolom_prediksi_lengkap_dan_valid(e2e_result):
    pred = e2e_result.predictions
    assert {"predicted_label", "confidence_score"} <= set(pred.columns)
    # Semua label dalam skema kanonik, tak ada NaN.
    assert pred["predicted_label"].notna().all()
    assert set(pred["predicted_label"].unique()) <= set(CANONICAL_LABELS)
    conf = pred["confidence_score"].astype(float)
    assert conf.between(0.0, 1.0).all()
    assert (conf > 0.0).all()


def test_e2e_kondisi_pemasaran_valid(e2e_result):
    rec = e2e_result.recommendation
    assert rec.condition in CONDITIONS
    assert rec.strategies, "Setiap kondisi harus memetakan minimal satu strategi"
    assert rec.business_insight


def test_e2e_distribusi_konsisten(e2e_result):
    dist = e2e_result.distribution
    counts = dist.get("counts", {})
    assert sum(counts.values()) == e2e_result.n_reviews
    proportions = dist.get("proportion", {})
    # Proporsi dibulatkan 4 desimal per kelas -> toleransi penjumlahan 3 kelas.
    assert abs(sum(proportions.values()) - 1.0) < 1e-3


# ── 3. Render 8 halaman dashboard memakai output model NYATA ───────────────────
@pytest.fixture(scope="module")
def real_predictions_csv(e2e_result, tmp_path_factory) -> str:
    """Persist prediksi nyata -> CSV; dipakai script AppTest sebagai sumber render."""
    path = tmp_path_factory.mktemp("e2e") / "real_predictions.csv"
    e2e_result.predictions.to_csv(path, index=False)
    return path.as_posix()


@pytest.mark.parametrize("fn", PAGE_FUNCS)
def test_render_halaman_dengan_output_model_nyata(fn, real_predictions_csv):
    # Halaman dirender dari data BERLABEL hasil model nyata (shortcut: tanpa
    # memuat ulang IndoBERT di dalam proses AppTest).
    script = (
        "import pandas as pd, streamlit as st\n"
        "from src.dashboard.analysis_pipeline import run_analysis\n"
        "from src.dashboard import pages\n"
        f"df = pd.read_csv(r'{real_predictions_csv}')\n"
        "st.session_state['result'] = run_analysis(df)\n"
        f"pages.{fn}()\n"
    )
    at = AppTest.from_string(script, default_timeout=90).run()
    assert at.exception == [], f"{fn} melempar exception: {at.exception}"


# ── 4. Ekspor CSV berlabel round-trip (skema utuh) ────────────────────────────
def test_ekspor_csv_roundtrip(e2e_result, tmp_path):
    out = tmp_path / "export.csv"
    e2e_result.predictions.to_csv(out, index=False)
    reloaded = pd.read_csv(out)
    assert len(reloaded) == e2e_result.n_reviews
    for col in ("review_text", "predicted_label", "confidence_score"):
        assert col in reloaded.columns
    assert reloaded["predicted_label"].notna().all()


# ── 5. Artefak laporan integrasi (deliverable Fase 9) ─────────────────────────
def test_tulis_laporan_integrasi(e2e_result, raw_sample):
    """Tulis ringkasan run E2E ke outputs/reports/ sebagai bukti terdokumentasi."""
    rec = e2e_result.recommendation
    report = {
        "phase": "9 — Integration Testing (FR-9.2)",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_dir": str(BEST_MODEL_DIR),
        "sample_source": str(RAW_REVIEWS_CSV),
        "n_reviews": e2e_result.n_reviews,
        "inference_skipped": e2e_result.inference_skipped,
        "total_prediction_time_s": round(e2e_result.total_prediction_time, 4),
        "avg_prediction_time_s": round(e2e_result.avg_prediction_time, 6),
        "labels_observed": sorted(
            e2e_result.predictions["predicted_label"].unique().tolist()
        ),
        "condition": rec.condition,
        "distribution": e2e_result.distribution,
        "strategies_count": len(rec.strategies),
        "pages_rendered": PAGE_FUNCS,
        "status": "PASS",
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), "utf-8")
    assert REPORT_JSON.exists()
    # Validasi artefak terbaca kembali & utuh.
    loaded = json.loads(REPORT_JSON.read_text("utf-8"))
    assert loaded["status"] == "PASS"
    assert loaded["condition"] in CONDITIONS
