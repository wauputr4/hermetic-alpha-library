---
title: "Gold/XAU Astrology Regime, Forward-Return, and 5-Year Cycle Study"
subtitle: "Hermetic Alpha v0.1.1 exact-window event study on GC=F with GLD/IAU validation summaries"
author: "Hermes Agent for Wauputra"
date: "2026-06-05"
geometry: margin=0.75in
fontsize: 9pt
---

# Executive Summary

This paper expands the initial Gold/XAU experiment into a more complete, repo-ready research package. It applies the same Hermetic Alpha workflow previously used for Bitcoin and S&P 500: convert planetary aspects into exact-date market events, compare those events against Gold futures returns and regime labels, then freeze a simple interpretation map for a 2026-2031 watchlist.

The report is intentionally exploratory. It does not claim astrology causes price movement and it is not financial advice. The useful output is a set of testable hypotheses: which aspect families coincided with Gold bear pressure, peak-risk, bottom/reversal zones, and above/below-baseline forward returns.

Main takeaways:

- Primary data: Yahoo Finance `GC=F` / COMEX Gold Futures, 2000-08-30 to 2026-06-05, 6,465 daily candles. Yahoo did not return a usable `XAUUSD=X` series in the run, so futures are the primary proxy.

- Major regime labels: 4 drawdown cycles of at least 20%, with bear/pressure days equal to 29.374% of the sample.

- Gold is not S&P 500. Stress themes are not automatically bearish because Gold can receive safe-haven flows. The best practical reading is four buckets: pressure/volatility, peak-risk, bottom/reversal watch, and constructive support.

- The most consistent constructive forward-return themes in this run include `jupiter_saturn`, `sun_venus`, outer-outer soft themes, and selected Mars/Saturn or Mars/Uranus sextile/trine features.

- The clearest instability/underperformance candidate is `jupiter_uranus`, especially around 30-day horizons, where test-period behavior lagged baseline.

- The 2026-2031 future table is a watchlist, not a forecast. 2027 has the densest mix of peak-risk and constructive windows; it should be monitored as a high-information year rather than interpreted one-directionally.

# Research Questions

1. Which large-cycle aspect themes are over-represented during Gold bear/pressure regimes?

2. Which themes cluster around historically defined peak-risk and bottom/reversal windows?

3. Which exact aspect windows show same-direction train/test forward-return edges versus Gold baseline?

4. Can those findings be converted into a simple 5-year watchlist without pretending to predict price?

# Data Provenance

| Item | Value |
| --- | --- |
| Primary asset | `GC=F` / COMEX Gold Futures via Yahoo Finance |
| Requested start | 1990-01-01 |
| Actual start | 2000-08-30 |
| Actual end | 2026-06-05 |
| Candles | 6,465 |
| Train/test split | Train through 2013-12-31 (3,341 candles); test after (3,124 candles) |
| Validation proxies | `GLD`, `IAU` summary checks |
| Library | `hermetic-alpha` / `hermetic-alpha-library` v0.1.1 workspace |

Why `GC=F`: the first attempted spot-like Yahoo symbol, `XAUUSD=X`, returned a market-data provider error. `GC=F` is not identical to spot XAU/USD; it can include futures contract and roll artifacts. The result should be treated as a Gold-proxy study until a cleaner spot source is added.

# Methodology

## Aspect event construction

- Generate daily planetary positions over the asset date range.
- Scan conjunction, opposition, trine, square, and sextile aspects.
- Collapse consecutive active aspect days into one event window.
- Use the minimum-orb day as the exact event date.
- Map non-trading exact dates to the same or next available Gold candle within a documented 3-calendar-day tolerance.
- Measure forward returns from exact event dates only, avoiding the mistake of counting every active day in a multi-day aspect as an independent observation.

## Universes scanned

| Universe | Bodies | Exact windows mapped | Raw aspect days | Feature buckets | Theme buckets |
| --- | --- | --- | --- | --- | --- |
| Outer big cycles | jupiter, saturn, uranus, neptune, pluto | 179 | 12431 | 17 | 27 |
| Full no-moon scan | sun, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto | 4812 | 36093 | 137 | 107 |

## Regime labels

Regimes are hindsight labels based on >=20% drawdown cycles. `bear` is the peak-to-bottom decline. `peak_window_30td` and `bottom_window_30td` are +/-30 trading-day windows around detected major peaks/bottoms. `pre_peak_30td` and `post_bottom_30td` are one-sided context labels.

## Return scoring

Forward-return horizons are 3, 7, 14, 30, 60, 90, and 180 trading days. Each event return is compared against the same-asset baseline for the same horizon. A candidate is more interesting when train edge and test edge have the same direction, median does not contradict average, and event count is not tiny.

# Gold Baseline

| Horizon | Valid days | Avg | Median | Bullish | Min | Max |
| --- | --- | --- | --- | --- | --- | --- |
| 3d | 6462 | 0.147% | 0.167% | 54.287% | -12.809% | 13.996% |
| 7d | 6458 | 0.345% | 0.393% | 56.302% | -14.708% | 21.934% |
| 14d | 6451 | 0.688% | 0.596% | 56.751% | -18.138% | 19.523% |
| 30d | 6435 | 1.479% | 1.113% | 58.135% | -19.748% | 25.620% |
| 60d | 6405 | 2.984% | 2.604% | 63.700% | -22.165% | 33.891% |
| 90d | 6375 | 4.564% | 4.223% | 68.894% | -24.907% | 45.500% |
| 180d | 6285 | 9.350% | 8.306% | 72.745% | -31.890% | 64.646% |

Gold has a positive long-run drift in this sample, especially at 90d and 180d horizons. This is why raw positive post-event returns are not sufficient; the event must beat Gold baseline to be interesting.

## Detected >=20% drawdown cycles

| Peak | Bottom | Recovery | Max drawdown | Peak-to-bottom trading days |
| --- | --- | --- | --- | --- |
| 2006-05-11 | 2006-10-04 | 2007-09-19 | -21.923% | 101 |
| 2008-03-18 | 2008-11-13 | 2009-09-11 | -29.735% | 168 |
| 2011-08-22 | 2015-12-17 | 2020-07-23 | -44.364% | 1088 |
| 2020-08-06 | 2022-09-26 | 2023-12-01 | -20.873% | 538 |

Base day shares:

| Label | Share of trading days |
| --- | --- |
| bear | 29.374% |
| bottom_window_30td | 3.774% |
| bull | 70.626% |
| peak_window_30td | 3.774% |
| post_bottom_30td | 1.918% |
| pre_peak_30td | 1.918% |

# Regime Enrichment Results

The enrichment tables show which aspect/theme buckets appeared inside a regime label more often than the label baseline. `Lift` > 1 means the bucket appeared more frequently inside that label than random trading days did. The z-score is approximate and used only for screening.

## Bear / pressure: outer big-cycle themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `jupiter_uranus` | 26 | 12 | 46.154% | 29.374% | 1.571 | 1.879 | 14 | 0.129% | 0.490% |
| 2 | `jupiter_uranus_instability` | 26 | 12 | 46.154% | 29.374% | 1.571 | 1.879 | 14 | 0.129% | 0.490% |
| 3 | `jupiter_trine` | 32 | 11 | 34.375% | 29.374% | 1.170 | 0.621 | 90 | -1.494% | -0.970% |
| 4 | `jupiter_sextile` | 24 | 8 | 33.333% | 29.374% | 1.135 | 0.426 | 14 | 1.132% | 0.003% |
| 5 | `saturn_trine` | 24 | 8 | 33.333% | 29.374% | 1.135 | 0.426 | 180 | -1.735% | -6.188% |
| 6 | `aspect:square` | 44 | 14 | 31.818% | 29.374% | 1.083 | 0.356 | 180 | 1.978% | 2.248% |
| 7 | `planet:uranus` | 54 | 17 | 31.481% | 29.374% | 1.072 | 0.340 | 90 | 0.077% | 2.615% |
| 8 | `aspect:sextile` | 41 | 13 | 31.707% | 29.374% | 1.079 | 0.328 | 60 | 3.007% | 2.432% |
| 9 | `aspect_family:soft` | 92 | 28 | 30.435% | 29.374% | 1.036 | 0.223 | 60 | 0.983% | 1.329% |
| 10 | `pair_family:outer_outer_soft` | 92 | 28 | 30.435% | 29.374% | 1.036 | 0.223 | 60 | 0.983% | 1.329% |

