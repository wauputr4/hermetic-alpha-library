# Hermetic Alpha Library

**Hermetic Alpha Library** is the core research engine for exploring statistical relationships between astrological configurations and financial market behavior.

The library is designed to calculate planetary positions, derive astrological aspects, transform them into quantitative features, and evaluate their relationship with market outcomes such as bullish probability, local tops, local bottoms, and forward returns.

> This project does not claim deterministic prediction. It provides transparent tools for statistical research, event studies, and reproducible backtesting.

## Goals

- Compute planetary positions and astrological aspects for historical timestamps.
- Convert chart configurations into machine-readable features.
- Analyze whether specific aspects correlate with market behavior.
- Support event-study workflows for assets such as Bitcoin.
- Provide reusable Python APIs for CLI, notebooks, and future web applications.

## Initial Scope

The first version focuses on:

- Natal/transit-style chart calculation for timestamps.
- Major aspects: conjunction, opposition, trine, square, sextile.
- Configurable orb ranges.
- Market return labels across multiple horizons.
- Conditional probability analysis.
- Event-study summaries.
- Exportable CSV/JSON results.

## Planned Python Package

```python
from hermetic_alpha.analysis import aspect_event_study

result = aspect_event_study(
    asset="BTC-USD",
    aspect={
        "body_a": "sun",
        "body_b": "jupiter",
        "type": "conjunction",
        "orb": 3,
    },
    start="2015-01-01",
    end="2026-01-01",
    horizons=[1, 7, 30],
)

print(result.summary())
```

## Repository Role

This repository contains only the reusable core logic. User-facing tools such as command-line interfaces, APIs, and dashboards should call this library instead of duplicating analysis logic.

## Development Quickstart

Create a local development environment with `uv` when it is available:

```bash
uv venv
uv pip install -e ".[dev]"
uv run python3 -m pytest -q
```

Or use the standard library `venv` plus `pip`:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

The `pyproject.toml` pytest configuration sets `pythonpath = ["src"]`, so tests
can import the editable package without manually exporting `PYTHONPATH`.

```bash
PYTHONPATH=src python3 examples/basic_event_study.py
```

Fetch normalized BTC daily candles through the first market provider:

```python
from hermetic_alpha.market import YahooFinanceProvider

candles = YahooFinanceProvider().fetch_daily_btc("2024-01-01", "2024-01-31")
```

When the development extra is installed:

```bash
python3 -m pytest -q
```

## License

MIT
