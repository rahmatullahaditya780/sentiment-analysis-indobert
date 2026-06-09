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

### Matriks Fitur: Versi Cloud vs Lokal/Desktop

| Komponen | Versi Cloud | Versi Lokal/Desktop |
|---|---|---|
| Tier 1 — CSV Upload | Aktif | Aktif |
| Tier 2 — Import Ekstensi | Aktif | Aktif |
| Tier 3 — URL Auto-Fetch | **Dinonaktifkan** (FR-8.14) | Aktif (Playwright headful + login sekali) |
| Model IndoBERT | Load dari HuggingFace Hub / Google Drive | Load lokal dari `models/` |
| Platform hosting | Streamlit Cloud / HuggingFace Spaces | Lokal (`python app.py` / `streamlit run`) |

### Batasan Streamlit Community Cloud (free) — dasar keputusan deployment

| Batasan | Implikasi Desain | Solusi |
|---|---|---|
| RAM 1 GB per app | IndoBERT (~500 MB) + Chromium = risiko OOM | Gunakan HF Spaces atau model quantization |
| Chromium headless saja (via `packages.txt`) | Login manual (human-in-the-loop) mustahil di cloud | URL Auto-Fetch dinonaktifkan di cloud (FR-8.14) |
| IP datacenter + headless | Persis pola yang diblokir anti-bot Shopee | Jalur scraping hanya dijalankan lokal |
| Filesystem ephemeral + app sleep | Sesi login persisten tidak bertahan | Hanya upload (Tier 1 & 2) yang cocok untuk cloud |

> **Keputusan deployment:** Versi cloud (Streamlit/HF Spaces) hanya mengaktifkan **Tier 1 (CSV)** + **Tier 2 (Ekstensi)**; jalur URL Auto-Fetch (Tier 3) hanya tersedia di versi lokal/desktop. Detail di `planning/trd-revisi-pengambilan-data-implementasi.md` §C.

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

| No | Risiko | Dampak | Probabilitas | Strategi Mitigasi |
|---|---|---|---|---|
| R-01 | Keterbatasan GPU lokal (AMD Radeon Vega 7, bukan NVIDIA) | Training IndoBERT sangat lambat | Tinggi | Gunakan Google Colab (gratis/Pro) untuk training |
| R-02 | Streamlit Cloud melampaui batas memori (~1 GB) saat memuat IndoBERT (~500 MB) | Dashboard crash saat runtime | Tinggi | Gunakan HuggingFace Spaces; pertimbangkan model quantization / caching model di cloud storage |
| R-03 | Anti-bot Shopee memblokir scraping (IP datacenter, Chromium headless) | Dataset implementasi tidak terkumpul di cloud | Sedang | Jalankan scraping hanya di lokal (Tier 3); versi cloud hanya Tier 1 & 2; sediakan fallback CSV |
| R-04 | Selektor DOM Shopee berubah (maintenance / redesign layout) | Scraper gagal mengekstrak data | Sedang | Gunakan `selectors_shopee.json` eksternal agar selektor dapat diperbarui tanpa ubah kode; monitor & update berkala |
| R-05 | Class imbalance ekstrem pada unified dataset (selisih > 25%) | Model bias terhadap kelas mayoritas | Sedang | Stratified split + class weight; jika masih ekstrem, augmentasi back-translation untuk kelas minoritas |
| R-06 | Dataset SmSA atau Kaggle tidak tersedia | Training tidak dapat dilakukan | Rendah | Download & simpan snapshot lokal di awal; dokumentasikan versi |
| R-07 | Performa model tidak mencapai target (F1 macro < 85%) | Gagal memenuhi requirement evaluasi | Sedang | Focused random search lebih luas; periksa kualitas label (label noise); dokumentasikan hasil meski tak capai target |
| R-08 | Inferensi IndoBERT lambat (> 5 detik) di CPU | Pengalaman pengguna buruk | Sedang | `st.session_state` untuk cache model; loading spinner; batasi batch size inference |
| R-09 | Validasi praktisi memberi nilai rendah pada relevansi rekomendasi | Kualitas rule-based mapping perlu diperbaiki | Rendah–Sedang | Iterasi rule-based mapping berdasarkan masukan; sesi diskusi dengan praktisi |

## Deliverables Checkpoint 10

- [ ] Dashboard online dan dapat diakses publik (Streamlit Cloud / HuggingFace Spaces) — **Tier 1–2 di cloud, Tier 1–3 di lokal**.
- [ ] Repository GitHub selesai dengan dokumentasi lengkap.
- [ ] `README.md` lengkap dan informatif.
- [ ] User Guide tersedia (PDF atau Markdown).
- [ ] Evaluation report final tersedia (`outputs/reports/evaluation_final.json`).
- [ ] Validation report tersedia (`outputs/reports/validation_report.pdf`).
- [ ] Sistem siap untuk demo seminar hasil.

## Gate Akhir

Fase ini adalah penutup. Jika semua deliverables terpenuhi dan sistem dapat diakses publik, proyek dinyatakan **selesai**.
