---
title: "Radical S&P 500 Astrology Event Study"
subtitle: "Dogfooding hermetic-alpha-library v0.1.1 on ^GSPC, 1927–2026"
author: "Hermes Agent for Wau"
date: "2026-06-04"
lang: id-ID
geometry: margin=0.8in
fontsize: 10pt
---

# Radical S&P 500 Astrology Event Study

**Repository:** `wauputr4/hermetic-alpha-library`  
**Library:** `hermetic-alpha` v0.1.1 + `pyswisseph` backend 20230604  
**Asset:** `^GSPC` / S&P 500 index proxy via Yahoo Finance  
**Actual data:** 1927-12-30 → 2026-06-04 (24,723 daily candles)  
**Train/test split:** train through 1987-12-31 (15,045 candles), test after (9,678 candles)  
**Status:** eksplorasi statistik / dogfood library, bukan financial advice.

## Executive summary

Penelitian ini menguji apakah window aspek astrologi besar punya korelasi historis dengan forward return S&P 500. Metodenya sengaja dibuat lebih ketat dari sekadar menghitung setiap hari aspek aktif: semua active aspect day dikelompokkan menjadi window, lalu hanya **nearest exact date** yang dipakai sebagai event. Untuk kalender saham, event yang jatuh weekend/libur dipetakan ke trading day berikutnya maksimum 3 hari.

Temuan utamanya:

1. **S&P 500 punya drift positif kuat**, jadi pola harus dibandingkan melawan baseline asset sendiri. Baseline 180d rata-rata adalah **5.731%** dengan bullish rate **68.728%**.
2. **Saturn–Neptune square** muncul sebagai kandidat konstruktif paling menarik pada horizon 180d: 12–13 event, all-events avg sekitar **12.6–13.6%**, bullish **100%**, train/test edge sama-sama positif. Namun sample kecil, jadi ini hipotesis siklus besar, bukan sinyal trading.
3. **Saturn–Neptune trine**, **Jupiter–Uranus sextile**, dan **Saturn–Uranus square** muncul sebagai pressure / underperformance candidates, terutama 90–180d. Beberapa terlihat regime-sensitive; post-GFC tidak selalu seburuk era sebelumnya.
4. Pola BTC tidak transfer satu-ke-satu ke SPX. Theme `venus_opposition_riskon` yang menarik di BTC justru mild underperformance di SPX pada 14d. Sebaliknya, theme cooldown `mercury_venus` cukup konsisten sebagai pause window.
5. Dalam scan no-moon full, Mars opposition ke Sun/Mercury/Venus terlihat konstruktif di 180d — berlawanan dengan tafsir simbolik simplistis bahwa Mars opposition otomatis bearish.

## Research question

Pertanyaan risetnya: jika `hermetic-alpha-library` dipakai untuk event study finansial, apakah aspek planet besar bisa membentuk bucket return yang **konsisten train/test**, bukan cuma cherry-picked? Fokusnya bukan membuktikan astrologi sebagai kausalitas market, melainkan mengubah klaim yang biasanya naratif menjadi objek data: event date, forward return, baseline, sample size, dan validation split.

## Data dan metodologi

### Data market

- Symbol Yahoo: `^GSPC`
- Requested start: 1900-01-01
- Actual start: 1927-12-30
- Actual end: 2026-06-04
- Candle count: 24,723
- Caveat: data Yahoo untuk indeks panjang historis berguna untuk eksplorasi, tapi bukan audit-grade dan bukan instrumen investable langsung seperti SPY/ES futures.

### Event construction

1. Generate posisi planet harian untuk rentang candle.
2. Scan aspek: conjunction, opposition, trine, square, sextile.
3. Kelompokkan active aspect days berdasarkan feature `body_a_body_b_aspect`.
4. Collapse consecutive days menjadi satu window.
5. Pilih exact event date = baris dengan orb terkecil di window itu.
6. Untuk `^GSPC`, jika exact date bukan trading day, map ke same/next available trading day dalam 3 hari kalender.
7. Hitung forward return 3d, 7d, 14d, 30d, 60d, 90d, 180d.

### Universes

#### Outer Big Cycles

- Internal name: `spx_outer_big_cycles`
- Bodies: jupiter, saturn, uranus, neptune, pluto
- Aspects: conjunction, opposition, trine, square, sextile
- Orb: 3.0°
- Horizons: 3d, 7d, 14d, 30d, 60d, 90d, 180d
- Raw aspect days: 56,010
- Exact windows mapped: 661
- Features scored: 24
- Tags/themes scored: 29/3

