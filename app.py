"""
Sistem Analisis Sentimen Ulasan Produk E-Commerce Berbasis IndoBERT
Entry point Streamlit — Fase 8 (Dashboard Development).

Mengintegrasikan modul-modul dashboard. Model IndoBERT dimuat sekali dan
disimpan di `st.session_state` agar tidak di-load ulang setiap interaksi
(UI Requirement: Model Loading).
"""

from __future__ import annotations

import streamlit as st

from src.dashboard import (
    recommendation_module,
    results_module,
    settings_module,
    visualization_module,
)
from src.dashboard.analysis_pipeline import (
    load_predictor,
    recompute_from_predictions,
    run_analysis,
)
from src.dashboard.input_module import render_csv_tab, render_url_tab

st.set_page_config(
    page_title="Sentara — Analisis Sentimen OmorfoShop",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_predictor():
    """Muat & cache `SentimentPredictor` di session_state (sekali per sesi)."""
    if "predictor" not in st.session_state:
        with st.spinner("Memuat model IndoBERT (sekali saja)…"):
            st.session_state["predictor"] = load_predictor()
    return st.session_state["predictor"]


def _analyze_with_progress(df_raw):
    """Jalankan `run_analysis` dengan progress bar inferensi (FR-8.11).

    Bila CSV sudah berlabel, `run_analysis` melewati inferensi sehingga callback
    progress tak terpanggil — bar tetap langsung penuh. Model hanya dimuat saat
    inferensi memang diperlukan (data mentah).
    """
    progress = st.progress(0.0, text="Menyiapkan analisis…")

    def on_progress(done: int, total: int) -> None:
        frac = (done / total) if total else 1.0
        progress.progress(
            min(frac, 1.0), text=f"Menganalisis {done:,}/{total:,} ulasan…"
        )

    # Model hanya dibutuhkan bila data belum berlabel; load lazy via predictor.
    predictor = get_predictor()
    result = run_analysis(df_raw, predictor=predictor, progress_cb=on_progress)
    progress.progress(1.0, text="Selesai.")
    progress.empty()
    return result


def main() -> None:
    st.title("📊 Sentara")
    st.subheader("Sistem Analisis Sentimen Ulasan Produk E-Commerce Berbasis IndoBERT")

    with st.sidebar:
        st.header("Navigasi")
        st.caption("Fase 8 — Dashboard sedang dibangun bertahap.")
        st.divider()
        st.caption("Model: `indolem/indobert-base-uncased` (fine-tuned)")

    tab_csv, tab_url = st.tabs(["📁 CSV Upload", "🔗 URL Auto-Fetch (Lokal saja)"])
    with tab_csv:
        df_csv = render_csv_tab(st)
    with tab_url:
        df_url = render_url_tab(st)
    # Prioritaskan CSV bila keduanya terisi; jika tidak, pakai hasil URL fetch.
    df_raw = df_csv if df_csv is not None else df_url

    if df_raw is not None and st.button("🔍 Analisis Sentimen", type="primary"):
        try:
            result = _analyze_with_progress(df_raw)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.session_state["result"] = result
        if result.inference_skipped:
            st.success(
                f"Data sudah berlabel — inferensi dilewati untuk "
                f"{result.n_reviews:,} ulasan (langsung ke analisis).",
                icon="⚡",
            )

    if "result" in st.session_state:
        base = st.session_state["result"]

        with st.sidebar:
            st.divider()
            filters = settings_module.render_sidebar(st, base.predictions)

        filtered = settings_module.apply_filters(base.predictions, **filters)
        st.divider()
        if filtered.empty:
            st.warning(
                "Tidak ada ulasan yang cocok dengan filter saat ini. "
                "Longgarkan kategori, rentang tanggal, atau confidence threshold."
            )
            return

        active_filter = len(filtered) < len(base.predictions)
        if active_filter:
            st.info(
                f"Menampilkan **{len(filtered):,}** dari {len(base.predictions):,} "
                "ulasan sesuai filter.",
                icon="🔎",
            )
        view = recompute_from_predictions(
            filtered,
            avg_prediction_time=base.avg_prediction_time,
            total_prediction_time=base.total_prediction_time,
        )

        results_module.render(st, view)
        st.divider()
        recommendation_module.render(st, view.recommendation)
        st.divider()
        visualization_module.render(st, view)


if __name__ == "__main__":
    main()
