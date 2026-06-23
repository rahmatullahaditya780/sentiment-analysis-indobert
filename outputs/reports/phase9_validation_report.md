# Laporan Validasi Ahli (Expert Validation) — Fase 9 (FR-9.4)

> Deliverable Checkpoint 9: *"Validation report tersedia: skor rata-rata Likert +
> masukan kualitatif"* (`validation_report` — versi PDF diekspor dari dokumen ini).
> Instrumen: [`phase9_expert_validation_questionnaire.md`](phase9_expert_validation_questionnaire.md);
> data terisi: [`phase9_expert_validation_scoring_template.csv`](phase9_expert_validation_scoring_template.csv).
> Berkas angket asli ber-tanda tangan: `Validasi 1.pdf` (arsip peneliti).
> Data keluaran sistem atas ulasan toko validator: [`Forta_Beauty_predictions.csv`](Forta_Beauty_predictions.csv) (17 ulasan).

## 1. Validator

| Isian | Keterangan |
|---|---|
| Nama | Rizka Oktavia B. |
| Peran | Pemilik Toko **Forta Beauty** di Shopee |
| Pengalaman e-commerce | ± 1 tahun |
| Bidang | Produk kecantikan (relevan dengan studi kasus) |
| Tanggal | 22 Juni 2026 |

Sesuai **FR-9.4** (expert validation oleh 1–2 praktisi e-commerce / seller Shopee).
Validator adalah seller produk kecantikan di Shopee — sebanding dengan konteks
OmorfoShop sehingga representatif untuk menilai relevansi keluaran sistem.

## 2. Metode

Kuesioner terstruktur **skala Likert 1–5** (1 = Sangat Tidak Setuju … 5 = Sangat
Setuju), 13 item tertutup pada 4 aspek + penilaian keseluruhan, ditambah 4
pertanyaan terbuka.

Sebelum menilai, validator menelaah keluaran sistem atas **dua sumber data nyata**:

1. **Dataset studi kasus OmorfoShop** — 3.739 ulasan (distribusi 88,5% positif),
   beserta kondisi toko, panel rekomendasi pemasaran, dan word cloud.
2. **Ulasan tokonya sendiri — Forta Beauty** — 17 ulasan produk perawatan rambut
   (Makarizo) & wajah (Pigeon Teens) yang diklasifikasikan sistem
   (`outputs/reports/Forta_Beauty_predictions.csv`). Distribusi hasil: **15 positif /
   1 negatif / 1 netral** (88,2% / 5,9% / 5,9%). Sistem **mengenali dengan benar**
   satu keluhan kualitas (ulasan bintang-3 *"banyak yang sudah meleleh"* → negatif,
   keyakinan 0,96) dan satu ucapan terima kasih tanpa sentimen produk (→ netral,
   keyakinan 0,79).

Penelaahan pada data tokonya sendiri penting karena validator **mengenal langsung
sentimen pelanggannya**, sehingga dapat membandingkan label sistem dengan persepsi
nyata atas ulasan yang ia pahami betul. Hal ini memperkuat **validitas muka (face
validity)** penilaian — khususnya Aspek 1 (akurasi klasifikasi sentimen, item 1–3)
yang dinilai **"Sangat Layak" (4,67)** — karena penilaian itu berpijak pada data
toko sendiri sekaligus data studi kasus, bukan semata data pihak ketiga.

## 3. Skor per Item

| No | Aspek / Pernyataan | Skor |
|---|---|:-:|
| 1 | Klasifikasi sentimen sesuai persepsi | 4 |
| 2 | Distribusi sentimen realistis (produk kecantikan) | 5 |
| 3 | Word cloud / topik dominan mencerminkan ulasan | 5 |
| 4 | Aturan (threshold/kondisi) mudah dipahami | **3** |
| 5 | Pengelompokan kondisi sesuai realita lapangan | **2** |
| 6 | Penjelasan rule-based transparan | 4 |
| 7 | Rekomendasi relevan dengan kondisi toko | 5 |
| 8 | Strategi dapat diterapkan operasional | 4 |
| 9 | Strategi berpotensi menaikkan conversion/penjualan | 4 |
| 10 | Strategi realistis (tanpa sumber daya berlebih) | 3 |
| 11 | Sesuai dinamika pasar e-commerce | 5 |
| 12 | Selaras perilaku pelanggan kecantikan | 5 |
| 13 | **Keseluruhan: layak sebagai alat bantu keputusan** | 5 |

## 4. Rekapitulasi & Interpretasi

Rata-rata per aspek = total skor item ÷ jumlah item. Skor akhir = rata-rata
seluruh item (1–13).

