"""
Fase 3 — Runner preprocessing: cleaning korpus train/validation/test.

Input : data/processed/{train,validation,test}.csv   (kolom: text,label,source)
Output: data/processed/clean_{train,validation,test}.csv
        outputs/reports/phase3_preprocessing_stats.json

Tahap tokenization IndoBERT TIDAK dijalankan di sini (transformers/torch tidak
terpasang lokal — dijalankan di Google Colab pada Fase 4 lewat
`PreprocessingPipeline.tokenizer.tokenize_dataset(...)`). Runner ini memvalidasi
& membersihkan teks sehingga datasetnya siap langsung ditokenisasi & dilatih.

Jalankan:
    .venv\\Scripts\\python.exe -m src.phase3_preprocessing
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.pipeline import PreprocessingPipeline  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"

SPLITS = ("train", "validation", "test")


def _distribution(df: pd.DataFrame) -> dict:
    counts = df["label"].value_counts().to_dict()
    total = len(df)
    pct = {k: round(v / total * 100, 2) for k, v in counts.items()}
    return {"total": total, "counts": counts, "pct": pct}


def run(save: bool = True) -> dict:
    pipeline = PreprocessingPipeline()
    report: dict = {
        "model_name": pipeline.tokenizer.model_name,
        "max_length": pipeline.max_length,
        "stemming": False,
        "stopword_removal": False,
        "tokenization_executed_here": False,
        "tokenization_note": (
            "Tokenization IndoBERT dijalankan di Google Colab (Fase 4); "
            "wrapper: src/preprocessing/tokenizer_wrapper.py"
        ),
        "splits": {},
    }

    for split in SPLITS:
        src_path = PROCESSED_DIR / f"{split}.csv"
        if not src_path.exists():
            raise FileNotFoundError(
                f"{src_path} belum ada. Jalankan dulu: python -m src.phase2_dataset_builder"
            )
        df = pd.read_csv(src_path)
        cleaned = pipeline.clean_frame(df)
        stats = pipeline.last_stats

        print(
            f"[{split}] {stats.rows_in} -> {stats.rows_out} baris "
            f"(buang: kosong={stats.dropped_empty_text}, "
            f"label_hilang={stats.dropped_missing_label}, "
            f"label_invalid={stats.dropped_invalid_label}, "
            f"duplikat={stats.dropped_duplicate})"
        )

        report["splits"][split] = {
            "cleaning": stats.as_dict(),
            "distribution": _distribution(cleaned),
        }

        if save:
            out_path = PROCESSED_DIR / f"clean_{split}.csv"
            cleaned.to_csv(out_path, index=False, encoding="utf-8")
            print(f"        disimpan -> data/processed/clean_{split}.csv")

    if save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / "phase3_preprocessing_stats.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("\nLaporan -> outputs/reports/phase3_preprocessing_stats.json")

    return report


if __name__ == "__main__":
    run()