#### No-Moon Full Scan

- Internal name: `spx_no_moon_full`
- Bodies: sun, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto
- Aspects: conjunction, opposition, trine, square, sextile
- Orb: 2.5°
- Horizons: 3d, 7d, 14d, 30d, 60d, 90d, 180d
- Raw aspect days: 145,527
- Exact windows mapped: 18,342
- Features scored: 145
- Tags/themes scored: 92/12

## Baseline S&P 500

Ini baseline forward return semua candle valid. Semua pola harus dinilai relatif terhadap angka ini, bukan relatif terhadap nol.

| Horizon | N | Avg | Median | Bullish | Min | Max |
|---:|---:|---:|---:|---:|---:|---:|
| 3d | 24,720 | 0.094% | 0.183% | 55.174% | -26.338% | 22.655% |
| 7d | 24,716 | 0.219% | 0.395% | 56.987% | -29.161% | 29.642% |
| 14d | 24,709 | 0.440% | 0.737% | 59.225% | -37.531% | 55.439% |
| 30d | 24,693 | 0.951% | 1.390% | 61.013% | -41.446% | 78.750% |
| 60d | 24,663 | 1.902% | 2.416% | 63.824% | -50.113% | 93.435% |
| 90d | 24,633 | 2.825% | 3.545% | 65.392% | -49.024% | 117.179% |
| 180d | 24,543 | 5.731% | 6.760% | 68.728% | -65.135% | 84.891% |

## Results: feature-level findings

## Outer Big Cycles

### Top constructive candidates

| # | Feature | Events | Best horizon | Avg | Median | Bullish | Train edge | Test edge | Exact-date span |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `neptune_saturn_square` | 13 | 180d | 12.563% | 11.707% | 100.000% | +8.752 pp | +4.594 pp | 1944-07-02 → 2016-09-10 |
| 2 | `jupiter_saturn_sextile` | 22 | 180d | 8.947% | 11.153% | 90.909% | +0.645 pp | +6.930 pp | 1937-04-03 → 2024-02-06 |
| 3 | `jupiter_saturn_square` | 27 | 60d | 4.658% | 5.022% | 77.778% | +2.592 pp | +2.962 pp | 1935-11-26 → 2025-06-15 |
| 4 | `jupiter_neptune_square` | 26 | 90d | 5.235% | 5.943% | 84.615% | +2.124 pp | +2.867 pp | 1929-06-07 → 2025-06-19 |
| 5 | `pluto_saturn_sextile` | 13 | 30d | 2.922% | 1.332% | 84.615% | +0.885 pp | +2.902 pp | 1942-06-09 → 2026-03-28 |
| 6 | `jupiter_pluto_square` | 25 | 30d | 2.218% | 1.390% | 80.000% | +0.582 pp | +2.293 pp | 1928-03-31 → 2023-05-17 |
| 7 | `neptune_pluto_sextile` | 45 | 90d | 4.620% | 4.411% | 75.000% | +2.379 pp | +0.237 pp | 1945-02-19 → 2026-06-03 |
| 8 | `jupiter_pluto_trine` | 26 | 14d | 1.293% | 1.800% | 73.077% | +1.069 pp | +0.556 pp | 1935-03-13 → 2024-06-02 |
| 9 | `jupiter_saturn_trine` | 30 | 30d | 1.584% | 1.687% | 66.667% | +0.643 pp | +0.619 pp | 1928-04-16 → 2025-11-17 |
| 10 | `pluto_saturn_square` | 11 | 7d | 0.637% | 0.120% | 54.545% | +0.665 pp | +0.120 pp | 1939-07-28 → 2010-08-21 |

### Top pressure / underperformance candidates

