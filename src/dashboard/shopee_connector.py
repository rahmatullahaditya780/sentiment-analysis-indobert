"""
Fase 8 — Module 6: Shopee Review Collector (tiered router).

Jalur **URL Auto-Fetch** (lokal/desktop saja): validasi URL, deteksi lingkungan,
dan pengambilan ulasan. Metode aktif = **mode CDP (Opsi B)**: Chrome ASLI
pengguna diluncurkan dengan remote-debugging (`launch_chrome_cdp`), pengguna
login/selesaikan captcha & cari produk, lalu `cdp_fetch_worker` menempel
(`connect_over_cdp`) untuk fetch — sidik jari otomasi minimal vs DataDome.
`fetch_worker`/`build_worker_command` (launch Playwright) tetap ada sebagai
alternatif tetapi tidak lagi jalur UI utama.

- `validate_shopee_url`  : validasi & ekstraksi (shopid, itemid) dari URL produk
  Shopee (FR-8.10). Mirror regex `i.<shopid>.<itemid>` di
  `src/scraping/scrape_omorfo_api.py`.
- `detect_environment`   : tentukan cloud vs lokal (FR-8.14). Jalur URL Auto-Fetch
  hanya aktif di lokal/desktop (browser ber-login tak tersedia di Streamlit Cloud
  headless — lihat catatan deployment di planning/fase-08-dashboard.md).
- `build_worker_command` : susun argumen CLI `fetch_worker` (clamp cap, FR-8.12).
- `run_fetch_subprocess` : jalankan worker, alirkan event NDJSON ke callback UI
  (progress bar + counter, FR-8.11), kembalikan hasil akhir.
- `render_url_section`   : UI tab URL (badge lingkungan, validasi, fetch+progress).

`validate_shopee_url`, `detect_environment`, `build_worker_command`, &
`parse_progress_line` murni (tanpa Streamlit) agar teruji. `sync_playwright`
diisolasi di proses worker terpisah, bukan di proses Streamlit.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

# Mirror pola id Shopee dari scrape_omorfo_api._URL_ID_RE (sumber kebenaran).
_URL_ID_RE = re.compile(r"i\.(\d+)\.(\d+)")

# Default sesi browser ber-login (persisten) untuk worker fetch & login.
DEFAULT_USER_DATA_DIR = ".shopee_session"
HARD_CAP = 1200  # FR-8.12

# Cookie yang menandakan sesi Shopee sudah login (heuristik, dapat dikalibrasi).
# SPC_EC/SPC_ST = token login; SPC_U = user id ("-1" bila anonim).
_LOGIN_COOKIE_TOKENS = ("SPC_EC", "SPC_ST", "SPC_ST_")
LOGIN_TIMEOUT_DEFAULT = 240  # detik menunggu pengguna login

# ── Mode CDP (Opsi B): tempel ke Chrome ASLI pengguna ─────────────────────────
CDP_PORT = 9222
DEFAULT_CDP_PROFILE = ".shopee_cdp_profile"
_CHROME_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)


def find_chrome() -> str | None:
    """Cari path Chrome ASLI (bukan Chromium Playwright). None bila tak ada."""
    import shutil

    for name in ("chrome", "chrome.exe", "google-chrome", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in _CHROME_CANDIDATES:
        path = Path(os.path.expandvars(candidate))
        if path.exists():
            return str(path)
    return None


def is_cdp_running(port: int = CDP_PORT) -> bool:
    """True bila ada Chrome dengan remote-debugging aktif di `port`."""
    import urllib.request

    try:
        with urllib.request.urlopen(
            f"http://localhost:{port}/json/version", timeout=2
        ) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001 — port tertutup / belum jalan
        return False


def launch_chrome_cdp(
    *,
    port: int = CDP_PORT,
    user_data_dir: str = DEFAULT_CDP_PROFILE,
    start_url: str = "https://shopee.co.id",
    wait: float = 12.0,
) -> dict:
    """Luncurkan Chrome ASLI dengan remote-debugging-port (mode CDP).

    Chrome dibuka sebagai proses lepas (detached) tanpa flag otomasi → sidik jari
    bersih. Mengembalikan {status: 'running'|'launched'|'error', message}.
    """
    if is_cdp_running(port):
        return {"status": "running", "message": "Chrome (mode CDP) sudah berjalan."}

    chrome = find_chrome()
    if not chrome:
        return {
            "status": "error",
            "message": "Google Chrome tidak ditemukan. Pasang Chrome lebih dulu.",
        }

    profile = Path(user_data_dir).resolve()
    profile.mkdir(parents=True, exist_ok=True)
    args = [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile}",
        start_url,
    ]
    creationflags = 0
    if sys.platform == "win32":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP → lepas dari proses Streamlit.
        creationflags = 0x00000008 | 0x00000200
    try:
        subprocess.Popen(
            args,
            creationflags=creationflags,
            start_new_session=(sys.platform != "win32"),
        )
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Gagal meluncurkan Chrome: {exc}"}

    deadline = time.time() + wait
    while time.time() < deadline:
        if is_cdp_running(port):
            return {"status": "launched", "message": "Chrome terbuka (mode CDP)."}
        time.sleep(0.5)
    return {
        "status": "error",
        "message": "Chrome diluncurkan tetapi port debug belum merespons.",
    }


def build_cdp_fetch_command(
    *,
    url: str,
    output: str,
    port: int = CDP_PORT,
    category: str = "",
    max_reviews: int = HARD_CAP,
    delay: float = 1.5,
    python_exe: str | None = None,
) -> list[str]:
    """Susun argumen CLI `cdp_fetch_worker` (clamp cap, FR-8.12). Teruji."""
    cap = max(1, min(int(max_reviews), HARD_CAP))
    return [
        python_exe or sys.executable,
        "-m",
        "src.dashboard.cdp_fetch_worker",
        "--url",
        url,
        "--port",
        str(int(port)),
        "--category",
        category,
        "--max-reviews",
        str(cap),
        "--delay",
        str(delay),
        "--output",
        output,
    ]


# Env var yang, bila ada, menandai lingkungan Streamlit Cloud.
_CLOUD_ENV_MARKERS = ("STREAMLIT_RUNTIME_CLOUD", "STREAMLIT_CLOUD", "STREAMLIT_SHARING")
# Override manual untuk pengujian/penyesuaian: "cloud" | "local".
_ENV_OVERRIDE_VAR = "SENTARA_FORCE_ENV"


def validate_shopee_url(url: str | None) -> dict:
    """Validasi URL produk Shopee & ekstrak (shopid, itemid) (FR-8.10).

    Mengembalikan dict {valid, shopid, itemid, message}. Tidak memunculkan
    exception — cocok untuk umpan balik live di UI.
    """
    result = {"valid": False, "shopid": None, "itemid": None, "message": ""}
    if not isinstance(url, str) or not url.strip():
        result["message"] = "URL masih kosong."
        return result

    url = url.strip()
    if "shopee." not in url.lower():
        result["message"] = "Bukan URL Shopee (domain `shopee.*` tidak ditemukan)."
        return result

    match = _URL_ID_RE.search(url)
    if not match:
        result["message"] = (
            "Pola `i.<shopid>.<itemid>` tidak ditemukan. Salin URL dari halaman "
            "produk Shopee (mis. …-i.188380895.25462161057)."
        )
        return result

    result.update(
        valid=True,
        shopid=match.group(1),
        itemid=match.group(2),
        message=f"URL valid (shopid={match.group(1)}, itemid={match.group(2)}).",
    )
    return result


def detect_environment(*, env: dict | None = None, platform: str | None = None) -> dict:
    """Deteksi lingkungan eksekusi: cloud vs lokal (FR-8.14).

    Mengembalikan {is_cloud: bool, reason: str}. Parameter `env`/`platform` dapat
    diinjeksi untuk pengujian; default membaca `os.environ` & `sys.platform`.

    Heuristik (berurutan):
    1. Override eksplisit `SENTARA_FORCE_ENV=cloud|local`.
    2. Marker env Streamlit Cloud.
    3. Desktop OS (Windows/macOS) -> lokal.
    4. Linux dengan `DISPLAY` -> desktop lokal; tanpa DISPLAY -> diasumsikan
       cloud/server headless.
    """
    env = dict(os.environ) if env is None else env
    platform = sys.platform if platform is None else platform

    override = str(env.get(_ENV_OVERRIDE_VAR, "")).strip().lower()
    if override == "cloud":
        return {"is_cloud": True, "reason": f"Dipaksa via {_ENV_OVERRIDE_VAR}=cloud."}
    if override == "local":
        return {"is_cloud": False, "reason": f"Dipaksa via {_ENV_OVERRIDE_VAR}=local."}

    for marker in _CLOUD_ENV_MARKERS:
        if env.get(marker):
            return {"is_cloud": True, "reason": f"Marker lingkungan cloud: {marker}."}

    if platform in ("win32", "darwin"):
        return {
            "is_cloud": False,
            "reason": f"OS desktop ({platform}) — jalur URL Auto-Fetch aktif.",
        }

    if env.get("DISPLAY"):
        return {"is_cloud": False, "reason": "Linux desktop (DISPLAY tersedia)."}

    return {
        "is_cloud": True,
        "reason": "Linux headless tanpa DISPLAY — diasumsikan cloud/server.",
    }


def build_worker_command(
    *,
    shopid: str,
    itemid: str,
    output: str,
    category: str = "",
    max_reviews: int = HARD_CAP,
    delay: float = 1.5,
    user_data_dir: str = DEFAULT_USER_DATA_DIR,
    python_exe: str | None = None,
) -> list[str]:
    """Susun argumen CLI untuk menjalankan `fetch_worker` sebagai subprocess.

    Cap di-clamp ke `HARD_CAP` (FR-8.12). Murni (tanpa efek samping) agar teruji.
    """
    cap = max(1, min(int(max_reviews), HARD_CAP))
    return [
        python_exe or sys.executable,
        "-m",
        "src.dashboard.fetch_worker",
        "--shopid",
        str(shopid),
        "--itemid",
        str(itemid),
        "--category",
        category,
        "--max-reviews",
        str(cap),
        "--delay",
        str(delay),
        "--user-data-dir",
        user_data_dir,
        "--output",
        output,
    ]


def parse_progress_line(line: str) -> dict | None:
    """Parse satu baris stdout worker -> event NDJSON, atau None bila bukan event.

    Toleran terhadap baris log `[api] ...` (non-JSON) yang ikut tercetak worker.
    """
    line = (line or "").strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except (ValueError, json.JSONDecodeError):
        return None
    if isinstance(obj, dict) and "type" in obj:
        return obj
    return None


def classify_fetch_error(message: str | None) -> dict:
    """Petakan pesan error mentah worker -> kategori + panduan tindak lanjut (FR-8.9).

    Mengembalikan {category, title, guidance}. Murni (tanpa Streamlit) agar teruji.
    Semua panduan mengarahkan ke CSV Upload sebagai fallback yang selalu tersedia.
    """
    text = (message or "").lower()
    fallback = "Sebagai alternatif, gunakan tab **CSV Upload**."

    # invalid_id: hanya pesan spesifik resolusi id (BUKAN frasa 'id produk salah'
    # pada pesan 0-ulasan, yang akarnya anti-bot/login — lihat klausa di bawah).
    if "tidak lengkap" in text or "menemukan pola" in text:
        return {
            "category": "invalid_id",
            "title": "URL / ID produk tidak valid.",
            "guidance": (
                "Salin ulang URL dari halaman produk Shopee "
                f"(mengandung `i.<shopid>.<itemid>`). {fallback}"
            ),
        }
    if any(k in text for k in ("anti-bot", "datadome", "verifikasi", "json parse")):
        return {
            "category": "anti_bot",
            "title": "Terkena verifikasi anti-bot / sesi belum login.",
            "guidance": (
                "Di **jendela Chrome yang terbuka**: login ke Shopee & selesaikan "
                "captcha bila muncul, buka halaman produknya hingga ulasan tampil, "
                f"lalu ulangi. Naikkan jeda antar-permintaan bila perlu. {fallback}"
            ),
        }
    if "login" in text or "0 ulasan" in text or "login-wall" in text:
        return {
            "category": "login_wall",
            "title": "Tidak ada ulasan terambil.",
            "guidance": (
                "Di **jendela Chrome yang terbuka**: pastikan Anda **login ke "
                "Shopee** dan halaman produk menampilkan ulasan, lalu coba lagi. "
                f"Pastikan juga URL produk benar. {fallback}"
            ),
        }
    if "timeout" in text or "timed out" in text:
        return {
            "category": "timeout",
            "title": "Pengambilan melebihi batas waktu (timeout).",
            "guidance": (
                "Koneksi lambat atau Shopee membatasi laju. Naikkan jeda "
                f"antar-permintaan lalu coba lagi. {fallback}"
            ),
        }
    if any(k in text for k in ("net::", "err_", "connection", "koneksi", "dns")):
        return {
            "category": "network",
            "title": "Masalah jaringan saat menghubungi Shopee.",
            "guidance": f"Periksa koneksi internet lalu coba lagi. {fallback}",
        }
    return {
        "category": "unknown",
        "title": "Pengambilan gagal.",
        "guidance": f"{message or 'Kesalahan tidak diketahui.'} {fallback}",
    }


def run_fetch_subprocess(cmd: list[str], *, on_event=None) -> dict:
    """Jalankan worker, alirkan event NDJSON ke `on_event`, kembalikan hasil akhir.

    Mengembalikan {status: 'ok'|'error', path, count, message}. `on_event(event)`
    dipanggil untuk tiap event terstruktur (start/progress/done/error) — dipakai
    UI memperbarui progress bar. Stdout & stderr digabung; baris non-NDJSON
    diabaikan.
    """
    result = {
        "status": "error",
        "path": None,
        "count": 0,
        "message": "Worker tidak menghasilkan event apa pun.",
    }
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        event = parse_progress_line(line)
        if event is None:
            continue
        if on_event is not None:
            on_event(event)
        if event["type"] == "done":
            result = {
                "status": "ok",
                "path": event.get("path"),
                "count": int(event.get("count", 0)),
                "message": "",
            }
        elif event["type"] == "error":
            result = {
                "status": "error",
                "path": None,
                "count": 0,
                "message": event.get("msg", "Kesalahan tidak diketahui."),
            }
    proc.wait()
    if result["status"] == "error" and proc.returncode not in (0, 1, 2):
        result["message"] = (
            f"Worker berhenti tak normal (exit {proc.returncode}). "
            "Periksa sesi browser / koneksi."
        )
    return result


def is_login_cookie(cookies) -> bool:
    """True bila daftar cookie menandakan sesi Shopee sudah login (heuristik).

    Murni (tanpa Streamlit/Playwright) agar teruji. Dipakai login worker untuk
    mendeteksi login selesai.
    """
    for cookie in cookies or []:
        name = cookie.get("name", "")
        value = str(cookie.get("value", "")).strip()
        if (
            name in _LOGIN_COOKIE_TOKENS
            and value
            and value.lower()
            not in (
                "-",
                "null",
                "none",
            )
        ):
            return True
        if name == "SPC_U" and value not in ("", "-1"):
            return True
    return False


def build_login_command(
    *,
    user_data_dir: str = DEFAULT_USER_DATA_DIR,
    timeout: int = LOGIN_TIMEOUT_DEFAULT,
    fresh: bool = False,
    keep_open: bool = False,
    python_exe: str | None = None,
) -> list[str]:
    """Susun argumen CLI untuk menjalankan `login_worker` (subprocess). Teruji.

    `fresh=True` → worker menghapus profil sesi lama dulu (lepas cookie basi).
    `keep_open=True` → browser tetap terbuka setelah login (mode jelajah) sampai
    menerima perintah quit.
    """
    cmd = [
        python_exe or sys.executable,
        "-m",
        "src.dashboard.login_worker",
        "--user-data-dir",
        user_data_dir,
        "--timeout",
        str(int(timeout)),
    ]
    if fresh:
        cmd.append("--fresh")
    if keep_open:
        cmd.append("--keep-open")
    return cmd


def start_browse_session(cmd: list[str], *, on_event=None):
    """Mulai sesi browse (login + browser tetap terbuka). Kembalikan dict hasil.

    Membaca stdout worker sampai `session_ready` (sukses) atau `error`. Pada
    sukses, mengembalikan {status:'ok', proc:Popen} dengan **proc tetap hidup**
    (browser terbuka) — simpan di session_state. `on_event` menerima event
    login_reset/login_open/login_ok untuk umpan balik UI.
    """
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        event = parse_progress_line(line)
        if event is None:
            continue
        if on_event is not None:
            on_event(event)
        if event["type"] == "session_ready":
            return {"status": "ok", "proc": proc, "message": ""}
        if event["type"] == "error":
            try:
                proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                pass
            return {"status": "error", "proc": None, "message": event.get("msg", "")}
    # stdout berakhir tanpa session_ready → worker mati tak terduga.
    try:
        proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        pass
    return {
        "status": "error",
        "proc": None,
        "message": "Sesi browser berakhir sebelum siap.",
    }


def stop_browse_session(proc) -> None:
    """Tutup sesi browse dengan rapi (lepas lock profil agar fetch bisa jalan)."""
    if proc is None:
        return
    try:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.write('{"cmd":"quit"}\n')
            proc.stdin.flush()
    except Exception:  # noqa: BLE001
        pass
    try:
        proc.wait(timeout=8)
    except Exception:  # noqa: BLE001 — paksa tutup bila tak merespons
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass


def render_url_section(st):
    """Render tab URL Auto-Fetch (mode CDP): buka Chrome asli → tempel URL → fetch.

    Mode CDP (Opsi B): Chrome ASLI pengguna diluncurkan dengan remote-debugging;
    pengguna login & cari produk (boleh selesaikan captcha manual), lalu menempel
    URL. Fetch menempel ke Chrome itu (sidik jari otomasi minimal). Mengembalikan
    DataFrame hasil fetch bila ada, atau None.
    """
    env_info = detect_environment()

    if env_info["is_cloud"]:
        st.info(
            "Jalur **URL Auto-Fetch** dinonaktifkan di lingkungan **cloud** "
            "(tanpa browser ber-login). Gunakan tab **CSV Upload** — kumpulkan "
            "data lebih dulu di aplikasi lokal/desktop.",
            icon="☁️",
        )
        st.caption(f"Deteksi lingkungan: {env_info['reason']}")
        return None

    st.caption(f"Deteksi lingkungan: {env_info['reason']}")
    st.info(
        "**Mode CDP** — memakai **Chrome asli** Anda agar lolos anti-bot. "
        "Browser dibuka tanpa flag otomasi; Anda login & selesaikan captcha (bila "
        "ada) langsung di Chrome tersebut.",
        icon="🧭",
    )

    if not is_cdp_running(CDP_PORT):
        st.warning("Chrome (mode CDP) belum berjalan.")
        if st.button("1️⃣ Buka Chrome untuk Shopee", type="primary"):
            with st.spinner("Membuka Chrome…"):
                res = launch_chrome_cdp()
            if res["status"] in ("launched", "running"):
                st.rerun()
            else:
                st.error(res["message"])
        return st.session_state.get("url_fetched_df")

    st.success(
        "✅ Chrome (mode CDP) **aktif** — login & cari produk di jendela Chrome itu "
        "(selesaikan captcha bila muncul), lalu **salin URL produknya** ke bawah.",
        icon="🟢",
    )

    url = st.text_input(
        "URL produk Shopee (salin dari Chrome)",
        placeholder="https://shopee.co.id/...-i.188380895.25462161057",
        key="shopee_url",
    )
    category = st.text_input("Kategori produk (opsional)", key="shopee_category")
    col_a, col_b = st.columns(2)
    max_reviews = col_a.number_input(
        "Maks ulasan", min_value=50, max_value=HARD_CAP, value=HARD_CAP, step=50
    )
    delay = col_b.number_input(
        "Jeda antar-permintaan (detik)",
        min_value=0.5,
        max_value=10.0,
        value=1.5,
        step=0.5,
    )

    check = validate_shopee_url(url) if url else None
    if check is not None:
        (st.success if check["valid"] else st.error)(check["message"])

    if st.button(
        "2️⃣ Ambil Ulasan", disabled=not (check and check["valid"]), type="primary"
    ):
        out_path = str(
            Path(tempfile.gettempdir()) / f"sentara_fetch_{int(time.time())}.csv"
        )
        cmd = build_cdp_fetch_command(
            url=url.strip(),
            output=out_path,
            category=category,
            max_reviews=int(max_reviews),
            delay=float(delay),
        )
        _run_fetch_ui(st, cmd=cmd, cap=int(max_reviews))

    return st.session_state.get("url_fetched_df")


def _run_fetch_ui(st, *, cmd: list[str], cap: int) -> None:
    """Jalankan worker fetch (CDP) via subprocess + progress bar (FR-8.11)."""
    progress = st.progress(0.0)
    status = st.empty()
    cap = max(1, min(int(cap), HARD_CAP))

    def on_event(event: dict) -> None:
        etype = event.get("type")
        if etype == "start":
            status.info(f"Memulai pengambilan (target ≤ {event.get('cap', cap)})…")
        elif etype == "progress":
            done = int(event.get("done", 0))
            progress.progress(min(done / cap, 1.0))
            status.info(f"Terkumpul **{done}** ulasan…")
        elif etype == "error":
            status.error(event.get("msg", "Gagal."))

    result = run_fetch_subprocess(cmd, on_event=on_event)

    if result["status"] == "ok":
        progress.progress(1.0)
        df = pd.read_csv(result["path"])
        st.session_state["url_fetched_df"] = df
        status.success(f"Berhasil mengambil **{result['count']:,} ulasan**.")
        st.dataframe(df.head(), width="stretch")
    else:
        err = classify_fetch_error(result["message"])
        status.error(f"**{err['title']}**")
        st.info(err["guidance"], icon="↩️")
        with st.expander("Detail teknis (untuk diagnosis)"):
            st.code(result.get("message") or "(tidak ada pesan)", language="text")
