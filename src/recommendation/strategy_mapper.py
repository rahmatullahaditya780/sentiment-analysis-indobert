"""
Fase 7 — Strategy mapper & business insight (FR-7.3, FR-7.4).

Mengubah `ConditionResult` (dari `rule_engine`) menjadi rekomendasi pemasaran
lengkap: daftar strategi spesifik + business insight yang dapat
dipertanggungjawabkan (interpretasi distribusi sentimen secara naratif).

Output `MarketingRecommendation.as_dict()` adalah kontrak yang dikonsumsi
Recommendation Panel dashboard (Fase 8) dan disimpan sebagai
`outputs/reports/marketing_recommendation.json`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.recommendation.config import (
    CONDITION_INTERPRETATION,
    RECOMMENDATION_REPORT_JSON,
    STRATEGY_MAP,
    STRATEGY_PLAYBOOK,
    ensure_output_dirs,
)
from src.recommendation.rule_engine import ConditionResult


@dataclass
class MarketingRecommendation:
    """Paket rekomendasi final untuk satu batch ulasan."""

    condition: str
    interpretation: str
    business_insight: str
    strategies: list[str]
    distribution: dict
    reason: str = ""
    trend_shift: bool = False
    playbook: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "condition": self.condition,
            "interpretation": self.interpretation,
            "business_insight": self.business_insight,
            "strategies": list(self.strategies),
            "reason": self.reason,
            "trend_shift": self.trend_shift,
            "playbook": [dict(play) for play in self.playbook],
            "distribution": self.distribution,
            "meta": dict(self.meta),
        }


def _build_business_insight(result: ConditionResult) -> str:
    """Susun narasi business insight dari distribusi + kondisi (FR-7.4)."""
    dist = result.distribution
    pos, neg, neu = dist.positive, dist.negative, dist.neutral
    interp = CONDITION_INTERPRETATION.get(result.condition, "")
    return (
        f"Dari {dist.n_reviews} ulasan: {pos:.1%} positif, {neg:.1%} negatif, "
        f"{neu:.1%} netral. Kondisi terklasifikasi sebagai "
        f"'{result.condition}' ({result.reason}). {interp}"
    )


def map_to_recommendation(
    result: ConditionResult,
    *,
    meta: dict | None = None,
) -> MarketingRecommendation:
    """Petakan `ConditionResult` -> `MarketingRecommendation` (FR-7.3/7.4)."""
    return MarketingRecommendation(
        condition=result.condition,
        interpretation=CONDITION_INTERPRETATION.get(result.condition, ""),
        business_insight=_build_business_insight(result),
        strategies=list(STRATEGY_MAP.get(result.condition, [])),
        playbook=[
            play.as_dict() for play in STRATEGY_PLAYBOOK.get(result.condition, ())
        ],
        distribution=result.distribution.as_dict(),
        reason=result.reason,
        trend_shift=result.trend_shift,
        meta=meta or {},
    )


def save_recommendation(
    recommendation: MarketingRecommendation,
    *,
    output_json: str | Path = RECOMMENDATION_REPORT_JSON,
) -> Path:
    """Tulis rekomendasi ke JSON (deliverable Checkpoint 7)."""
    ensure_output_dirs()
    output_json = Path(output_json)
    output_json.write_text(
        json.dumps(recommendation.as_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_json
