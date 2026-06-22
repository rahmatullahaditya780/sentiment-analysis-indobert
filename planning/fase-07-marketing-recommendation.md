# Fase 7 — Rule-Based Marketing Recommendation (Checkpoint 7)

## Tujuan
Mengubah hasil analisis sentimen menjadi rekomendasi strategi pemasaran yang transparan dan dapat dipertanggungjawabkan melalui mekanisme rule-based mapping.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-7.1 | Sistem harus menghitung distribusi sentimen (persentase Positif, Negatif, Netral) dari hasil prediksi. |
| FR-7.2 | Sistem harus menentukan kondisi pemasaran berdasarkan threshold distribusi sentimen (5 kategori). |
| FR-7.3 | Sistem harus menghasilkan rekomendasi strategi pemasaran spesifik untuk setiap kondisi. |
| FR-7.4 | Sistem harus menampilkan business insight berupa interpretasi distribusi sentimen. |
| FR-7.5 | Sistem harus mendukung trend analysis jika data memiliki timestamp (`date_review`). |

## Threshold & Kondisi Pemasaran (5 Kondisi Compound)

> Menggunakan **kriteria gabungan** (positif AND negatif) — bukan hanya persentase positif saja.

> **Revisi 2026-06-23 (pasca-validasi praktisi):** kondisi **"Moderate" dihapus**
> (5→4) karena dinilai terlalu rumit; label diubah ke Bahasa Indonesia. Threshold
> kondisi lain TIDAK diubah — band Moderate lama jatuh ke "Beragam / Tidak Stabil".

| Kondisi (label) | Kriteria (Compound) | Interpretasi |
|---|---|---|
| **Sangat Baik** | Positif ≥ 50% DAN Negatif ≤ 20% | Produk/layanan dikomunikasikan dengan sangat baik; kepuasan pelanggan tinggi |
| **Baik** | Positif 40–49% DAN Negatif 20–30% | Produk dapat diterima, namun ada ruang untuk perbaikan |
| **Perlu Perbaikan** | Positif < 30% DAN Negatif > 40% | Produk/layanan menghadapi masalah signifikan; perlu perhatian urgent |
| **Beragam / Tidak Stabil** | Netral > 35% ATAU Trend berubah signifikan (atau di luar tier mana pun) | Persepsi pelanggan tidak konsisten; perlu monitoring lebih lanjut |

## Rule-Based Mapping ke Strategi Pemasaran

> **Peningkatan pasca-gate (playbook terhubung-fitur).** Strategi tidak lagi
> berupa satu kalimat samar, melainkan *playbook* terstruktur per kondisi:
> **judul aksi → langkah konkret → contoh penerapan (e-commerce umum) → fitur
> Sentara pendukung**. Tujuannya agar pelaku usaha tahu persis cara menjalankan
> tiap strategi memakai dashboard. Sumber kebenaran tunggal:
> `STRATEGY_PLAYBOOK` di `src/recommendation/config.py`; `STRATEGY_MAP` (daftar
> judul) diturunkan otomatis darinya agar kontrak lama (list[str], JSON) tetap utuh.

| Kondisi | Fokus & contoh strategi (judul) | Fitur Sentara yang dirujuk |
|---|---|---|
| Excellent Performance | Social proof dari ulasan positif; loyalitas produk unggulan; referral berbasis keunggulan; pemantauan dini. | Bukti Ulasan Representatif, Kondisi per Produk, Kata Kunci/Word Cloud, auto-fetch + peringatan tren. |
| Good Performance | Bedah keluhan spesifik; perbaiki lalu komunikasikan & verifikasi; tonjolkan keunggulan. | Bukti Ulasan (negatif), Word Cloud negatif, Detail Ulasan, fetch ulang. |
| Moderate Performance | Akar masalah via analisis kata; perbaikan terukur per produk; komunikasi transparan; cek keluhan tersembunyi. | Word Cloud/Kata Kunci negatif, Kondisi per Produk + filter, mismatch rating↔sentimen. |
| Poor Performance | Triase keluhan mendesak; evaluasi harga/kualitas/kemasan; recovery terbuka; fokus/hentikan SKU terparah. | Bukti Ulasan + Word Cloud negatif, Kata Kunci negatif, Detail Ulasan, Kondisi per Produk. |
| Mixed/Unstable | Selaraskan ekspektasi via mismatch; perkuat deskripsi dari kata netral; pantau berkala; investigasi pemicu. | Mismatch rating↔sentimen, Word Cloud netral, auto-fetch + tren, Kondisi per Produk. |

