# Laporan Unit Testing — Fase 9 (FR-9.1)

> Deliverable Checkpoint 9: *"Unit testing selesai dan terdokumentasi."*
> Dokumen ini merangkum hasil unit testing otomatis sistem analisis sentimen
> IndoBERT (Sentara). Artefak data pendukung: [`phase9_unit_test_summary.json`](phase9_unit_test_summary.json)
> (jumlah test per file, di-generate dari koleksi `pytest`).

## Ringkasan

| Metrik | Nilai |
|---|---|
| Total unit test | **199** |
| Status | **199 lulus / 0 gagal** (hijau) |
| Waktu eksekusi suite cepat | ± 11 detik (CPU lokal) |
| Framework | `pytest` 9.x, Python 3.13 |
| File test | 16 berkas di `tests/` |
| Cakupan modul | `src/preprocessing/`, `src/recommendation/`, seluruh `src/dashboard/` |
| Tanggal verifikasi | 2026-06-14 |

Unit test ini terpisah dari **integration test end-to-end** (model IndoBERT
nyata, 16 test) — lihat [`phase9_integration_report.json`](phase9_integration_report.json)
dan bagian "Integration Testing" di bawah.

## Cara Menjalankan

```bash
pytest                     # 199 unit test (cepat; integration dikecualikan via pytest.ini)
pytest -q tests/test_preprocessing.py   # satu modul
pytest -m integration -v   # 16 integration test end-to-end (memuat model ~500MB)
```

`pytest.ini` menetapkan `addopts = -m "not integration"` sehingga `pytest` default
selalu menjalankan suite unit yang cepat dan **bisa berjalan di lingkungan tanpa
model** (cloud/CI; bobot model di-gitignore).

## Rincian per Modul yang Diuji

### Fase 3 — Preprocessing (31 test)

| File | Jml | Fokus uji |
|---|---|---|
| `test_preprocessing.py` | 31 | Case folding; cleaning regex (URL, emoji, tag HTML, simbol, tanda baca berulang, elipsis, spasi); `preprocess_text` gabungan; **guard FR-3.3**: TIDAK stemming (imbuhan utuh: "membaca" ≠ "baca"), stopword dipertahankan ("yang/di/ke"), dan AST modul TIDAK mengimpor Sastrawi/NLTK; `PreprocessingPipeline.clean_frame` (buang label hilang/invalid/teks kosong/duplikat + `CleaningStats`) |

### Fase 7 — Rule-Based Recommendation (27 test)

| File | Jml | Fokus uji |
|---|---|---|
| `test_recommendation.py` | 27 | `compute_distribution` (dari DataFrame/dict); klasifikasi **4 kondisi compound** (Sangat Baik/Baik/Perlu Perbaikan/Beragam–Tidak Stabil; "Moderate" dihapus pasca-validasi) + fallback antar-tier; override Mixed via netral tinggi & trend shift; `strategy_mapper` (strategi + insight + simpan JSON); `trend_analyzer` (guard sampel kecil, deteksi shift nyata); orkestrasi `recommend()` end-to-end; `condition_criteria()` turunan `THRESHOLDS` |

### Fase 8 — Dashboard (141 test)

| File | Jml | Modul / komponen |
|---|---|---|
| `test_shopee_connector.py` | 25 | Module 6 — validasi URL, deteksi lingkungan (cloud/lokal), `split_quota` (kuota multi-URL), `combine_fetch_results` (dedup), `plan_fetches` (simpanan sesi) |
| `test_pages_render.py` | 16 | Smoke render 8 halaman multipage (`AppTest`) — dengan data & tanpa data |
| `test_settings_module.py` | 15 | Module 5 — filter kategori/confidence/rentang tanggal/keyword + paginasi |
| `test_visualization_module.py` | 13 | Module 4 — frekuensi kata (buang stopword tampilan), word cloud, top keywords, distribusi kategori |
| `test_login_flow.py` | 12 | Module 6 — deteksi sesi login, perintah worker login, wipe session, start/close browse |
| `test_analysis_pipeline.py` | 11 | Glue — `normalize_input`, `has_predictions`, shortcut lewati inferensi saat berlabel |
| `test_fetch_error_classify.py` | 8 | Module 6 — klasifikasi error fetch (login-wall/ID invalid/timeout/jaringan/anti-bot) + fallback CSV |
| `test_fetch_worker.py` | 7 | Module 6 — parse event NDJSON, susun perintah subprocess, clamp cap |
| `test_results_module.py` | 5 | Module 2 — figure pie/bar/trend, palet sentimen satu sumber |
| `test_input_module.py` | 5 | Module 1 — baca CSV (UTF-8/latin1), validasi kolom teks, CSV kosong |
| `test_model_info.py` | 4 | Baca metrik model dari `outputs/reports/*.json` + fallback |
| `test_cdp_flow.py` | 4 | Module 6 — susun perintah CDP, clamp cap, deteksi Chrome/port |
| `test_recommendation_module.py` | 3 | Module 3 — gaya panel per kondisi (warna), default kondisi tak dikenal |
| **Module 7 (Fase 8.5)** | | |
| `test_insights_module.py` | 13 | Insight Analitik — deteksi mismatch rating↔sentimen, ringkasan kondisi per produk, contoh ulasan representatif |

**Subtotal Fase 8 (termasuk Module 7):** 141 test.

## Integration Testing (FR-9.2) — ringkas

Suite `tests/integration/test_e2e_real_model.py` (16 test, marker `integration`)
menjalankan rantai inti **dengan best model IndoBERT nyata** atas ulasan
OmorfoShop mentah: normalisasi → preprocessing → inferensi → rule engine →
render 8 halaman → ekspor CSV. Hasil run terekam di
[`phase9_integration_report.json`](phase9_integration_report.json). Status: **16 lulus**.
Bila best model tidak tersedia (mis. cloud), modul di-skip otomatis (bukan gagal).

## Pemetaan ke FR-9.1

> *FR-9.1 — Sistem harus lolos unit testing pada setiap fungsi/module
> (preprocessing, inference, rule-based, dashboard).*

| Area FR-9.1 | Status | Bukti |
|---|---|---|
| Preprocessing | ✅ | `test_preprocessing.py` (31) |
| Inference | ✅ | Jalur inferensi divalidasi pada integration test model nyata (FR-9.2); unit test glue memverifikasi kontrak I/O (`test_analysis_pipeline.py`) |
| Rule-based | ✅ | `test_recommendation.py` (27) + `test_recommendation_module.py` (3) |
| Dashboard | ✅ | 12 file dashboard (141 test) termasuk smoke render 8 halaman |

**Kesimpulan:** unit testing inti **selesai & terdokumentasi**; 199 test hijau.
