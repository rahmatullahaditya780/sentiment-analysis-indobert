"""
Shopee Open Platform — normalizer JSON -> DataFrame (Fase 2).

Mengonversi respons get_comment/get_rating Shopee menjadi DataFrame dengan
skema dataset implementasi OmorfoShop:
    [review_id, review_text, rating, product_name, product_category, date_review]

Privasi: identitas pelanggan TIDAK disimpan (data minimization).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

IMPLEMENTATION_COLUMNS = [
    "review_id",
    "review_text",
    "rating",
    "product_name",
    "product_category",
    "date_review",
]


def _to_date(ctime) -> str | None:
    """Konversi unix timestamp (detik) Shopee -> tanggal ISO (YYYY-MM-DD)."""
    if ctime in (None, "", 0):
        return None
    try:
        return datetime.fromtimestamp(int(ctime), tz=timezone.utc).date().isoformat()
    except (ValueError, TypeError, OSError):
        return None


def normalize_comments(
    comments: list[dict],
    product_name: str = "",
    product_category: str = "",
) -> pd.DataFrame:
    """Normalkan list komentar Shopee menjadi DataFrame implementasi."""
    rows = []
    for c in comments:
        text = (c.get("comment") or "").strip()
        if not text:
            continue  # lewati ulasan kosong (rating-only)
        rows.append(
            {
                "review_id": str(c.get("comment_id", "")),
                "review_text": text,
                "rating": c.get("rating_star"),
                "product_name": product_name,
                "product_category": product_category,
                "date_review": _to_date(c.get("ctime") or c.get("create_time")),
            }
        )
    return pd.DataFrame(rows, columns=IMPLEMENTATION_COLUMNS)


def empty_implementation_frame() -> pd.DataFrame:
    """DataFrame kosong dengan skema implementasi (untuk template fallback CSV)."""
    return pd.DataFrame(columns=IMPLEMENTATION_COLUMNS)