Tiap baris di atas berisi 3–4 *play*; rincian langkah & contoh penuh ada di
`STRATEGY_PLAYBOOK` dan dirender sebagai **kartu yang bisa dibuka (expander)** pada
panel Rekomendasi dashboard (Fase 8).

## Deliverables Checkpoint 7

- [x] Rule engine dengan 5 kategori kondisi pemasaran selesai.
- [x] Threshold compound conditions (positif AND negatif) terimplementasi.
- [x] Kategori Mixed/Unstable Performance terimplementasi (netral > 35% ATAU trend berubah).
- [x] Recommendation engine selesai.
- [x] Business insight dan marketing strategy tersedia untuk setiap kondisi.
- [x] Trend analysis berjalan jika data punya kolom `date_review`.
- [x] **Playbook strategi terhubung-fitur** (peningkatan pasca-gate): tiap strategi = judul + langkah konkret + contoh penerapan + fitur Sentara pendukung; dirender sebagai kartu expander di dashboard.

### Hasil pada data nyata OmorfoShop (3.739 ulasan, Fase 6)

Dijalankan via `recommend(df_predictions, save=True)` atas
`outputs/reports/omorfo_predictions.csv` → output
`outputs/reports/marketing_recommendation.json`:

- **Kondisi: Excellent Performance** (Positif 88,5% ≥ 50% AND Negatif 10,6% ≤ 20%) — konsisten dengan kesimpulan Fase 6.
- **Trend shift: False** — Δ proporsi positif maks 9,9% < ambang 15% atas 37 periode bulanan layak (≥ 30 ulasan).
- Strategi: pertahankan kualitas & branding, tingkatkan loyalitas, social proof, program referral.

### Catatan kalibrasi trend analysis

Trend analyzer kini memakai guard `MIN_PERIOD_SIZE = 30`: hanya periode bulanan
dengan ≥ 30 ulasan yang ikut hitung deteksi shift. Tanpa guard ini, bulan-bulan
awal riwayat toko bersampel kecil (n=1–2) menghasilkan swing proporsi palsu
(Δ 35,7%) yang keliru memicu Mixed/Unstable. `TREND_SHIFT_THRESHOLD = 0.15` dan
`MIN_PERIOD_SIZE = 30` dapat dikalibrasi ulang di `src/recommendation/config.py`.

## Implementasi Kode

- `src/recommendation/rule_engine.py` — `MarketingConditionClassifier` (evaluasi 4 kondisi compound)
- `src/recommendation/config.py` — `MarketingPlay` + `STRATEGY_PLAYBOOK` (playbook terstruktur); `STRATEGY_MAP` diturunkan dari judul play
- `src/recommendation/strategy_mapper.py` — Mapping kondisi → playbook strategi + business insight (`MarketingRecommendation.playbook`)
- `src/recommendation/trend_analyzer.py` — Analisis tren sentimen berbasis `date_review`
- Input: hasil batch prediction (DataFrame dengan `predicted_label`, opsional `date_review`)
- Output: kondisi pemasaran, strategi (judul + langkah + contoh + fitur), business insight (string/dict)

## Gate ke Fase Berikutnya

Lanjut ke Fase 8 hanya jika rule engine dengan 4 kondisi compound sudah stabil dan diuji pada berbagai skenario distribusi sentimen.
