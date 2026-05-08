# ADR 0001: First Ephemeris Engine

## Status

Accepted for first experimental integration.

## Context

Hermetic Alpha needs an ephemeris engine that can produce planetary ecliptic
longitudes for UTC timestamps and expose enough motion data to derive
retrograde status. The first backend should support reproducible research while
keeping the core library independent from CLI, notebook, API, or dashboard
concerns.

The evaluated candidates were:

- Kerykeion
- Immanuel Python
- pyswisseph / Swiss Ephemeris

Evaluation criteria from issue #5:

- Accuracy and reliability.
- License compatibility for open source.
- Ease of installation.
- Ability to produce planetary longitudes and retrograde status.
- Long-term maintainability.

## Decision

Use `pyswisseph` as the first experimental ephemeris backend, wrapped behind a
small Hermetic Alpha adapter instead of exposing `swisseph` objects directly.

The adapter should:

- Accept timezone-aware UTC `datetime` values.
- Return Hermetic Alpha `PlanetPosition` models.
- Normalize longitudes to `[0, 360)`.
- Derive `retrograde` from negative apparent speed when speed is available.
- Record the backend name and version in generated datasets when dataset
  metadata exists.
- Stay optional until licensing and packaging policy are finalized.

## Rationale

`pyswisseph` is closest to the raw calculation layer Hermetic Alpha needs. It
wraps Swiss Ephemeris directly, exposes planetary position data including speed,
and avoids forcing the library through birth-chart-oriented abstractions before
the research model is stable.

Kerykeion and Immanuel remain useful references because they provide higher
level astrology workflows and structured chart output. They are not the first
backend because Hermetic Alpha currently needs a narrow, auditable source of
positions for time-series research rather than full chart rendering,
interpretation, localization, or synastry features.

## Candidate Notes

### Kerykeion

Strengths:

- Actively maintained astrology library.
- Provides chart calculations, aspects, and structured astrology concepts.
- Documentation emphasizes correctness and transparent design.

Limitations:

- AGPLv3 licensing requires explicit compatibility review for downstream use.
- Higher-level chart scope is broader than the first research backend needs.
- Current public release stream includes active alpha releases, so pinning a
  stable version would be important.

### Immanuel Python

Strengths:

- Based on Swiss Ephemeris.
- Produces detailed chart-centric data and JSON-friendly output.
- Python package install flow is straightforward.

Limitations:

- AGPL-3.0 licensing requires explicit compatibility review for downstream use.
- Chart-centric API may add translation, dignity, house, and presentation
  concepts that are not required for raw time-series ephemeris generation.

### pyswisseph / Swiss Ephemeris

Strengths:

- Direct Python extension for Swiss Ephemeris.
- Swiss Ephemeris is a mature high-precision astrology calculation engine.
- Exposes low-level calculation results suitable for longitude and speed based
  retrograde detection.

Limitations:

- AGPL licensing and Swiss Ephemeris licensing need clear downstream policy
  before making it a required dependency.
- Native extension and ephemeris file path handling can complicate installation.
- Low-level API needs a Hermetic Alpha adapter to keep research code clean.

## Consequences

- The first implementation issue should add an optional `pyswisseph` adapter,
  not a mandatory package dependency.
- Tests should mock or isolate the backend boundary where possible so the core
  test suite remains runnable without external ephemeris files.
- Documentation must continue warning users about timezone normalization,
  ephemeris source/version recording, and license review.

## Follow-Up Work

- Implement an optional `pyswisseph` ephemeris adapter.
- Add regression tests for known UTC timestamps.
- Decide packaging extras, for example `hermetic-alpha[ephemeris]`.
- Document license implications before publishing a release with the optional
  backend.

