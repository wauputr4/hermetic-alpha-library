# Hermetic Alpha Library Documentation

This documentation describes the design, research logic, statistical methods, and implementation plan for **Hermetic Alpha Library**.

Hermetic Alpha Library is the reusable Python core for astro-financial pattern research. It should remain independent from any CLI, API, notebook, or web dashboard.

## Documentation Map

- [Overview](overview.md)
- [Architecture](architecture.md)
- [Research Concepts](concepts.md)
- [Anti-Overfitting Guide](anti-overfitting.md)
- [Statistical Methods](statistical-methods.md)
- [Data Model](data-model.md)
- [Implementation Roadmap](roadmap.md)
- [Troubleshooting Notes](troubleshooting.md)
- [ADR 0001: First Ephemeris Engine](adr/0001-first-ephemeris-engine.md)
- [Research Workflow + Quick Start](research-workflow.md)

## Companion Agent Skill

Researchers who want an AI agent to run repeatable Hermetic Alpha studies can use the companion open Agent Skill:

- Repository: [wauputr4/financial-astrology-skills](https://github.com/wauputr4/financial-astrology-skills)
- Skill: `financial-astrology-pattern-search`

It provides a portable workflow for asset selection, aspect event construction, train/test validation, anti-overfitting controls, cross-asset checks, and publishable research reporting on top of this library.

```bash
npx skills add wauputr4/financial-astrology-skills --skill financial-astrology-pattern-search
```

## Core Philosophy

Hermetic Alpha should be built as a transparent research engine, not a black-box prediction system.

The project should help answer questions such as:

- How often did Bitcoin rise after a specific astrological aspect?
- Is the result better than the baseline market probability?
- How many historical events support the observation?
- Is the effect stable across different time periods?
- Are there similar past chart configurations?

Every result should be reproducible, inspectable, and statistically cautious.
