"""
Fase 8 — Module 2: Sentiment Analysis Results (visualisasi distribusi & tren).

Membangun figure Plotly dari `AnalysisResult` (hasil `analysis_pipeline`):
- Pie chart  : distribusi persentase 3 kelas sentimen (FR-8.4).
- Bar chart  : jumlah ulasan per kelas (FR-8.4).
- Trend chart: proporsi positif/negatif per periode bila ada `date_review`
  (FR-8.7), digambar ulang dari `meta["trend"]["periods"]` Fase 7 (tanpa
  hitung ulang).

Builder figure bersifat murni (mengembalikan `go.Figure`, tanpa `import
streamlit`) agar dapat diuji unit; `render` membungkusnya dengan layout kolom
Streamlit.
"""

from __future__ import annotations

import plotly.graph_objects as go

# Warna konsisten lintas modul (Module 4 word cloud mengikuti palet ini).
SENTIMENT_COLORS = {
    "positive": "#2E9E5B",  # hijau
    "negative": "#D64545",  # merah
    "neutral": "#9AA0A6",  # abu
}
SENTIMENT_LABELS_ID = {
    "positive": "Positif",
    "negative": "Negatif",
    "neutral": "Netral",
}
_ORDER = ("positive", "negative", "neutral")


def build_distribution_pie(distribution: dict) -> go.Figure:
    """Pie chart proporsi 3 kelas sentimen dari `distribution['proportion']`."""
    prop = distribution["proportion"]
    labels = [SENTIMENT_LABELS_ID[k] for k in _ORDER]
    values = [prop.get(k, 0.0) for k in _ORDER]
    colors = [SENTIMENT_COLORS[k] for k in _ORDER]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.45,
            textinfo="percent+label",
            sort=False,
        )
    )
    fig.update_layout(
        title="Distribusi Sentimen (%)",
        showlegend=True,
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def build_distribution_bar(distribution: dict) -> go.Figure:
    """Bar chart jumlah ulasan per kelas dari `distribution['counts']`."""
    counts = distribution["counts"]
    labels = [SENTIMENT_LABELS_ID[k] for k in _ORDER]
    values = [int(counts.get(k, 0)) for k in _ORDER]
    colors = [SENTIMENT_COLORS[k] for k in _ORDER]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=values,
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Jumlah Ulasan per Kelas",
        yaxis_title="Jumlah ulasan",
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def build_trend_chart(trend_meta: dict) -> go.Figure | None:
    """Garis tren proporsi positif & negatif per periode (FR-8.7).

    Mengembalikan None bila tren tidak tersedia atau tak ada periode untuk
    digambar. Memakai `trend_meta['periods']` (hasil `trend_analyzer`).
    """
    if not trend_meta or not trend_meta.get("available"):
        return None
    periods = trend_meta.get("periods") or []
    if not periods:
        return None

    x = [p["period"] for p in periods]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=[p["positive"] for p in periods],
            mode="lines+markers",
            name="Positif",
            line=dict(color=SENTIMENT_COLORS["positive"]),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=[p["negative"] for p in periods],
            mode="lines+markers",
            name="Negatif",
            line=dict(color=SENTIMENT_COLORS["negative"]),
        )
    )
    fig.update_layout(
        title="Tren Sentimen per Periode",
        xaxis_title="Periode",
        yaxis_title="Proporsi",
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def render(st, result) -> None:
    """Render Module 2: ringkasan metrik + pie/bar berdampingan + tren."""
    dist = result.distribution
    prop = dist["proportion"]
    counts = dist["counts"]

    st.subheader("Hasil Analisis Sentimen")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total ulasan", f"{result.n_reviews:,}")
    c2.metric("Positif", f"{prop['positive']:.1%}", f"{counts['positive']:,} ulasan")
    c3.metric("Negatif", f"{prop['negative']:.1%}", f"{counts['negative']:,} ulasan")
    c4.metric("Netral", f"{prop['neutral']:.1%}", f"{counts['neutral']:,} ulasan")
    st.caption(
        f"Rata-rata waktu inferensi {result.avg_prediction_time:.3f} dtk/ulasan "
        f"· total {result.total_prediction_time:.1f} dtk"
    )

    left, right = st.columns(2)
    left.plotly_chart(build_distribution_pie(dist), width="stretch")
    right.plotly_chart(build_distribution_bar(dist), width="stretch")

    trend_meta = (result.recommendation.meta or {}).get("trend", {})
    trend_fig = build_trend_chart(trend_meta)
    if trend_fig is not None:
        st.plotly_chart(trend_fig, width="stretch")
        if trend_meta.get("note"):
            st.caption(trend_meta["note"])
    else:
        st.caption(
            "Tren waktu tidak ditampilkan — data tidak memiliki kolom "
            "`date_review` yang valid."
        )

    with st.expander("Lihat tabel hasil klasifikasi per ulasan"):
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
            result.predictions[show_cols],
            width="stretch",
            hide_index=True,
        )
