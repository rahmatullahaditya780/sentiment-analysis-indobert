"""
Fase 8 — Glue pipeline dashboard (Module-agnostic).

Satu fungsi `run_analysis()` yang merangkai kembali rantai inti sistem agar
dipakai **kedua jalur input** (CSV Upload & URL Auto-Fetch) lewat satu pintu:

    DataFrame mentah (skema implementasi)
      -> normalisasi kolom         (normalize_input)
      -> SentimentPredictor.predict_batch   (Fase 6: +predicted_label, +confidence)
      -> recommend                 (Fase 7: kondisi + strategi + insight + trend)
      -> AnalysisResult            (bundel siap-render untuk Module 2/3/4/5)

Tujuan modul ini adalah memisahkan *orkestrasi* dari *tampilan* Streamlit:
fungsi di sini murni pandas + objek hasil (tanpa `import streamlit`), sehingga
bisa diuji unit tanpa menjalankan server. Dependency berat (`torch` via
`SentimentPredictor`) di-impor lazy — modul tetap ringan untuk inspeksi/test
normalisasi.

Pemakaian dari `app.py`:

    from src.dashboard.analysis_pipeline import run_analysis
    result = run_analysis(df_raw, predictor=st.session_state["predictor"])
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.recommendation import MarketingRecommendation, recommend

# ── Kontrak kolom (selaras skema implementasi OmorfoShop & Fase 6/7) ──────────
TEXT_COLUMN = "review_text"
DATE_COLUMN = "date_review"
LABEL_COLUMN = "predicted_label"
CONFIDENCE_COLUMN = "confidence_score"

# Skema standar yang dipakai semua modul; kolom opsional diisi NA bila absen
# agar Module 4 (per-kategori) & trend (per-tanggal) tidak crash.
STANDARD_COLUMNS = [
    "review_id",
    "review_text",
    "rating",
    "product_name",
    "product_category",
    "date_review",
]


@dataclass
class AnalysisResult:
    """Bundel hasil analisis end-to-end, siap dirender modul tampilan.

    Atribut
    -------
    predictions : DataFrame input + `predicted_label` + `confidence_score`.
    recommendation : objek Fase 7 (kondisi, strategi, business_insight, trend).
    distribution : ringkasan {n_reviews, proportion{}, counts{}} (dari rec).
    n_reviews : jumlah ulasan yang dianalisis (setelah normalisasi).
    total_prediction_time / avg_prediction_time : monitoring inferensi (detik).
    has_dates : True bila trend analysis layak (ada `date_review` ter-parse).
    inference_skipped : True bila CSV sudah berlabel -> inferensi dilewati.
    """

    predictions: pd.DataFrame
    recommendation: MarketingRecommendation
    distribution: dict
    n_reviews: int
    total_prediction_time: float = 0.0
    avg_prediction_time: float = 0.0
    has_dates: bool = False
    inference_skipped: bool = False


def has_predictions(
    data: pd.DataFrame,
    *,
    label_column: str = LABEL_COLUMN,
    confidence_column: str = CONFIDENCE_COLUMN,
) -> bool:
    """True bila DataFrame sudah memuat hasil prediksi lengkap (semua baris).

    Dipakai untuk melewati inferensi (mahal di CPU) saat CSV yang diunggah —
    mis. `outputs/reports/omorfo_predictions.csv` — sudah berisi
    `predicted_label` & `confidence_score` untuk setiap baris.
    """
    return (
        label_column in data.columns
        and confidence_column in data.columns
        and len(data) > 0
        and bool(data[label_column].notna().all())
    )


def normalize_input(
    data: pd.DataFrame, *, text_column: str = TEXT_COLUMN
) -> pd.DataFrame:
    """Seragamkan DataFrame mentah ke skema standar (Data Normalizer).

    - Memvalidasi keberadaan kolom teks; pesan error menunjuk template CSV.
    - Membuang baris dengan teks kosong/NaN (tak ada gunanya diprediksi).
    - Menambah kolom opsional yang absen sebagai NA agar modul hilir aman.

    Mengembalikan salinan baru; input tidak dimutasi.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError(
            f"Input harus pandas DataFrame; diterima {type(data).__name__}."
        )
    if text_column not in data.columns:
        raise ValueError(
            f"Kolom teks '{text_column}' tidak ditemukan. Kolom tersedia: "
            f"{list(data.columns)}. Gunakan template "
            "data/implementation/omorfo_reviews_TEMPLATE.csv sebagai acuan."
        )

    df = data.copy()
    df[text_column] = df[text_column].astype("string").str.strip()
    df = df[df[text_column].notna() & (df[text_column] != "")].reset_index(drop=True)

    if df.empty:
        raise ValueError(
            f"Tidak ada ulasan valid pada kolom '{text_column}' setelah "
            "membersihkan baris kosong."
        )

    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return df


