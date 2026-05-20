# Data Model

This page defines the initial data structures Hermetic Alpha Library should support.

## Market Candle

```json
{
  "timestamp": "2024-05-18T00:00:00Z",
  "asset": "BTC-USD",
  "open": 65200.0,
  "high": 67200.0,
  "low": 64800.0,
  "close": 66921.4,
  "volume": 12450.0,
  "interval": "1d"
}
```

## Planet Position

```json
{
  "timestamp": "2024-05-18T00:00:00Z",
  "body": "sun",
  "longitude": 57.42,
  "latitude": 0.0,
  "speed": 0.96,
  "retrograde": false,
  "zodiac": "tropical"
}
```

## Aspect Definition

```json
{
  "name": "conjunction",
  "angle": 0,
  "default_orb": 3
}
```

## Aspect Event

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

## Market Label

```json
{
  "timestamp": "2024-05-18T00:00:00Z",
  "asset": "BTC-USD",
  "return_1d": 0.012,
  "return_7d": 0.074,
  "return_30d": 0.118,
  "bullish_7d": true,
  "local_top_7d": false,
  "local_bottom_7d": true
}
```

Local top and bottom labels are retrospective centered-window labels. For a
window of 7, `local_top_7d` means the current close is the maximum close in the
range from seven candles before through seven candles after the current candle.
The labeling helper accepts one window or multiple windows, such as `[3, 7, 14]`,
and emits matching `local_top_*d` and `local_bottom_*d` fields. The first and
last `window` rows cannot be labeled without incomplete context and should be
represented as `null` for each affected window.

Use `add_candle_forward_returns()` when labels are derived from ordered
`MarketCandle` values and need to preserve exact `timestamp` and `asset`
metadata for event joins. The helper uses the same `return_*d` and
`bullish_*d` semantics as `add_forward_returns()`, but rejects mixed-asset
candle sequences so one label table cannot silently combine incompatible
markets.
Use `forward_return_label_coverage_row()` when notebooks, audits, or future CLI
commands need one compact row describing whether a forward-return label table
has enough usable rows before event-study joins. It reports row count,
non-missing return count, bullish/bearish counts, missing label count, optional
dataset ID, optional single asset, and first/last timestamps without replacing
the underlying label rows.

Use `add_candle_local_extrema_labels()` when retrospective top/bottom labels are
derived from ordered `MarketCandle` values. It preserves the candle `timestamp`
and `asset` in every output row, reuses the same `local_top_*d` and
`local_bottom_*d` semantics as `add_local_extrema_labels()`, and keeps edge rows
as `null` where the centered window lacks enough prior or future candles.
Use `local_extrema_label_coverage_row()` when reports need one compact row
describing retrospective top/bottom label coverage for a centered window. It
reports labeled and missing row counts, local top/bottom counts, optional
dataset ID, optional single asset, and first/last timestamps. The row is audit
metadata only; local-extrema labels remain retrospective and should not be
treated as predictive features.

## Event Study Result

```json
{
  "asset": "BTC-USD",
  "aspect": "sun:jupiter:conjunction",
  "orb": 3,
  "date_range": {
    "start": "2015-01-01",
    "end": "2026-01-01"
  },
  "events": 42,
  "baseline_bullish_7d": 0.531,
  "conditional_bullish_7d": 0.642,
  "average_return_7d": 0.038,
  "median_return_7d": 0.019,
  "confidence_interval_7d": [0.498, 0.764]
}
```

## Implementation Status

The initial domain model layer is now implemented under:

```text
src/hermetic_alpha/models/
├─ astro.py
└─ market.py
```

Current models:

- `PlanetPosition`
- `AspectDefinition`
- `AspectEvent`
- `MarketCandle`
- `MarketLabel`
- `EventStudyResult`

Each model provides a `to_dict()` helper for JSON-compatible serialization. Timestamp fields are serialized with `datetime.isoformat()`.
