# Statistical Methods

Hermetic Alpha should start with transparent methods before adding complex models.

All statistical reports should follow the
[anti-overfitting guide](anti-overfitting.md). Probability estimates are
exploratory unless they include enough observations, baseline comparison,
uncertainty estimates, and validation outside the discovery sample.

## 1. Event Study

Event study is the first core method.

Process:

1. Detect all timestamps where an aspect is active.
2. Join each event with market data.
3. Calculate forward returns after selected horizons.
4. Summarize bullish probability, average return, median return, and sample size.

Use `scan_aspect_series()` when event studies start from timestamped
`PlanetPosition` rows. It scans each timestamp independently and preserves the
event timestamp so joins to market labels stay explicit.
Use `join_aspect_events_to_market_labels()` when aspect events and market labels
need exact timestamp matching before calling `summarize_event_study()`. The
helper rejects duplicate market-label timestamps and untimestamped aspect
events, skips unmatched events, and reports matched label indexes plus unmatched
event indexes for audit notes.
Use `timestamp_join_summary_row()` when the exact-join result needs a compact
CSV-safe audit row. It reports matched/unmatched counts and first/last matched
or unmatched event indexes without replacing the full `TimestampJoinResult`
object used for inspection.

Multi-horizon event studies should reuse the same selected event indexes across all configured horizons so 1D, 7D, and 30D summaries are comparable and auditable.

Use `summarize_validated_event_study()` when a report should bundle the core
event-study summary with validation metadata. The helper delegates core
statistics to `summarize_event_study()`, adds `low_sample_warning()` output for
the matched event count, and optionally computes a seeded bootstrap percentile
interval for event forward returns when valid returns exist.
Use `summarize_validated_multi_horizon_event_study()` when the same selected
events need cautious reports across ordered horizons. The helper preserves
caller horizon order, deduplicates repeated horizons, and passes the same
bootstrap and minimum-sample settings to every single-horizon report.
Use `validated_event_study_report_row()` when that validated report needs CSV
output. It converts the nested summary and validation metadata into explicit
flat scalar columns, including separate lower/upper return confidence interval
fields, so the generic CSV exporter can remain limited to flat rows.
Use `validated_multi_horizon_event_study_report_rows()` when the ordered
mapping from `summarize_validated_multi_horizon_event_study()` needs CSV output.
It preserves report order and delegates each row to the single-report flattener;
it is an export convenience, not a separate statistical method.
Use `event_study_baseline_comparison_row()` when a report needs explicit
baseline comparison fields. It preserves the core event count and probabilities,
then adds absolute `probability_delta` and relative `relative_lift` values while
returning `None` when probabilities are missing or the baseline is zero.

Example output:

```text
Aspect: Sun conjunct Jupiter
Orb: <= 3°
Events: 42
Bullish 7D: 64.2%
Average Return 7D: +3.8%
Median Return 7D: +1.9%
```

## 2. Conditional Probability

The basic question:

```text
P(bullish | aspect)
```

Formula:

```text
number of bullish outcomes after aspect / total aspect events
```

Always compare against baseline:

```text
P(bullish)
```

If BTC rises 53% of all 7-day windows, and Sun-Jupiter conjunction has 64% bullish 7-day outcomes, the difference is worth investigating.

## 3. Baseline Comparison

Every signal should be compared with a baseline.

Recommended baselines:

- All market windows.
- Random timestamps with same sample size.
- Same asset and same horizon.
- Same market regime if regime filtering exists later.

Baseline comparison deltas are reporting conveniences, not predictive claims.
`relative_lift` is calculated as `(conditional - baseline) / baseline`, so a
zero baseline is intentionally left as `None` instead of inventing an infinite
or undefined value.
Use `multi_horizon_baseline_comparison_rows()` when ordered
`summarize_multi_horizon_event_study()` results need the same flat baseline
comparison fields for CSV or notebook tables. It is an export convenience, not a
new statistical method, and each row still delegates to the single-horizon
baseline comparison helper.

## 4. Bootstrap Confidence Interval

Bootstrap can estimate uncertainty around probabilities and average returns.

Process:

1. Resample event outcomes with replacement.
2. Recalculate the statistic many times.
3. Report the percentile range.

Example:

```text
Conditional bullish probability: 64.2%
95% CI: 49.8% - 76.4%
```

