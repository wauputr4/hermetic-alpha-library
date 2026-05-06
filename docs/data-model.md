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
