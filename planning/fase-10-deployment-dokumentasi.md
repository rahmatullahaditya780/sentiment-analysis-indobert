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

> **Sinkronisasi 2026-06-12:** jalur **Import Ekstensi dihapus** dari Fase 8
> final (input = 2 tier saja); URL Auto-Fetch berjalan dengan **mode CDP**
> (Chrome asli pengguna + endpoint JSON internal), bukan Playwright headful,
> dan kini mendukung **multi-URL dengan kuota dibagi rata + simpanan sesi**
> (`st.session_state` — kompatibel filesystem ephemeral cloud karena memang
> tidak menulis file).

| Komponen | Versi Cloud | Versi Lokal/Desktop |
|---|---|---|
| Tier 1 — CSV Upload | Aktif | Aktif |
| Tier 2 — URL Auto-Fetch (mode CDP, multi-URL) | **Dinonaktifkan** (FR-8.14) | Aktif (Chrome asli ber-login + endpoint JSON internal) |
| Model IndoBERT | Load dari HuggingFace Hub / Google Drive | Load lokal dari `models/` |
| Platform hosting | Streamlit Cloud / HuggingFace Spaces | Lokal (`python app.py` / `streamlit run`) |

> **Artefak wajib ikut repo saat deploy:** `outputs/reports/evaluation_final.json`
> dan `cross_validation_report.json` — dibaca `src/dashboard/model_info.py`
> untuk menampilkan F1/CV di dashboard (ada fallback hardcoded bila absen,
> tetapi nilai laporan asli lebih disukai).

### Batasan Streamlit Community Cloud (free) — dasar keputusan deployment

| Batasan | Implikasi Desain | Solusi |
|---|---|---|
| RAM 1 GB per app | IndoBERT (~500 MB) + Chromium = risiko OOM | Gunakan HF Spaces atau model quantization |
| Chromium headless saja (via `packages.txt`) | Login manual (human-in-the-loop) mustahil di cloud | URL Auto-Fetch dinonaktifkan di cloud (FR-8.14) |
| IP datacenter + headless | Persis pola yang diblokir anti-bot Shopee | Jalur scraping hanya dijalankan lokal |
| Filesystem ephemeral + app sleep | Sesi login persisten tidak bertahan | Hanya upload (Tier 1 & 2) yang cocok untuk cloud |

> **Keputusan deployment (diperbarui):** Versi cloud (Streamlit/HF Spaces) hanya mengaktifkan **Tier 1 (CSV Upload)**; jalur URL Auto-Fetch hanya tersedia di versi lokal/desktop. (Tier Import Ekstensi pada rencana lama sudah dihapus dari implementasi final Fase 8.) Detail latar belakang di `planning/trd-revisi-pengambilan-data-implementasi.md` §C.

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
| R-04 | Skema endpoint JSON internal Shopee (`/api/v2/item/get_ratings`) berubah, atau anti-bot diperketat (metode aktual Fase 8 = endpoint JSON via Chrome CDP; DOM scraping hanya fallback) | Auto-fetch gagal mengambil ulasan | Sedang | Worker fetch terisolasi (mudah diperbarui tanpa sentuh UI); klasifikasi error + panduan pengguna + fallback CSV Upload sudah terpasang; `selectors_shopee.json` dipertahankan untuk fallback DOM |
| R-05 | Class imbalance ekstrem pada unified dataset (selisih > 25%) | Model bias terhadap kelas mayoritas | Sedang | Stratified split + class weight; jika masih ekstrem, augmentasi back-translation untuk kelas minoritas |
| R-06 | Dataset SmSA atau Kaggle tidak tersedia | Training tidak dapat dilakukan | Rendah | Download & simpan snapshot lokal di awal; dokumentasikan versi |
| R-07 | Performa model tidak mencapai target (F1 macro < 85%) | Gagal memenuhi requirement evaluasi | Sedang | Focused random search lebih luas; periksa kualitas label (label noise); dokumentasikan hasil meski tak capai target |
| R-08 | Inferensi IndoBERT lambat (> 5 detik) di CPU | Pengalaman pengguna buruk | Sedang | `st.session_state` untuk cache model; loading spinner; batasi batch size inference |
| R-09 | Validasi praktisi memberi nilai rendah pada relevansi rekomendasi | Kualitas rule-based mapping perlu diperbaiki | Rendah–Sedang | Iterasi rule-based mapping berdasarkan masukan; sesi diskusi dengan praktisi |

