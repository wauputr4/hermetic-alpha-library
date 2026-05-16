# Architecture

Hermetic Alpha Library should be designed as a reusable Python package with a clean separation between calculation, data preparation, analysis, and output formatting.

## Design Principles

1. **Core logic must be interface-agnostic**

   The library should not know whether it is being called by a CLI, notebook, API, or web app.

2. **Research must be reproducible**

   Given the same market data, astro engine, date range, aspect rules, and label configuration, the result should be reproducible.

3. **Data transformations should be explicit**

   Each stage should produce inspectable intermediate data.

4. **Statistics should be honest**

   Results should include sample size, baseline comparisons, and uncertainty where possible.

## Proposed Package Layout

```text
hermetic_alpha/
├─ astro/
│  ├─ ephemeris.py
│  ├─ aspects.py
│  └─ models.py
├─ market/
│  ├─ providers.py
│  ├─ candles.py
│  └─ storage.py
├─ features/
│  └─ build.py
├─ labels/
│  └─ market.py
├─ analysis/
│  ├─ event_study.py
│  ├─ probability.py
│  └─ validation.py
├─ similarity/
│  ├─ encoding.py
│  └─ search.py
└─ exports/
   ├─ json.py
   └─ csv.py
```

The initial `hermetic_alpha.exports` package provides dependency-free helpers
for serializing library-owned models and result dictionaries. JSON export
accepts mappings, sequences, and objects with `to_dict()`. CSV export is limited
to flat rows with scalar values so notebooks, future CLIs, and batch jobs do not
silently invent incompatible nested flattening rules.

## Data Model Concepts

### Aspect Event

```json
{
  "timestamp": "2024-05-18T00:00:00Z",
  "body_a": "sun",
  "body_b": "jupiter",
  "aspect": "conjunction",
  "target_angle": 0,
  "actual_angle": 1.42,
  "orb": 1.42,
  "max_orb": 3,
  "strength": 0.5267,
  "phase": "applying"
}
```

### Market Label

```json
{
  "timestamp": "2024-05-18T00:00:00Z",
  "asset": "BTC-USD",
  "close": 66921.4,
  "return_1d": 0.012,
  "return_7d": 0.074,
  "return_30d": 0.118,
  "bullish_7d": true,
  "local_top_7d": false,
  "local_bottom_7d": true
}
```

## Future Interfaces

The core library should support:

- CLI repository.
- FastAPI service.
- SvelteKit dashboard.
- Jupyter notebooks.
- Batch research jobs.

## Ephemeris Backend Decision

ADR 0001 selects `pyswisseph` as the first experimental ephemeris backend. The
integration should be isolated behind a Hermetic Alpha adapter and remain
optional until licensing and packaging policy are finalized.