## Bear / pressure: full no-moon themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `jupiter_uranus` | 26 | 12 | 46.154% | 29.374% | 1.571 | 1.879 | 30 | -0.643% | -2.276% |
| 2 | `jupiter_uranus_instability` | 26 | 12 | 46.154% | 29.374% | 1.571 | 1.879 | 30 | -0.643% | -2.276% |
| 3 | `neptune_opposition` | 104 | 39 | 37.500% | 29.374% | 1.277 | 1.820 | 30 | -0.378% | -1.525% |
| 4 | `pluto_trine` | 196 | 68 | 34.694% | 29.374% | 1.181 | 1.635 | 60 | -0.348% | -1.397% |
| 5 | `saturn_conjunction` | 97 | 34 | 35.052% | 29.374% | 1.193 | 1.228 | 180 | 1.526% | 0.977% |
| 6 | `uranus_opposition` | 104 | 36 | 34.615% | 29.374% | 1.178 | 1.174 | 90 | 2.935% | 1.735% |
| 7 | `pluto_square` | 209 | 68 | 32.536% | 29.374% | 1.108 | 1.004 | 60 | -0.037% | -0.785% |
| 8 | `venus_opposition` | 143 | 47 | 32.867% | 29.374% | 1.119 | 0.917 | 60 | -0.640% | -1.376% |
| 9 | `mars_pluto` | 119 | 39 | 32.773% | 29.374% | 1.116 | 0.814 | 30 | -0.978% | -0.690% |
| 10 | `uranus_trine` | 204 | 65 | 31.863% | 29.374% | 1.085 | 0.781 | 90 | 0.135% | 0.608% |

## Peak-risk window: outer big-cycle themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `jupiter_uranus` | 26 | 2 | 7.692% | 3.774% | 2.038 | 1.048 | 14 | 0.129% | 0.490% |
| 2 | `jupiter_uranus_instability` | 26 | 2 | 7.692% | 3.774% | 2.038 | 1.048 | 14 | 0.129% | 0.490% |
| 3 | `planet:uranus` | 54 | 3 | 5.556% | 3.774% | 1.472 | 0.687 | 90 | 0.077% | 2.615% |
| 4 | `planet:pluto` | 60 | 3 | 5.000% | 3.774% | 1.325 | 0.498 | 90 | 0.394% | 2.102% |
| 5 | `aspect:sextile` | 41 | 2 | 4.878% | 3.774% | 1.292 | 0.371 | 60 | 3.007% | 2.432% |
| 6 | `aspect_family:soft` | 92 | 4 | 4.348% | 3.774% | 1.152 | 0.289 | 60 | 0.983% | 1.329% |
| 7 | `pair_family:outer_outer_soft` | 92 | 4 | 4.348% | 3.774% | 1.152 | 0.289 | 60 | 0.983% | 1.329% |
| 8 | `outer_soft_release` | 92 | 4 | 4.348% | 3.774% | 1.152 | 0.289 | 60 | 0.983% | 1.329% |
| 9 | `aspect:square` | 44 | 2 | 4.545% | 3.774% | 1.204 | 0.268 | 180 | 1.978% | 2.248% |
| 10 | `jupiter_sextile` | 24 | 1 | 4.167% | 3.774% | 1.104 | 0.101 | 14 | 1.132% | 0.003% |

## Peak-risk window: full no-moon themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `pluto_opposition` | 103 | 9 | 8.738% | 3.774% | 2.315 | 2.643 | 180 | 1.308% | 1.966% |
| 2 | `aspect:opposition` | 516 | 29 | 5.620% | 3.774% | 1.489 | 2.200 | 3 | 0.030% | 0.110% |
| 3 | `mars_square` | 252 | 15 | 5.952% | 3.774% | 1.577 | 1.814 | 7 | 0.603% | 0.104% |
| 4 | `sun_opposition` | 135 | 9 | 6.667% | 3.774% | 1.766 | 1.764 | 3 | 0.481% | 0.183% |
| 5 | `mercury_opposition` | 157 | 10 | 6.369% | 3.774% | 1.688 | 1.706 | 90 | 1.021% | 0.659% |
| 6 | `mercury_trine` | 329 | 18 | 5.471% | 3.774% | 1.450 | 1.615 | 60 | 0.624% | 0.508% |
| 7 | `jupiter_opposition` | 110 | 7 | 6.364% | 3.774% | 1.686 | 1.425 | 180 | -0.346% | -2.039% |
| 8 | `pluto_trine` | 196 | 11 | 5.612% | 3.774% | 1.487 | 1.350 | 60 | -0.348% | -1.397% |
| 9 | `mars_mercury` | 196 | 11 | 5.612% | 3.774% | 1.487 | 1.350 | 7 | 0.004% | -0.228% |
| 10 | `venus_opposition` | 143 | 8 | 5.594% | 3.774% | 1.482 | 1.142 | 60 | -0.640% | -1.376% |

## Pre-peak 30 trading days: outer big-cycle themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `planet:uranus` | 54 | 2 | 3.704% | 1.918% | 1.931 | 0.957 | 90 | 0.077% | 2.615% |
| 2 | `jupiter_uranus` | 26 | 1 | 3.846% | 1.918% | 2.005 | 0.717 | 14 | 0.129% | 0.490% |
| 3 | `jupiter_uranus_instability` | 26 | 1 | 3.846% | 1.918% | 2.005 | 0.717 | 14 | 0.129% | 0.490% |
| 4 | `jupiter_trine` | 32 | 1 | 3.125% | 1.918% | 1.629 | 0.498 | 90 | -1.494% | -0.970% |
| 5 | `aspect:square` | 44 | 1 | 2.273% | 1.918% | 1.185 | 0.172 | 180 | 1.978% | 2.248% |
| 6 | `aspect:trine` | 51 | 1 | 1.961% | 1.918% | 1.022 | 0.022 | 180 | -0.580% | -3.745% |
| 7 | `planet:pluto` | 60 | 1 | 1.667% | 1.918% | 0.869 | -0.142 | 90 | 0.394% | 2.102% |
| 8 | `aspect_family:hard` | 84 | 1 | 1.190% | 1.918% | 0.621 | -0.486 | 180 | 3.563% | 0.972% |
| 9 | `pair_family:outer_outer_hard` | 84 | 1 | 1.190% | 1.918% | 0.621 | -0.486 | 180 | 3.563% | 0.972% |
| 10 | `outer_hard_pressure` | 84 | 1 | 1.190% | 1.918% | 0.621 | -0.486 | 180 | 3.563% | 0.972% |

## Pre-peak 30 trading days: full no-moon themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `pluto_opposition` | 103 | 6 | 5.825% | 1.918% | 3.037 | 2.891 | 180 | 1.308% | 1.966% |
| 2 | `mars_pluto_capitulation` | 63 | 3 | 4.762% | 1.918% | 2.483 | 1.646 | 180 | -0.121% | -0.561% |
| 3 | `aspect:opposition` | 516 | 15 | 2.907% | 1.918% | 1.516 | 1.638 | 3 | 0.030% | 0.110% |
| 4 | `sun_opposition` | 135 | 5 | 3.704% | 1.918% | 1.931 | 1.513 | 3 | 0.481% | 0.183% |
| 5 | `saturn_opposition` | 101 | 4 | 3.960% | 1.918% | 2.065 | 1.496 | 60 | -0.663% | -1.010% |
| 6 | `neptune_conjunction` | 105 | 4 | 3.810% | 1.918% | 1.986 | 1.413 | 90 | -3.509% | -1.148% |
| 7 | `mars_mercury` | 196 | 6 | 3.061% | 1.918% | 1.596 | 1.167 | 7 | 0.004% | -0.228% |
| 8 | `mercury_opposition` | 157 | 5 | 3.185% | 1.918% | 1.660 | 1.157 | 90 | 1.021% | 0.659% |
| 9 | `mars_sextile` | 253 | 7 | 2.767% | 1.918% | 1.443 | 0.984 | 180 | 0.661% | 1.406% |
| 10 | `sun_sextile` | 271 | 7 | 2.583% | 1.918% | 1.347 | 0.798 | 30 | 0.392% | 0.541% |

## Bottom / reversal window: outer big-cycle themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `aspect:square` | 44 | 5 | 11.364% | 3.774% | 3.011 | 2.642 | 180 | 1.978% | 2.248% |
| 2 | `aspect_family:hard` | 84 | 6 | 7.143% | 3.774% | 1.893 | 1.620 | 180 | 3.563% | 0.972% |
| 3 | `pair_family:outer_outer_hard` | 84 | 6 | 7.143% | 3.774% | 1.893 | 1.620 | 180 | 3.563% | 0.972% |
| 4 | `outer_hard_pressure` | 84 | 6 | 7.143% | 3.774% | 1.893 | 1.620 | 180 | 3.563% | 0.972% |
| 5 | `planet:uranus` | 54 | 4 | 7.407% | 3.774% | 1.963 | 1.401 | 90 | 0.077% | 2.615% |
| 6 | `planet:neptune` | 55 | 4 | 7.273% | 3.774% | 1.927 | 1.361 | 180 | 2.377% | 5.787% |
| 7 | `jupiter_uranus` | 26 | 2 | 7.692% | 3.774% | 2.038 | 1.048 | 14 | 0.129% | 0.490% |
| 8 | `jupiter_uranus_instability` | 26 | 2 | 7.692% | 3.774% | 2.038 | 1.048 | 14 | 0.129% | 0.490% |
| 9 | `pair_family:outer_outer` | 176 | 9 | 5.114% | 3.774% | 1.355 | 0.932 | 180 | 1.477% | 1.741% |
| 10 | `jupiter_square` | 30 | 2 | 6.667% | 3.774% | 1.766 | 0.831 | 180 | 3.741% | 6.657% |

