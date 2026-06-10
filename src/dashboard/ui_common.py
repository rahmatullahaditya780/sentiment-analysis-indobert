"""
Fase 8 — Helper state bersama untuk dashboard multipage.

Menyediakan fungsi lintas-halaman: cache predictor, jalankan analisis dengan
progress bar, dan resolusi "active view" (hasil analisis penuh -> difilter sesuai
Pengaturan -> dihitung ulang tanpa inferensi). Halaman (`pages.py`) memanggil ini
agar filter berlaku global di semua halaman hasil.
"""

from __future__ import annotations

import streamlit as st

from src.dashboard import settings_module
from src.dashboard.analysis_pipeline import (
    AnalysisResult,
    load_predictor,
    recompute_from_predictions,
    run_analysis,
)

# Satu sumber palet sentimen: re-export dari results_module agar tidak ada
# divergensi warna antar halaman/chart (results_module bebas streamlit).
from src.dashboard.results_module import (  # noqa: F401  (re-export)
    SENTIMENT_COLORS as SENTIMENT_HEX,
)
from src.dashboard.visualization_module import (
    build_frequencies,
    build_wordcloud_from_frequencies,
)


# Kunci cache WAJIB tuple string (bukan DataFrame/AnalysisResult — mahal/unhashable).
# `max_entries` membatasi memori: 16 array word cloud 800×400 ≈ 20 MB, aman
# untuk Streamlit Cloud 1 GB.
@st.cache_data(show_spinner=False, max_entries=16)
def cached_frequencies(texts: tuple[str, ...]) -> dict[str, int]:
    """Frekuensi kata word cloud, di-cache per kombinasi teks."""
    return build_frequencies(texts)


@st.cache_data(show_spinner=False, max_entries=16)
def cached_wordcloud(texts: tuple[str, ...], hex_color: str):
    """Gambar word cloud, di-cache — tidak digambar ulang tiap rerun halaman."""
    return build_wordcloud_from_frequencies(
        build_frequencies(texts), hex_color=hex_color
    )


def get_predictor():
    """Muat & cache `SentimentPredictor` di session_state (sekali per sesi)."""
    if "predictor" not in st.session_state:
        with st.spinner("Memuat model IndoBERT (sekali saja)…"):
            st.session_state["predictor"] = load_predictor()
    return st.session_state["predictor"]


def analyze_with_progress(df_raw) -> AnalysisResult:
    """Jalankan `run_analysis` dengan progress bar inferensi (FR-8.11).

    Bila CSV sudah berlabel, inferensi dilewati (`inference_skipped`) dan bar
    langsung penuh. Model hanya dimuat saat inferensi memang diperlukan.
    """
    progress = st.progress(0.0, text="Menyiapkan analisis…")

    def on_progress(done: int, total: int) -> None:
        frac = (done / total) if total else 1.0
        progress.progress(
            min(frac, 1.0), text=f"Menganalisis {done:,}/{total:,} ulasan…"
        )

    predictor = get_predictor()
    result = run_analysis(df_raw, predictor=predictor, progress_cb=on_progress)
    progress.progress(1.0, text="Selesai.")
    progress.empty()
    return result


def resolve_view() -> AnalysisResult | None:
    """Kembalikan AnalysisResult aktif (sudah difilter Pengaturan) atau None.

    Menulis pesan panduan bila belum ada analisis atau filter mengosongkan data,
    lalu mengembalikan None — halaman pemanggil cukup `return` setelahnya.
    """
    base: AnalysisResult | None = st.session_state.get("result")
    if base is None:
        st.info(
            "Belum ada analisis. Buka halaman **Input & Pengambilan Data** untuk "
            "mengunggah CSV atau mengambil ulasan.",
            icon="📥",
        )
        return None

    filters = st.session_state.get("filters", {})
    filtered = settings_module.apply_filters(base.predictions, **filters)
    if filtered.empty:
        st.warning(
            "Filter aktif tidak menyisakan ulasan. Longgarkan filter di halaman "
            "**Pengaturan**.",
            icon="🔎",
        )
        return None

    return recompute_from_predictions(
        filtered,
        avg_prediction_time=base.avg_prediction_time,
        total_prediction_time=base.total_prediction_time,
    )


def filter_active() -> bool:
    """True bila ada filter Pengaturan yang sedang membatasi data."""
    base: AnalysisResult | None = st.session_state.get("result")
    if base is None:
        return False
    filters = st.session_state.get("filters", {})
    filtered = settings_module.apply_filters(base.predictions, **filters)
    return len(filtered) < len(base.predictions)
