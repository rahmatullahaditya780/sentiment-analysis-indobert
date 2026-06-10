"""
Fase 8 — Module 1: Input Interface (berlapis, 2 tab).

Tab **CSV Upload** (jalan di cloud & lokal) + tab **URL Auto-Fetch** (lokal saja,
dibangun penuh pada langkah Module 6). Modul ini hanya bertugas *mengambil* input
dari pengguna dan mengembalikannya sebagai DataFrame mentah berskema implementasi;
analisis dilakukan oleh `analysis_pipeline.run_analysis`.

Pemisahan tanggung jawab: logika parsing CSV ditaruh di helper murni
`read_uploaded_csv` (tanpa `import streamlit`) agar dapat diuji unit; fungsi
`render_*` membungkusnya dengan widget Streamlit.
"""

from __future__ import annotations

import io

import pandas as pd

from src.dashboard.analysis_pipeline import TEXT_COLUMN

# Encoding yang dicoba berurutan saat membaca CSV unggahan (ulasan Indonesia
# umumnya utf-8; sebagian ekspor lama memakai latin-1).
_CSV_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1")

TEMPLATE_PATH = "data/implementation/omorfo_reviews_TEMPLATE.csv"


def read_uploaded_csv(raw: bytes, *, text_column: str = TEXT_COLUMN) -> pd.DataFrame:
    """Parse byte CSV unggahan -> DataFrame, dengan validasi kolom teks.

    Mencoba beberapa encoding; memunculkan `ValueError` informatif bila gagal
    di-decode atau kolom teks (`review_text`) tidak ada. Helper ini murni
    (tanpa Streamlit) sehingga bisa diuji unit.
    """
    last_err: Exception | None = None
    df: pd.DataFrame | None = None
    for enc in _CSV_ENCODINGS:
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            break
        except (UnicodeDecodeError, ValueError) as exc:  # noqa: PERF203
            last_err = exc
            continue

    if df is None:
        raise ValueError(
            f"Gagal membaca CSV (encoding dicoba: {', '.join(_CSV_ENCODINGS)}). "
            f"Detail: {last_err}"
        )
    if text_column not in df.columns:
        raise ValueError(
            f"Kolom teks '{text_column}' tidak ditemukan. Kolom terbaca: "
            f"{list(df.columns)}. Acuan format: {TEMPLATE_PATH}."
        )
    return df


def render_csv_tab(st) -> pd.DataFrame | None:
    """Render tab CSV Upload; kembalikan DataFrame mentah atau None.

    `st` adalah modul streamlit (di-inject agar modul ini tak meng-import
    streamlit di tingkat atas dan tetap ringan untuk unit test).
    """
    st.markdown(
        "Unggah berkas **CSV** ulasan untuk analisis batch. Wajib memuat kolom "
        f"`{TEXT_COLUMN}`. Kolom opsional yang dimanfaatkan: `product_category` "
        "(filter & distribusi) dan `date_review` (analisis tren)."
    )
    uploaded = st.file_uploader("Pilih berkas CSV", type=["csv"], key="csv_uploader")
    if uploaded is None:
        st.caption(f"Belum ada berkas. Acuan format: `{TEMPLATE_PATH}`.")
        return None

    try:
        df = read_uploaded_csv(uploaded.getvalue())
    except ValueError as exc:
        st.error(str(exc))
        return None

    st.success(f"Terbaca **{len(df):,} baris**. Pratinjau 5 baris pertama:")
    st.dataframe(df.head(), use_container_width=True)
    return df


def render_url_tab(st) -> pd.DataFrame | None:
    """Tab URL Auto-Fetch — delegasi ke Module 6 (`shopee_connector`).

    Jalur ini memakai endpoint JSON internal Shopee via sesi browser ber-login
    dan **hanya aktif di app lokal/desktop** (lihat FR-8.14). Mengembalikan
    DataFrame mentah hasil fetch bila ada, atau None.
    """
    from src.dashboard.shopee_connector import render_url_section

    return render_url_section(st)
