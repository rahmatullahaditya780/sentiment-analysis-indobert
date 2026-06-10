"""
Fase 8 — Unit test mode CDP (Opsi B): helper murni.

Fetch nyata via CDP butuh Chrome asli + interaksi → verifikasi manual. Di sini
hanya helper yang dapat diuji tanpa browser.
"""

from __future__ import annotations

import sys

from src.dashboard.shopee_connector import (
    CDP_PORT,
    HARD_CAP,
    build_cdp_fetch_command,
    find_chrome,
    is_cdp_running,
)


def test_build_cdp_command_struktur():
    cmd = build_cdp_fetch_command(
        url="https://shopee.co.id/x-i.1.2", output="o.csv", category="serum"
    )
    assert cmd[0] == sys.executable
    assert "src.dashboard.cdp_fetch_worker" in cmd
    assert "--url" in cmd and "https://shopee.co.id/x-i.1.2" in cmd
    assert "--port" in cmd and str(CDP_PORT) in cmd
    assert "--output" in cmd and "o.csv" in cmd


def test_build_cdp_command_clamp_cap():
    cmd = build_cdp_fetch_command(url="u", output="o.csv", max_reviews=99999)
    i = cmd.index("--max-reviews")
    assert cmd[i + 1] == str(HARD_CAP)


def test_find_chrome_mengembalikan_str_atau_none():
    result = find_chrome()
    assert result is None or isinstance(result, str)


def test_is_cdp_running_false_pada_port_tak_terpakai():
    # Port tinggi yang hampir pasti tidak dipakai → False (bukan exception).
    assert is_cdp_running(59999) is False