| # | Feature | Events | Best horizon | Avg | Median | Bullish | Train edge | Test edge | Exact-date span |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `neptune_saturn_trine` | 16 | 180d | -3.238% | -5.486% | 43.750% | -10.244 pp | -6.162 pp | 1929-03-06 → 2013-07-19 |
| 2 | `jupiter_uranus_sextile` | 22 | 90d | -3.206% | -2.156% | 36.364% | -5.580 pp | -6.998 pp | 1929-08-07 → 2022-02-17 |
| 3 | `saturn_uranus_square` | 16 | 180d | -2.625% | 2.254% | 56.250% | -11.837 pp | -2.552 pp | 1930-02-22 → 2022-10-04 |
| 4 | `jupiter_pluto_opposition` | 12 | 90d | -2.851% | -1.227% | 50.000% | -5.171 pp | -6.384 pp | 1937-05-29 → 2014-01-31 |
| 5 | `jupiter_uranus_square` | 24 | 180d | -1.260% | 1.386% | 54.167% | -8.443 pp | -4.085 pp | 1930-09-05 → 2021-01-17 |
| 6 | `pluto_saturn_trine` | 13 | 180d | 0.392% | 3.794% | 61.538% | -8.987 pp | -1.081 pp | 1937-03-26 → 2008-04-26 |
| 7 | `jupiter_uranus_trine` | 27 | 180d | 0.712% | 3.020% | 62.963% | -7.017 pp | -2.112 pp | 1931-10-10 → 2019-12-15 |
| 8 | `jupiter_saturn_opposition` | 17 | 90d | -2.055% | -2.724% | 47.059% | -6.797 pp | -2.142 pp | 1930-07-27 → 2012-01-09 |
| 9 | `jupiter_uranus_opposition` | 15 | 180d | 1.720% | 4.200% | 53.333% | -4.182 pp | -3.816 pp | 1934-01-30 → 2017-09-28 |
| 10 | `jupiter_neptune_sextile` | 24 | 60d | -0.771% | -1.897% | 37.500% | -2.530 pp | -2.872 pp | 1930-07-03 → 2024-05-23 |

## No-Moon Full Scan

### Top constructive candidates

| # | Feature | Events | Best horizon | Avg | Median | Bullish | Train edge | Test edge | Exact-date span |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `neptune_saturn_square` | 12 | 180d | 13.591% | 12.647% | 100.000% | +8.752 pp | +6.613 pp | 1944-07-02 → 2016-09-10 |
| 2 | `jupiter_uranus_conjunction` | 13 | 90d | 7.507% | 8.256% | 76.923% | +3.194 pp | +7.061 pp | 1928-01-25 → 2024-04-20 |
| 3 | `jupiter_saturn_sextile` | 22 | 180d | 10.881% | 11.153% | 95.455% | +4.223 pp | +6.265 pp | 1937-12-12 → 2024-02-06 |
| 4 | `mars_sun_opposition` | 46 | 180d | 9.319% | 12.197% | 80.435% | +3.311 pp | +4.021 pp | 1928-12-21 → 2025-01-16 |
| 5 | `jupiter_saturn_square` | 26 | 60d | 4.833% | 5.275% | 76.923% | +2.592 pp | +3.393 pp | 1935-11-26 → 2025-06-15 |
| 6 | `mars_mercury_opposition` | 49 | 180d | 8.667% | 10.207% | 77.551% | +2.809 pp | +3.137 pp | 1928-12-20 → 2025-01-23 |
| 7 | `mars_neptune_conjunction` | 53 | 60d | 3.979% | 3.407% | 75.000% | +1.009 pp | +3.786 pp | 1929-07-03 → 2026-04-13 |
| 8 | `mars_venus_opposition` | 45 | 180d | 8.129% | 10.333% | 80.000% | +1.926 pp | +3.109 pp | 1928-11-23 → 2024-12-12 |
| 9 | `mars_pluto_conjunction` | 55 | 90d | 4.628% | 6.233% | 70.370% | +0.476 pp | +4.059 pp | 1929-04-16 → 2026-01-27 |
| 10 | `jupiter_neptune_square` | 27 | 90d | 5.188% | 5.299% | 85.185% | +2.124 pp | +2.710 pp | 1929-06-07 → 2025-06-19 |

### Top pressure / underperformance candidates

