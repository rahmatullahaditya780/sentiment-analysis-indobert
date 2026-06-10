"""
Fase 7 — Trend analysis sentimen berbasis waktu (FR-7.5).

Opsional: aktif hanya jika data implementasi punya kolom timestamp
(`date_review`). Menghitung proporsi positif/negatif per periode (mingguan/
bulanan) dan mendeteksi apakah tren berubah signifikan — sinyal yang memicu
kondisi Mixed/Unstable di `rule_engine`.

KERANGKA: implementasi inti tersedia, namun ambang & granularitas periode
(`TREND_SHIFT_THRESHOLD`, freq) masih perlu dikalibrasi pada data OmorfoShop
ber-`date_review`. Saat ini sebagian ulasan endpoint JSON internal belum punya
timestamp ter-parse → fungsi mengembalikan `available=False` secara aman.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.recommendation.config import (
    MIN_PERIOD_SIZE,
    NEGATIVE,
    POSITIVE,
    TREND_SHIFT_THRESHOLD,
)
from src.recommendation.rule_engine import DEFAULT_LABEL_COLUMN

DEFAULT_DATE_COLUMN = "date_review"


@dataclass
class TrendResult:
    """Hasil analisis tren sentimen antar periode."""

    available: bool
    trend_shift: bool = False
    max_delta_positive: float = 0.0
    periods: list[dict] = field(default_factory=list)
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "available": self.available,
            "trend_shift": self.trend_shift,
            "max_delta_positive": round(self.max_delta_positive, 4),
            "periods": self.periods,
            "note": self.note,
        }


def analyze_trend(
    data: pd.DataFrame,
    *,
    date_column: str = DEFAULT_DATE_COLUMN,
    label_column: str = DEFAULT_LABEL_COLUMN,
    freq: str = "ME",
    shift_threshold: float = TREND_SHIFT_THRESHOLD,
    min_period_size: int = MIN_PERIOD_SIZE,
) -> TrendResult:
    """Analisis tren proporsi sentimen per periode (FR-7.5).

    Mengembalikan `TrendResult(available=False)` secara aman jika kolom tanggal
    tidak ada atau tidak ada timestamp valid (data tetap dapat diklasifikasi
    tanpa tren). `trend_shift=True` jika |Δ proporsi positif| antar periode
    berurutan melebihi `shift_threshold`.

    PENTING: hanya periode dengan ulasan >= `min_period_size` yang ikut hitung
    deteksi shift. Tanpa guard ini, bulan bersampel kecil (mis. n=1–2 di awal
    riwayat toko) menghasilkan swing proporsi ekstrem yang palsu memicu
    Mixed/Unstable. Periode <`min_period_size` tetap ditampilkan (`eligible=False`)
    untuk transparansi, tetapi diabaikan saat menghitung Δ.
    """
    if date_column not in data.columns or label_column not in data.columns:
        return TrendResult(
            available=False,
            note=f"Kolom '{date_column}'/'{label_column}' tidak lengkap.",
        )

    df = data[[date_column, label_column]].copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
    df = df.dropna(subset=[date_column])
    if df.empty:
        return TrendResult(available=False, note="Tidak ada timestamp valid pada data.")

    # Proporsi positif & negatif per periode.
    grouped = df.groupby(pd.Grouper(key=date_column, freq=freq))[label_column]
    periods: list[dict] = []
    for period, labels in grouped:
        n = int(labels.size)
        if n == 0:
            continue
        vc = labels.value_counts()
        periods.append(
            {
                "period": str(period.date()),
                "n_reviews": n,
                "positive": round(int(vc.get(POSITIVE, 0)) / n, 4),
                "negative": round(int(vc.get(NEGATIVE, 0)) / n, 4),
                "eligible": n >= min_period_size,
            }
        )

    # Hanya periode yang cukup besar yang dipakai menghitung shift.
    eligible = [p for p in periods if p["eligible"]]
    if len(eligible) < 2:
        return TrendResult(
            available=True,
            periods=periods,
            note=(
                f"Periode dengan >= {min_period_size} ulasan < 2; "
                "tren belum dapat dinilai (sampel per bulan terlalu kecil)."
            ),
        )

    deltas = [
        abs(eligible[i]["positive"] - eligible[i - 1]["positive"])
        for i in range(1, len(eligible))
    ]
    max_delta = max(deltas)
    return TrendResult(
        available=True,
        trend_shift=max_delta > shift_threshold,
        max_delta_positive=max_delta,
        periods=periods,
        note=(
            f"Δ positif maks {max_delta:.1%} vs ambang {shift_threshold:.0%} "
            f"(atas {len(eligible)} periode >= {min_period_size} ulasan)."
        ),
    )
