"""
Sistem Analisis Sentimen Ulasan Produk E-Commerce Berbasis IndoBERT
Entry point Streamlit — Fase 8 (Dashboard multipage).

Mendefinisikan navigasi sidebar bergrup (struktur selaras
`Design/Sentara_Prototype.html`). Logika tiap halaman ada di
`src/dashboard/pages.py`; state lintas-halaman dikelola `src/dashboard/ui_common.py`.
Model IndoBERT dimuat sekali & disimpan di `st.session_state`.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Sentara — Analisis Sentimen OmorfoShop",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.dashboard import pages  # noqa: E402 — set_page_config harus lebih dulu


def main() -> None:
    with st.sidebar:
        st.markdown("### 📊 Sentara")
        st.caption("Analisis Sentimen Ulasan E-Commerce — IndoBERT")
        st.divider()

    # Navigasi progresif: sebelum ada hasil, hanya Beranda (mode input) yang
    # tampil; menu hasil & lainnya baru muncul setelah analisis dijalankan.
    beranda = st.Page(pages.page_beranda, title="Beranda", icon="🏠", default=True)
    if st.session_state.get("result") is None:
        nav = st.navigation([beranda])
    else:
        nav = st.navigation(
            {
                "Hasil Analisis": [
                    beranda,
                    st.Page(pages.page_detail, title="Daftar Ulasan", icon="📋"),
                    st.Page(
                        pages.page_visualisasi,
                        title="Kata yang Sering Muncul",
                        icon="☁️",
                    ),
                    st.Page(pages.page_rekomendasi, title="Saran Pemasaran", icon="💡"),
                ],
                "Lainnya": [
                    st.Page(pages.page_pengaturan, title="Pengaturan", icon="⚙️"),
                    st.Page(pages.page_ekspor, title="Ekspor", icon="⬇️"),
                    st.Page(pages.page_tentang, title="Tentang & Bantuan", icon="ℹ️"),
                ],
            }
        )
    nav.run()


main()
