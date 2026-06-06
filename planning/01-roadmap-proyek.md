# Roadmap Proyek Sistem Analisis Sentimen Ulasan Produk E-Commerce

## Tujuan
Dokumen ini menjadi acuan utama pengembangan sistem berdasarkan TRD, mulai dari inisialisasi sampai dokumentasi akhir.

## Aturan Gate Antar Fase
Setiap fase hanya boleh dilanjutkan jika checklist fase saat ini sudah terpenuhi seluruhnya.

### Format Status
- `Belum mulai`
- `Berjalan`
- `Siap dicek`
- `Selesai`

## Daftar Fase
1. Fase 1 - Project Initialization & Environment Setup
2. Fase 2 - Data Collection & Data Management
3. Fase 3 - Data Preprocessing
4. Fase 4 - Model Training & Fine-Tuning
5. Fase 5 - Model Evaluation
6. Fase 6 - Sentiment Inference Engine
7. Fase 7 - Rule-Based Marketing Recommendation
8. Fase 8 - Dashboard Development
9. Fase 9 - Testing & Validation
10. Fase 10 - Deployment & Documentation

## Checklist Gate Global
- [x] Struktur folder project sudah modular.
- [x] Environment Python aktif dan terdokumentasi.
- [ ] Data flow antar fase terdokumentasi.
- [ ] Output tiap fase tersimpan sebagai artefak.
- [ ] Setiap fase punya checklist selesai sebelum pindah.
- [ ] File catatan revisi terpisah dan selalu diperbarui.

## Urutan Kerja
### Fase 1
- Siapkan struktur project, virtual environment, dan konfigurasi dasar.
- Output: struktur folder, requirements, konfigurasi awal.

### Fase 2
- Kumpulkan dan kelola data ulasan.
- Output: dataset mentah yang siap diproses.

### Fase 3
- Bersihkan dan normalisasi data.
- Output: dataset hasil preprocessing.

### Fase 4
- Latih dan fine-tune IndoBERT.
- Output: model terlatih dan checkpoint terbaik.

### Fase 5
- Evaluasi performa model.
- Output: metrik evaluasi dan analisis hasil.

### Fase 6
- Bangun mesin inferensi sentimen.
- Output: endpoint atau modul prediksi sentimen.

### Fase 7
- Tambahkan rekomendasi pemasaran berbasis aturan.
- Output: modul rekomendasi yang terhubung ke hasil sentimen.

### Fase 8
- Kembangkan dashboard Streamlit.
- Output: antarmuka visual untuk monitoring dan analisis.

### Fase 9
- Lakukan testing dan validasi menyeluruh.
- Output: laporan uji dan perbaikan akhir.

### Fase 10
- Siapkan deployment dan dokumentasi.
- Output: panduan penggunaan, deployment notes, dan dokumentasi final.

## Cara Memakai
1. Kerjakan file fase secara berurutan.
2. Tandai checklist sebelum pindah ke fase berikutnya.
3. Catat revisi non-fase di file khusus catatan revisi.