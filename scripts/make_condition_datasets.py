"""
Buat dataset uji 5 kondisi pemasaran (Fase 7) dari data nyata OmorfoShop.

Data implementasi nyata sangat positif (≈88,5% pos) sehingga secara natural hanya
memicu kondisi **Excellent**. Untuk menguji kelima kondisi rule engine, skrip ini
menyusun subset BERLABEL dari kolam prediksi Fase 6 yang sengaja menyentuh ambang
tiap kondisi (lihat tabel SPECS di bawah).

Sumber (hasil inferensi Fase 6, sudah berlabel `predicted_label`):
- outputs/reports/omorfo_predictions.csv            (3.739 ulasan)
- outputs/reports/omorfo_predictions_minoritas.csv  (669 ulasan bintang 1-4)
Gabungan unik (dedup review_id): positif ≈3.335 / negatif ≈407 / netral ≈32.

Kendala: netral hanya ≈32 ulasan di seluruh data nyata → kondisi yang butuh netral
tinggi (Good, Moderate, Mixed-via-netral) berukuran kecil (≤ ~120 baris).

Output: data/implementation/scenarios/scenario_<kondisi>.csv (berlabel, TANPA
`date_review` agar kondisi murni ditentukan distribusi) + manifest.json.

Jalankan:  python scripts/make_condition_datasets.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendation import recommend  # noqa: E402
from src.recommendation.config import (  # noqa: E402
    EXCELLENT,
    GOOD,
    MIXED,
    MODERATE,
    NEGATIVE,
    NEUTRAL,
    POOR,
    POSITIVE,
)

REPORTS = PROJECT_ROOT / "outputs" / "reports"
MAIN_PRED = REPORTS / "omorfo_predictions.csv"
MINORITY_PRED = REPORTS / "omorfo_predictions_minoritas.csv"
OUT_DIR = PROJECT_ROOT / "data" / "implementation" / "scenarios"

SEED = 42

# Kolom keluaran (TANPA date_review — lihat docstring).
OUTPUT_COLUMNS = [
    "review_id",
    "review_text",
    "rating",
    "product_name",
    "product_category",
    "predicted_label",
    "confidence_score",
]

# Spesifikasi tiap skenario: jumlah ulasan per label yang menyentuh ambang kondisi.
# (proporsi → kondisi diharapkan dapat dilihat di README/manifest)
SPECS: list[dict] = [
    {
        "name": "excellent",
        "expected": EXCELLENT,
        "counts": {POSITIVE: 425, NEGATIVE: 65, NEUTRAL: 10},  # 85/13/2  → n=500
    },
    {
        "name": "good",
        "expected": GOOD,
        "counts": {POSITIVE: 55, NEGATIVE: 34, NEUTRAL: 31},  # 45.8/28.3/25.8 → n=120
    },
    {
        "name": "moderate",
        "expected": MODERATE,
        "counts": {POSITIVE: 39, NEGATIVE: 42, NEUTRAL: 29},  # 35.5/38.2/26.4 → n=110
    },
    {
        "name": "poor",
        "expected": POOR,
        "counts": {POSITIVE: 104, NEGATIVE: 333, NEUTRAL: 13},  # 23.1/74.0/2.9 → n=450
    },
    {
        "name": "mixed",
        "expected": MIXED,
        "counts": {POSITIVE: 30, NEGATIVE: 18, NEUTRAL: 32},  # 37.5/22.5/40 → n=80
    },
]


def load_pool() -> pd.DataFrame:
    """Gabung kedua CSV prediksi & dedup review_id → kolam berlabel."""
    frames = [pd.read_csv(MAIN_PRED)]
    if MINORITY_PRED.exists():
        frames.append(pd.read_csv(MINORITY_PRED))
    pool = pd.concat(frames, ignore_index=True).drop_duplicates(
        subset="review_id", keep="first"
    )
    counts = pool["predicted_label"].value_counts().to_dict()
    print(
        f"[pool] {len(pool)} ulasan unik — "
        f"pos {counts.get(POSITIVE, 0)} / neg {counts.get(NEGATIVE, 0)} / "
        f"neu {counts.get(NEUTRAL, 0)}"
    )
    return pool


def label_pool(pool: pd.DataFrame, label: str) -> pd.DataFrame:
    """Subset satu label, urut confidence menurun (tiebreak review_id) → deterministik."""
    return (
        pool[pool["predicted_label"] == label]
        .sort_values(["confidence_score", "review_id"], ascending=[False, True])
        .reset_index(drop=True)
    )


def build_scenario(pool: pd.DataFrame, spec: dict) -> pd.DataFrame:
    """Susun satu DataFrame skenario dari kolam berlabel sesuai jumlah per label."""
    parts = []
    for label, n in spec["counts"].items():
        available = label_pool(pool, label)
        if len(available) < n:
            raise ValueError(
                f"Skenario '{spec['name']}' butuh {n} '{label}', tersedia "
                f"{len(available)}."
            )
        parts.append(available.head(n))

    df = pd.concat(parts, ignore_index=True)
    # Acak urutan agar label tidak berkelompok (stabil via seed).
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    # Hanya kolom keluaran (buang date_review dll bila ada).
    return df[[c for c in OUTPUT_COLUMNS if c in df.columns]]


def summarize(df: pd.DataFrame) -> dict:
    """Hitung jumlah & proporsi per label untuk manifest."""
    vc = df["predicted_label"].value_counts()
    n = int(len(df))
    counts = {lbl: int(vc.get(lbl, 0)) for lbl in (POSITIVE, NEGATIVE, NEUTRAL)}
    proportions = {lbl: round(counts[lbl] / n, 4) if n else 0.0 for lbl in counts}
    return {"n_reviews": n, "counts": counts, "proportions": proportions}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pool = load_pool()

    manifest: list[dict] = []
    all_ok = True
    for spec in SPECS:
        df = build_scenario(pool, spec)
        out_csv = OUT_DIR / f"scenario_{spec['name']}.csv"
        df.to_csv(out_csv, index=False, encoding="utf-8")

        # Verifikasi: kondisi murni dari distribusi (trend dimatikan).
        rec = recommend(df, use_trend=False)
        ok = rec.condition == spec["expected"]
        all_ok = all_ok and ok

        stats = summarize(df)
        manifest.append(
            {
                "file": out_csv.name,
                "expected_condition": spec["expected"],
                "verified_condition": rec.condition,
                "match": ok,
                **stats,
            }
        )
        p = stats["proportions"]
        flag = "OK" if ok else "MISMATCH!"
        print(
            f"[{spec['name']:9s}] n={stats['n_reviews']:>3} "
            f"pos {p[POSITIVE]:.1%} / neg {p[NEGATIVE]:.1%} / neu {p[NEUTRAL]:.1%} "
            f"→ {rec.condition}  [{flag}]"
        )

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "seed": SEED,
                "source": [MAIN_PRED.name, MINORITY_PRED.name],
                "scenarios": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[manifest] {manifest_path}")
    print(
        "[SELESAI] Semua kondisi terverifikasi." if all_ok else "[GAGAL] ada mismatch."
    )
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
