"""
Fase 6 — terapkan model ke dataset implementasi OmorfoShop (FR-6.5).

Menjalankan inferензi pada:
1. Dataset NATURAL (`omorfo_reviews.csv`) → distribusi sentimen jujur untuk rule
   engine Fase 7. Ringkasan ditulis ke `outputs/reports/omorfo_distribution.json`.
2. Dataset MINORITAS (`omorfo_reviews_minoritas.csv`, bintang 1-4) → bukti model
   menangkap negatif/netral di data nyata. Ringkasan ke
   `outputs/reports/omorfo_distribution_minoritas.json`.

Output prediksi per ulasan: `outputs/reports/omorfo_predictions.csv` (+ _minoritas).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modeling.inference import SentimentPredictor, analyze_omorfo_reviews

REPORTS = PROJECT_ROOT / "outputs" / "reports"
NATURAL_CSV = PROJECT_ROOT / "data" / "implementation" / "omorfo_reviews.csv"
MINORITY_CSV = PROJECT_ROOT / "data" / "implementation" / "omorfo_reviews_minoritas.csv"


def main() -> None:
    predictor = SentimentPredictor().load()  # muat sekali, pakai ulang
    print(f"[fase6] device={predictor.device}")

    # 1) Natural — untuk rule engine.
    print(f"[fase6] inferensi NATURAL: {NATURAL_CSV}")
    _, summary = analyze_omorfo_reviews(
        NATURAL_CSV,
        predictor=predictor,
        output_csv=REPORTS / "omorfo_predictions.csv",
    )
    (REPORTS / "omorfo_distribution.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[fase6] distribusi natural:")
    for label, st in summary["distribution"].items():
        print(f"   {label:9s}: {st['count']:5d} ({st['proportion']*100:.1f}%)")

    # 2) Minoritas — bukti deteksi negatif/netral.
    if MINORITY_CSV.exists():
        print(f"\n[fase6] inferensi MINORITAS: {MINORITY_CSV}")
        _, summary_min = analyze_omorfo_reviews(
            MINORITY_CSV,
            predictor=predictor,
            output_csv=REPORTS / "omorfo_predictions_minoritas.csv",
        )
        (REPORTS / "omorfo_distribution_minoritas.json").write_text(
            json.dumps(summary_min, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[fase6] distribusi minoritas (prediksi model atas ulasan bintang 1-4):")
        for label, st in summary_min["distribution"].items():
            print(f"   {label:9s}: {st['count']:5d} ({st['proportion']*100:.1f}%)")

    print("\n[fase6] SELESAI.")


if __name__ == "__main__":
    main()
