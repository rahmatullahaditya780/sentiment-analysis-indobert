"""
Orkestrator scraping multi-produk OmorfoShop — data implementasi Fase 6+.

Menelusuri BEBERAPA URL produk Shopee dalam satu sesi login persisten, menerapkan
iterasi filter rating (5→1 bintang) per produk agar diversitas kelas terjaga, lalu
menggabung + dedup global ke satu CSV kanonik:

    data/implementation/omorfo_reviews.csv
    [review_id, review_text, rating, product_name, product_category, date_review]

Mengapa multi-produk
--------------------
Satu produk populer sering didominasi ulasan 5 bintang & jumlahnya terbatas.
Menggabungkan beberapa produk OmorfoShop (1) mencapai target ±1.200 ulasan, dan
(2) menambah diversitas kategori & sentimen — penting agar rule-based engine Fase 7
punya distribusi positif/negatif/netral yang bermakna.

Sesi login (anti-bot Shopee)
----------------------------
Sama seperti scraper satu-produk: WAJIB profil persisten yang sudah login. Login
sekali (headful), lalu semua produk memakai cookie yang sama:

    # 1) Login manual sekali (lihat scrape_omorfo_reviews.py).
    python src/scraping/scrape_omorfo_reviews.py "<URL produk pertama>" \
        --user-data-dir .shopee_session --headful --login-wait 60

    # 2) Batch semua produk (sesi sudah login).
    python src/scraping/scrape_omorfo_batch.py --urls-file products.json \
        --user-data-dir .shopee_session --rating-filters 5,4,3,2,1

Format --urls-file (JSON)
-------------------------
    [
      {"url": "https://shopee.co.id/...", "category": "deodorant"},
      {"url": "https://shopee.co.id/...", "category": "sabun"}
    ]

Alternatif: berikan URL sebagai argumen posisi + satu --category umum.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scraping.scrape_omorfo_reviews import (  # noqa: E402
    IMPLEMENTATION_COLUMNS,
    load_selectors,
    scrape_reviews,
)

# Path kanonik dataset implementasi (TRD A.5 butir 5).
DEFAULT_OUTPUT = "data/implementation/omorfo_reviews.csv"


def load_products(
    urls_file: str | Path | None,
    positional_urls: list[str],
    default_category: str,
) -> list[dict[str, str]]:
    """Rakit daftar {url, category} dari --urls-file ATAU argumen posisi."""
    products: list[dict[str, str]] = []
    if urls_file:
        raw = json.loads(Path(urls_file).read_text(encoding="utf-8"))
        for entry in raw:
            if isinstance(entry, str):
                products.append({"url": entry, "category": default_category})
            else:
                products.append(
                    {
                        "url": entry["url"],
                        "category": entry.get("category", default_category),
                    }
                )
    products.extend({"url": u, "category": default_category} for u in positional_urls)
    if not products:
        raise ValueError(
            "Tidak ada URL produk. Berikan --urls-file atau URL sebagai argumen posisi."
        )
    return products


def scrape_many(
    products: list[dict[str, str]],
    *,
    max_pages: int = 50,
    delay: float = 2.0,
    product_delay: float = 5.0,
    headful: bool = False,
    selectors: dict[str, str] | None = None,
    user_data_dir: str | Path | None = None,
    rating_filters: list[int] | None = None,
) -> pd.DataFrame:
    """Scrape beberapa produk berurutan & gabung-dedup ke satu DataFrame.

    Tiap produk memakai `scrape_reviews` (profil persisten yang sama → cookie login
    dipakai ulang). Dedup global by `review_id` lintas produk. `product_delay` = jeda
    sopan antar produk (rate-limit).
    """
    frames: list[pd.DataFrame] = []
    for i, product in enumerate(products, start=1):
        url, category = product["url"], product.get("category", "")
        print(f"\n=== Produk {i}/{len(products)} (kategori: {category or '-'}) ===")
        df = scrape_reviews(
            url,
            product_category=category,
            max_pages=max_pages,
            delay=delay,
            headful=headful,
            selectors=selectors,
            user_data_dir=user_data_dir,
            login_wait=0,  # login dilakukan sekali di luar (scrape_omorfo_reviews.py)
            rating_filters=rating_filters,
        )
        if not df.empty:
            frames.append(df)
        print(f"[batch] produk {i}: {len(df)} ulasan (akumulasi {sum(len(f) for f in frames)})")
        if i < len(products):
            time.sleep(product_delay)  # jeda antar produk

    if not frames:
        print("[warn] 0 ulasan dari semua produk — periksa selektor/sesi login")
        return pd.DataFrame(columns=IMPLEMENTATION_COLUMNS)

    combined = pd.concat(frames, ignore_index=True)
    before = len(combined)
    combined = combined.drop_duplicates(subset="review_id").reset_index(drop=True)
    print(f"\n[batch] dedup global: {before} → {len(combined)} ulasan unik")
    return combined[IMPLEMENTATION_COLUMNS]


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="URL produk (alternatif --urls-file). Pakai --category untuk semuanya.",
    )
    parser.add_argument(
        "--urls-file",
        default=None,
        help="File JSON daftar produk: [{\"url\":..., \"category\":...}, ...]",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Path CSV gabungan (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--category", default="", help="Kategori default semua URL posisi")
    parser.add_argument("--max-pages", type=int, default=50, help="Batas halaman per filter")
    parser.add_argument("--delay", type=float, default=2.0, help="Jeda detik antar-halaman")
    parser.add_argument("--product-delay", type=float, default=5.0, help="Jeda detik antar-produk")
    parser.add_argument("--headful", action="store_true", help="Tampilkan jendela browser")
    parser.add_argument(
        "--user-data-dir",
        default=None,
        help="Folder profil browser persisten (WAJIB utk Shopee; simpan sesi login)",
    )
    parser.add_argument(
        "--rating-filters",
        default="5,4,3,2,1",
        help="Daftar bintang ditelusuri per produk (default '5,4,3,2,1'). "
        "Kosongkan ('') untuk tab 'Semua' saja.",
    )
    parser.add_argument(
        "--selectors-json",
        default=None,
        help="File JSON untuk menimpa selektor DOM",
    )
    args = parser.parse_args()

    rating_filters = (
        [int(x) for x in args.rating_filters.split(",") if x.strip()]
        if args.rating_filters
        else None
    )

    products = load_products(args.urls_file, args.urls, args.category)
    selectors = load_selectors(args.selectors_json)

    df = scrape_many(
        products,
        max_pages=args.max_pages,
        delay=args.delay,
        product_delay=args.product_delay,
        headful=args.headful,
        selectors=selectors,
        user_data_dir=args.user_data_dir,
        rating_filters=rating_filters,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"\nOK: {len(df)} ulasan -> {output_path}")
    if not df.empty:
        print(f"Distribusi rating:\n{df['rating'].value_counts().sort_index().to_string()}")


if __name__ == "__main__":
    main()
