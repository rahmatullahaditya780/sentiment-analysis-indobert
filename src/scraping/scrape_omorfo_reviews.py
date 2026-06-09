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

PENTING — Shopee memblokir sesi anonim/headless
------------------------------------------------
Anti-bot Shopee menampilkan login-wall ("Halaman Tidak Tersedia — belum masuk")
untuk browser headless tanpa sesi. Karena itu scraping WAJIB pakai profil browser
persisten yang sudah login:

    # 1) Run pertama: login manual sekali (jendela terbuka 60 detik).
    python src/scraping/scrape_omorfo_reviews.py "<URL>" \
        --user-data-dir .shopee_session --headful --login-wait 60 --category "Deodoran"

    # 2) Run berikutnya: sesi sudah tersimpan, langsung scraping.
    python src/scraping/scrape_omorfo_reviews.py "<URL>" \
        --user-data-dir .shopee_session --max-pages 20 --category "Deodoran"

    # Timpa selektor bila layout Shopee berubah.
    python src/scraping/scrape_omorfo_reviews.py "<URL>" \
        --user-data-dir .shopee_session --selectors-json src/scraping/selectors_shopee.json

Catatan: tambahkan `.shopee_session/` ke .gitignore — berisi cookie sesi pribadi.
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
    # Pill filter rating ("Semua", "5 Bintang", … "1 Bintang") di atas daftar ulasan.
    # Selektor ini mencocokkan SEMUA pill; pemilihan rating spesifik dilakukan dgn
    # mencocokkan teks pill (mis. "5 Bintang"). Lihat _click_rating_filter().
    "rating_filter_button": "div.product-rating-overview__filters div.product-rating-overview__filter",
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


def _click_rating_filter(page, selectors: dict[str, str], rating: int) -> bool:
    """Klik pill filter bintang (mis. "5 Bintang") pada blok ulasan.

    Mencocokkan teks pill yang mengandung "{rating} Bintang". Kembalikan True bila
    pill ditemukan & diklik, False bila tidak ada (selektor berubah / fitur absen)
    sehingga pemanggil bisa degrade graceful ke tab "Semua".
    """
    label = f"{rating} Bintang"
    pills = page.query_selector_all(selectors["rating_filter_button"])
    for pill in pills:
        try:
            text = pill.inner_text().strip()
        except Exception:  # noqa: BLE001 — elemen bisa lepas dari DOM
            continue
        if label in text:
            pill.scroll_into_view_if_needed()
            pill.click()
            return True
    return False


def _harvest_pages(
    page,
    selectors: dict[str, str],
    *,
    collected: list[dict],
    seen_ids: set[str],
    product_name: str,
    max_pages: int,
    delay: float,
    timeout_ms: int,
    label: str = "",
) -> int:
    """Telusuri paginasi ulasan pada tampilan saat ini & kumpulkan ulasan baru.

    Menulis langsung ke `collected`/`seen_ids` (dedup global lintas filter/produk).
    Kembalikan jumlah ulasan baru yang ditambahkan pada pemanggilan ini.
    """
    from playwright.sync_api import TimeoutError as PWTimeout

    tag = f"[{label}] " if label else ""
    added = 0

    # Gulir ke bawah agar blok ulasan ter-render (lazy load) untuk tampilan ini.
    for _ in range(6):
        page.mouse.wheel(0, 2000)
        time.sleep(0.6)

    for page_idx in range(1, max_pages + 1):
        try:
            page.wait_for_selector(selectors["review_item"], timeout=timeout_ms)
        except PWTimeout:
            print(f"[scrape] {tag}tidak ada kartu ulasan di halaman {page_idx} — berhenti")
            break

        new_count = 0
        for row in _extract_reviews_on_page(page, selectors):
            rid = _make_review_id(row["review_text"], row["date_review"])
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            collected.append({"review_id": rid, "product_name": product_name, **row})
            new_count += 1
            added += 1

        print(f"[scrape] {tag}halaman {page_idx}: +{new_count} ulasan baru "
              f"(total {len(collected)})")

        next_btn = page.query_selector(selectors["next_page"])
        if not next_btn:
            print(f"[scrape] {tag}tombol 'berikutnya' tidak aktif — selesai")
            break
        next_btn.scroll_into_view_if_needed()
        next_btn.click()
        time.sleep(delay)

    return added


