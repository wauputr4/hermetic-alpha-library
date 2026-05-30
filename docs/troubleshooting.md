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

### CSV Export Schema Boundaries

`to_csv(..., fieldnames=...)` validates explicit headers before writing output.
Field names must be strings, are trimmed before use, must not be blank, and must
remain unique after trimming. Inferred headers still come from normalized row
keys, but row keys must not be blank or contain leading/trailing whitespace
after string conversion. Explicit headers are treated as a caller-supplied
schema and reject unsupported fields in each row.

### Python Support Metadata

The package metadata advertises only Python versions that CI validates. Keep
the Python classifiers in `pyproject.toml` aligned with the GitHub Actions
matrix, and do not broaden the `requires-python` floor beyond tested runtime
support.

### Typed Package Marker

The package includes `src/hermetic_alpha/py.typed` so downstream type checkers
can treat Hermetic Alpha as a PEP 561 typed package. The marker advertises the
inline type annotations already shipped with the library and does not add a
runtime dependency or CLI behavior.

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
- Use `planet_position_series_summary_row()` after ephemeris generation when an
  audit table needs compact coverage metadata. Empty position series emit zero
  counts and `None` timestamp boundaries. Positions without speed or retrograde
  values are counted explicitly so downstream aspect phase and retrograde
  analyses can see missing metadata before scanning or vector encoding.
- Use `planet_position_series_summary_rows()` when a report compares several
  named ephemeris runs, such as different body sets, date ranges, zodiac modes,
  or engines. The helper keeps caller order, requires series IDs to be
  non-blank strings without leading or trailing whitespace, rejects duplicates,
  and reuses the single-series summary schema for each row; it is
  multi-series audit metadata, not a replacement for raw `PlanetPosition` rows
  or encoded similarity vectors. Ordered named inputs must contain explicit
  two-item `(series_id, positions)` pairs; malformed entries are rejected before
  Python tuple unpacking can raise a generic error.

### Timezone and Candle Alignment

Market candles and astro timestamps must be aligned carefully.

Mitigation:

- Internally use UTC.
- Make candle interval explicit.
- Avoid mixing daily candles from different exchange timezone conventions without recording the source.
- `YahooFinanceProvider` requests daily candles with UTC period boundaries,
  records `source="yahoo_finance"` and `interval="1d"`, and skips incomplete
  rows where Yahoo returns missing OHLC values. If every returned row is
  incomplete, the provider raises `MarketDataProviderError` instead of handing
  an ambiguous empty candle list to downstream cache writers.
- Malformed Yahoo per-row numeric values, including timestamps, OHLC values, and
  optional volume, are wrapped in `MarketDataProviderError` with the candle row
  index. Missing OHLC values are still treated as incomplete rows and skipped.
- `YahooFinanceProvider.fetch_daily()` requires caller-supplied asset symbols
  to be non-blank strings without leading or trailing whitespace before any
  network request is built. Validate or normalize user-facing input at the
  interface boundary, then pass an explicit provider symbol such as `BTC-USD`
  into the library.
- `examples/provider_to_cache.py` is the reference provider-to-cache workflow:
  it fetches normalized BTC daily candles through `YahooFinanceProvider` and
  persists them with `write_candles_json()` without introducing CLI framework
  behavior into the library.
- Yahoo Finance is an unofficial public data source and can change response
  shape, throttle requests, or revise historical candles. Treat it as a
  convenient research input, not a canonical audit feed.
- Use `forward_return_label_coverage_row()` before exact joins when a compact
  audit table needs to show whether `add_forward_returns()` or
  `add_candle_forward_returns()` produced usable horizon labels. Missing horizon
  fields count as missing labels, single-asset candle labels report that asset,
  and plain close-list labels leave asset and timestamp boundaries empty.
- Use `multi_horizon_forward_return_label_coverage_rows()` when a single label
  table carries several forward-return horizons. The helper keeps requested
  horizon order, removes duplicate horizons, and returns flat metadata rows for
  CSV or notebook audit tables; it does not replace exporting the underlying
  label rows.
