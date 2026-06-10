"""
Fase 8 — Unit test alur login Shopee (helper murni + plumbing subprocess).

Login nyata ke Shopee butuh interaksi manusia + browser → verifikasi manual.
Di sini hanya bagian yang dapat diuji otomatis: deteksi cookie login, penyusunan
command, dan pemetaan event NDJSON `run_login_subprocess`.
"""

from __future__ import annotations

import sys

from src.dashboard.shopee_connector import (
    build_login_command,
    is_login_cookie,
    run_login_subprocess,
)


# ── is_login_cookie ───────────────────────────────────────────────────────────
def test_login_terdeteksi_dari_token():
    assert is_login_cookie([{"name": "SPC_EC", "value": "abc123"}]) is True


def test_login_terdeteksi_dari_spc_u_valid():
    assert is_login_cookie([{"name": "SPC_U", "value": "880012345"}]) is True


def test_belum_login_saat_spc_u_anonim():
    assert is_login_cookie([{"name": "SPC_U", "value": "-1"}]) is False


def test_belum_login_saat_token_kosong():
    assert is_login_cookie([{"name": "SPC_EC", "value": ""}]) is False


def test_belum_login_tanpa_cookie_relevan():
    assert is_login_cookie([{"name": "csrftoken", "value": "x"}]) is False
    assert is_login_cookie([]) is False
    assert is_login_cookie(None) is False


# ── build_login_command ───────────────────────────────────────────────────────
def test_login_command_struktur():
    cmd = build_login_command(user_data_dir=".sess", timeout=120)
    assert cmd[0] == sys.executable
    assert "src.dashboard.login_worker" in cmd
    assert "--user-data-dir" in cmd and ".sess" in cmd
    i = cmd.index("--timeout")
    assert cmd[i + 1] == "120"


# ── run_login_subprocess (fake emitter, tanpa browser) ────────────────────────
def test_run_login_ok_already():
    cmd = [
        sys.executable,
        "-c",
        'print(\'{"type":"login_ok","already":true}\')',
    ]
    events = []
    result = run_login_subprocess(cmd, on_event=events.append)
    assert result["status"] == "ok"
    assert result["already"] is True
    assert any(e["type"] == "login_ok" for e in events)


def test_run_login_error():
    cmd = [
        sys.executable,
        "-c",
        'print(\'{"type":"error","msg":"Timeout menunggu login (240 dtk)."}\')',
    ]
    result = run_login_subprocess(cmd)
    assert result["status"] == "error"
    assert "timeout" in result["message"].lower()
