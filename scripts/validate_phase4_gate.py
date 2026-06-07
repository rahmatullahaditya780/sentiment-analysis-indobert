"""
Validasi gate Fase 4 (Model Training & Fine-Tuning) sebelum lanjut ke Fase 5.

Memeriksa dua lapis:

A. Kesiapan kerangka (selalu bisa dicek lokal tanpa torch/transformers):
   1. Modul src/modeling importable (config & data).
   2. Pemetaan label kanonik konsisten (3 kelas).
   3. File implementasi inti ada (trainer / hyperparameter_search /
      cross_validation).

B. Deliverable hasil training (terisi SETELAH eksekusi di Colab):
   4. Best model + tokenizer tersimpan di models/best_model/.
   5. hyperparameter_log.csv ada (focused random search).
   6. cross_validation_report.json ada (mean F1 +/- std).
   7. phase4_final_metrics.json ada (metrik test set, f1_macro >= 0.85).

Jalankan:
    .venv\\Scripts\\python.exe -m scripts.validate_phase4_gate
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modeling.config import (  # noqa: E402
    BEST_MODEL_DIR,
    CV_REPORT_JSON,
    FINAL_METRICS_JSON,
    HYPERPARAM_LOG_CSV,
    LABEL2ID,
    NUM_LABELS,
)

MODELING_DIR = PROJECT_ROOT / "src" / "modeling"
CORE_MODULES = ("trainer.py", "hyperparameter_search.py", "cross_validation.py")
TARGET_F1 = 0.85


def _check(passed: bool, label: str, detail: str = "") -> bool:
    mark = "OK " if passed else "GAGAL"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{mark}] {label}{suffix}")
    return passed


def validate() -> bool:
    ok = True

    # A. Kesiapan kerangka
    print("A. Kesiapan kerangka")
    ok &= _check(
        NUM_LABELS == 3 and set(LABEL2ID) == {"positive", "negative", "neutral"},
        "pemetaan label kanonik (3 kelas)",
        f"{LABEL2ID}",
    )
    for name in CORE_MODULES:
        ok &= _check((MODELING_DIR / name).exists(), f"src/modeling/{name} ada")

    # B. Deliverable hasil training (Colab)
    print("\nB. Deliverable hasil training (terisi setelah eksekusi Colab)")
    has_model = BEST_MODEL_DIR.exists() and any(
        (BEST_MODEL_DIR / f).exists() for f in ("model.safetensors", "pytorch_model.bin")
    )
    has_tok = (BEST_MODEL_DIR / "tokenizer_config.json").exists()
    ok &= _check(has_model, "best model tersimpan", f"di {BEST_MODEL_DIR}")
    ok &= _check(has_tok, "tokenizer tersimpan bersama model")
    ok &= _check(HYPERPARAM_LOG_CSV.exists(), "hyperparameter_log.csv ada")
    ok &= _check(CV_REPORT_JSON.exists(), "cross_validation_report.json ada")

    metrics_ok = FINAL_METRICS_JSON.exists()
    ok &= _check(metrics_ok, "phase4_final_metrics.json ada")
    if metrics_ok:
        data = json.loads(FINAL_METRICS_JSON.read_text(encoding="utf-8"))
        f1 = float(data.get("f1_macro", data.get("eval_f1_macro", 0.0)))
        ok &= _check(
            f1 >= TARGET_F1,
            f"f1_macro test set >= {TARGET_F1}",
            f"f1_macro={f1:.4f}",
        )

    return ok


def main() -> int:
    print("Validasi gate Fase 4 — Model Training & Fine-Tuning\n")
    if validate():
        print("\nGate Fase 4 LULUS. Siap lanjut ke Fase 5 (Model Evaluation).")
        return 0
    print(
        "\nGate Fase 4 BELUM LULUS. Item bagian A harus hijau sebelum training;"
        " item bagian B terisi setelah notebook Colab dijalankan & artefak diunduh."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
