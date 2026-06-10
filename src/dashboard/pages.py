"""
Fase 8 — Halaman-halaman dashboard multipage (struktur selaras prototipe).

Setiap fungsi adalah satu halaman `st.navigation`. Logika analisis/visualisasi
tetap di modul masing-masing (results/recommendation/visualization/settings);
file ini hanya menyusun tata letak per halaman & berbagi state lewat `ui_common`.

Diselaraskan ke keputusan final proyek:
- Input **2 tier** (CSV + URL Auto-Fetch) — jalur Import Ekstensi sudah dihapus.
- Sumber data implementasi = **endpoint JSON internal** (bukan render-DOM / API resmi).
- Ekspor PDF/PNG ditunda ke Fase 10; di sini hanya unduh CSV.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.dashboard import (
    input_module,
    recommendation_module,
    results_module,
    settings_module,
    visualization_module,
)
from src.dashboard.shopee_connector import detect_environment
from src.dashboard.ui_common import (
    SENTIMENT_HEX,
    analyze_with_progress,
    resolve_view,
)
from src.recommendation.config import (
    CONDITIONS,
    EXCELLENT,
    GOOD,
    MIXED,
    MODERATE,
    POOR,
)

# Kriteria 5 kondisi (selaras CLAUDE.md & planning/fase-07).
CONDITION_CRITERIA = {
    EXCELLENT: "Positif ≥ 50% DAN Negatif ≤ 20%",
    GOOD: "Positif 40–49% DAN Negatif 20–30%",
    MODERATE: "Positif 30–39% DAN Negatif 30–40%",
    POOR: "Positif < 30% DAN Negatif > 40%",
    MIXED: "Netral > 35% ATAU tren berubah signifikan",
}

_LABEL_EMOJI = {
    "positive": "🟢 Positif",
    "negative": "🔴 Negatif",
    "neutral": "⚪ Netral",
}


# ── Dashboard ─────────────────────────────────────────────────────────────────
def page_dashboard() -> None:
    st.title("Ringkasan Analisis Sentimen")
    st.caption("Ikhtisar distribusi sentimen, tren, dan kata dominan.")

    view = resolve_view()
    if view is None:
        return

    dist = view.distribution
    prop = dist["proportion"]
    cond = view.recommendation.condition

    c1, c2, c3, c4, c5 = st.columns(5)
    _stat(c1, "Total Ulasan", f"{view.n_reviews:,}")
    _stat(c2, "Positif", f"{prop['positive']:.1%}", SENTIMENT_HEX["positive"])
    _stat(c3, "Netral", f"{prop['neutral']:.1%}", SENTIMENT_HEX["neutral"])
    _stat(c4, "Negatif", f"{prop['negative']:.1%}", SENTIMENT_HEX["negative"])
    _stat(c5, "Kondisi", cond)

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.plotly_chart(results_module.build_distribution_pie(dist), width="stretch")
    with right, st.container(border=True):
        trend_meta = (view.recommendation.meta or {}).get("trend", {})
        trend_fig = results_module.build_trend_chart(trend_meta)
        if trend_fig is not None:
            st.plotly_chart(trend_fig, width="stretch")
        else:
            st.markdown("**Tren Sentimen**")
            st.caption(
                "Tidak tersedia — data tidak memiliki kolom `date_review` valid."
            )

    with st.container(border=True):
        st.markdown("**Kata Dominan (semua ulasan)**")
        img = visualization_module.build_wordcloud_image(
            view.predictions["review_text"].tolist(), hex_color="#FF4B4B"
        )
        if img is not None:
            st.image(img, width="stretch")
        else:
            st.caption("_Tidak cukup kata untuk ditampilkan._")
    st.caption(
        "Buka **Visualisasi & Word Cloud** untuk word cloud per kelas, atau "
        "**Rekomendasi Strategi** untuk saran pemasaran."
    )


def _stat(col, label: str, value: str, color: str | None = None) -> None:
    with col, st.container(border=True):
        val_style = f"color:{color};" if color else ""
        st.markdown(
            f"<div style='font-size:.8rem;color:#6B7280'>{label}</div>"
            f"<div style='font-size:1.7rem;font-weight:700;{val_style}'>{value}</div>",
            unsafe_allow_html=True,
        )


# ── Input & Pengambilan Data ──────────────────────────────────────────────────
def page_input() -> None:
    st.title("Input & Pengambilan Data Ulasan")
    st.caption(
        "Modul input berlapis — pilih jalur sesuai lingkungan, lalu jalankan "
        "IndoBERT untuk klasifikasi sentimen."
    )

    env = detect_environment()
    if env["is_cloud"]:
        st.info(
            "Lingkungan **cloud** terdeteksi — jalur URL Auto-Fetch dinonaktifkan "
            "(FR-8.14). Gunakan CSV Upload.",
            icon="☁️",
        )
    else:
        st.success(
            "Lingkungan **lokal/desktop** terdeteksi — semua jalur input aktif.",
            icon="💻",
        )

    left, right = st.columns([2, 1])
    with left:
        tab_csv, tab_url = st.tabs(
            ["📁 CSV Upload (Cloud & Lokal)", "🔗 URL Auto-Fetch (Lokal saja)"]
        )
        with tab_csv:
            df_csv = input_module.render_csv_tab(st)
        with tab_url:
            df_url = input_module.render_url_tab(st)
        df_raw = df_csv if df_csv is not None else df_url

        if df_raw is not None and st.button("🔍 Analisis Sentimen", type="primary"):
            try:
                result = analyze_with_progress(df_raw)
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state["result"] = result
                st.session_state.pop("filters", None)  # reset filter untuk data baru
                if result.inference_skipped:
                    st.success(
                        f"Data sudah berlabel — inferensi dilewati untuk "
                        f"{result.n_reviews:,} ulasan.",
                        icon="⚡",
                    )
                else:
                    st.success(
                        f"Selesai menganalisis {result.n_reviews:,} ulasan. Buka "
                        "**Dashboard** atau **Detail Ulasan**.",
                        icon="✅",
                    )

    with right:
        with st.container(border=True):
            st.markdown("**Preprocessing Teks (otomatis)**")
            st.markdown(
                "- Case folding (huruf kecil)\n"
                "- Text cleaning regex (URL, emoji, tanda baca)\n"
                "- **Tanpa** stemming & stopword removal\n"
                "- Tokenisasi IndoBERT, `max_length=128`"
            )
        with st.container(border=True):
            st.markdown("**Model IndoBERT**")
            st.caption("indolem/indobert-base-uncased · fine-tuned 3 kelas")
            st.markdown(
                "- Macro F1 (test): **0,9031** (target ≥ 0,85)\n"
                "- Cross-validation: **0,9016 ± 0,010**"
            )


# ── Detail Ulasan ─────────────────────────────────────────────────────────────
def page_detail() -> None:
    st.title("Detail Ulasan & Hasil Klasifikasi")
    st.caption("Setiap ulasan diberi label sentimen + skor keyakinan model.")

    view = resolve_view()
    if view is None:
        return

    df = view.predictions
    choice = st.segmented_control(
        "Saring sentimen",
        options=["Semua", "Positif", "Negatif", "Netral"],
        default="Semua",
    )
    label_map = {"Positif": "positive", "Negatif": "negative", "Netral": "neutral"}
    if choice and choice != "Semua":
        df = df[df["predicted_label"] == label_map[choice]]

    if df.empty:
        st.caption("Tidak ada ulasan pada kategori ini.")
        return

    st.dataframe(
        _build_detail_table(df),
        width="stretch",
        hide_index=True,
        column_config={
            "Skor": st.column_config.ProgressColumn(
                "Skor", min_value=0.0, max_value=1.0, format="%.2f"
            ),
        },
    )


def _stars(rating) -> str:
    try:
        n = int(rating)
    except (ValueError, TypeError):
        return ""
    n = max(0, min(n, 5))
    return "★" * n + "☆" * (5 - n)


def _build_detail_table(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["Ulasan"] = df["review_text"]
    out["Sentimen"] = df["predicted_label"].map(_LABEL_EMOJI)
    out["Skor"] = pd.to_numeric(df["confidence_score"], errors="coerce")
    out["Rating"] = df["rating"].map(_stars)
    out["Kategori"] = df["product_category"]
    out["Tanggal"] = df["date_review"]
    return out.reset_index(drop=True)


# ── Visualisasi & Word Cloud ──────────────────────────────────────────────────
def page_visualisasi() -> None:
    st.title("Visualisasi & Word Cloud per Kelas")
    st.caption("Kata dominan per kategori sentimen + distribusi per kategori produk.")

    view = resolve_view()
    if view is None:
        return
    visualization_module.render(st, view)


# ── Rekomendasi Strategi ──────────────────────────────────────────────────────
def page_rekomendasi() -> None:
    st.title("Rekomendasi Strategi Pemasaran (Rule-Based)")
    st.caption("Kondisi ditentukan dari rasio sentimen terhadap threshold compound.")

    view = resolve_view()
    if view is None:
        return

    rec = view.recommendation
    recommendation_module.render(st, rec)

    st.divider()
    st.subheader("Acuan Klasifikasi 5 Kondisi")
    for cond in CONDITIONS:
        icon = recommendation_module.condition_style(cond)["icon"]
        line = f"{icon} **{cond}** — {CONDITION_CRITERIA[cond]}"
        if cond == rec.condition:
            st.markdown(f"> {line}  ◄ **kondisi saat ini**")
        else:
            st.markdown(line)


# ── Pengaturan ────────────────────────────────────────────────────────────────
def page_pengaturan() -> None:
    st.title("Pengaturan & Konfigurasi")
    st.caption("Filter berlaku ke seluruh halaman hasil (tanpa inferensi ulang).")

    base = st.session_state.get("result")
    if base is None:
        st.info(
            "Belum ada analisis. Buka **Input & Pengambilan Data** lebih dulu.",
            icon="📥",
        )
        return

    st.subheader("Filter Data")
    filters = settings_module.render_filters(st, base.predictions)
    st.session_state["filters"] = filters

    filtered = settings_module.apply_filters(base.predictions, **filters)
    st.caption(
        f"**{len(filtered):,}** dari {len(base.predictions):,} ulasan lolos filter."
    )

    st.divider()
    st.subheader("Ambang Rule-Based (acuan, read-only)")
    st.markdown(
        "- **Excellent** — Positif ≥ 50%\n"
        "- **Mixed/Unstable** — Netral > 35% atau tren berubah signifikan\n"
        "- Maks. ulasan per produk (URL Auto-Fetch): **1.200**"
    )


# ── Ekspor Laporan ────────────────────────────────────────────────────────────
def page_ekspor() -> None:
    st.title("Ekspor & Unduh Hasil Analisis")
    st.caption("Unduh data ulasan berlabel; ekspor PDF/PNG menyusul pada Fase 10.")

    view = resolve_view()
    if view is None:
        return

    csv = view.predictions.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Unduh Data Berlabel (CSV)",
        data=csv,
        file_name="sentara_hasil_analisis.csv",
        mime="text/csv",
        type="primary",
    )

    dist = view.distribution
    prop = dist["proportion"]
    with st.container(border=True):
        st.markdown("**Ringkasan**")
        st.markdown(
            f"- Total ulasan dianalisis: **{view.n_reviews:,}**\n"
            f"- Positif / Netral / Negatif: "
            f"**{prop['positive']:.1%} / {prop['neutral']:.1%} / "
            f"{prop['negative']:.1%}**\n"
            f"- Kondisi pemasaran: **{view.recommendation.condition}**\n"
            f"- Macro F1-Score model: **0,9031**"
        )
    st.info(
        "Ekspor PDF & PNG dijadwalkan pada Fase 10 (Deployment & Dokumentasi).",
        icon="🗓️",
    )


# ── Tentang & Bantuan ─────────────────────────────────────────────────────────
def page_tentang() -> None:
    st.title("Tentang Aplikasi & Cara Pakai")
    st.caption("Sentara — analisis sentimen ulasan e-commerce berbasis IndoBERT.")

    with st.container(border=True):
        st.markdown("**Tentang Sentara**")
        st.write(
            "Sentara mengklasifikasikan ulasan produk e-commerce menjadi tiga "
            "kelas (Positif/Negatif/Netral) memakai IndoBERT "
            "(indolem/indobert-base-uncased) yang di-fine-tune dari gabungan tiga "
            "dataset publik — SmSA, PRDECT-ID, dan Review Product Shopee (Kaggle) — "
            "total 20.608 ulasan. Model diterapkan pada 3.739 ulasan OmorfoShop "
            "Official Store yang dikumpulkan via **endpoint JSON internal Shopee** "
            "dari sesi browser ber-login. Input dashboard berlapis: upload CSV "
            "atau auto-fetch URL produk (mode lokal)."
        )

    with st.container(border=True):
        st.markdown("**Cara Pakai (4 langkah)**")
        st.markdown(
            "1. **Pilih jalur input** — CSV Upload atau URL Auto-Fetch (lokal).\n"
            "2. **Jalankan IndoBERT** — klik Analisis Sentimen.\n"
            "3. **Lihat hasil** — Dashboard, Detail, Visualisasi, Rekomendasi.\n"
            "4. **Saring & ekspor** — Pengaturan lalu unduh CSV."
        )

    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.markdown("**Teknologi**")
        st.markdown(
            "Python · HuggingFace Transformers · IndoBERT · Streamlit · "
            "Scikit-learn · Pandas · Plotly · WordCloud · Playwright"
        )
    with col2, st.container(border=True):
        st.markdown("**Informasi Skripsi**")
        st.markdown(
            "- Nama: **Aditya Rahmatullah**\n"
            "- NIM: **60900122038**\n"
            "- Program Studi: **Sistem Informasi**\n"
            "- Capaian: **Macro F1 0,9031** (≥ 0,85)"
        )
