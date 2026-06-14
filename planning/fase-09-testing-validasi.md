# Fase 9 — Testing & Validation (Checkpoint 9)

## Tujuan
Melakukan pengujian sistem secara menyeluruh dan validasi oleh praktisi e-commerce untuk memastikan relevansi dan kelayakan implementasi.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-9.1 | Sistem harus lolos unit testing pada setiap fungsi/module (preprocessing, inference, rule-based, dashboard). |
| FR-9.2 | Sistem harus lolos integration testing untuk memastikan aliran data antar module berjalan dengan benar. |
| FR-9.3 | Sistem harus lolos UI testing / usability testing pada pengguna nyata (non-teknis). |
| FR-9.4 | Sistem harus menjalani expert validation oleh 1–2 praktisi e-commerce (seller OmorfoShop). |

## Testing Scope

| Jenis Testing | Fokus | Tools/Metode |
|---|---|---|
| Unit Testing | Setiap fungsi individual (preprocessing, inference, rule-engine, dashboard) | `pytest` |
| Integration Testing | Aliran data antar module (preprocessing → model → recommendation → dashboard) | End-to-end workflow test |
| UI Testing / Usability | Kemudahan penggunaan dashboard oleh pengguna non-teknis | Observasi langsung pada pengguna nyata |
| Model Testing | Akurasi model pada test set dan dataset OmorfoShop | Metrik evaluasi (accuracy, F1 macro) |

> **Posisi awal Fase 9 (per 2026-06-12):** unit testing sebagian besar sudah
> berjalan paralel selama pengembangan Fase 7–8 — **168 unit test** hijau di
> `tests/` (preprocessing, rule engine, seluruh modul dashboard termasuk
> Module 7 Insight Analitik, smoke render 8 halaman via `AppTest`, multi-URL
> fetch & simpanan sesi). Fokus Fase 9 yang tersisa: (1) dokumentasi formal
> hasil unit testing, (2) integration test end-to-end dengan model nyata,
> (3) usability testing, (4) expert validation, dan (5) item yang tak
> terjangkau test otomatis — **verifikasi manual fetch nyata Shopee** (juga
> penutup gate Fase 8).
>
> **Progres Fase 9 (per 2026-06-14):**
> - **(1) Unit testing — SELESAI & terdokumentasi.** Ditambah 31 unit test
>   khusus `src/preprocessing/` (`tests/test_preprocessing.py`) yang sebelumnya
>   belum ada → **199 unit test** hijau total (sebelumnya 168). Laporan formal:
>   [`outputs/reports/phase9_unit_test_report.md`](../outputs/reports/phase9_unit_test_report.md)
>   + ringkasan terukur [`phase9_unit_test_summary.json`](../outputs/reports/phase9_unit_test_summary.json).
> - **(2) Integration test end-to-end model nyata — SELESAI** (jalur CSV).
>   `tests/integration/test_e2e_real_model.py` (16 test, marker `integration`):
>   CSV mentah OmorfoShop → preprocessing → inferensi IndoBERT nyata → rule
>   engine → render 8 halaman dashboard → ekspor CSV. Artefak:
>   [`phase9_integration_report.json`](../outputs/reports/phase9_integration_report.json).
> - **Tersisa:** (3) usability testing, (4) expert validation, (5) verifikasi
>   **manual** fetch nyata Shopee jalur CDP (perlu desktop ber-login; jalur
>   analisis lain sudah tervalidasi otomatis). Tiga item ini butuh keterlibatan
>   manusia/desktop, di luar jangkauan test otomatis.

### Skenario UI/Usability — wajib mencakup fitur pasca-gate Fase 8.5

Selain alur dasar (upload CSV → analisis → baca hasil → ekspor), sesi
usability harus menguji fitur yang ditambahkan setelah spek awal:

1. Pencarian kata + paginasi di **Detail Ulasan**.
2. Toggle **ketidaksesuaian rating–sentimen** (Detail) + kartu mismatch (Dashboard) — apakah pengguna memahami maknanya.
3. Drill-down **kata kunci teratas per kelas** dan **perbandingan per produk** (Visualisasi).
4. **Bukti ulasan representatif** & kondisi per produk (Rekomendasi).
5. Filter global (Pengaturan) + badge "X dari Y ulasan" di semua halaman hasil.
6. *(Lokal/desktop saja)* multi-URL auto-fetch: tambah baris URL, kuota dibagi rata, simpanan sesi (link lama tidak di-fetch ulang), panel hapus per produk.
7. Empty state & seksi Troubleshooting (Tentang) — apakah pesan cukup menolong tanpa pendamping.

## Expert Validation

Validasi praktisi menggunakan kuesioner terstruktur dengan skala Likert 1–5 (1 = Sangat Tidak Setuju, 5 = Sangat Setuju).

