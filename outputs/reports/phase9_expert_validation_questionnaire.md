# Kuesioner Validasi Ahli (Expert Validation) — Fase 9 (FR-9.4)

**Sistem:** Sentara — Analisis Sentimen Ulasan Produk E-Commerce berbasis IndoBERT
**Objek validasi:** Hasil analisis sentimen, pemetaan kondisi pemasaran, dan
rekomendasi strategi untuk produk OmorfoShop.
**Sasaran responden:** 1–2 praktisi e-commerce / seller OmorfoShop.

> Instrumen ini adalah **input** Fase 9. Hasil pengisian direkap ke
> `outputs/reports/phase9_expert_validation_scoring_template.csv` lalu dirangkum
> menjadi deliverable `outputs/reports/validation_report.pdf` (skor rata-rata
> Likert + masukan kualitatif).

---

## A. Identitas Validator

| Isian | Jawaban |
|---|---|
| Nama | ……………………………………… |
| Peran / Jabatan | ……………………………………… |
| Pengalaman di e-commerce (tahun) | ……………………………………… |
| Toko / unit terkait | ……………………………………… |
| Tanggal pengisian | ……………………………………… |

---

## B. Bahan yang Dinilai (dilihat sebelum mengisi)

Sebelum mengisi, validator dipersilakan menelaah keluaran sistem berikut
(lewat dashboard `streamlit run app.py` atau tangkapan layar yang disediakan):

1. **Distribusi sentimen nyata** dari **3.739 ulasan** 5 produk terlaris OmorfoShop:
   - Positif **88,5%** (3.310) · Negatif **10,6%** (398) · Netral **0,8%** (31).
2. **Kondisi pemasaran** hasil rule engine atas distribusi tersebut:
   **Excellent Performance** (Positif ≥ 50% DAN Negatif ≤ 20%).
3. **Panel rekomendasi strategi** yang menyertai kondisi tersebut.
4. **Word cloud** kata kunci per kelas sentimen (positif/negatif/netral).
5. **Insight tambahan** (opsional dinilai di Bagian E): deteksi ketidaksesuaian
   rating–sentimen & perbandingan kondisi antar produk.

---

## C. Penilaian Skala Likert (1–5)

Beri tanda pada kolom skor yang sesuai untuk tiap pernyataan.

**Skala:** 1 = Sangat Tidak Setuju · 2 = Tidak Setuju · 3 = Netral ·
4 = Setuju · 5 = Sangat Setuju.

### Aspek 1 — Hasil Analisis Sentimen (3 item)

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 1 | Klasifikasi sentimen (positif/negatif/netral) yang dihasilkan sistem **sesuai dengan makna ulasan** pelanggan yang sebenarnya. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 2 | Distribusi sentimen yang ditampilkan (mayoritas positif) **realistis** dan mencerminkan kondisi nyata ulasan produk OmorfoShop. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 3 | Kata-kata pada **word cloud** per kelas sentimen **relevan** dan menggambarkan isi ulasan pelanggan. | ☐ | ☐ | ☐ | ☐ | ☐ |

### Aspek 2 — Rule-Based Mapping (3 item)

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 4 | Ambang batas (threshold) yang memetakan distribusi sentimen ke kondisi pemasaran **mudah dipahami**. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 5 | Lima kondisi pemasaran (Excellent/Good/Moderate/Poor/Mixed) **sesuai dengan realita** performa produk. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 6 | Dasar/alasan sistem menentukan suatu kondisi **transparan** dan dapat ditelusuri. | ☐ | ☐ | ☐ | ☐ | ☐ |

### Aspek 3 — Rekomendasi Strategi Pemasaran (4 item)

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 7 | Rekomendasi strategi pemasaran yang diberikan **relevan** dengan kondisi produk. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 8 | Strategi yang direkomendasikan **dapat diimplementasikan** pada operasional toko. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 9 | Strategi yang direkomendasikan **berpotensi memberi dampak** positif bagi penjualan/citra produk. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 10 | Strategi yang direkomendasikan **realistis dari sisi sumber daya** (biaya, waktu, tenaga). | ☐ | ☐ | ☐ | ☐ | ☐ |

