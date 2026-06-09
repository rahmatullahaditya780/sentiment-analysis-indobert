# TRD — Revisi Pengambilan Data Ulasan Implementasi (Selaras Proposal)

> **Status:** Usulan revisi, 2026-06-09.
> **Tujuan:** menyelaraskan TRD dengan **Proposal Revisi Final** pada metode
> pengambilan data ulasan implementasi OmorfoShop, serta menambah **opsi input
> praktis berlapis** bagi pengguna awam untuk analisis ulasan volume besar.
>
> Dokumen ini ditulis dalam Markdown agar mudah ditinjau & diversi-kontrol. Teks
> pada Bagian A–C siap disalin ke `TRD.docx`. Mengganti istilah lama "Shopee Open
> Platform API (metode utama)" → "Web Scraping (Playwright, halaman publik)".

---

## 0. Latar Belakang Revisi

| Aspek | Proposal Revisi Final (acuan) | TRD lama (menyimpang) |
|---|---|---|
| Metode data implementasi | **Web scraping** halaman produk **publik** Shopee via Python | Shopee Open Platform API (OAuth2, `get_item_list`/`get_rating`) |
| Akses | Tanpa autentikasi akun khusus; izin **informal** pemilik toko | Butuh otorisasi OAuth2 toko (Shop-scoped) |
| Input dashboard | **Input URL produk** → scraping dinamis → analisis | Item Selector dropdown produk **toko sendiri** dari API |

**Akar masalah TRD lama:** endpoint `get_rating`/`get_comment` bersifat **Shop-scoped**
— hanya mengembalikan ulasan toko yang **mengotorisasi** aplikasi partner. Karena
sistem ini ditujukan untuk menganalisis **toko publik mana pun** (bukan hanya toko
milik pengguna), jalur API resmi **tidak dapat dipakai** untuk toko pihak ketiga.
Maka metode dikembalikan ke **web scraping halaman publik**, sesuai proposal.

Modul `src/shopee_api/` (OAuth2 + client) **tidak dibuang** — diturunkan menjadi
**opsi lanjutan (future work)** khusus persona "seller menganalisis tokonya sendiri",
di mana self-authorization memungkinkan.

---

## Bagian A — Metode Pengambilan Data Implementasi (kembali ke scraping)

### A.1 Struktur Folder (revisi baris terkait)
```
├── data/
│   └── implementation/ # Dataset OmorfoShop hasil web scraping (CSV)
├── src/
│   ├── scraping/       # Scraper Playwright OmorfoShop (modul AKTIF)
│   └── shopee_api/     # Open Platform client (OPSIONAL/future: toko sendiri)
```

### A.2 Tech Stack (revisi baris pengambilan data)
| Komponen | Teknologi | Keterangan |
|---|---|---|
| Web Scraping | Python + **Playwright (Chromium)** | Render DOM halaman produk publik Shopee; sesi login persisten untuk lewati anti-bot |
| Konversi Ekstensi | Python (Pandas) | Konversi CSV hasil ekstensi browser → skema implementasi |
| (Opsional/future) API | `requests` + HMAC-SHA256 (OAuth2) | Hanya untuk persona seller-toko-sendiri |

### A.3 Functional Requirement (revisi FR-2.2)
| ID | Requirement (revisi) |
|---|---|
| FR-2.2 | Sistem harus dapat mengambil ulasan produk **publik** Shopee (OmorfoShop Official Store) melalui **web scraping render-DOM menggunakan Python (Playwright)**, dengan sesi browser ber-login untuk melewati proteksi anti-bot. |

### A.4 Dataset Implementasi (revisi Metode Pengumpulan)
| Atribut | Detail |
|---|---|
| Sumber | OmorfoShop Official Store — Shopee (halaman publik) |
| Jumlah | ± 1.200 ulasan produk |
| Periode | sesuai pengambilan (dokumentasikan tanggal aktual) |
| **Metode Pengumpulan** | **Web scraping (Playwright, halaman publik)** + opsi ekstensi browser → CSV |
| Tujuan | Implementasi model & rekomendasi pemasaran (**BUKAN** training) |
| Privasi | Identitas pelanggan (nama, foto) **tidak disimpan** — data minimization |
| Etika | Hanya ulasan publik; izin **informal** pemilik toko; jeda rate-limit; patuh batas wajar ToS |
| Atribut | `review_id, review_text, rating, product_name, product_category, date_review` |

