# Laporan Usability Testing — Fase 9 (FR-9.3)

> Deliverable Checkpoint 9: *"Usability testing pada pengguna nyata selesai"* +
> *"Bug fixing selesai berdasarkan temuan testing."*
> Sistem: **Sentara** — Dashboard Analisis Sentimen Ulasan E-Commerce (IndoBERT).
> Instrumen: [`phase9_usability_task_scenarios.md`](phase9_usability_task_scenarios.md),
> [`phase9_usability_observation_sheet.md`](phase9_usability_observation_sheet.md),
> [`phase9_usability_sus_questionnaire.md`](phase9_usability_sus_questionnaire.md).

## 1. Metode & Peserta

- **Metode:** task-based usability testing + think-aloud, dilanjutkan kuesioner
  **SUS (System Usability Scale)**. Satu peserta per sesi, mode lokal/desktop.
- **Peserta:** 2 pengguna **non-teknis** (sesuai FR-9.3), dikumpulkan via Google Form.

| Kode | Latar | Lingkungan | Tanggal | Data uji |
|---|---|---|---|---|
| P1 | Mahasiswa Bisnis | Lokal/desktop | 21 Jun 2026 | `omorfo_reviews_minoritas` |
| P2 | Barista | Lokal/desktop | 22 Jun 2026 | Data implementasi skenario Excellent |

- **Tugas:** 10 skenario (T1–T10) mencakup alur dasar (input → analisis → baca
  hasil → ekspor) + fitur pasca-gate Fase 8.5 (pencarian/paginasi, mismatch
  rating–sentimen, kata kunci, filter global, multi-URL fetch, troubleshooting).

## 2. Skor SUS

| Item (1–10) | P1 | P2 |
|---|:-:|:-:|
| Jawaban | 4,2,4,4,4,2,4,2,4,5 | 3,5,3,4,4,2,3,3,3,3 |
| Jumlah kontribusi (0–40) | 25 | 19 |
| **Skor SUS (×2,5)** | **62,5** | **47,5** |

**Rata-rata SUS = 55,0** → **di bawah** ambang rata-rata industri (68).
Interpretasi: P1 = grade D (*marginal*), P2 = grade F. Temuan ini **konsisten**
dengan jawaban keduanya yang **"Ragu"** memakai sistem tanpa pendamping, dan
menjadi dasar perbaikan pada Bagian 5.

## 3. Metrik Tugas (observasi fasilitator)

Status: **B** = berhasil sendiri · **BB** = berhasil dengan bantuan · **G** = gagal.

| Tugas | Fitur diuji | P1 (status / dtk / err) | P2 (status / dtk / err) |
|---|---|:-:|:-:|
| T1 | Unggah + analisis | BB / 189 / 0 | BB / 36 / 0 |
| T2 | Baca hasil utama | B / 30 / 0 | BB / 55 / 0 |
| T3 | Pencarian kata + paginasi | B / 43 / 0 | B / 63 / 0 |
| T4 | Mismatch rating–sentimen | BB / 34 / 0 | B / 36 / 0 |
| T5 | Kata kunci negatif | BB / 20 / 0 | B / 21 / 0 |
| T6 | Rekomendasi + dasar | B / 14 / 0 | B / 24 / 0 |
| T7 | **Filter global (kategori+bulan)** | **BB / 114 / 2** | **BB / 93 / 2** |
| T8 | Ekspor CSV | B / 10 / 0 | B / 13 / 0 |
| T9 | Empty state / bantuan | B / 15 / 0 | BB / 62 / 0 |
| T10 | Multi-URL auto-fetch | BB / 67 / 1 | BB / 97 / 0 |

| Metrik | P1 | P2 | Rata-rata |
|---|:-:|:-:|:-:|
| Task success rate (B ÷ 10) | 50% | 50% | **50%** |
| Completion rate ((B+BB) ÷ 10) | 100% | 100% | **100%** |
| Total error | 3 | 2 | 5 |
| Waktu rata-rata/tugas | 53,6 dtk | 50,0 dtk | 51,8 dtk |

**Catatan kunci:** seluruh tugas **selesai** (tak ada kegagalan total), namun
separuh butuh bantuan fasilitator. **T7 (filter) adalah satu-satunya tugas
ber-error** (2 untuk masing-masing peserta) dan **berdurasi terlama** — titik
masalah usability paling tajam.

