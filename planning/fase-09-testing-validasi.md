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
| Unit Testing | Setiap fungsi individual (preprocessing, inference, rule-engine) | `pytest` |
| Integration Testing | Aliran data antar module (preprocessing → model → recommendation → dashboard) | End-to-end workflow test |
| UI Testing / Usability | Kemudahan penggunaan dashboard oleh pengguna non-teknis | Observasi langsung pada pengguna nyata |
| Model Testing | Akurasi model pada test set dan dataset OmorfoShop | Metrik evaluasi (accuracy, F1 macro) |

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

- Tulis unit test di `tests/` menggunakan `pytest`.
- Test coverage minimal untuk modul: `src/preprocessing/`, `src/modeling/inference.py`, `src/recommendation/rule_engine.py`.
- Lakukan sesi usability testing dengan 1–2 pengguna non-teknis menggunakan dashboard.
- Buat kuesioner expert validation dan lakukan dengan seller OmorfoShop.

## Gate ke Fase Berikutnya

Lanjut ke Fase 10 hanya jika seluruh pengujian inti lulus, bug kritis sudah diperbaiki, dan validation report dari praktisi tersedia.