### Aspek 4 — Kesesuaian Konteks Pasar (2 item)

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 11 | Keluaran sistem **sesuai dengan dinamika pasar e-commerce** (Shopee) saat ini. | ☐ | ☐ | ☐ | ☐ | ☐ |
| 12 | Hasil analisis **selaras dengan perilaku pelanggan produk kecantikan**. | ☐ | ☐ | ☐ | ☐ | ☐ |

### Penilaian Keseluruhan (1 item)

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| 13 | Secara keseluruhan, sistem ini **layak digunakan** sebagai alat bantu pengambilan keputusan pemasaran berbasis ulasan pelanggan. | ☐ | ☐ | ☐ | ☐ | ☐ |

> ⚠️ **Catatan penyusun — verifikasi vs proposal.** Tabel rincian di
> `planning/fase-09-testing-validasi.md` menjumlah **12 item Likert** (Aspek 1–4)
> + 4 pertanyaan terbuka = 16, sedangkan catatan implementasi menyebut
> **"17 item inti"**. Item **No. 13 (Penilaian Keseluruhan)** ditambahkan sebagai
> rekonstruksi agar genap 17 (13 Likert + 4 terbuka). **Mohon cocokkan dengan
> kuesioner di proposal Anda**: jika item ke-17 di proposal berbeda, ganti
> No. 13 ini dengan item yang sesuai.

---

## D. Pertanyaan Terbuka (4 pertanyaan)

**14. Strategi paling relevan.** Dari rekomendasi yang diberikan, strategi mana
yang menurut Anda paling relevan/berguna? Mengapa?

> ………………………………………………………………………………………………………………………

**15. Yang kurang sesuai.** Adakah hasil analisis atau rekomendasi yang menurut
Anda kurang sesuai dengan realita lapangan? Jelaskan.

> ………………………………………………………………………………………………………………………

**16. Saran pengembangan.** Apa saran Anda untuk pengembangan sistem ke depan?

> ………………………………………………………………………………………………………………………

**17. Potensi monitoring berkala.** Apakah sistem ini berpotensi dipakai untuk
memantau sentimen pelanggan secara berkala? Bagaimana idealnya menurut Anda?

> ………………………………………………………………………………………………………………………

---

## E. Item Tambahan — Fitur Insight (OPSIONAL, di luar 17 item inti)

> Hanya diisi **bila pembimbing menyetujui** penambahan. TIDAK mengubah/menggeser
> 17 item inti di atas. Menilai fitur pasca-gate (Fase 8.5).

| No | Pernyataan | 1 | 2 | 3 | 4 | 5 |
|---|---|:-:|:-:|:-:|:-:|:-:|
| O1 | Deteksi **ketidaksesuaian rating–sentimen** (mis. bintang 5 tetapi teks bernada negatif) memberi nilai tambah dalam memahami ulasan. | ☐ | ☐ | ☐ | ☐ | ☐ |
| O2 | **Perbandingan kondisi pemasaran antar produk** membantu memprioritaskan tindakan per produk. | ☐ | ☐ | ☐ | ☐ | ☐ |

---

## F. Rekap & Interpretasi Skor (diisi penyusun)

Rata-rata per aspek = total skor item dalam aspek ÷ jumlah item.
Skor akhir = rata-rata seluruh item Likert (No. 1–13).

| Aspek | Item | Rata-rata (V1) | Rata-rata (V2) | Rata-rata Gabungan |
|---|---|:-:|:-:|:-:|
| 1. Hasil Analisis Sentimen | 1–3 | … | … | … |
| 2. Rule-Based Mapping | 4–6 | … | … | … |
| 3. Rekomendasi Strategi | 7–10 | … | … | … |
| 4. Kesesuaian Konteks Pasar | 11–12 | … | … | … |
| Penilaian Keseluruhan | 13 | … | … | … |
| **Skor Akhir** | **1–13** | **…** | **…** | **…** |

**Pedoman interpretasi (interval 0,8 pada skala 1–5):**

| Rentang skor | Kategori |
|---|---|
| 1,00 – 1,79 | Sangat Tidak Layak |
| 1,80 – 2,59 | Tidak Layak |
| 2,60 – 3,39 | Cukup Layak |
| 3,40 – 4,19 | Layak |
| 4,20 – 5,00 | Sangat Layak |

---

*Tanda tangan validator:* ……………………………  *Tanggal:* ……………………
