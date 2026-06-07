"""
Shopee Open Platform — API client (Fase 2).

Menyediakan:
- get_item_list   : daftar produk toko (untuk dropdown product selector).
- get_rating      : ulasan/komentar produk (endpoint v2 /product/get_comment),
                    dengan pagination otomatis + retry exponential backoff.

Mengikuti spesifikasi TRD v2: max page_size 50/request, maks 20 iterasi,
hingga 1.000 ulasan atau has_next_page=false. Menghormati rate limit dengan
jeda antar request + retry.

CATATAN: belum dapat diuji live sampai kredensial Open Platform tersedia.
"""

from __future__ import annotations

import time

import requests

from src.shopee_api.auth import ShopeeAuth

MAX_PAGE_SIZE = 50  # batas Shopee per request untuk komentar
MAX_ITERATIONS = 20  # 20 x 50 = 1.000 ulasan
MAX_REVIEWS = 1000
REQUEST_PAUSE = 0.5  # jeda antar request (rate limit)
MAX_RETRIES = 3
BACKOFF_BASE = 1.5


class ShopeeClient:
    def __init__(self, auth: ShopeeAuth | None = None):
        self.auth = auth or ShopeeAuth()

    # ── HTTP dengan retry/backoff ────────────────────────────────────────────
    def _get(self, api_path: str, extra_params: dict | None = None) -> dict:
        self.auth.ensure_valid()
        url = f"{self.auth.host}{api_path}"
        params = self.auth.signed_params(api_path)
        if extra_params:
            params.update(extra_params)

        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, params=params, timeout=20)
                data = resp.json()
                if data.get("error"):
                    # Error API (token, signature, rate limit) -> retry terbatas
                    raise RuntimeError(f"Shopee API error: {data.get('error')} — {data.get('message')}")
                return data
            except (requests.RequestException, RuntimeError) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_BASE ** attempt)
                    # signature memakai timestamp -> regenerasi tiap percobaan
                    params = self.auth.signed_params(api_path)
                    if extra_params:
                        params.update(extra_params)
        raise RuntimeError(f"Gagal setelah {MAX_RETRIES} percobaan: {last_exc}")

    # ── Endpoints ────────────────────────────────────────────────────────────
    def get_item_list(self, offset: int = 0, page_size: int = 50, item_status: str = "NORMAL") -> dict:
        """Daftar item toko. Mengembalikan respons mentah (item_id list + has_next)."""
        path = "/api/v2/product/get_item_list"
        return self._get(path, {"offset": offset, "page_size": page_size, "item_status": item_status})

    def get_item_base_info(self, item_id_list: list[int]) -> dict:
        """Info dasar produk (nama, kategori) untuk daftar item_id."""
        path = "/api/v2/product/get_item_base_info"
        ids = ",".join(str(i) for i in item_id_list)
        return self._get(path, {"item_id_list": ids})

    def get_rating(
        self,
        item_id: int,
        max_reviews: int = MAX_REVIEWS,
        progress_cb=None,
    ) -> list[dict]:
        """Ambil ulasan produk dengan pagination otomatis.

        Endpoint v2: /api/v2/product/get_comment (field: comment, rating_star, ctime).
        progress_cb(collected, target) opsional untuk progress bar dashboard.
        """
        path = "/api/v2/product/get_comment"
        collected: list[dict] = []
        cursor = ""

        for _ in range(MAX_ITERATIONS):
            params = {"item_id": item_id, "cursor": cursor, "page_size": MAX_PAGE_SIZE}
            data = self._get(path, params)
            resp = data.get("response", {})
            batch = resp.get("item_comment_list", []) or resp.get("comment_list", [])
            collected.extend(batch)

            if progress_cb:
                progress_cb(min(len(collected), max_reviews), max_reviews)

            if len(collected) >= max_reviews:
                collected = collected[:max_reviews]
                break
            if not resp.get("has_next_page", False):
                break
            cursor = resp.get("next_cursor", "")
            time.sleep(REQUEST_PAUSE)

        return collected