| # | Feature | Events | Best horizon | Avg | Median | Bullish | Train edge | Test edge | Exact-date span |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `neptune_saturn_trine` | 16 | 180d | -3.238% | -5.486% | 43.750% | -10.244 pp | -6.162 pp | 1929-03-06 → 2013-07-19 |
| 2 | `saturn_uranus_square` | 17 | 180d | -2.400% | 1.330% | 58.824% | -11.837 pp | -2.835 pp | 1930-02-22 → 2022-10-04 |
| 3 | `jupiter_uranus_sextile` | 22 | 90d | -3.206% | -2.156% | 36.364% | -5.580 pp | -6.998 pp | 1929-08-07 → 2022-02-17 |
| 4 | `jupiter_uranus_square` | 23 | 180d | -0.610% | 2.620% | 56.522% | -7.543 pp | -4.085 pp | 1930-09-05 → 2021-01-17 |
| 5 | `jupiter_pluto_opposition` | 13 | 90d | -2.105% | 0.258% | 53.846% | -5.171 pp | -4.649 pp | 1937-05-29 → 2014-04-20 |
| 6 | `jupiter_uranus_opposition` | 14 | 180d | 1.360% | 1.609% | 50.000% | -4.182 pp | -4.622 pp | 1934-01-30 → 2017-09-28 |
| 7 | `jupiter_saturn_opposition` | 18 | 90d | -2.678% | -2.767% | 44.444% | -7.642 pp | -2.142 pp | 1930-07-27 → 2012-01-09 |
| 8 | `pluto_saturn_trine` | 13 | 180d | 0.392% | 3.794% | 61.538% | -8.987 pp | -1.081 pp | 1937-03-26 → 2008-04-26 |
| 9 | `neptune_saturn_sextile` | 11 | 90d | -0.850% | -0.582% | 45.455% | -2.514 pp | -5.069 pp | 1946-11-02 → 2019-11-09 |
| 10 | `jupiter_uranus_trine` | 28 | 180d | 1.398% | 4.063% | 64.286% | -5.769 pp | -2.112 pp | 1931-10-10 → 2019-12-15 |

## Deep dives on the most important patterns

### Constructive candidates

#### `neptune_saturn_square`

- **Events:** 13 total; 7 train, 6 test
- **Exact-date span:** 1944-07-02 → 2016-09-10
- **Mapped weekend/holiday events:** 4
- **Best horizon:** 180d
- **All events:** avg 12.563%, median 11.707%, bullish 100.000%; baseline avg 5.731%
- **Train edge:** +8.752 pp; **test edge:** +4.594 pp

Regime read:

- `early_1927_1971`: events 5; 180d avg 14.095%, median 13.587%, bullish 100.000%
- `post_bretton_woods_1971_2008`: events 5; 180d avg 15.340%, median 15.760%, bullish 100.000%
- `post_gfc_2009_now`: events 3; 180d avg 5.384%, median 4.212%, bullish 100.000%

#### `jupiter_saturn_sextile`

- **Events:** 22 total; 13 train, 9 test
- **Exact-date span:** 1937-04-03 → 2024-02-06
- **Mapped weekend/holiday events:** 12
- **Best horizon:** 180d
- **All events:** avg 8.947%, median 11.153%, bullish 90.909%; baseline avg 5.731%
- **Train edge:** +0.645 pp; **test edge:** +6.930 pp

Regime read:

- `early_1927_1971`: events 9; 180d avg 7.269%, median 12.978%, bullish 88.889%
- `post_bretton_woods_1971_2008`: events 9; 180d avg 8.389%, median 10.040%, bullish 88.889%
- `post_gfc_2009_now`: events 4; 180d avg 13.978%, median 14.201%, bullish 100.000%

#### `jupiter_saturn_square`

- **Events:** 27 total; 15 train, 12 test
- **Exact-date span:** 1935-11-26 → 2025-06-15
- **Mapped weekend/holiday events:** 8
- **Best horizon:** 60d
- **All events:** avg 4.658%, median 5.022%, bullish 77.778%; baseline avg 1.902%
- **Train edge:** +2.592 pp; **test edge:** +2.962 pp

Regime read:


#### `jupiter_neptune_square`

- **Events:** 26 total; 16 train, 10 test
- **Exact-date span:** 1929-06-07 → 2025-06-19
- **Mapped weekend/holiday events:** 12
- **Best horizon:** 90d
- **All events:** avg 5.235%, median 5.943%, bullish 84.615%; baseline avg 2.825%
- **Train edge:** +2.124 pp; **test edge:** +2.867 pp

Regime read:

- `early_1927_1971`: events 12; 90d avg 5.343%, median 5.003%, bullish 83.333%
- `post_bretton_woods_1971_2008`: events 9; 90d avg 3.091%, median 2.706%, bullish 77.778%
- `post_gfc_2009_now`: events 5; 90d avg 8.836%, median 7.813%, bullish 100.000%

