# Hermetic Alpha Library Overview

Hermetic Alpha Library is the analytical core of the Hermetic Alpha ecosystem.

It is responsible for turning two independent time-series domains into a single research dataset:

1. **Astrological time series** — planetary positions, angular relationships, aspects, orbs, and chart similarity vectors.
2. **Market time series** — OHLCV candles, returns, local tops, local bottoms, volatility, and trend labels.

The library then allows researchers to test whether certain astrological configurations appear more often before bullish, bearish, top, or bottom events.

## Core Pipeline

```text
Market OHLCV data
        ↓
Astrological ephemeris data
        ↓
Aspect detection and feature engineering
        ↓
Market labeling
        ↓
Event study / probability analysis / similarity search
        ↓
Backtest and statistical validation
```

## Core Modules

### `hermetic_alpha.astro`

Responsible for astronomical and astrological calculations.

Planned responsibilities:

- Planetary longitude calculation.
- Aspect detection.
- Orb calculation.
- Applying/separating status.
- Retrograde status when supported by the selected engine.
- Optional support for signs, houses, and zodiac systems.

Candidate engines:

- Kerykeion
- Immanuel Python
- Swiss Ephemeris / pyswisseph

ADR 0001 selects `pyswisseph` as the first experimental backend because it is
closest to the raw longitude and speed calculations Hermetic Alpha needs. The
adapter should remain optional until licensing and packaging policy are clear.
The initial adapter lives behind `hermetic_alpha.astro.SwissEphemerisAdapter`
and returns Hermetic Alpha `PlanetPosition` models instead of exposing raw
`swisseph` results.
Use `generate_planet_positions()` when research code needs a deterministic
timestamp/body series from any adapter with a `position(timestamp, body)`
method. The helper keeps ordering as timestamp first, then the caller-supplied
body order, while leaving UTC normalization to the adapter.
Use `scan_aspect_series()` to group timestamped `PlanetPosition` rows and run
the existing aspect detector independently for each timestamp. The scanner
orders results by timestamp, then sorted body pair and configured aspect order;
if a timestamp is missing a body, it scans only the bodies present at that
timestamp instead of inventing positions.

### `hermetic_alpha.market`

Responsible for market data ingestion and normalization.

Responsibilities:

- Fetch OHLCV data from providers such as Yahoo Finance, Binance, CoinGecko, or CCXT-compatible exchanges.
- Normalize timestamps.
- Resample candles.
- Store reusable local datasets.

The first implemented provider is `YahooFinanceProvider`, which fetches daily
`BTC-USD` candles from Yahoo Finance's chart endpoint and returns normalized
`MarketCandle` models with `source="yahoo_finance"` and `interval="1d"`.
Use `write_candles_json()` and `read_candles_json()` when notebooks or examples
need a small dependency-free local cache of those normalized candles.

### `hermetic_alpha.features`

Responsible for transforming raw astro data into quantitative features.

Examples:

- `sun_jupiter_conjunction_active`
- `sun_jupiter_conjunction_orb`
- `sun_jupiter_conjunction_strength`
- `mars_saturn_square_active`
- `moon_phase_angle`

Aspect strength can be represented as:

```text
strength = 1 - (orb / max_orb)
```

### `hermetic_alpha.labels`

Responsible for defining market outcomes.

Examples:

- Forward return after 1, 3, 7, 14, or 30 days.
- Bullish/bearish classification.
- Local top detection.
- Local bottom detection.
- Volatility regime.

### `hermetic_alpha.analysis`

Responsible for statistical research workflows.

Initial methods:

- Event study analysis.
- Conditional probability.
- Baseline comparison.
- Bootstrap confidence intervals.
- Permutation tests.

### `hermetic_alpha.similarity`

Responsible for comparing chart configurations.

Important note: planetary degrees are circular values. Longitudes should usually be encoded as sine/cosine pairs before similarity search.

Example:

```text
angle = 359° and angle = 1° are close, not far apart.
```

The initial dependency-free similarity layer exposes `encode_longitude()` and
`encode_planet_positions()`. Position vectors are ordered by timestamp, then
body name, then zodiac, and each position contributes `longitude_sin` followed
by `longitude_cos`. Aware timestamps are compared as datetimes, so equivalent
instants in different timezone offsets keep chronological ordering before the
body and zodiac tie-breakers are applied.

The search layer exposes `SimilarityCandidate`, `find_nearest()`,
`cosine_similarity()`, and `euclidean_distance()` for small in-memory
nearest-neighbor workflows. It is intentionally dependency-free and returns
ranked neighbors with caller-provided IDs and optional payloads. Exact score
ties are ordered by candidate ID for reproducible reports.

Recommended methods:

- Circular distance.
- Cosine similarity.
- K-nearest neighbors for small in-memory candidate sets.
- Vector search over historical chart states.

## Statistical Principles

Hermetic Alpha should prioritize transparency and avoid overclaiming.

Every result should ideally include:

- Number of events.
- Baseline market probability.
- Conditional probability.
- Average and median returns.
- Confidence interval.
- Out-of-sample validation where possible.
- Warning for low sample sizes.

## Anti-Bias Rules

The project should avoid:

- Data leakage.
- Cherry-picking only profitable aspects.
- Ignoring failed hypotheses.
- Reporting probabilities without sample size.
- Treating correlation as deterministic prediction.
