"""
Fase 8 — Unit test Module 6 (worker fetch + plumbing subprocess).

Menguji bagian yang BISA divalidasi tanpa Shopee/Playwright:
- `parse_progress_line`  : toleransi baris log & event NDJSON.
- `build_worker_command` : susunan argumen + clamp cap (FR-8.12).
- `run_fetch_subprocess` : plumbing end-to-end via jalur ERROR worker (id tak
  lengkap) — tak butuh sesi browser.

Fetch nyata ke Shopee (sukses) memerlukan sesi browser ber-login → verifikasi
manual di desktop.
"""

from __future__ import annotations

import sys

from src.dashboard.shopee_connector import (
    HARD_CAP,
    build_worker_command,
    parse_progress_line,
    run_fetch_subprocess,
)


# ── parse_progress_line ───────────────────────────────────────────────────────
def test_parse_event_valid():
    ev = parse_progress_line('{"type":"progress","done":50,"total":200}')
    assert ev["type"] == "progress" and ev["done"] == 50


def test_parse_abaikan_log_non_json():
    assert parse_progress_line("[api] type=0 offset 0: +50 (subtotal 50)") is None
    assert parse_progress_line("") is None
    assert parse_progress_line("   ") is None


def test_parse_abaikan_json_tanpa_type():
    assert parse_progress_line('{"foo":1}') is None


# ── build_worker_command ──────────────────────────────────────────────────────
def test_command_berisi_modul_dan_argumen():
    cmd = build_worker_command(shopid="1", itemid="2", output="o.csv", category="serum")
    assert cmd[0] == sys.executable
    assert "src.dashboard.fetch_worker" in cmd
    assert "--shopid" in cmd and "1" in cmd
    assert "--output" in cmd and "o.csv" in cmd


def test_command_clamp_cap():
    cmd = build_worker_command(
        shopid="1", itemid="2", output="o.csv", max_reviews=99999
    )
    i = cmd.index("--max-reviews")
    assert cmd[i + 1] == str(HARD_CAP)


# ── run_fetch_subprocess (jalur error, tanpa Shopee) ──────────────────────────
def test_subprocess_error_saat_id_tak_lengkap():
    # Worker dipanggil tanpa shopid/itemid -> emit event error, exit 2.
    cmd = [
        sys.executable,
        "-m",
        "src.dashboard.fetch_worker",
        "--output",
        "x.csv",
    ]
    events = []
    result = run_fetch_subprocess(cmd, on_event=events.append)
    assert result["status"] == "error"
    assert "tidak lengkap" in result["message"].lower()
    assert any(e["type"] == "error" for e in events)


def test_subprocess_error_url_tak_valid():
    cmd = [
        sys.executable,
        "-m",
        "src.dashboard.fetch_worker",
        "--url",
        "https://contoh.com/tanpa-id",
        "--output",
        "x.csv",
    ]
    result = run_fetch_subprocess(cmd)
    assert result["status"] == "error"