## Bottom / reversal window: full no-moon themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `uranus_trine` | 204 | 15 | 7.353% | 3.774% | 1.948 | 2.682 | 90 | 0.135% | 0.608% |
| 2 | `pair_family:outer_outer_hard` | 84 | 7 | 8.333% | 3.774% | 2.208 | 2.193 | 180 | 3.417% | 0.418% |
| 3 | `neptune_square` | 212 | 14 | 6.604% | 3.774% | 1.750 | 2.162 | 60 | 1.160% | 1.153% |
| 4 | `pluto_conjunction` | 101 | 7 | 6.931% | 3.774% | 1.836 | 1.665 | 30 | 1.653% | 1.596% |
| 5 | `jupiter_sextile` | 202 | 12 | 5.941% | 3.774% | 1.574 | 1.616 | 14 | -0.192% | -0.390% |
| 6 | `pair_family:outer_personal_soft` | 1612 | 73 | 4.529% | 3.774% | 1.200 | 1.589 | 14 | -0.036% | -0.292% |
| 7 | `uranus_opposition` | 104 | 7 | 6.731% | 3.774% | 1.783 | 1.582 | 90 | 2.935% | 1.735% |
| 8 | `outer_soft_release` | 1678 | 75 | 4.470% | 3.774% | 1.184 | 1.495 | 14 | -0.050% | -0.241% |
| 9 | `aspect:square` | 1017 | 47 | 4.621% | 3.774% | 1.224 | 1.418 | 7 | 0.284% | 0.035% |
| 10 | `aspect:trine` | 972 | 45 | 4.630% | 3.774% | 1.227 | 1.400 | 7 | -0.031% | -0.136% |

## Post-bottom 30 trading days: outer big-cycle themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `aspect:square` | 44 | 3 | 6.818% | 1.918% | 3.555 | 2.370 | 180 | 1.978% | 2.248% |
| 2 | `planet:uranus` | 54 | 3 | 5.556% | 1.918% | 2.897 | 1.949 | 90 | 0.077% | 2.615% |
| 3 | `aspect_family:hard` | 84 | 3 | 3.571% | 1.918% | 1.862 | 1.105 | 180 | 3.563% | 0.972% |
| 4 | `pair_family:outer_outer_hard` | 84 | 3 | 3.571% | 1.918% | 1.862 | 1.105 | 180 | 3.563% | 0.972% |
| 5 | `outer_hard_pressure` | 84 | 3 | 3.571% | 1.918% | 1.862 | 1.105 | 180 | 3.563% | 0.972% |
| 6 | `jupiter_sextile` | 24 | 1 | 4.167% | 1.918% | 2.172 | 0.803 | 14 | 1.132% | 0.003% |
| 7 | `jupiter_uranus` | 26 | 1 | 3.846% | 1.918% | 2.005 | 0.717 | 14 | 0.129% | 0.490% |
| 8 | `jupiter_uranus_instability` | 26 | 1 | 3.846% | 1.918% | 2.005 | 0.717 | 14 | 0.129% | 0.490% |
| 9 | `jupiter_saturn` | 27 | 1 | 3.704% | 1.918% | 1.931 | 0.676 | 180 | 2.890% | 7.260% |
| 10 | `jupiter_square` | 30 | 1 | 3.333% | 1.918% | 1.738 | 0.565 | 180 | 3.741% | 6.657% |

## Post-bottom 30 trading days: full no-moon themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `pluto_conjunction` | 101 | 6 | 5.941% | 1.918% | 3.097 | 2.947 | 30 | 1.653% | 1.596% |
| 2 | `mars_conjunction` | 134 | 6 | 4.478% | 1.918% | 2.334 | 2.160 | 90 | -0.943% | -1.358% |
| 3 | `saturn_square` | 203 | 8 | 3.941% | 1.918% | 2.055 | 2.101 | 3 | 0.052% | 0.061% |
| 4 | `uranus_square` | 209 | 8 | 3.828% | 1.918% | 1.996 | 2.013 | 180 | 1.161% | 0.148% |
| 5 | `neptune_square` | 212 | 8 | 3.774% | 1.918% | 1.967 | 1.970 | 60 | 1.160% | 1.153% |
| 6 | `sun_venus` | 32 | 2 | 6.250% | 1.918% | 3.259 | 1.787 | 60 | 0.429% | 2.246% |
| 7 | `sun_venus_relief` | 32 | 2 | 6.250% | 1.918% | 3.259 | 1.787 | 60 | 0.429% | 2.246% |
| 8 | `aspect:square` | 1017 | 27 | 2.655% | 1.918% | 1.384 | 1.713 | 7 | 0.284% | 0.035% |
| 9 | `venus_conjunction` | 240 | 8 | 3.333% | 1.918% | 1.738 | 1.599 | 60 | 0.522% | 0.461% |
| 10 | `aspect:conjunction` | 757 | 20 | 2.642% | 1.918% | 1.377 | 1.452 | 180 | -0.250% | -0.619% |

## Bull / constructive background: outer big-cycle themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `aspect:opposition` | 26 | 21 | 80.769% | 70.626% | 1.144 | 1.135 | 30 | -0.330% | 0.080% |
| 2 | `jupiter_neptune` | 31 | 24 | 77.419% | 70.626% | 1.096 | 0.830 | 180 | 3.810% | 1.142% |
| 3 | `jupiter_neptune_liquidity` | 31 | 24 | 77.419% | 70.626% | 1.096 | 0.830 | 180 | 3.810% | 1.142% |
| 4 | `jupiter_square` | 30 | 23 | 76.667% | 70.626% | 1.086 | 0.726 | 180 | 3.741% | 6.657% |
| 5 | `jupiter_pluto` | 30 | 23 | 76.667% | 70.626% | 1.086 | 0.726 | 3 | 0.031% | 0.089% |
| 6 | `jupiter_pluto_power` | 30 | 23 | 76.667% | 70.626% | 1.086 | 0.726 | 3 | 0.031% | 0.089% |
| 7 | `aspect_family:hard` | 84 | 62 | 73.810% | 70.626% | 1.045 | 0.641 | 180 | 3.563% | 0.972% |
| 8 | `pair_family:outer_outer_hard` | 84 | 62 | 73.810% | 70.626% | 1.045 | 0.641 | 180 | 3.563% | 0.972% |
| 9 | `outer_hard_pressure` | 84 | 62 | 73.810% | 70.626% | 1.045 | 0.641 | 180 | 3.563% | 0.972% |
| 10 | `planet:saturn` | 74 | 54 | 72.973% | 70.626% | 1.033 | 0.443 | 180 | 1.723% | 5.675% |

## Bull / constructive background: full no-moon themes

| Rank | Bucket | Events | Inside label | Rate | Baseline | Lift | z | Best h | Train edge | Test edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `neptune_conjunction` | 105 | 81 | 77.143% | 70.626% | 1.092 | 1.466 | 90 | -3.509% | -1.148% |
| 2 | `saturn_opposition` | 101 | 77 | 76.238% | 70.626% | 1.079 | 1.238 | 60 | -0.663% | -1.010% |
| 3 | `neptune_sextile` | 208 | 155 | 74.519% | 70.626% | 1.055 | 1.233 | 60 | 0.273% | 1.160% |
| 4 | `saturn_trine` | 210 | 156 | 74.286% | 70.626% | 1.052 | 1.164 | 180 | -0.167% | -1.099% |
| 5 | `planet:mercury` | 1445 | 1040 | 71.972% | 70.626% | 1.019 | 1.123 | 60 | 0.553% | 0.052% |
| 6 | `pluto_sextile` | 219 | 162 | 73.973% | 70.626% | 1.047 | 1.087 | 7 | -0.269% | -0.043% |
| 7 | `uranus_conjunction` | 102 | 77 | 75.490% | 70.626% | 1.069 | 1.078 | 90 | -1.593% | -1.518% |
| 8 | `uranus_sextile` | 205 | 151 | 73.659% | 70.626% | 1.043 | 0.953 | 180 | 0.591% | 0.897% |
| 9 | `aspect:sextile` | 1051 | 755 | 71.836% | 70.626% | 1.017 | 0.861 | 90 | 0.104% | 0.498% |
| 10 | `jupiter_neptune` | 31 | 24 | 77.419% | 70.626% | 1.096 | 0.830 | 180 | 3.810% | 1.142% |

# Forward-Return Results

These tables rank candidates by robust same-direction train/test edge. Positive candidates are not necessarily trade signals; they are hypothesis candidates for further validation. Negative candidates are underperformance or caution themes versus Gold baseline.

## Robust bullish / constructive themes

