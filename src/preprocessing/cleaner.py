"""
Fase 3 — Text Cleaner berbasis regex.

Tahap cleaning untuk ulasan e-commerce berbahasa Indonesia SEBELUM masuk
IndoBERT tokenizer:

    case folding  ->  hapus URL  ->  hapus emoji/piktograf  ->  hapus tag HTML
                  ->  hapus simbol non-teks  ->  rapikan tanda baca & spasi

PENTING (FR-3.3): pipeline ini TIDAK melakukan stemming maupun stopword
removal. IndoBERT memakai subword embeddings (WordPiece) yang mempertahankan
konteks; menghapus imbuhan/stopword justru merusak representasi semantik.
Karena itu modul ini sengaja TIDAK mengimpor Sastrawi maupun NLTK.
"""

from __future__ import annotations

import re

# ── Pola regex (dikompilasi sekali) ──────────────────────────────────────────
# URL: http(s):// ... dan pola www. ...
_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)

# Tag HTML mentah (mis. <br>, <p>) yang kadang ikut dari hasil scraping
_HTML_TAG_RE = re.compile(r"<[^>]+>")

# Emoji & piktograf (emoticon, simbol & piktograf, transport, dingbats, dll.)
_EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001faff"  # simbol & piktograf, emoji tambahan
    "\U00002600-\U000027bf"  # misc symbols + dingbats
    "\U0001f1e6-\U0001f1ff"  # regional indicator (bendera)
    "\U0000fe00-\U0000fe0f"  # variation selectors
    "\U00002190-\U000021ff"  # arrows
    "\U00002b00-\U00002bff"  # misc symbols & arrows
    "\U0000200d"             # zero width joiner
    "]+",
    flags=re.UNICODE,
)

# Karakter yang DIPERTAHANKAN: huruf (termasuk beraksen), digit, spasi,
# dan tanda baca dasar yang relevan untuk konteks ulasan.
_KEPT_PUNCT = ".,!?'\"-"
_NON_TEXT_RE = re.compile(rf"[^0-9a-zA-ZÀ-ɏ\s{re.escape(_KEPT_PUNCT)}]+")

# Tanda baca berlebih: 3+ titik -> '...', selain itu karakter berulang -> tunggal
_ELLIPSIS_RE = re.compile(r"\.{3,}")
_REPEAT_PUNCT_RE = re.compile(r"([!?,;:'\"-])\1+")

# Spasi/whitespace berlebih
_WHITESPACE_RE = re.compile(r"\s+")


def case_fold(text: str) -> str:
    """FR-3.1 — ubah seluruh teks menjadi huruf kecil."""
    return str(text).lower()


def clean_text(text: str) -> str:
    """FR-3.2 — hapus URL, emoji, tag HTML, simbol, dan tanda baca berlebih.

    TIDAK melakukan stemming/stopword removal (FR-3.3). Mengembalikan string
    yang sudah dirapikan; bisa berupa string kosong jika seluruh isi terhapus.
    """
    if text is None:
        return ""
    s = str(text)
    s = _URL_RE.sub(" ", s)
    s = _HTML_TAG_RE.sub(" ", s)
    s = _EMOJI_RE.sub(" ", s)
    s = _NON_TEXT_RE.sub(" ", s)
    s = _ELLIPSIS_RE.sub("...", s)
    s = _REPEAT_PUNCT_RE.sub(r"\1", s)
    s = _WHITESPACE_RE.sub(" ", s).strip()
    return s


def preprocess_text(text: str) -> str:
    """Gabungan tahap teks: case folding lalu cleaning."""
    return clean_text(case_fold(text))
