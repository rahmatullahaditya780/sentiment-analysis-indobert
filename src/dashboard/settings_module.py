"""
Fase 8 — Module 5: Settings & Configuration (filter & threshold).

Menyediakan kontrol di sidebar untuk memfilter hasil **tanpa inferensi ulang**
(FR-8.8):
- Filter kategori produk (`product_category`).
- Filter rentang tanggal (`date_review`).
- Confidence threshold (`confidence_score`).

`apply_filters` murni (tanpa Streamlit) & teruji; `render_sidebar` membangun
widget dan mengembalikan pilihan pengguna. app.py memakai keduanya lalu memanggil
`analysis_pipeline.recompute_from_predictions` atas DataFrame terfilter.
"""

from __future__ import annotations

import pandas as pd

CATEGORY_COLUMN = "product_category"
DATE_COLUMN = "date_review"
CONFIDENCE_COLUMN = "confidence_score"


def apply_filters(
    predictions: pd.DataFrame,
    *,
    categories: list | None = None,
    date_range: tuple | None = None,
    min_confidence: float = 0.0,
) -> pd.DataFrame:
    """Terapkan filter kategori/tanggal/confidence -> DataFrame subset.

    Semua filter opsional & defensif: kolom yang tidak ada diabaikan. `date_range`
    adalah (start, end) bertipe date/datetime (inklusif). Mengembalikan salinan;
    input tidak dimutasi.
    """
    df = predictions

    if categories and CATEGORY_COLUMN in df.columns:
        df = df[df[CATEGORY_COLUMN].isin(categories)]

    if min_confidence > 0 and CONFIDENCE_COLUMN in df.columns:
        df = df[df[CONFIDENCE_COLUMN] >= min_confidence]

    if date_range and DATE_COLUMN in df.columns:
        start, end = date_range
        dates = pd.to_datetime(df[DATE_COLUMN], errors="coerce")
        mask = dates.notna()
        if start is not None:
            mask &= dates >= pd.Timestamp(start)
        if end is not None:
            mask &= dates <= pd.Timestamp(end) + pd.Timedelta(days=1)
        df = df[mask]

    return df.copy()


def _available_categories(predictions: pd.DataFrame) -> list[str]:
    if CATEGORY_COLUMN not in predictions.columns:
        return []
    vals = predictions[CATEGORY_COLUMN].dropna().unique().tolist()
    return sorted(str(v) for v in vals)


def _date_bounds(predictions: pd.DataFrame):
    if DATE_COLUMN not in predictions.columns:
        return None
    dates = pd.to_datetime(predictions[DATE_COLUMN], errors="coerce").dropna()
    if dates.empty:
        return None
    return dates.min().date(), dates.max().date()


def render_sidebar(st, predictions: pd.DataFrame) -> dict:
    """Render kontrol filter di sidebar; kembalikan dict pilihan pengguna.

    Hanya menampilkan kontrol yang relevan dengan kolom data yang tersedia.
    """
    st.header("⚙️ Settings & Filter")

    categories = _available_categories(predictions)
    selected_categories = (
        st.multiselect(
            "Kategori produk",
            options=categories,
            default=[],
            help="Kosongkan untuk menyertakan semua kategori.",
        )
        if categories
        else []
    )

    date_range = None
    bounds = _date_bounds(predictions)
    if bounds is not None:
        lo, hi = bounds
        picked = st.date_input(
            "Rentang tanggal ulasan",
            value=(lo, hi),
            min_value=lo,
            max_value=hi,
        )
        if isinstance(picked, (tuple, list)) and len(picked) == 2:
            date_range = (picked[0], picked[1])

    min_confidence = st.slider(
        "Confidence threshold minimum",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        help="Hanya ulasan dengan confidence ≥ ambang yang dianalisis.",
    )

    return {
        "categories": selected_categories,
        "date_range": date_range,
        "min_confidence": min_confidence,
    }