| Rank | Bucket | Events | Best horizon | Train edge | Test edge | Avg return | Median | Bullish | Median agrees |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `jupiter_saturn` | 27 | 180d | 2.775% | 7.260% | 14.023% | 12.098% | 80.769% | yes |
| 2 | `sun_venus` | 32 | 60d | 0.429% | 2.246% | 4.321% | 4.514% | 81.250% | yes |
| 3 | `sun_venus_relief` | 32 | 60d | 0.429% | 2.246% | 4.321% | 4.514% | 81.250% | yes |
| 4 | `pluto_opposition` | 103 | 180d | 1.308% | 1.966% | 10.965% | 8.925% | 77.670% | yes |
| 5 | `uranus_opposition` | 104 | 90d | 2.935% | 1.735% | 6.922% | 6.805% | 77.885% | yes |
| 6 | `pluto_conjunction` | 101 | 30d | 1.653% | 1.596% | 3.104% | 2.989% | 69.307% | yes |
| 7 | `pair_family:outer_outer` | 176 | 180d | 1.348% | 1.558% | 10.794% | 9.658% | 73.529% | yes |
| 8 | `saturn_sextile` | 206 | 90d | 0.953% | 1.468% | 5.778% | 5.436% | 73.267% | yes |
| 9 | `neptune_trine` | 202 | 180d | 0.272% | 1.463% | 10.139% | 9.258% | 74.490% | yes |
| 10 | `mars_sextile` | 253 | 180d | 0.661% | 1.406% | 10.355% | 9.793% | 74.899% | yes |
| 11 | `pair_family:outer_outer_soft` | 92 | 60d | 1.061% | 1.384% | 4.203% | 2.667% | 66.667% | yes |
| 12 | `neptune_sextile` | 208 | 60d | 0.273% | 1.160% | 3.696% | 3.040% | 69.118% | yes |
| 13 | `neptune_square` | 212 | 60d | 1.160% | 1.153% | 4.141% | 3.493% | 67.619% | yes |
| 14 | `jupiter_neptune` | 31 | 180d | 3.810% | 1.142% | 12.042% | 10.761% | 83.871% | yes |
| 15 | `jupiter_neptune_liquidity` | 31 | 180d | 3.810% | 1.142% | 12.042% | 10.761% | 83.871% | yes |
| 16 | `mercury_venus` | 120 | 180d | 0.114% | 1.068% | 9.929% | 9.724% | 76.923% | yes |
| 17 | `mars_uranus` | 119 | 180d | 0.849% | 1.031% | 10.283% | 9.793% | 74.783% | yes |
| 18 | `saturn_conjunction` | 97 | 180d | 1.526% | 0.977% | 10.622% | 9.884% | 67.742% | yes |

## Robust bearish / underperforming themes

| Rank | Bucket | Events | Best horizon | Train edge | Test edge | Avg return | Median | Bullish | Median agrees |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `jupiter_uranus` | 26 | 30d | -0.643% | -2.276% | 0.208% | -0.281% | 42.308% | yes |
| 2 | `jupiter_uranus_instability` | 26 | 30d | -0.643% | -2.276% | 0.208% | -0.281% | 42.308% | yes |
| 3 | `jupiter_opposition` | 110 | 180d | -0.346% | -2.039% | 8.268% | 6.895% | 67.593% | yes |
| 4 | `neptune_opposition` | 104 | 30d | -0.378% | -1.525% | 0.594% | 0.697% | 56.731% | yes |
| 5 | `uranus_conjunction` | 102 | 90d | -1.593% | -1.518% | 3.005% | 2.016% | 61.616% | yes |
| 6 | `pluto_trine` | 196 | 60d | -0.348% | -1.397% | 2.142% | 2.050% | 61.658% | yes |
| 7 | `venus_opposition` | 143 | 60d | -0.640% | -1.376% | 1.994% | 2.227% | 59.441% | yes |
| 8 | `mars_conjunction` | 134 | 90d | -0.943% | -1.358% | 3.425% | 3.498% | 72.093% | yes |
| 9 | `neptune_conjunction` | 105 | 90d | -3.509% | -1.148% | 2.236% | 2.533% | 61.000% | yes |
| 10 | `saturn_trine` | 210 | 180d | -0.167% | -1.099% | 8.772% | 8.554% | 74.510% | no |
| 11 | `jupiter_mars` | 107 | 180d | -0.994% | -1.028% | 8.342% | 6.654% | 69.903% | yes |
| 12 | `saturn_opposition` | 101 | 60d | -0.663% | -1.010% | 2.180% | 2.241% | 61.386% | yes |
| 13 | `mars_uranus_shock` | 59 | 14d | -0.093% | -0.903% | 0.197% | 0.780% | 55.932% | no |
| 14 | `pluto_square` | 209 | 60d | -0.037% | -0.785% | 2.593% | 2.098% | 62.927% | yes |
| 15 | `venus_square` | 291 | 180d | -0.692% | -0.695% | 8.657% | 7.902% | 71.174% | yes |
| 16 | `mars_pluto` | 119 | 30d | -0.978% | -0.690% | 0.640% | 0.757% | 55.085% | yes |
| 17 | `neptune_venus` | 220 | 180d | -0.261% | -0.681% | 8.898% | 8.532% | 70.423% | no |
| 18 | `aspect:conjunction` | 757 | 180d | -0.250% | -0.619% | 8.925% | 8.106% | 71.272% | yes |

## Robust bullish exact features

| Rank | Bucket | Events | Best horizon | Train edge | Test edge | Avg return | Median | Bullish | Median agrees |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `jupiter_saturn_square` | 8 | 180d | 5.587% | 16.919% | 22.020% | 18.777% | 87.500% | yes |
| 2 | `mars_uranus_sextile` | 32 | 180d | 4.249% | 5.249% | 14.051% | 10.844% | 87.097% | yes |
| 3 | `mars_saturn_opposition` | 13 | 180d | 0.226% | 4.831% | 11.701% | 8.576% | 84.615% | yes |
| 4 | `mars_saturn_trine` | 32 | 180d | 3.015% | 4.740% | 13.200% | 13.144% | 90.323% | yes |
| 5 | `mercury_pluto_opposition` | 27 | 180d | 2.452% | 4.156% | 12.686% | 11.787% | 77.778% | yes |
| 6 | `mars_sun_sextile` | 24 | 180d | 1.018% | 3.846% | 11.664% | 10.913% | 79.167% | yes |
| 7 | `mercury_neptune_trine` | 61 | 180d | 0.445% | 3.614% | 11.216% | 10.282% | 74.138% | yes |
| 8 | `saturn_venus_conjunction` | 28 | 180d | 4.246% | 3.198% | 13.130% | 13.039% | 70.370% | yes |
| 9 | `mars_uranus_opposition` | 16 | 90d | 1.541% | 3.165% | 6.917% | 7.384% | 75.000% | yes |
| 10 | `mercury_venus_sextile` | 58 | 180d | 1.388% | 2.799% | 11.419% | 10.432% | 86.207% | yes |
| 11 | `mars_saturn_sextile` | 28 | 30d | 2.162% | 2.780% | 3.906% | 5.156% | 82.143% | yes |
| 12 | `pluto_sun_conjunction` | 26 | 60d | 1.720% | 2.709% | 5.198% | 5.183% | 76.923% | yes |
| 13 | `saturn_sun_conjunction` | 25 | 90d | 1.298% | 2.674% | 6.493% | 4.478% | 83.333% | yes |
| 14 | `mars_venus_trine` | 33 | 180d | 1.149% | 2.616% | 11.255% | 10.582% | 69.697% | yes |
| 15 | `mercury_saturn_conjunction` | 31 | 180d | 0.267% | 2.409% | 10.546% | 9.064% | 73.333% | yes |
| 16 | `neptune_sun_square` | 51 | 180d | 1.582% | 2.381% | 11.300% | 7.211% | 76.000% | no |
| 17 | `mars_venus_sextile` | 33 | 90d | 0.515% | 2.292% | 5.968% | 2.908% | 65.625% | no |
| 18 | `jupiter_mercury_trine` | 62 | 60d | 0.444% | 2.290% | 4.427% | 4.569% | 65.574% | yes |

## Robust bearish exact features