## Deliverables Checkpoint 10

- [ ] Dashboard online dan dapat diakses publik (Streamlit Cloud / HuggingFace Spaces) — **CSV Upload di cloud; CSV + URL Auto-Fetch (CDP, multi-URL) di lokal**. *(Repo SIAP deploy untuk kedua platform; deploy aktual = aksi pengguna, butuh akun.)*
- [ ] Repository GitHub selesai dengan dokumentasi lengkap. *(Konten dokumentasi lengkap; tinggal push ke GitHub.)*
- [x] `README.md` lengkap dan informatif. *(Instalasi, struktur, sumber data, interpretasi 4 kondisi, panduan deploy dua platform, logging.)*
- [x] User Guide tersedia (PDF atau Markdown). *(`docs/panduan-pengguna.md` — langkah demi langkah untuk pengguna non-teknis.)*
- [x] Evaluation report final tersedia (`outputs/reports/evaluation_final.json`). *(F1 macro 0.9031; sudah ada sejak Fase 5.)*
- [x] Validation report tersedia (`outputs/reports/validation_report.pdf`). *(Diekspor dari `phase9_validation_report.md` via `scripts/md_to_pdf.py`.)*
- [ ] Sistem siap untuk demo seminar hasil. *(Lokal siap dijalankan; final setelah deploy cloud.)*

### Artefak persiapan deployment yang sudah dibuat (2026-06-23)

| Artefak | Fungsi | FR |
|---|---|---|
| `src/utils/logging_setup.py` (+ integrasi `app.py`/`inference.py`/`analysis_pipeline.py`) | Logging terpusat ke stderr + `outputs/logs/app.log` | FR-10.4 |
| `MODEL_HUB_ID` (`config.py`) + `inference._resolve_source()` | Fallback muat bobot dari HuggingFace Hub bila `models/best_model/` absen (deploy cloud) | FR-10.1 |
| `.streamlit/secrets.toml.example` | Template secrets Streamlit Community Cloud | FR-10.1 |
| `packages.txt` | Apt deps (font wordcloud) untuk cloud | FR-10.1 |
| `README_HF.md` | Front-matter & panduan HuggingFace Spaces (SDK streamlit, `python_version`) | FR-10.1 |
| `README.md`, `docs/panduan-pengguna.md` | Dokumentasi proyek & user guide | FR-10.2/10.3 |
| `.gitignore` (+`.streamlit/secrets.toml`), `.env.example` (+`MODEL_HUB_ID`/`LOG_LEVEL`/`SENTARA_FORCE_ENV`) | Repo bersih & aman | FR-10.5 |
| `scripts/md_to_pdf.py` | Generator PDF dokumentasi (pure-Python) | — |

> **Catatan:** `runtime.txt` tidak dibuat — Streamlit Community Cloud memilih versi
> Python via UI deploy, HF Spaces via `python_version` di front-matter `README_HF.md`;
> tidak ada platform target yang membaca `runtime.txt`.

### Langkah deploy tersisa (aksi pengguna — butuh akun)

1. Upload bobot IndoBERT fine-tuned ke repo HuggingFace Hub; set `MODEL_HUB_ID`.
2. Push repo ke GitHub.
3. Deploy ke Streamlit Community Cloud (isi Secrets) **atau** HuggingFace Spaces
   (salin front-matter `README_HF.md`). Lihat section README "Deployment".

## Gate Akhir

Fase ini adalah penutup. Jika semua deliverables terpenuhi dan sistem dapat diakses publik, proyek dinyatakan **selesai**.
