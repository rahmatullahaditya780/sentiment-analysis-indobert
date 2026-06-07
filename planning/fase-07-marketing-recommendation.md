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

| Kondisi | Kriteria (Compound) | Interpretasi |
|---|---|---|
| **Excellent Performance** | Positif ≥ 50% AND Negatif ≤ 20% | Produk/layanan dikomunikasikan dengan sangat baik; kepuasan pelanggan tinggi |
| **Good Performance** | Positif 40–49% AND Negatif 20–30% | Produk dapat diterima, namun ada ruang untuk perbaikan |
| **Moderate Performance** | Positif 30–39% AND Negatif 30–40% | Keseimbangan antara kepuasan dan ketidakpuasan pelanggan |
| **Poor Performance** | Positif < 30% AND Negatif > 40% | Produk/layanan menghadapi masalah signifikan; perlu perhatian urgent |
| **Mixed/Unstable** | Netral > 35% ATAU Trend berubah signifikan | Persepsi pelanggan tidak konsisten; perlu monitoring lebih lanjut |

## Rule-Based Mapping ke Strategi Pemasaran

| Kondisi | Strategi yang Direkomendasikan |
|---|---|
| Excellent Performance | Pertahankan kualitas & branding; tingkatkan loyalitas; manfaatkan ulasan positif sebagai social proof; pertimbangkan program referral. |
| Good Performance | Identifikasi aspek yang masih kurang dari ulasan negatif; perbaiki titik kelemahan spesifik; tingkatkan komunikasi keunggulan produk. |
| Moderate Performance | Analisis aspek (word cloud negatif) untuk identifikasi masalah utama; tingkatkan kualitas produk dan layanan; susun kampanye komunikasi yang lebih transparan. |
| Poor Performance | Prioritaskan peningkatan kualitas produk dan layanan secara urgent; evaluasi pricing dan packaging; pertimbangkan kampanye permintaan maaf publik. |
| Mixed/Unstable | Tingkatkan edukasi produk; perkuat deskripsi produk agar ekspektasi lebih terarah; lakukan monitoring sentimen secara berkala. |

## Deliverables Checkpoint 7

- [ ] Rule engine dengan 5 kategori kondisi pemasaran selesai.
- [ ] Threshold compound conditions (positif AND negatif) terimplementasi.
- [ ] Kategori Mixed/Unstable Performance terimplementasi (netral > 35% ATAU trend berubah).
- [ ] Recommendation engine selesai.
- [ ] Business insight dan marketing strategy tersedia untuk setiap kondisi.
- [ ] Trend analysis berjalan jika data punya kolom `date_review`.

## Implementasi Kode

- `src/recommendation/rule_engine.py` — `MarketingConditionClassifier` (evaluasi 5 kondisi compound)
- `src/recommendation/strategy_mapper.py` — Mapping kondisi → daftar strategi pemasaran
- `src/recommendation/trend_analyzer.py` — Analisis tren sentimen berbasis `date_review`
- Input: hasil batch prediction (DataFrame dengan `predicted_label`, opsional `date_review`)
- Output: kondisi pemasaran, strategi, business insight (string/dict)

## Gate ke Fase Berikutnya

Lanjut ke Fase 8 hanya jika rule engine dengan 5 kondisi compound sudah stabil dan diuji pada berbagai skenario distribusi sentimen.
