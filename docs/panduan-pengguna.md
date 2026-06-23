# Panduan Pengguna Sentara

Panduan langkah demi langkah memakai dashboard **Sentara** untuk menganalisis
sentimen ulasan produk dan membaca rekomendasi pemasaran. Ditujukan untuk
pengguna **non-teknis** (mis. pemilik toko, tim pemasaran).

> Tidak perlu paham pemrograman. Cukup ikuti langkah-langkah di bawah.

---

## 1. Membuka Dashboard

- **Versi online (cloud):** buka tautan dashboard yang dibagikan (Streamlit Cloud
  / HuggingFace Spaces). Tidak perlu instalasi.
- **Versi lokal (di komputer sendiri):** jalankan `streamlit run app.py`, lalu
  buka `http://localhost:8501` di peramban.

Saat pertama dibuka, Anda berada di halaman **Beranda**. Menu lain (Daftar Ulasan,
Kata yang Sering Muncul, Saran Pemasaran, dst.) baru muncul **setelah** analisis
pertama dijalankan — ini disengaja agar tampilan tidak membingungkan di awal.

---

## 2. Memasukkan Data Ulasan

Di **Beranda** ada dua cara memasukkan ulasan:

### Cara A — Unggah file CSV (tersedia di semua versi)

1. Siapkan file `.csv` berisi ulasan. Kolom **wajib**: `review_text` (isi ulasan).
   Kolom **opsional** yang memperkaya analisis: `rating`, `product_name`,
   `product_category`, `date_review`, `review_id`.
2. Gunakan berkas contoh
   [`data/implementation/omorfo_reviews_TEMPLATE.csv`](../data/implementation/omorfo_reviews_TEMPLATE.csv)
   sebagai acuan format.
3. Klik area unggah, pilih file CSV Anda, lalu tekan tombol analisis.

> **Tip:** bila CSV sudah memuat kolom `predicted_label` & `confidence_score`
> (mis. hasil ekspor sebelumnya), sistem melewati proses prediksi dan langsung
> menampilkan hasil — jauh lebih cepat.

### Cara B — URL Auto-Fetch (hanya versi lokal/desktop)

1. Pindah ke tab **URL Auto-Fetch**.
2. Tempel **URL produk Shopee** (mis. `https://shopee.co.id/...-i.<shopid>.<itemid>`).
3. Ikuti proses login browser bila diminta, lalu jalankan pengambilan. Ulasan
   diambil otomatis dengan jeda agar aman.

> Tab ini **tidak muncul di versi online** karena lingkungan cloud tidak bisa
> membuka sesi browser ber-login. Di cloud, gunakan **Cara A (CSV)**.

---

## 3. Menjalankan Analisis

Setelah data masuk, tekan tombol analisis. Sistem akan:

1. Membersihkan teks ulasan.
2. Menilai sentimen tiap ulasan dengan model IndoBERT (**Positif / Negatif / Netral**).
3. Menghitung distribusi & menyusun rekomendasi pemasaran.

Proses bisa memakan beberapa detik hingga menit tergantung jumlah ulasan (model
berjalan di CPU). Tunggu hingga indikator selesai.

---

## 4. Membaca Hasil

Setelah analisis selesai, menu baru muncul di sisi kiri:

### Beranda (ringkasan)
- **Verdict / kondisi pemasaran** ditampilkan menonjol (lihat tabel di bawah).
- Ringkasan jumlah ulasan dan proporsi tiap sentimen.
- Tombol **Tambah data** (gabungkan data baru) dan **Reset** (mulai ulang).

### Daftar Ulasan
Tabel tiap ulasan beserta label sentimen dan **skor keyakinan** (0–1; makin tinggi
makin yakin model). Bisa difilter per sentimen / produk.

### Kata yang Sering Muncul
*Word cloud* — kata yang paling sering muncul di ulasan. Membantu menebak tema
pujian/keluhan yang dominan.

### Saran Pemasaran
*Playbook* rekomendasi sesuai kondisi: **judul strategi + langkah konkret +
contoh penerapan**. Inilah inti tindak lanjut bisnis.

---

## 5. Memahami 4 Kondisi Pemasaran

| Kondisi | Artinya | Kriteria |
|---|---|---|
| **Sangat Baik** | Pelanggan sangat puas; jaga momentum | Positif ≥ 50% DAN Negatif ≤ 20% |
| **Baik** | Cukup positif; ada ruang perbaikan kecil | Positif 40–49% DAN Negatif 20–30% |
| **Perlu Perbaikan** | Banyak keluhan; perlu tindakan | Positif < 30% DAN Negatif > 40% |
| **Beragam / Tidak Stabil** | Pendapat campur / berubah-ubah | Netral > 35% ATAU tren berubah signifikan |

Penjelasan tambahan tiap istilah tersedia di menu **Tentang & Bantuan** (glosarium).

---

## 6. Mengekspor & Menyetel

- **Ekspor:** unduh hasil prediksi sebagai CSV untuk dianalisis lebih lanjut atau
  diunggah ulang nanti.
- **Pengaturan:** filter data (per produk/sentimen/tanggal) — hasil & rekomendasi
  dihitung ulang otomatis mengikuti filter, tanpa menjalankan model lagi.

---

## 7. Bila Terjadi Masalah

| Gejala | Solusi |
|---|---|
| "Kolom teks tidak ditemukan" | Pastikan ada kolom `review_text` di CSV; pakai berkas TEMPLATE sebagai acuan. |
| Analisis lama / berat | Wajar untuk ribuan ulasan di CPU. Kurangi jumlah baris atau tunggu. |
| Tab URL Auto-Fetch tidak ada | Anda memakai versi online — gunakan unggah CSV. |
| Hasil fetch gagal (versi lokal) | Skema Shopee bisa berubah; gunakan jalur CSV sebagai cadangan. |

Untuk istilah teknis & detail metrik model, lihat menu **Tentang & Bantuan** di
dashboard atau [README.md](../README.md).

---

> 📷 *Catatan dokumentasi:* untuk versi cetak/skripsi, sisipkan tangkapan layar
> tiap langkah (Beranda, unggah CSV, hasil verdict, Saran Pemasaran). Ambil
> screenshot saat menjalankan `streamlit run app.py` dengan data contoh.
