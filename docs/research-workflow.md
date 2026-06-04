# Research flow + quick start

Dokumen ini pakai pipeline yang sudah ada di repo untuk bikin riset mini: cari korelasi statistik antar aspek astrologi dan perilaku pasar tanpa membuat black-box.

## 0) Siapkan environment

```bash
PYTHONPATH=src python3 -m pip install -U pip
PYTHONPATH=src pip install -e .
```

Jika mau jalankan test:

```bash
PYTHONPATH=src python3 -m pytest -q
```

## 1) Alur riset singkat

1. **Rumusan hipotesis**  
   Contoh: “Conjunction Sun-Moon hari *t* meningkatkan peluang return `1d` positif.”

2. **Siapkan label pasar**  
   - Dari close price: `add_forward_returns(closes, horizons=[1])` (otomatis kasih `return_1d`, `bullish_1d`).  
   - Tambahkan `timestamp` + `asset` ke tiap label jika akan di-*join* dengan aspek.

3. **Siapkan data astro (position per timestamp)**  
   - Pakai real data: `generate_planet_positions(...)` + `scan_aspect_series(...)`.
   - Atau sintetik untuk prototipe cepat, tapi tetap valid terhadap validator library.

4. **Deteksi aspek**  
   - `scan_aspect_series(...)` memindai aspek di tiap timestamp.
   - Kalau perlu, filter aspek tertentu: contoh hanya `conjunction`.

5. **Join aspek ↔ label**
   - Gunakan `join_aspect_events_to_market_labels(...)` untuk hasilkan `TimestampJoinResult`.
   - Ini memastikan pemetaan berbasis timestamp, bukan hanya index.

6. **Event study + validasi**
   - `summarize_event_study(labels, event_indexes, horizon)` untuk baseline vs conditional.
   - `summarize_validated_event_study(... bootstrap_samples=..., bootstrap_seed=...)` untuk interval confidence + warning.
   - `permutation_test(...)` untuk cek signifikansi kasar secara non-parametrik.

7. **Eksport hasil**
   - `to_json(...)` dan `to_csv(...)` untuk jejak audit/laporan.

## 2) Antarmuka antarmuka yang berguna

- `hermetic_alpha.astro`:
  - `generate_planet_positions`, `scan_aspect_series`, `detect_aspect`, `find_aspects`
- `hermetic_alpha.labels`:
  - `add_forward_returns`, `add_local_extrema_labels`
- `hermetic_alpha.analysis`:
  - `join_aspect_events_to_market_labels`, `summarize_event_study`, `summarize_validated_event_study`, `permutation_test`
- `hermetic_alpha.exports`:
  - `to_csv`, `to_json`

## 3) Contoh mini riset (bukti kerja)

Buka contoh ini untuk bukti end-to-end:

- Script sintetik: [`examples/synthetic_astronomy_return_case.py`](../examples/synthetic_astronomy_return_case.py)
- Script real-market (multi-asset + walk-forward): [`examples/real_market_astronomy_return_case.py`](../examples/real_market_astronomy_return_case.py)
- Jalankan yang sintetik:

```bash
PYTHONPATH=src python3 examples/synthetic_astronomy_return_case.py
```

Atau jalankan yang real-market (multi-asset + walk-forward, data Yahoo Finance):

```bash
PYTHONPATH=src python3 examples/real_market_astronomy_return_case.py \
  --assets BTC-USD,ETH-USD,SOL-USD \
  --start 2025-01-01 \
  --end 2026-01-01 \
  --horizon 1 \
  --aspects conjunction,square \
  --bodies sun,moon \
  --max-orb 1.0 \
  --walk-forward-train-size 200 \
  --walk-forward-test-size 60 \
  --walk-forward-step-size 60
```

Pasang paket ephemeris agar posisi sungguhan bisa dipakai:

```bash
PYTHONPATH=src pip install -e ".[ephemeris]"
```

Script real-market otomatis pakai `pyswisseph` jika tersedia, atau fallback ke posisi sintetik yang reproducible agar pipeline tetap bisa dijalankan.

Untuk melihat format laporan di output:
- `tmp/market_multi_asset_<start>_<end>_<horizon>d.csv`
- `tmp/market_multi_asset_<start>_<end>_<horizon>d.json`

Script ini:
- membuat seri harga sintetik,
- generate posisi Sun/Moon sintetik per hari,
- scan aspek untuk ambil conjunction,
- hitung event-study 1-hari,
- validasi dengan bootstrap + permutation test,
- lalu cetak rekomendasi interpretasi.

## 4) Catatan kualitas riset

Untuk publish, ikuti prinsip di [Anti-Overfitting Guide](anti-overfitting.md):
- selalu bandingkan ke baseline,
- pakai sample-size-aware (low sample warning),
- simpan metode & parameter di log,
- pisahkan data penemuan dan data verifikasi (kalau proyek skala lebih besar).
