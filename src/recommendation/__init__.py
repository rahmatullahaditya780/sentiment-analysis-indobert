"""Paket recommendation Fase 7 — rule-based marketing recommendation.

Pipeline ringan (pandas saja, tanpa torch) yang mengubah hasil batch prediction
Fase 6 menjadi rekomendasi pemasaran:

    distribusi sentimen  (rule_engine.compute_distribution)
      -> kondisi pemasaran  (MarketingConditionClassifier — 5 kondisi compound)
      -> strategi + insight  (strategy_mapper.map_to_recommendation)
      [+ trend_analyzer bila ada kolom `date_review`]

Pemakaian umum cukup lewat `recommend(df_predictions)`.
"""

from __future__ import annotations

import pandas as pd

from src.recommendation.config import (
    CONDITIONS,
    RECOMMENDATION_REPORT_JSON,
    STRATEGY_MAP,
)
from src.recommendation.rule_engine import (
    ConditionResult,
    MarketingConditionClassifier,
    SentimentDistribution,
    compute_distribution,
)
from src.recommendation.strategy_mapper import (
    MarketingRecommendation,
    map_to_recommendation,
    save_recommendation,
)
from src.recommendation.trend_analyzer import TrendResult, analyze_trend


def recommend(
    predictions: pd.DataFrame | dict,
    *,
    label_column: str = "predicted_label",
    date_column: str = "date_review",
    use_trend: bool = True,
    save: bool = False,
) -> MarketingRecommendation:
    """Orkestrasi end-to-end Fase 7 (FR-7.1 s/d FR-7.5).

    Menerima DataFrame hasil `predict_batch` (atau dict distribusi), menjalankan
    klasifikasi kondisi + (opsional) trend analysis, lalu mengembalikan
    `MarketingRecommendation`. Set `save=True` untuk menulis JSON report.
    """
    trend = TrendResult(available=False)
    if use_trend and isinstance(predictions, pd.DataFrame):
        trend = analyze_trend(
            predictions, date_column=date_column, label_column=label_column
        )

    result = MarketingConditionClassifier().classify(
        predictions, label_column=label_column, trend_shift=trend.trend_shift
    )
    recommendation = map_to_recommendation(result, meta={"trend": trend.as_dict()})

    if save:
        save_recommendation(recommendation)
    return recommendation


__all__ = [
    "CONDITIONS",
    "STRATEGY_MAP",
    "RECOMMENDATION_REPORT_JSON",
    "ConditionResult",
    "MarketingConditionClassifier",
    "SentimentDistribution",
    "compute_distribution",
    "MarketingRecommendation",
    "map_to_recommendation",
    "save_recommendation",
    "TrendResult",
    "analyze_trend",
    "recommend",
]