def scrape_reviews(
    url: str,
    *,
    product_category: str = "",
    max_pages: int = 50,
    delay: float = 2.0,
    headful: bool = False,
    selectors: dict[str, str] | None = None,
    timeout_ms: int = 30_000,
    user_data_dir: str | Path | None = None,
    login_wait: int = 0,
    rating_filters: list[int] | None = None,
) -> pd.DataFrame:
    """Render halaman produk Shopee & kumpulkan ulasan -> DataFrame implementasi.

    Parameters
    ----------
    url : URL halaman produk Shopee OmorfoShop.
    product_category : isian kolom `product_category` (manual; tidak ada di DOM).
    max_pages : batas jumlah halaman ulasan yang ditelusuri (rem pengaman).
    delay : jeda detik antar-halaman (sopan ke server / hindari rate-limit).
    headful : True = tampilkan jendela browser (wajib untuk login pertama kali).
    selectors : override DEFAULT_SELECTORS (lihat load_selectors).
    timeout_ms : timeout navigasi & tunggu elemen.
    user_data_dir : folder profil browser persisten. WAJIB untuk Shopee — anti-bot
        memblokir sesi anonim/headless dengan login-wall. Login sekali (headful),
        cookie tersimpan di folder ini, lalu dipakai ulang otomatis run berikutnya.
    login_wait : detik jeda setelah membuka halaman agar Anda bisa login manual
        (mis. 60). 0 = tidak menunggu (sesi sudah login dari run sebelumnya).
    rating_filters : daftar rating bintang yang ditelusuri satu per satu (mis.
        [5, 4, 3, 2, 1]). Untuk tiap rating, pill filter "{n} Bintang" diklik lalu
        paginasi dipanen — menjaga DIVERSITAS kelas (positif/negatif/netral) karena
        produk populer didominasi ulasan 5 bintang. None = tab "Semua" (perilaku lama).
        Bila pill filter tak ditemukan, otomatis fallback ke tab "Semua".
    """
    # Import lokal supaya proyek tetap bisa di-import tanpa Playwright terpasang.
    from playwright.sync_api import TimeoutError as PWTimeout
    from playwright.sync_api import sync_playwright

    selectors = selectors or dict(DEFAULT_SELECTORS)
    collected: list[dict] = []
    seen_ids: set[str] = set()
    product_name = ""
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    with sync_playwright() as pw:
        # Sesi persisten (login Shopee bertahan antar-run) vs sesi sekali pakai.
        if user_data_dir:
            context = pw.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=not headful,
                locale="id-ID",
                user_agent=user_agent,
            )
            browser = None
            page = context.pages[0] if context.pages else context.new_page()
        else:
            browser = pw.chromium.launch(headless=not headful)
            context = browser.new_context(locale="id-ID", user_agent=user_agent)
            page = context.new_page()
        page.set_default_timeout(timeout_ms)

        print(f"[scrape] membuka {url}")
        page.goto(url, wait_until="domcontentloaded")

        # Jeda login manual: beri waktu user masuk akun di jendela browser.
        if login_wait > 0:
            print(f"[scrape] menunggu {login_wait}s untuk login manual di jendela browser...")
            time.sleep(login_wait)
            # Setelah login, Shopee biasanya me-redirect. Muat ulang URL produk dalam
            # sesi yang sudah login agar konten ulasan tampil (& konteks DOM stabil).
            try:
                page.goto(url, wait_until="domcontentloaded")
            except Exception as exc:  # noqa: BLE001 — navigasi bisa gagal sementara
                print(f"[warn] gagal memuat ulang URL setelah login: {exc}")

        # Pastikan halaman selesai dimuat sebelum membaca DOM (hindari error
        # "execution context was destroyed" saat halaman sedang bernavigasi).
        try:
            page.wait_for_load_state("domcontentloaded")
            body_head = page.inner_text("body")[:300]
        except Exception:  # noqa: BLE001 — defensif terhadap navigasi
            body_head = ""

        # Deteksi login-wall (anti-bot Shopee).
        if "belum masuk" in body_head.lower() or "halaman tidak tersedia" in body_head.lower():
            print("[warn] terdeteksi login-wall Shopee. Jalankan dengan "
                  "--user-data-dir <folder> --headful --login-wait 60 lalu login manual.")

        # Ambil nama produk (sekali saja).
        try:
            name_el = page.wait_for_selector(selectors["product_name"], timeout=timeout_ms)
            product_name = name_el.inner_text().strip() if name_el else ""
        except PWTimeout:
            print("[warn] nama produk tidak ditemukan — selektor mungkin berubah")

        harvest_kwargs = dict(
            collected=collected,
            seen_ids=seen_ids,
            product_name=product_name,
            max_pages=max_pages,
            delay=delay,
            timeout_ms=timeout_ms,
        )

        if rating_filters:
            # Telusuri tiap filter bintang agar diversitas kelas terjaga.
            for rating in rating_filters:
                if _click_rating_filter(page, selectors, rating):
                    time.sleep(delay)  # tunggu daftar ter-refresh setelah filter diklik
                    _harvest_pages(page, selectors, label=f"{rating}★", **harvest_kwargs)
                else:
                    print(f"[warn] pill filter '{rating} Bintang' tak ditemukan — "
                          "selektor 'rating_filter_button' mungkin berubah; lewati")
            if not collected:
                print("[warn] 0 ulasan dari semua filter — fallback ke tab 'Semua'")
                _harvest_pages(page, selectors, **harvest_kwargs)
        else:
            _harvest_pages(page, selectors, **harvest_kwargs)

        context.close()
        if browser is not None:
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
        "--user-data-dir",
        default=None,
        help="Folder profil browser persisten (WAJIB utk Shopee; simpan sesi login)",
    )
    parser.add_argument(
        "--login-wait",
        type=int,
        default=0,
        help="Detik jeda untuk login manual setelah halaman terbuka (mis. 60)",
    )
    parser.add_argument(
        "--selectors-json",
        default=None,
        help="File JSON untuk menimpa selektor DOM (lihat DEFAULT_SELECTORS)",
    )
    parser.add_argument(
        "--rating-filters",
        default=None,
        help="Daftar bintang yang ditelusuri satu per satu, mis. '5,4,3,2,1' "
        "(jaga diversitas kelas). Kosong = tab 'Semua'.",
    )
    args = parser.parse_args()

    rating_filters = (
        [int(x) for x in args.rating_filters.split(",") if x.strip()]
        if args.rating_filters
        else None
    )

    selectors = load_selectors(args.selectors_json)
    df = scrape_reviews(
        args.url,
        product_category=args.category,
        max_pages=args.max_pages,
        delay=args.delay,
        headful=args.headful,
        selectors=selectors,
        user_data_dir=args.user_data_dir,
        login_wait=args.login_wait,
        rating_filters=rating_filters,
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
