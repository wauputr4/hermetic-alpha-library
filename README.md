# Hermetic Alpha Library

**Hermetic Alpha Library** is the core research engine for exploring statistical relationships between astrological configurations and financial market behavior.

The library is designed to calculate planetary positions, derive astrological aspects, transform them into quantitative features, and evaluate their relationship with market outcomes such as bullish probability, local tops, local bottoms, and forward returns.

> This project does not claim deterministic prediction. It provides transparent tools for statistical research, event studies, and reproducible backtesting.

Hermetic Alpha is not financial advice and should not be used as a standalone
trading signal. Any observed relationship between astrological features and
market outcomes must be interpreted as exploratory until it is supported by
adequate sample size, baseline comparison, confidence intervals, and validation
on data that was not used to discover the pattern.

See the [anti-overfitting guide](docs/anti-overfitting.md) for the project
rules on responsible probability reporting, leakage prevention, and
cherry-picking control.

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
from hermetic_alpha.analysis import summarize_event_study
from hermetic_alpha.astro import detect_aspect
from hermetic_alpha.labels import add_forward_returns

closes = [100, 110, 99, 120, 95, 128]
labels = add_forward_returns(closes, horizons=[1, 7, 30])

aspect = detect_aspect(
    body_a="sun",
    longitude_a=10,
    body_b="jupiter",
    longitude_b=12,
    aspect="conjunction",
    max_orb=3,
)

assert aspect is not None
result = summarize_event_study(labels, event_indexes=[0, 1], horizon=1)
print(result)
```

Export library result objects without adding runtime dependencies:

```python
from hermetic_alpha.exports import to_csv, to_json

json_text = to_json(result)
csv_text = to_csv([result])
```

CSV export is intentionally limited to flat rows. Flatten nested research
structures before writing CSV so downstream column names remain explicit.

## Repository Role

This repository contains only the reusable core logic. User-facing tools such as command-line interfaces, APIs, and dashboards should call this library instead of duplicating analysis logic.

## Development Quickstart

### Install package

Install from PyPI:

```bash
python3 -m pip install hermetic-alpha
```

Install from GitHub Packages (requires a GitHub token for read access):

```bash
export GH_PACKAGES_TOKEN=...
python3 -m pip install --index-url "https://__token__:${GH_PACKAGES_TOKEN}@pypi.pkg.github.com/wauputr4/" hermetic-alpha
```

Install directly from a GitHub tag (useful for quick validation):

```bash
python3 -m pip install "git+https://github.com/wauputr4/hermetic-alpha-library.git@v0.1.4"
```

Optional real ephemeris support:

```bash
python3 -m pip install "git+https://github.com/wauputr4/hermetic-alpha-library.git@v0.1.4#egg=hermetic-alpha[ephemeris]"
```

For development contributors:

```bash
python3 -m pip install -e ".[dev,ephemeris]"
```

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
can import the package directly from the source tree even before an editable
install is created.

```bash
python3 examples/basic_event_study.py
```

Fetch normalized BTC daily candles through the first market provider and write
the local JSON cache with the library storage helper:

```bash
python3 examples/provider_to_cache.py data/btc-daily.json --start 2024-01-01 --end 2024-01-31
```

Yahoo Finance is a convenient research input, not an audit-grade market feed.

When the development extra is installed:

```bash
python3 -m pytest -q
```

## Research Quickstart

Run a research workflow from scratch:

1. Build market labels from closes:

```bash
python3 - <<'PY'
from hermetic_alpha.labels import add_forward_returns
returns = add_forward_returns([100, 110, 99, 120, 95, 128], [1, 7, 30])
print(returns)
PY
```

2. Run the synthetic end-to-end example (Sun-Moon conjunction vs 1d return):

```bash
python3 examples/synthetic_astronomy_return_case.py
```

3. Run the real-market example (Yahoo Finance price data):

```bash
python3 examples/real_market_astronomy_return_case.py
```

For a stronger configuration (multi-asset + walk-forward), run:

```bash
python3 examples/real_market_astronomy_return_case.py \
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

4. Read the research workflow and anti-overfitting docs:

- [Research workflow docs](docs/research-workflow.md)
- [Anti-overfitting guide](docs/anti-overfitting.md)

## License

MIT
