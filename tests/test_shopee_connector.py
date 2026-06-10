"""
Fase 8 — Unit test Module 6 (validasi URL + deteksi lingkungan).

Hanya helper murni; `render_url_section` membungkus widget Streamlit dan
divalidasi manual.
"""

from __future__ import annotations

from src.dashboard.shopee_connector import detect_environment, validate_shopee_url


# ── validate_shopee_url ───────────────────────────────────────────────────────
def test_url_valid_mengekstrak_id():
    res = validate_shopee_url(
        "https://shopee.co.id/Deodorant-Omorfo-i.188380895.25462161057"
    )
    assert res["valid"] is True
    assert res["shopid"] == "188380895"
    assert res["itemid"] == "25462161057"


def test_url_kosong_tidak_valid():
    res = validate_shopee_url("   ")
    assert res["valid"] is False
    assert "kosong" in res["message"].lower()


def test_url_bukan_shopee():
    res = validate_shopee_url("https://tokopedia.com/produk-i.1.2")
    assert res["valid"] is False
    assert "shopee" in res["message"].lower()


def test_url_shopee_tanpa_pola_id():
    res = validate_shopee_url("https://shopee.co.id/halaman-tanpa-id")
    assert res["valid"] is False
    assert "shopid" in res["message"].lower() or "itemid" in res["message"].lower()


def test_url_none():
    assert validate_shopee_url(None)["valid"] is False


# ── detect_environment ────────────────────────────────────────────────────────
def test_override_cloud():
    res = detect_environment(env={"SENTARA_FORCE_ENV": "cloud"}, platform="win32")
    assert res["is_cloud"] is True


def test_override_local():
    res = detect_environment(env={"SENTARA_FORCE_ENV": "local"}, platform="linux")
    assert res["is_cloud"] is False


def test_marker_cloud():
    res = detect_environment(env={"STREAMLIT_RUNTIME_CLOUD": "1"}, platform="linux")
    assert res["is_cloud"] is True


def test_windows_default_lokal():
    res = detect_environment(env={}, platform="win32")
    assert res["is_cloud"] is False


def test_linux_headless_default_cloud():
    res = detect_environment(env={}, platform="linux")
    assert res["is_cloud"] is True


def test_linux_dengan_display_lokal():
    res = detect_environment(env={"DISPLAY": ":0"}, platform="linux")
    assert res["is_cloud"] is False
