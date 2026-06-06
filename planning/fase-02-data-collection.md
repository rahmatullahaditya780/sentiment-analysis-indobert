# Fase 2 - Data Collection & Data Management

## Tujuan
Mengumpulkan, menyusun, dan mengelola data ulasan produk e-commerce agar siap masuk preprocessing.

## Deliverables
- Dataset mentah dari sumber yang disepakati.
- Skema penyimpanan data.
- Catatan sumber data dan izin penggunaan.
- Struktur data management yang konsisten.
- Utilitas inisialisasi data collection dan validasi kolom dasar.
- Manifest sumber data untuk setiap dataset mentah.

## Checklist Selesai Fase
- [ ] Sumber data sudah ditetapkan.
- [ ] Data mentah berhasil dikumpulkan.
- [ ] Struktur penyimpanan data sudah jelas.
- [ ] Metadata sumber data terdokumentasi.
- [ ] Dataset siap diproses ke fase berikutnya.
- [ ] Struktur folder phase 2 dapat diinisialisasi ulang tanpa error.
- [ ] Kolom wajib dataset dapat divalidasi sebelum preprocessing.

## Implementasi Awal
- Gunakan `scripts/init_phase2_data.py` untuk membuat struktur folder standar phase 2.
- Simpan metadata sumber data di `data/raw/source_manifest.yaml`.
- Validasi kelengkapan kolom penting dengan utilitas `src/data_management.py` sebelum preprocessing.

## Struktur Data Management
- `data/raw/` untuk dataset mentah dan manifest sumber data.
- `data/external/` untuk data pendukung dari luar sumber utama.
- `data/interim/` untuk hasil antara setelah pembersihan awal.
- `data/processed/` untuk data final yang siap dipakai pelatihan.

## Metadata Minimum
- Nama sumber.
- Tipe sumber.
- URL atau referensi sumber.
- Lisensi atau izin penggunaan.
- Tanggal pengambilan data.
- Versi dataset.
- Catatan tambahan bila ada batasan atau anomali.

## Catatan Implementasi
- Fase ini sengaja dibuat generik karena sumber data final belum ditetapkan di dokumen.
- Jika sumber sudah pasti, isi manifest dengan nilai nyata dan gunakan validasi kolom sebelum data dipindah ke fase 3.

## Gate ke Fase Berikutnya
Lanjut hanya jika dataset mentah siap dan dokumentasi sumber data lengkap.