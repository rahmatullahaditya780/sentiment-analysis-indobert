# Kuesioner SUS (System Usability Scale) — Versi Indonesia — Fase 9 (FR-9.3)

**Sistem:** Sentara — Dashboard Analisis Sentimen Ulasan E-Commerce (IndoBERT)

> Diisi peserta **setelah** menyelesaikan tugas usability. SUS = 10 pernyataan
> baku (Brooke, 1996) menghasilkan skor 0–100. Pernyataan **berselang-seling**
> positif/negatif — isi sesuai perasaan Anda, **jangan lama berpikir**.

## Identitas

| Isian | Jawaban |
|---|---|
| Kode peserta | P… |
| Tanggal | …………………… |

## Petunjuk

Beri tanda pada **satu** angka untuk tiap pernyataan.
**1 = Sangat Tidak Setuju · 2 = Tidak Setuju · 3 = Netral · 4 = Setuju · 5 = Sangat Setuju.**

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 1 | Saya rasa saya akan **sering menggunakan** sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | Saya merasa sistem ini **terlalu rumit** padahal bisa dibuat lebih sederhana. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | Saya rasa sistem ini **mudah digunakan**. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 4 | Saya rasa saya **membutuhkan bantuan orang teknis** untuk dapat menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Saya merasa berbagai fungsi dalam sistem ini **terintegrasi dengan baik**. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Saya rasa **terlalu banyak ketidakkonsistenan** dalam sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 7 | Saya membayangkan **kebanyakan orang akan cepat belajar** menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Saya merasa sistem ini **sangat merepotkan/membingungkan** untuk digunakan. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | Saya merasa **sangat percaya diri** saat menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | Saya perlu **belajar banyak hal dulu** sebelum bisa menggunakan sistem ini. | ☐ | ☐ | ☐ | ☐ | ☐ |

*Tanda tangan peserta:* ……………………………

---

## Cara Menghitung Skor (diisi fasilitator)

SUS dihitung dari kontribusi tiap item (rentang 0–4), bukan dari rata-rata mentah:

- **Item ganjil (1, 3, 5, 7, 9):** kontribusi = **(skor jawaban − 1)**
- **Item genap (2, 4, 6, 8, 10):** kontribusi = **(5 − skor jawaban)**
- **Skor SUS = (jumlah seluruh kontribusi) × 2,5**  → rentang akhir **0–100**.

Contoh: jika seluruh item dijawab paling ideal, jumlah kontribusi = 40 → 40 × 2,5 = **100**.

### Tabel hitung (per peserta)

| No | Jenis | Jawaban (1–5) | Kontribusi |
|---|---|:-:|:-:|
| 1 | Ganjil → (jawaban − 1) | … | … |
| 2 | Genap → (5 − jawaban) | … | … |
| 3 | Ganjil → (jawaban − 1) | … | … |
| 4 | Genap → (5 − jawaban) | … | … |
| 5 | Ganjil → (jawaban − 1) | … | … |
| 6 | Genap → (5 − jawaban) | … | … |
| 7 | Ganjil → (jawaban − 1) | … | … |
| 8 | Genap → (5 − jawaban) | … | … |
| 9 | Ganjil → (jawaban − 1) | … | … |
| 10 | Genap → (5 − jawaban) | … | … |
| | **Jumlah kontribusi** | | **…** |
| | **SKOR SUS = jumlah × 2,5** | | **… / 100** |

> Template entri & perhitungan otomatis untuk beberapa peserta:
> `phase9_usability_sus_scoring_template.csv`.

---

## Interpretasi Skor SUS

| Skor SUS | Grade | Adjektiva | Penerimaan (Acceptability) |
|---|:-:|---|---|
| 84,1 – 100 | A+ / A | Best Imaginable / Excellent | Acceptable |
| 80,8 – 84,0 | A− | Excellent | Acceptable |
| 71,1 – 80,7 | B / B+ | Good | Acceptable |
| **68,0** | C | **Rata-rata industri** (acuan) | Marginal (atas) |
| 51,7 – 67,9 | D | OK / Poor | Marginal (bawah) |
| 0 – 51,6 | F | Awful / Worst Imaginable | Not Acceptable |

**Acuan utama:** skor **rata-rata** sistem secara umum ≈ **68**. Skor **≥ 68**
berarti **di atas rata-rata**; **> 80** tergolong **sangat baik** (grade A).

> Catatan metodologis: dengan 1–2 peserta, SUS hanya **indikasi kasar** (interval
> kepercayaan lebar). Sajikan skor SUS **berdampingan** dengan temuan kualitatif
> task-based (success rate + daftar masalah) sebagai bukti utama usability.