| Aspek Validasi | Item Kuesioner | Jumlah Item |
|---|---|---|
| Hasil Analisis Sentimen | Kesesuaian klasifikasi, realisme distribusi, relevansi word cloud | 3 item |
| Rule-Based Mapping | Kemudahan pemahaman threshold, kesesuaian kategori dengan realita, transparansi sistem | 3 item |
| Rekomendasi Strategi Pemasaran | Relevansi, kemampuan implementasi, potensi dampak bisnis, kerealistisan sumber daya | 4 item |
| Kesesuaian Konteks Pasar | Kesesuaian dinamika e-commerce, keselarasan perilaku pelanggan kecantikan | 2 item |
| Pertanyaan Terbuka | Strategi paling relevan, yang kurang sesuai, saran pengembangan, potensi monitoring berkala | 4 pertanyaan |

> **Instrumen siap pakai (per 2026-06-14):**
> [`outputs/reports/phase9_expert_validation_questionnaire.md`](../outputs/reports/phase9_expert_validation_questionnaire.md)
> (identitas validator, bahan yang dinilai, 13 item Likert + 4 pertanyaan terbuka,
> item insight opsional, rekap & interpretasi skor) + template entri skor
> [`phase9_expert_validation_scoring_template.csv`](../outputs/reports/phase9_expert_validation_scoring_template.csv).
> **Catatan rekonsiliasi:** tabel di atas berjumlah 12 item Likert; instrumen
> menambahkan 1 item "Penilaian Keseluruhan" (No. 13) agar genap **17 item inti**
> (13 Likert + 4 terbuka) sesuai proposal — **cocokkan No. 13 dengan proposal**.
> Pelaksanaan dengan seller OmorfoShop & penyusunan `validation_report.pdf` masih
> menunggu (butuh responden nyata).

## Deliverables Checkpoint 9

- [x] Unit testing selesai dan terdokumentasi. *(199 test hijau; laporan `outputs/reports/phase9_unit_test_report.md`)*
- [x] Integration testing selesai (alur preprocessing → model → recommendation → dashboard). *(jalur CSV otomatis, 16 test `tests/integration/`; jalur fetch CDP = verifikasi manual, masih terbuka)*
- [ ] Usability testing pada pengguna nyata selesai.
- [ ] Expert validation oleh praktisi OmorfoShop selesai.
- [ ] Bug fixing selesai berdasarkan temuan testing.
- [ ] Validation report tersedia: skor rata-rata Likert + masukan kualitatif (`outputs/reports/validation_report.pdf`).

## Implementasi

- ✅ Unit test di `tests/` (`pytest`) — **199 test** (sebelumnya 168) mencakup
  `src/preprocessing/`, `src/recommendation/`, dan seluruh `src/dashboard/`.
  Ditutup gap cakupan `src/preprocessing/` dengan `tests/test_preprocessing.py`
  (31 test: cleaning regex + guard FR-3.3 tanpa stemming/stopword + `clean_frame`).
  Dirangkum di [`outputs/reports/phase9_unit_test_report.md`](../outputs/reports/phase9_unit_test_report.md)
  (jumlah test per modul, semua hijau).
- ✅ Integration test end-to-end dengan **model nyata** (bukan df pra-label):
  CSV mentah → inferensi IndoBERT → rule engine → render dashboard → ekspor CSV
  — `tests/integration/test_e2e_real_model.py` (16 test, marker `integration`,
  jalan eksplisit `pytest -m integration`). Artefak run:
  [`outputs/reports/phase9_integration_report.json`](../outputs/reports/phase9_integration_report.json).
  *Jalur kedua* URL Auto-Fetch (CDP) → analisis (sekaligus menutup verifikasi
  manual fetch Fase 8; uji multi-URL + simpanan sesi) **masih perlu dijalankan
  manual** di desktop ber-login — belum tercakup otomatis.
- Lakukan sesi usability testing dengan 1–2 pengguna non-teknis (skenario di
  atas, termasuk fitur pasca-gate).
- ✅ Kuesioner expert validation **sudah disusun** (`phase9_expert_validation_questionnaire.md`
  + template skor `.csv`) — tinggal **dilaksanakan** dengan seller OmorfoShop lalu
  direkap ke `validation_report.pdf`.
  *(Opsional, bila pembimbing setuju)*: item kuesioner untuk fitur insight baru
  (kebermanfaatan deteksi ketidaksesuaian rating–sentimen & perbandingan kondisi
  per produk) sudah tersedia di Bagian E instrumen — tanpa mengubah 17 item inti.

## Gate ke Fase Berikutnya

Lanjut ke Fase 10 hanya jika seluruh pengujian inti lulus, bug kritis sudah diperbaiki, dan validation report dari praktisi tersedia.
