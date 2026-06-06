"""Validate minimum gate requirements before entering phase 3."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_management import REQUIRED_COLUMNS, load_source_manifest, validate_required_columns


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate phase 2 gate artifacts.")
    parser.add_argument(
        "--corpus",
        default=str(PROJECT_ROOT / "data" / "processed" / "phase2_sentiment_corpus.csv"),
        help="Path to the combined phase 2 corpus CSV",
    )
    parser.add_argument(
        "--manifest",
        default=str(PROJECT_ROOT / "data" / "raw" / "source_manifest.yaml"),
        help="Path to source manifest file",
    )
    return parser


def ensure_manifest_has_sources(manifest_path: Path) -> None:
    payload = load_source_manifest(manifest_path)
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("Manifest must contain a non-empty `sources` list")


def main() -> int:
    args = build_argument_parser().parse_args()
    corpus_path = Path(args.corpus)
    manifest_path = Path(args.manifest)

    if not corpus_path.exists():
        raise FileNotFoundError(f"Combined corpus not found: {corpus_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Source manifest not found: {manifest_path}")

    missing_columns = validate_required_columns(corpus_path, REQUIRED_COLUMNS)
    if missing_columns:
        raise ValueError(f"Combined corpus missing required columns: {missing_columns}")

    ensure_manifest_has_sources(manifest_path)
    print("Phase 2 gate validation passed.")
    print(f"- corpus: {corpus_path}")
    print(f"- manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