- Use `multi_dataset_forward_return_label_coverage_rows()` when forward-return
  coverage needs one audit table across several named label datasets. The helper
  preserves dataset and horizon order, rejects blank, whitespace-padded, or
  duplicate dataset IDs, and delegates row fields to the single-dataset coverage
  helpers; it is
  multi-dataset audit metadata, not a replacement for inspecting the underlying
  label rows.
- Use `forward_return_label_group_rows()` when the audit needs those underlying
  raw forward-return label rows from several declared datasets in one flat
  table. The helper preserves caller order, rejects blank/duplicate/non-string
  dataset IDs, skips empty datasets, and prepends `dataset_id` before each
  label row's existing fields. It does not summarize coverage because the
  coverage helpers already provide compact label metadata.
- Supplied label coverage `dataset_id` values must be non-blank strings. Pass
  `None` when a forward-return or local-extrema coverage row should remain
  unnamed. Dataset IDs are never trimmed implicitly; leading or trailing
  whitespace is rejected so exported identifiers stay explicit.
- Use `local_extrema_label_coverage_row()` before exporting retrospective
  top/bottom labels when the edge-row footprint needs to be visible. Centered
  local-extrema windows intentionally leave rows near the start and end
  unlabeled; the coverage row reports those missing labels but does not make
  local top/bottom values valid future-looking prediction targets.
- Use `multi_window_local_extrema_label_coverage_rows()` when a single
  retrospective label table carries several centered windows. The helper keeps
  requested window order, removes duplicate windows, and returns flat coverage
  rows for CSV or notebook audits while preserving the same retrospective-label
  caveat as `local_extrema_label_coverage_row()`.
- Use `multi_dataset_local_extrema_label_coverage_rows()` when retrospective
  label coverage needs one audit table across several named datasets. The
  helper preserves dataset and window order, rejects blank, whitespace-padded,
  or duplicate dataset IDs, and delegates row fields to the existing
  local-extrema coverage helpers; it is multi-dataset audit metadata, not a
  replacement for inspecting the
  underlying label rows.
- Use `local_extrema_label_group_rows()` when the audit needs those underlying
  raw retrospective local-extrema label rows from several declared datasets in
  one flat table. The helper preserves caller order, rejects
  blank/duplicate/non-string dataset IDs, skips empty datasets, and prepends
  `dataset_id` before each label row's existing fields. It does not make
  centered local-extrema labels predictive; it only groups raw retrospective
  label rows for export.
- Forward-return and local-extrema grouped label row helpers share the same
  private named-dataset assembly path. Keep dataset ID validation, whitespace
  rejection, duplicate rejection, empty-dataset skipping, and raw row prepending
  behavior aligned there instead of changing only one public helper. Ordered
  named label dataset inputs must contain explicit two-item `(dataset_id,
  labels)` pairs; strings, bytes, and malformed tuple/list lengths are rejected
  before Python tuple unpacking can raise a generic error.

### Local Candle Cache Files

`write_candles_json()` and `read_candles_json()` persist normalized
`MarketCandle` rows as a JSON list. Cache files must contain at least one row,
must include `timestamp`, `asset`, `open`, `high`, `low`, `close`, and
`interval`, string fields must be non-blank after trimming whitespace, and
timestamps must be timezone-aware ISO datetimes. Optional `source` metadata must
also be non-blank when present. These files are
convenience caches for repeatable local research runs, not audit-grade market
data stores; keep upstream source metadata and regenerate them when provider
normalization rules change.
Use `candle_dataset_summary_row()` for compact cache audit tables before joins
or label generation. It requires a non-empty single-asset, single-interval
dataset, reports chronological first/last timestamp boundaries even if input
rows are unsorted, and leaves `source` as `None` when rows come from mixed or
unknown sources.
Use `candle_dataset_summary_rows()` when a report compares several cached
datasets in one flat table. The helper preserves caller order from mappings or
ordered `(dataset_id, candles)` pairs, requires supplied dataset IDs to be
non-blank strings without leading or trailing whitespace, rejects duplicates,
rejects malformed ordered entries before tuple unpacking, and keeps the same
single-dataset validation as
`candle_dataset_summary_row()`.
It is compact cache metadata only, not a replacement for exporting the
underlying candle rows.
Use `candle_dataset_group_rows()` when the audit needs those underlying
normalized candle rows from several declared datasets in one flat table. The
helper preserves caller order, rejects blank/duplicate/non-string or
whitespace-padded dataset IDs, skips empty datasets, and prepends `dataset_id`
before the existing `MarketCandle.to_dict()` fields. It does not enforce
single-asset or single-interval datasets because it exports raw grouped rows
rather than cache metadata.

