# Changelog

## [Unreleased]

- Work in progress.

## [0.1.3] - 2026-06-05

### Added
- Re-release with automated PyPI publish workflow validation.

### Changed
- Bump package version to `0.1.3` for validated release publication.
- Keep existing install and research documentation; release path now includes GitHub tag -> PyPI publish.

## [0.1.2] - 2026-06-05

### Added
- Add standard OSS distribution metadata in `pyproject.toml` (project urls, keywords, version bump).
- Add `CHANGELOG.md`.
- Add import-time smoke test in CI.
- Improve README quick start with standard `pip install` flow and non-PYTHONPATH usage.

### Changed
- Synchronize package version constant (`src/hermetic_alpha/__init__.py`) with project version.
- Update release tagging to `v0.1.2` for packaging alignment.

## [0.1.1] - 2026-06-04

### Added
- Real market research workflow docs and scripts.
- Synthetic and real-market astrology-case examples.

### Changed
- Improve fallback handling and CSV/JSON export consistency for research scripts.

## [0.1.0] - 2026-06-01

- Initial packaged research engine release.