| Aspek | Item | Rata-rata | Kategori |
|---|---|:-:|---|
| 1. Hasil Analisis Sentimen | 1–3 | **4,67** | Sangat Layak |
| 2. Rule-Based Mapping | 4–6 | **3,00** | Cukup Layak |
| 3. Rekomendasi Strategi Pemasaran | 7–10 | **4,00** | Layak |
| 4. Kesesuaian Konteks Pasar | 11–12 | **5,00** | Sangat Layak |
| Penilaian Keseluruhan | 13 | **5,00** | Sangat Layak |
| **Skor Akhir** | **1–13** | **4,15** | **Layak** |

*Pedoman interval 0,8: 1,00–1,79 Sangat Tidak Layak · 1,80–2,59 Tidak Layak ·
2,60–3,39 Cukup Layak · 3,40–4,19 **Layak** · 4,20–5,00 Sangat Layak.*

**Interpretasi:** sistem dinilai **Layak** secara keseluruhan (4,15). Aspek
terkuat: **Hasil Analisis Sentimen (4,67)** & **Kesesuaian Konteks Pasar (5,00)** —
inti nilai sistem (klasifikasi + relevansi pasar) tervalidasi kuat. **Aspek
terlemah: Rule-Based Mapping (3,00)**, ditarik turun oleh **item 5 = 2 (Tidak
Setuju)** — pengelompokan kondisi pemasaran dinilai belum sepenuhnya selaras dan
terlalu rumit.

## 5. Masukan Kualitatif (pertanyaan terbuka)

- **Strategi paling relevan:** *"Pemanfaatan ulasan positif sebagai testimoni,
  karena media sosial cukup berperan menarik pelanggan."*
- **Strategi kurang sesuai:** *"Semua strategi cukup sesuai dengan kondisi
  lapangan yang ada."* (tidak ada yang dinilai tidak sesuai).
- **Saran pengembangan:** (1) **sederhanakan bahasa & istilah** agar mudah
  dipahami; (2) setelah analisis **langsung diarahkan ke dashboard**; (3) **gabung
  input & dashboard jadi satu halaman (landing page)** agar tidak banyak berpindah.
- **Potensi monitoring berkala:** **"Iya"** — sistem dinilai dapat dipakai untuk
  pemantauan sentimen berkala.

## 6. Tindak Lanjut — temuan → perbaikan

Masukan validator **bertemu (triangulasi)** dengan temuan usability dan telah
**ditindaklanjuti** (commit `aebaf7c`, 2026-06-23):

| Temuan validator | Perbaikan yang diterapkan |
|---|---|
| Rule-Based Mapping rumit / kurang selaras (Aspek 2 = 3,00; item 5 = 2) | Kondisi **disederhanakan 5→4** (kondisi **"Moderate" dihapus**) + **label Bahasa Indonesia** (Sangat Baik/Baik/Perlu Perbaikan/Beragam–Tidak Stabil); kriteria ditampilkan dalam bahasa lugas. **Threshold tidak diubah** (validator menyatakan ambang sudah baik). |
| Sederhanakan bahasa & istilah | Sapu jargon menyeluruh + glosarium (lihat laporan usability). |
| Langsung ke dashboard setelah analisis | **Beranda adaptif** — setelah klik Mulai Analisis, halaman langsung berubah menjadi ringkasan (tanpa pindah halaman). |
| Gabung input & dashboard jadi satu halaman | **Dashboard + Input disatukan jadi "Beranda"**; grup navigasi "Menu" dihapus. |

Strategi yang dipuji validator (ulasan positif sebagai testimoni) **sudah** menjadi
salah satu playbook kondisi "Sangat Baik" pada panel Saran Pemasaran — selaras
dengan penilaian praktisi.

## 7. Kesimpulan & Catatan

- **Kesimpulan:** keluaran Sentara dinilai **Layak** (4,15) dan **dapat diterapkan**
  oleh praktisi e-commerce kecantikan, dengan kekuatan pada akurasi sentimen dan
  kesesuaian konteks pasar. Kelemahan pada kerumitan pemetaan kondisi telah
  diperbaiki melalui penyederhanaan 5→4 kondisi + label Indonesia.
- **Keterbatasan:** validasi oleh **1 praktisi** (proposal membolehkan 1–2);
  item 5 = 2 adalah satu opini subjektif. Penyederhanaan kondisi dilakukan sebagai
  respons terhadap masukan ini **tanpa mengubah ambang numerik** agar konsistensi
  metodologis Fase 7 terjaga; perbedaan ini didokumentasikan sebagai keterbatasan.
