# Troubleshooting Notes

This document should be updated whenever implementation reveals important context, errors, limitations, or setup decisions.

## Documentation Rule

After each meaningful coding session, update relevant documentation with:

- Important architecture changes.
- New assumptions.
- Known limitations.
- Troubleshooting steps.
- Provider quirks.
- Statistical caveats.

## Expected Early Issues

### Ephemeris Engine Differences

Different astro libraries may produce slightly different outputs due to:

- Zodiac mode.
- House system.
- Ephemeris source.
- Timezone handling.
- UTC conversion.

Mitigation:

- Store the engine name and version in generated datasets.
- Normalize timestamps to UTC.
- Write regression tests for known dates.
- Treat the first `pyswisseph` integration as optional and experimental until
  packaging, native-extension installation, ephemeris-file paths, and licensing
  implications are documented.
- Install the optional backend with `hermetic-alpha[ephemeris]` when planetary
  positions are needed. Core imports and tests should continue to work without
  the native extension installed.
- Pass `ephemeris_path=` to `SwissEphemerisAdapter` when Swiss Ephemeris data
  files are stored outside the backend default search path. Swiss Ephemeris
  stores that path as process-global backend state, so multiple adapter
  instances with different paths can overwrite each other.
- The adapter accepts timezone-aware datetimes and normalizes them to UTC before
  converting to Julian day. Naive datetimes are rejected to avoid silent candle
  and ephemeris alignment errors.
- `generate_planet_positions()` also requires timezone-aware start/end values,
  a positive step, a non-empty body list, and `end >= start`. It preserves the
  supplied timezone-aware timestamps when calling the adapter, so adapter-level
  UTC normalization remains the single source of truth.
- A negative `calc_ut` return flag is treated as a calculation failure and
  raised instead of returning a potentially invalid zeroed position.
- `pyswisseph`/Swiss Ephemeris licensing remains a release policy concern. Keep
  the dependency optional and document downstream obligations before any
  packaged release depends on it by default.

### Timezone and Candle Alignment

Market candles and astro timestamps must be aligned carefully.

Mitigation:

- Internally use UTC.
- Make candle interval explicit.
- Avoid mixing daily candles from different exchange timezone conventions without recording the source.
- `YahooFinanceProvider` requests daily candles with UTC period boundaries,
  records `source="yahoo_finance"` and `interval="1d"`, and skips incomplete
  rows where Yahoo returns missing OHLC values.
- Yahoo Finance is an unofficial public data source and can change response
  shape, throttle requests, or revise historical candles. Treat it as a
  convenient research input, not a canonical audit feed.

### Local Candle Cache Files

`write_candles_json()` and `read_candles_json()` persist normalized
`MarketCandle` rows as a JSON list. Cache files must contain at least one row,
must include `timestamp`, `asset`, `open`, `high`, `low`, `close`, and
`interval`, and timestamps must be timezone-aware ISO datetimes. These files are
convenience caches for repeatable local research runs, not audit-grade market
data stores; keep upstream source metadata and regenerate them when provider
normalization rules change.

### Small Sample Size

Some aspects occur rarely. Probabilities can look impressive but be statistically weak.

Mitigation:

- Always report event count.
- Add low-sample warnings.
- Use bootstrap confidence intervals.
- Compare against random baselines.
- Seed bootstrap and random-baseline helpers when results need to be reproducible in docs, tests, or PR reviews.
- Seed `permutation_test()` and report its `alternative`, `permutations`, and
  p-value correction behavior when using permutation p-values in research notes.

### Permutation Test Interpretation

`permutation_test()` compares observed outcomes with baseline outcomes by
randomly relabeling the combined sample. It validates only the supplied
statistic and alternative direction. If the aspect, horizon, orb, date range, or
statistic was chosen after looking at many alternatives, the p-value is still
exploratory and should be paired with the anti-overfitting guide.

The helper raises `ValueError` for empty samples, non-positive permutation
counts, unsupported alternatives, or statistics that do not return finite
numeric values.

### Walk-Forward Split Boundaries

`walk_forward_splits()` expects ordered observations or a positive observation
count. It rejects empty inputs, non-positive train/test/step sizes, impossible
window lengths, and `step_size < test_size` because that would create overlapping
test windows in reports. Train windows are rolling fixed-size slices and each
test window starts immediately after its matching train window, so future test
observations are not included in that train slice.

### Exact-Orb Aspect Queries

Aspect detection supports `max_orb=0` for exact-match searches. Decimal
longitude arithmetic can leave tiny floating-point residuals around an otherwise
exact angle, so exact-orb matching treats residuals within `1e-9` degrees as
zero and records the event with `orb=0.0` and `strength=1.0`.

### Data Leakage

Top/bottom labels require future data, so they must not be used as predictive features.

Mitigation:

- Keep labels separate from features.
- Clearly document whether an analysis is retrospective or predictive.
- Treat `local_top_*` and `local_bottom_*` labels as retrospective outcomes only because centered windows inspect candles after the labeled timestamp.
- Multi-window extrema labels share this caveat for every requested window. Larger windows leave more unlabeled edge rows because both prior and future candles are required.

### Overfitting and Cherry-Picking

Testing many aspects can produce false positives.

Mitigation:

- Follow the [anti-overfitting guide](anti-overfitting.md) before presenting a
  probability as meaningful.
