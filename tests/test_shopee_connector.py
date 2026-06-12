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


# ── split_quota (multi-URL: kuota dibagi rata, FR-8.12 terjaga) ───────────────
def test_split_quota_dua_url_sama_rata():
    from src.dashboard.shopee_connector import split_quota

    assert split_quota(1200, 2) == [600, 600]


def test_split_quota_sisa_dibagikan_ke_awal():
    from src.dashboard.shopee_connector import split_quota

    assert split_quota(1000, 3) == [334, 333, 333]
    assert sum(split_quota(1000, 3)) == 1000


def test_split_quota_satu_url_penuh():
    from src.dashboard.shopee_connector import split_quota

    assert split_quota(1200, 1) == [1200]


def test_split_quota_clamp_ke_hard_cap():
    from src.dashboard.shopee_connector import HARD_CAP, split_quota

    assert sum(split_quota(99999, 2)) == HARD_CAP


def test_split_quota_n_nol_kosong():
    from src.dashboard.shopee_connector import split_quota

    assert split_quota(1200, 0) == []


# ── combine_fetch_results (gabung multi-produk + dedup) ───────────────────────
def test_combine_gabung_dan_dedup_review_id():
    import pandas as pd

    from src.dashboard.shopee_connector import combine_fetch_results

    a = pd.DataFrame({"review_id": [1, 2], "review_text": ["x", "y"]})
    b = pd.DataFrame({"review_id": [2, 3], "review_text": ["y", "z"]})
    out = combine_fetch_results([a, b])
    assert list(out["review_id"]) == [1, 2, 3]


def test_combine_abaikan_none_dan_kosong():
    import pandas as pd

    from src.dashboard.shopee_connector import combine_fetch_results

    a = pd.DataFrame({"review_text": ["x"]})
    out = combine_fetch_results([None, pd.DataFrame(), a])
    assert len(out) == 1


def test_combine_semua_kosong():
    from src.dashboard.shopee_connector import combine_fetch_results

    assert combine_fetch_results([]).empty


# ── product_key & plan_fetches (fetch berkelanjutan dengan simpanan sesi) ─────
def test_product_key_dari_url_valid():
    from src.dashboard.shopee_connector import product_key

    assert (
        product_key("https://shopee.co.id/produk-i.188380895.25462161057")
        == "188380895.25462161057"
    )


def test_product_key_none_bila_tak_valid():
    from src.dashboard.shopee_connector import product_key

    assert product_key("https://tokopedia.com/x-i.1.2") is None
    assert product_key("") is None
    assert product_key(None) is None


_URL_A = "https://shopee.co.id/a-i.111.222"
_URL_B = "https://shopee.co.id/b-i.333.444"


def test_plan_tanpa_cache_semua_diambil():
    from src.dashboard.shopee_connector import plan_fetches

    plan = plan_fetches([(_URL_A, "serum"), (_URL_B, "")], set(), 1200)
    assert [p["skip"] for p in plan] == [False, False]
    assert [p["quota"] for p in plan] == [600, 600]
    assert plan[0]["key"] == "111.222"


def test_plan_produk_tersimpan_dilewati_kuota_tetap():
    from src.dashboard.shopee_connector import plan_fetches

    plan = plan_fetches([(_URL_A, ""), (_URL_B, "")], {"111.222"}, 1200)
    assert plan[0]["skip"] is True
    # Kuota link baru tetap total / jumlah SEMUA link (keputusan pengguna).
    assert plan[1]["skip"] is False
    assert plan[1]["quota"] == 600


def test_plan_duplikat_baris_dilewati():
    from src.dashboard.shopee_connector import plan_fetches

    plan = plan_fetches([(_URL_A, ""), (_URL_A, "lain")], set(), 1200)
    assert plan[0]["skip"] is False
    assert plan[1]["skip"] is True


def test_plan_entri_kosong():
    from src.dashboard.shopee_connector import plan_fetches

    assert plan_fetches([], set(), 1200) == []
