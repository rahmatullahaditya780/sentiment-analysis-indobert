"""
Fase 8 — Module 7: Insight Analitik (pasca-gate, peningkatan dashboard).

Helper murni (pandas, tanpa Streamlit) untuk insight bernilai pemasaran di atas
hasil klasifikasi Fase 6/7:
- Deteksi ketidaksesuaian rating <-> sentimen: ulasan yang bintang dan isi
  teksnya bertolak belakang — sinyal yang luput dari rating numerik dan bukti
  nilai tambah IndoBERT.
- Ringkasan kondisi pemasaran per produk: rule engine Fase 7 diterapkan per
  `product_name`, menunjukkan rekomendasi bekerja di bawah tingkat toko.
- Contoh ulasan representatif: bukti positif/keluhan terkuat (confidence
  tertinggi) untuk mengakar strategi pada kutipan nyata.

Semua fungsi defensif terhadap kolom absen/kosong (pola `apply_filters`):
mengembalikan DataFrame kosong / None, bukan raise.
"""

from __future__ import annotations

import pandas as pd

from src.recommendation.rule_engine import MarketingConditionClassifier

# Tipe ketidaksesuaian rating <-> sentimen.
MISMATCH_NEG = "rating_tinggi_sentimen_negatif"  # bintang >= 4 tapi teks negatif
MISMATCH_POS = "rating_rendah_sentimen_positif"  # bintang <= 2 tapi teks positif

_HIGH_RATING_MIN = 4
_LOW_RATING_MAX = 2


def detect_mismatch(
    predictions: pd.DataFrame,
    *,
    rating_column: str = "rating",
    label_column: str = "predicted_label",
) -> pd.DataFrame:
    """Subset baris yang rating & label sentimennya bertolak belakang.

    Menambahkan kolom `mismatch_type` (MISMATCH_NEG/MISMATCH_POS). Rating
    di-coerce numeric (`errors="coerce"`); baris rating NaN diabaikan. Kolom
    rating/label absen -> DataFrame kosong.
    """
    empty = predictions.iloc[0:0].copy()
    empty["mismatch_type"] = pd.Series(dtype=str)
    if rating_column not in predictions.columns:
        return empty
    if label_column not in predictions.columns:
        return empty

    rating = pd.to_numeric(predictions[rating_column], errors="coerce")
    label = predictions[label_column]
    mask_neg = (rating >= _HIGH_RATING_MIN) & (label == "negative")
    mask_pos = (rating <= _LOW_RATING_MAX) & (label == "positive")

    out = predictions[mask_neg | mask_pos].copy()
    if out.empty:
        return empty
    out["mismatch_type"] = mask_neg.loc[out.index].map(
        {True: MISMATCH_NEG, False: MISMATCH_POS}
    )
    return out


def mismatch_summary(
    predictions: pd.DataFrame,
    *,
    rating_column: str = "rating",
    label_column: str = "predicted_label",
) -> dict:
    """Ringkasan mismatch: {n_rated, n_mismatch, rate, counts}.

    `n_rated` = baris dengan rating numerik valid; `rate` = n_mismatch/n_rated
    (0.0 bila tidak ada baris ber-rating).
    """
    if rating_column in predictions.columns:
        n_rated = int(
            pd.to_numeric(predictions[rating_column], errors="coerce").notna().sum()
        )
    else:
        n_rated = 0

    mismatch = detect_mismatch(
        predictions, rating_column=rating_column, label_column=label_column
    )
    counts = mismatch["mismatch_type"].value_counts().to_dict() if len(mismatch) else {}
    n_mismatch = int(len(mismatch))
    return {
        "n_rated": n_rated,
        "n_mismatch": n_mismatch,
        "rate": (n_mismatch / n_rated) if n_rated else 0.0,
        "counts": {
            MISMATCH_NEG: int(counts.get(MISMATCH_NEG, 0)),
            MISMATCH_POS: int(counts.get(MISMATCH_POS, 0)),
        },
    }


def summarize_by_product(
    predictions: pd.DataFrame,
    *,
    product_column: str = "product_name",
    label_column: str = "predicted_label",
    min_reviews: int = 1,
) -> pd.DataFrame | None:
    """Ringkasan per produk: n ulasan, proporsi sentimen, kondisi pemasaran.

    Kondisi via rule engine Fase 7 pada subset tiap produk — TANPA analisis
    tren (proporsi periode per-produk tidak valid untuk n kecil). Produk
    dengan ulasan < `min_reviews` disembunyikan. None bila kolom produk
    absen/seluruhnya kosong.
    """
    if product_column not in predictions.columns:
        return None
    df = predictions.dropna(subset=[product_column])
    if df.empty:
        return None

    clf = MarketingConditionClassifier()
    rows = []
    for product, subset in df.groupby(product_column, sort=True):
        if len(subset) < min_reviews:
            continue
        result = clf.classify(subset, label_column=label_column)
        dist = result.distribution
        rows.append(
            {
                "product": str(product),
                "n_reviews": int(dist.n_reviews),
                "positive": dist.positive,
                "neutral": dist.neutral,
                "negative": dist.negative,
                "condition": result.condition,
            }
        )
    if not rows:
        return None
    return (
        pd.DataFrame(rows)
        .sort_values("n_reviews", ascending=False)
        .reset_index(drop=True)
    )


def top_examples(
    predictions: pd.DataFrame,
    *,
    label: str,
    n: int = 3,
    text_column: str = "review_text",
    confidence_column: str = "confidence_score",
    label_column: str = "predicted_label",
) -> pd.DataFrame:
    """`n` ulasan berlabel `label` dengan confidence tertinggi (representatif).

    Confidence di-coerce numeric; baris NaN dibuang. Label tidak ada / kolom
    absen -> DataFrame kosong.
    """
    if (
        label_column not in predictions.columns
        or text_column not in predictions.columns
    ):
        return predictions.iloc[0:0]

    subset = predictions[predictions[label_column] == label].copy()
    if confidence_column in subset.columns:
        subset[confidence_column] = pd.to_numeric(
            subset[confidence_column], errors="coerce"
        )
        subset = subset.dropna(subset=[confidence_column]).sort_values(
            confidence_column, ascending=False
        )
    return subset.head(n)
