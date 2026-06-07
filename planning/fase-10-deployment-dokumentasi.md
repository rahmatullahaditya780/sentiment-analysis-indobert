# Fase 10 — Deployment & Documentation (Checkpoint 10)

## Tujuan
Mempublikasikan sistem ke lingkungan online dan menyelesaikan seluruh dokumentasi penelitian.

## Functional Requirements
| ID | Requirement |
|---|---|
| FR-10.1 | Sistem harus dapat di-deploy ke Streamlit Cloud (atau HuggingFace Spaces sebagai alternatif jika melampaui batas memori). |
| FR-10.2 | Sistem harus memiliki dokumentasi penggunaan dashboard yang dapat dipahami pengguna non-teknis. |
| FR-10.3 | Sistem harus memiliki README project yang lengkap (cara instalasi, cara penggunaan, struktur project). |
| FR-10.4 | Sistem harus memiliki mekanisme logging untuk mendeteksi error dan memantau performa. |
| FR-10.5 | Repository GitHub harus bersih, terstruktur, dan memiliki `.gitignore` yang sesuai. |

## Deployment Requirements

> **Catatan:** Streamlit Cloud versi gratis memiliki batas memori ~1GB. Model IndoBERT (~500MB) berpotensi melampaui batas ini. Siapkan **HuggingFace Spaces** sebagai alternatif.

| Komponen | Platform | Keterangan |
|---|---|---|
| Dashboard Web App | Streamlit Cloud | Deployment utama; alternatif: HuggingFace Spaces jika memori kurang |
| Model Storage | HuggingFace Hub atau Google Drive | Simpan model weight terpisah; load saat startup dashboard |
| Repository Kode | GitHub | Repository publik dengan dokumentasi lengkap |
| Dataset Publik | Tetap di sumber asli (IndoNLU, Kaggle) | Tidak perlu re-upload; gunakan link ke sumber asli |

## Documentation Requirements

| Dokumen | Isi | Format |
|---|---|---|
| `README.md` | Cara instalasi, cara menjalankan, struktur project, daftar dependency, cara interpretasi dashboard | Markdown (GitHub) |
| API Docs | Struktur module, fungsi utama, parameter input/output | Docstring Python / Markdown |
| User Guide | Panduan penggunaan dashboard step-by-step untuk pengguna non-teknis | PDF atau Markdown |
| Hyperparameter Log | Tabel eksperimen focused random search dan justifikasi konfigurasi terpilih | CSV + Markdown |
| Evaluation Report | Hasil evaluasi model (accuracy, F1, confusion matrix, learning curve, cross-validation) | JSON + PDF |
| Validation Report | Hasil expert validation (skor kuesioner, masukan kualitatif, penyempurnaan yang dilakukan) | PDF |

## Identifikasi Risiko & Mitigasi

| No | Risiko | Probabilitas | Mitigasi |
|---|---|---|---|
| R-01 | Keterbatasan GPU lokal (AMD Radeon Vega 7, bukan NVIDIA) | Tinggi | Gunakan Google Colab untuk training |
| R-02 | Streamlit Cloud melampaui batas memori ~1GB saat memuat IndoBERT (~500MB) | Tinggi | Gunakan HuggingFace Spaces; pertimbangkan model quantization |
| R-03 | Akses Open Platform API terkendala (kredensial, token, otorisasi toko) | Rendah–Sedang | Daftarkan app sejak awal; implementasikan auto-refresh token + retry + fallback CSV |
| R-04 | Class imbalance ekstrem pada unified dataset (selisih > 25%) | Sedang | Stratified split + class weight + data augmentation (back-translation) |
| R-05 | Dataset SmSA atau Kaggle tidak tersedia | Rendah | Download dan simpan snapshot lokal di awal; dokumentasikan versi |
| R-06 | Performa model tidak mencapai target (F1 macro < 85%) | Sedang | Lakukan focused random search lebih luas; periksa kualitas label dataset |
| R-07 | Inferensi IndoBERT lambat (> 5 detik) di CPU | Sedang | `st.session_state` untuk cache model; batasi batch size inference; tambahkan loading spinner |
| R-08 | Expert validation memberi nilai rendah pada relevansi rekomendasi | Rendah–Sedang | Iterasi rule-based mapping berdasarkan masukan; diskusi dengan praktisi |
| R-09 | Deprecation/perubahan endpoint Open Platform API | Sedang | Tangani dengan try/except; tampilkan error + panduan fallback CSV; catat versi API dalam dokumentasi |

## Deliverables Checkpoint 10

- [ ] Dashboard online dan dapat diakses publik (Streamlit Cloud / HuggingFace Spaces).
- [ ] Repository GitHub selesai dengan dokumentasi lengkap.
- [ ] `README.md` lengkap dan informatif.
- [ ] User Guide tersedia (PDF atau Markdown).
- [ ] Evaluation report final tersedia (`outputs/reports/evaluation_final.json`).
- [ ] Validation report tersedia (`outputs/reports/validation_report.pdf`).
- [ ] Sistem siap untuk demo seminar hasil.

## Gate Akhir

Fase ini adalah penutup. Jika semua deliverables terpenuhi dan sistem dapat diakses publik, proyek dinyatakan **selesai**.
