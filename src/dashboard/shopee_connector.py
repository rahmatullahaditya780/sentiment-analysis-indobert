"""
Fase 8 — Module 6: Shopee Review Collector (tiered router) — bagian non-fetch.

Langkah ini menyediakan fondasi jalur **URL Auto-Fetch** tanpa menjalankan fetch
nyata (itu menyusul: subprocess + progress NDJSON):

- `validate_shopee_url`  : validasi & ekstraksi (shopid, itemid) dari URL produk
  Shopee (FR-8.10). Mirror regex `i.<shopid>.<itemid>` di
  `src/scraping/scrape_omorfo_api.py`.
- `detect_environment`   : tentukan cloud vs lokal (FR-8.14). Jalur URL Auto-Fetch
  hanya aktif di lokal/desktop (browser ber-login tak tersedia di Streamlit Cloud
  headless — lihat catatan deployment di planning/fase-08-dashboard.md).
- `render_url_section`   : UI tab URL (badge lingkungan + validasi URL). Tombol
  Fetch dinonaktifkan sampai engine fetch dibangun pada langkah berikutnya.

`validate_shopee_url` & `detect_environment` murni (tanpa Streamlit) agar teruji.
"""

from __future__ import annotations

import os
import re
import sys

# Mirror pola id Shopee dari scrape_omorfo_api._URL_ID_RE (sumber kebenaran).
_URL_ID_RE = re.compile(r"i\.(\d+)\.(\d+)")

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


def render_url_section(st) -> None:
    """Render tab URL Auto-Fetch (langkah 7: badge lingkungan + validasi URL).

    Engine fetch (subprocess + progress) menyusul pada langkah berikutnya; tombol
    Fetch sengaja dinonaktifkan di sini.
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
        return

    st.success(
        "Lingkungan **lokal/desktop** terdeteksi — jalur URL Auto-Fetch tersedia."
    )
    st.caption(f"Deteksi lingkungan: {env_info['reason']}")

    url = st.text_input(
        "URL produk Shopee",
        placeholder="https://shopee.co.id/...-i.188380895.25462161057",
        key="shopee_url",
    )
    if url:
        check = validate_shopee_url(url)
        if check["valid"]:
            st.success(check["message"])
        else:
            st.error(check["message"])

    st.button(
        "🔗 Ambil Ulasan",
        disabled=True,
        help="Engine pengambilan ulasan diaktifkan pada langkah implementasi berikutnya.",
    )
    st.caption(
        "Pengambilan otomatis (endpoint JSON internal via sesi browser ber-login) "
        "akan diaktifkan pada tahap berikutnya."
    )