## 4. Temuan Kualitatif (think-aloud + wawancara)

| # | Temuan | Sumber | Keparahan |
|---|---|---|:-:|
| U1 | **Filter di Pengaturan membingungkan** (terutama filter bulan/tanggal) | P1 & P2 (paling membingungkan); T7 error+terlama | **Kritis** |
| U2 | **Navigasi & penemuan fitur belum jelas** | P1: "navigasi belum jelas, pencarian fitur belum jelas"; minta fitur *search* | Sedang |
| U3 | **Bahasa/istilah terlalu rumit untuk orang awam** | P2: "bahasa terlalu rumit", "instruksi sulit dipahami orang awam" | **Kritis** |
| U4 | **Bantuan kurang menolong** | P2 (T9): "bantuannya kurang jelas" | Sedang |
| U5 | Keduanya ragu memakai tanpa pendamping | P1 & P2 (jawaban "Ragu") | Sedang |
| — | Aspek positif: kemudahan pengambilan data (P1), visualisasi & word cloud (P2) | P1 & P2 | — |
| — | *Keluhan kurir kurang sopan* (P1) | P1 komentar | Di luar lingkup sistem |

## 5. Tindak Lanjut (Bug Fixing) — temuan → perbaikan

Seluruh temuan kritis & sedang telah **ditindaklanjuti** (commit `aebaf7c`,
2026-06-23). Temuan U-x dipetakan ke perbaikan konkret:

| Temuan | Perbaikan yang diterapkan |
|---|---|
| **U1** Filter membingungkan | Filter Pengaturan dirombak: **pilihan periode per-bulan (Bahasa Indonesia)** menggantikan input rentang tanggal mentah; "Confidence threshold" → **"Tingkat keyakinan minimum"** dipindah ke expander **"Saringan lanjutan"**; tombol **"Reset saringan"**; istilah & tooltip diperjelas. |
| **U2** Navigasi tak jelas | **Dashboard + Input disatukan jadi "Beranda" adaptif**; **navigasi progresif** — saat pertama dibuka hanya Beranda tampil, menu hasil muncul otomatis setelah analisis (lebih sedikit halaman & alur lebih linear). |
| **U3** Bahasa rumit | **Sapu jargon** menyeluruh (threshold compound/kelas/stopword/confidence/softmax → bahasa lugas); **judul menu awam** (Daftar Ulasan / Kata yang Sering Muncul / Saran Pemasaran); **ringkasan verdict bahasa-awam** di Beranda; "Skor" → **"Keyakinan"**; **glosarium** ditambahkan di Tentang. |
| **U4** Bantuan kurang jelas | Seksi **Troubleshooting** diperjelas + **glosarium istilah** di halaman Tentang. |
| **U5** Ragu tanpa pendamping | Konsekuensi gabungan U1–U4; ditambah **panduan 3 langkah** di Beranda + tombol **Reset/Tambah data** untuk alur coba-ulang yang aman. |
| Expert (terkait) | Kondisi pemasaran disederhanakan **5→4** (hapus "Moderate") + **label Bahasa Indonesia** (Sangat Baik/Baik/Perlu Perbaikan/Beragam–Tidak Stabil). |
| Kurir kurang sopan | **Di luar lingkup sistem** (operasional toko) — dicatat sebagai masukan bisnis, bukan perbaikan perangkat lunak. |

Verifikasi pasca-perbaikan: **207 unit test + 15 integration (model nyata) hijau**,
lint/format bersih, dashboard boot mulus pada kedua mode (input & ringkasan).

## 6. Kesimpulan

Sistem **fungsional dan dapat diselesaikan** oleh pengguna non-teknis (completion
100%, tanpa kegagalan), tetapi **kepuasan awal rendah (SUS 55)** akibat antarmuka
yang terlalu teknis dan filter yang membingungkan. Seluruh temuan testing telah
**diperbaiki**; pengujian SUS ulang disarankan sebagai pekerjaan lanjutan untuk
mengukur dampak perbaikan. Dengan 2 peserta, skor SUS bersifat **indikatif**;
bukti utama kelayakan bertumpu pada metrik task-based + temuan kualitatif yang
telah ditindaklanjuti.
