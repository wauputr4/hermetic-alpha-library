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

### Timezone and Candle Alignment

Market candles and astro timestamps must be aligned carefully.

Mitigation:

- Internally use UTC.
- Make candle interval explicit.
- Avoid mixing daily candles from different exchange timezone conventions without recording the source.

### Small Sample Size

Some aspects occur rarely. Probabilities can look impressive but be statistically weak.

Mitigation:

- Always report event count.
- Add low-sample warnings.
- Use bootstrap confidence intervals.
- Compare against random baselines.

### Data Leakage

Top/bottom labels require future data, so they must not be used as predictive features.

Mitigation:

- Keep labels separate from features.
- Clearly document whether an analysis is retrospective or predictive.

### Overfitting and Cherry-Picking

Testing many aspects can produce false positives.

Mitigation:

- Report all tested hypotheses.
- Use holdout periods.
- Add permutation tests.
- Avoid claiming deterministic prediction.

## Git and Release Workflow

Wau's preferred workflow:

- Update docs/context/troubleshooting after coding.
- Commit and push completed changes using GitHub CLI when available.
- Keep library and CLI responsibilities separated.

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
