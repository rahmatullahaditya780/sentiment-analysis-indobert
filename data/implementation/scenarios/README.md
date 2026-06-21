# Dataset Uji 5 Kondisi Pemasaran (Fase 7)

Subset **berlabel** dari data nyata OmorfoShop yang sengaja disusun untuk memicu
tiap kondisi rule engine pemasaran. Tujuannya: menguji & mendemonstrasikan kelima
kondisi (Excellent / Good / Moderate / Poor / Mixed-Unstable) — yang tidak mungkin
muncul dari data natural (≈88,5% positif → hanya Excellent).

Dibuat ulang dengan: `python scripts/make_condition_datasets.py` (deterministik,
seed=42). Angka aktual tercatat di [`manifest.json`](manifest.json).

## Berkas & kondisi yang diharapkan

| Berkas | n | pos / neg / neu | Kondisi | Pemicu |
|---|---|---|---|---|
| `scenario_excellent.csv` | 500 | 85% / 13% / 2% | **Excellent** | pos ≥ 50% AND neg ≤ 20% |
| `scenario_good.csv` | 120 | 45,8% / 28,3% / 25,8% | **Good** | pos 40–49% AND neg 20–30% |
| `scenario_moderate.csv` | 110 | 35,5% / 38,2% / 26,4% | **Moderate** | pos 30–39% AND neg 30–40% |
| `scenario_poor.csv` | 450 | 23,1% / 74,0% / 2,9% | **Poor** | pos < 30% AND neg > 40% |
| `scenario_mixed.csv` | 80 | 37,5% / 22,5% / 40,0% | **Mixed/Unstable** | netral > 35% |

Kolom: `review_id, review_text, rating, product_name, product_category,
predicted_label, confidence_score`.

## Cara pakai

**Dashboard** — `streamlit run app.py` → halaman *Input & Pengambilan Data* → tab
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
  netral**; kondisi yang butuh netral tinggi (Good, Moderate, Mixed) otomatis
  berukuran lebih kecil. Ini sekaligus temuan: ulasan e-commerce nyata nyaris tak
  berkelas netral.
- Berkas saling independen sehingga dapat berbagi baris dari kolam berlabel yang
  sama (mis. ke-32 ulasan netral dipakai ulang lintas skenario).
