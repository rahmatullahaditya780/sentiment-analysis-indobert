"""
Fase 3 — Unit test pipeline preprocessing teks.

Menutup cakupan unit test untuk `src/preprocessing/` (cleaner regex + orkestrasi
`PreprocessingPipeline.clean_frame`). Semuanya murni Python/pandas — tahap
tokenisasi IndoBERT (butuh `transformers`) divalidasi pada integration test
end-to-end, bukan di sini, agar suite unit tetap cepat & tanpa dependency berat.

Fokus khusus FR-3.3: pipeline TIDAK boleh melakukan stemming / stopword removal
dan TIDAK mengimpor Sastrawi/NLTK (merusak konteks subword IndoBERT).
"""

from __future__ import annotations

import ast
import inspect

import pandas as pd
import pytest

import src.preprocessing.cleaner as cleaner_mod
import src.preprocessing.pipeline as pipeline_mod
from src.preprocessing import (
    CleaningStats,
    PreprocessingPipeline,
    case_fold,
    clean_text,
    preprocess_text,
)


# ── case_fold (FR-3.1) ────────────────────────────────────────────────────────
def test_case_fold_mengubah_ke_huruf_kecil():
    assert case_fold("BARANG Bagus BANGET") == "barang bagus banget"


def test_case_fold_mengoerce_non_string():
    assert case_fold(123) == "123"


# ── clean_text (FR-3.2) ───────────────────────────────────────────────────────
def test_clean_membuang_url_http():
    assert clean_text("Kunjungi https://shopee.co.id/produk sekarang") == (
        "Kunjungi sekarang"
    )


def test_clean_membuang_url_www():
    assert clean_text("cek www.toko.com ya") == "cek ya"


def test_clean_membuang_tag_html():
    assert clean_text("bagus <br> banget <b>sekali</b>") == "bagus banget sekali"


def test_clean_membuang_emoji():
    assert clean_text("mantap \U0001f60d\U0001f525 keren ❤") == "mantap keren"


def test_clean_membuang_simbol_non_teks():
    assert clean_text("harga @#$ murah % banget") == "harga murah banget"


def test_clean_meredam_tanda_baca_berulang():
    assert clean_text("bagus!!! mantap???") == "bagus! mantap?"


def test_clean_meredam_koma_berulang():
    assert clean_text("oke,,, sip") == "oke, sip"


def test_clean_menormalkan_elipsis_panjang_jadi_tiga_titik():
    assert clean_text("lamaaa.......") == "lamaaa..."


def test_clean_merapikan_spasi_dan_baris_baru():
    assert clean_text("BARANG   bagus\n\n  banget") == "BARANG bagus banget"


def test_clean_mempertahankan_huruf_beraksen():
    # Rentang À-ɏ dipertahankan (mis. café) — tak boleh ikut terbuang.
    assert clean_text("kopi café enak") == "kopi café enak"


def test_clean_tidak_mengubah_kapitalisasi():
    # clean_text murni membersihkan; lowercasing adalah tugas case_fold.
    assert clean_text("BARANG Bagus") == "BARANG Bagus"


def test_clean_none_mengembalikan_string_kosong():
    assert clean_text(None) == ""


@pytest.mark.parametrize("teks", ["https://x.com", "@#$%", "\U0001f60d", "<br>"])
def test_clean_konten_terhapus_total_jadi_kosong(teks):
    assert clean_text(teks) == ""


# ── preprocess_text (case fold -> clean) ──────────────────────────────────────
def test_preprocess_menggabung_casefold_dan_cleaning():
    assert preprocess_text("BAGUS!!! https://x.id keren") == "bagus! keren"


def test_preprocess_tidak_melakukan_stemming():
    # Imbuhan WAJIB utuh — "membaca" tak boleh menjadi "baca" (FR-3.3).
    out = preprocess_text("Membaca buku yang bagus")
    assert "membaca" in out
    assert out == "membaca buku yang bagus"


def test_preprocess_mempertahankan_stopword():
    # Stopword (yang, di, ke, dari) WAJIB tetap ada — konteks IndoBERT (FR-3.3).
    out = preprocess_text("paket dikirim dari toko ke rumah yang jauh")
    for stop in ("dari", "ke", "yang"):
        assert stop in out.split()


