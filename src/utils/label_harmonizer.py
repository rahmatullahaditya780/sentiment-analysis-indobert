"""
Harmonisasi label sentimen lintas sumber dataset (Fase 2).

Tiga sumber dataset memakai skema label berbeda:
- SmSA (IndoNLU)     : integer {0: positive, 1: neutral, 2: negative}
- PRDECT-ID          : string  {positive, negative}  (tanpa neutral)
- Kaggle E-Commerce  : rating bintang 1-5  ATAU  string sentiment_label

Modul ini menyeragamkan semuanya ke label kanonik: positive / negative / neutral.
"""

from __future__ import annotations

# Label kanonik yang dipakai di seluruh pipeline
CANONICAL_LABELS = ("positive", "negative", "neutral")

# SmSA / IndoNLU: label2idx resmi {'positive': 0, 'neutral': 1, 'negative': 2}
SMSA_INT_TO_LABEL = {0: "positive", 1: "neutral", 2: "negative"}

# Sinonim string yang mungkin muncul di berbagai sumber
_STRING_ALIASES = {
    "positive": "positive",
    "positif": "positive",
    "pos": "positive",
    "1": "positive",
    "negative": "negative",
    "negatif": "negative",
    "neg": "negative",
    "-1": "negative",
    "neutral": "neutral",
    "netral": "neutral",
    "neu": "neutral",
    "0": "neutral",
}


def harmonize_string(value: str) -> str:
    """Petakan label string apa pun ke label kanonik. Raise jika tak dikenal."""
    key = str(value).strip().lower()
    if key in _STRING_ALIASES:
        return _STRING_ALIASES[key]
    raise ValueError(f"Label string tidak dikenal: {value!r}")


def harmonize_smsa_int(value: int) -> str:
    """Petakan integer label SmSA (0/1/2) ke label kanonik."""
    try:
        return SMSA_INT_TO_LABEL[int(value)]
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"Label SmSA tidak valid: {value!r}") from exc


def harmonize_rating(rating: int | float) -> str:
    """Petakan rating bintang 1-5 ke label kanonik.

    1-2 -> negative, 3 -> neutral, 4-5 -> positive.
    """
    try:
        r = int(round(float(rating)))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Rating tidak valid: {rating!r}") from exc
    if r <= 2:
        return "negative"
    if r == 3:
        return "neutral"
    if r >= 4:
        return "positive"
    raise ValueError(f"Rating di luar rentang 1-5: {rating!r}")


def is_canonical(value: str) -> bool:
    """True jika value sudah berupa label kanonik."""
    return value in CANONICAL_LABELS