def run_analysis(
    data: pd.DataFrame,
    *,
    predictor=None,
    text_column: str = TEXT_COLUMN,
    batch_size: int = 32,
    use_trend: bool = True,
    progress_cb=None,
) -> AnalysisResult:
    """Orkestrasi one-click: normalisasi -> (inferensi) -> rekomendasi.

    Parameter
    ---------
    data : DataFrame mentah hasil CSV Upload / URL Auto-Fetch.
    predictor : instance `SentimentPredictor` (idealnya di-cache di
        `st.session_state`). Bila None, dibuat sekali di sini (memuat model —
        mahal; hindari di jalur interaktif).
    use_trend : aktifkan trend analysis bila ada `date_review` (FR-8.7).
    progress_cb : callable(done, total) opsional untuk progress bar inferensi.

    Jika `data` sudah berlabel (`predicted_label` + `confidence_score` untuk semua
    baris), inferensi **dilewati** (`inference_skipped=True`) — hemat waktu besar
    di CPU untuk dataset yang sudah diprediksi.

    Mengembalikan `AnalysisResult`.
    """
    df = normalize_input(data, text_column=text_column)

    # (#2) Shortcut: CSV sudah berlabel -> lewati inferensi IndoBERT.
    if has_predictions(df):
        df[CONFIDENCE_COLUMN] = pd.to_numeric(df[CONFIDENCE_COLUMN], errors="coerce")
        return _assemble_result(df, use_trend=use_trend, inference_skipped=True)

    if predictor is None:
        predictor = load_predictor()

    predictions = predictor.predict_batch(
        df, text_column=text_column, batch_size=batch_size, progress_cb=progress_cb
    )
    return _assemble_result(
        predictions,
        use_trend=use_trend,
        total_prediction_time=float(
            predictions.attrs.get("total_prediction_time", 0.0)
        ),
        avg_prediction_time=float(predictions.attrs.get("avg_prediction_time", 0.0)),
    )


def recompute_from_predictions(
    predictions: pd.DataFrame,
    *,
    use_trend: bool = True,
    total_prediction_time: float = 0.0,
    avg_prediction_time: float = 0.0,
) -> AnalysisResult:
    """Rakit ulang `AnalysisResult` dari DataFrame yang **sudah berlabel**.

    Dipakai Module 5 (Settings) untuk merefleksikan filter pengguna TANPA
    menjalankan inferensi ulang (hanya pandas): distribusi, kondisi pemasaran,
    dan tren dihitung ulang atas subset terfilter. Waktu inferensi dibawa dari
    hasil penuh (parameter) karena tak ada prediksi baru di sini.
    """
    return _assemble_result(
        predictions,
        use_trend=use_trend,
        total_prediction_time=total_prediction_time,
        avg_prediction_time=avg_prediction_time,
    )


def _assemble_result(
    predictions: pd.DataFrame,
    *,
    use_trend: bool,
    total_prediction_time: float = 0.0,
    avg_prediction_time: float = 0.0,
    inference_skipped: bool = False,
) -> AnalysisResult:
    """Jalankan rule engine atas `predictions` berlabel -> `AnalysisResult`."""
    recommendation = recommend(
        predictions,
        label_column=LABEL_COLUMN,
        date_column=DATE_COLUMN,
        use_trend=use_trend,
    )
    trend_meta = recommendation.meta.get("trend", {}) if recommendation.meta else {}
    return AnalysisResult(
        predictions=predictions,
        recommendation=recommendation,
        distribution=recommendation.distribution,
        n_reviews=int(recommendation.distribution.get("n_reviews", len(predictions))),
        total_prediction_time=total_prediction_time,
        avg_prediction_time=avg_prediction_time,
        has_dates=bool(trend_meta.get("available", False)),
        inference_skipped=inference_skipped,
    )


def load_predictor():
    """Buat `SentimentPredictor` (impor lazy agar torch tak dimuat saat import).

    `app.py` sebaiknya memanggil ini sekali lalu menyimpan hasilnya di
    `st.session_state` (UI Requirement: model tidak di-load ulang per interaksi).
    """
    from src.modeling.inference import SentimentPredictor

    return SentimentPredictor()
