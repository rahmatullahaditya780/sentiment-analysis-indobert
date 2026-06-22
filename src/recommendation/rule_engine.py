"""
Fase 7 — Rule engine: klasifikasi kondisi pemasaran (FR-7.1, FR-7.2).

`MarketingConditionClassifier` mengubah distribusi sentimen (hasil batch
prediction Fase 6) menjadi satu dari 4 kondisi pemasaran melalui aturan
compound yang transparan (positif DAN negatif), dengan "Beragam / Tidak Stabil"
sebagai kondisi override (netral > 35% ATAU trend berubah signifikan).

Input fleksibel:
- DataFrame hasil `predict_batch` (punya kolom `predicted_label`), atau
- dict distribusi {label: proportion} / {label: {"proportion": ...}}, atau
- mapping count {label: int}.

Output: `SentimentDistribution` + `ConditionResult` (kondisi, kriteria yang
terpenuhi, distribusi) — siap dipakai `strategy_mapper` & dashboard Fase 8.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.recommendation.config import (
    EXCELLENT,
    GOOD,
    MIXED,
    NEGATIVE,
    NEUTRAL,
    NEUTRAL_MIXED_THRESHOLD,
    POOR,
    POSITIVE,
    THRESHOLDS,
)

DEFAULT_LABEL_COLUMN = "predicted_label"


@dataclass
class SentimentDistribution:
    """Distribusi sentimen ternormalisasi (proporsi 0..1) + jumlah mentah."""

    positive: float
    negative: float
    neutral: float
    counts: dict[str, int] = field(default_factory=dict)
    n_reviews: int = 0

    def as_dict(self) -> dict:
        return {
            "n_reviews": self.n_reviews,
            "proportion": {
                POSITIVE: round(self.positive, 4),
                NEGATIVE: round(self.negative, 4),
                NEUTRAL: round(self.neutral, 4),
            },
            "counts": dict(self.counts),
        }


@dataclass
class ConditionResult:
    """Hasil klasifikasi kondisi pemasaran untuk satu batch ulasan."""

    condition: str
    distribution: SentimentDistribution
    reason: str = ""
    trend_shift: bool = False

    def as_dict(self) -> dict:
        return {
            "condition": self.condition,
            "reason": self.reason,
            "trend_shift": self.trend_shift,
            "distribution": self.distribution.as_dict(),
        }


def compute_distribution(
    data: pd.DataFrame | dict,
    *,
    label_column: str = DEFAULT_LABEL_COLUMN,
) -> SentimentDistribution:
    """Hitung distribusi sentimen dari berbagai bentuk input (FR-7.1).

    Menerima DataFrame (kolom `label_column`), dict proporsi, dict bersarang
    {label: {"proportion"/"count": ...}}, atau dict count {label: int}.
    """
    counts: dict[str, int] = {POSITIVE: 0, NEGATIVE: 0, NEUTRAL: 0}
    proportions: dict[str, float] | None = None

    if isinstance(data, pd.DataFrame):
        if label_column not in data.columns:
            raise ValueError(
                f"Kolom label '{label_column}' tidak ada. Kolom tersedia: "
                f"{list(data.columns)}"
            )
        vc = data[label_column].value_counts()
        for label in counts:
            counts[label] = int(vc.get(label, 0))
    elif isinstance(data, dict):
        # Deteksi bentuk dict: bersarang vs flat.
        sample = next(iter(data.values()), None)
        if isinstance(sample, dict):  # {label: {"count"/"proportion": ...}}
            for label in counts:
                entry = data.get(label, {})
                counts[label] = int(entry.get("count", 0))
            if all("proportion" in data.get(lbl, {}) for lbl in counts):
                proportions = {lbl: float(data[lbl]["proportion"]) for lbl in counts}
        else:  # flat: bisa count (int) atau proportion (float)
            vals = {lbl: float(data.get(lbl, 0)) for lbl in counts}
            # Heuristik: ada nilai pecahan -> proporsi (dinormalisasi defensif
            # agar 0.999 / 1.05 tetap valid); semua bilangan bulat -> count.
            has_fraction = any(abs(v - round(v)) > 1e-9 for v in vals.values())
            total_vals = sum(vals.values())
            if has_fraction:
                proportions = {
                    lbl: (vals[lbl] / total_vals if total_vals else 0.0) for lbl in vals
                }
            else:
                counts = {lbl: int(round(v)) for lbl, v in vals.items()}
    else:
        raise TypeError(
            "Input harus DataFrame atau dict distribusi; diterima: "
            f"{type(data).__name__}"
        )

    total = sum(counts.values())
    if proportions is None:
        proportions = (
            {lbl: counts[lbl] / total for lbl in counts}
            if total
            else {lbl: 0.0 for lbl in counts}
        )

    return SentimentDistribution(
        positive=proportions[POSITIVE],
        negative=proportions[NEGATIVE],
        neutral=proportions[NEUTRAL],
        counts=counts,
        n_reviews=total,
    )


class MarketingConditionClassifier:
    """Evaluasi 5 kondisi pemasaran compound (FR-7.2).

    Contoh
    ------
    >>> clf = MarketingConditionClassifier()
    >>> res = clf.classify({"positive": 0.885, "negative": 0.106, "neutral": 0.008})
    >>> res.condition
    'Sangat Baik'
    """

    def classify(
        self,
        data: pd.DataFrame | dict | SentimentDistribution,
        *,
        label_column: str = DEFAULT_LABEL_COLUMN,
        trend_shift: bool = False,
    ) -> ConditionResult:
        """Tentukan kondisi pemasaran dari distribusi sentimen.

        `trend_shift` (opsional) diisi oleh `trend_analyzer` untuk memicu
        Mixed/Unstable bila tren berubah signifikan walau netral rendah.
        """
        dist = (
            data
            if isinstance(data, SentimentDistribution)
            else compute_distribution(data, label_column=label_column)
        )

        pos, neg, neu = dist.positive, dist.negative, dist.neutral

        # 1) Override: Mixed/Unstable (netral > 35% ATAU trend berubah).
        if neu > NEUTRAL_MIXED_THRESHOLD or trend_shift:
            reason = (
                f"Netral {neu:.1%} > {NEUTRAL_MIXED_THRESHOLD:.0%}"
                if neu > NEUTRAL_MIXED_THRESHOLD
                else "Tren sentimen berubah signifikan antar periode"
            )
            return ConditionResult(MIXED, dist, reason, trend_shift)

        # 2) Tier performa compound (positif DAN negatif).
        if self._match(EXCELLENT, pos, neg):
            return ConditionResult(
                EXCELLENT, dist, f"Positif {pos:.1%} ≥ 50% DAN negatif {neg:.1%} ≤ 20%"
            )
        if self._match(GOOD, pos, neg):
            return ConditionResult(
                GOOD, dist, f"Positif {pos:.1%} (40–49%) DAN negatif {neg:.1%} (20–30%)"
            )
        if self._match(POOR, pos, neg):
            return ConditionResult(
                POOR, dist, f"Positif {pos:.1%} < 30% DAN negatif {neg:.1%} > 40%"
            )

        # 3) Fallback: kombinasi di luar semua kriteria -> persepsi tidak konsisten
        #    (termasuk band "Moderate" lama: pos 30–39% & neg 30–40%).
        return ConditionResult(
            MIXED,
            dist,
            f"Sentimen beragam (positif {pos:.1%} / negatif {neg:.1%}) — "
            "tidak memenuhi kriteria kondisi mana pun",
            trend_shift,
        )

    @staticmethod
    def _match(condition: str, pos: float, neg: float) -> bool:
        """Cek apakah (pos, neg) memenuhi seluruh batas threshold kondisi."""
        t = THRESHOLDS[condition]
        if "pos_min" in t and pos < t["pos_min"]:
            return False
        if "pos_max" in t and pos > t["pos_max"]:
            return False
        if "neg_min" in t and neg < t["neg_min"]:
            return False
        if "neg_max" in t and neg > t["neg_max"]:
            return False
        return True
