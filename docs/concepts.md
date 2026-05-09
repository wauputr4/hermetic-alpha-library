# Research Concepts

## Project Thesis

Hermetic Alpha explores whether astrological configurations can be transformed into quantitative features and tested against historical market behavior.

The project does not assume that astrology deterministically predicts price. Instead, it treats aspects and chart states as time-based signals that can be measured, compared, and statistically evaluated.

Research findings should follow the project
[anti-overfitting guide](anti-overfitting.md): report sample size, compare
against baselines, avoid future-label leakage, and describe probabilities as
exploratory historical frequencies rather than deterministic predictions.

## Main Research Object

The primary object is an **astro-market event**.

Example:

```text
Sun conjunct Jupiter with orb <= 3° occurred on a given date.
What happened to BTC after 1, 7, and 30 days?
```

## Aspect

An aspect is an angular relationship between two planetary bodies.

Common aspects:

| Aspect | Angle |
|---|---:|
| Conjunction | 0° |
| Sextile | 60° |
| Square | 90° |
| Trine | 120° |
| Opposition | 180° |

## Orb

Orb is the allowed deviation from the exact aspect angle.

Example:

```text
Sun-Jupiter conjunction, orb <= 3°
```

Means the angular distance between Sun and Jupiter must be between 0° and 3° from exact conjunction.

## Circular Distance

Planetary longitude is circular, not linear. A longitude of 359° is close to 1°.

Use circular distance:

```text
diff = abs(a - b)
distance = min(diff, 360 - diff)
```

## Aspect Strength

Aspect strength can be modeled as stronger when the orb is tighter.

```text
strength = 1 - (orb / max_orb)
```

An exact aspect has strength close to 1. An aspect at the edge of the allowed orb has strength close to 0.

## Applying vs Separating

If supported by the ephemeris engine, aspects should eventually distinguish between:

- **Applying**: bodies are moving toward exact aspect.
- **Separating**: bodies are moving away from exact aspect.

This may matter because market behavior could differ before and after exactitude.

## Market Labels

Market labels translate future price behavior into measurable outcomes.

Examples:

- Forward return after 1, 3, 7, 14, or 30 days.
- Bullish if forward return > 0.
- Bearish if forward return <= 0.
- Local top within a window.
- Local bottom within a window.

## Local Top and Bottom

A local bottom can be defined as:

```text
close[t] is the minimum close in window t-7 ... t+7
```

A local top can be defined as:

```text
close[t] is the maximum close in window t-7 ... t+7
```

Window size should be configurable.
