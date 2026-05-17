# Anti-Overfitting Guide

Hermetic Alpha treats astro-financial research as exploratory statistics, not
deterministic prediction or financial advice. A result is only useful when a
reader can see how it was selected, how many observations support it, how it
compares with the market baseline, and how uncertain the estimate remains.

## Responsible Interpretation

Probabilities such as `P(bullish | aspect)` should be read as conditional
historical frequencies for a specific dataset and rule set. They do not imply
that the same outcome will happen in the future.

Every reported signal should include:

- The exact aspect, orb, asset, date range, and market label definition.
- Event count and the number of valid market windows.
- Baseline probability for the same asset and horizon.
- Conditional probability for the selected aspect events.
- Average and median forward return where available.
- Confidence interval or another uncertainty estimate.
- A warning when sample size is too small for a stable interpretation.

## Baseline Comparison

A signal is not meaningful just because its conditional probability is above
50%. Compare it against the asset's baseline behavior for the same horizon.

Example:

```text
Baseline BTC bullish 7D probability: 53%
Sun-Jupiter conjunction bullish 7D probability: 58%
Event count: 12
```

This should be treated as weak exploratory evidence because the difference is
small and the sample is limited. A larger difference can still be fragile if it
comes from a small number of events or a narrow date range.

## Sample Size

Rare aspects can create impressive-looking percentages from only a few
observations. Reports should avoid strong wording when the event count is low.
Use `low_sample_warning()` in generated summaries and prefer larger date ranges
when the selected aspect occurs rarely.

## Confidence Intervals

Confidence intervals make uncertainty visible. A wide interval means the
estimated effect is unstable even when the point estimate looks interesting.
For exploratory reports, bootstrap intervals are acceptable as a transparent
first pass when their assumptions are documented.

## Data Leakage

Never use future-looking labels as predictive features. Centered local-top and
local-bottom labels are retrospective outcomes because they inspect candles
after the labeled timestamp. They can support event-study analysis, but they
must not be fed into a forward-looking model as if they were known at the time.

For chronological validation, use `walk_forward_splits()` to keep each test
window strictly after its train window. The helper makes split boundaries
inspectable, but the resulting scores remain exploratory unless the hypothesis,
features, horizons, and reporting metric were chosen before evaluating the
holdout windows.

## Cherry-Picking Control

Overfitting risk grows when many aspects, orbs, assets, horizons, and date
ranges are tested. To reduce false discoveries:

- Record every tested hypothesis, including weak or failed results.
- Prefer predeclared aspect/orb/horizon sets for formal comparisons.
- Compare against random baseline distributions or permutation tests.
- Recheck promising findings on later out-of-sample periods.
- Prefer walk-forward windows when evaluating rules over chronological market
  samples.
- Avoid changing the rule set after seeing the result unless the change is
  clearly marked as exploratory.

When using `permutation_test()`, record the statistic, alternative direction,
permutation count, and seed with the result. Treat the p-value as a check
against one declared random-label baseline, not as proof that the relationship
will persist out of sample.

## Reporting Language

Use cautious language:

- Prefer "historically associated with" over "predicts".
- Prefer "exploratory signal" over "edge" until validation is stronger.
- Prefer "needs out-of-sample validation" when the finding was discovered by
  scanning many possibilities.

Do not present Hermetic Alpha output as deterministic trading guidance.
