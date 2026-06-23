"""
Konversi Markdown -> PDF (pure-Python, tanpa dependency sistem).

Dipakai Fase 10 untuk menghasilkan laporan PDF dari sumber Markdown (mis.
validation report) agar deliverable dokumentasi terpenuhi. Memakai `markdown`
(MD -> HTML) + `xhtml2pdf`/pisa (HTML -> PDF) — keduanya pure-Python sehingga
jalan di Windows tanpa GTK/wkhtmltopdf.

Pemakaian:
    python scripts/md_to_pdf.py <input.md> <output.pdf>
    python scripts/md_to_pdf.py outputs/reports/phase9_validation_report.md \
        outputs/reports/validation_report.pdf

Catatan: ini alat dokumentasi (dev-only). Dependensi ada di requirements-dev.txt.
"""

from __future__ import annotations

import sys
from pathlib import Path

import markdown  # type: ignore
from xhtml2pdf import pisa  # type: ignore

# Gaya cetak sederhana & rapi (tabel bergaris, font serif, margin nyaman).
_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; color: #1A1D21;
       line-height: 1.4; }
h1 { font-size: 16pt; border-bottom: 2px solid #FF4B4B; padding-bottom: 4px; }
h2 { font-size: 13pt; margin-top: 16px; color: #333; }
h3 { font-size: 11pt; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; }
th, td { border: 1px solid #999; padding: 4px 6px; text-align: left; font-size: 9pt; }
th { background-color: #F4F5F7; }
blockquote { color: #555; border-left: 3px solid #ccc; padding-left: 10px; margin-left: 0; }
code { background-color: #F4F5F7; padding: 1px 3px; }
"""


def convert(src: Path, dest: Path) -> None:
    """Render `src` (Markdown) menjadi PDF di `dest`."""
    if not src.exists():
        raise FileNotFoundError(f"Sumber Markdown tidak ditemukan: {src}")

    html_body = markdown.markdown(
        src.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "sane_lists"],
    )
    html_doc = (
        f"<html><head><style>{_CSS}</style></head><body>{html_body}</body></html>"
    )

    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as fh:
        result = pisa.CreatePDF(html_doc, dest=fh, encoding="utf-8")
    if result.err:
        raise RuntimeError(f"Gagal membuat PDF: {result.err} error.")
    print(f"PDF dibuat: {dest}")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    convert(Path(argv[1]), Path(argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
