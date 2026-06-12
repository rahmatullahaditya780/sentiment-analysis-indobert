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

## Deliverables Checkpoint 9

- [ ] Unit testing selesai dan terdokumentasi.
- [ ] Integration testing selesai (alur preprocessing → model → recommendation → dashboard).
- [ ] Usability testing pada pengguna nyata selesai.
- [ ] Expert validation oleh praktisi OmorfoShop selesai.
- [ ] Bug fixing selesai berdasarkan temuan testing.
- [ ] Validation report tersedia: skor rata-rata Likert + masukan kualitatif (`outputs/reports/validation_report.pdf`).

## Implementasi

- Unit test di `tests/` (`pytest`) — **sudah ada 168 test** mencakup
  `src/preprocessing/`, `src/recommendation/`, dan seluruh `src/dashboard/`;
  Fase 9 tinggal merangkum hasilnya ke laporan testing (jumlah test per modul,
  semua hijau) + menambah test bila ditemukan bug.
- Integration test end-to-end dengan **model nyata** (bukan df pra-label):
  CSV mentah → inferensi IndoBERT → rule engine → render dashboard → ekspor
  CSV. Jalur kedua: URL Auto-Fetch (CDP) → analisis (sekaligus menutup
  verifikasi manual fetch Fase 8; uji skenario multi-URL + simpanan sesi).
- Lakukan sesi usability testing dengan 1–2 pengguna non-teknis (skenario di
  atas, termasuk fitur pasca-gate).
- Buat kuesioner expert validation dan lakukan dengan seller OmorfoShop.
  *(Opsional, bila pembimbing setuju)*: tambahkan item kuesioner untuk fitur
  insight baru — kebermanfaatan deteksi ketidaksesuaian rating–sentimen dan
  perbandingan kondisi per produk — tanpa mengubah 17 item inti yang sudah
  ditetapkan di proposal.

## Gate ke Fase Berikutnya

Lanjut ke Fase 10 hanya jika seluruh pengujian inti lulus, bug kritis sudah diperbaiki, dan validation report dari praktisi tersedia.
