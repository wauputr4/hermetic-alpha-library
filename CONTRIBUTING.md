# Contributing to Hermetic Alpha Library

Thank you for considering a contribution.

## Project Principles

- Keep research reproducible.
- Avoid deterministic financial claims.
- Report sample size and baseline comparisons.
- Keep core logic independent from CLI, API, and web UI concerns.
- Update documentation and troubleshooting notes after meaningful code changes.

## Local Development

```bash
PYTHONPATH=src python3 examples/basic_event_study.py
```

When `pytest` is available:

```bash
python3 -m pytest -q
```

## Documentation

Before opening a pull request, update relevant files in `docs/`, especially `docs/troubleshooting.md` for implementation notes, known limitations, or environment issues.
