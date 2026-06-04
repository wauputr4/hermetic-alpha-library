"""Synthetic mini case-study: test apakah conjunction Sun-Moon terkait peluang return 1 hari.

Script ini sengaja tidak memakai dependency opsional `pyswisseph` supaya bisa
langsung jalan dengan library core yang sudah ada.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from hermetic_alpha.astro import scan_aspect_series
from hermetic_alpha.models import PlanetPosition
from hermetic_alpha.analysis import (
    event_study_baseline_comparison_row,
    join_aspect_events_to_market_labels,
    permutation_test,
    summarize_event_study,
    summarize_validated_event_study,
    validated_event_study_report_row,
)
from hermetic_alpha.exports import to_csv, to_json
from hermetic_alpha.labels import add_forward_returns


def build_synthetic_universe(day_count: int = 70) -> tuple[list[datetime], list[float], set[int]]:
    """Return timestamps, close prices, and conjunction event candidate indexes."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    timestamps = [start + timedelta(days=index) for index in range(day_count)]

    # Conjunction events will be injected every 7 hari pada index ini.
    conjunction_day_indexes = set(range(2, day_count - 2, 7))

    closes: list[float] = [1000.0]
    for index in range(day_count - 1):
        delta = 12.0 if index in conjunction_day_indexes else -7.0
        closes.append(closes[-1] + delta)

    return timestamps, closes, conjunction_day_indexes


def synthetic_planet_positions(timestamps: list[datetime], conjunction_day_indexes: set[int]) -> list[PlanetPosition]:
    positions: list[PlanetPosition] = []
    for index, timestamp in enumerate(timestamps):
        sun_lon = (index * 17.3) % 360
        if index in conjunction_day_indexes:
            moon_lon = sun_lon
        else:
            moon_lon = (sun_lon + 90.0) % 360

        positions.append(
            PlanetPosition(
                timestamp=timestamp,
                body="sun",
                longitude=sun_lon,
                zodiac="tropical",
                engine="synthetic",
            )
        )
        positions.append(
            PlanetPosition(
                timestamp=timestamp,
                body="moon",
                longitude=moon_lon,
                zodiac="tropical",
                engine="synthetic",
            )
        )
    return positions


def run_case() -> None:
    timestamps, closes, conjunction_day_indexes = build_synthetic_universe()

    # 1) Label pasar: 1-day forward returns + bullish flag
    label_rows = [
        {"timestamp": timestamp, "asset": "SYNTHETIC", **row}
        for timestamp, row in zip(timestamps, add_forward_returns(closes, [1]), strict=True)
    ]

    # 2) Planet positions + scan aspek
    positions = synthetic_planet_positions(timestamps, conjunction_day_indexes)
    aspect_events = scan_aspect_series(
        positions,
        aspects={"conjunction": 0.5, "square": 0.5},
    )

    conjunction_events = [event for event in aspect_events if event.aspect == "conjunction"]
    joined = join_aspect_events_to_market_labels(conjunction_events, label_rows)

    if not joined.event_indexes:
        print("Tidak ada conjunction event yang bisa dijoin ke label timestamp.")
        return

    # 3) Event study + validasi
    summary = summarize_event_study(joined.labels, joined.event_indexes, 1)
    validated = summarize_validated_event_study(
        joined.labels,
        joined.event_indexes,
        1,
        bootstrap_samples=2000,
        bootstrap_seed=2026,
        minimum_events=5,
    )

    event_indexes = set(joined.event_indexes)
    event_returns = [
        joined.labels[index]["return_1d"] for index in joined.event_indexes
        if isinstance(joined.labels[index].get("return_1d"), (int, float))
    ]
    baseline_returns = [
        row["return_1d"] for index, row in enumerate(joined.labels)
        if index not in event_indexes and isinstance(row.get("return_1d"), (int, float))
    ]

    ptest = permutation_test(
        [float(value) for value in event_returns],
        [float(value) for value in baseline_returns],
        permutations=3000,
        seed=2026,
        alternative="greater",
    )

    # 4) Ringkas dan ekspor
    output = {
        "hypothesis": "Conjunction Sun-Moon meningkatkan return_1d bullish probability",
        "matched_events": joined.matched_events,
        "unmatched_events": joined.unmatched_events,
        "event_study_summary": summary.to_dict(),
        "validated_event_study": validated.to_dict(),
        "baseline_vs_conditional": event_study_baseline_comparison_row(summary),
        "validated_event_study_row": validated_event_study_report_row(validated),
        "permutation_test": ptest.to_dict(),
    }

    print("=== Case study result (synthetic) ===")
    print(f"Detected aspects: {len(aspect_events)}")
    print(f"Conjunction events: {len(conjunction_events)}")
    print(f"Join matches: {joined.matched_events}/{len(conjunction_events)}")
    print(f"Baseline bullish prob: {summary.baseline_bullish_probability}")
    print(f"Conditional bullish prob: {summary.conditional_bullish_probability}")
    print(f"Avg return (event set): {summary.average_return}")
    print(f"Permutation p-value (greater): {ptest.p_value}")
    print(f"Return CI (95%): {validated.return_confidence_interval}")
    if validated.low_sample_warning:
        print(f"Warning: {validated.low_sample_warning}")

    csv_rows = [
        {
            "report_type": "synthetic_baseline",
            **event_study_baseline_comparison_row(summary),
        },
        {
            "report_type": "synthetic_validated",
            **validated_event_study_report_row(validated),
        },
    ]
    csv_report = to_csv(csv_rows)
    json_report = to_json(output)

    print("\nCSV:")
    print(csv_report)
    print("\nJSON:")
    print(json_report)

    out_dir = Path("tmp")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "synthetic_astronomy_case.csv").write_text(csv_report, encoding="utf-8")
    (out_dir / "synthetic_astronomy_case.json").write_text(json_report, encoding="utf-8")
    print(f"\nReports saved to {out_dir}/synthetic_astronomy_case.*")


if __name__ == "__main__":
    run_case()
