"""
Fase 8 — Module 6: fetch via CDP attach ke Chrome asli pengguna (Opsi B).

Berbeda dari `fetch_worker` (yang MELUNCURKAN Chromium via Playwright dengan flag
otomasi → mudah dideteksi DataDome), worker ini **menempel** (`connect_over_cdp`)
ke Chrome asli yang diluncurkan pengguna dengan `--remote-debugging-port`. Karena
browser bukan diluncurkan Playwright, `navigator.webdriver` tetap false & sidik
jari otomasi minimal — peluang lolos anti-bot jauh lebih besar. Pengguna juga bisa
menyelesaikan captcha manual di browser itu.

Alur:
1. `connect_over_cdp(http://localhost:<port>)` → context default Chrome.
2. Buka tab baru, navigasi ke URL produk (sesi & cookie kepercayaan pengguna).
3. `_paginate` in-browser fetch get_ratings → CSV.
4. Tutup HANYA tab yang kita buka; Chrome pengguna dibiarkan terbuka.

Emit NDJSON sama seperti fetch_worker: start / progress / done / error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

HARD_CAP = 1200  # FR-8.12


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CDP fetch worker (NDJSON).")
    parser.add_argument("--url", default="")
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--category", default="")
    parser.add_argument("--max-reviews", type=int, default=HARD_CAP)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    from src.scraping.scrape_omorfo_api import (
        _paginate,
        _rows_to_df,
        parse_ids_from_url,
    )

    try:
        shopid, itemid = parse_ids_from_url(args.url)
    except ValueError as exc:
        _emit({"type": "error", "msg": str(exc)})
        return 2

    cap = max(1, min(int(args.max_reviews), HARD_CAP))
    _emit({"type": "start", "shopid": shopid, "itemid": itemid, "cap": cap})

    def progress_cb(done: int, total) -> None:
        _emit(
            {
                "type": "progress",
                "done": int(done),
                "total": (int(total) if total else None),
                "cap": cap,
            }
        )

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        _emit({"type": "error", "msg": f"Playwright tidak tersedia: {exc}"})
        return 1

    diag: dict = {}
    rows: list[dict] = []
    name = None
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.connect_over_cdp(f"http://localhost:{args.port}")
            except Exception as exc:  # noqa: BLE001
                _emit(
                    {
                        "type": "error",
                        "msg": (
                            f"Gagal menempel ke Chrome di port {args.port}: {exc}. "
                            "Pastikan Chrome dibuka via tombol langkah 1."
                        ),
                    }
                )
                return 1

            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            # Utamakan tab Shopee yang SUDAH dibuka pengguna (cookie & anti-bot
            # sudah "hangat") daripada membuka tab baru + navigasi programatik
            # yang bisa memicu anti-bot. Fetch get_ratings bersifat same-origin,
            # jadi tab Shopee mana pun cukup.
            shopee_pages = [
                p for p in ctx.pages if "shopee.co.id" in (p.url or "").lower()
            ]
            opened_new = False
            if shopee_pages:
                page = shopee_pages[-1]
            else:
                page = ctx.new_page()
                opened_new = True
                try:
                    page.goto(args.url, wait_until="domcontentloaded")
                except Exception:  # noqa: BLE001 — fetch tetap bisa jalan same-origin
                    pass
            rows, name = _paginate(
                page,
                shopid=shopid,
                itemid=itemid,
                rating_type=0,
                limit=50,
                max_reviews=cap,
                delay=args.delay,
                seen=set(),
                progress_cb=progress_cb,
                diag=diag,
            )
            if opened_new:
                try:
                    page.close()  # tutup hanya tab yang KITA buka; tab pengguna tetap
                except Exception:  # noqa: BLE001
                    pass
    except Exception as exc:  # noqa: BLE001
        _emit({"type": "error", "msg": f"{type(exc).__name__}: {exc}"})
        return 1

    df = _rows_to_df(rows, args.category and name or (name or ""), args.category)
    if df.empty:
        reason = diag.get("error")
        total = diag.get("rating_total")
        raw = diag.get("raw_ratings_seen", 0)
        stats = f"rating_total={total}, entri mentah dilihat={raw}"
        if reason:
            # Endpoint mengembalikan error (anti-bot / sesi).
            msg = (
                f"0 ulasan terkumpul. Penyebab teknis: error endpoint {reason} "
                f"({stats}). Kemungkinan verifikasi anti-bot / sesi belum login — "
                "selesaikan captcha/login di Chrome lalu coba lagi."
            )
        elif raw and not len(df):
            # Endpoint memberi ulasan, tetapi semuanya tanpa teks (rating-only).
            msg = (
                f"0 ulasan BERKOMENTAR ({stats}). Endpoint mengembalikan ulasan "
                "tetapi semuanya tanpa teks pada sampel ini — coba produk lain "
                "atau naikkan 'Maks ulasan'."
            )
        else:
            # Tidak ada array ulasan sama sekali (sering = belum login / anti-bot).
            msg = (
                f"0 ulasan terkumpul ({stats}). Endpoint tidak mengembalikan "
                "ulasan — biasanya sesi belum login / cookie anti-bot belum valid "
                "di Chrome ini. Login & buka produk hingga ulasan tampil, lalu ulangi."
            )
        _emit({"type": "error", "msg": msg})
        return 1

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8")
    _emit({"type": "done", "path": str(out), "count": int(len(df))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