### Small Sample Size

Some aspects occur rarely. Probabilities can look impressive but be statistically weak.

Mitigation:

- Always report event count.
- Add low-sample warnings.
- Use bootstrap confidence intervals.
- Compare against random baselines.
- Seed bootstrap and random-baseline helpers when results need to be reproducible in docs, tests, or PR reviews.
- Use `bootstrap_interval_row()` before writing standalone bootstrap interval
  reports to CSV. It expects the two-bound tuple returned by
  `bootstrap_percentile_interval()` and rejects malformed, missing, or non-finite
  bounds with a clear validation error instead of letting export code infer a
  schema.
- Use `bootstrap_interval_rows()` before writing a compact table of several
  predeclared bootstrap intervals. It accepts an ordered mapping or ordered
  `(statistic_name, interval)` pairs, requires statistic names to be non-blank
  strings, rejects duplicates, and reuses `bootstrap_interval_row()` for each
  interval; malformed ordered entries and malformed interval values are rejected
  before generic tuple unpacking or length errors can leak through. It does not
  replace the raw bootstrap distribution or the single-interval helper.
- Seed `permutation_test()` and report its `alternative`, `permutations`, and
  p-value correction behavior when using permutation p-values in research notes.
- Use `summarize_validated_event_study()` when a report should carry the core
  event-study summary, low-sample warning, bootstrap settings, and optional
  return confidence interval together. If selected event rows have no valid
  forward returns, the helper leaves the interval as `None` instead of failing.
- Use `summarize_validated_multi_horizon_event_study()` when comparing the same
  selected events across horizons. It deduplicates repeated horizons in caller
  order and applies identical bootstrap/sample-size settings to each horizon so
  notebook reports do not accidentally mix validation metadata.
- Use `validated_event_study_report_row()` before CSV export. `to_csv()` is
  intentionally generic and rejects nested values, while validated reports keep
  their JSON representation nested; the flat row helper bridges those two
  formats, emits `None` for missing interval bounds, and rejects malformed
  report values before attribute access can leak implementation-detail errors.
- Use `validated_multi_horizon_event_study_report_rows()` before CSV export
  when `summarize_validated_multi_horizon_event_study()` produced several
  reports. The helper preserves mapping or sequence order and reuses the
  single-report row flattener, so missing confidence intervals still emit
  `None` lower/upper bounds.
- Use `validated_multi_horizon_event_study_report_group_rows()` when combining
  several declared validated-report scenarios into one audit table. It preserves
  ordered mappings or `(report_group_id, reports)` pairs, requires group IDs to
  be non-blank strings, rejects duplicates, skips empty groups, and prepends
  `report_group_id`; malformed ordered entries are rejected before tuple
  unpacking, and malformed report values are rejected before row flattening.
  Keep the original `ValidatedEventStudyReport` objects for detailed inspection.

### Permutation Test Interpretation

`permutation_test()` compares observed outcomes with baseline outcomes by
randomly relabeling the combined sample. It validates only the supplied
statistic and alternative direction. If the aspect, horizon, orb, date range, or
statistic was chosen after looking at many alternatives, the p-value is still
exploratory and should be paired with the anti-overfitting guide.

The helper raises `ValueError` for empty samples, non-positive permutation
counts, unsupported alternatives, or statistics that do not return finite
numeric values.

Use `permutation_test_result_row()` before writing permutation reports with the
flat CSV exporter. `PermutationTestResult.to_dict()` intentionally keeps the full
`null_distribution` list for JSON inspection, while the row helper emits compact
distribution metadata (`count`, `min`, and `max`) that is CSV-safe. If a manually
constructed result has an empty distribution, the count is `0` and the min/max
fields are `None`.
Use `permutation_test_result_rows()` for compact multi-scenario permutation
metadata tables. It preserves ordered mapping or pair-sequence input, rejects
scenario IDs that are not non-blank strings, rejects duplicates, and prepends
`scenario_id` while keeping full null distributions out of CSV output.
Malformed ordered entries are rejected before tuple unpacking so caller shape
errors stay explicit.

