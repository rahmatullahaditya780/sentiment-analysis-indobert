"""
Uji dataset skenario 5 kondisi pemasaran (data/implementation/scenarios/).

Memastikan tiap berkas skenario berlabel memetakan ke kondisi rule engine yang
diharapkan — murni rule engine Fase 7 (tanpa model IndoBERT), jadi cepat & dapat
ikut suite unit biasa. Dataset dibuat oleh scripts/make_condition_datasets.py.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.recommendation import recommend
from src.recommendation.config import EXCELLENT, GOOD, MIXED, MODERATE, POOR

SCENARIOS_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "implementation" / "scenarios"
)

CASES = [
    ("scenario_excellent.csv", EXCELLENT),
    ("scenario_good.csv", GOOD),
    ("scenario_moderate.csv", MODERATE),
    ("scenario_poor.csv", POOR),
    ("scenario_mixed.csv", MIXED),
]


@pytest.mark.parametrize("filename, expected", CASES)
def test_scenario_memetakan_ke_kondisi_diharapkan(filename, expected):
    path = SCENARIOS_DIR / filename
    assert (
        path.exists()
    ), f"{filename} tidak ada — jalankan: python scripts/make_condition_datasets.py"
    df = pd.read_csv(path)

    assert len(df) <= 500, "Dataset skenario harus ≤ 500 baris."
    assert {"review_text", "predicted_label"} <= set(df.columns)

    rec = recommend(df, use_trend=False)
    assert rec.condition == expected
    # Playbook strategi ikut terisi untuk kondisi tersebut.
    assert rec.playbook
