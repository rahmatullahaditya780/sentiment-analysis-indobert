"""
Konverter CSV hasil ekstensi ShopeeReviewsExtractor -> format dataset implementasi.

Memetakan output ekstensi browser ke skema implementasi OmorfoShop yang sama
dengan normalizer Shopee Open Platform API:
    [review_id, review_text, rating, product_name, product_category, date_review]

Mengikuti konvensi normalizer.py:
- Privasi: identitas pelanggan (User Id/Name) TIDAK disimpan (data minimization).
- review_text di-strip; ulasan kosong (rating-only) dilewati.
- date_review diformat ISO (YYYY-MM-DD).

Catatan metodologi: sumber data ini adalah scraping ekstensi, BUKAN Shopee
Open Platform API resmi. Gunakan hanya untuk uji teknis pipeline; samakan klaim
sumber data di bab metodologi skripsi sebelum dipakai sebagai data final.

Pemakaian:
    python src/utils/convert_extension_csv.py <input.csv> [output.csv] [--category KATEGORI]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

IMPLEMENTATION_COLUMNS = [
    "review_id",
    "review_text",
    "rating",
    "product_name",
    "product_category",
    "date_review",
]


def _to_date(value: object) -> str | None:
    """Konversi timestamp ISO ekstensi (mis. 2024-02-23T04:20:22.000Z) -> YYYY-MM-DD."""
    if value in (None, ""):
        return None
    try:
        return pd.to_datetime(value, utc=True, errors="coerce").date().isoformat()
    except (ValueError, TypeError, AttributeError):
        return None


def convert_extension_csv(
    input_path: str | Path,
    product_category: str = "",
    drop_duplicates: bool = True,
) -> pd.DataFrame:
    """Baca CSV ekstensi dan kembalikan DataFrame berskema implementasi."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"File input tidak ditemukan: {input_path}")

    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)

    required = {"Comment Id", "Comment", "Rating", "Product Name", "Comment Date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Kolom wajib hilang dari CSV ekstensi: {sorted(missing)}")

    out = pd.DataFrame(
        {
            "review_id": df["Comment Id"].astype(str).str.strip(),
            "review_text": df["Comment"].astype(str).str.strip(),
            "rating": pd.to_numeric(df["Rating"], errors="coerce").astype("Int64"),
            "product_name": df["Product Name"].astype(str).str.strip(),
            "product_category": product_category,
            "date_review": df["Comment Date"].map(_to_date),
        },
        columns=IMPLEMENTATION_COLUMNS,
    )

    out = out[out["review_text"].str.len() > 0]  # lewati ulasan kosong
    if drop_duplicates:
        out = out.drop_duplicates(subset="review_id")
    return out.reset_index(drop=True)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path CSV hasil ekstensi")
    parser.add_argument(
        "output",
        nargs="?",
        default="data/implementation/omorfo_reviews_extension.csv",
        help="Path output (default: data/implementation/omorfo_reviews_extension.csv)",
    )
    parser.add_argument("--category", default="", help="Isi kolom product_category")
    args = parser.parse_args()

    df = convert_extension_csv(args.input, product_category=args.category)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"OK: {len(df)} ulasan -> {output_path}")
    print(f"Distribusi rating:\n{df['rating'].value_counts().sort_index().to_string()}")


if __name__ == "__main__":
    main()
