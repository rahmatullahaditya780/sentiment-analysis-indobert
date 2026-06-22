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
    insights_module,
    recommendation_module,
    results_module,
    settings_module,
    visualization_module,
)
from src.dashboard.model_info import fmt_id, load_model_metrics
from src.dashboard.shopee_connector import HARD_CAP, detect_environment
from src.dashboard.ui_common import (
    SENTIMENT_HEX,
    analyze_with_progress,
    cached_frequencies,
    cached_wordcloud,
    resolve_view,
)
from src.recommendation.config import CONDITIONS, condition_criteria

_LABEL_EMOJI = {
    "positive": "🟢 Positif",
    "negative": "🔴 Negatif",
    "neutral": "⚪ Netral",
}


# ── Beranda (Input + Ringkasan menyatu) ───────────────────────────────────────
def page_beranda() -> None:
    """Halaman utama adaptif.

    - Belum ada hasil  -> **mode input** (unggah CSV / ambil URL + Mulai Analisis).
    - Sudah ada hasil   -> **mode ringkasan** (verdict awam + stat + grafik) dengan
      tombol "Tambah data" & "Analisis baru".
    """
    if st.session_state.get("result") is None:
        _render_input_mode()
    else:
        _render_dashboard_mode()


def _input_tabs(*, csv_key: str = "csv_uploader"):
    """Render 2 tab input (CSV / URL) -> DataFrame mentah atau None."""
    env = detect_environment()
    if env["is_cloud"]:
        st.info(
            "Terdeteksi berjalan di **server (cloud)** — pengambilan dari URL "
            "dimatikan. Silakan unggah berkas CSV.",
            icon="☁️",
        )
    else:
        st.caption("💻 Mode lokal — pengambilan ulasan dari URL produk tersedia.")

    tab_csv, tab_url = st.tabs(["📁 Unggah CSV", "🔗 Ambil dari URL (lokal)"])
    with tab_csv:
        df_csv = input_module.render_csv_tab(st, key=csv_key)
    with tab_url:
        df_url = input_module.render_url_tab(st)
    return df_csv if df_csv is not None else df_url


def _run_and_store(df_raw, *, append: bool) -> None:
    """Analisis `df_raw` (opsional gabung data lama) lalu simpan hasil ke sesi."""
    if append and st.session_state.get("raw_data") is not None:
        combined = pd.concat([st.session_state["raw_data"], df_raw], ignore_index=True)
        if "review_id" in combined.columns:
            combined = combined.drop_duplicates(
                subset="review_id", keep="last"
            ).reset_index(drop=True)
        df_raw = combined

    result = analyze_with_progress(df_raw)
    st.session_state["result"] = result
    st.session_state["raw_data"] = df_raw
    # Bersihkan state turunan halaman hasil agar selaras data baru.
    for stale_key in (
        "filters",
        "detail_search",
        "detail_page",
        "detail_mismatch",
        "show_add_data",
    ):
        st.session_state.pop(stale_key, None)


def _render_input_mode() -> None:
    st.title("Analisis Sentimen Ulasan Pelanggan")
    st.caption(
        "Ubah banyak ulasan menjadi ringkasan kepuasan pelanggan dan saran "
        "pemasaran — otomatis."
    )
    with st.container(border=True):
        st.markdown(
            "**Cara pakai — 3 langkah:**\n\n"
            "1. **Masukkan ulasan** — unggah berkas CSV, atau ambil dari URL "
            "produk (mode lokal).\n"
            "2. Klik tombol **🔍 Mulai Analisis**.\n"
            "3. Ringkasan hasil dan menu lainnya **muncul otomatis** di halaman ini."
        )

    df_raw = _input_tabs()
    if df_raw is not None and st.button("🔍 Mulai Analisis", type="primary"):
        try:
            _run_and_store(df_raw, append=False)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.rerun()

    with st.expander("ℹ️ Detail teknis (opsional)"):
        st.markdown(
            "**Pemrosesan teks otomatis:** huruf dikecilkan, URL/emoji/tanda baca "
            "dibersihkan (tanpa stemming/penghapusan kata umum), lalu diterjemahkan "
            "ke token untuk model."
        )
        st.markdown("**Model:** IndoBERT (indolem/indobert-base-uncased), 3 kelas.")
        m = load_model_metrics()
        st.markdown(
            f"- Akurasi seimbang (Macro F1): **{fmt_id(m['f1_macro'])}** "
            f"(target ≥ {fmt_id(m['target_f1'], 2)})\n"
            f"- Uji silang 5-lipat: **{fmt_id(m['cv_mean'])} "
            f"± {fmt_id(m['cv_std'], 3)}**"
        )