- Report all tested hypotheses.
- Use holdout periods.
- Add permutation tests.
- Avoid claiming deterministic prediction.

## Git and Release Workflow

Wau's preferred workflow:

- Update docs/context/troubleshooting after coding.
- Commit and push completed changes using GitHub CLI when available.
- Keep library and CLI responsibilities separated.

## Export Helpers

JSON and CSV export helpers normalize native `date` and `datetime` values to
ISO strings before serialization. CSV helpers are intentionally limited to flat
rows; nested mappings or sequences should be flattened by the caller before
export. When passing explicit CSV `fieldnames`, every row must fit that header
exactly apart from missing fields, which are emitted as blank cells.

## Similarity Encoding

Longitude similarity must use circular encodings. Raw degree values make `359`
and `1` look far apart even though they are only two degrees away around the
zodiac wheel. Use `encode_longitude()` for one value or
`encode_planet_positions()` for chart-state vectors. Position vectors are sorted
by timestamp, body, and zodiac before encoding, then each position contributes
`longitude_sin` followed by `longitude_cos`. Timestamp sorting uses datetime
comparison instead of ISO strings so timezone-aware values representing the same
instant are ordered by the body and zodiac tie-breakers, not by their textual
offset representation.

Use `find_nearest()` with `SimilarityCandidate` values for small in-memory
nearest-neighbor searches. The default cosine metric rejects zero vectors
because their direction is undefined; use Euclidean distance only when magnitude
differences are meaningful for the research question. Exact score ties are
ordered by candidate ID, so choose stable IDs when reports need reproducible
ordering.

## Python Development Environment

Use `uv` when it is available:

```bash
uv venv
uv pip install -e ".[dev]"
uv run python3 -m pytest -q
```

If `uv` is not installed, use the standard library virtual environment flow:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

The project requires Python 3.11 or newer. If `python3 -m pytest -q` cannot
import `hermetic_alpha`, confirm the editable install completed or run tests
from the repository root so the `pyproject.toml` pytest `pythonpath` setting can
take effect.

On Debian/Ubuntu, `python3 -m venv .venv` can fail when `ensurepip` is missing.
Install the matching `python3.11-venv` or `python3-venv` system package before
creating the virtual environment. If `pip` reports an `externally-managed-environment`
error, do not install into the system Python; create a venv first or use `uv`.

CI should use the same development extra and pytest command so local failures
match pull request failures. Adding the workflow requires a GitHub credential
with `workflow` scope; otherwise GitHub rejects pushes that create files under
`.github/workflows/`.

## Export Helpers

Use `hermetic_alpha.exports.to_json()` or `write_json()` for deterministic JSON
serialization of mappings, sequences, and model objects with `to_dict()`.

Use `to_csv()` or `write_csv()` only for flat row data. CSV export writes a
stable header based on first-seen field order unless `fieldnames=` is supplied,
and it raises `TypeError` for nested dictionaries, lists, tuples, or other
structured values. Flatten nested research outputs explicitly before exporting
them to CSV so column names remain auditable.

## Reliable test verification (local + CI)

Recommended one-command local verification after checkout:

```bash
python3 -m pip install -e ".[dev]" && python3 -m pytest -q
```

If `python3 -m pytest -q` fails because `pytest` is missing, the install step
did not complete in the active environment. Re-run the install command and then
retry the test command in the same shell.

Core tests and mock ephemeris coverage should run without `hermetic-alpha[ephemeris]`.
Optional ephemeris dependencies are exercised by mocks in
`tests/test_ephemeris.py`, so CI can keep the dependency set lightweight.

## 2026-05-06 — Initial MVP Scaffold

Implemented the first library scaffold:

- Circular degree normalization and distance helpers.
- Aspect strength calculation.
- Major aspect detection utilities.
- Forward-return market labels.
- Basic event-study summary.

Test note:

- `pytest` and `pip` are not currently available in this runtime.
- A direct Python smoke test was used instead and passed with `PYTHONPATH=src python3`.
- Keep the pytest test files in the repository; run them once the Python dev environment is prepared.


## 2026-05-06 — Core Domain Models

Added explicit domain models under `src/hermetic_alpha/models/` for astro, market, labels, and event-study results.

Notes:

- Existing aspect detection now reuses the shared `AspectEvent` model.
- Existing event-study summaries now reuse the shared `EventStudyResult` model.
- Models expose `to_dict()` for JSON-compatible output, with datetimes serialized through `isoformat()`.


### Aspect events missing timestamps

`detect_aspect(..., timestamp=...)` attaches a timestamp to a single detected event. `find_aspects()` also accepts `PlanetPosition` values and propagates their shared timestamp into the returned `AspectEvent` objects. If paired positions have different timestamps, pass an explicit `timestamp=` for the event-study sampling point.


## 2026-05-06 — Multi-Horizon Event Study

Added `summarize_multi_horizon_event_study()` for running the same event index set across several forward-return horizons. The helper deduplicates repeated horizons and ignores invalid event indexes consistently through the existing single-horizon summarizer.

### PR review: multi-horizon type hints

The multi-horizon event-study helper intentionally uses the same `Sequence[dict[str, float | bool | None]]` label type as `summarize_event_study()`. Keeping the public helper signatures aligned avoids static type-checker friction when one helper delegates to the other.