#### `pluto_saturn_sextile`

- **Events:** 13 total; 6 train, 7 test
- **Exact-date span:** 1942-06-09 → 2026-03-28
- **Mapped weekend/holiday events:** 4
- **Best horizon:** 30d
- **All events:** avg 2.922%, median 1.332%, bullish 84.615%; baseline avg 0.951%
- **Train edge:** +0.885 pp; **test edge:** +2.902 pp

Regime read:

- `early_1927_1971`: events 4; 30d avg 3.290%, median 2.931%, bullish 100.000%
- `post_bretton_woods_1971_2008`: events 5; 30d avg 0.324%, median 0.003%, bullish 60.000%
- `post_gfc_2009_now`: events 4; 30d avg 5.800%, median 2.903%, bullish 100.000%

#### `jupiter_pluto_square`

- **Events:** 25 total; 15 train, 10 test
- **Exact-date span:** 1928-03-31 → 2023-05-17
- **Mapped weekend/holiday events:** 5
- **Best horizon:** 30d
- **All events:** avg 2.218%, median 1.390%, bullish 80.000%; baseline avg 0.951%
- **Train edge:** +0.582 pp; **test edge:** +2.293 pp

Regime read:

- `early_1927_1971`: events 11; 30d avg 0.493%, median 0.613%, bullish 63.636%
- `post_bretton_woods_1971_2008`: events 8; 30d avg 4.675%, median 4.869%, bullish 87.500%
- `post_gfc_2009_now`: events 6; 30d avg 2.103%, median 1.028%, bullish 100.000%

#### `neptune_pluto_sextile`

- **Events:** 45 total; 32 train, 13 test
- **Exact-date span:** 1945-02-19 → 2026-06-03
- **Mapped weekend/holiday events:** 14
- **Best horizon:** 90d
- **All events:** avg 4.620%, median 4.411%, bullish 75.000%; baseline avg 2.825%
- **Train edge:** +2.379 pp; **test edge:** +0.237 pp

Regime read:

- `early_1927_1971`: events 21; 90d avg 5.311%, median 5.250%, bullish 66.667%
- `post_bretton_woods_1971_2008`: events 17; 90d avg 3.702%, median 3.759%, bullish 82.353%
- `post_gfc_2009_now`: events 7; 90d avg 4.803%, median 7.224%, bullish 83.333%

### Pressure candidates

#### `neptune_saturn_trine`

- **Events:** 16 total; 11 train, 5 test
- **Exact-date span:** 1929-03-06 → 2013-07-19
- **Mapped weekend/holiday events:** 4
- **Best horizon:** 180d
- **All events:** avg -3.238%, median -5.486%, bullish 43.750%; baseline avg 5.731%
- **Train edge:** -10.244 pp; **test edge:** -6.162 pp

Regime read:

- `early_1927_1971`: events 8; 180d avg -2.967%, median -3.054%, bullish 50.000%
- `post_bretton_woods_1971_2008`: events 5; 180d avg -12.204%, median -7.302%, bullish 0.000%
- `post_gfc_2009_now`: events 3; 180d avg 10.985%, median 11.175%, bullish 100.000%

#### `jupiter_uranus_sextile`

- **Events:** 22 total; 15 train, 7 test
- **Exact-date span:** 1929-08-07 → 2022-02-17
- **Mapped weekend/holiday events:** 6
- **Best horizon:** 90d
- **All events:** avg -3.206%, median -2.156%, bullish 36.364%; baseline avg 2.825%
- **Train edge:** -5.580 pp; **test edge:** -6.998 pp

Regime read:

- `early_1927_1971`: events 10; 90d avg -5.019%, median -3.717%, bullish 30.000%
- `post_bretton_woods_1971_2008`: events 9; 90d avg -1.762%, median -2.686%, bullish 33.333%
- `post_gfc_2009_now`: events 3; 90d avg -1.495%, median 3.470%, bullish 66.667%

#### `saturn_uranus_square`

- **Events:** 16 total; 10 train, 6 test
- **Exact-date span:** 1930-02-22 → 2022-10-04
- **Mapped weekend/holiday events:** 6
- **Best horizon:** 180d
- **All events:** avg -2.625%, median 2.254%, bullish 56.250%; baseline avg 5.731%
- **Train edge:** -11.837 pp; **test edge:** -2.552 pp

Regime read:

