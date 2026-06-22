# Dataset Uji 4 Kondisi Pemasaran (Fase 7)

Subset **berlabel** dari data nyata OmorfoShop yang sengaja disusun untuk memicu
tiap kondisi rule engine pemasaran. Tujuannya: menguji & mendemonstrasikan keempat
kondisi (Sangat Baik / Baik / Perlu Perbaikan / Beragam-Tidak Stabil) — yang tidak
mungkin muncul dari data natural (≈88,5% positif → hanya Sangat Baik).

Dibuat ulang dengan: `python scripts/make_condition_datasets.py` (deterministik,
seed=42). Angka aktual tercatat di [`manifest.json`](manifest.json).

## Berkas & kondisi yang diharapkan

| Berkas | n | pos / neg / neu | Kondisi | Pemicu |
|---|---|---|---|---|
| `scenario_excellent.csv` | 500 | 85% / 13% / 2% | **Sangat Baik** | pos ≥ 50% DAN neg ≤ 20% |
| `scenario_good.csv` | 120 | 45,8% / 28,3% / 25,8% | **Baik** | pos 40–49% DAN neg 20–30% |
| `scenario_poor.csv` | 450 | 23,1% / 74,0% / 2,9% | **Perlu Perbaikan** | pos < 30% DAN neg > 40% |
| `scenario_mixed.csv` | 80 | 37,5% / 22,5% / 40,0% | **Beragam / Tidak Stabil** | netral > 35% |

> Kondisi **Moderate dihapus** (penyederhanaan pasca-validasi praktisi, 5→4 kondisi).
> Band lama Moderate (pos 30–39% & neg 30–40%) kini jatuh ke **Beragam / Tidak Stabil**.

Kolom: `review_id, review_text, rating, product_name, product_category,
predicted_label, confidence_score`.

## Cara pakai

**Dashboard** — `streamlit run app.py` → halaman *Beranda* (mode input) → tab
**CSV Upload** → unggah salah satu berkas. Karena CSV sudah berisi `predicted_label`
+ `confidence_score`, dashboard **melewati inferensi** dan langsung menampilkan
distribusi, kondisi, serta playbook strategi yang sesuai.

**Tes otomatis** — `pytest tests/test_condition_scenarios.py -q` memverifikasi tiap
berkas memetakan ke kondisi yang diharapkan (rule engine saja, tanpa model).

## Catatan

- Kolom `date_review` sengaja **tidak disertakan** agar kondisi murni ditentukan
  distribusi sentimen (analisis tren nonaktif) — hasil konsisten antara dashboard
  dan tes.
- Ukuran berkas **bervariasi (≤ 500)** karena data nyata hanya memiliki **32 ulasan
  netral**; kondisi yang butuh netral tinggi (Baik, Beragam/Tidak Stabil) otomatis
  berukuran lebih kecil. Ini sekaligus temuan: ulasan e-commerce nyata nyaris tak
  berkelas netral.
- Berkas saling independen sehingga dapat berbagi baris dari kolam berlabel yang
  sama (mis. ke-32 ulasan netral dipakai ulang lintas skenario).