| Rank | Bucket | Events | Best horizon | Train edge | Test edge | Avg return | Median | Bullish | Median agrees |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `pluto_uranus_square` | 7 | 180d | -17.602% | -9.468% | -4.765% | -5.466% | 14.286% | yes |
| 2 | `mars_saturn_conjunction` | 13 | 180d | -0.231% | -8.545% | 4.962% | 2.554% | 50.000% | yes |
| 3 | `jupiter_neptune_trine` | 9 | 60d | -2.549% | -4.321% | -0.156% | 0.222% | 55.556% | yes |
| 4 | `neptune_sun_conjunction` | 26 | 180d | -3.324% | -4.286% | 5.565% | 5.418% | 68.000% | yes |
| 5 | `uranus_venus_conjunction` | 26 | 180d | -3.558% | -3.616% | 5.764% | 4.010% | 72.000% | yes |
| 6 | `mars_uranus_conjunction` | 14 | 60d | -0.113% | -3.576% | 1.387% | 2.002% | 57.143% | yes |
| 7 | `pluto_venus_opposition` | 27 | 60d | -1.163% | -3.437% | 0.810% | 0.620% | 51.852% | yes |
| 8 | `mars_neptune_conjunction` | 14 | 90d | -3.216% | -3.338% | 1.292% | 2.353% | 76.923% | yes |
| 9 | `jupiter_pluto_trine` | 9 | 180d | -2.976% | -3.158% | 6.293% | 8.633% | 66.667% | no |
| 10 | `sun_uranus_conjunction` | 26 | 180d | -1.243% | -3.084% | 7.224% | 7.541% | 72.000% | yes |
| 11 | `mars_neptune_sextile` | 27 | 90d | -1.205% | -2.820% | 2.582% | 0.377% | 55.556% | yes |
| 12 | `saturn_sun_trine` | 50 | 180d | -0.177% | -2.687% | 7.995% | 9.879% | 73.469% | no |
| 13 | `pluto_venus_conjunction` | 28 | 180d | -1.316% | -2.686% | 7.375% | 4.321% | 62.963% | yes |
| 14 | `mars_venus_square` | 34 | 180d | -2.340% | -2.667% | 6.847% | 4.307% | 64.706% | yes |
| 15 | `pluto_sun_trine` | 51 | 60d | -0.009% | -2.654% | 1.706% | 3.244% | 60.000% | no |
| 16 | `mercury_uranus_conjunction` | 33 | 180d | -1.386% | -2.574% | 7.444% | 7.226% | 78.125% | yes |
| 17 | `jupiter_uranus_trine` | 8 | 30d | -5.238% | -2.572% | -2.426% | -2.930% | 25.000% | yes |
| 18 | `mercury_saturn_opposition` | 27 | 180d | -2.184% | -2.362% | 7.091% | 6.826% | 73.077% | yes |

# Headline Candidate Profiles

### Horizon profile: `jupiter_saturn`

| Horizon | Baseline avg | Train avg | Train edge | Test avg | Test edge | All median | All bullish | Same direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3d | 0.147% | 0.477% | 0.330% | -0.051% | -0.198% | 0.073% | 59.259% | no |
| 7d | 0.345% | 2.638% | 2.293% | 0.937% | 0.592% | 2.382% | 66.667% | yes |
| 14d | 0.688% | 3.802% | 3.114% | 1.536% | 0.848% | 2.471% | 70.370% | yes |
| 30d | 1.479% | 5.429% | 3.950% | 3.319% | 1.840% | 5.408% | 77.778% | yes |
| 60d | 2.984% | 4.359% | 1.375% | 6.317% | 3.333% | 5.643% | 70.370% | yes |
| 90d | 4.564% | 7.574% | 3.009% | 7.315% | 2.750% | 6.574% | 77.778% | yes |
| 180d | 9.350% | 12.125% | 2.775% | 16.610% | 7.260% | 12.098% | 80.769% | yes |

### Horizon profile: `sun_venus`

| Horizon | Baseline avg | Train avg | Train edge | Test avg | Test edge | All median | All bullish | Same direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3d | 0.147% | -0.340% | -0.488% | 0.228% | 0.081% | -0.297% | 46.875% | no |
| 7d | 0.345% | -0.088% | -0.433% | 0.564% | 0.219% | 0.435% | 56.250% | no |
| 14d | 0.688% | 0.762% | 0.073% | 3.043% | 2.354% | 1.810% | 68.750% | yes |
| 30d | 1.479% | 1.314% | -0.165% | 4.243% | 2.764% | 3.391% | 75.000% | no |
| 60d | 2.984% | 3.413% | 0.429% | 5.230% | 2.246% | 4.514% | 81.250% | yes |
| 90d | 4.564% | 5.136% | 0.571% | 3.695% | -0.869% | 4.333% | 78.125% | no |
| 180d | 9.350% | 9.236% | -0.114% | 8.421% | -0.930% | 11.637% | 74.194% | yes |

### Horizon profile: `jupiter_uranus`

| Horizon | Baseline avg | Train avg | Train edge | Test avg | Test edge | All median | All bullish | Same direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3d | 0.147% | 0.696% | 0.549% | -0.420% | -0.567% | 0.118% | 53.846% | no |
| 7d | 0.345% | 1.911% | 1.565% | -0.535% | -0.880% | 0.820% | 61.538% | no |
| 14d | 0.688% | 0.567% | -0.122% | 1.178% | 0.490% | 0.018% | 50.000% | no |
| 30d | 1.479% | 0.836% | -0.643% | -0.797% | -2.276% | -0.281% | 42.308% | yes |
| 60d | 2.984% | 4.998% | 2.014% | -0.688% | -3.672% | 1.830% | 57.692% | no |
| 90d | 4.564% | 5.146% | 0.581% | 2.334% | -2.230% | 3.068% | 61.538% | no |
| 180d | 9.350% | 11.027% | 1.676% | 2.088% | -7.262% | 5.197% | 57.692% | no |

### Horizon profile: `pluto_uranus_square`

| Horizon | Baseline avg | Train avg | Train edge | Test avg | Test edge | All median | All bullish | Same direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3d | 0.147% | 1.418% | 1.271% | 2.485% | 2.337% | 1.570% | 85.714% | yes |
| 7d | 0.345% | 0.997% | 0.652% | 5.280% | 4.935% | 1.074% | 85.714% | yes |
| 14d | 0.688% | 0.053% | -0.635% | 5.008% | 4.320% | 1.171% | 57.143% | no |
| 30d | 1.479% | -2.556% | -4.035% | 3.849% | 2.370% | -2.858% | 42.857% | no |
| 60d | 2.984% | -1.303% | -4.287% | 5.943% | 2.959% | 2.752% | 57.143% | no |
| 90d | 4.564% | -0.871% | -5.436% | 2.711% | -1.853% | 0.483% | 57.143% | yes |
| 180d | 9.350% | -8.251% | -17.602% | -0.118% | -9.468% | -5.466% | 14.286% | yes |

# Interpretation Map

## 1. Pressure / bear watch

The clearest large-cycle pressure candidate is `jupiter_uranus`. In the outer-cycle scan it had 26 events, with 46.154% inside bear regimes versus a 29.374% bear baseline. It also appeared in peak and bottom windows at roughly 2x baseline, which makes it an instability marker rather than a simple bearish signal. In forward returns, `jupiter_uranus` was a same-direction underperformer at the 30d horizon in the full no-moon theme screen.

Other pressure-enriched full-scan themes include `neptune_opposition`, `pluto_trine`, `saturn_conjunction`, `uranus_opposition`, `pluto_square`, and `venus_opposition`. These should be read as volatility and stress markers first.

## 2. Peak-risk watch

Peak-risk enrichment leans toward opposition/square language: `pluto_opposition`, broad `opposition`, `mars_square`, `sun_opposition`, `mercury_opposition`, and `jupiter_opposition`. In Gold this can mean late-cycle speculative acceleration, macro stress, or exhaustion depending on the prior price path.

## 3. Bottom / reversal watch

Bottom-window enrichment is not purely soft. The outer-cycle scan highlights `square`, `hard`, and `outer_outer_hard`, while the full scan highlights `uranus_trine`, `neptune_square`, `pluto_conjunction`, `jupiter_sextile`, and `outer_personal_soft`. This supports a reset/rebuild interpretation: Gold bottoms may form around both hard capitulation windows and soft release windows.

## 4. Constructive windows

Forward-return candidates make `jupiter_saturn` the cleanest constructive theme in this run: 27 events, best horizon 180d, train edge +2.775pp, test edge +7.260pp, average return 14.023%, median 12.098%, bullish 80.769%. `sun_venus` is shorter horizon but also notable: 32 events, best horizon 60d, train edge +0.429pp, test edge +2.246pp, average return 4.321%, median 4.514%, bullish 81.250%.

## 5. Gold versus S&P 500

For equities, pressure windows often map more directly to downside risk. For Gold, the same macro-stress window can produce either pressure or a defensive bid. Therefore the Gold framework should not be used as a one-line long/short engine. It is better as a context layer: identify historically interesting dates, then check trend, real rates, USD strength, inflation expectations, liquidity, and geopolitical stress.

# Validation Proxies: GLD and IAU

The current run includes GLD and IAU as regime/data sanity checks, not full replicated aspect scans. They broadly confirm that ETF Gold proxies have similar major drawdown structure but shorter histories than `GC=F`.