- `early_1927_1971`: events 7; 180d avg -9.499%, median 1.330%, bullish 57.143%
- `post_bretton_woods_1971_2008`: events 6; 180d avg 1.608%, median 0.244%, bullish 50.000%
- `post_gfc_2009_now`: events 3; 180d avg 4.951%, median 14.704%, bullish 66.667%

#### `jupiter_pluto_opposition`

- **Events:** 12 total; 7 train, 5 test
- **Exact-date span:** 1937-05-29 → 2014-01-31
- **Mapped weekend/holiday events:** 6
- **Best horizon:** 90d
- **All events:** avg -2.851%, median -1.227%, bullish 50.000%; baseline avg 2.825%
- **Train edge:** -5.171 pp; **test edge:** -6.384 pp

Regime read:

- `early_1927_1971`: events 6; 90d avg -2.284%, median -2.414%, bullish 50.000%
- `post_bretton_woods_1971_2008`: events 4; 90d avg -8.636%, median -7.611%, bullish 25.000%
- `post_gfc_2009_now`: events 2; 90d avg 7.020%, median 7.020%, bullish 100.000%

#### `jupiter_uranus_square`

- **Events:** 24 total; 16 train, 8 test
- **Exact-date span:** 1930-09-05 → 2021-01-17
- **Mapped weekend/holiday events:** 7
- **Best horizon:** 180d
- **All events:** avg -1.260%, median 1.386%, bullish 54.167%; baseline avg 5.731%
- **Train edge:** -8.443 pp; **test edge:** -4.085 pp

Regime read:

- `early_1927_1971`: events 11; 180d avg -5.242%, median 2.620%, bullish 54.545%
- `post_bretton_woods_1971_2008`: events 10; 180d avg -0.829%, median -2.388%, bullish 40.000%
- `post_gfc_2009_now`: events 3; 180d avg 11.908%, median 14.346%, bullish 100.000%

#### `pluto_saturn_trine`

- **Events:** 13 total; 7 train, 6 test
- **Exact-date span:** 1937-03-26 → 2008-04-26
- **Mapped weekend/holiday events:** 5
- **Best horizon:** 180d
- **All events:** avg 0.392%, median 3.794%, bullish 61.538%; baseline avg 5.731%
- **Train edge:** -8.987 pp; **test edge:** -1.081 pp

Regime read:

- `early_1927_1971`: events 6; 180d avg -5.082%, median 0.123%, bullish 50.000%
- `post_bretton_woods_1971_2008`: events 7; 180d avg 5.084%, median 7.695%, bullish 71.429%
- `post_gfc_2009_now`: events 0; 180d avg n/a, median n/a, bullish n/a

#### `jupiter_uranus_trine`

- **Events:** 27 total; 16 train, 11 test
- **Exact-date span:** 1931-10-10 → 2019-12-15
- **Mapped weekend/holiday events:** 11
- **Best horizon:** 180d
- **All events:** avg 0.712%, median 3.020%, bullish 62.963%; baseline avg 5.731%
- **Train edge:** -7.017 pp; **test edge:** -2.112 pp

Regime read:

- `early_1927_1971`: events 12; 180d avg -0.426%, median 5.613%, bullish 58.333%
- `post_bretton_woods_1971_2008`: events 11; 180d avg 1.362%, median 0.852%, bullish 72.727%
- `post_gfc_2009_now`: events 4; 180d avg 2.336%, median 1.717%, bullish 50.000%

## Theme-level read

Feature individual bisa kuat tapi sample kecil. Theme bucket menggabungkan beberapa feature terkait untuk melihat apakah narasi lebih besar tetap tahan. Ini lebih cocok untuk teori kerja daripada entry/exit signal.

### Outer Big Cycles — anchored themes

| # | Theme / feature bucket | Events | Best horizon | Avg | Median | Bullish | Train edge | Test edge | Included features |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `jupiter_uranus_major` | 100 | 180d | 1.073% | 3.541% | 60.000% | -6.162 pp | -2.095 pp | `jupiter_uranus_conjunction`, `jupiter_uranus_opposition`, `jupiter_uranus_sextile`, `jupiter_uranus_square`, `jupiter_uranus_trine` |
| 2 | `saturn_pluto_major` | 53 | 60d | -0.922% | 0.960% | 55.769% | -4.974 pp | -0.111 pp | `pluto_saturn_conjunction`, `pluto_saturn_opposition`, `pluto_saturn_sextile`, `pluto_saturn_square`, `pluto_saturn_trine` |
| 3 | `jupiter_saturn_major` | 101 | 60d | 2.769% | 3.310% | 74.257% | +0.467 pp | +1.430 pp | `jupiter_saturn_conjunction`, `jupiter_saturn_opposition`, `jupiter_saturn_sextile`, `jupiter_saturn_square`, `jupiter_saturn_trine` |