### A.5 Proses Pengambilan (revisi)
1. Siapkan sesi login persisten Playwright (`--user-data-dir`, login manual sekali).
2. Untuk tiap URL produk: render DOM, gulir lazy-load, **iterasi filter rating
   (5→1 bintang)** agar diversitas kelas (positif/negatif/netral) terjaga.
3. Telusuri pagination ulasan per filter; ekstrak `review_text`, `rating`, `date_review`.
4. Dedup deterministik (`review_id` = SHA1 teks+tanggal) lintas produk & run.
5. Export CSV ke `data/implementation/omorfo_reviews.csv` (skema kanonik).

---

## Bagian B — Modul Input Dashboard Berlapis (Fase 8)

Menggantikan dikotomi lama (URL-scraper **vs** API-connector) dengan **satu modul
input berlapis (tiered)** yang memberi pengguna awam beberapa jalur sesuai
kemampuan & lingkungan, diurut dari paling tahan-banting:

| Tier | Jalur | Ramah awam | Anti-bot | Lingkungan | Catatan |
|---|---|---|---|---|---|
| 1 | **CSV Upload** | ★★★ | non-isu | Cloud & Lokal | Lantai universal; selalu jalan |
| 2 | **Import Ekstensi Browser** | ★★★ | nol | Cloud & Lokal | User export CSV dari halaman yang ia buka sendiri |
| 3 | **URL Auto-Fetch (browser ber-login)** | ★★ | dilewati manusia | **Lokal saja** | Playwright headful + login sekali → otomasi sesi sah |
| (4) | API resmi toko sendiri | ★★ | nol | Cloud & Lokal | *Future work*, hanya untuk seller toko sendiri |
| (5) | Layanan scraping berbayar | ★ | ditangani vendor | Cloud & Lokal | Opsional; biaya + ToS abu-abu; bukan metode utama |

### B.1 Functional Requirements (revisi)
| ID | Requirement (revisi) |
|---|---|
| FR-8.2 | Dashboard harus menyediakan **input berlapis** sebagai metode utama: (a) Upload CSV, (b) Import CSV hasil ekstensi browser, (c) Input **URL produk Shopee** untuk pengambilan otomatis via **browser ber-login (mode lokal/desktop)**. |
| FR-8.9 | Dashboard harus menampilkan indikator status **pengambilan/scraping** yang informatif (berjalan / berhasil + jumlah ulasan / gagal + pesan error + panduan fallback ke jalur lain). |
| FR-8.10 | Dashboard harus **memvalidasi format URL produk Shopee** sebelum memulai scraping dan menampilkan pesan error informatif jika URL tidak valid. |
| FR-8.11 | Dashboard harus menampilkan **progress bar & counter** jumlah ulasan terkumpul selama scraping berlangsung. |
| FR-8.12 | Dashboard harus membatasi jumlah ulasan maksimal **±1.200 ulasan** per produk untuk menjaga performa. |
| FR-8.13 | Dashboard harus menerapkan **jeda antar-aksi (rate limiting)** saat scraping untuk menghindari pemblokiran Shopee. |
| FR-8.14 (BARU) | Dashboard harus **mendeteksi lingkungan** (cloud vs lokal) dan **menonaktifkan/menyembunyikan** jalur URL Auto-Fetch saat berjalan di cloud (tanpa display/browser), mengarahkan pengguna ke CSV/ekstensi. |

