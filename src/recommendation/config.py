"""
Fase 7 — Konfigurasi rule-based marketing recommendation.

Modul ringan (tanpa dependency berat) berisi:
- Re-export label kanonik (positive/negative/neutral) dari Fase 4 agar tidak ada
  drift dengan output inferensi Fase 6.
- Nama 5 kondisi pemasaran (compound conditions) & ambang batasnya.
- Pemetaan kondisi -> daftar strategi pemasaran (lihat planning/fase-07-*.md).
- Lokasi output standar Fase 7 (marketing_recommendation.json).

Nilai mengikuti tabel "Threshold & Kondisi Pemasaran" pada
`planning/fase-07-marketing-recommendation.md` dan CLAUDE.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Label kanonik & folder report dipinjam dari Fase 4 supaya konsisten dengan
# kolom `predicted_label` yang dihasilkan engine inferensi Fase 6.
from src.modeling.config import (  # noqa: F401  (re-export)
    ID2LABEL,
    REPORTS_DIR,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Output standar Fase 7 (deliverable Checkpoint 7) ──────────────────────────
RECOMMENDATION_REPORT_JSON = REPORTS_DIR / "marketing_recommendation.json"

# ── Label kanonik (alfabetis: negative=0, neutral=1, positive=2) ──────────────
POSITIVE = "positive"
NEGATIVE = "negative"
NEUTRAL = "neutral"

# ── Nama 5 kondisi pemasaran ──────────────────────────────────────────────────
EXCELLENT = "Excellent Performance"
GOOD = "Good Performance"
MODERATE = "Moderate Performance"
POOR = "Poor Performance"
MIXED = "Mixed/Unstable"

CONDITIONS: tuple[str, ...] = (EXCELLENT, GOOD, MODERATE, POOR, MIXED)

# ── Ambang batas compound (proporsi 0..1) ─────────────────────────────────────
# Tiap kondisi performa memakai kriteria gabungan positif AND negatif.
# Mixed/Unstable adalah kondisi override: netral > 35% ATAU trend berubah.
# Catatan: nilai berikut sesuai tabel rencana; ada celah di antara tier
# (mis. pos 45% & neg 15%) yang sengaja jatuh ke fallback Mixed/Unstable.
THRESHOLDS: dict[str, dict[str, float]] = {
    EXCELLENT: {"pos_min": 0.50, "neg_max": 0.20},
    GOOD: {"pos_min": 0.40, "pos_max": 0.499, "neg_min": 0.20, "neg_max": 0.30},
    MODERATE: {"pos_min": 0.30, "pos_max": 0.399, "neg_min": 0.30, "neg_max": 0.40},
    POOR: {"pos_max": 0.299, "neg_min": 0.401},
}

# Mixed/Unstable
NEUTRAL_MIXED_THRESHOLD = 0.35  # netral > 35% -> persepsi tidak konsisten
# Ambang perubahan tren signifikan (selisih proporsi positif antar periode).
# TODO Fase 7: kalibrasi pada data OmorfoShop ber-`date_review`.
TREND_SHIFT_THRESHOLD = 0.15
# Ukuran sampel minimum per periode agar layak masuk deteksi shift. Tanpa guard
# ini, bulan bersampel kecil (n=1–2) menghasilkan swing proporsi palsu.
MIN_PERIOD_SIZE = 30

# ── Interpretasi singkat per kondisi (business insight inti) ──────────────────
CONDITION_INTERPRETATION: dict[str, str] = {
    EXCELLENT: (
        "Produk/layanan dikomunikasikan dengan sangat baik; kepuasan pelanggan tinggi."
    ),
    GOOD: "Produk dapat diterima, namun ada ruang untuk perbaikan.",
    MODERATE: "Keseimbangan antara kepuasan dan ketidakpuasan pelanggan.",
    POOR: "Produk/layanan menghadapi masalah signifikan; perlu perhatian urgent.",
    MIXED: "Persepsi pelanggan tidak konsisten; perlu monitoring lebih lanjut.",
}


# ── Rule-based mapping kondisi -> playbook strategi pemasaran ──────────────────
# Tiap strategi bukan sekadar kalimat samar, melainkan *playbook* terstruktur:
# judul aksi + langkah konkret + contoh penerapan (e-commerce umum) + fitur
# Sentara pendukung. Tujuannya agar pelaku usaha tahu PERSIS cara menjalankan
# strategi memakai dashboard ini. `fitur` merujuk nama halaman navigasi nyata
# (lihat app.py): "Dashboard", "Detail Ulasan", "Visualisasi & Word Cloud",
# "Rekomendasi Strategi", "Input & Pengambilan Data".
@dataclass(frozen=True)
class MarketingPlay:
    """Satu strategi pemasaran konkret + cara menjalankannya lewat fitur Sentara."""

    judul: str  # nama aksi singkat (jadi judul kartu di dashboard)
    langkah: tuple[str, ...]  # langkah implementasi konkret (urut)
    contoh: str  # contoh penerapan, gaya e-commerce umum
    fitur: str  # fitur/halaman Sentara yang mendukung eksekusi/monitoring

    def as_dict(self) -> dict:
        return {
            "judul": self.judul,
            "langkah": list(self.langkah),
            "contoh": self.contoh,
            "fitur": self.fitur,
        }


STRATEGY_PLAYBOOK: dict[str, tuple[MarketingPlay, ...]] = {
    EXCELLENT: (
        MarketingPlay(
            judul="Manfaatkan ulasan positif sebagai social proof",
            langkah=(
                "Buka halaman Rekomendasi Strategi → Bukti Ulasan Representatif "
                "dan salin 3–5 kutipan positif ber-confidence tertinggi.",
                "Tempatkan kutipan pada deskripsi produk, banner toko, dan konten "
                "media sosial.",
                "Sematkan kata kunci pujian yang paling sering muncul sebagai "
                "highlight penjualan.",
            ),
            contoh=(
                "Kutipan 'barang sesuai deskripsi, pengiriman cepat' (confidence "
                "99%) dijadikan caption foto produk dan testimoni di etalase toko."
            ),
            fitur=(
                "Rekomendasi Strategi → Bukti Ulasan Representatif (positif) + "
                "Visualisasi & Word Cloud (kelas positif)."
            ),
        ),
        MarketingPlay(
            judul="Perkuat loyalitas pada produk unggulan",
            langkah=(
                "Lihat Kondisi per Produk untuk menemukan produk ber-sentimen "
                "positif tertinggi.",
                "Tawarkan bundling, poin, atau membership untuk pembeli ulang "
                "produk tersebut.",
                "Prioritaskan stok dan promosi pada produk unggulan ini.",
            ),
            contoh=(
                "Produk dengan 90%+ ulasan positif dipaketkan bersama voucher "
                "pembelian berikutnya untuk mendorong repeat order."
            ),
            fitur="Rekomendasi Strategi → Kondisi per Produk.",
        ),
        MarketingPlay(
            judul="Jalankan program referral berbasis keunggulan yang dipuji",
            langkah=(
                "Buka Visualisasi & Word Cloud → Kata Kunci Teratas kelas positif "
                "untuk tahu keunggulan yang paling sering disebut.",
                "Angkat keunggulan itu sebagai pesan utama kampanye 'ajak teman'.",
                "Beri insentif (cashback/diskon) bagi pelanggan yang mereferensikan.",
            ),
            contoh=(
                "Kata 'awet' dan 'murah' mendominasi → tagline referral "
                "'Rekomendasikan yang awet & hemat, dapat cashback'."
            ),
            fitur="Visualisasi & Word Cloud → Kata Kunci Teratas / Word Cloud (positif).",
        ),
        MarketingPlay(
            judul="Pertahankan kualitas dengan pemantauan dini",
            langkah=(
                "Jadwalkan auto-fetch ulasan secara berkala di halaman Input & "
                "Pengambilan Data.",
                "Pantau apakah kondisi tetap Excellent dan perhatikan peringatan "
                "Perubahan Tren.",
                "Tindak lanjuti penurunan proporsi positif sebelum menjadi keluhan "
                "massal.",
            ),
            contoh=(
                "Setiap bulan fetch ulang ulasan; bila muncul peringatan tren "
                "positif turun >15%, tinjau perubahan pemasok atau logistik."
            ),
            fitur=(
                "Input & Pengambilan Data (auto-fetch) + peringatan Perubahan Tren "
                "di panel Rekomendasi."
            ),
        ),
    ),
    GOOD: (
        MarketingPlay(
            judul="Bedah keluhan spesifik dari ulasan negatif",
            langkah=(
                "Buka Rekomendasi Strategi → Bukti Ulasan Representatif (keluhan "
                "terkuat) untuk membaca keluhan paling meyakinkan.",
                "Buka Visualisasi & Word Cloud kelas negatif untuk menemukan tema "
                "keluhan yang berulang.",
                "Daftarkan 3 keluhan teratas sebagai backlog perbaikan.",
            ),
            contoh=(
                "Word cloud negatif menonjolkan 'lama' dan 'pengiriman' → akar "
                "masalah ada di logistik, bukan kualitas produk."
            ),
            fitur=(
                "Rekomendasi Strategi → Bukti Ulasan (negatif) + Visualisasi & "
                "Word Cloud (negatif)."
            ),
        ),
        MarketingPlay(
            judul="Perbaiki titik lemah lalu komunikasikan perbaikannya",
            langkah=(
                "Tetapkan target perbaikan pada keluhan teratas (mis. SLA "
                "pengiriman, QC kemasan).",
                "Setelah diperbaiki, umumkan ke pelanggan via deskripsi produk atau "
                "pengumuman toko.",
                "Pantau ulang lewat fetch berikutnya untuk memverifikasi keluhan "
                "menurun.",
            ),
            contoh=(
                "Keluhan kemasan penyok → ganti bubble wrap; tulis 'kini dikemas "
                "ekstra aman' di deskripsi, lalu cek ulasan bulan berikutnya."
            ),
            fitur=(
                "Detail Ulasan (filter keluhan) + Input & Pengambilan Data (fetch "
                "ulang untuk verifikasi)."
            ),
        ),
        MarketingPlay(
            judul="Naikkan rasio positif dengan menonjolkan keunggulan",
            langkah=(
                "Identifikasi keunggulan yang dipuji dari Word Cloud / Kata Kunci "
                "kelas positif.",
                "Perjelas keunggulan tersebut di judul dan foto produk agar "
                "ekspektasi pembeli tepat.",
                "Sertakan kutipan positif untuk meyakinkan calon pembeli yang ragu.",
            ),
            contoh=(
                "Banyak pujian 'sesuai foto' → tambahkan label 'real product, "
                "sesuai foto' pada thumbnail untuk menarik pembeli ragu."
            ),
            fitur="Visualisasi & Word Cloud → Kata Kunci / Word Cloud (positif).",
        ),
    ),
    MODERATE: (
        MarketingPlay(
            judul="Temukan akar masalah utama via analisis kata",
            langkah=(
                "Buka Visualisasi & Word Cloud → Word Cloud & Kata Kunci kelas "
                "negatif untuk memetakan masalah dominan.",
                "Kelompokkan keluhan ke kategori (produk / pengiriman / layanan).",
                "Urutkan berdasarkan frekuensi untuk menentukan prioritas perbaikan.",
            ),
            contoh=(
                "Kata 'rusak', 'beda', dan 'lambat' sama besar → tiga lini masalah "
                "ditangani paralel sesuai frekuensinya."
            ),
            fitur="Visualisasi & Word Cloud → Word Cloud & Kata Kunci Teratas (negatif).",
        ),
        MarketingPlay(
            judul="Tingkatkan kualitas produk & layanan secara terukur",
            langkah=(
                "Tetapkan KPI perbaikan (mis. rasio negatif < 30%) sebagai target.",
                "Perbaiki proses pada lini masalah teratas.",
                "Bandingkan kondisi antar produk untuk fokus pada yang terburuk.",
            ),
            contoh=(
                "SKU dengan negatif tertinggi dipisahkan; perbaikan QC difokuskan "
                "pada produk itu lebih dulu."
            ),
            fitur=(
                "Rekomendasi Strategi / Visualisasi → Kondisi per Produk + "
                "Pengaturan → Filter per produk."
            ),
        ),
        MarketingPlay(
            judul="Susun komunikasi yang lebih transparan",
            langkah=(
                "Tuliskan ekspektasi realistis (estimasi kirim, varian warna) di "
                "deskripsi produk.",
                "Tanggapi ulasan negatif secara terbuka dengan solusi konkret.",
                "Hindari klaim berlebihan yang memicu kekecewaan.",
            ),
            contoh=(
                "Cantumkan 'estimasi tiba 3–5 hari' agar keluhan 'lama' berkurang "
                "karena ekspektasi pembeli sudah selaras."
            ),
            fitur="Detail Ulasan (baca konteks keluhan untuk menyusun balasan).",
        ),
        MarketingPlay(
            judul="Cek keluhan tersembunyi lewat ketidaksesuaian rating–sentimen",
            langkah=(
                "Buka Dashboard / Detail Ulasan dan tinjau ulasan rating tinggi "
                "tetapi bersentimen negatif.",
                "Identifikasi keluhan yang luput dari skor bintang.",
                "Tindak lanjuti karena ini sinyal ketidakpuasan yang tak tampak di "
                "rata-rata rating.",
            ),
            contoh=(
                "Pelanggan beri bintang 5 tapi menulis 'produk bagus, sayang dusnya "
                "penyok' → masalah kemasan tetap perlu dibenahi."
            ),
            fitur="Dashboard / Detail Ulasan → Ketidaksesuaian Rating ↔ Sentimen.",
        ),
    ),
    POOR: (
        MarketingPlay(
            judul="Triase keluhan paling mendesak",
            langkah=(
                "Buka Bukti Ulasan Representatif (keluhan terkuat) dan Word Cloud "
                "negatif untuk masalah paling tajam.",
                "Pisahkan masalah fatal (rusak, tidak sesuai, penipuan) dari yang "
                "minor.",
                "Tangani masalah fatal lebih dulu sebagai prioritas darurat.",
            ),
            contoh=(
                "Dominasi kata 'rusak' dan 'tidak sesuai' → hentikan sementara "
                "penjualan SKU bermasalah sampai QC beres."
            ),
            fitur=(
                "Rekomendasi Strategi → Bukti Ulasan (negatif) + Visualisasi & "
                "Word Cloud (negatif)."
            ),
        ),
        MarketingPlay(
            judul="Evaluasi harga, kualitas, dan kemasan",
            langkah=(
                "Periksa kata kunci negatif terkait 'mahal', 'murahan', 'kemasan', "
                "'rusak'.",
                "Bandingkan value produk dengan harga dan kompetitor.",
                "Perbaiki kemasan/QC sebelum melanjutkan promosi berbayar.",
            ),
            contoh=(
                "Kata 'mahal' dan 'mengecewakan' menonjol → tinjau ulang harga atau "
                "tingkatkan kualitas agar sepadan."
            ),
            fitur="Visualisasi & Word Cloud → Kata Kunci Teratas (negatif).",
        ),
        MarketingPlay(
            judul="Lakukan recovery pelanggan secara terbuka",
            langkah=(
                "Akui masalah utama lewat pengumuman toko dan balasan ulasan.",
                "Tawarkan solusi konkret (refund, ganti, garansi) bagi pelanggan "
                "terdampak.",
                "Komunikasikan langkah perbaikan yang sudah atau akan dilakukan.",
            ),
            contoh=(
                "Publikasikan permintaan maaf + program ganti barang untuk pembeli "
                "yang menerima produk cacat pada periode bermasalah."
            ),
            fitur="Detail Ulasan (identifikasi ulasan terdampak untuk ditindaklanjuti).",
        ),
        MarketingPlay(
            judul="Hentikan kerugian: fokus pada produk terparah",
            langkah=(
                "Buka Kondisi per Produk untuk menemukan SKU berkondisi Poor.",
                "Pause atau perbaiki produk terparah agar tidak menyeret reputasi "
                "toko.",
                "Alihkan anggaran promosi ke produk yang masih sehat.",
            ),
            contoh=(
                "Dua SKU berkondisi Poor dinonaktifkan sementara; anggaran iklan "
                "dialihkan ke produk ber-sentimen positif."
            ),
            fitur=(
                "Rekomendasi Strategi / Visualisasi → Kondisi per Produk + "
                "Pengaturan → Filter per produk."
            ),
        ),
    ),
    MIXED: (
        MarketingPlay(
            judul="Selaraskan ekspektasi lewat edukasi produk",
            langkah=(
                "Periksa ketidaksesuaian rating–sentimen untuk melihat kesenjangan "
                "ekspektasi vs realita.",
                "Buat konten edukasi (cara pakai, spesifikasi, FAQ) yang menjawab "
                "kebingungan.",
                "Tampilkan informasi penting sebelum pembelian untuk menekan ulasan "
                "netral/bingung.",
            ),
            contoh=(
                "Banyak ulasan netral 'masih bingung pakainya' → tambahkan panduan "
                "pemakaian bergambar di galeri produk."
            ),
            fitur="Dashboard / Detail Ulasan → Ketidaksesuaian Rating ↔ Sentimen.",
        ),
        MarketingPlay(
            judul="Perkuat deskripsi agar persepsi konsisten",
            langkah=(
                "Identifikasi istilah ambigu dari Word Cloud kelas netral.",
                "Perjelas spesifikasi, ukuran, varian, dan isi paket di deskripsi.",
                "Hilangkan klaim yang menimbulkan tafsir ganda.",
            ),
            contoh=(
                "Netral seputar 'ukuran' → cantumkan tabel dimensi dan perbandingan "
                "agar pembeli tidak ragu."
            ),
            fitur="Visualisasi & Word Cloud → Word Cloud / Kata Kunci (netral).",
        ),
        MarketingPlay(
            judul="Pantau sentimen secara berkala",
            langkah=(
                "Jadwalkan auto-fetch berulang dan amati panel Perubahan Tren.",
                "Catat periode saat proporsi berubah signifikan dan kaitkan dengan "
                "peristiwa (promo, ganti pemasok).",
                "Tetapkan ambang peringatan untuk tindak lanjut cepat.",
            ),
            contoh=(
                "Tren positif anjlok di bulan tertentu bertepatan dengan ganti "
                "kurir → kembalikan kurir lama atau perbaiki SLA."
            ),
            fitur=(
                "Input & Pengambilan Data (auto-fetch) + panel Perubahan Tren "
                "(Rekomendasi)."
            ),
        ),
        MarketingPlay(
            judul="Investigasi penyebab ketidakstabilan",
            langkah=(
                "Tinjau apakah Mixed dipicu netral tinggi atau perubahan tren "
                "(lihat keterangan kondisi).",
                "Bandingkan kondisi antar produk untuk melihat apakah masalah "
                "menyeluruh atau spesifik.",
                "Telusuri ulasan netral terbaru untuk menemukan akar penyebabnya.",
            ),
            contoh=(
                "Mixed karena netral 38% → ternyata satu produk baru membanjiri "
                "ulasan ambigu; fokuskan edukasi pada produk itu."
            ),
            fitur=(
                "Rekomendasi Strategi (keterangan kondisi) → Kondisi per Produk + "
                "Detail Ulasan."
            ),
        ),
    ),
}

# Mapping ringkas kondisi -> daftar judul strategi (kontrak lama: list[str]).
# Diturunkan dari STRATEGY_PLAYBOOK agar judul tidak terduplikasi & selalu sinkron.
STRATEGY_MAP: dict[str, list[str]] = {
    condition: [play.judul for play in plays]
    for condition, plays in STRATEGY_PLAYBOOK.items()
}


def _pct(value: float) -> int:
    """Proporsi -> persen bulat via truncation (0.499 -> 49, 0.401 -> 40)."""
    return int(value * 100)


def condition_criteria() -> dict[str, str]:
    """Teks kriteria 5 kondisi untuk tampilan, digenerate dari THRESHOLDS.

    Satu-satunya sumber angka adalah THRESHOLDS & NEUTRAL_MIXED_THRESHOLD —
    dashboard tidak boleh menduplikasi nilai ambang sebagai string lepas.
    Kata-kata mengikuti tabel `planning/fase-07-marketing-recommendation.md`.
    """
    exc, good, mod, poor = (
        THRESHOLDS[EXCELLENT],
        THRESHOLDS[GOOD],
        THRESHOLDS[MODERATE],
        THRESHOLDS[POOR],
    )
    return {
        EXCELLENT: (
            f"Positif ≥ {_pct(exc['pos_min'])}% DAN Negatif ≤ {_pct(exc['neg_max'])}%"
        ),
        GOOD: (
            f"Positif {_pct(good['pos_min'])}–{_pct(good['pos_max'])}% "
            f"DAN Negatif {_pct(good['neg_min'])}–{_pct(good['neg_max'])}%"
        ),
        MODERATE: (
            f"Positif {_pct(mod['pos_min'])}–{_pct(mod['pos_max'])}% "
            f"DAN Negatif {_pct(mod['neg_min'])}–{_pct(mod['neg_max'])}%"
        ),
        POOR: (
            f"Positif < {_pct(poor['pos_max']) + 1}% "
            f"DAN Negatif > {_pct(poor['neg_min'])}%"
        ),
        MIXED: (
            f"Netral > {_pct(NEUTRAL_MIXED_THRESHOLD)}% " "ATAU tren berubah signifikan"
        ),
    }


def ensure_output_dirs() -> None:
    """Pastikan folder output Fase 7 ada (idempoten)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
