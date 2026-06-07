"""
Fase 2 — Data Management: pembangunan unified corpus dari 3 sumber.

Sumber:
- SmSA (IndoNLU)              -> data/raw/smsa/{train,validation,test}_preprocess.tsv
- PRDECT-ID (snapshot)        -> data/raw/prdect_id/prdect_snapshot.csv
- Kaggle E-Commerce Review    -> data/raw/kaggle_ecommerce/*.csv  (opsional, skip jika belum ada)

Pipeline: load -> harmonisasi label -> normalisasi teks -> deduplikasi -> merge.
Output: data/processed/unified_corpus.csv  [text, label, source]

Jalankan:
    .venv\\Scripts\\python.exe -m src.data_management
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.label_harmonizer import (  # noqa: E402
    CANONICAL_LABELS,
    harmonize_rating,
    harmonize_smsa_int,
    harmonize_string,
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
UNIFIED_PATH = PROCESSED_DIR / "unified_corpus.csv"


# ── Loader per sumber ────────────────────────────────────────────────────────
def load_smsa() -> pd.DataFrame:
    """Muat 3 split SmSA, map integer label -> kanonik. Source: smsa:<split>."""
    smsa_dir = RAW_DIR / "smsa"
    files = {
        "smsa:train": smsa_dir / "train_preprocess.tsv",
        "smsa:validation": smsa_dir / "validation_preprocess.tsv",
        "smsa:test": smsa_dir / "test_preprocess.tsv",
    }
    frames = []
    for source, path in files.items():
        if not path.exists():
            print(f"  [SmSA] LEWAT — tidak ada: {path}")
            continue
        df = pd.read_csv(path, sep="\t", header=None, names=["text", "label"])
        df["label"] = df["label"].map(harmonize_smsa_int)
        df["source"] = source
        frames.append(df[["text", "label", "source"]])
        print(f"  [SmSA] {source}: {len(df)} baris")
    if not frames:
        return _empty()
    return pd.concat(frames, ignore_index=True)


def load_prdect_id() -> pd.DataFrame:
    """Muat snapshot PRDECT-ID (label sudah string kanonik). Source: prdect_id."""
    path = RAW_DIR / "prdect_id" / "prdect_snapshot.csv"
    if not path.exists():
        print(f"  [PRDECT-ID] LEWAT — tidak ada: {path}")
        return _empty()
    df = pd.read_csv(path)
    df["label"] = df["label"].map(harmonize_string)
    df["source"] = "prdect_id"
    print(f"  [PRDECT-ID] {len(df)} baris")
    return df[["text", "label", "source"]]


def load_kaggle() -> pd.DataFrame:
    """Muat Kaggle Indonesian E-Commerce Review (rizqinugroho).

    Mendeteksi otomatis kolom teks (review_text/content/ulasan) dan label
    (sentiment_label) atau rating (rating/star). Skip jika folder/file kosong.
    Source: kaggle_ecommerce.
    """
    kaggle_dir = RAW_DIR / "kaggle_ecommerce"
    csvs = sorted(kaggle_dir.glob("*.csv")) if kaggle_dir.exists() else []
    if not csvs:
        print(
            "  [Kaggle] LEWAT — belum ada CSV di data/raw/kaggle_ecommerce/. "
            "Unduh dataset rizqinugroho lalu jalankan ulang."
        )
        return _empty()

    frames = []
    for path in csvs:
        df = pd.read_csv(path)
        cols = {c.lower(): c for c in df.columns}
        text_col = _first_present(cols, ["review_text", "content", "ulasan", "review", "text"])
        if text_col is None:
            print(f"  [Kaggle] LEWAT {path.name} — kolom teks tidak ditemukan")
            continue

        label_col = _first_present(cols, ["sentiment_label", "sentiment", "label"])
        rating_col = _first_present(cols, ["rating", "star", "bintang", "score"])
        out = pd.DataFrame({"text": df[text_col]})
        if label_col is not None:
            out["label"] = df[label_col].map(harmonize_string)
        elif rating_col is not None:
            out["label"] = df[rating_col].map(harmonize_rating)
        else:
            print(f"  [Kaggle] LEWAT {path.name} — tak ada kolom label/rating")
            continue
        out["source"] = "kaggle_ecommerce"
        frames.append(out[["text", "label", "source"]])
        print(f"  [Kaggle] {path.name}: {len(out)} baris")

    return pd.concat(frames, ignore_index=True) if frames else _empty()


# ── Helper ───────────────────────────────────────────────────────────────────
def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["text", "label", "source"])


def _first_present(cols_lower: dict[str, str], candidates: list[str]) -> str | None:
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower[cand]
    return None


def _norm_key(text: str) -> str:
    """Kunci normalisasi untuk deduplikasi: lowercase + rapikan whitespace."""
    return " ".join(str(text).lower().split())


# ── Pipeline utama ───────────────────────────────────────────────────────────
def build_unified_corpus(save: bool = True) -> pd.DataFrame:
    """Gabungkan 3 sumber -> harmonisasi -> buang kosong -> dedup -> simpan."""
    print("Memuat sumber dataset…")
    df = pd.concat([load_smsa(), load_prdect_id(), load_kaggle()], ignore_index=True)

    if df.empty:
        raise RuntimeError("Tidak ada data termuat — periksa folder data/raw/.")

    before = len(df)

    # Buang teks/label kosong atau tidak valid
    df["text"] = df["text"].astype("string").str.strip()
    df = df[df["text"].notna() & (df["text"].str.len() > 0)]
    df = df[df["label"].isin(CANONICAL_LABELS)]
    after_clean = len(df)
    print(f"\nBuang kosong/invalid: {before - after_clean} baris")

    # Deduplikasi berbasis teks ternormalisasi (cegah data leakage)
    df["_key"] = df["text"].map(_norm_key)
    df = df.drop_duplicates(subset="_key", keep="first").drop(columns="_key")
    print(f"Buang duplikat: {after_clean - len(df)} baris")

    df = df.reset_index(drop=True)

    print(f"\nUnified corpus: {len(df)} baris")
    print("Distribusi label:", df["label"].value_counts().to_dict())
    print("Distribusi sumber:", df["source"].value_counts().to_dict())

    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(UNIFIED_PATH, index=False, encoding="utf-8")
        print(f"\nDisimpan -> {UNIFIED_PATH.relative_to(PROJECT_ROOT)}")

    return df


if __name__ == "__main__":
    build_unified_corpus()
