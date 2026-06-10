"""
Fase 8 — Module 4: Visualization (word cloud + distribusi per kategori).

- Word cloud kata dominan per kelas sentimen (FR-8.6).
- Bar distribusi sentimen per kategori produk (FR-8.4 lanjutan).

PENTING — stopword di sini **hanya untuk tampilan** word cloud, BUKAN untuk
preprocessing model. Pipeline IndoBERT tetap TANPA stopword removal/stemming
(lihat CLAUDE.md) agar konteks utuh; daftar ringan di bawah semata-mata menyaring
kata fungsi yang tak informatif supaya word cloud lebih bermakna.

Helper frekuensi (`build_frequencies`) murni & teruji; pembuatan gambar word
cloud memakai pustaka `wordcloud` dan dirender via `st.image`.
"""

from __future__ import annotations

import re
from collections import Counter

import plotly.graph_objects as go

from src.dashboard.results_module import (
    SENTIMENT_COLORS,
    SENTIMENT_LABELS_ID,
)

# Stopword Indonesia ringan + filler e-commerce (KHUSUS TAMPILAN word cloud).
DISPLAY_STOPWORDS: frozenset[str] = frozenset(
    {
        "yang",
        "yg",
        "dan",
        "di",
        "ke",
        "dari",
        "untuk",
        "dengan",
        "ini",
        "itu",
        "pada",
        "ada",
        "tidak",
        "ga",
        "gak",
        "nggak",
        "ya",
        "aja",
        "saja",
        "juga",
        "atau",
        "karena",
        "kalau",
        "kalo",
        "jadi",
        "akan",
        "sudah",
        "udah",
        "belum",
        "masih",
        "lagi",
        "saya",
        "aku",
        "kamu",
        "dia",
        "kita",
        "kami",
        "mereka",
        "nya",
        "ku",
        "mu",
        "sih",
        "deh",
        "dong",
        "kok",
        "nih",
        "tuh",
        "loh",
        "lah",
        "pun",
        "se",
        "para",
        "buat",
        "biar",
        "agar",
        "tapi",
        "namun",
        "serta",
        "adalah",
        "bahwa",
        "oleh",
        "dalam",
        "antara",
        "sebagai",
        "yaitu",
        "hanya",
        "bisa",
        "dapat",
        "harus",
        "punya",
        "banget",
        "bgt",
        "sekali",
        "sangat",
        "lebih",
        "paling",
        "cukup",
        "agak",
        "terlalu",
        "produk",
        "barang",
        "beli",
        "pesan",
        "order",
        "toko",
        "seller",
        "shopee",
        "gan",
        "sis",
        "kak",
        "min",
    }
)

_WORD_RE = re.compile(r"[a-zA-Z]+")
_MIN_WORD_LEN = 3

# Dimensi & kapasitas word cloud (dipakai builder + acuan ukuran cache).
WC_WIDTH = 800
WC_HEIGHT = 400
WC_MAX_WORDS = 100


def build_frequencies(
    texts,
    *,
    stopwords: frozenset[str] = DISPLAY_STOPWORDS,
    min_len: int = _MIN_WORD_LEN,
) -> dict[str, int]:
    """Hitung frekuensi kata untuk word cloud (lowercase, buang stopword/pendek).

    Murni (tanpa pustaka berat) sehingga dapat diuji unit. Mengabaikan token
    non-alfabet, kata < `min_len` huruf, dan stopword tampilan.
    """
    counter: Counter[str] = Counter()
    for text in texts:
        if not isinstance(text, str):
            continue
        for token in _WORD_RE.findall(text.lower()):
            if len(token) >= min_len and token not in stopwords:
                counter[token] += 1
    return dict(counter)


def _solid_color_func(hex_color: str):
    """Buat color_func WordCloud yang mengembalikan satu warna solid."""

    def color_func(*_args, **_kwargs):
        return hex_color

    return color_func


