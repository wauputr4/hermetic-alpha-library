# Research workflow + quick start

This document uses the repository's existing pipeline to run a compact statistical research flow: identify and evaluate potential relationships between astrological aspects and market behavior without building a black-box model.

## 0) Prepare the environment

```bash
PYTHONPATH=src python3 -m pip install -U pip
PYTHONPATH=src pip install -e .
```

To run tests:

```bash
PYTHONPATH=src python3 -m pytest -q
```

## 1) Short research flow

1. **Hypothesis setup**  
   Example: "A Sun-Moon conjunction at timestamp *t* is associated with higher probability of positive `1d` return."

2. **Prepare market labels**  
   - From close price: `add_forward_returns(closes, horizons=[1])` (adds `return_1d`, `bullish_1d`).  
   - Add `timestamp` and `asset` to each label if joining with aspects.

3. **Prepare astronomy data (position per timestamp)**  
   - Use real data: `generate_planet_positions(...)` + `scan_aspect_series(...)`.
   - Or synthetic data for rapid prototyping, while still passing library validation.

4. **Detect aspects**  
   - `scan_aspect_series(...)` scans aspects at each timestamp.
   - Filter by selected aspect when needed, e.g. only `conjunction`.

5. **Join aspect ↔ labels**
   - Use `join_aspect_events_to_market_labels(...)` to produce `TimestampJoinResult`.
   - This ensures alignment by timestamp, not by row index.

6. **Event study + validation**
   - `summarize_event_study(labels, event_indexes, horizon)` for baseline vs conditional comparison.
   - `summarize_validated_event_study(... bootstrap_samples=..., bootstrap_seed=...)` for confidence intervals and low-sample warnings.
   - `permutation_test(...)` for a non-parametric baseline significance check.

7. **Export results**
   - `to_json(...)` and `to_csv(...)` for audit/report artifacts.

## 2) Useful interfaces

- `hermetic_alpha.astro`:
  - `generate_planet_positions`, `scan_aspect_series`, `detect_aspect`, `find_aspects`
- `hermetic_alpha.labels`:
  - `add_forward_returns`, `add_local_extrema_labels`
- `hermetic_alpha.analysis`:
  - `join_aspect_events_to_market_labels`, `summarize_event_study`, `summarize_validated_event_study`, `permutation_test`
- `hermetic_alpha.exports`:
  - `to_csv`, `to_json`

## 3) Mini research example (evidence)

Open these scripts for an end-to-end example:

- Synthetic script: [`examples/synthetic_astronomy_return_case.py`](../examples/synthetic_astronomy_return_case.py)
- Real-market script (multi-asset + walk-forward): [`examples/real_market_astronomy_return_case.py`](../examples/real_market_astronomy_return_case.py)
- Run the synthetic case:

```bash
PYTHONPATH=src python3 examples/synthetic_astronomy_return_case.py
```

Or run the real-market case (multi-asset + walk-forward, Yahoo Finance):

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

Install the ephemeris extra to enable real planetary positions:

```bash
PYTHONPATH=src pip install -e ".[ephemeris]"
```

The real-market script automatically uses `pyswisseph` when available; otherwise it falls back to reproducible synthetic positions so the pipeline remains runnable.

Output report formats:
- `tmp/market_multi_asset_<start>_<end>_<horizon>d.csv`
- `tmp/market_multi_asset_<start>_<end>_<horizon>d.json`

This script:
- creates a synthetic price series,
- generates synthetic Sun/Moon positions per day,
- scans aspects to detect conjunction events,
- computes 1-day event-study summaries,
- validates with bootstrap + permutation test,
- and prints interpretation guidance.

## 4) Research quality notes

For publishable research quality, follow the [Anti-Overfitting Guide](anti-overfitting.md):
- always compare against baseline,
- apply sample-size-aware warnings,
- log method choices and parameters,
- and separate discovery from verification data for larger studies.
