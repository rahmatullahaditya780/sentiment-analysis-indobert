"""
Scraper ulasan OmorfoShop (otomasi browser, TANPA API) — data implementasi Fase 6+.

Tujuan
------
Mengambil ulasan publik produk OmorfoShop dari halaman produk Shopee dengan cara
**merender halaman di browser nyata (Playwright/Chromium) lalu membaca DOM**.
Skrip ini TIDAK memanggil endpoint API mana pun (baik Shopee Open Platform resmi
maupun endpoint internal `/api/...`). Yang dibaca hanyalah teks yang sudah tampil
di layar — sama seperti yang dilihat pengunjung biasa.

Output diselaraskan dengan skema dataset implementasi yang dipakai di seluruh
pipeline (lihat `src/shopee_api/normalizer.py` dan `data/implementation/
omorfo_reviews_TEMPLATE.csv`):

    [review_id, review_text, rating, product_name, product_category, date_review]

Etika & metodologi (WAJIB DIBACA)
---------------------------------
- **Privasi (data minimization):** identitas pelanggan (nama/username/foto) TIDAK
  pernah disimpan. Hanya teks ulasan, rating, dan tanggal yang diambil.
- **Hanya ulasan publik OmorfoShop:** dipakai untuk data IMPLEMENTASI/uji teknis
  pipeline, bukan data training.
- **Catatan sumber data:** metode ini adalah scraping DOM, BUKAN Shopee Open
  Platform API resmi yang disebut di CLAUDE.md. Jika dipakai sebagai data final
  skripsi, **samakan klaim "sumber data" di bab metodologi** agar konsisten
  (mis. sebutkan keterbatasan: scraping render-DOM karena kredensial Open
  Platform belum tersedia). Hormati ToS Shopee dan beri jeda antar-permintaan
  (rate limiting) — default sudah konservatif.
- **Selektor rapuh:** struktur HTML Shopee sering berubah & ter-obfuscate. Semua
  selektor dikumpulkan di `DEFAULT_SELECTORS` dan dapat ditimpa lewat
  `--selectors-json` tanpa mengubah kode. Bila scraper mengembalikan 0 ulasan,
  hampir pasti selektornya perlu diperbarui — jalankan dengan `--headful` untuk
  memeriksa halaman secara visual.

Prasyarat
---------
    pip install playwright
    python -m playwright install chromium

Pemakaian
---------
    # Dasar (headless) — keluaran default ke data/implementation/
    python src/scraping/scrape_omorfo_reviews.py "<URL_PRODUK_SHOPEE>"

    # Tampilkan browser, batasi 10 halaman ulasan, kategori manual
    python src/scraping/scrape_omorfo_reviews.py "<URL>" \
        --headful --max-pages 10 --category "Deodoran"

    # Timpa selektor bila layout Shopee berubah
    python src/scraping/scrape_omorfo_reviews.py "<URL>" \
        --selectors-json src/scraping/selectors_shopee.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Skema kanonik dataset implementasi (samakan dgn normalizer.py & template CSV).
IMPLEMENTATION_COLUMNS = [
    "review_id",
    "review_text",
    "rating",
    "product_name",
    "product_category",
    "date_review",
]

DEFAULT_OUTPUT = "data/implementation/omorfo_reviews_scraped.csv"

# ---------------------------------------------------------------------------
# Selektor DOM Shopee. SENGAJA dipusatkan di sini karena paling sering berubah.
# Timpa via --selectors-json (file JSON dengan kunci-kunci yang sama) bila perlu,
# tanpa menyentuh kode. Nilai default mengacu pada struktur blok rating Shopee ID.
# ---------------------------------------------------------------------------
DEFAULT_SELECTORS: dict[str, str] = {
    # Judul produk (di bagian atas halaman).
    "product_name": "div.WBVL_7",
    # Kontainer satu kartu ulasan.
    "review_item": "div.shopee-product-rating",
    # Teks ulasan di dalam kartu.
    "review_text": "div.YNedDV",
    # Bintang aktif (terisi) di dalam kartu — jumlahnya = rating.
    "rating_active_star": "div.repeat-purchase-con svg.icon-rating-solid--active--full",
    # Baris waktu/tanggal ulasan.
    "review_time": "div.shopee-product-rating__time",
    # Tombol "halaman berikutnya" pada paginasi ulasan.
    "next_page": "button.shopee-icon-button--right:not([disabled])",
}

# Pola tanggal Shopee, mis. "2024-02-23 04:20" atau "2024-02-23".
_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def load_selectors(path: str | Path | None) -> dict[str, str]:
    """Gabungkan selektor default dengan file override (bila ada)."""
    selectors = dict(DEFAULT_SELECTORS)
    if path:
        override = json.loads(Path(path).read_text(encoding="utf-8"))
        selectors.update({k: v for k, v in override.items() if k in selectors})
    return selectors


def _make_review_id(text: str, date_review: str | None) -> str:
    """ID ulasan deterministik (SHA1 12-char) dari teks+tanggal.

    DOM Shopee tidak mengekspos comment_id yang andal, jadi ID di-hash dari konten
    agar stabil & memungkinkan deduplikasi konsisten dengan tahap lain.
    """
    basis = f"{text.strip()}|{date_review or ''}".encode("utf-8")
    return hashlib.sha1(basis).hexdigest()[:12]


def _parse_date(raw: str | None) -> str | None:
    """Ambil YYYY-MM-DD dari string waktu Shopee; None bila tidak ditemukan."""
    if not raw:
        return None
    m = _DATE_RE.search(raw)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def _extract_reviews_on_page(page, selectors: dict[str, str]) -> list[dict]:
    """Baca semua kartu ulasan yang sedang terlihat di DOM halaman aktif."""
    rows: list[dict] = []
    cards = page.query_selector_all(selectors["review_item"])
    for card in cards:
        text_el = card.query_selector(selectors["review_text"])
        text = (text_el.inner_text().strip() if text_el else "")
        if not text:
            continue  # lewati ulasan kosong (rating-only) — konsisten normalizer

        rating = len(card.query_selector_all(selectors["rating_active_star"]))
        time_el = card.query_selector(selectors["review_time"])
        date_review = _parse_date(time_el.inner_text() if time_el else None)

        rows.append(
            {
                "review_text": text,
                "rating": rating if rating > 0 else None,
                "date_review": date_review,
            }
        )
    return rows


def scrape_reviews(
    url: str,
    *,
    product_category: str = "",
    max_pages: int = 50,
    delay: float = 2.0,
    headful: bool = False,
    selectors: dict[str, str] | None = None,
    timeout_ms: int = 30_000,
) -> pd.DataFrame:
    """Render halaman produk Shopee & kumpulkan ulasan -> DataFrame implementasi.

    Parameters
    ----------
    url : URL halaman produk Shopee OmorfoShop.
    product_category : isian kolom `product_category` (manual; tidak ada di DOM).
    max_pages : batas jumlah halaman ulasan yang ditelusuri (rem pengaman).
    delay : jeda detik antar-halaman (sopan ke server / hindari rate-limit).
    headful : True = tampilkan jendela browser (berguna untuk debugging selektor).
    selectors : override DEFAULT_SELECTORS (lihat load_selectors).
    timeout_ms : timeout navigasi & tunggu elemen.
    """
    # Import lokal supaya proyek tetap bisa di-import tanpa Playwright terpasang.
    from playwright.sync_api import TimeoutError as PWTimeout
    from playwright.sync_api import sync_playwright

    selectors = selectors or dict(DEFAULT_SELECTORS)
    collected: list[dict] = []
    seen_ids: set[str] = set()
    product_name = ""

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headful)
        # User-agent realistis; locale Indonesia agar tanggal/format konsisten.
        context = browser.new_context(
            locale="id-ID",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        print(f"[scrape] membuka {url}")
        page.goto(url, wait_until="domcontentloaded")

        # Ambil nama produk (sekali saja).
        try:
            name_el = page.wait_for_selector(selectors["product_name"], timeout=timeout_ms)
            product_name = name_el.inner_text().strip() if name_el else ""
        except PWTimeout:
            print("[warn] nama produk tidak ditemukan — selektor mungkin berubah")

        # Gulir ke bawah agar blok ulasan ter-render (lazy load).
        for _ in range(6):
            page.mouse.wheel(0, 2000)
            time.sleep(0.6)

        for page_idx in range(1, max_pages + 1):
            try:
                page.wait_for_selector(selectors["review_item"], timeout=timeout_ms)
            except PWTimeout:
                print(f"[warn] tidak ada kartu ulasan di halaman {page_idx} — berhenti")
                break

            page_rows = _extract_reviews_on_page(page, selectors)
            new_count = 0
            for row in page_rows:
                rid = _make_review_id(row["review_text"], row["date_review"])
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)
                collected.append({"review_id": rid, "product_name": product_name, **row})
                new_count += 1

            print(f"[scrape] halaman {page_idx}: +{new_count} ulasan baru "
                  f"(total {len(collected)})")

            # Pindah ke halaman ulasan berikutnya.
            next_btn = page.query_selector(selectors["next_page"])
            if not next_btn:
                print("[scrape] tombol 'berikutnya' tidak aktif — selesai")
                break
            next_btn.scroll_into_view_if_needed()
            next_btn.click()
            time.sleep(delay)

        context.close()
        browser.close()

    df = pd.DataFrame(collected)
    if df.empty:
        print("[warn] 0 ulasan terkumpul — periksa selektor (jalankan --headful)")
        return pd.DataFrame(columns=IMPLEMENTATION_COLUMNS)

    df["product_category"] = product_category
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype("Int64")
    return df[IMPLEMENTATION_COLUMNS].reset_index(drop=True)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="URL halaman produk Shopee OmorfoShop")
    parser.add_argument(
        "output",
        nargs="?",
        default=DEFAULT_OUTPUT,
        help=f"Path CSV keluaran (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument("--category", default="", help="Isi kolom product_category")
    parser.add_argument("--max-pages", type=int, default=50, help="Batas halaman ulasan")
    parser.add_argument("--delay", type=float, default=2.0, help="Jeda detik antar-halaman")
    parser.add_argument("--headful", action="store_true", help="Tampilkan jendela browser")
    parser.add_argument(
        "--selectors-json",
        default=None,
        help="File JSON untuk menimpa selektor DOM (lihat DEFAULT_SELECTORS)",
    )
    args = parser.parse_args()

    selectors = load_selectors(args.selectors_json)
    df = scrape_reviews(
        args.url,
        product_category=args.category,
        max_pages=args.max_pages,
        delay=args.delay,
        headful=args.headful,
        selectors=selectors,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"\nOK: {len(df)} ulasan -> {output_path}")
    if not df.empty:
        dist = df["rating"].value_counts().sort_index().to_string()
        print(f"Distribusi rating:\n{dist}")


if __name__ == "__main__":
    main()
