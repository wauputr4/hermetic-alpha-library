# Hermetic Alpha Library Documentation

This documentation describes the design, research logic, statistical methods, and implementation plan for **Hermetic Alpha Library**.

Hermetic Alpha Library is the reusable Python core for astro-financial pattern research. It should remain independent from any CLI, API, notebook, or web dashboard.

## Documentation Map

- [Overview](overview.md)
- [Architecture](architecture.md)
- [Research Concepts](concepts.md)
- [Statistical Methods](statistical-methods.md)
- [Data Model](data-model.md)
- [Implementation Roadmap](roadmap.md)
- [Troubleshooting Notes](troubleshooting.md)
- [ADR 0001: First Ephemeris Engine](adr/0001-first-ephemeris-engine.md)

## Core Philosophy

Hermetic Alpha should be built as a transparent research engine, not a black-box prediction system.

The project should help answer questions such as:

- How often did Bitcoin rise after a specific astrological aspect?
- Is the result better than the baseline market probability?
- How many historical events support the observation?
- Is the effect stable across different time periods?
- Are there similar past chart configurations?

Every result should be reproducible, inspectable, and statistically cautious.