Use `random_baseline_distribution_row()` when random-baseline results need the
same compact CSV treatment. `random_baseline_distribution()` intentionally
returns the full statistic list for plots and JSON inspection; the row helper
summarizes that list as count, min, max, and mean, plus optional sample-size,
sample-count, and seed metadata. Empty distributions emit `0` count and `None`
summary values instead of raising from `min()` or `max()`.

Use `random_baseline_distribution_rows()` for compact multi-scenario baseline
tables. It accepts an ordered mapping or ordered `(baseline_id, distribution)`
pairs, rejects baseline IDs that are not non-blank strings, rejects duplicates,
prepends `baseline_id`, and reuses the single-distribution row helper for
summary fields. Malformed ordered entries and malformed distribution values are
rejected before tuple unpacking or iteration errors can leak through. It is for
audit metadata, not a replacement for inspecting or plotting full distributions.

### Walk-Forward Split Boundaries

`walk_forward_splits()` expects ordered observations or a positive observation
count. It rejects empty inputs, non-positive train/test/step sizes, impossible
window lengths, and `step_size < test_size` because that would create overlapping
test windows in reports. Train windows are rolling fixed-size slices and each
test window starts immediately after its matching train window, so future test
observations are not included in that train slice.

Use `walk_forward_split_rows()` before writing split reports with the flat CSV
exporter. `WalkForwardSplit.to_dict()` intentionally keeps the full train/test
windows for JSON inspection, while the row helper emits compact boundary,
window-size, and endpoint fields. Endpoint values are included only when they
are CSV-safe scalars; nested observations such as mappings or lists are emitted
as `None` in the endpoint columns. Malformed split values are rejected as clear
validation errors before attribute access.
Use `walk_forward_split_group_rows()` when a report compares several declared
split configurations, such as train/test sizes, step sizes, or asset subsets.
It preserves mapping or pair-sequence order, rejects split group IDs that are
not non-blank strings, rejects duplicates, prepends `split_group_id`, and emits
no rows for empty groups. Malformed ordered entries are rejected before tuple
unpacking, and malformed split values are rejected before row flattening. Keep
the original `WalkForwardSplit` objects for inspecting full train/test windows.

### Nearest-Neighbor Report Rows

`find_nearest()` preserves caller-owned payload values on `NearestNeighbor`
results for in-memory inspection. Use `nearest_neighbor_rows()` before writing
similarity rankings with `to_csv()`. The row helper emits rank, ID, score, and
distance fields; scalar payloads are included as `payload`, while mapping
payloads require explicit non-blank `payload_fields` so report columns stay
intentional. Blank payload field names raise `ValueError`, and selected nested
payload fields raise `TypeError` instead of letting the generic CSV exporter
fail later with an unclear schema.
Use `nearest_neighbor_group_rows()` when a report needs one ranked-neighbor
audit table across several declared similarity searches. It rejects blank or
duplicate search IDs, requires supplied search IDs to be strings without
leading or trailing whitespace, skips empty result groups, prepends `search_id`,
rejects malformed ordered entries before tuple unpacking, and delegates rank
and payload columns to `nearest_neighbor_rows()`; keep the raw
`NearestNeighbor` objects for deeper payload inspection.
Use `nearest_neighbor_summary_row()` when reports need one compact row per
similarity search run. It keeps payload inspection out of the summary, uses the
first ranked result as the top neighbor, reports min/max score and distance
boundaries across the supplied results, and emits `None` boundary fields for
empty result sets.
Use `nearest_neighbor_summary_rows()` when a report compares several predeclared
similarity searches. The helper preserves caller order, rejects blank or
duplicate search IDs, prepends `search_id`, and can attach per-search
`query_id`, `metric`, and `limit` metadata while reusing the single-search
summary schema. Those optional metadata mappings must use declared non-blank
string search IDs without leading or trailing whitespace; unknown metadata IDs
are rejected so typos do not silently disappear from audit reports. Ordered
search inputs and optional metadata inputs must contain explicit two-item pairs
and are rejected before Python tuple unpacking can raise a generic error. Keep
`nearest_neighbor_rows()` or the raw `NearestNeighbor` values for
ranked neighbor and payload inspection.

