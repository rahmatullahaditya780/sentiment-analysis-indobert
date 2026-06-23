"""
Fase 10 — Mekanisme logging terpusat (FR-10.4).

Menyediakan logging ringan untuk mendeteksi error & memantau performa sistem
(load model, fetch ulasan, analisis) tanpa mengubah perilaku modul mana pun.

Desain
------
- Logger bernamespace tunggal ``"sentara"`` (bukan root) agar tidak mengganggu
  logging library pihak ketiga (transformers, urllib3, dll.).
- Dua handler: **stream** (stderr — tampil di konsol/Streamlit Cloud logs) dan
  **file** (``outputs/logs/app.log`` — sudah di-gitignore). File handler bersifat
  *best-effort*: bila filesystem read-only/ephemeral (mis. sebagian cloud),
  kegagalan membuat file diabaikan dan logging tetap jalan via stderr.
- Level dibaca dari env ``LOG_LEVEL`` (default ``INFO``).
- ``configure_logging()`` **idempoten** — aman dipanggil berulang (mis. tiap
  rerun Streamlit) tanpa menduplikasi handler.

Pemakaian
---------
    from src.utils.logging_setup import configure_logging, get_logger

    configure_logging()              # sekali di entry point (app.py)
    log = get_logger(__name__)       # di modul mana pun
    log.info("memuat model dari %s", model_dir)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Root logger namespace proyek. Semua get_logger() berada di bawah ini.
_ROOT_LOGGER_NAME = "sentara"

# Lokasi file log (selaras config.py: outputs/logs/, di-gitignore).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOG_DIR = _PROJECT_ROOT / "outputs" / "logs"
_LOG_FILE = _LOG_DIR / "app.log"

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Penanda agar handler tidak dipasang dua kali (idempotensi).
_CONFIGURED_FLAG = "_sentara_configured"


def _resolve_level(level: str | int | None) -> int:
    """Terjemahkan level (arg > env LOG_LEVEL > INFO) ke konstanta logging."""
    raw = level if level is not None else os.getenv("LOG_LEVEL", "INFO")
    if isinstance(raw, int):
        return raw
    return logging.getLevelName(str(raw).strip().upper()) if raw else logging.INFO


def configure_logging(level: str | int | None = None) -> logging.Logger:
    """Pasang handler stream + file pada logger ``"sentara"`` (idempoten).

    Mengembalikan logger root proyek. Dipanggil sekali di entry point; pemanggilan
    berulang hanya menyesuaikan level tanpa menambah handler.
    """
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    resolved = _resolve_level(level)
    if not isinstance(resolved, int):  # nama level tak dikenal -> INFO
        resolved = logging.INFO
    logger.setLevel(resolved)
    # Jangan teruskan ke root agar pesan tak tercetak ganda bila app lain
    # mengonfigurasi root logger.
    logger.propagate = False

    if getattr(logger, _CONFIGURED_FLAG, False):
        return logger

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler best-effort — diabaikan bila FS tak bisa ditulis.
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:  # pragma: no cover - tergantung lingkungan FS
        logger.warning("File log tidak dapat dibuat (%s); lanjut via stderr.", exc)

    setattr(logger, _CONFIGURED_FLAG, True)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Ambil logger anak di bawah namespace ``"sentara"``.

    ``get_logger(__name__)`` menghasilkan, mis., ``sentara.src.modeling.inference``.
    Tidak memaksa ``configure_logging()`` — bila belum dikonfigurasi, pesan akan
    diam mengikuti perilaku standar logging (aman untuk unit test).
    """
    if not name:
        return logging.getLogger(_ROOT_LOGGER_NAME)
    safe = name if name.startswith(_ROOT_LOGGER_NAME) else f"{_ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(safe)