### No-Moon Full Scan — anchored themes

| # | Theme / feature bucket | Events | Best horizon | Avg | Median | Bullish | Train edge | Test edge | Included features |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `saturn_pluto_major` | 52 | 180d | 0.709% | 2.700% | 58.824% | -8.531 pp | -0.008 pp | `pluto_saturn_conjunction`, `pluto_saturn_opposition`, `pluto_saturn_sextile`, `pluto_saturn_square`, `pluto_saturn_trine` |
| 2 | `jupiter_uranus_major` | 100 | 180d | 1.492% | 4.121% | 61.000% | -5.589 pp | -1.941 pp | `jupiter_uranus_conjunction`, `jupiter_uranus_opposition`, `jupiter_uranus_sextile`, `jupiter_uranus_square`, `jupiter_uranus_trine` |
| 3 | `jupiter_saturn_major` | 101 | 60d | 2.781% | 3.310% | 72.277% | +0.509 pp | +1.422 pp | `jupiter_saturn_conjunction`, `jupiter_saturn_opposition`, `jupiter_saturn_sextile`, `jupiter_saturn_square`, `jupiter_saturn_trine` |
| 4 | `saturn_personal_conjunction_pressure` | 367 | 30d | 0.329% | 0.993% | 56.131% | -0.795 pp | -0.340 pp | `mars_saturn_conjunction`, `mercury_saturn_conjunction`, `saturn_sun_conjunction`, `saturn_venus_conjunction` |
| 5 | `mercury_venus_cooldown` | 461 | 14d | 0.174% | 0.578% | 56.182% | -0.262 pp | -0.272 pp | `mercury_venus_conjunction`, `mercury_venus_sextile` |
| 6 | `jupiter_inner_boost` | 1030 | 30d | 0.595% | 1.111% | 59.515% | -0.542 pp | -0.065 pp | `jupiter_mars_conjunction`, `jupiter_mars_trine`, `jupiter_mercury_conjunction`, `jupiter_mercury_trine`, `jupiter_sun_conjunction` +3 |
| 7 | `mars_inner_trigger_all` | 1057 | 3d | 0.270% | 0.284% | 57.994% | +0.089 pp | +0.310 pp | `mars_mercury_conjunction`, `mars_mercury_sextile`, `mars_mercury_trine`, `mars_sun_conjunction`, `mars_sun_sextile` +4 |
| 8 | `venus_opposition_riskon` | 441 | 14d | 0.217% | 0.689% | 57.370% | -0.237 pp | -0.203 pp | `jupiter_venus_opposition`, `mars_venus_opposition`, `pluto_venus_opposition`, `saturn_venus_opposition`, `uranus_venus_opposition` |
| 9 | `uranus_hard_to_personal` | 1449 | 60d | 1.659% | 2.372% | 62.932% | -0.354 pp | -0.068 pp | `mars_uranus_conjunction`, `mars_uranus_opposition`, `mars_uranus_square`, `mercury_uranus_conjunction`, `mercury_uranus_opposition` +7 |
| 10 | `saturn_hard_to_personal` | 1418 | 3d | 0.185% | 0.216% | 57.052% | +0.032 pp | +0.183 pp | `mars_saturn_conjunction`, `mars_saturn_opposition`, `mars_saturn_square`, `mercury_saturn_conjunction`, `mercury_saturn_opposition` +7 |
| 11 | `pluto_hard_to_personal` | 1474 | 7d | 0.093% | 0.302% | 54.817% | -0.197 pp | -0.013 pp | `mars_pluto_conjunction`, `mars_pluto_opposition`, `mars_pluto_square`, `mercury_pluto_conjunction`, `mercury_pluto_opposition` +7 |
| 12 | `mars_inner_trigger_soft` | 610 | 3d | 0.223% | 0.272% | 58.689% | -0.009 pp | +0.341 pp | `mars_mercury_conjunction`, `mars_mercury_trine`, `mars_sun_conjunction`, `mars_sun_trine`, `mars_venus_conjunction` +1 |

