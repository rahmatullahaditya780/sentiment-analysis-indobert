# Lembar Skenario Tugas — Usability Testing Fase 9 (FR-9.3)

**Sistem:** Sentara — Dashboard Analisis Sentimen Ulasan E-Commerce (IndoBERT)
**Metode:** Task-based testing + think-aloud, 1 peserta per sesi (~30–45 menit).
**Sasaran peserta:** pengguna **non-teknis** (staf/admin toko atau awam jualan online).

> Lembar ini **dibacakan/diberikan ke peserta**. Catatan ber-ikon 🛈 adalah
> petunjuk **untuk fasilitator** (jangan dibacakan). Pencatatan hasil dilakukan di
> `phase9_usability_observation_sheet.md`.

---

## Persiapan fasilitator (sebelum peserta datang)

- [ ] `streamlit run app.py` aktif, semua halaman terbuka, model ter-load.
- [ ] File CSV contoh siap: `data/implementation/omorfo_reviews.csv`
      (atau subset ~100 baris agar inferensi cepat).
- [ ] Tahu lebih dulu: 1 kata yang pasti ada di ulasan (mis. **"pengiriman"**),
      1 nama **kategori produk** yang tersedia di data, dan 1 **bulan** yang ada.
- [ ] Lembar observasi + alat tulis/timer siap. (Opsional: rekam layar — izin dulu.)
- [ ] *(Untuk T10)* siapkan sesi login Shopee di Chrome bila ingin menguji fetch.

---

## Naskah pembuka (dibacakan ke peserta)

> "Terima kasih sudah membantu. Hari ini kita menguji **sistemnya**, bukan menguji
> Anda — jadi tidak ada jawaban benar atau salah. Saya akan memberi beberapa tugas;
> kerjakan seperti biasa. Tolong **bersuara** menyampaikan apa yang Anda pikirkan —
> kalau bingung, katakan bingungnya di mana. Saya tidak akan banyak membantu karena
> justru ingin tahu apakah sistemnya bisa dipakai sendiri. Boleh kita mulai?"

---

## Daftar Tugas

> 🛈 Untuk tiap tugas catat di lembar observasi: **status** (Berhasil sendiri /
> Berhasil dengan bantuan / Gagal), **waktu**, **jumlah error/salah-klik**, dan
> **kutipan** komentar peserta. Mulai timer saat selesai membaca tugas.

### T1 — Memasukkan data & menjalankan analisis
**Dibacakan:** "Di depan Anda ada file berisi ulasan pelanggan. Tolong masukkan
file itu ke sistem, lalu jalankan analisisnya."
> 🛈 Menguji: Upload CSV → tombol Analisis (alur dasar). **Sukses:** hasil analisis
> muncul (mis. halaman Dashboard terisi). Halaman: *Input & Pengambilan Data*.

### T2 — Membaca hasil utama
**Dibacakan:** "Dari hasil tadi, kira-kira berapa persen pelanggan yang merasa
puas? Dan produk mana yang paling banyak dikeluhkan?"
> 🛈 Menguji: keterbacaan Dashboard + ringkasan per-produk. **Sukses:** peserta
> menyebut angka % positif & mengidentifikasi produk dengan negatif tertinggi.

### T3 — Mencari kata & berpindah halaman
**Dibacakan:** "Coba temukan ulasan yang menyebut kata **'pengiriman'**. Lalu
lihat halaman berikutnya dari daftar ulasan itu."
> 🛈 Menguji: pencarian kata + paginasi (skenario fase-09 #1). Halaman: *Detail
> Ulasan*. **Sukses:** hasil tersaring ke kata tsb + pindah ke halaman 2.

### T4 — Memahami ketidaksesuaian rating–sentimen
**Dibacakan:** "Coba temukan ulasan yang diberi **bintang 5 tetapi isinya
sebenarnya keluhan**. Menurut Anda, apa artinya itu?"
> 🛈 Menguji: fitur mismatch (skenario #2) — apakah peserta **paham maknanya**.
> Halaman: *Dashboard* (kartu mismatch) / *Detail* (toggle). **Sukses:** peserta
> menemukan contoh & menjelaskan maknanya dengan kata sendiri.

### T5 — Membaca kata dominan
**Dibacakan:** "Kata apa yang paling sering muncul di ulasan yang **negatif**?"
> 🛈 Menguji: word cloud / kata kunci per kelas (skenario #3). Halaman:
> *Visualisasi & Word Cloud*. **Sukses:** peserta menyebut kata dari kelas negatif.

### T6 — Membaca rekomendasi & dasarnya
**Dibacakan:** "Strategi pemasaran apa yang **disarankan** sistem? Dan menurut
sistem, apa **dasar** rekomendasi itu?"
> 🛈 Menguji: panel Rekomendasi + bukti ulasan (skenario #4). Halaman:
> *Rekomendasi Strategi*. **Sukses:** peserta menyebut ≥1 strategi & dasar/kondisinya.

### T7 — Menyaring data
**Dibacakan:** "Sekarang tampilkan **hanya** ulasan untuk kategori
**[sebutkan 1 kategori yang ada]**, untuk bulan **[sebutkan 1 bulan]**."
> 🛈 Menguji: filter global + badge "X dari Y" (skenario #5). Halaman:
> *Pengaturan*. **Sukses:** filter diterapkan & peserta sadar jumlah ulasan berubah.

### T8 — Mengunduh hasil
**Dibacakan:** "Tolong unduh/simpan hasil analisis ini ke sebuah file."
> 🛈 Menguji: ekspor CSV. Halaman: *Ekspor Laporan*. **Sukses:** file
> `sentara_hasil_analisis.csv` terunduh. (Catatan: PDF/PNG memang belum ada.)

### T9 — Mencari bantuan saat buntu
**Dibacakan:** "Bayangkan sistem tidak menampilkan data atau Anda bingung. Di mana
Anda akan mencari **petunjuk/bantuan**?"
> 🛈 Menguji: empty state & Troubleshooting (skenario #7). Halaman: *Tentang &
> Bantuan*. **Sukses:** peserta menemukan seksi Troubleshooting / panduan.

### T10 — *(Lokal/desktop saja, opsional)* Ambil ulasan dari URL
**Dibacakan:** "Coba ambil ulasan langsung dari **dua** link produk Shopee ini
sekaligus."
> 🛈 Menguji: multi-URL auto-fetch + simpanan sesi (skenario #6). Halaman: *Input*
> tab URL Auto-Fetch. **Bagian login/captcha boleh dibantu fasilitator**; yang
> dinilai adalah alur menambah URL, kuota dibagi rata, & hasil gabungan.
> Lewati tugas ini bila sesi diuji di lingkungan cloud.

---

## Wawancara penutup (dibacakan, ~5 menit)

1. "Bagian mana yang menurut Anda **paling membingungkan**?"
2. "Bagian mana yang **paling membantu**?"
3. "Kalau ada **satu hal** yang bisa diubah agar lebih mudah, apa itu?"
4. "Apakah Anda merasa bisa memakai sistem ini **tanpa pendamping**?"

> Setelah ini, minta peserta mengisi **Kuesioner SUS**
> (`phase9_usability_sus_questionnaire.md`).
