"""
Validasi gate Fase 3 (Data Preprocessing) sebelum lanjut ke Fase 4.

Memeriksa deliverable Checkpoint 3:
1. File clean_{train,validation,test}.csv ada & punya kolom wajib.
2. Tidak ada teks kosong.
3. Tidak ada label hilang / di luar skema kanonik.
4. Pipeline TIDAK mengimpor Sastrawi/NLTK (tanpa stemming & stopword removal).
5. Wrapper tokenizer IndoBERT tersedia & terkonfigurasi (max_length=128).

Jalankan:
    .venv\\Scripts\\python.exe -m scripts.validate_phase3_gate
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.tokenizer_wrapper import IndoBERTTokenizerWrapper  # noqa: E402
from src.utils.label_harmonizer import CANONICAL_LABELS  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PREP_DIR = PROJECT_ROOT / "src" / "preprocessing"
REQUIRED_COLUMNS = {"text", "label", "source"}
SPLITS = ("train", "validation", "test")

# Impor terlarang (stemming / stopword removal)
_FORBIDDEN_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(sastrawi|nltk)\b", re.IGNORECASE | re.MULTILINE
)


def _check(passed: bool, label: str, detail: str = "") -> bool:
    mark = "OK " if passed else "GAGAL"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{mark}] {label}{suffix}")
    return passed


def validate() -> bool:
    ok = True

    # 1-3. Dataset bersih
    for split in SPLITS:
        path = PROCESSED_DIR / f"clean_{split}.csv"
        if not path.exists():
            ok &= _check(False, f"clean_{split}.csv ada", f"tidak ditemukan: {path}")
            continue
        df = pd.read_csv(path)

        ok &= _check(
            REQUIRED_COLUMNS.issubset(df.columns),
            f"clean_{split}.csv kolom wajib",
            f"kolom: {list(df.columns)}",
        )
        empty = int((df["text"].fillna("").str.len() == 0).sum())
        ok &= _check(empty == 0, f"clean_{split}.csv tanpa teks kosong", f"{empty} kosong")

        missing = int(df["label"].isna().sum())
        ok &= _check(missing == 0, f"clean_{split}.csv tanpa label hilang", f"{missing} hilang")

        invalid = int((~df["label"].isin(CANONICAL_LABELS)).sum())
        ok &= _check(
            invalid == 0, f"clean_{split}.csv label kanonik", f"{invalid} di luar {CANONICAL_LABELS}"
        )

    # 4. Tidak ada impor stemming/stopword
    offenders = []
    for py in PREP_DIR.glob("*.py"):
        if _FORBIDDEN_IMPORT_RE.search(py.read_text(encoding="utf-8")):
            offenders.append(py.name)
    ok &= _check(
        not offenders,
        "tanpa impor Sastrawi/NLTK (tanpa stemming & stopword removal)",
        f"ditemukan di: {offenders}" if offenders else "",
    )

    # 5. Wrapper tokenizer terkonfigurasi
    wrapper = IndoBERTTokenizerWrapper()
    ok &= _check(
        wrapper.model_name == "indolem/indobert-base-uncased" and wrapper.max_length == 128,
        "wrapper IndoBERT tokenizer terkonfigurasi",
        f"model={wrapper.model_name}, max_length={wrapper.max_length}",
    )

    return ok


def main() -> int:
    print("Validasi gate Fase 3 — Data Preprocessing")
    if validate():
        print("\nGate Fase 3 LULUS. Siap lanjut ke Fase 4 (Model Training).")
        return 0
    print("\nGate Fase 3 BELUM LULUS — perbaiki item GAGAL di atas.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