def test_preprocess_tidak_meredam_pengulangan_huruf():
    # Hanya tanda baca berulang yang diredam; elongasi huruf dibiarkan utuh
    # (IndoBERT subword menangani "lamaaa") — bukan tugas cleaner.
    assert "lamaaa" in preprocess_text("Lamaaa banget")


# ── Guard arsitektural FR-3.3: tanpa Sastrawi / NLTK ──────────────────────────
def _imported_roots(modul) -> set[str]:
    """Kumpulkan nama paket level-atas yang benar-benar di-`import` modul.

    Memparse AST (bukan cocok-teks) supaya penyebutan 'Sastrawi'/'NLTK' di
    docstring/komentar — yang justru menjelaskan keduanya TIDAK dipakai — tak
    ikut terhitung sebagai impor.
    """
    tree = ast.parse(inspect.getsource(modul))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return {r.lower() for r in roots}


@pytest.mark.parametrize("modul", [cleaner_mod, pipeline_mod])
def test_tidak_mengimpor_pustaka_stemming_atau_stopword(modul):
    roots = _imported_roots(modul)
    assert "sastrawi" not in roots
    assert "nltk" not in roots


# ── PreprocessingPipeline.clean_frame ─────────────────────────────────────────
def _pipeline() -> PreprocessingPipeline:
    return PreprocessingPipeline(text_column="text", label_column="label")


def test_clean_frame_membersihkan_teks_kolom():
    df = pd.DataFrame({"text": ["BAGUS!!! https://x.id"], "label": ["positive"]})
    out = _pipeline().clean_frame(df)
    assert out.loc[0, "text"] == "bagus!"


def test_clean_frame_membuang_label_hilang():
    df = pd.DataFrame({"text": ["bagus", "jelek"], "label": ["positive", None]})
    out = _pipeline().clean_frame(df)
    assert out["text"].tolist() == ["bagus"]
    assert _pipeline().clean_frame(df).shape[0] == 1


def test_clean_frame_membuang_teks_kosong_setelah_cleaning():
    # Baris kedua hanya emoji+URL -> kosong setelah cleaning -> dibuang.
    df = pd.DataFrame(
        {
            "text": ["bagus", "\U0001f60d https://x.id"],
            "label": ["positive", "negative"],
        }
    )
    pipe = _pipeline()
    out = pipe.clean_frame(df)
    assert out["text"].tolist() == ["bagus"]
    assert pipe.last_stats.dropped_empty_text == 1


def test_clean_frame_membuang_label_di_luar_skema_kanonik():
    df = pd.DataFrame({"text": ["bagus", "jelek"], "label": ["positive", "happy"]})
    pipe = _pipeline()
    out = pipe.clean_frame(df)
    assert out["label"].tolist() == ["positive"]
    assert pipe.last_stats.dropped_invalid_label == 1


def test_clean_frame_membuang_duplikat_teks_label():
    df = pd.DataFrame(
        {
            "text": ["barang bagus", "barang bagus", "barang jelek"],
            "label": ["positive", "positive", "negative"],
        }
    )
    pipe = _pipeline()
    out = pipe.clean_frame(df)
    assert len(out) == 2
    assert pipe.last_stats.dropped_duplicate == 1


def test_clean_frame_statistik_lengkap_dan_konsisten():
    df = pd.DataFrame(
        {
            "text": ["bagus", "jelek", "biasa", "bagus"],
            "label": ["positive", "negative", "neutral", "positive"],
        }
    )
    pipe = _pipeline()
    out = pipe.clean_frame(df)
    stats = pipe.last_stats
    assert isinstance(stats, CleaningStats)
    assert stats.rows_in == 4
    assert stats.rows_out == len(out) == 3  # satu duplikat dibuang
    assert stats.dropped_duplicate == 1
    # Sanity: rows_out = rows_in - semua yang dibuang.
    dibuang = (
        stats.dropped_empty_text
        + stats.dropped_missing_label
        + stats.dropped_invalid_label
        + stats.dropped_duplicate
    )
    assert stats.rows_out == stats.rows_in - dibuang


def test_clean_frame_tidak_memutasi_input():
    df = pd.DataFrame({"text": ["BAGUS!!!"], "label": ["positive"]})
    _pipeline().clean_frame(df)
    assert df.loc[0, "text"] == "BAGUS!!!"  # input asli utuh
