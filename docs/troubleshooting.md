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
- Treat `local_top_*` and `local_bottom_*` labels as retrospective outcomes only because centered windows inspect candles after the labeled timestamp.

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