def _render_dashboard_mode() -> None:
    st.title("Ringkasan Hasil Analisis")
    c1, c2, _ = st.columns([1, 1, 3])
    if c1.button(
        "➕ Tambah data",
        help="Gabungkan ulasan lain ke analisis ini, lalu hitung ulang.",
    ):
        st.session_state["show_add_data"] = not st.session_state.get(
            "show_add_data", False
        )
    if c2.button("🔄 Analisis baru", help="Hapus hasil sekarang dan mulai dari awal."):
        for key in (
            "result",
            "raw_data",
            "filters",
            "detail_search",
            "detail_page",
            "detail_mismatch",
            "show_add_data",
            "fetch_cache",
        ):
            st.session_state.pop(key, None)
        st.rerun()

    if st.session_state.get("show_add_data"):
        with st.container(border=True):
            st.markdown(
                "**➕ Tambah data ke analisis ini** — ulasan baru digabung dengan "
                "yang sudah ada (duplikat otomatis dibuang)."
            )
            df_new = _input_tabs(csv_key="csv_uploader_add")
            if df_new is not None and st.button(
                "Gabungkan & analisis ulang", type="primary"
            ):
                try:
                    _run_and_store(df_new, append=True)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    st.rerun()

    _render_dashboard_body()


def _render_verdict(view) -> None:
    """Kalimat ringkasan bahasa awam di paling atas (paham hasil tanpa grafik)."""
    prop = view.distribution["proportion"]
    cond = view.recommendation.condition
    pos, neg = prop["positive"], prop["negative"]
    if pos >= 0.5:
        mood = "Mayoritas pelanggan **puas**"
    elif neg > pos:
        mood = "Cukup banyak pelanggan **kecewa**"
    else:
        mood = "Tanggapan pelanggan **beragam**"
    msg = (
        f"{mood} — **{pos:.1%}** ulasan positif dari **{view.n_reviews:,}** "
        f"ulasan. Kondisi toko: **{cond}**."
    )
    style = recommendation_module.condition_style(cond)
    icon = style.get("icon", "📊")
    status = style.get("status", "info")
    box = {"success": st.success, "error": st.error, "warning": st.warning}.get(
        status, st.info
    )
    box(msg, icon=icon)


