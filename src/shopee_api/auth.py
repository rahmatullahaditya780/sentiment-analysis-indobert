"""
Shopee Open Platform — OAuth2 & HMAC-SHA256 signing (Fase 2).

Menangani:
- Pembuatan signature HMAC-SHA256 untuk Public API & Shop API (v2.0).
- Penukaran authorization code -> access_token + refresh_token.
- Refresh otomatis access_token (berlaku 4 jam).

Referensi: https://open.shopee.com/documents (API v2.0).
Kredensial dibaca dari environment variables (lihat .env.example):
    SHOPEE_PARTNER_ID, SHOPEE_PARTNER_KEY, SHOPEE_SHOP_ID, SHOPEE_REDIRECT_URL

CATATAN: belum dapat diuji live sampai kredensial Open Platform tersedia.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass, field

import requests

# Host produksi. Untuk sandbox: https://partner.test-stable.shopeemobile.com
DEFAULT_HOST = "https://partner.shopeemobile.com"
TOKEN_TTL_SECONDS = 4 * 3600  # access_token berlaku 4 jam
REFRESH_MARGIN = 300  # refresh 5 menit sebelum kedaluwarsa


@dataclass
class ShopeeAuth:
    partner_id: int = field(default_factory=lambda: int(os.getenv("SHOPEE_PARTNER_ID", "0")))
    partner_key: str = field(default_factory=lambda: os.getenv("SHOPEE_PARTNER_KEY", ""))
    shop_id: int = field(default_factory=lambda: int(os.getenv("SHOPEE_SHOP_ID", "0")))
    host: str = DEFAULT_HOST

    access_token: str | None = None
    refresh_token: str | None = None
    _expires_at: float = 0.0

    # ── Signing ──────────────────────────────────────────────────────────────
    def _sign(self, base_string: str) -> str:
        return hmac.new(
            self.partner_key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def public_sign(self, api_path: str, timestamp: int) -> str:
        """Signature untuk Public API (mis. get_access_token): id+path+ts."""
        base = f"{self.partner_id}{api_path}{timestamp}"
        return self._sign(base)

    def shop_sign(self, api_path: str, timestamp: int) -> str:
        """Signature untuk Shop API: id+path+ts+access_token+shop_id."""
        base = f"{self.partner_id}{api_path}{timestamp}{self.access_token}{self.shop_id}"
        return self._sign(base)

    def signed_params(self, api_path: str) -> dict:
        """Parameter umum (partner_id, timestamp, sign, access_token, shop_id) untuk Shop API."""
        ts = int(time.time())
        return {
            "partner_id": self.partner_id,
            "timestamp": ts,
            "access_token": self.access_token,
            "shop_id": self.shop_id,
            "sign": self.shop_sign(api_path, ts),
        }

    # ── Token lifecycle ──────────────────────────────────────────────────────
    def fetch_token(self, code: str) -> dict:
        """Tukar authorization code (dari redirect OAuth2) menjadi token."""
        path = "/api/v2/auth/token/get"
        ts = int(time.time())
        url = f"{self.host}{path}"
        body = {"code": code, "partner_id": self.partner_id, "shop_id": self.shop_id}
        params = {"partner_id": self.partner_id, "timestamp": ts, "sign": self.public_sign(path, ts)}
        resp = requests.post(url, params=params, json=body, timeout=20)
        data = resp.json()
        self._store_token(data)
        return data

    def refresh(self) -> dict:
        """Perbarui access_token memakai refresh_token."""
        if not self.refresh_token:
            raise RuntimeError("refresh_token belum tersedia — lakukan fetch_token() dahulu.")
        path = "/api/v2/auth/access_token/get"
        ts = int(time.time())
        url = f"{self.host}{path}"
        body = {
            "refresh_token": self.refresh_token,
            "partner_id": self.partner_id,
            "shop_id": self.shop_id,
        }
        params = {"partner_id": self.partner_id, "timestamp": ts, "sign": self.public_sign(path, ts)}
        resp = requests.post(url, params=params, json=body, timeout=20)
        data = resp.json()
        self._store_token(data)
        return data

    def ensure_valid(self) -> None:
        """Pastikan access_token masih berlaku; refresh otomatis bila perlu."""
        if not self.access_token:
            raise RuntimeError("Belum terautentikasi — panggil fetch_token(code) dahulu.")
        if time.time() >= self._expires_at - REFRESH_MARGIN:
            self.refresh()

    def _store_token(self, data: dict) -> None:
        if "access_token" not in data:
            raise RuntimeError(f"Gagal memperoleh token: {data}")
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        ttl = int(data.get("expire_in", TOKEN_TTL_SECONDS))
        self._expires_at = time.time() + ttl

    def authorization_url(self) -> str:
        """URL yang dibuka seller untuk memberi otorisasi toko (OAuth2)."""
        path = "/api/v2/shop/auth_partner"
        ts = int(time.time())
        redirect = os.getenv("SHOPEE_REDIRECT_URL", "http://localhost:8501")
        return (
            f"{self.host}{path}?partner_id={self.partner_id}"
            f"&timestamp={ts}&sign={self.public_sign(path, ts)}&redirect={redirect}"
        )