| Asset | Start | End | Candles | Bull share | Bear share | Peak window | Bottom window | Drawdown cycles |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GLD | 2004-11-18 | 2026-06-04 | 5419 | 66.414% | 33.586% | 4.503% | 4.503% | [{'bottom_close': 55.62, 'bottom_date': '2006-06-14', 'bottom_idx': 394, 'max_drawdown_pct': -21.794, 'peak_close': 71.12, 'peak_date': '2006-05-12', 'peak_idx': 372, 'peak_to_bottom_days': 22, 'recovery_date': '2007-09-18', 'recovery_idx': 711, 'status': 'recovered', 'underwater_trading_days': 340}, {'bottom_close': 70.0, 'bottom_date': '2008-11-12', 'bottom_idx': 1003, 'max_drawdown_pct': -29.414, 'peak_close': 99.17, 'peak_date': '2008-03-17', 'peak_idx': 835, 'peak_to_bottom_days': 168, 'recovery_date': '2009-09-16', 'recovery_idx': 1214, 'status': 'recovered', 'underwater_trading_days': 380}, {'bottom_close': 100.5, 'bottom_date': '2015-12-17', 'bottom_idx': 2789, 'max_drawdown_pct': -45.555, 'peak_close': 184.59, 'peak_date': '2011-08-22', 'peak_idx': 1701, 'peak_to_bottom_days': 1088, 'recovery_date': '2020-07-29', 'recovery_idx': 3949, 'status': 'recovered', 'underwater_trading_days': 2249}, {'bottom_close': 151.23, 'bottom_date': '2022-09-26', 'bottom_idx': 4493, 'max_drawdown_pct': -22.002, 'peak_close': 193.89, 'peak_date': '2020-08-06', 'peak_idx': 3955, 'peak_to_bottom_days': 538, 'recovery_date': '2024-03-04', 'recovery_idx': 4853, 'status': 'recovered', 'underwater_trading_days': 899}] |
| IAU | 2005-01-28 | 2026-06-04 | 5371 | 66.301% | 33.699% | 4.543% | 4.543% | [{'bottom_close': 11.12, 'bottom_date': '2006-06-14', 'bottom_idx': 346, 'max_drawdown_pct': -21.987, 'peak_close': 14.254, 'peak_date': '2006-05-11', 'peak_idx': 323, 'peak_to_bottom_days': 23, 'recovery_date': '2007-09-18', 'recovery_idx': 663, 'status': 'recovered', 'underwater_trading_days': 341}, {'bottom_close': 14.068, 'bottom_date': '2008-11-12', 'bottom_idx': 955, 'max_drawdown_pct': -29.228, 'peak_close': 19.878, 'peak_date': '2008-03-17', 'peak_idx': 787, 'peak_to_bottom_days': 168, 'recovery_date': '2009-09-16', 'recovery_idx': 1166, 'status': 'recovered', 'underwater_trading_days': 380}, {'bottom_close': 20.3, 'bottom_date': '2015-12-02', 'bottom_idx': 2730, 'max_drawdown_pct': -45.135, 'peak_close': 37.0, 'peak_date': '2011-08-22', 'peak_idx': 1653, 'peak_to_bottom_days': 1077, 'recovery_date': '2020-07-27', 'recovery_idx': 3899, 'status': 'recovered', 'underwater_trading_days': 2247}, {'bottom_close': 30.82, 'bottom_date': '2022-09-26', 'bottom_idx': 4445, 'max_drawdown_pct': -21.816, 'peak_close': 39.42, 'peak_date': '2020-08-06', 'peak_idx': 3907, 'peak_to_bottom_days': 538, 'recovery_date': '2024-03-04', 'recovery_idx': 4805, 'status': 'recovered', 'underwater_trading_days': 899}] |

Next validation should run the complete event/return scan on `GLD`, `IAU`, `GDX`, `GDXJ`, `UUP`, and `TLT`, then test whether the same frozen Gold rules remain directionally useful.

# Five-Year Projection Watchlist: 2026-2031

The future projection freezes the historical interpretation map into category rules and applies it to future exact aspect windows. It is not a price forecast. It is a dated research checklist.

| Item | Value |
| --- | --- |
| Projection start | 2026-06-06 |
| Projection end | 2031-06-05 |
| Future exact aspect windows generated | 936 |
| Classified watchlist windows | 259 |

## Category counts by year

| Year | Peak-risk | Pressure | Bottom/reversal watch | Constructive window |
| --- | --- | --- | --- | --- |
| 2026 | 8 | 11 | 4 | 8 |
| 2027 | 21 | 14 | 5 | 21 |
| 2028 | 15 | 12 | 7 | 16 |
| 2029 | 16 | 13 | 3 | 18 |
| 2030 | 17 | 13 | 4 | 18 |
| 2031 | 9 | 2 | 1 | 8 |

Interpretation: 2027 is the busiest year by both peak-risk and constructive markers. That does not mean “up” or “down”; it means more historically interesting windows where Gold should be monitored closely. 2028-2030 remain active but more balanced. 2031 is partial-year only in this projection.

## Category definitions

- `peak_risk`: euphoria, instability, exhaustion, or fragile-structure candidates.
- `pressure`: stress, drawdown, volatility, or macro-risk candidates. In Gold, pressure may also coincide with safe-haven demand.
- `bottom_reversal_watch`: capitulation, reset, or rebuild candidates; most useful after a preceding decline.
- `constructive_bull_window`: historically supportive or relief-oriented candidates, not standalone buy signals.

## Highest-score highlights by year

### 2026

| Exact date | Window | Feature | Categories | Score |
| --- | --- | --- | --- | --- |
| 2026-09-01 | 2026-08-23 to 2026-09-10 | `jupiter_saturn_trine` | bottom_reversal_watch, constructive_bull_window | 5.099 |
| 2026-06-26 | 2026-06-24 to 2026-06-28 | `neptune_sun_square` | peak_risk | 4.098 |
| 2026-08-29 | 2026-08-27 to 2026-08-31 | `sun_uranus_square` | peak_risk | 4.097 |
| 2026-12-05 | 2026-11-29 to 2026-12-11 | `mars_uranus_square` | peak_risk | 4.097 |
| 2026-08-17 | 2026-08-14 to 2026-08-21 | `mars_neptune_square` | peak_risk | 4.089 |
| 2026-12-27 | 2026-12-26 to 2026-12-28 | `mercury_neptune_square` | peak_risk | 4.089 |
| 2026-07-14 | 2026-07-12 to 2026-07-15 | `uranus_venus_square` | peak_risk | 4.083 |
| 2026-12-23 | 2026-12-22 to 2026-12-25 | `neptune_sun_square` | peak_risk | 4.080 |

### 2027

| Exact date | Window | Feature | Categories | Score |
| --- | --- | --- | --- | --- |
| 2027-07-12 | 2027-06-21 to 2027-07-27 | `jupiter_saturn_trine` | bottom_reversal_watch, constructive_bull_window | 5.100 |
| 2027-04-04 | 2027-03-21 to 2027-04-23 | `jupiter_saturn_trine` | bottom_reversal_watch, constructive_bull_window | 5.097 |
| 2027-05-29 | 2027-05-23 to 2027-06-04 | `mars_uranus_square` | peak_risk | 4.099 |
| 2027-02-17 | 2027-02-15 to 2027-02-19 | `mercury_uranus_square` | peak_risk | 4.098 |
| 2027-12-01 | 2027-11-28 to 2027-12-04 | `mars_neptune_square` | peak_risk | 4.098 |
| 2027-06-11 | 2027-06-03 to 2027-06-19 | `mercury_neptune_square` | peak_risk | 4.097 |
| 2027-09-11 | 2027-08-30 to 2027-09-22 | `jupiter_uranus_square` | peak_risk | 4.097 |
| 2027-12-26 | 2027-12-24 to 2027-12-28 | `neptune_sun_square` | peak_risk | 4.097 |
| 2027-02-17 | 2027-02-11 to 2027-02-23 | `mars_uranus_square` | peak_risk | 4.096 |
| 2027-12-21 | 2027-12-20 to 2027-12-22 | `mercury_neptune_square` | peak_risk | 4.096 |
| 2027-09-10 | 2027-09-07 to 2027-09-13 | `mars_pluto_square` | peak_risk | 4.094 |
| 2027-02-06 | 2027-02-04 to 2027-02-07 | `neptune_venus_square` | peak_risk | 4.088 |

### 2028

| Exact date | Window | Feature | Categories | Score |
| --- | --- | --- | --- | --- |
| 2028-09-24 | 2028-09-14 to 2028-10-05 | `jupiter_pluto_trine` | bottom_reversal_watch, constructive_bull_window | 5.097 |
| 2028-08-03 | 2028-07-31 to 2028-08-06 | `mars_neptune_square` | peak_risk | 4.098 |
| 2028-02-25 | 2028-02-23 to 2028-02-27 | `sun_uranus_square` | peak_risk | 4.096 |
| 2028-06-30 | 2028-06-28 to 2028-07-02 | `neptune_sun_square` | peak_risk | 4.095 |
| 2028-02-18 | 2028-02-16 to 2028-02-21 | `mars_uranus_square` | peak_risk | 4.094 |
| 2028-07-14 | 2028-07-13 to 2028-07-15 | `mercury_neptune_square` | peak_risk | 4.094 |
| 2028-05-10 | 2028-05-07 to 2028-05-13 | `mars_pluto_square` | peak_risk | 4.092 |
| 2028-11-16 | 2028-11-12 to 2028-11-20 | `mars_uranus_square` | peak_risk | 4.092 |
| 2028-09-06 | 2028-09-04 to 2028-09-08 | `sun_uranus_square` | peak_risk | 4.091 |
| 2028-10-14 | 2028-10-13 to 2028-10-16 | `uranus_venus_square` | peak_risk | 4.088 |
| 2028-12-27 | 2028-12-25 to 2028-12-29 | `neptune_sun_square` | peak_risk | 4.085 |
| 2028-08-17 | 2028-08-15 to 2028-08-18 | `neptune_venus_square` | peak_risk | 4.080 |