def _render_dashboard_body() -> None:
    view = resolve_view()
    if view is None:
        return

    _render_verdict(view)

    dist = view.distribution
    prop = dist["proportion"]
    cond = view.recommendation.condition

    c1, c2, c3, c4, c5 = st.columns(5)
    _stat(c1, "Total Ulasan", f"{view.n_reviews:,}")
    _stat(c2, "Positif", f"{prop['positive']:.1%}", SENTIMENT_HEX["positive"])
    _stat(c3, "Netral", f"{prop['neutral']:.1%}", SENTIMENT_HEX["neutral"])
    _stat(c4, "Negatif", f"{prop['negative']:.1%}", SENTIMENT_HEX["negative"])
    _stat(c5, "Kondisi", cond)

    mm = insights_module.mismatch_summary(view.predictions)
    if mm["n_rated"] > 0 and mm["n_mismatch"] > 0:
        st.caption(
            f"⚠️ **{mm['n_mismatch']:,}** dari {mm['n_rated']:,} ulasan ber-bintang "
            f"({mm['rate']:.1%}) **diberi bintang tinggi tapi isinya keluhan** "
            "(atau sebaliknya) — buka **Daftar Ulasan** untuk menelusurinya."
        )

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.plotly_chart(results_module.build_distribution_pie(dist), width="stretch")
    with right, st.container(border=True):
        trend_meta = (view.recommendation.meta or {}).get("trend", {})
        trend_fig = results_module.build_trend_chart(trend_meta)
        if trend_fig is not None:
            st.plotly_chart(trend_fig, width="stretch")
        else:
            st.markdown("**Tren Sentimen dari Waktu ke Waktu**")
            date_state = visualization_module.column_state(
                view.predictions, "date_review"
            )
            if date_state == "absen":
                st.caption(
                    "Belum tersedia — data tidak memuat tanggal ulasan. "
                    "Tambahkan kolom tanggal pada CSV untuk melihat tren."
                )
            elif date_state == "kosong":
                st.caption(
                    "Belum tersedia — kolom tanggal ulasan ada, namun semua "
                    "nilainya kosong/tidak valid."
                )
            else:
                st.caption(
                    "Belum tersedia — data tanggal belum cukup membentuk "
                    "minimal dua periode untuk dibandingkan."
                )

    with st.container(border=True):
        st.markdown("**Kata yang Paling Sering Muncul (semua ulasan)**")
        img = cached_wordcloud(
            tuple(view.predictions["review_text"].tolist()), "#FF4B4B"
        )
        if img is not None:
            st.image(img, width="stretch")
        else:
            st.caption(
                "_Tidak ada kata tersisa setelah kata umum & kata pendek "
                "diabaikan — gambar kata tidak dapat dibuat._"
            )
    st.caption(
        "Buka **Kata yang Sering Muncul** untuk rincian per jenis sentimen, atau "
        "**Saran Pemasaran** untuk rekomendasi tindakan."
    )


def _stat(col, label: str, value: str, color: str | None = None) -> None:
    with col, st.container(border=True):
        val_style = f"color:{color};" if color else ""
        st.markdown(
            f"<div style='font-size:.8rem;color:#6B7280'>{label}</div>"
            f"<div style='font-size:1.7rem;font-weight:700;{val_style}'>{value}</div>",
            unsafe_allow_html=True,
        )


