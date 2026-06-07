"""
Validasi gate Fase 5 (Model Evaluation) sebelum lanjut ke Fase 6.

Memeriksa dua lapis:

A. Kesiapan kerangka (selalu bisa dicek lokal tanpa torch/transformers):
   1. Modul src/evaluation importable (config, metrics, cross_val_report).
   2. Pemetaan label kanonik konsisten (3 kelas, selaras Fase 4).
   3. File implementasi inti ada (metrics / evaluator / visualizer /
      cross_val_report).

B. Deliverable hasil evaluasi (terisi SETELAH eksekusi di Colab):
   4. evaluation_final.json ada (accuracy & f1_macro >= 0.85).
   5. confusion_matrix.png ada.
   6. learning_curve.png ada.
   7. Ringkasan 5-fold CV terbaca (dari report Fase 4).

Jalankan:
    .venv\\Scripts\\python.exe -m scripts.validate_phase5_gate
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.config import (  # noqa: E402
    CONFUSION_MATRIX_PNG,
    CV_REPORT_JSON,
    EVALUATION_FINAL_JSON,
    LABEL2ID,
    LEARNING_CURVE_PNG,
    NUM_LABELS,
    TARGET_ACCURACY,
    TARGET_F1_MACRO,
)

EVAL_DIR = PROJECT_ROOT / "src" / "evaluation"
CORE_MODULES = ("metrics.py", "evaluator.py", "visualizer.py", "cross_val_report.py")


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
        ok &= _check((EVAL_DIR / name).exists(), f"src/evaluation/{name} ada")

    # B. Deliverable hasil evaluasi (Colab)
    print("\nB. Deliverable hasil evaluasi (terisi setelah eksekusi Colab)")
    eval_ok = EVALUATION_FINAL_JSON.exists()
    ok &= _check(eval_ok, "evaluation_final.json ada", f"di {EVALUATION_FINAL_JSON}")
    if eval_ok:
        data = json.loads(EVALUATION_FINAL_JSON.read_text(encoding="utf-8"))
        metrics = data.get("metrics", data)
        acc = float(metrics.get("accuracy", 0.0))
        f1 = float(metrics.get("f1_macro", 0.0))
        ok &= _check(acc >= TARGET_ACCURACY, f"accuracy >= {TARGET_ACCURACY}", f"accuracy={acc:.4f}")
        ok &= _check(f1 >= TARGET_F1_MACRO, f"f1_macro >= {TARGET_F1_MACRO}", f"f1_macro={f1:.4f}")

    ok &= _check(CONFUSION_MATRIX_PNG.exists(), "confusion_matrix.png ada")
    ok &= _check(LEARNING_CURVE_PNG.exists(), "learning_curve.png ada")
    ok &= _check(CV_REPORT_JSON.exists(), "cross_validation_report.json terbaca (dari Fase 4)")

    return ok


def main() -> int:
    print("Validasi gate Fase 5 — Model Evaluation\n")
    if validate():
        print("\nGate Fase 5 LULUS. Siap lanjut ke Fase 6 (Sentiment Inference Engine).")
        return 0
    print(
        "\nGate Fase 5 BELUM LULUS. Item bagian A harus hijau sebelum evaluasi;"
        " item bagian B terisi setelah notebook Colab dijalankan & artefak diunduh."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
