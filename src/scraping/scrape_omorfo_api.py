"""
Pengambil ulasan OmorfoShop via endpoint JSON internal Shopee (in-browser fetch).

Pendekatan
----------
Halaman produk Shopee mengambil ulasannya dari endpoint internal
`/api/v2/item/get_ratings`. Anti-bot (DataDome) memblokir request server anonim,
TETAPI fetch *same-origin* dari dalam halaman shopee.co.id yang sudah login membawa
cookie sesi sah & cookie anti-bot, sehingga lolos. Skrip ini:

1. Membuka browser (Chrome asli + penyamaran sinyal otomasi) dengan sesi login
   persisten (`--user-data-dir`).
2. Membuka beranda shopee.co.id (mendapatkan cookie anti-bot yang valid).
3. Menjalankan `fetch('/api/v2/item/get_ratings?...')` DARI DALAM halaman via
   `page.evaluate`, paginasi `offset` sampai habis.
4. Memetakan JSON → skema implementasi & menulis CSV.

Karena `type=0` mengembalikan SEMUA ulasan beserta `rating_star`-nya, diversitas
kelas (1–5 bintang) otomatis terjaga tanpa perlu mengklik filter DOM.

Catatan metodologi (WAJIB diselaraskan di bab metodologi skripsi)
-----------------------------------------------------------------
Ini mengambil **data ulasan publik yang sama** yang dirender halaman produk, namun
via endpoint JSON internal situs (BUKAN render-DOM, BUKAN Shopee Open Platform API
resmi), dieksekusi dari dalam **sesi browser pengguna yang sah**. Privasi: identitas
pelanggan (username/foto) TIDAK disimpan (data minimization). Hanya ulasan publik;
jeda antar-permintaan (rate limiting) dihormati.

Skema keluaran (sama dgn pipeline implementasi):
    [review_id, review_text, rating, product_name, product_category, date_review]

Pemakaian
---------
    # Login sekali (lihat scrape_omorfo_reviews.py) lalu:
    python src/scraping/scrape_omorfo_api.py \
        --url "https://shopee.co.id/...-i.188380895.25462161057" \
        --user-data-dir .shopee_session --category deodorant

    # atau berikan id eksplisit:
    python src/scraping/scrape_omorfo_api.py --shopid 188380895 --itemid 25462161057 ...
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IMPLEMENTATION_COLUMNS = [
    "review_id",
    "review_text",
    "rating",
    "product_name",
    "product_category",
    "date_review",
]

DEFAULT_OUTPUT = "data/implementation/omorfo_reviews.csv"
RATINGS_ENDPOINT = "https://shopee.co.id/api/v2/item/get_ratings"

# Pola id pada URL Shopee: ...-i.<shopid>.<itemid>
_URL_ID_RE = re.compile(r"i\.(\d+)\.(\d+)")

# JS: fetch get_ratings dari dalam halaman (same-origin, bawa cookie sesi).
# `type`: 0=semua, atau filter tab bintang (lihat catatan mapping di fetch_ratings).
_JS_FETCH = """
async ([itemid, shopid, offset, limit, rtype]) => {
  const url = `https://shopee.co.id/api/v2/item/get_ratings?filter=0&flag=1`
    + `&itemid=${itemid}&shopid=${shopid}&type=${rtype}&offset=${offset}&limit=${limit}`;
  const res = await fetch(url, { headers: { 'x-requested-with': 'XMLHttpRequest' },
                                 credentials: 'include' });
  if (!res.ok) return { error: `HTTP ${res.status}` };
  try { return await res.json(); }
  catch (e) { return { error: 'JSON parse gagal (kemungkinan anti-bot)' }; }
}
"""


def parse_ids_from_url(url: str) -> tuple[str, str]:
    """Ambil (shopid, itemid) dari URL produk Shopee."""
    m = _URL_ID_RE.search(url)
    if not m:
        raise ValueError(f"Tidak menemukan pola 'i.<shopid>.<itemid>' di URL: {url}")
    return m.group(1), m.group(2)


def _epoch_to_date(ctime: object) -> str | None:
    """Epoch detik → YYYY-MM-DD (UTC)."""
    try:
        return datetime.fromtimestamp(int(ctime), tz=timezone.utc).date().isoformat()
    except (ValueError, TypeError, OSError):
        return None


def _launch_context(pw, user_data_dir: str | Path | None, headful: bool):
    """Buka persistent context (Chrome asli + penyamaran otomasi) & beranda Shopee."""
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    launch_kwargs = dict(
        headless=not headful,
        locale="id-ID",
        user_agent=ua,
        # chromium_sandbox=True -> JANGAN pakai --no-sandbox (sidik jari otomasi
        # yang dideteksi DataDome + banner "unsupported flag"). Chrome di Windows
        # desktop berjalan normal dengan sandbox aktif.
        chromium_sandbox=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
        ignore_default_args=["--enable-automation"],
    )
    target_dir = str(user_data_dir) if user_data_dir else ".shopee_session_tmp"
    try:
        ctx = pw.chromium.launch_persistent_context(
            target_dir, channel="chrome", **launch_kwargs
        )
        print("[api] pakai Chrome asli (channel=chrome)")
    except Exception as exc:  # noqa: BLE001 — Chrome tak ada → fallback Chromium
        print(f"[api] channel=chrome gagal ({exc}); fallback Chromium")
        ctx = pw.chromium.launch_persistent_context(target_dir, **launch_kwargs)
    # Penyamaran sinyal otomasi yang lazim dicek anti-bot (navigator.webdriver,
    # plugins, languages). Bukan jaminan lolos DataDome, tetapi mengurangi tell.
    ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        "Object.defineProperty(navigator,'languages',{get:()=>['id-ID','id','en-US']});"
        "Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});"
        "window.chrome={runtime:{}};"
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(30000)
    # Beranda → dapatkan cookie anti-bot yang valid dalam sesi login.
    page.goto("https://shopee.co.id", wait_until="domcontentloaded")
    time.sleep(4)
    return ctx, page


def _paginate(
    page,
    *,
    shopid: str,
    itemid: str,
    rating_type: int,
    limit: int,
    max_reviews: int,
    delay: float,
    seen: set[str],
    max_empty_pages: int = 4,
    progress_cb=None,
    diag: dict | None = None,
) -> tuple[list[dict], str | None]:
    """Paginasi satu `type` via in-browser fetch. Tulis ke `seen` (dedup global).

    Berhenti bila: capai max_reviews, halaman kosong, offset >= total, ATAU
    `max_empty_pages` halaman beruntun tanpa ulasan-berkomentar baru (banyak entri
    rating-only di Shopee yang kita lewati — hindari paginasi sia-sia).

    `progress_cb` (opsional): callable(done:int, total:int|None) dipanggil setelah
    tiap halaman — dipakai dashboard Fase 8 untuk progress bar. Default None
    (kompatibel mundur dengan pemakaian CLI Fase 6).
    `diag` (opsional): bila diberikan, alasan kegagalan fetch (mis. error anti-bot)
    ditulis ke `diag['error']` untuk diteruskan ke UI.
    """
    rows: list[dict] = []
    resolved_name: str | None = None
    offset, total = 0, None
    empty_streak = 0
    tag = f"type={rating_type}"
    while len(rows) < max_reviews:
        data = page.evaluate(_JS_FETCH, [itemid, shopid, offset, limit, rating_type])
        if not isinstance(data, dict) or data.get("error"):
            print(f"[api] {tag} gagal di offset {offset}: {data}")
            if diag is not None:
                diag["error"] = (
                    data.get("error")
                    if isinstance(data, dict)
                    else "respons tak terduga dari endpoint"
                )
            break
        payload = data.get("data") or {}
        ratings = payload.get("ratings") or []
        if total is None:
            total = (payload.get("item_rating_summary") or {}).get("rating_total")
        if not ratings:
            break
        new_count = 0
        for r in ratings:
            comment = (r.get("comment") or "").strip()
            if not comment:
                continue  # lewati ulasan kosong (rating-only)
            cmtid = str(r.get("cmtid") or r.get("orderid") or "")
            if cmtid and cmtid in seen:
                continue
            seen.add(cmtid)
            if not resolved_name:
                pinfo = r.get("product_items") or []
                if pinfo and isinstance(pinfo, list):
                    resolved_name = (pinfo[0].get("name") or "").strip()
            rows.append(
                {
                    "review_id": cmtid or _epoch_to_date(r.get("ctime")),
                    "review_text": comment,
                    "rating": r.get("rating_star"),
                    "date_review": _epoch_to_date(r.get("ctime")),
                }
            )
            new_count += 1
        print(f"[api] {tag} offset {offset}: +{new_count} (subtotal {len(rows)})")
        if progress_cb is not None:
            progress_cb(len(rows), total)
        empty_streak = empty_streak + 1 if new_count == 0 else 0
        if empty_streak >= max_empty_pages:
            print(
                f"[api] {tag}: {max_empty_pages} halaman tanpa komentar baru — berhenti"
            )
            break
        offset += limit
        if total and offset >= total:
            break
        time.sleep(delay)
    return rows, resolved_name


def _rows_to_df(
    rows: list[dict], product_name: str, product_category: str
) -> pd.DataFrame:
    """Bungkus list dict → DataFrame berskema implementasi."""
    if not rows:
        return pd.DataFrame(columns=IMPLEMENTATION_COLUMNS)
    df = pd.DataFrame(rows)
    df["product_name"] = product_name
    df["product_category"] = product_category
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").astype("Int64")
    return df[IMPLEMENTATION_COLUMNS].reset_index(drop=True)


def fetch_ratings(
    *,
    shopid: str,
    itemid: str,
    product_name: str = "",
    product_category: str = "",
    limit: int = 50,
    max_reviews: int = 2000,
    delay: float = 1.5,
    user_data_dir: str | Path | None = None,
    headful: bool = True,
    rating_type: int = 0,
    progress_cb=None,
) -> pd.DataFrame:
    """Ambil ulasan satu `type` → DataFrame berskema implementasi.

    `progress_cb` (opsional): diteruskan ke `_paginate` untuk progress dashboard.
    """
    from playwright.sync_api import sync_playwright

    seen: set[str] = set()
    diag: dict = {}
    with sync_playwright() as pw:
        ctx, page = _launch_context(pw, user_data_dir, headful)
        rows, name = _paginate(
            page,
            shopid=shopid,
            itemid=itemid,
            rating_type=rating_type,
            limit=limit,
            max_reviews=max_reviews,
            delay=delay,
            seen=seen,
            progress_cb=progress_cb,
            diag=diag,
        )
        ctx.close()
    if not rows:
        print("[api] 0 ulasan — periksa sesi login / id produk")
    df = _rows_to_df(rows, product_name or (name or ""), product_category)
    if df.empty and diag.get("error"):
        df.attrs["fetch_error"] = diag["error"]
    return df


def run_hybrid(
    *,
    shopid: str,
    itemid: str,
    product_name: str = "",
    product_category: str = "",
    main_target: int = 1200,
    limit: int = 50,
    delay: float = 1.5,
    user_data_dir: str | Path | None = None,
    headful: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Strategi hybrid dalam SATU sesi browser.

    Kembalikan (df_natural, df_minoritas):
    - df_natural   : sampel `type=0` (≤ main_target) — distribusi nyata utk rule engine.
    - df_minoritas : SEMUA ulasan berkomentar bintang 1–4 (`type=1..4`) — bukti model
                     menangkap negatif/netral di data nyata. Dedup global lintas keduanya
                     dihindari (set `seen` terpisah) agar masing-masing utuh & jujur.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        ctx, page = _launch_context(pw, user_data_dir, headful)

        print(f"\n[api] === NATURAL (type=0, target {main_target}) ===")
        seen_nat: set[str] = set()
        nat_rows, name = _paginate(
            page,
            shopid=shopid,
            itemid=itemid,
            rating_type=0,
            limit=limit,
            max_reviews=main_target,
            delay=delay,
            seen=seen_nat,
        )

        print("\n[api] === MINORITAS (type=1..4, ambil semua) ===")
        seen_min: set[str] = set()
        min_rows: list[dict] = []
        for star in (1, 2, 3, 4):
            rows, n2 = _paginate(
                page,
                shopid=shopid,
                itemid=itemid,
                rating_type=star,
                limit=limit,
                max_reviews=10_000,
                delay=delay,
                seen=seen_min,
            )
            min_rows.extend(rows)
            name = name or n2
        ctx.close()

    resolved = product_name or (name or "")
    df_nat = _rows_to_df(nat_rows, resolved, product_category)
    df_min = _rows_to_df(min_rows, resolved, product_category)
    return df_nat, df_min


def run_hybrid_many(
    products: list[dict],
    *,
    main_target_per: int = 1200,
    limit: int = 50,
    delay: float = 1.5,
    product_delay: float = 4.0,
    user_data_dir: str | Path | None = None,
    headful: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Strategi hybrid untuk BANYAK produk dalam SATU sesi browser.

    `products`: list of {"shopid","itemid","category"(opsional),"product_name"(opsional)}.
    Kembalikan (df_natural_gabung, df_minoritas_gabung), dedup global by review_id.
    """
    from playwright.sync_api import sync_playwright

    nat_frames: list[pd.DataFrame] = []
    min_frames: list[pd.DataFrame] = []
    with sync_playwright() as pw:
        ctx, page = _launch_context(pw, user_data_dir, headful)
        for i, p in enumerate(products, start=1):
            shopid, itemid = str(p["shopid"]), str(p["itemid"])
            category = p.get("category", "")
            print(
                f"\n[api] ===== Produk {i}/{len(products)} "
                f"(itemid={itemid}, kategori={category or '-'}) ====="
            )

            print("[api] --- natural (type=0) ---")
            seen_nat: set[str] = set()
            nat_rows, name = _paginate(
                page,
                shopid=shopid,
                itemid=itemid,
                rating_type=0,
                limit=limit,
                max_reviews=main_target_per,
                delay=delay,
                seen=seen_nat,
            )
            print("[api] --- minoritas (type=1..4) ---")
            seen_min: set[str] = set()
            min_rows: list[dict] = []
            for star in (1, 2, 3, 4):
                rows, n2 = _paginate(
                    page,
                    shopid=shopid,
                    itemid=itemid,
                    rating_type=star,
                    limit=limit,
                    max_reviews=10_000,
                    delay=delay,
                    seen=seen_min,
                )
                min_rows.extend(rows)
                name = name or n2

            resolved = p.get("product_name") or (name or "")
            nat_frames.append(_rows_to_df(nat_rows, resolved, category))
            min_frames.append(_rows_to_df(min_rows, resolved, category))
            if i < len(products):
                time.sleep(product_delay)
        ctx.close()

    def _merge(frames: list[pd.DataFrame]) -> pd.DataFrame:
        frames = [f for f in frames if not f.empty]
        if not frames:
            return pd.DataFrame(columns=IMPLEMENTATION_COLUMNS)
        out = pd.concat(frames, ignore_index=True)
        out = out.drop_duplicates(subset="review_id").reset_index(drop=True)
        return out[IMPLEMENTATION_COLUMNS]

    return _merge(nat_frames), _merge(min_frames)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--url", default=None, help="URL produk Shopee (untuk ambil id)"
    )
    parser.add_argument("--shopid", default=None, help="Shop ID (jika tanpa --url)")
    parser.add_argument("--itemid", default=None, help="Item ID (jika tanpa --url)")
    parser.add_argument("--product-name", default="", help="Nama produk (opsional)")
    parser.add_argument("--category", default="", help="Isi kolom product_category")
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT, help=f"CSV keluaran ({DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Ulasan per request (maks ~50)"
    )
    parser.add_argument("--max", type=int, default=2000, help="Batas total ulasan")
    parser.add_argument(
        "--delay", type=float, default=1.5, help="Jeda detik antar-request"
    )
    parser.add_argument(
        "--user-data-dir", default=".shopee_session", help="Profil sesi login"
    )
    parser.add_argument(
        "--type",
        type=int,
        default=0,
        dest="rating_type",
        help="Param 'type' endpoint: 0=semua (natural). Non-0=filter tab bintang.",
    )
    parser.add_argument(
        "--mode",
        choices=["single", "hybrid", "hybrid-multi"],
        default="single",
        help="single=satu type; hybrid=1 produk natural+minoritas; "
        "hybrid-multi=banyak produk (pakai --urls-file) dalam 1 sesi",
    )
    parser.add_argument(
        "--urls-file",
        default=None,
        help='JSON [{"url":..., "category":...}, ...] untuk hybrid-multi',
    )
    parser.add_argument(
        "--main-target",
        type=int,
        default=1200,
        help="Target ulasan natural (mode hybrid)",
    )
    parser.add_argument(
        "--minority-output",
        default="data/implementation/omorfo_reviews_minoritas.csv",
        help="CSV bukti minoritas (mode hybrid)",
    )
    args = parser.parse_args()

    import json

    def _save(df: pd.DataFrame, path: str, label: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(p, index=False, encoding="utf-8")
        print(f"\nOK [{label}]: {len(df)} ulasan -> {p}")
        if not df.empty:
            print(
                f"Distribusi rating:\n{df['rating'].value_counts().sort_index().to_string()}"
            )

    if args.mode == "hybrid-multi":
        if not args.urls_file:
            parser.error("--mode hybrid-multi membutuhkan --urls-file")
        raw = json.loads(Path(args.urls_file).read_text(encoding="utf-8"))
        products = []
        for entry in raw:
            url = entry["url"] if isinstance(entry, dict) else entry
            sid, iid = parse_ids_from_url(url)
            products.append(
                {
                    "shopid": sid,
                    "itemid": iid,
                    "category": (
                        entry.get("category", "") if isinstance(entry, dict) else ""
                    ),
                }
            )
        print(f"[api] hybrid-multi: {len(products)} produk")
        df_nat, df_min = run_hybrid_many(
            products,
            main_target_per=args.main_target,
            limit=args.limit,
            delay=args.delay,
            user_data_dir=args.user_data_dir,
        )
        _save(df_nat, args.output, "natural-gabung")
        _save(df_min, args.minority_output, "minoritas-gabung")
        return

    if args.url:
        shopid, itemid = parse_ids_from_url(args.url)
    elif args.shopid and args.itemid:
        shopid, itemid = args.shopid, args.itemid
    else:
        parser.error("Berikan --url ATAU (--shopid dan --itemid)")

    print(f"[api] shopid={shopid} itemid={itemid} mode={args.mode}")

    if args.mode == "hybrid":
        df_nat, df_min = run_hybrid(
            shopid=shopid,
            itemid=itemid,
            product_name=args.product_name,
            product_category=args.category,
            main_target=args.main_target,
            limit=args.limit,
            delay=args.delay,
            user_data_dir=args.user_data_dir,
        )
        _save(df_nat, args.output, "natural")
        _save(df_min, args.minority_output, "minoritas")
    else:
        df = fetch_ratings(
            shopid=shopid,
            itemid=itemid,
            product_name=args.product_name,
            product_category=args.category,
            limit=args.limit,
            max_reviews=args.max,
            delay=args.delay,
            user_data_dir=args.user_data_dir,
            rating_type=args.rating_type,
        )
        _save(df, args.output, "single")


if __name__ == "__main__":
    main()
