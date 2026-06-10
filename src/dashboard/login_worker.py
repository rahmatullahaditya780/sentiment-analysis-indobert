"""
Fase 8 — Module 6: subprocess login Shopee (tangkap sesi persisten).

Membuka browser **headful** dengan profil persisten (`--user-data-dir`),
mengarahkan ke halaman login Shopee, lalu menunggu pengguna login sambil memantau
cookie. Begitu sesi terdeteksi login, browser ditutup & sesi tersimpan untuk
dipakai `fetch_worker`.

Dijalankan sebagai proses terpisah agar `sync_playwright` tak bentrok dengan
event-loop asyncio Streamlit. Emit baris **NDJSON** ke stdout:

    {"type":"login_open"}                 (browser siap, menunggu pengguna)
    {"type":"login_ok","already":bool}    (sesi terdeteksi login)
    {"type":"error","msg":"..."}          (timeout / browser ditutup / gagal)

`already=True` berarti sesi memang sudah login sebelumnya (tak perlu input).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOGIN_URL = "https://shopee.co.id/buyer/login"


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Login Shopee worker (NDJSON).")
    parser.add_argument("--user-data-dir", default=".shopee_session")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--poll", type=float, default=3.0)
    args = parser.parse_args(argv)

    from src.dashboard.shopee_connector import is_login_cookie
    from src.scraping.scrape_omorfo_api import _launch_context

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        _emit({"type": "error", "msg": f"Playwright tidak tersedia: {exc}"})
        return 1

    try:
        with sync_playwright() as pw:
            # _launch_context membuka homepage (mendapatkan cookie anti-bot) headful.
            ctx, page = _launch_context(pw, args.user_data_dir, True)

            if is_login_cookie(ctx.cookies()):
                _emit({"type": "login_ok", "already": True})
                ctx.close()
                return 0

            try:
                page.goto(LOGIN_URL, wait_until="domcontentloaded")
            except Exception:  # noqa: BLE001 — lanjut; pengguna bisa navigasi sendiri
                pass
            _emit({"type": "login_open"})

            deadline = time.time() + args.timeout
            while time.time() < deadline:
                try:
                    cookies = ctx.cookies()
                except Exception as exc:  # noqa: BLE001 — browser ditutup pengguna
                    _emit(
                        {
                            "type": "error",
                            "msg": f"Browser tertutup sebelum login selesai: {exc}",
                        }
                    )
                    return 1
                if is_login_cookie(cookies):
                    _emit({"type": "login_ok", "already": False})
                    ctx.close()
                    return 0
                time.sleep(args.poll)

            _emit(
                {
                    "type": "error",
                    "msg": f"Timeout menunggu login ({args.timeout} dtk).",
                }
            )
            ctx.close()
            return 1
    except Exception as exc:  # noqa: BLE001
        _emit({"type": "error", "msg": f"{type(exc).__name__}: {exc}"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