def build_wordcloud_from_frequencies(
    freq: dict[str, int], *, hex_color: str, max_words: int = WC_MAX_WORDS
):
    """Bangun array gambar word cloud (RGB) dari peta frekuensi; None bila kosong.

    Mengembalikan `numpy.ndarray` siap dipakai `st.image`. Dipisah dari
    `build_frequencies` agar frekuensi bisa dihitung/dicek (empty state) dan
    di-cache terpisah. Import `wordcloud` lokal agar modul tetap ringan untuk
    unit test fungsi murni.
    """
    if not freq:
        return None

    from wordcloud import WordCloud

    wc = WordCloud(
        width=WC_WIDTH,
        height=WC_HEIGHT,
        background_color="white",
        max_words=max_words,
        color_func=_solid_color_func(hex_color),
        prefer_horizontal=0.9,
    )
    wc.generate_from_frequencies(freq)
    return wc.to_array()


def build_wordcloud_image(
    texts,
    *,
    hex_color: str = SENTIMENT_COLORS["positive"],
    max_words: int = WC_MAX_WORDS,
):
    """Wrapper lama: daftar teks -> frekuensi -> gambar word cloud (atau None)."""
    return build_wordcloud_from_frequencies(
        build_frequencies(texts), hex_color=hex_color, max_words=max_words
    )


def build_category_distribution(
    predictions,
    *,
    category_column: str = "product_category",
    label_column: str = "predicted_label",
) -> go.Figure | None:
    """Bar bertumpuk proporsi sentimen per kategori produk; None bila tak ada.

    Mengembalikan None jika kolom kategori tidak ada atau seluruhnya kosong.
    """
    if category_column not in predictions.columns:
        return None
    df = predictions[[category_column, label_column]].dropna(subset=[category_column])
    if df.empty:
        return None

    # Proporsi tiap label per kategori (baris dinormalisasi ke 1).
    ct = df.groupby(category_column)[label_column].value_counts(normalize=True)
    ct = ct.unstack(fill_value=0.0)

    fig = go.Figure()
    for label in ("positive", "negative", "neutral"):
        if label in ct.columns:
            fig.add_trace(
                go.Bar(
                    x=ct.index.tolist(),
                    y=ct[label].tolist(),
                    name=SENTIMENT_LABELS_ID[label],
                    marker_color=SENTIMENT_COLORS[label],
                )
            )
    fig.update_layout(
        title="Distribusi Sentimen per Kategori Produk",
        barmode="stack",
        xaxis_title="Kategori produk",
        yaxis_title="Proporsi",
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        margin=dict(t=50, b=10, l=10, r=10),
    )
    return fig


def render(st, result) -> None:
    """Render Module 4: word cloud per kelas + distribusi per kategori."""
    # Import lokal: helper ter-cache butuh streamlit; modul ini tetap murni
    # di level import agar unit test fungsi builder tidak menyeret streamlit.
    from src.dashboard.ui_common import cached_wordcloud

    st.subheader("Visualisasi Kata & Kategori")

    df = result.predictions
    st.markdown("**Word Cloud per Kelas Sentimen**")
    cols = st.columns(3)
    for col, label in zip(cols, ("positive", "negative", "neutral")):
        with col:
            st.caption(f"{SENTIMENT_LABELS_ID[label]}")
            texts = df.loc[df["predicted_label"] == label, "review_text"].tolist()
            image = cached_wordcloud(tuple(texts), SENTIMENT_COLORS[label])
            if image is not None:
                st.image(image, width="stretch")
            else:
                st.caption("_Tidak cukup kata untuk ditampilkan._")

    cat_fig = build_category_distribution(df)
    if cat_fig is not None:
        st.plotly_chart(cat_fig, width="stretch")
    else:
        st.caption(
            "Distribusi per kategori tidak ditampilkan — data tidak memiliki "
            "kolom `product_category`."
        )
