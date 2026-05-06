# Statistical Methods

Hermetic Alpha should start with transparent methods before adding complex models.

## 1. Event Study

Event study is the first core method.

Process:

1. Detect all timestamps where an aspect is active.
2. Join each event with market data.
3. Calculate forward returns after selected horizons.
4. Summarize bullish probability, average return, median return, and sample size.

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

## 5. Permutation Test

Permutation tests help check whether observed results are stronger than random chance.

Process:

1. Keep market data fixed.
2. Randomly shuffle event dates or sample random dates.
3. Recalculate event-study metrics.
4. Compare the real result against the random distribution.

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

## Reporting Requirements

Every result should show:

- Event count.
- Baseline probability.
- Conditional probability.
- Average return.
- Median return.
- Confidence interval where available.
- Warning if sample size is too small.
