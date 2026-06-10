"""
Fase 8 — Module 3: Marketing Recommendation Panel.

Murni *tampilan* atas objek `MarketingRecommendation` (hasil rule engine Fase 7
yang sudah dijalankan `analysis_pipeline`): menampilkan kondisi pemasaran +
kriteria yang terpenuhi (FR-8.5), daftar strategi, dan business insight (FR-7.4).
Tidak ada logika klasifikasi di sini — semua keputusan berasal dari Fase 7.

Helper `condition_style` bersifat murni (tanpa Streamlit) agar dapat diuji.
"""

from __future__ import annotations

from src.recommendation.config import EXCELLENT, GOOD, MIXED, MODERATE, POOR

# Pemetaan kondisi -> gaya tampilan (warna selaras semafor performa + ikon).
_CONDITION_STYLE = {
    EXCELLENT: {"color": "#2E9E5B", "icon": "🟢", "status": "success"},
    GOOD: {"color": "#3B82C4", "icon": "🔵", "status": "info"},
    MODERATE: {"color": "#E8A13A", "icon": "🟠", "status": "warning"},
    POOR: {"color": "#D64545", "icon": "🔴", "status": "error"},
    MIXED: {"color": "#9AA0A6", "icon": "⚪", "status": "warning"},
}
_DEFAULT_STYLE = {"color": "#9AA0A6", "icon": "⚪", "status": "info"}


def condition_style(condition: str) -> dict:
    """Kembalikan gaya tampilan (color/icon/status) untuk satu kondisi."""
    return _CONDITION_STYLE.get(condition, _DEFAULT_STYLE)


def render(st, recommendation) -> None:
    """Render panel rekomendasi pemasaran dari `MarketingRecommendation`."""
    style = condition_style(recommendation.condition)

    st.subheader("Rekomendasi Strategi Pemasaran")

    # Kartu kondisi: ikon + nama kondisi + kriteria yang terpenuhi (reason).
    st.markdown(
        f"<div style='border-left:6px solid {style['color']};"
        "padding:0.6rem 1rem;background:rgba(150,150,150,0.08);"
        "border-radius:4px;'>"
        f"<span style='font-size:1.3rem;font-weight:700;'>"
        f"{style['icon']} {recommendation.condition}</span><br>"
        f"<span style='color:gray;'>{recommendation.reason}</span></div>",
        unsafe_allow_html=True,
    )

    if recommendation.trend_shift:
        st.warning(
            "Terdeteksi **perubahan tren sentimen** yang signifikan antar periode "
            "— pertimbangkan monitoring lebih ketat.",
            icon="📈",
        )

    st.markdown("**Business Insight**")
    st.write(recommendation.business_insight)

    st.markdown("**Strategi yang Direkomendasikan**")
    if recommendation.strategies:
        for strategy in recommendation.strategies:
            st.markdown(f"- {strategy}")
    else:
        st.caption("Tidak ada strategi spesifik untuk kondisi ini.")
