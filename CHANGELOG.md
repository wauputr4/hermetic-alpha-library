# Changelog

## [Unreleased]

- Work in progress.

## [0.1.6] - 2026-06-05

### Changed
- Disable GitHub Packages publish step in release workflow because current GitHub Packages upload endpoint is not reliably reachable from the CI runner (SSL/endpoint mismatch).
- Keep release pipeline focused on successful PyPI publish (`python3 -m pip install hermetic-alpha`).

## [0.1.5] - 2026-06-05

### Added
- Fix GitHub Packages publish endpoint in release workflow (`pypi.pkg.github.com/...`) to eliminate SSL hostname mismatch failures.
- Keep quick-release docs aligned to the latest Git tag.

### Changed
- Bump package version to `0.1.5` in runtime and packaging metadata.

## [0.1.4] - 2026-06-05

### Added
- Publish release workflow now publishes to both PyPI and GitHub Packages.
- Document installation path from GitHub Packages for token-authenticated installs.

### Changed
- Keep package metadata and runtime version in sync with release `0.1.4`.

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
