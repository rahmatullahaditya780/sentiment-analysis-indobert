"""
Fase 8 — Module 5: Settings & Configuration (filter & threshold).

Menyediakan kontrol untuk memfilter hasil **tanpa inferensi ulang** (FR-8.8):
- Filter kategori produk (`product_category`).
- Filter rentang tanggal (`date_review`).
- Confidence threshold (`confidence_score`).

`apply_filters` murni (tanpa Streamlit) & teruji; `render_filters` membangun
widget (dipakai di body halaman Pengaturan) dan mengembalikan pilihan pengguna.
Hasilnya diteruskan ke `analysis_pipeline.recompute_from_predictions`.
"""

from __future__ import annotations

import re

import pandas as pd

CATEGORY_COLUMN = "product_category"
DATE_COLUMN = "date_review"
CONFIDENCE_COLUMN = "confidence_score"
TEXT_COLUMN = "review_text"


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


def filter_by_keyword(
    predictions: pd.DataFrame,
    keyword: str,
    *,
    column: str = TEXT_COLUMN,
) -> pd.DataFrame:
    """Saring baris yang teksnya memuat `keyword` (substring, case-insensitive).

    `re.escape` mengamankan karakter regex pada input pengguna. Keyword
    kosong/whitespace atau kolom absen -> DataFrame dikembalikan apa adanya.
    """
    keyword = (keyword or "").strip()
    if not keyword or column not in predictions.columns:
        return predictions
    mask = (
        predictions[column]
        .astype(str)
        .str.contains(re.escape(keyword), case=False, na=False)
    )
    return predictions[mask]


def paginate(
    df: pd.DataFrame, *, page: int, page_size: int
) -> tuple[pd.DataFrame, int]:
    """Potong DataFrame ke halaman ke-`page` -> (subset, total_halaman).

    `page` di-clamp ke [1, total_halaman]; DataFrame kosong menghasilkan
    (kosong, 1) agar widget nomor halaman tetap valid.
    """
    n_pages = max(1, -(-len(df) // page_size))  # ceil division
    page = max(1, min(page, n_pages))
    start = (page - 1) * page_size
    return df.iloc[start : start + page_size], n_pages


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


# Nama bulan Bahasa Indonesia untuk label periode (lebih ramah dari "Jan 2025").
_BULAN_ID = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}

# Kunci widget filter (dipakai tombol "Reset saringan" untuk mengosongkan state).
FILTER_WIDGET_KEYS = ("flt_kategori", "flt_periode", "flt_rentang", "flt_keyakinan")


def _available_months(predictions: pd.DataFrame) -> list[tuple[str, tuple]]:
    """Daftar bulan tersedia -> [(label "Mei 2025", (tgl_awal, tgl_akhir)), ...]."""
    if DATE_COLUMN not in predictions.columns:
        return []
    dates = pd.to_datetime(predictions[DATE_COLUMN], errors="coerce").dropna()
    if dates.empty:
        return []
    out: list[tuple[str, tuple]] = []
    for period in sorted(dates.dt.to_period("M").unique()):
        label = f"{_BULAN_ID[period.month]} {period.year}"
        out.append((label, (period.start_time.date(), period.end_time.date())))
    return out


def render_filters(st, predictions: pd.DataFrame) -> dict:
    """Render kontrol saringan (kategori/periode/keyakinan); kembalikan pilihan.

    Bahasa sengaja awam (tanpa istilah teknis). Hanya menampilkan kontrol yang
    relevan dengan kolom data yang tersedia. Dipakai di halaman Pengaturan.
    """
    categories = _available_categories(predictions)
    selected_categories = (
        st.multiselect(
            "Kategori produk",
            options=categories,
            default=[],
            key="flt_kategori",
            help="Biarkan kosong untuk menampilkan semua kategori.",
        )
        if categories
        else []
    )

    date_range = None
    months = _available_months(predictions)
    if months:
        labels = ["Semua waktu"] + [m[0] for m in months] + ["Rentang tanggal khusus…"]
        pilihan = st.selectbox(
            "Periode waktu",
            options=labels,
            key="flt_periode",
            help="Pilih satu bulan, atau tentukan rentang tanggal sendiri.",
        )
        if pilihan == "Rentang tanggal khusus…":
            bounds = _date_bounds(predictions)
            if bounds is not None:
                lo, hi = bounds
                picked = st.date_input(
                    "Dari tanggal — sampai tanggal",
                    value=(lo, hi),
                    min_value=lo,
                    max_value=hi,
                    key="flt_rentang",
                )
                if isinstance(picked, (tuple, list)) and len(picked) == 2:
                    date_range = (picked[0], picked[1])
        elif pilihan != "Semua waktu":
            date_range = dict(months)[pilihan]

    with st.expander("⚙️ Saringan lanjutan (opsional)"):
        min_confidence = st.slider(
            "Tingkat keyakinan minimum model",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            key="flt_keyakinan",
            help=(
                "Hanya tampilkan ulasan yang diprediksi model dengan keyakinan "
                "minimal sebesar ini. Biarkan 0 untuk menampilkan semua."
            ),
        )

    return {
        "categories": selected_categories,
        "date_range": date_range,
        "min_confidence": min_confidence,
    }