### 2029

| Exact date | Window | Feature | Categories | Score |
| --- | --- | --- | --- | --- |
| 2029-03-13 | 2029-03-12 to 2029-03-14 | `mercury_uranus_square` | peak_risk | 4.098 |
| 2029-08-22 | 2029-08-19 to 2029-08-25 | `mars_pluto_square` | peak_risk | 4.097 |
| 2029-09-11 | 2029-09-09 to 2029-09-13 | `sun_uranus_square` | peak_risk | 4.097 |
| 2029-06-11 | 2029-06-09 to 2029-06-12 | `neptune_venus_square` | peak_risk | 4.095 |
| 2029-01-13 | 2029-01-12 to 2029-01-15 | `neptune_venus_square` | peak_risk | 4.093 |
| 2029-09-29 | 2029-09-19 to 2029-10-01 | `mercury_uranus_square` | peak_risk | 4.093 |
| 2029-12-10 | 2029-12-09 to 2029-12-12 | `mercury_neptune_square` | peak_risk | 4.092 |
| 2029-12-30 | 2029-12-28 to 2030-01-01 | `neptune_sun_square` | peak_risk | 4.092 |
| 2029-08-05 | 2029-08-04 to 2029-08-07 | `uranus_venus_square` | peak_risk | 4.091 |
| 2029-07-03 | 2029-07-01 to 2029-07-05 | `neptune_sun_square` | peak_risk | 4.089 |
| 2029-03-05 | 2029-03-04 to 2029-03-07 | `uranus_venus_square` | peak_risk | 4.087 |
| 2029-08-14 | 2029-08-12 to 2029-08-15 | `mercury_uranus_square` | peak_risk | 4.087 |

### 2030

| Exact date | Window | Feature | Categories | Score |
| --- | --- | --- | --- | --- |
| 2030-01-30 | 2030-01-17 to 2030-02-08 | `neptune_venus_square` | peak_risk | 4.100 |
| 2030-02-08 | 2030-02-05 to 2030-02-11 | `mars_uranus_square` | peak_risk | 4.100 |
| 2030-01-23 | 2030-01-21 to 2030-01-25 | `mercury_neptune_square` | peak_risk | 4.099 |
| 2030-11-08 | 2030-11-05 to 2030-11-12 | `mars_uranus_square` | peak_risk | 4.099 |
| 2030-09-23 | 2030-09-22 to 2030-09-25 | `uranus_venus_square` | peak_risk | 4.097 |
| 2030-12-18 | 2030-12-17 to 2030-12-20 | `neptune_venus_square` | peak_risk | 4.097 |
| 2030-03-05 | 2030-03-03 to 2030-03-07 | `sun_uranus_square` | peak_risk | 4.095 |
| 2030-04-20 | 2030-04-18 to 2030-04-22 | `uranus_venus_square` | peak_risk | 4.093 |
| 2030-07-22 | 2030-07-18 to 2030-07-25 | `mars_neptune_square` | peak_risk | 4.090 |
| 2030-01-02 | 2029-12-31 to 2030-01-03 | `mercury_neptune_square` | peak_risk | 4.089 |
| 2030-06-29 | 2030-06-28 to 2030-06-30 | `mercury_neptune_square` | peak_risk | 4.089 |
| 2030-07-05 | 2030-07-03 to 2030-07-07 | `neptune_sun_square` | peak_risk | 4.088 |

### 2031

| Exact date | Window | Feature | Categories | Score |
| --- | --- | --- | --- | --- |
| 2031-01-21 | 2031-01-10 to 2031-02-01 | `jupiter_uranus_opposition` | peak_risk, pressure | 7.096 |
| 2031-05-05 | 2031-04-29 to 2031-05-11 | `mars_pluto_square` | peak_risk | 4.098 |
| 2031-05-21 | 2031-05-19 to 2031-05-23 | `neptune_venus_square` | peak_risk | 4.097 |
| 2031-01-20 | 2031-01-19 to 2031-01-21 | `mercury_neptune_square` | peak_risk | 4.093 |
| 2031-02-13 | 2031-02-06 to 2031-02-20 | `mars_pluto_square` | peak_risk | 4.093 |
| 2031-02-11 | 2031-02-09 to 2031-02-12 | `uranus_venus_square` | peak_risk | 4.092 |
| 2031-01-01 | 2030-12-30 to 2031-01-03 | `neptune_sun_square` | peak_risk | 4.090 |
| 2031-03-10 | 2031-03-08 to 2031-03-12 | `sun_uranus_square` | peak_risk | 4.088 |

## Full classified highlight table