### Exact-Orb Aspect Queries

Aspect detection supports `max_orb=0` for exact-match searches. Decimal
longitude arithmetic can leave tiny floating-point residuals around an otherwise
exact angle, so exact-orb matching treats residuals within `1e-9` degrees as
zero and records the event with `orb=0.0` and `strength=1.0`.

### Historical Aspect Scans

`scan_aspect_series()` groups `PlanetPosition` rows by exact timestamp and scans
each timestamp independently. Missing bodies at a timestamp are not filled or
carried forward from nearby timestamps; only bodies present in that group are
scanned. Position timestamps must be timezone-aware, body names must be
non-empty, and duplicate body rows for the same timestamp are rejected so a scan
cannot silently choose between conflicting longitudes.
Use `aspect_scan_summary_row()` before exporting or joining scan results when a
compact audit row is needed. Empty scans emit zero counts and `None` timestamp
boundaries. Raw-longitude `find_aspects()` workflows may produce events without
timestamps; those are counted in `missing_timestamp_count` and excluded from
timestamp boundaries.
Use `aspect_scan_summary_rows()` when a report compares several named scan
configurations, such as different body sets, orb settings, date ranges, or
ephemeris engines. The helper keeps caller order, prepends `scan_id`, rejects
scan IDs that are not non-blank strings or include leading/trailing whitespace,
rejects duplicates, and reuses the single-scan summary schema for each row; it
is batch audit metadata, not a replacement for exporting raw aspect events or
feature rows.
Use `aspect_scan_event_group_rows()` when several named scans need one flat raw
aspect-event audit table. The helper keeps caller order, prepends `scan_id`,
rejects scan IDs that are not non-blank strings or include leading/trailing
whitespace, rejects duplicates, skips empty scan groups, and delegates event
columns to `AspectEvent.to_dict()`. Keep `AspectEvent` objects for inspection,
feature-row helpers for model inputs, and summary rows for compact scan
metadata. Ordered named scan inputs must contain explicit two-item `(scan_id,
events)` pairs; malformed entries are rejected before Python tuple unpacking
can raise a generic error.
Aspect scan summary and grouped event helpers require every supplied scan event
value to be an `AspectEvent`. Malformed event values are rejected with a clear
validation error before summary counts, timestamp boundaries, or raw event row
construction read event attributes.

### Planet-Position Encoding Reports

`encode_planet_positions()` intentionally returns only the numeric sine/cosine
vector needed for similarity ranking. Use `planet_position_encoding_rows()` when
reports need to show how that vector was built. The row helper sorts positions
with the same timestamp/body/zodiac key, keeps the original longitude visible,
and emits `longitude_sin` and `longitude_cos` columns that can be written with
the flat CSV exporter.

Use `planet_position_vector_summary_row()` when reports need one compact row per
chart state. It emits optional chart ID, position count, vector length, and
first/last timestamp/body/zodiac metadata using the same ordering as the vector
encoder. Keep using `encode_planet_positions()` for numeric similarity search
and `planet_position_encoding_rows()` when individual sine/cosine components
must be inspected.
Use `planet_position_encoding_group_rows()` when reports need one per-position
encoding audit table for several named chart states. It prepends `chart_id`,
skips empty groups, requires chart IDs to be non-blank strings without leading
or trailing whitespace, rejects duplicates, rejects malformed ordered entries
before tuple unpacking, and delegates each non-empty group to
`planet_position_encoding_rows()`. Keep raw
`PlanetPosition` objects and numeric vectors for deeper inspection or
similarity search.
Use `planet_position_vector_summary_rows()` when audit reports compare several
named chart states in one flat table. It preserves caller order from mappings or
`(chart_id, positions)` pairs, requires chart IDs to be non-blank strings
without leading or trailing whitespace, rejects duplicates, rejects malformed
ordered entries before tuple unpacking, and keeps the same metadata-only role as
the single-chart helper.
Similarity position encoding and vector summary helpers require every supplied
position value to be a `PlanetPosition`. Malformed position values are rejected
with a clear validation error before sorting, longitude encoding, or metadata
field access so caller mistakes do not surface as implementation-detail
attribute errors.

### Aspect Phase Classification

