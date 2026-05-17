# Implementation Roadmap

## Phase 0 — Documentation and Repository Shape

Status: in progress.

Goals:

- Define library and CLI boundaries.
- Document research logic.
- Document data model.
- Document statistical methods.
- Prepare for code implementation.

## Phase 1 — Core Library MVP

Goals:

- Create Python package structure.
- Add aspect math utilities.
- Add circular distance calculation.
- Add basic aspect detection.
- Add market label generation from OHLCV data.
- Add event-study summary function.
- Add dependency-free JSON and flat CSV result export helpers.
- Add unit tests for math and labels.

Expected outputs:

- Python importable package.
- Simple event-study API.
- JSON-compatible result object.
- Stable JSON and CSV exports for model objects and result mappings.

## Phase 2 — Data Providers

Goals:

- Add market provider abstraction.
- Support at least one BTC data source.
- Cache or store downloaded candles locally. Dependency-free JSON candle cache
  helpers are implemented in `hermetic_alpha.market`.
- Normalize timestamps and intervals.

Candidate providers:

- yfinance
- ccxt
- CoinGecko

## Phase 3 — Astro Engine Integration

Goals:

- Evaluate Kerykeion, Immanuel, and pyswisseph.
- Select first implementation engine.
- Generate planetary positions for a date range.
- Detect major aspects over historical timestamps.

## Phase 4 — Statistical Validation

Goals:

- Add baseline comparisons.
- Add bootstrap confidence intervals.
- Add permutation tests.
- Add warnings for low sample size.

## Phase 5 — Similarity Engine

Goals:

- Encode chart states as vectors. Initial sine/cosine longitude encoding is
  implemented in `hermetic_alpha.similarity`.
- Use sin/cos encoding for circular values.
- Implement K-nearest-neighbor search. Initial dependency-free in-memory
  nearest-neighbor ranking is implemented in `hermetic_alpha.similarity`.
- Return similar historical chart-market states with caller-owned IDs and
  payloads.

## Phase 6 — CLI Integration

The CLI repository should call the library for:

- fetching data,
- generating aspects,
- running event studies,
- exporting results,
- searching similar states.

## Phase 7 — Future Web App

Potential stack:

- FastAPI backend.
- SvelteKit frontend.
- DuckDB or PostgreSQL storage.
- Interactive event charts and aspect leaderboards.