The library exposes `bootstrap_percentile_interval()` for dependency-free
percentile intervals. It resamples the observed values with replacement,
supports a deterministic random seed, and accepts a custom statistic function
for probabilities or other summary metrics.
Use `bootstrap_interval_row()` when a standalone bootstrap interval needs a
compact CSV-safe report. The raw tuple remains the right output for Python
workflows that immediately feed the interval into another calculation; the row
helper adds explicit lower/upper bound columns plus optional sample count,
confidence, seed, and statistic-name metadata for notebooks and audit exports.

## 5. Permutation Test

Permutation tests help check whether observed results are stronger than random chance.

Process:

1. Keep market data fixed.
2. Randomly shuffle event dates or sample random dates.
3. Recalculate event-study metrics.
4. Compare the real result against the random distribution.

The initial validation helper is `random_baseline_distribution()`. It samples
random baseline subsets without replacement, supports a deterministic seed, and
returns the selected statistic for each sample. This is a simple baseline
distribution, not proof of causality.
Use `random_baseline_distribution_row()` when a compact flat report is needed
for CSV output. It keeps the full distribution list out of the row and emits
count, minimum, maximum, mean, and optional sample metadata instead.

The library also exposes `permutation_test()` for dependency-free two-sample
random relabeling. Pass observed event outcomes and baseline outcomes, choose a
statistic such as mean return or bullish probability, and set `seed=` when the
report must be reproducible. The helper returns a `PermutationTestResult` with
the observed statistic, null distribution, null mean, p-value, alternative,
permutation count, and seed metadata. P-values use plus-one correction and can
be calculated as `greater`, `less`, or `two-sided`.
Use `permutation_test_result_row()` before CSV export when reports need a compact
flat summary. It preserves the key statistic, p-value, alternative, permutation
count, seed, and null mean fields, while replacing the full null distribution
list with count, minimum, and maximum metadata.

Permutation tests do not remove overfitting by themselves. They only compare one
declared statistic against a random relabeling baseline for the supplied sample.
Use them with predeclared hypotheses, sample-size warnings, and out-of-sample
checks before treating a pattern as meaningful.

## 6. Logistic Regression

Useful after the event-study engine is stable.

Target:

```text
bullish_7d = 1 if return_7d > 0 else 0
```

Features:

- Aspect active flags.
- Aspect strength.
- Moon phase angle.
- Retrograde flags.
- Volatility/trend controls.

Benefit:

- Explainable coefficients.
- Good baseline model.
- Easier to audit than black-box ML.

## 7. Similarity Search

Chart states can be encoded as vectors and compared against historical states.

Important: circular degrees should use sine/cosine encoding.

```text
longitude_sin = sin(longitude)
longitude_cos = cos(longitude)
```

`hermetic_alpha.similarity.encode_planet_positions()` applies this encoding to
`PlanetPosition` values with deterministic timestamp/body/zodiac ordering. The
helper creates numeric chart-state vectors that can be passed to
`find_nearest()` with `SimilarityCandidate` values for dependency-free
nearest-neighbor ranking. The default metric is cosine similarity; Euclidean
distance is also available. Empty candidate sets return no neighbors, while
empty vectors, zero vectors under cosine similarity, and vector length
mismatches raise `ValueError`.

Recommended methods:

- K-nearest neighbors.
- Cosine similarity.
- Circular distance for aspect angle differences.

## 8. Walk-Forward Validation

To reduce overfitting:

1. Train or discover patterns on an earlier time period.
2. Test on a later unseen period.
3. Move the window forward.
4. Report stability.

Use `walk_forward_splits()` to generate dependency-free chronological
train/test window definitions from ordered observations or positional indexes.
The helper uses fixed `train_size`, `test_size`, and optional `step_size`
values. Every test window begins immediately after its train window, and
`step_size` must be at least `test_size` so reported test windows do not overlap.
Use `walk_forward_split_rows()` before CSV export when reports need compact
split boundaries instead of the full nested train/test windows. It preserves
split order, includes boundary and size fields, and emits scalar endpoint
values when they are CSV-safe.
Walk-forward validation reduces leakage risk, but it does not prove predictive
value by itself.

## Reporting Requirements

Every result should show:

- Event count.
- Baseline probability.
- Conditional probability.
- Average return.
- Median return.
- Confidence interval where available.
- Warning if sample size is too small.

Use `low_sample_warning()` to surface small-sample caveats in reports. Low
sample warnings do not invalidate a result; they mark it as exploratory until
more observations are available.