`find_aspects()` and `scan_aspect_series()` classify `AspectEvent.phase` only
when both paired `PlanetPosition` values include longitude `speed`. Exact
aspects within the shared angle tolerance return `phase="exact"`; otherwise the
classifier projects each longitude by a tiny step in the supplied speed
direction and marks the orb as `applying` when it is shrinking or `separating`
when it is widening. Raw float longitude inputs and pairs with missing speed
data continue to return `phase="unknown"`.

This is a simplified longitude-speed classification. Retrograde and negative
speed values are handled through their sign, but downstream research reports
should still record the ephemeris engine and speed convention used to generate
the positions.

### Exact Timestamp Event Joins

`join_aspect_events_to_market_labels()` performs exact timestamp joins between
timestamped `AspectEvent` values and market label rows. It does not resample,
round, or fuzzy-match timestamps. Duplicate market-label timestamps raise
`ValueError`, because the event-study label index would be ambiguous. Aspect
events without timestamps also raise `ValueError`.

Unmatched events are skipped from `event_indexes` and reported through
`unmatched_event_indexes` and `unmatched_events`. Review those counts before
interpreting event-study summaries; a high unmatched count usually means the
ephemeris sampling cadence and candle/label timestamps are misaligned.

Use `timestamp_join_summary_row()` before CSV export when notebooks or future
CLIs need only compact join audit metadata. The summary row intentionally keeps
the nested joined records and full unmatched-event detail in
`TimestampJoinResult.to_dict()` so researchers can inspect the full join when a
count looks suspicious. Malformed join result values are rejected before
attribute access can leak implementation-detail errors.
Use `timestamp_join_summary_rows()` when several predeclared exact joins need
one compact CSV-safe audit table. The helper preserves caller order, requires
join IDs to be non-blank strings, rejects duplicates, prepends `join_id`, and
reuses the single-join summary fields; inspect `TimestampJoinResult.joined`
when row counts look suspicious. Ordered named join inputs must contain explicit
two-item `(join_id, result)` pairs; strings, bytes, and malformed tuple/list
lengths are rejected before Python tuple unpacking can raise a generic error,
and malformed join result values are rejected before row flattening.

Use `add_candle_forward_returns()` instead of the bare close-list helper when an
event-study workflow starts from `MarketCandle` rows. It preserves candle
timestamps and asset names for exact joins while reusing the same forward-return
math. Mixed-asset candle inputs raise `ValueError`; split or normalize assets
before building one label table.

Use `add_candle_local_extrema_labels()` when local top/bottom outcomes need the
same timestamp and asset metadata. It wraps the bare close-list extrema helper,
so centered-window edge rows still emit `None` values and mixed-asset candle
inputs still raise `ValueError`.

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
exactly apart from missing fields, which are emitted as blank cells. Explicit
CSV field names are trimmed before output and must be non-blank and unique, so
notebook and audit exports do not produce ambiguous schema headers.
`write_json()` and `write_csv()` create missing parent directories before
writing, matching the market candle cache helper so notebook and future CLI
export paths can target nested output folders directly.

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
serialization of mappings, sequences, and model objects with `to_dict()`. JSON
object keys must be strings, must not be blank, and must not contain leading or
trailing whitespace at any nesting level.

Use `to_csv()` or `write_csv()` only for flat row data. CSV export writes a
stable header based on first-seen field order unless `fieldnames=` is supplied,
and it rejects blank or whitespace-padded row keys before inferring that header.
It trims explicit field names before rejecting blank or duplicate names. It raises
`TypeError` for nested dictionaries, lists, tuples, or other structured values.
Flatten nested research outputs explicitly before exporting them to CSV so
column names remain auditable.

`aspect_event_feature_rows()` is the preferred flattening helper for
`AspectEvent` rows. It preserves input ordering, leaves missing timestamps as
`None`, and emits only scalar values, so its output can be exported through
`to_csv()` without nested-value errors. The helper records the row as an active
aspect event; it does not pivot absent aspects into false indicator columns.
Aspect feature row builders require `body_a`, `body_b`, and `aspect` values to
be non-blank strings so malformed external events fail before ambiguous column
keys are produced.
Use `aspect_event_feature_group_rows()` when several declared event groups need
one raw feature-row export. It preserves caller group order and event order,
rejects blank/duplicate/non-string or whitespace-padded group IDs, skips empty
groups, rejects malformed ordered entries before tuple unpacking, prepends
`group_id`, and reuses `aspect_event_feature_rows()` so malformed aspect
components keep the same validation behavior. Use matrix helpers only when the
report needs timestamp-level pivoted feature columns or matrix metadata.