## Interpretasi radikal tapi disiplin

### Saturn–Neptune: square konstruktif, trine pressure

Hasil paling provokatif adalah split Saturn–Neptune. Square tampil sebagai repair/re-rating window yang kuat di 180d, sementara trine tampil sebagai underperformance candidate. Ini tidak cocok dengan pembacaan simbolik dangkal `trine baik, square buruk`. Secara data, konfigurasi tension justru bisa bertepatan dengan fase penyesuaian yang kemudian direprice positif, sedangkan harmoni Saturn–Neptune bisa bertepatan dengan stagnasi atau disillusionment market.

### Jupiter tidak selalu risk-on

Jupiter–Uranus conjunction terlihat konstruktif, tapi Jupiter–Uranus sextile justru pressure candidate. Jupiter–Saturn sextile konstruktif, sementara Jupiter–Saturn opposition lemah. Jadi yang terbaca bukan `planet baik/buruk`, melainkan kombinasi pair + aspect + horizon.

### SPX berbeda dari BTC

BTC cenderung lebih sensitif terhadap release/risk-on yang cepat. SPX, karena komposisi large-cap, earnings cycle, buyback, dan policy regime, punya drift yang membuat banyak event positif nominal tapi tidak outperformance. Maka theme yang tampak bullish di BTC bisa menjadi underperformance relatif di SPX.

### Personal planets sebagai trigger, bukan siklus utama

Mars/Sun/Mercury/Venus feature yang konstruktif pada 180d kemungkinan bukan `penyebab`, melainkan marker fase market yang lebih besar. Ini butuh validasi tambahan karena no-moon full scan punya multiple testing jauh lebih berat.

## Anti-overfitting notes

- Multiple testing sangat besar: 24 feature di outer scan dan 145 feature di no-moon full scan, plus horizon dan theme bucket.
- Sample aspek planet luar kecil; angka terlihat ekstrem bisa berubah setelah beberapa dekade data baru.
- Average bisa didominasi crash/rebound; median dan bullish rate wajib dilihat bersama.
- Train/test split kronologis membantu, tapi bukan pengganti pre-registration.
- Mapping weekend/libur ke trading day berikutnya membuat penelitian dapat dieksekusi di pasar saham, tapi dapat menggeser interpretasi astrologis 1–3 hari.
- `^GSPC` bukan tradable instrument; perlu validasi di SPY, ES futures continuous, Dow, Nasdaq, equal-weight S&P, dan international equities.

## Working theory untuk SPX

1. **Constructive expansion / repair:** Saturn–Neptune square, Jupiter–Saturn sextile, Jupiter–Uranus conjunction.
2. **Pressure / underperformance:** Saturn–Neptune trine, Jupiter–Uranus sextile, Saturn–Uranus square, Jupiter–Saturn opposition.
3. **Cooldown:** Mercury–Venus conjunction/sextile bucket menunjukkan mild underperformance di 14d, konsisten train/test.
4. **BTC-to-SPX transfer:** Venus opposition risk-on tidak transfer bersih; SPX justru short-horizon underperformance relatif baseline.
5. **Use-case praktis:** bukan buy/sell, tapi watchlist kalender untuk menguji apakah window tertentu bertepatan dengan re-rating, compression, atau volatility clustering.

## Next research steps

- Re-run exact same hypothesis on `SPY`, `ES=F` / continuous futures if available, `^DJI`, `^IXIC`, `RSP`, and global equity indices.
- Freeze top rules from this paper, then test forward on 2026–2028 without re-optimizing.
- Add bootstrap/permutation test: compare exact aspect dates against random dates matched by decade/month/weekday.
- Add drawdown and volatility metrics, not only forward return.
- Build future watch calendar per theory category, clearly labeled as hypothesis watchlist.

## Appendix A. Output artifacts

- Raw JSON: `/tmp/radical-spx500-astro-search-v011.json`
- Markdown paper: `/tmp/spx500-radical-astrology-research-hermetic-alpha-v011.md`
- PDF paper: `/tmp/spx500-radical-astrology-research-hermetic-alpha-v011.pdf`

## Disclaimer

This is exploratory research and library dogfooding only. It is not investment advice, not a trading system, and not evidence of astrological causality. Any market use requires independent validation, risk management, and pre-registered forward testing.
