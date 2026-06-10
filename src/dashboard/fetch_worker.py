"""
Fase 8 — Module 6: subprocess entrypoint URL Auto-Fetch (emit progress NDJSON).

Dijalankan oleh dashboard sebagai **proses terpisah** (`python -m
src.dashboard.fetch_worker ...`) agar `sync_playwright` tidak bentrok dengan
event-loop asyncio milik Streamlit. Worker memanggil
`scrape_omorfo_api.fetch_ratings` (endpoint JSON internal, `type=0`) dan
memancarkan baris **NDJSON** ke stdout untuk dibaca induk:

    {"type":"start","shopid":...,"itemid":...,"cap":N}
    {"type":"progress","done":N,"total":M|null,"cap":C}   (tiap halaman)
    {"type":"done","path":"...","count":N}                (sukses)
    {"type":"error","msg":"..."}                          (gagal)

Catatan:
- FR-8.12: cap keras ≤ 1.200 ulasan (dipotong di sini, apa pun argumennya).
- FR-8.13: jeda antar-permintaan via `--delay` diteruskan ke pagination.
- Log `[api] ...` dari modul scraping tetap ke stdout; induk mengabaikan baris
  non-NDJSON (parser toleran), jadi tak perlu dibungkam.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

HARD_CAP = 1200  # FR-8.12: maksimum ulasan per produk


def _emit(obj: dict) -> None:
    """Tulis satu objek sebagai baris NDJSON ke stdout (langsung di-flush)."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="URL Auto-Fetch worker (NDJSON).")
    parser.add_argument("--url", default="")
    parser.add_argument("--shopid", default="")
    parser.add_argument("--itemid", default="")
    parser.add_argument("--category", default="")
    parser.add_argument("--max-reviews", type=int, default=HARD_CAP)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--user-data-dir", default=".shopee_session")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    # Resolusi id: dari URL atau argumen eksplisit.
    shopid, itemid = args.shopid.strip(), args.itemid.strip()
    if args.url:
        from src.scraping.scrape_omorfo_api import parse_ids_from_url

        try:
            shopid, itemid = parse_ids_from_url(args.url)
        except ValueError as exc:
            _emit({"type": "error", "msg": str(exc)})
            return 2
    if not shopid or not itemid:
        _emit({"type": "error", "msg": "shopid/itemid tidak lengkap."})
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

    from src.scraping.scrape_omorfo_api import fetch_ratings

    try:
        df = fetch_ratings(
            shopid=shopid,
            itemid=itemid,
            product_category=args.category,
            max_reviews=cap,
            delay=args.delay,
            user_data_dir=args.user_data_dir,
            progress_cb=progress_cb,
        )
    except Exception as exc:  # noqa: BLE001 — laporkan semua kegagalan via NDJSON
        _emit({"type": "error", "msg": f"{type(exc).__name__}: {exc}"})
        return 1

    if df is None or df.empty:
        reason = df.attrs.get("fetch_error") if df is not None else None
        detail = f" Penyebab teknis: {reason}." if reason else ""
        _emit(
            {
                "type": "error",
                "msg": (
                    f"0 ulasan terkumpul.{detail} Kemungkinan besar sesi browser "
                    "belum login Shopee atau terkena verifikasi anti-bot (DataDome)."
                ),
            }
        )
        return 1

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8")
    _emit({"type": "done", "path": str(out), "count": int(len(df))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
