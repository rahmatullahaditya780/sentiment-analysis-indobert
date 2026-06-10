"""
Fase 8 — Unit test Module 6 (klasifikasi error fetch, FR-8.9).
"""

from __future__ import annotations

from src.dashboard.shopee_connector import classify_fetch_error


def test_login_wall():
    err = classify_fetch_error(
        "0 ulasan terkumpul — kemungkinan login-wall / sesi belum login."
    )
    assert err["category"] == "login_wall"


def test_id_tidak_valid():
    assert (
        classify_fetch_error("shopid/itemid tidak lengkap.")["category"] == "invalid_id"
    )
    assert (
        classify_fetch_error("Tidak menemukan pola 'i.<shopid>.<itemid>'")["category"]
        == "invalid_id"
    )


def test_timeout():
    assert (
        classify_fetch_error("TimeoutError: Timeout 30000ms")["category"] == "timeout"
    )


def test_network():
    assert classify_fetch_error("net::ERR_CONNECTION_REFUSED")["category"] == "network"


def test_anti_bot_dari_pesan_json_parse():
    err = classify_fetch_error(
        "0 ulasan terkumpul. Penyebab teknis: JSON parse gagal (kemungkinan "
        "anti-bot). Kemungkinan besar sesi browser belum login Shopee atau "
        "terkena verifikasi anti-bot (DataDome)."
    )
    assert err["category"] == "anti_bot"
    assert "login" in err["guidance"].lower()


def test_pesan_0_ulasan_tidak_salah_klasifikasi_jadi_invalid_id():
    # Regresi: pesan worker lama memuat 'id produk salah' -> keliru invalid_id.
    # Pesan baru tanpa frasa itu harus jatuh ke anti_bot (bukan invalid_id).
    err = classify_fetch_error(
        "0 ulasan terkumpul. Kemungkinan besar sesi browser belum login Shopee "
        "atau terkena verifikasi anti-bot (DataDome)."
    )
    assert err["category"] != "invalid_id"
    assert err["category"] == "anti_bot"


def test_unknown_membawa_pesan_asli():
    err = classify_fetch_error("Sesuatu yang aneh terjadi")
    assert err["category"] == "unknown"
    assert "aneh" in err["guidance"]


def test_semua_kategori_punya_fallback_csv():
    for msg in (
        "login-wall",
        "tidak lengkap",
        "timeout",
        "net::err_x",
        "entah apa",
        None,
    ):
        err = classify_fetch_error(msg)
        assert "csv" in err["guidance"].lower()
        assert {"category", "title", "guidance"} <= err.keys()
