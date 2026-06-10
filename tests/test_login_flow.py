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
    start_browse_session,
    stop_browse_session,
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


def test_login_command_fresh_flag():
    assert "--fresh" not in build_login_command()
    assert "--fresh" in build_login_command(fresh=True)


def test_login_command_keep_open_flag():
    assert "--keep-open" not in build_login_command()
    assert "--keep-open" in build_login_command(keep_open=True)


# ── _wipe_session (login bersih) ──────────────────────────────────────────────
def test_wipe_session_menghapus_dir(tmp_path):
    from src.dashboard.login_worker import _wipe_session

    sess = tmp_path / ".shopee_session"
    sess.mkdir()
    (sess / "Cookies").write_text("stale")
    assert _wipe_session(str(sess)) is True
    assert not sess.exists()


def test_wipe_session_aman_untuk_path_tak_ada(tmp_path):
    from src.dashboard.login_worker import _wipe_session

    assert _wipe_session(str(tmp_path / "tidak_ada")) is False


# ── start/stop_browse_session (fake worker keep-open, tanpa browser) ──────────
def test_start_browse_session_siap_lalu_ditutup():
    # Fake worker: emit session_ready, lalu blok di stdin (browser "terbuka")
    # sampai menerima perintah quit -> keluar.
    fake = (
        "import sys\n"
        'sys.stdout.write(\'{"type":"session_ready"}\\n\'); sys.stdout.flush()\n'
        "sys.stdin.readline()\n"
    )
    cmd = [sys.executable, "-c", fake]
    events = []
    result = start_browse_session(cmd, on_event=events.append)
    assert result["status"] == "ok"
    proc = result["proc"]
    assert proc is not None and proc.poll() is None  # masih hidup (browser terbuka)
    stop_browse_session(proc)  # kirim quit
    assert proc.poll() is not None  # sudah tertutup


def test_start_browse_session_error():
    cmd = [
        sys.executable,
        "-c",
        'print(\'{"type":"error","msg":"Timeout menunggu login (240 dtk)."}\')',
    ]
    result = start_browse_session(cmd)
    assert result["status"] == "error"
    assert result["proc"] is None
    assert "timeout" in result["message"].lower()
