"""
Fase 7 — Konfigurasi rule-based marketing recommendation.

Modul ringan (tanpa dependency berat) berisi:
- Re-export label kanonik (positive/negative/neutral) dari Fase 4 agar tidak ada
  drift dengan output inferensi Fase 6.
- Nama 5 kondisi pemasaran (compound conditions) & ambang batasnya.
- Pemetaan kondisi -> daftar strategi pemasaran (lihat planning/fase-07-*.md).
- Lokasi output standar Fase 7 (marketing_recommendation.json).

Nilai mengikuti tabel "Threshold & Kondisi Pemasaran" pada
`planning/fase-07-marketing-recommendation.md` dan CLAUDE.md.
"""

from __future__ import annotations

from pathlib import Path

# Label kanonik & folder report dipinjam dari Fase 4 supaya konsisten dengan
# kolom `predicted_label` yang dihasilkan engine inferensi Fase 6.
from src.modeling.config import (  # noqa: F401  (re-export)
    ID2LABEL,
    REPORTS_DIR,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Output standar Fase 7 (deliverable Checkpoint 7) ──────────────────────────
RECOMMENDATION_REPORT_JSON = REPORTS_DIR / "marketing_recommendation.json"

# ── Label kanonik (alfabetis: negative=0, neutral=1, positive=2) ──────────────
POSITIVE = "positive"
NEGATIVE = "negative"
NEUTRAL = "neutral"

# ── Nama 5 kondisi pemasaran ──────────────────────────────────────────────────
EXCELLENT = "Excellent Performance"
GOOD = "Good Performance"
MODERATE = "Moderate Performance"
POOR = "Poor Performance"
MIXED = "Mixed/Unstable"

CONDITIONS: tuple[str, ...] = (EXCELLENT, GOOD, MODERATE, POOR, MIXED)

# ── Ambang batas compound (proporsi 0..1) ─────────────────────────────────────
# Tiap kondisi performa memakai kriteria gabungan positif AND negatif.
# Mixed/Unstable adalah kondisi override: netral > 35% ATAU trend berubah.
# Catatan: nilai berikut sesuai tabel rencana; ada celah di antara tier
# (mis. pos 45% & neg 15%) yang sengaja jatuh ke fallback Mixed/Unstable.
THRESHOLDS: dict[str, dict[str, float]] = {
    EXCELLENT: {"pos_min": 0.50, "neg_max": 0.20},
    GOOD: {"pos_min": 0.40, "pos_max": 0.499, "neg_min": 0.20, "neg_max": 0.30},
    MODERATE: {"pos_min": 0.30, "pos_max": 0.399, "neg_min": 0.30, "neg_max": 0.40},
    POOR: {"pos_max": 0.299, "neg_min": 0.401},
}

# Mixed/Unstable
NEUTRAL_MIXED_THRESHOLD = 0.35  # netral > 35% -> persepsi tidak konsisten
# Ambang perubahan tren signifikan (selisih proporsi positif antar periode).
# TODO Fase 7: kalibrasi pada data OmorfoShop ber-`date_review`.
TREND_SHIFT_THRESHOLD = 0.15

# ── Interpretasi singkat per kondisi (business insight inti) ──────────────────
CONDITION_INTERPRETATION: dict[str, str] = {
    EXCELLENT: (
        "Produk/layanan dikomunikasikan dengan sangat baik; kepuasan pelanggan tinggi."
    ),
    GOOD: "Produk dapat diterima, namun ada ruang untuk perbaikan.",
    MODERATE: "Keseimbangan antara kepuasan dan ketidakpuasan pelanggan.",
    POOR: "Produk/layanan menghadapi masalah signifikan; perlu perhatian urgent.",
    MIXED: "Persepsi pelanggan tidak konsisten; perlu monitoring lebih lanjut.",
}

# ── Rule-based mapping kondisi -> daftar strategi pemasaran ────────────────────
STRATEGY_MAP: dict[str, list[str]] = {
    EXCELLENT: [
        "Pertahankan kualitas & branding.",
        "Tingkatkan loyalitas pelanggan.",
        "Manfaatkan ulasan positif sebagai social proof.",
        "Pertimbangkan program referral.",
    ],
    GOOD: [
        "Identifikasi aspek yang masih kurang dari ulasan negatif.",
        "Perbaiki titik kelemahan spesifik.",
        "Tingkatkan komunikasi keunggulan produk.",
    ],
    MODERATE: [
        "Analisis aspek (word cloud negatif) untuk identifikasi masalah utama.",
        "Tingkatkan kualitas produk dan layanan.",
        "Susun kampanye komunikasi yang lebih transparan.",
    ],
    POOR: [
        "Prioritaskan peningkatan kualitas produk dan layanan secara urgent.",
        "Evaluasi pricing dan packaging.",
        "Pertimbangkan kampanye permintaan maaf publik.",
    ],
    MIXED: [
        "Tingkatkan edukasi produk.",
        "Perkuat deskripsi produk agar ekspektasi lebih terarah.",
        "Lakukan monitoring sentimen secara berkala.",
    ],
}


def ensure_output_dirs() -> None:
    """Pastikan folder output Fase 7 ada (idempoten)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