| Exact date | Window | Feature | Categories | Score |
| --- | --- | --- | --- | --- |
| 2026-06-26 | 2026-06-24 to 2026-06-28 | `neptune_sun_square` | peak_risk | 4.098 |
| 2026-07-14 | 2026-07-12 to 2026-07-15 | `uranus_venus_square` | peak_risk | 4.083 |
| 2026-08-17 | 2026-08-14 to 2026-08-21 | `mars_neptune_square` | peak_risk | 4.089 |
| 2026-08-29 | 2026-08-27 to 2026-08-31 | `sun_uranus_square` | peak_risk | 4.097 |
| 2026-09-01 | 2026-08-23 to 2026-09-10 | `jupiter_saturn_trine` | bottom_reversal_watch, constructive_bull_window | 5.099 |
| 2026-12-05 | 2026-11-29 to 2026-12-11 | `mars_uranus_square` | peak_risk | 4.097 |
| 2026-12-23 | 2026-12-22 to 2026-12-25 | `neptune_sun_square` | peak_risk | 4.080 |
| 2026-12-27 | 2026-12-26 to 2026-12-28 | `mercury_neptune_square` | peak_risk | 4.089 |
| 2027-02-03 | 2027-02-01 to 2027-02-05 | `mercury_uranus_square` | peak_risk | 4.079 |
| 2027-02-06 | 2027-02-04 to 2027-02-07 | `neptune_venus_square` | peak_risk | 4.088 |
| 2027-02-17 | 2027-02-15 to 2027-02-19 | `mercury_uranus_square` | peak_risk | 4.098 |
| 2027-02-17 | 2027-02-11 to 2027-02-23 | `mars_uranus_square` | peak_risk | 4.096 |
| 2027-02-21 | 2027-02-19 to 2027-02-23 | `sun_uranus_square` | peak_risk | 4.085 |
| 2027-03-21 | 2027-03-19 to 2027-03-22 | `mercury_uranus_square` | peak_risk | 4.082 |
| 2027-03-29 | 2027-03-27 to 2027-03-30 | `uranus_venus_square` | peak_risk | 4.079 |
| 2027-04-04 | 2027-03-21 to 2027-04-23 | `jupiter_saturn_trine` | bottom_reversal_watch, constructive_bull_window | 5.097 |
| 2027-05-29 | 2027-05-23 to 2027-06-04 | `mars_uranus_square` | peak_risk | 4.099 |
| 2027-06-11 | 2027-06-03 to 2027-06-19 | `mercury_neptune_square` | peak_risk | 4.097 |
| 2027-06-29 | 2027-06-26 to 2027-07-01 | `neptune_sun_square` | peak_risk | 4.082 |
| 2027-07-12 | 2027-06-21 to 2027-07-27 | `jupiter_saturn_trine` | bottom_reversal_watch, constructive_bull_window | 5.100 |
| 2027-07-20 | 2027-07-18 to 2027-07-21 | `mercury_neptune_square` | peak_risk | 4.079 |
| 2027-08-29 | 2027-08-27 to 2027-08-30 | `uranus_venus_square` | peak_risk | 4.088 |
| 2027-09-03 | 2027-08-31 to 2027-09-05 | `sun_uranus_square` | peak_risk | 4.084 |
| 2027-09-10 | 2027-09-07 to 2027-09-13 | `mars_pluto_square` | peak_risk | 4.094 |
| 2027-09-11 | 2027-08-30 to 2027-09-22 | `jupiter_uranus_square` | peak_risk | 4.097 |
| 2027-11-29 | 2027-11-27 to 2027-11-30 | `neptune_venus_square` | peak_risk | 4.084 |
| 2027-12-01 | 2027-11-28 to 2027-12-04 | `mars_neptune_square` | peak_risk | 4.098 |
| 2027-12-21 | 2027-12-20 to 2027-12-22 | `mercury_neptune_square` | peak_risk | 4.096 |
| 2027-12-26 | 2027-12-24 to 2027-12-28 | `neptune_sun_square` | peak_risk | 4.097 |
| 2028-01-18 | 2028-01-17 to 2028-01-20 | `uranus_venus_square` | peak_risk | 4.078 |
| 2028-02-18 | 2028-02-16 to 2028-02-21 | `mars_uranus_square` | peak_risk | 4.094 |
| 2028-02-25 | 2028-02-23 to 2028-02-27 | `sun_uranus_square` | peak_risk | 4.096 |
| 2028-05-10 | 2028-05-07 to 2028-05-13 | `mars_pluto_square` | peak_risk | 4.092 |
| 2028-06-30 | 2028-06-28 to 2028-07-02 | `neptune_sun_square` | peak_risk | 4.095 |
| 2028-07-14 | 2028-07-13 to 2028-07-15 | `mercury_neptune_square` | peak_risk | 4.094 |
| 2028-08-03 | 2028-07-31 to 2028-08-06 | `mars_neptune_square` | peak_risk | 4.098 |
| 2028-08-17 | 2028-08-15 to 2028-08-18 | `neptune_venus_square` | peak_risk | 4.080 |
| 2028-09-06 | 2028-09-04 to 2028-09-08 | `sun_uranus_square` | peak_risk | 4.091 |
| 2028-09-24 | 2028-09-14 to 2028-10-05 | `jupiter_pluto_trine` | bottom_reversal_watch, constructive_bull_window | 5.097 |
| 2028-10-14 | 2028-10-13 to 2028-10-16 | `uranus_venus_square` | peak_risk | 4.088 |
| 2028-11-16 | 2028-11-12 to 2028-11-20 | `mars_uranus_square` | peak_risk | 4.092 |
| 2028-12-14 | 2028-12-13 to 2028-12-15 | `mercury_neptune_square` | peak_risk | 4.080 |
| 2028-12-27 | 2028-12-25 to 2028-12-29 | `neptune_sun_square` | peak_risk | 4.085 |
| 2029-01-13 | 2029-01-12 to 2029-01-15 | `neptune_venus_square` | peak_risk | 4.093 |
| 2029-03-01 | 2029-02-27 to 2029-03-03 | `sun_uranus_square` | peak_risk | 4.084 |
| 2029-03-05 | 2029-03-04 to 2029-03-07 | `uranus_venus_square` | peak_risk | 4.087 |
| 2029-03-13 | 2029-03-12 to 2029-03-14 | `mercury_uranus_square` | peak_risk | 4.098 |
| 2029-06-11 | 2029-06-09 to 2029-06-12 | `neptune_venus_square` | peak_risk | 4.095 |
| 2029-07-03 | 2029-07-01 to 2029-07-05 | `neptune_sun_square` | peak_risk | 4.089 |
| 2029-08-05 | 2029-08-04 to 2029-08-07 | `uranus_venus_square` | peak_risk | 4.091 |
| 2029-08-14 | 2029-08-12 to 2029-08-15 | `mercury_uranus_square` | peak_risk | 4.087 |
| 2029-08-22 | 2029-08-19 to 2029-08-25 | `mars_pluto_square` | peak_risk | 4.097 |
| 2029-09-11 | 2029-09-09 to 2029-09-13 | `sun_uranus_square` | peak_risk | 4.097 |
| 2029-09-29 | 2029-09-19 to 2029-10-01 | `mercury_uranus_square` | peak_risk | 4.093 |
| 2029-11-15 | 2029-11-13 to 2029-11-18 | `neptune_venus_square` | peak_risk | 4.086 |
| 2029-11-16 | 2029-11-13 to 2029-11-18 | `mars_neptune_square` | peak_risk | 4.084 |
| 2029-12-10 | 2029-12-09 to 2029-12-12 | `mercury_neptune_square` | peak_risk | 4.092 |
| 2029-12-30 | 2029-12-28 to 2030-01-01 | `neptune_sun_square` | peak_risk | 4.092 |
| 2030-01-02 | 2029-12-31 to 2030-01-03 | `mercury_neptune_square` | peak_risk | 4.089 |
| 2030-01-23 | 2030-01-21 to 2030-01-25 | `mercury_neptune_square` | peak_risk | 4.099 |
| 2030-01-30 | 2030-01-17 to 2030-02-08 | `neptune_venus_square` | peak_risk | 4.100 |
| 2030-02-08 | 2030-02-05 to 2030-02-11 | `mars_uranus_square` | peak_risk | 4.100 |
| 2030-03-05 | 2030-03-03 to 2030-03-07 | `sun_uranus_square` | peak_risk | 4.095 |
| 2030-04-20 | 2030-04-18 to 2030-04-22 | `uranus_venus_square` | peak_risk | 4.093 |
| 2030-04-24 | 2030-04-21 to 2030-04-27 | `mars_pluto_square` | peak_risk | 4.087 |
| 2030-06-29 | 2030-06-28 to 2030-06-30 | `mercury_neptune_square` | peak_risk | 4.089 |
| 2030-07-05 | 2030-07-03 to 2030-07-07 | `neptune_sun_square` | peak_risk | 4.088 |
| 2030-07-22 | 2030-07-18 to 2030-07-25 | `mars_neptune_square` | peak_risk | 4.090 |
| 2030-09-16 | 2030-09-14 to 2030-09-18 | `sun_uranus_square` | peak_risk | 4.086 |
| 2030-09-23 | 2030-09-22 to 2030-09-25 | `uranus_venus_square` | peak_risk | 4.097 |
| 2030-11-08 | 2030-11-05 to 2030-11-12 | `mars_uranus_square` | peak_risk | 4.099 |
| 2030-12-18 | 2030-12-17 to 2030-12-20 | `neptune_venus_square` | peak_risk | 4.097 |
| 2031-01-01 | 2030-12-30 to 2031-01-03 | `neptune_sun_square` | peak_risk | 4.090 |
| 2031-01-20 | 2031-01-19 to 2031-01-21 | `mercury_neptune_square` | peak_risk | 4.093 |
| 2031-01-21 | 2031-01-10 to 2031-02-01 | `jupiter_uranus_opposition` | peak_risk, pressure | 7.096 |
| 2031-02-11 | 2031-02-09 to 2031-02-12 | `uranus_venus_square` | peak_risk | 4.092 |
| 2031-02-13 | 2031-02-06 to 2031-02-20 | `mars_pluto_square` | peak_risk | 4.093 |
| 2031-03-10 | 2031-03-08 to 2031-03-12 | `sun_uranus_square` | peak_risk | 4.088 |
| 2031-05-05 | 2031-04-29 to 2031-05-11 | `mars_pluto_square` | peak_risk | 4.098 |
| 2031-05-21 | 2031-05-19 to 2031-05-23 | `neptune_venus_square` | peak_risk | 4.097 |

# Practical Research Workflow

A practical way to use this research without over-trusting it:

1. Keep the 2026-2031 dates as a watchlist.
2. Before each window, check whether Gold is extended, basing, or already drawing down.
3. Pair the astrology bucket with non-astrology context: real rates, USD, inflation expectations, central-bank policy, liquidity, and geopolitical stress.
4. Record what actually happened after each window without changing the rules.
5. After enough future windows pass, evaluate the frozen rules out-of-sample.

# Caveats and Failure Modes

- Exploratory research only; not financial advice.

- Yahoo Finance commodity futures data is convenient but not audit-grade and may include contract/roll artifacts.

- Peak and bottom labels are hindsight-defined by drawdown cycles.

- Multiple testing is severe; future projection is a watchlist, not a prediction.

- The projection should be validated against spot XAU/USD, GLD, and gold-miner equities when better data is available.

- Futures data can differ from spot Gold because of contract roll, liquidity, adjustment, and Yahoo data choices.
- Hindsight drawdown labels are useful for research, but they are not known in real time.
- Multiple testing is severe. A pattern that looks good after scanning many bodies/aspects/horizons can be a false positive.
- Outer-planet aspects have small event counts; treat them as narrative hypotheses unless validated elsewhere.
- Average returns can be distorted by a few large moves; median and bullish percentage must be checked alongside averages.
- The future calendar can look authoritative because it has exact dates. It should be read as a watchlist, not a prediction.

# Suggested Next Steps

1. Add a cleaner spot XAU/USD provider and rerun the same pipeline.
2. Run full scans on `GLD`, `IAU`, `GDX`, `GDXJ`, `UUP`, `TLT`, and real-rate proxies.
3. Convert the frozen interpretation rules into code under Hermetic Alpha so future watchlist generation is reproducible.
4. Create a prospective tracking issue/discussion that logs each 2026-2031 window outcome without changing criteria.
5. Compare Gold rules against S&P 500 and Bitcoin rules to separate asset-specific behavior from broad macro-cycle behavior.

# Reproducibility

Artifacts in this research package:

- `README.md`: this paper.
- `gold-xau-astrology-research-hermetic-alpha-v011.pdf`: PDF version.
- `scripts/gold_xau_astrology_research.py`: reproduction script used for the experiment.
- `scripts/generate_comprehensive_gold_report.py`: report generator used to convert the JSON result into this paper.

The source script writes a JSON results file and then the paper generator converts selected tables and interpretation into Markdown/PDF artifacts.

# Disclaimer

This is exploratory market research and library dogfooding. It is not investment advice, financial advice, or a recommendation to buy, sell, short, or leverage Gold or any related instrument.