Use `aspect_event_feature_matrix_rows()` when downstream code needs one row per
timestamp with deterministic aspect indicator columns. It rejects untimestamped
events because they cannot be placed in the matrix and rejects duplicate
feature keys at the same timestamp because the orb/strength/phase value would
be ambiguous. Feature columns are derived only from aspects present in the
supplied events; missing columns mean the dataset did not contain that aspect,
not that a complete ephemeris scan proved it absent.

Use `aspect_event_feature_matrix_rows_with_schema()` when downstream train/test
or walk-forward splits need stable columns across datasets. Configured features
that are absent at a timestamp emit `False` for `_active` and `None` for
`_orb`, `_strength`, and `_phase`; this only means the configured feature was
not observed in the supplied events. It does not prove the feature was absent
from a complete ephemeris scan unless the caller supplied a complete scan and
schema. Unknown observed features are included by default and appended after
configured columns; pass `include_unknown_features=False` to reject them during
strict production exports. Configured aspect feature keys must be non-blank
strings; non-string entries are rejected before normalization so configuration
mistakes fail as library validation errors instead of string-method failures.

Use `aspect_event_feature_matrix_summary_row()` before CSV export or model
training when an audit needs matrix shape metadata without writing the full
wide matrix. The helper counts unique timestamp rows, observed feature keys,
optional unique configured feature keys, duplicate configured keys after the
same normalization used by schema helpers, and events missing timestamps.
Missing timestamps are counted but excluded from row count and first/last
timestamp boundaries because they cannot become matrix rows.
Use `aspect_event_feature_matrix_summary_rows()` when batch feature-matrix
audits need one flat table across named matrices. It preserves caller order from
ordered mappings or `(matrix_id, events)` pairs, requires matrix IDs to be
non-blank strings without leading or trailing whitespace, rejects duplicates,
rejects malformed ordered entries before tuple unpacking, supports shared or
per-matrix configured feature keys, and keeps the same metadata-only role as
the single-row helper. When configured feature keys are supplied per matrix,
each configured matrix ID must also be a non-blank string without leading or
trailing whitespace and match a declared matrix ID so notebook and CLI audit
setup mistakes fail early. Shared and per-matrix configured feature keys must
also be non-blank strings.

`event_study_baseline_comparison_row()` is the preferred flat row helper when
reports need probability deltas and relative lift. It leaves derived fields as
`None` if either probability is missing, and leaves `relative_lift` as `None`
when baseline probability is zero to avoid division-by-zero ambiguity. Malformed
result values are rejected before attribute access can leak implementation-detail
errors.
Use `multi_horizon_baseline_comparison_rows()` when the same baseline comparison
columns are needed for ordered multi-horizon summaries. It accepts the mapping
returned by `summarize_multi_horizon_event_study()` or an already ordered
sequence of `EventStudyResult` values, preserves caller order, and returns an
empty list for empty input.
Use `multi_horizon_baseline_comparison_group_rows()` when combining several
declared baseline-comparison result sets into one audit table. The helper
accepts an ordered mapping or ordered `(comparison_group_id, results)` pairs,
prepends `comparison_group_id`, requires group IDs to be non-blank strings
without leading or trailing whitespace, rejects duplicates, rejects malformed
ordered entries before tuple unpacking, rejects malformed result values before
row flattening, and emits no rows for empty groups. It is multi-scenario audit
metadata only; keep the raw `EventStudyResult` values for statistical
interpretation and deeper review.
Validated event-study report groups and timestamp-join summary IDs follow the
same identifier boundary: callers must pass explicit, already-normalized IDs
instead of relying on export helpers to trim ambiguous whitespace.
Validation report helpers use the same boundary for permutation scenario IDs,
random-baseline IDs, bootstrap statistic names, and walk-forward split group
IDs. Rejecting whitespace-padded identifiers keeps downstream CSV and notebook
joins explicit instead of mixing visually similar report labels.

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
