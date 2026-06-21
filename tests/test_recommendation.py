"""
Fase 7 — Unit test rule-based marketing recommendation.

Cakupan:
- compute_distribution: DataFrame, dict bersarang, dict proporsi flat,
  dict count flat, kolom hilang, & data kosong.
- MarketingConditionClassifier: kelima kondisi compound + override Mixed
  (netral & trend) + fallback celah antar-tier.
- strategy_mapper: pemetaan strategi + business insight + tulis JSON.
- trend_analyzer: kolom tanggal hilang, guard sampel kecil, deteksi shift.
- recommend(): orkestrasi end-to-end.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from src.recommendation import recommend
from src.recommendation.config import (
    CONDITIONS,
    EXCELLENT,
    GOOD,
    MIXED,
    MODERATE,
    POOR,
    STRATEGY_MAP,
    STRATEGY_PLAYBOOK,
)
from src.recommendation.rule_engine import (
    MarketingConditionClassifier,
    SentimentDistribution,
    compute_distribution,
)
from src.recommendation.strategy_mapper import (
    map_to_recommendation,
    save_recommendation,
)
from src.recommendation.trend_analyzer import analyze_trend


def _labels_df(pos: int, neg: int, neu: int, dates: list[str] | None = None):
    """Bangun DataFrame `predicted_label` (+ opsional `date_review`)."""
    labels = ["positive"] * pos + ["negative"] * neg + ["neutral"] * neu
    df = pd.DataFrame({"predicted_label": labels})
    if dates is not None:
        df["date_review"] = dates
    return df


# ── compute_distribution ──────────────────────────────────────────────────────
class TestComputeDistribution:
    def test_from_dataframe(self):
        dist = compute_distribution(_labels_df(80, 15, 5))
        assert dist.n_reviews == 100
        assert dist.counts == {"positive": 80, "negative": 15, "neutral": 5}
        assert dist.positive == pytest.approx(0.80)
        assert dist.negative == pytest.approx(0.15)

    def test_from_nested_dict_with_proportion(self):
        data = {
            "positive": {"count": 3310, "proportion": 0.8853},
            "negative": {"count": 398, "proportion": 0.1064},
            "neutral": {"count": 31, "proportion": 0.0083},
        }
        dist = compute_distribution(data)
        assert dist.n_reviews == 3739
        assert dist.positive == pytest.approx(0.8853)

    def test_from_flat_proportion_dict_normalizes(self):
        # Jumlah 0.999 (pembulatan) tetap dianggap proporsi, lalu dinormalisasi.
        dist = compute_distribution(
            {"positive": 0.885, "negative": 0.106, "neutral": 0.008}
        )
        total = dist.positive + dist.negative + dist.neutral
        assert total == pytest.approx(1.0)
        assert dist.positive > dist.negative > dist.neutral

    def test_from_flat_count_dict(self):
        dist = compute_distribution({"positive": 80, "negative": 15, "neutral": 5})
        assert dist.n_reviews == 100
        assert dist.positive == pytest.approx(0.80)

    def test_missing_column_raises(self):
        with pytest.raises(ValueError):
            compute_distribution(pd.DataFrame({"teks": ["a"]}))

    def test_empty_dataframe(self):
        dist = compute_distribution(pd.DataFrame({"predicted_label": []}))
        assert dist.n_reviews == 0
        assert dist.positive == 0.0


# ── MarketingConditionClassifier ──────────────────────────────────────────────
class TestClassifier:
    @pytest.fixture
    def clf(self):
        return MarketingConditionClassifier()

    def test_excellent(self, clf):
        res = clf.classify({"positive": 0.60, "negative": 0.15, "neutral": 0.25})
        assert res.condition == EXCELLENT

    def test_good(self, clf):
        res = clf.classify({"positive": 0.45, "negative": 0.25, "neutral": 0.30})
        assert res.condition == GOOD

    def test_moderate(self, clf):
        res = clf.classify({"positive": 0.35, "negative": 0.35, "neutral": 0.30})
        assert res.condition == MODERATE

    def test_poor(self, clf):
        res = clf.classify({"positive": 0.25, "negative": 0.50, "neutral": 0.25})
        assert res.condition == POOR

    def test_mixed_via_high_neutral(self, clf):
        res = clf.classify({"positive": 0.40, "negative": 0.20, "neutral": 0.40})
        assert res.condition == MIXED
        assert "Netral" in res.reason

    def test_mixed_via_trend_shift_overrides_excellent(self, clf):
        # Distribusi seharusnya Excellent, tetapi trend_shift memaksa Mixed.
        res = clf.classify(
            {"positive": 0.60, "negative": 0.15, "neutral": 0.25},
            trend_shift=True,
        )
        assert res.condition == MIXED
        assert res.trend_shift is True
        assert "Tren" in res.reason

    def test_fallback_gap_between_tiers(self, clf):
        # pos 0.55 / neg 0.30 / neu 0.15: tak memenuhi tier manapun -> Mixed.
        res = clf.classify({"positive": 0.55, "negative": 0.30, "neutral": 0.15})
        assert res.condition == MIXED
        assert "tier" in res.reason.lower()

    def test_accepts_distribution_object(self, clf):
        dist = SentimentDistribution(positive=0.6, negative=0.15, neutral=0.25)
        assert clf.classify(dist).condition == EXCELLENT

    def test_real_omorfo_distribution(self, clf):
        # Distribusi nyata Fase 6 (3.739 ulasan) -> Excellent Performance.
        res = clf.classify(_labels_df(3310, 398, 31))
        assert res.condition == EXCELLENT


# ── strategy_mapper ───────────────────────────────────────────────────────────
class TestStrategyMapper:
    def test_map_returns_strategies_and_insight(self):
        clf = MarketingConditionClassifier()
        result = clf.classify({"positive": 0.60, "negative": 0.15, "neutral": 0.25})
        rec = map_to_recommendation(result)
        assert rec.condition == EXCELLENT
        assert rec.strategies == STRATEGY_MAP[EXCELLENT]
        assert "positif" in rec.business_insight
        assert rec.interpretation

    def test_save_writes_valid_json(self, tmp_path):
        clf = MarketingConditionClassifier()
        result = clf.classify({"positive": 0.25, "negative": 0.50, "neutral": 0.25})
        rec = map_to_recommendation(result)
        out = tmp_path / "rec.json"
        save_recommendation(rec, output_json=out)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["condition"] == POOR
        assert loaded["strategies"] == STRATEGY_MAP[POOR]
        assert loaded["distribution"]["proportion"]["negative"] == pytest.approx(0.50)
        # Playbook ikut terserialisasi (kontrak baru).
        assert "playbook" in loaded
        assert len(loaded["playbook"]) == len(STRATEGY_PLAYBOOK[POOR])
        assert loaded["playbook"][0]["judul"] == STRATEGY_PLAYBOOK[POOR][0].judul


# ── STRATEGY_PLAYBOOK (strategi terstruktur + terhubung fitur) ────────────────
class TestStrategyPlaybook:
    def test_kunci_playbook_sama_dengan_conditions(self):
        assert set(STRATEGY_PLAYBOOK) == set(CONDITIONS)

    def test_setiap_kondisi_punya_minimal_satu_play(self):
        for condition in CONDITIONS:
            assert len(STRATEGY_PLAYBOOK[condition]) >= 1

    def test_setiap_play_punya_semua_field_terisi(self):
        for condition, plays in STRATEGY_PLAYBOOK.items():
            for play in plays:
                assert play.judul.strip(), f"judul kosong di {condition}"
                assert play.contoh.strip(), f"contoh kosong di {condition}"
                assert play.fitur.strip(), f"fitur kosong di {condition}"
                assert isinstance(play.langkah, tuple)
                assert play.langkah, f"langkah kosong di {condition}"
                assert all(step.strip() for step in play.langkah)

    def test_strategy_map_diturunkan_dari_judul_playbook(self):
        for condition in CONDITIONS:
            assert STRATEGY_MAP[condition] == [
                play.judul for play in STRATEGY_PLAYBOOK[condition]
            ]

    def test_play_as_dict_lengkap(self):
        play = STRATEGY_PLAYBOOK[EXCELLENT][0]
        d = play.as_dict()
        assert set(d) == {"judul", "langkah", "contoh", "fitur"}
        assert isinstance(d["langkah"], list)  # tuple -> list saat serialisasi

    def test_map_to_recommendation_mengisi_playbook(self):
        clf = MarketingConditionClassifier()
        result = clf.classify({"positive": 0.60, "negative": 0.15, "neutral": 0.25})
        rec = map_to_recommendation(result)
        assert len(rec.playbook) == len(STRATEGY_PLAYBOOK[EXCELLENT])
        first = rec.playbook[0]
        assert first["judul"] == STRATEGY_PLAYBOOK[EXCELLENT][0].judul
        assert first["langkah"] and first["contoh"] and first["fitur"]
        # `strategies` (judul) tetap sinkron dengan judul playbook.
        assert rec.strategies == [p["judul"] for p in rec.playbook]


# ── trend_analyzer ────────────────────────────────────────────────────────────
class TestTrendAnalyzer:
    def test_missing_date_column(self):
        res = analyze_trend(_labels_df(10, 0, 0))
        assert res.available is False
        assert res.trend_shift is False

    def test_small_samples_are_guarded(self):
        # Dua bulan, masing-masing < min_period_size, proporsi berlawanan ekstrem.
        df = _labels_df(1, 1, 0, dates=["2020-01-15", "2020-02-15"])
        res = analyze_trend(df, min_period_size=30)
        assert res.available is True
        assert res.trend_shift is False  # tidak boleh memicu shift palsu

    def test_detects_real_shift(self):
        # Bulan 1: 30 positif (pos=1.0); bulan 2: 15 pos + 15 neg (pos=0.5).
        labels = ["positive"] * 30 + ["positive"] * 15 + ["negative"] * 15
        dates = ["2020-01-10"] * 30 + ["2020-02-10"] * 30
        df = pd.DataFrame({"predicted_label": labels, "date_review": dates})
        res = analyze_trend(df, min_period_size=30, shift_threshold=0.15)
        assert res.available is True
        assert res.trend_shift is True
        assert res.max_delta_positive == pytest.approx(0.5)

    def test_no_shift_when_stable(self):
        # Dua bulan stabil (pos ~0.9 keduanya), delta < ambang.
        labels = (["positive"] * 27 + ["negative"] * 3) + (
            ["positive"] * 28 + ["negative"] * 2
        )
        dates = ["2020-01-10"] * 30 + ["2020-02-10"] * 30
        df = pd.DataFrame({"predicted_label": labels, "date_review": dates})
        res = analyze_trend(df, min_period_size=30, shift_threshold=0.15)
        assert res.trend_shift is False


# ── recommend() end-to-end ────────────────────────────────────────────────────
class TestRecommendOrchestration:
    def test_end_to_end_excellent_no_trend(self):
        df = _labels_df(88, 11, 1)
        rec = recommend(df)
        assert rec.condition == EXCELLENT
        assert rec.trend_shift is False
        assert rec.meta["trend"]["available"] is False  # tanpa date_review

    def test_end_to_end_with_dates_real_shift(self):
        labels = ["positive"] * 30 + ["positive"] * 15 + ["negative"] * 15
        dates = ["2020-01-10"] * 30 + ["2020-02-10"] * 30
        df = pd.DataFrame({"predicted_label": labels, "date_review": dates})
        rec = recommend(df)
        # Trend shift terdeteksi -> override ke Mixed/Unstable.
        assert rec.trend_shift is True
        assert rec.condition == MIXED

    def test_accepts_dict_input(self):
        rec = recommend({"positive": 0.25, "negative": 0.50, "neutral": 0.25})
        assert rec.condition == POOR


# ── condition_criteria (teks kriteria digenerate dari THRESHOLDS) ─────────────
class TestConditionCriteria:
    def test_semua_kondisi_ada(self):
        from src.recommendation.config import CONDITIONS, condition_criteria

        criteria = condition_criteria()
        assert set(criteria) == set(CONDITIONS)
        assert all(isinstance(v, str) and v for v in criteria.values())

    def test_angka_turunan_thresholds(self):
        from src.recommendation.config import THRESHOLDS, condition_criteria

        criteria = condition_criteria()
        exc = THRESHOLDS[EXCELLENT]
        assert f"{int(exc['pos_min'] * 100)}%" in criteria[EXCELLENT]  # 50%
        assert f"{int(exc['neg_max'] * 100)}%" in criteria[EXCELLENT]  # 20%
        # Wording selaras tabel fase-07 (pin agar tidak berubah diam-diam).
        assert criteria[EXCELLENT] == "Positif >= 50% DAN Negatif <= 20%".replace(
            ">=", "≥"
        ).replace("<=", "≤")
        assert criteria[GOOD] == "Positif 40–49% DAN Negatif 20–30%"
        assert criteria[POOR] == "Positif < 30% DAN Negatif > 40%"

    def test_mixed_memuat_ambang_netral(self):
        from src.recommendation.config import (
            NEUTRAL_MIXED_THRESHOLD,
            condition_criteria,
        )

        teks = condition_criteria()[MIXED]
        assert f"{int(NEUTRAL_MIXED_THRESHOLD * 100)}%" in teks  # 35%
        assert "tren" in teks