### B.2 Module 1 — Input Interface (revisi, 3 tab)
| Tab | Komponen | Deskripsi |
|---|---|---|
| **CSV Upload** | File uploader + Analyze | Upload CSV ulasan untuk analisis batch |
| **Extension Import** | File uploader + konverter | Upload CSV hasil ekstensi browser → dipetakan ke skema implementasi |
| **URL Auto-Fetch** (badge *Lokal saja*) | URL input, Fetch button, Progress bar, Preview 5 baris | Scraping otomatis via browser ber-login; nonaktif di cloud |

### B.3 Module 6 — Shopee Review Collector (Berlapis) — revisi
| Komponen | Deskripsi & Spesifikasi |
|---|---|
| Tiered Router | Memilih jalur (CSV / Ekstensi / URL Auto-Fetch) sesuai pilihan & lingkungan |
| Playwright Engine | Render DOM, sesi login persisten, iterasi filter rating, pagination, dedup (lokal) |
| Extension Converter | Konversi CSV ekstensi → skema implementasi (reuse `convert_extension_csv.py`) |
| Selector Config | Selektor DOM eksternal (`selectors_shopee.json`) agar tahan perubahan layout |
| Data Normalizer | Output seragam `[review_id, review_text, rating, product_name, product_category, date_review]` |
| Error/Fallback Handler | Deteksi login-wall/0-ulasan/timeout → pesan informatif + arahkan ke jalur lain |

---

## Bagian C — Strategi Anti-Bot & Batasan Deployment (subbab BARU)

### C.1 Mengapa "tempel link → auto-scrape server" gagal
Yang diblokir Shopee adalah **permintaan anonim/headless dari server** (anti-bot:
DataDome, login-wall, CAPTCHA, device-fingerprinting, rate-limit IP), **bukan**
scraping itu sendiri. Solusi: **manusia melewati gerbang anti-bot satu kali, lalu
otomasi berjalan di dalam sesi sah** → diwujudkan sebagai input berlapis (Bagian B).

### C.2 Batasan Streamlit Community Cloud (free) — dasar keputusan deployment
| Batasan | Sumber | Implikasi desain |
|---|---|---|
| **RAM 1 GB / app** | Dokumentasi resmi Streamlit | IndoBERT (~500 MB) + Chromium → risiko OOM; pertimbangkan HF Spaces |
| **Chromium hanya HEADLESS** (via `packages.txt` + `playwright install`) | Forum Streamlit | Tak ada display → **login manual (human-in-the-loop) mustahil di cloud** |
| **IP datacenter + headless** | Sifat hosting cloud | Persis pola yang diblokir anti-bot Shopee |
| **Filesystem ephemeral + app sleep** | Dokumentasi resmi Streamlit | Sesi login persisten tak bertahan; cocok hanya untuk upload |

### C.3 Keputusan Deployment
- **Versi Cloud (Streamlit/HF Spaces):** hanya **Tier 1 (CSV)** + **Tier 2 (Ekstensi)**.
  Jalur URL Auto-Fetch dinonaktifkan (FR-8.14).
- **Versi Lokal/Desktop:** **semua tier** aktif, termasuk URL Auto-Fetch (browser ber-login).
- **Bila auto-fetch online wajib:** opsi = jalankan lokal, atau backend scraping
  berbayar (Tier 5) dengan konsekuensi biaya & ToS.

### C.4 Etika & Kepatuhan (dipertahankan dari proposal)
- Hanya ulasan **publik**; tanpa autentikasi akun khusus untuk akses (selain login
  pengguna sendiri pada Tier 3).
- **Tidak menyimpan identitas pelanggan** (data minimization).
- Izin **informal** dari pemilik OmorfoShop untuk pemanfaatan hasil analisis.
- Jeda antar-permintaan (rate limiting) untuk menghormati server.

---

## Referensi riset (batasan Streamlit Cloud)
- Streamlit — *Resource limits / Community Cloud limits* (RAM 1 GB, app sleep).
- Streamlit Community Forum — *Installing Playwright on Streamlit Cloud* (`packages.txt`,
  headless-only, `playwright install`).
- Streamlit Community Forum — *Running Selenium/ChromeDriver on Community Cloud*.
