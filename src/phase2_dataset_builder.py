"""
Fase 2 — Dataset Builder: stratified split 80/10/10 + laporan imbalance.

Input : data/processed/unified_corpus.csv   (dari src/data_management.py)
Output: data/processed/{train,validation,test}.csv
        outputs/reports/phase2_split_stats.json

Split memakai stratifikasi per label (pure pandas, seed tetap) sehingga
proporsi kelas konsisten di train/val/test. Penanganan class imbalance
TIDAK dilakukan di sini (split dulu agar tak ada data leakage) — strategi
class_weight diterapkan saat training Fase 4.

Jalankan:
    .venv\\Scripts\\python.exe -m src.phase2_dataset_builder
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
UNIFIED_PATH = PROCESSED_DIR / "unified_corpus.csv"

SEED = 42
TRAIN_FRAC, VAL_FRAC = 0.80, 0.10  # test = sisanya (0.10)
IMBALANCE_THRESHOLD = 0.15  # selisih proporsi kelas > 15% -> wajib ditangani


def stratified_split(
    df: pd.DataFrame,
    train_frac: float = TRAIN_FRAC,
    val_frac: float = VAL_FRAC,
    seed: int = SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified split per label menjadi (train, val, test)."""
    train_parts, val_parts, test_parts = [], [], []
    for _, group in df.groupby("label"):
        g = group.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        n = len(g)
        n_train = int(n * train_frac)
        n_val = int(n * val_frac)
        train_parts.append(g.iloc[:n_train])
        val_parts.append(g.iloc[n_train : n_train + n_val])
        test_parts.append(g.iloc[n_train + n_val :])

    def _finalize(parts: list[pd.DataFrame]) -> pd.DataFrame:
        return (
            pd.concat(parts, ignore_index=True)
            .sample(frac=1.0, random_state=seed)
            .reset_index(drop=True)
        )

    return _finalize(train_parts), _finalize(val_parts), _finalize(test_parts)


def _distribution(df: pd.DataFrame) -> dict[str, dict]:
    counts = df["label"].value_counts().to_dict()
    total = len(df)
    pct = {k: round(v / total * 100, 2) for k, v in counts.items()}
    return {"total": total, "counts": counts, "pct": pct}


def _imbalance_report(df: pd.DataFrame) -> dict:
    pct = {k: v / len(df) for k, v in df["label"].value_counts().to_dict().items()}
    spread = max(pct.values()) - min(pct.values())
    needs_handling = spread > IMBALANCE_THRESHOLD
    severe = spread > 0.25
    return {
        "spread": round(spread, 4),
        "threshold": IMBALANCE_THRESHOLD,
        "needs_handling": needs_handling,
        "severe_needs_augmentation": severe,
        "recommended_strategy": (
            "class_weight pada fine-tuning IndoBERT + F1 macro sebagai metrik utama"
            + ("; pertimbangkan augmentasi (back-translation) untuk kelas minoritas" if severe else "")
            if needs_handling
            else "tidak perlu penanganan khusus"
        ),
    }


def build_splits(save: bool = True) -> dict:
    if not UNIFIED_PATH.exists():
        raise FileNotFoundError(
            f"{UNIFIED_PATH} belum ada. Jalankan dulu: python -m src.data_management"
        )

    df = pd.read_csv(UNIFIED_PATH)
    print(f"Unified corpus: {len(df)} baris")

    train, val, test = stratified_split(df)
    print(f"Split  -> train {len(train)} | val {len(val)} | test {len(test)}")

    report = {
        "seed": SEED,
        "fractions": {"train": TRAIN_FRAC, "validation": VAL_FRAC, "test": round(1 - TRAIN_FRAC - VAL_FRAC, 2)},
        "unified": _distribution(df),
        "train": _distribution(train),
        "validation": _distribution(val),
        "test": _distribution(test),
        "imbalance": _imbalance_report(df),
        "sources": df["source"].value_counts().to_dict(),
    }

    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        train.to_csv(PROCESSED_DIR / "train.csv", index=False, encoding="utf-8")
        val.to_csv(PROCESSED_DIR / "validation.csv", index=False, encoding="utf-8")
        test.to_csv(PROCESSED_DIR / "test.csv", index=False, encoding="utf-8")
        with open(REPORTS_DIR / "phase2_split_stats.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Disimpan -> data/processed/{{train,validation,test}}.csv")
        print("Laporan  -> outputs/reports/phase2_split_stats.json")

    imb = report["imbalance"]
    print(f"\nImbalance spread: {imb['spread'] * 100:.1f}%  (ambang {IMBALANCE_THRESHOLD * 100:.0f}%)")
    print(f"Perlu penanganan: {imb['needs_handling']}  -> {imb['recommended_strategy']}")

    return report


if __name__ == "__main__":
    build_splits()
