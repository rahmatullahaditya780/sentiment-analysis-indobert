"""
Fase 4 (revisi) — Augmentasi data kelas minoritas via Back-Translation.

Latar belakang
--------------
Distribusi kelas training sangat timpang: positif 59,1% / negatif 33,7% /
neutral 7,2% (selisih ~52% >> ambang "ekstrem >25%" di proposal). Proposal
(baris 177) menjanjikan *back-translation atau paraphrase* bila ketidakseimbangan
ekstrem. Modul ini merealisasikan janji tersebut: menambah sampel kelas `neutral`
dengan back-translation (ID -> pivot -> ID) sehingga teks baru tetap natural &
mempertahankan makna, alih-alih sekadar menduplikasi (yang rawan overfitting).

Strategi
--------
- Pivot bahasa berlapis (default ['en', 'de']) — tiap pivot menghasilkan satu
  varian per kalimat sumber; pivot kedua dipakai hanya untuk menutup kekurangan
  target sehingga total mencapai `target_count`.
- Hasil back-translation dilewatkan `preprocess_text` yang SAMA dengan training
  (case fold + cleaning regex) agar distribusinya identik dengan korpus latih.
- Dedupe: varian yang (setelah normalisasi) identik dengan sumber atau dengan
  varian lain dibuang — augmentasi sejati, bukan duplikat.
- Cache resume: tiap hasil terjemahan ditulis incremental ke `cache_csv` sehingga
  run panjang yang terputus (rate-limit / jaringan) bisa dilanjutkan tanpa
  mengulang panggilan API yang sudah berhasil.

Catatan: augmentasi HANYA pada training set. Validation & test set TIDAK
disentuh agar evaluasi tetap mencerminkan distribusi nyata (jujur secara metodologis).
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from src.modeling.config import PROCESSED_DIR
from src.preprocessing.cleaner import preprocess_text

# ── Lokasi I/O default ────────────────────────────────────────────────────────
CLEAN_TRAIN_CSV = PROCESSED_DIR / "clean_train.csv"
AUGMENTED_TRAIN_CSV = PROCESSED_DIR / "clean_train_augmented.csv"
BT_CACHE_CSV = PROCESSED_DIR / "_bt_neutral_cache.csv"

DEFAULT_PIVOTS = ["en", "de"]
MAX_CHARS = 4500  # batas aman per panggilan GoogleTranslator (limit ~5000)


def _normalize(text: str) -> str:
    """Bentuk ternormalisasi untuk pembandingan dedupe (lower + strip spasi)."""
    return " ".join(str(text).lower().split())


def back_translate(
    text: str,
    pivot: str = "en",
    src: str = "id",
    *,
    retries: int = 3,
    backoff: float = 2.0,
) -> str | None:
    """Back-translate satu teks: src -> pivot -> src. None bila gagal/tak layak.

    Memakai deep_translator.GoogleTranslator (tanpa API key). Retry dengan
    exponential backoff untuk meredam rate-limit/jaringan sesaat.
    """
    from deep_translator import GoogleTranslator

    text = str(text).strip()[:MAX_CHARS]
    if not text:
        return None

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            mid = GoogleTranslator(source=src, target=pivot).translate(text)
            if not mid:
                return None
            back = GoogleTranslator(source=pivot, target=src).translate(mid)
            return back or None
        except Exception as exc:  # jaringan / rate-limit / teks bermasalah
            last_err = exc
            time.sleep(backoff * (attempt + 1))
    print(f"    [warn] gagal back-translate (pivot={pivot}): {last_err}")
    return None


def _load_cache(cache_csv: Path) -> pd.DataFrame:
    if cache_csv.exists():
        return pd.read_csv(cache_csv)
    return pd.DataFrame(columns=["src_idx", "pivot", "raw_back", "clean_back"])


def augment_neutral(
    input_csv: str | Path = CLEAN_TRAIN_CSV,
    *,
    label_column: str = "label",
    text_column: str = "text",
    minority_label: str = "neutral",
    target_count: int = 3000,
    pivots: list[str] | None = None,
    output_csv: str | Path = AUGMENTED_TRAIN_CSV,
    cache_csv: str | Path = BT_CACHE_CSV,
    throttle: float = 0.4,
    seed: int = 42,
) -> dict:
    """Tambah sampel `minority_label` hingga ~`target_count` via back-translation.

    Menulis `output_csv` = train asli + sampel netral augmented. Mengembalikan
    ringkasan (jumlah asli, jumlah baru, total, distribusi akhir).
    """
    pivots = pivots or DEFAULT_PIVOTS
    input_csv, output_csv, cache_csv = Path(input_csv), Path(output_csv), Path(cache_csv)

    df = pd.read_csv(input_csv)
    minority = df[df[label_column] == minority_label].reset_index(drop=True)
    n_orig = len(minority)
    n_needed = max(0, target_count - n_orig)
    print(f"[augment] {minority_label}: {n_orig} asli, target {target_count} -> butuh {n_needed} baru")
    if n_needed == 0:
        df.to_csv(output_csv, index=False)
        return {"n_orig": n_orig, "n_new": 0, "n_total": n_orig}

    # set teks yang sudah ada (untuk dedupe) — seluruh teks netral asli
    seen: set[str] = {_normalize(t) for t in minority[text_column]}
    cache = _load_cache(cache_csv)
    cache_seen = {(int(r.src_idx), r.pivot) for r in cache.itertuples()}

    new_rows: list[dict] = []

    def _consume_cache_first():
        """Pakai hasil yang sudah ada di cache sebelum panggil API baru."""
        for r in cache.itertuples():
            if len(new_rows) >= n_needed:
                break
            cb = _normalize(r.clean_back) if isinstance(r.clean_back, str) else ""
            if cb and cb not in seen:
                seen.add(cb)
                new_rows.append(
                    {
                        text_column: r.clean_back,
                        label_column: minority_label,
                        "source": f"augment:bt-{r.pivot}",
                    }
                )

    _consume_cache_first()
    print(f"[augment] dari cache: {len(new_rows)} varian dipakai ulang")

    cache_buffer: list[dict] = []

    def _flush_cache():
        nonlocal cache_buffer
        if not cache_buffer:
            return
        pd.DataFrame(cache_buffer).to_csv(
            cache_csv,
            mode="a",
            header=not cache_csv.exists(),
            index=False,
        )
        cache_buffer = []

    # urutan sumber acak-tetap agar reprodusibel
    order = minority.sample(frac=1.0, random_state=seed).index.tolist()

    for pivot in pivots:
        if len(new_rows) >= n_needed:
            break
        print(f"[augment] pivot '{pivot}' — progress {len(new_rows)}/{n_needed}")
        for i in order:
            if len(new_rows) >= n_needed:
                break
            if (i, pivot) in cache_seen:
                continue  # sudah dicoba sebelumnya (sudah dikonsumsi di atas)
            src_text = str(minority.loc[i, text_column])
            back = back_translate(src_text, pivot=pivot)
            clean_back = preprocess_text(back) if back else ""
            cache_buffer.append(
                {
                    "src_idx": int(i),
                    "pivot": pivot,
                    "raw_back": back or "",
                    "clean_back": clean_back,
                }
            )
            cache_seen.add((i, pivot))
            norm = _normalize(clean_back)
            if clean_back and norm not in seen:
                seen.add(norm)
                new_rows.append(
                    {
                        text_column: clean_back,
                        label_column: minority_label,
                        "source": f"augment:bt-{pivot}",
                    }
                )
            if len(cache_buffer) >= 25:
                _flush_cache()
            if throttle:
                time.sleep(throttle)
        _flush_cache()

    _flush_cache()

    aug_df = pd.DataFrame(new_rows)
    combined = pd.concat([df, aug_df], ignore_index=True)
    combined = combined.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    combined.to_csv(output_csv, index=False)

    dist = combined[label_column].value_counts(normalize=True).mul(100).round(1).to_dict()
    summary = {
        "n_orig_minority": n_orig,
        "n_new": len(new_rows),
        "n_total_minority": n_orig + len(new_rows),
        "n_total_rows": len(combined),
        "distribution_pct": dist,
        "output_csv": str(output_csv),
    }
    print(f"[augment] selesai: +{len(new_rows)} netral -> total netral {summary['n_total_minority']}")
    print(f"[augment] distribusi akhir: {dist}")
    return summary


if __name__ == "__main__":  # pragma: no cover
    import json

    print(json.dumps(augment_neutral(), indent=2, ensure_ascii=False))
