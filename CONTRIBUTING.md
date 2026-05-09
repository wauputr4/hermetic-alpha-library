# Contributing to Hermetic Alpha Library

Thank you for considering a contribution.

## Project Principles

- Keep research reproducible.
- Avoid deterministic financial claims.
- Report sample size and baseline comparisons.
- Keep core logic independent from CLI, API, and web UI concerns.
- Update documentation and troubleshooting notes after meaningful code changes.

## Local Development

Preferred setup with `uv`:

```bash
uv venv
uv pip install -e ".[dev]"
uv run python3 -m pytest -q
```

Standard `venv` setup:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

The development extra installs `pytest`, and the repository's
`pyproject.toml` config points pytest at `src/` and `tests/`.

```bash
PYTHONPATH=src python3 examples/basic_event_study.py
```

When the development extra is installed:

```bash
python3 -m pytest -q
```

## Documentation

Before opening a pull request, update relevant files in `docs/`, especially `docs/troubleshooting.md` for implementation notes, known limitations, or environment issues.
