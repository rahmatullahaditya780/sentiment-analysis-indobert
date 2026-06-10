"""
Sistem Analisis Sentimen Ulasan Produk E-Commerce Berbasis IndoBERT
Entry point Streamlit — Fase 8 (Dashboard Development).

Mengintegrasikan modul-modul dashboard. Model IndoBERT dimuat sekali dan
disimpan di `st.session_state` agar tidak di-load ulang setiap interaksi
(UI Requirement: Model Loading).
"""

from __future__ import annotations

import streamlit as st

from src.dashboard.analysis_pipeline import load_predictor, run_analysis
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


def render_results(result) -> None:
    """Render hasil minimal langkah 2: ringkasan distribusi + tabel berlabel.

    Visualisasi penuh (pie/bar/trend, panel rekomendasi, word cloud) menyusul
    pada Module 2–4.
    """
    dist = result.distribution
    prop = dist["proportion"]
    counts = dist["counts"]

    st.subheader("Ringkasan Sentimen")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total ulasan", f"{result.n_reviews:,}")
    c2.metric("Positif", f"{prop['positive']:.1%}", f"{counts['positive']:,} ulasan")
    c3.metric("Negatif", f"{prop['negative']:.1%}", f"{counts['negative']:,} ulasan")
    c4.metric("Netral", f"{prop['neutral']:.1%}", f"{counts['neutral']:,} ulasan")

    st.caption(
        f"Kondisi pemasaran (sementara): **{result.recommendation.condition}** · "
        f"Rata-rata waktu inferensi {result.avg_prediction_time:.3f} dtk/ulasan"
    )

    st.subheader("Hasil Klasifikasi per Ulasan")
    show_cols = [
        c
        for c in [
            "review_text",
            "predicted_label",
            "confidence_score",
            "rating",
            "product_category",
            "date_review",
        ]
        if c in result.predictions.columns
    ]
    st.dataframe(
        result.predictions[show_cols], use_container_width=True, hide_index=True
    )


def main() -> None:
    st.title("📊 Sentara")
    st.subheader("Sistem Analisis Sentimen Ulasan Produk E-Commerce Berbasis IndoBERT")

    with st.sidebar:
        st.header("Navigasi")
        st.caption("Fase 8 — Dashboard sedang dibangun bertahap.")
        st.divider()
        st.caption("Model: `indolem/indobert-base-uncased` (fine-tuned)")

    tab_csv, tab_url = st.tabs(["📁 CSV Upload", "🔗 URL Auto-Fetch (Lokal saja)"])
    df_raw = None
    with tab_csv:
        df_raw = render_csv_tab(st)
    with tab_url:
        render_url_tab(st)

    if df_raw is not None and st.button("🔍 Analisis Sentimen", type="primary"):
        predictor = get_predictor()
        with st.spinner(f"Menganalisis {len(df_raw):,} ulasan…"):
            try:
                result = run_analysis(df_raw, predictor=predictor)
            except ValueError as exc:
                st.error(str(exc))
                return
        st.session_state["result"] = result

    if "result" in st.session_state:
        st.divider()
        render_results(st.session_state["result"])


if __name__ == "__main__":
    main()