# ── Detail Ulasan ─────────────────────────────────────────────────────────────
def page_detail() -> None:
    st.title("Daftar Ulasan")
    st.caption(
        "Setiap ulasan diberi label sentimen (positif/negatif/netral) beserta "
        "tingkat keyakinan model."
    )

    view = resolve_view()
    if view is None:
        return

    df = view.predictions
    left, right = st.columns([3, 2])
    with left:
        choice = st.segmented_control(
            "Saring sentimen",
            options=["Semua", "Positif", "Negatif", "Netral"],
            default="Semua",
        )
    with right:
        keyword = st.text_input(
            "Cari kata dalam ulasan",
            key="detail_search",
            placeholder="mis. pengiriman, kemasan…",
        )

    label_map = {"Positif": "positive", "Negatif": "negative", "Netral": "neutral"}
    if choice and choice != "Semua":
        df = df[df["predicted_label"] == label_map[choice]]
    df = settings_module.filter_by_keyword(df, keyword)

    if insights_module.mismatch_summary(view.predictions)["n_rated"] > 0:
        only_mismatch = st.toggle(
            "⚠️ Hanya tampilkan bintang vs isi yang bertolak belakang",
            key="detail_mismatch",
            help=(
                "Ulasan yang nilai bintang dan isi tulisannya berlawanan "
                "(mis. bintang 5 tapi isinya keluhan) — keluhan yang tidak "
                "terlihat dari bintang saja."
            ),
        )
        if only_mismatch:
            df = insights_module.detect_mismatch(df)

    if df.empty:
        st.caption("Tidak ada ulasan yang cocok dengan saringan/kata kunci ini.")
        return

    # Slot tabel diisi belakangan agar kontrol paginasi tampil di bawah tabel
    # namun nilainya sudah terbaca sebelum tabel dirender.
    table_slot = st.container()
    c1, c2, _ = st.columns([1, 1, 2])
    page_size = c1.selectbox(
        "Baris per halaman", options=(25, 50, 100), key="detail_page_size"
    )
    n_pages = max(1, -(-len(df) // page_size))  # ceil
    # Sanitasi state lama (mis. jumlah halaman menyusut setelah pencarian).
    if st.session_state.get("detail_page", 1) > n_pages:
        st.session_state["detail_page"] = n_pages
    page = c2.number_input(
        "Halaman", min_value=1, max_value=n_pages, step=1, key="detail_page"
    )
    page_df, n_pages = settings_module.paginate(df, page=page, page_size=page_size)

    with table_slot:
        st.dataframe(
            _build_detail_table(page_df),
            width="stretch",
            hide_index=True,
            column_config={
                "Keyakinan": st.column_config.ProgressColumn(
                    "Keyakinan", min_value=0.0, max_value=1.0, format="%.2f"
                ),
            },
        )
    start = (min(page, n_pages) - 1) * page_size + 1
    st.caption(
        f"Menampilkan {start:,}–{start + len(page_df) - 1:,} dari {len(df):,} "
        f"ulasan · halaman {min(page, n_pages)}/{n_pages}"
    )


def _stars(rating) -> str:
    try:
        n = int(rating)
    except (ValueError, TypeError):
        return ""
    n = max(0, min(n, 5))
    return "★" * n + "☆" * (5 - n)


def build_detail_table(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["Ulasan"] = df["review_text"]
    out["Sentimen"] = df["predicted_label"].map(_LABEL_EMOJI)
    out["Keyakinan"] = pd.to_numeric(df["confidence_score"], errors="coerce")
    out["Rating"] = df["rating"].map(_stars)
    out["Kategori"] = df["product_category"]
    out["Tanggal"] = df["date_review"]
    return out.reset_index(drop=True)


_build_detail_table = build_detail_table  # alias lama (kompatibilitas)


# ── Visualisasi & Word Cloud ──────────────────────────────────────────────────
def page_visualisasi() -> None:
    st.title("Kata yang Sering Muncul")
    st.caption(
        "Kata yang paling sering dipakai pelanggan di tiap jenis sentimen, "
        "serta perbandingan antar produk."
    )

    view = resolve_view()
    if view is None:
        return
    visualization_module.render(st, view)

    # ── Kata kunci teratas per kelas + drill-down ulasan ──────────────────────
    st.divider()
    st.subheader("Kata Kunci Teratas per Jenis Sentimen")
    st.caption(
        "Kata yang paling sering muncul (kata umum & kata pendek diabaikan) — "
        "pilih satu kata untuk membaca ulasan yang memuatnya."
    )
    pilihan_kelas = st.selectbox(
        "Jenis sentimen",
        options=("Positif", "Negatif", "Netral"),
        key="viz_keyword_class",
        help="Lihat kata-kata khas pada ulasan positif, negatif, atau netral.",
    )
    label_map = {"Positif": "positive", "Negatif": "negative", "Netral": "neutral"}
    label = label_map[pilihan_kelas]
    df = view.predictions
    texts = df.loc[df["predicted_label"] == label, "review_text"].tolist()
    freq = cached_frequencies(tuple(texts))
    kw_fig = visualization_module.build_top_keywords_chart(
        freq,
        color=SENTIMENT_HEX[label],
        title=f"Kata Kunci Teratas — {pilihan_kelas}",
    )
    if kw_fig is None:
        st.info(
            f"Tidak ada kata tersisa untuk ulasan {pilihan_kelas.lower()} "
            "setelah kata umum & kata pendek diabaikan.",
            icon="🔤",
        )
    else:
        st.plotly_chart(kw_fig, width="stretch")
        kata_opsi = [w for w, _ in visualization_module.top_keywords(freq)]
        kata = st.selectbox(
            "Telusuri ulasan yang memuat kata…",
            options=["(pilih kata)"] + kata_opsi,
            key="viz_keyword_drill",
        )
        if kata != "(pilih kata)":
            cocok = settings_module.filter_by_keyword(
                df[df["predicted_label"] == label], kata
            )
            st.caption(
                f"**{len(cocok):,}** ulasan {pilihan_kelas.lower()} memuat “{kata}”."
            )
            st.dataframe(
                build_detail_table(cocok),
                width="stretch",
                hide_index=True,
                column_config={
                    "Keyakinan": st.column_config.ProgressColumn(
                        "Keyakinan", min_value=0.0, max_value=1.0, format="%.2f"
                    ),
                },
            )

    # ── Perbandingan per produk ───────────────────────────────────────────────
    st.divider()
    st.subheader("Perbandingan per Produk")
    ringkasan = insights_module.summarize_by_product(df)
    if ringkasan is None:
        st.info(
            "Perbandingan per produk tidak tersedia — data tidak memiliki kolom "
            "`product_name` berisi.",
            icon="📦",
        )
    else:
        prod_fig = visualization_module.build_category_distribution(
            df, category_column="product_name"
        )
        if prod_fig is not None:
            prod_fig.update_layout(
                title="Distribusi Sentimen per Produk", xaxis_title="Produk"
            )
            st.plotly_chart(prod_fig, width="stretch")
        st.dataframe(
            _product_summary_table(ringkasan),
            width="stretch",
            hide_index=True,
            column_config={
                "Positif": st.column_config.ProgressColumn(
                    "Positif", min_value=0.0, max_value=1.0, format="percent"
                ),
                "Negatif": st.column_config.ProgressColumn(
                    "Negatif", min_value=0.0, max_value=1.0, format="percent"
                ),
            },
        )
        st.caption(
            "Kondisi tiap produk dihitung dari proporsi sentimennya "
            "(tanpa analisis tren karena jumlah ulasan per produk lebih sedikit)."
        )


def _product_summary_table(ringkasan: pd.DataFrame) -> pd.DataFrame:
    """Susun tabel tampilan ringkasan per produk (ikon kondisi + proporsi)."""
    out = pd.DataFrame()
    out["Produk"] = ringkasan["product"]
    out["Ulasan"] = ringkasan["n_reviews"]
    out["Positif"] = ringkasan["positive"]
    out["Negatif"] = ringkasan["negative"]
    out["Kondisi"] = [
        f"{recommendation_module.condition_style(c)['icon']} {c}"
        for c in ringkasan["condition"]
    ]
    return out


# ── Rekomendasi Strategi ──────────────────────────────────────────────────────
def page_rekomendasi() -> None:
    st.title("Saran Pemasaran")
    st.caption(
        "Saran tindakan otomatis berdasarkan seberapa banyak pelanggan puas "
        "atau kecewa."
    )

    view = resolve_view()
    if view is None:
        return

    rec = view.recommendation
    recommendation_module.render(st, rec)

    # ── Bukti ulasan representatif (confidence tertinggi per kelas) ───────────
    st.divider()
    st.subheader("Bukti Ulasan Representatif")
    st.caption(
        "Ulasan dengan keyakinan model tertinggi — mengakar strategi pada "
        "kutipan pelanggan nyata."
    )
    col_pos, col_neg = st.columns(2)
    _render_examples(col_pos, view.predictions, "positive", "🟢 Bukti positif terkuat")
    _render_examples(col_neg, view.predictions, "negative", "🔴 Keluhan terkuat")

    # ── Kondisi pemasaran per produk (ringkas) ────────────────────────────────
    ringkasan = insights_module.summarize_by_product(view.predictions)
    if ringkasan is not None and len(ringkasan) > 1:
        st.divider()
        st.subheader("Kondisi per Produk")
        st.dataframe(
            _product_summary_table(ringkasan),
            width="stretch",
            hide_index=True,
            column_config={
                "Positif": st.column_config.ProgressColumn(
                    "Positif", min_value=0.0, max_value=1.0, format="percent"
                ),
                "Negatif": st.column_config.ProgressColumn(
                    "Negatif", min_value=0.0, max_value=1.0, format="percent"
                ),
            },
        )
        st.caption(
            "Strategi di atas berlaku tingkat toko; cek produk berkondisi "
            "lebih rendah untuk prioritas perbaikan."
        )

    st.divider()
    st.subheader("Acuan Klasifikasi 5 Kondisi")
    criteria = condition_criteria()
    for cond in CONDITIONS:
        icon = recommendation_module.condition_style(cond)["icon"]
        line = f"{icon} **{cond}** — {criteria[cond]}"
        if cond == rec.condition:
            st.markdown(f"> {line}  ◄ **kondisi saat ini**")
        else:
            st.markdown(line)


def _render_examples(col, predictions: pd.DataFrame, label: str, judul: str) -> None:
    """Render n contoh ulasan ber-confidence tertinggi untuk satu kelas."""
    with col:
        st.markdown(f"**{judul}**")
        contoh = insights_module.top_examples(predictions, label=label)
        if contoh.empty:
            st.caption("_Tidak ada ulasan pada jenis ini._")
            return
        for _, row in contoh.iterrows():
            with st.container(border=True):
                st.write(f"“{row['review_text']}”")
                conf = pd.to_numeric(row.get("confidence_score"), errors="coerce")
                meta = [] if pd.isna(conf) else [f"keyakinan {conf:.1%}"]
                bintang = _stars(row.get("rating"))
                if bintang:
                    meta.append(bintang)
                if meta:
                    st.caption(" · ".join(meta))


# ── Pengaturan ────────────────────────────────────────────────────────────────
def page_pengaturan() -> None:
    st.title("Pengaturan & Saringan")
    st.caption("Saringan di sini berlaku ke semua halaman hasil (tanpa hitung ulang).")

    base = st.session_state.get("result")
    if base is None:
        st.info(
            "Belum ada analisis. Buka **Beranda** lebih dulu, lalu klik "
            "**Mulai Analisis**.",
            icon="📥",
        )
        return

    st.subheader("Saring Ulasan")
    filters = settings_module.render_filters(st, base.predictions)
    st.session_state["filters"] = filters

    filtered = settings_module.apply_filters(base.predictions, **filters)
    st.caption(
        f"**{len(filtered):,}** dari {len(base.predictions):,} ulasan ditampilkan."
    )
    if st.button("🔄 Reset saringan", help="Kembalikan semua saringan ke semula."):
        for key in (*settings_module.FILTER_WIDGET_KEYS, "filters"):
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()
    with st.expander("ℹ️ Bagaimana sistem menilai kondisi toko?"):
        criteria = condition_criteria()
        st.markdown(
            "\n".join(f"- **{cond}** — {criteria[cond]}" for cond in CONDITIONS)
        )
        hard_cap_id = f"{HARD_CAP:,}".replace(",", ".")  # 1200 -> "1.200"
        st.caption(
            f"Maksimum ulasan yang diambil per produk dari URL: **{hard_cap_id}**."
        )


# ── Ekspor Laporan ────────────────────────────────────────────────────────────
def page_ekspor() -> None:
    st.title("Ekspor & Unduh Hasil")
    st.caption("Unduh hasil analisis sebagai berkas CSV (bisa dibuka di Excel).")

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
            f"- Kondisi toko: **{view.recommendation.condition}**\n"
            f"- Akurasi model (Macro F1): **{fmt_id(load_model_metrics()['f1_macro'])}**"
        )
    st.info(
        "Ekspor ke PDF & gambar akan ditambahkan pada versi berikutnya.",
        icon="🗓️",
    )


# ── Tentang & Bantuan ─────────────────────────────────────────────────────────
def page_tentang() -> None:
    st.title("Tentang Aplikasi & Cara Pakai")
    st.caption("Sentara — analisis sentimen ulasan e-commerce berbasis IndoBERT.")

    with st.container(border=True):
        st.markdown("**Tentang Sentara**")
        st.write(
            "Sentara membaca ulasan produk pelanggan dan mengelompokkannya menjadi "
            "tiga jenis: **Positif**, **Negatif**, dan **Netral**. Dari komposisi "
            "itu, sistem menilai kondisi toko dan memberi **saran pemasaran**. "
            "Mesin penilainya adalah IndoBERT (model bahasa Indonesia) yang dilatih "
            "dari 20.608 ulasan publik, lalu diuji pada 3.739 ulasan nyata "
            "OmorfoShop Official Store di Shopee."
        )

    with st.container(border=True):
        st.markdown("**Cara Pakai (3 langkah)**")
        st.markdown(
            "1. Di **Beranda**, masukkan ulasan — unggah CSV atau ambil dari URL "
            "produk (mode lokal).\n"
            "2. Klik **🔍 Mulai Analisis**.\n"
            "3. Ringkasan & menu hasil **muncul otomatis** — lihat **Daftar Ulasan**, "
            "**Kata yang Sering Muncul**, dan **Saran Pemasaran**. Saring di "
            "**Pengaturan**, unduh di **Ekspor**."
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
        m = load_model_metrics()
        st.markdown(
            "- Nama: **Aditya Rahmatullah**\n"
            "- NIM: **60900122038**\n"
            "- Program Studi: **Sistem Informasi**\n"
            f"- Capaian: **Macro F1 {fmt_id(m['f1_macro'])}** "
            f"(≥ {fmt_id(m['target_f1'], 2)})"
        )

    with st.expander("🛠️ Troubleshooting — masalah umum & solusinya"):
        st.markdown(
            "**Kolom `review_text` tidak ditemukan saat upload CSV**\n"
            "Pastikan CSV memiliki kolom bernama persis `review_text`. Acuan "
            "format: `data/implementation/omorfo_reviews_TEMPLATE.csv`.\n\n"
            "**URL Auto-Fetch tidak bisa dipakai**\n"
            "Jalur ini hanya aktif di mode lokal/desktop (FR-8.14). Pada "
            "deployment cloud, gunakan CSV Upload.\n\n"
            "**Pengambilan ulasan gagal / muncul captcha**\n"
            "Selesaikan login & captcha di jendela Chrome yang terbuka, "
            "pastikan halaman produk menampilkan ulasan, lalu klik "
            "**Ambil Ulasan** lagi. Bila tetap gagal, perbesar jeda "
            "antar-permintaan.\n\n"
            "**Halaman hasil kosong padahal sudah analisis**\n"
            "Kemungkinan saringan di **Pengaturan** menyaring habis data — "
            "longgarkan kategori/periode/tingkat keyakinan, atau klik "
            "**Reset saringan**.\n\n"
            "**Analisis terasa lambat di laptop tanpa kartu grafis (GPU)**\n"
            "Wajar — model berjalan di prosesor biasa. Untuk data yang sudah "
            "pernah dianalisis, unggah kembali CSV hasil ekspor (sudah berlabel) "
            "agar analisis dilewati dan langsung tampil."
        )

    with st.expander("📖 Glosarium — istilah singkat"):
        st.markdown(
            "- **Sentimen** — nada perasaan ulasan: positif, negatif, atau netral.\n"
            "- **Keyakinan** — seberapa yakin sistem terhadap label sebuah ulasan "
            "(0–100%). Makin tinggi makin meyakinkan.\n"
            "- **Kondisi toko** — ringkasan performa dari komposisi sentimen "
            "(Sangat Baik / Baik / Perlu Perbaikan / Beragam–Tidak Stabil).\n"
            "- **Tren** — perubahan proporsi sentimen dari waktu ke waktu (butuh "
            "kolom tanggal ulasan).\n"
            "- **Bintang vs isi bertolak belakang** — ulasan yang nilai bintangnya "
            "tinggi tetapi isinya keluhan (atau sebaliknya)."
        )
