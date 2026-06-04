#!/usr/bin/env python3
"""Real-market mini case: cari bukti statistik aspek astrologi vs return pasar.

Skrip ini menjalankan alur:
1) ambil harga nyata dari Yahoo Finance,
2) bangun label return,
3) hitung posisi planet (ephemeris nyata jika tersedia atau fallback,
4) scan aspek,
5) join aspek dengan label,
6) event study + bootstrap + permutation test.

Tambahan:
- mendukung beberapa aset sekaligus lewat `--assets`,
- tambahan evaluasi walk-forward untuk cek stabilitas temporal.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from hermetic_alpha.analysis import (
    event_study_baseline_comparison_row,
    join_aspect_events_to_market_labels,
    permutation_test,
    permutation_test_result_row,
    summarize_event_study,
    summarize_validated_event_study,
    timestamp_join_summary_row,
    validated_event_study_report_row,
    walk_forward_splits,
    walk_forward_split_rows,
)
from hermetic_alpha.astro import EphemerisBackendUnavailable, SwissEphemerisAdapter, scan_aspect_series
from hermetic_alpha.exports import to_csv, to_json
from hermetic_alpha.labels import (
    add_candle_forward_returns,
    forward_return_label_coverage_row,
)
from hermetic_alpha.market import (
    MarketDataProviderError,
    YahooFinanceProvider,
    candle_dataset_summary_row,
)
from hermetic_alpha.models import PlanetPosition


FALLBACK_SPEED_BY_BODY: dict[str, float] = {
    "sun": 0.9856,
    "moon": 13.1764,
    "mercury": 4.0923,
    "venus": 1.602,
    "mars": 0.524,
    "jupiter": 0.083,
    "saturn": 0.034,
    "uranus": 0.012,
    "neptune": 0.006,
    "pluto": 0.004,
}


def _split_csv_values(raw: str) -> list[str]:
    values = [item.strip().lower() for item in raw.split(",")]
    values = [item for item in values if item]
    if not values:
        raise ValueError("list argumen tidak boleh kosong")
    return list(dict.fromkeys(values))


def _parse_args() -> argparse.Namespace:
    default_start, default_end = _default_range()
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--asset", default="", help="Aset tunggal (alias lama, usahakan gunakan --assets)")
    parser.add_argument(
        "--assets",
        default="BTC-USD,ETH-USD,SOL-USD",
        help="Daftar aset, pisah dengan koma. Contoh: BTC-USD,ETH-USD",
    )
    parser.add_argument(
        "--start",
        default=default_start,
        help="Tanggal awal UTC: YYYY-MM-DD",
    )
    parser.add_argument(
        "--end",
        default=default_end,
        help="Tanggal akhir UTC: YYYY-MM-DD",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=1,
        help="Horizon return, contoh 1 = return_1d",
    )
    parser.add_argument(
        "--bodies",
        default="sun,moon",
        help="Body planet (comma-separated), mis. sun,moon",
    )
    parser.add_argument(
        "--aspects",
        default="conjunction",
        help="Aspek yang di-scan, mis. conjunction,square,trine",
    )
    parser.add_argument(
        "--max-orb",
        type=float,
        default=1.0,
        help="Batas orb maksimum per aspek (derajat)",
    )
    parser.add_argument(
        "--skip-ephemeris",
        action="store_true",
        help="Paksa fallback posisi sintetik (tanpa pyswisseph)",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=2000,
        help="Bootstrap sample untuk interval CI validasi",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=2026,
        help="Seed bootstrap",
    )
    parser.add_argument(
        "--minimum-events",
        type=int,
        default=30,
        help="Minimum event untuk warning low-sample",
    )
    parser.add_argument(
        "--permutations",
        type=int,
        default=4000,
        help="Jumlah permutations untuk permutation test",
    )
    parser.add_argument(
        "--alternative",
        default="greater",
        choices=("greater", "less", "two-sided"),
        help="Arah hipotesis permutation test",
    )
    parser.add_argument(
        "--walk-forward-train-size",
        type=int,
        default=0,
        help="Jumlah observasi untuk train window (0 = nonaktif)",
    )
    parser.add_argument(
        "--walk-forward-test-size",
        type=int,
        default=0,
        help="Jumlah observasi untuk test window (0 = nonaktif)",
    )
    parser.add_argument(
        "--walk-forward-step-size",
        type=int,
        default=0,
        help="Langkah mundur window; default ke test size",
    )
    parser.add_argument(
        "--output-dir",
        default="tmp",
        help="Folder output laporan",
    )
    return parser.parse_args()


def _default_range(days: int = 540) -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    end = today - timedelta(days=1)
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def _collect_assets(cli_asset: str, cli_assets: str) -> list[str]:
    if cli_asset:
        return [cli_asset.strip().upper()]
    assets = _split_csv_values(cli_assets)
    return [asset.strip().upper() for asset in assets]


def _ensure_date_order(start: str, end: str) -> tuple[str, str]:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    if end_date < start_date:
        raise ValueError("start harus pada atau sebelum end")
    return start, end


def _load_market_data(asset: str, start: str, end: str) -> list:
    provider = YahooFinanceProvider()
    return provider.fetch_daily(asset, start, end)


def _build_fallback_positions(candles: Sequence, bodies: Sequence[str]) -> list[PlanetPosition]:
    if not candles:
        return []

    timestamps = [candle.timestamp for candle in candles]
    normalized_bodies = list(dict.fromkeys(body.lower() for body in bodies))
    positions: list[PlanetPosition] = []
    base_date = min(timestamps).date()

    for index, timestamp in enumerate(timestamps):
        day_index = (timestamp.date() - base_date).days
        for body_index, body in enumerate(normalized_bodies):
            body_speed = FALLBACK_SPEED_BY_BODY.get(body, 0.75 + body_index * 0.11)
            sun_base = (day_index * FALLBACK_SPEED_BY_BODY["sun"]) % 360

            if body == "sun":
                longitude = (day_index * FALLBACK_SPEED_BY_BODY["sun"]) % 360
            elif body == "moon":
                if day_index % 7 == 0:
                    longitude = sun_base
                else:
                    longitude = (sun_base + day_index * FALLBACK_SPEED_BY_BODY["moon"] / 4) % 360
            else:
                longitude = (day_index * body_speed + body_index * 17.0) % 360

            positions.append(
                PlanetPosition(
                    timestamp=timestamp,
                    body=body,
                    longitude=longitude,
                    speed=body_speed,
                    retrograde=False,
                    zodiac="tropical",
                    engine="synthetic_fallback",
                )
            )

    return positions


def _walk_forward_step_size(args: argparse.Namespace) -> int:
    return args.walk_forward_step_size if args.walk_forward_step_size > 0 else args.walk_forward_test_size


def _with_report_type(row: dict[str, object], report_type: str) -> dict[str, object]:
    return {
        "report_type": report_type,
        **row,
    }


def _build_positions(candles: Sequence, bodies: Sequence[str], *, use_ephemeris: bool) -> list[PlanetPosition]:
    if not use_ephemeris:
        return _build_fallback_positions(candles, bodies)

    try:
        adapter = SwissEphemerisAdapter()
        print("[INFO] Ephemeris aktif: SwissEphemerisAdapter")
    except EphemerisBackendUnavailable as exc:
        print(f"[INFO] Pyswisseph tidak tersedia: {exc}. Pakai fallback sintetik.")
        return _build_fallback_positions(candles, bodies)

    positions: list[PlanetPosition] = []
    for candle in candles:
        for body in bodies:
            positions.append(adapter.position(candle.timestamp, body))
    return positions


def _collect_returns(
    labels: list[dict],
    horizon: int,
    event_indexes: set[int],
) -> tuple[list[float], list[float]]:
    key = f"return_{horizon}d"
    event_returns: list[float] = []
    baseline_returns: list[float] = []

    for index, row in enumerate(labels):
        value = row.get(key)
        if not isinstance(value, (int, float)):
            continue
        if index in event_indexes:
            event_returns.append(float(value))
        else:
            baseline_returns.append(float(value))

    return event_returns, baseline_returns


def _run_event_study(labels: list[dict], event_indexes: Sequence[int], horizon: int, args: argparse.Namespace) -> dict[str, object]:
    joined_event_indexes = [index for index in event_indexes if 0 <= index < len(labels)]
    summary = summarize_event_study(labels, joined_event_indexes, horizon)
    validated = summarize_validated_event_study(
        labels,
        joined_event_indexes,
        horizon,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
        minimum_events=args.minimum_events,
    )

    event_returns, baseline_returns = _collect_returns(labels, horizon, set(joined_event_indexes))
    permutation = None
    if event_returns and baseline_returns:
        permutation = permutation_test(
            event_returns,
            baseline_returns,
            permutations=args.permutations,
            seed=args.bootstrap_seed,
            alternative=args.alternative,
        )

    return {
        "summary": summary,
        "validated": validated,
        "permutation": permutation,
    }


def _run_walk_forward(
    labels: list[dict],
    event_indexes: Sequence[int],
    horizon: int,
    args: argparse.Namespace,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    splits = walk_forward_splits(
        observations=labels,
        train_size=args.walk_forward_train_size,
        test_size=args.walk_forward_test_size,
        step_size=_walk_forward_step_size(args),
    )

    split_summary_rows: list[dict[str, object]] = []
    split_output_rows: list[dict[str, object]] = []
    event_index_set = set(event_indexes)

    for split_index, split in enumerate(splits):
        local_event_indexes = [
            index - split.test_start_index
            for index in sorted(event_index_set)
            if split.test_start_index <= index < split.test_end_index
        ]

        result = _run_event_study(split.test, local_event_indexes, horizon, args)
        split_summary = result["summary"]
        validated = result["validated"]
        permutation = result["permutation"]

        split_rows = walk_forward_split_rows([split])[0]
        split_summary_row = event_study_baseline_comparison_row(split_summary)
        split_report_row = validated_event_study_report_row(validated)
        if permutation is not None:
            permutation_row = permutation_test_result_row(permutation)
        else:
            permutation_row = {
                "observed_statistic": None,
                "p_value": None,
                "alternative": args.alternative,
                "permutations": args.permutations,
                "seed": args.bootstrap_seed,
                "null_mean": None,
                "null_distribution_count": 0,
                "null_distribution_min": None,
                "null_distribution_max": None,
            }

        split_summary_rows.append(
            {
                "report_type": "walk_forward_split_overview",
                "split_index": split_index,
                **split_rows,
                **split_summary_row,
                **split_report_row,
            }
        )

        split_output_rows.append(
            {
                "report_type": "walk_forward_permutation",
                "split_index": split_index,
                **permutation_row,
            }
        )

    return split_summary_rows, split_output_rows


def run_case_for_asset(asset: str, start: str, end: str, bodies: list[str], aspects: list[str], args: argparse.Namespace) -> dict:
    if args.horizon <= 0:
        raise ValueError("horizon harus positif")

    try:
        candles = _load_market_data(asset, start, end)
    except (ValueError, MarketDataProviderError) as exc:
        raise RuntimeError(f"Gagal ambil market data untuk {asset}: {exc}") from exc

    if len(candles) <= args.horizon:
        raise RuntimeError(f"Data market {asset} tidak cukup untuk horizon {args.horizon}")

    labels = add_candle_forward_returns(candles, [args.horizon])
    market_summary = candle_dataset_summary_row(candles, dataset_id=asset)
    label_coverage = forward_return_label_coverage_row(labels, args.horizon, dataset_id=asset)

    positions = _build_positions(candles, bodies, use_ephemeris=not args.skip_ephemeris)
    aspect_events = scan_aspect_series(positions, aspects={aspect: args.max_orb for aspect in aspects})
    aspect_counts = Counter(event.aspect for event in aspect_events)
    joined = join_aspect_events_to_market_labels(aspect_events, labels)

    full_result = _run_event_study(labels, joined.event_indexes, args.horizon, args)
    summary = full_result["summary"]
    validated = full_result["validated"]
    permutation = full_result["permutation"]

    walk_forward_rows: list[dict[str, object]] = []
    walk_forward_permutation_rows: list[dict[str, object]] = []
    if args.walk_forward_train_size > 0 or args.walk_forward_test_size > 0:
        if args.walk_forward_train_size <= 0 or args.walk_forward_test_size <= 0:
            raise ValueError("walk-forward harus diaktifkan dengan train-size dan test-size > 0")
        if args.walk_forward_step_size < 0:
            raise ValueError("walk-forward step-size tidak boleh negatif")

        split_summary_rows, split_perm_rows = _run_walk_forward(labels, joined.event_indexes, args.horizon, args)
        walk_forward_rows.extend(split_summary_rows)
        walk_forward_permutation_rows.extend(split_perm_rows)

    if permutation is not None:
        permutation_row = permutation_test_result_row(permutation)
    else:
        permutation_row = {
            "observed_statistic": None,
            "p_value": None,
            "alternative": args.alternative,
            "permutations": args.permutations,
            "seed": args.bootstrap_seed,
            "null_mean": None,
            "null_distribution_count": 0,
            "null_distribution_min": None,
            "null_distribution_max": None,
        }

    print("=== Real-market astronomy case ===")
    print(f"Asset: {asset}")
    print(f"Window: {start} to {end}")
    print(f"Horizon: {args.horizon}d")
    print(f"Market rows: {market_summary['candle_count']}")
    print(f"Aspect events: {len(aspect_events)}")
    print(f"Join matches: {joined.matched_events}/{len(aspect_events)}")
    print(f"Baseline bullish prob: {summary.baseline_bullish_probability}")
    print(f"Conditional bullish prob: {summary.conditional_bullish_probability}")
    print(f"Event sample count: {summary.events}")
    print(f"Avg event return: {summary.average_return}")
    if permutation is not None:
        print(f"Permutation p-value ({args.alternative}): {permutation.p_value}")
    if validated.low_sample_warning:
        print(f"Warning: {validated.low_sample_warning}")

    if walk_forward_rows:
        print(f"Walk-forward splits: {len(walk_forward_rows)}")

    report = {
        "meta": {
            "asset": asset,
            "start": start,
            "end": end,
            "horizon": args.horizon,
            "aspects": aspects,
            "max_orb": args.max_orb,
            "bodies": bodies,
            "positions_mode": "ephemeris" if not args.skip_ephemeris else "synthetic_fallback",
            "permutation_alternative": args.alternative,
            "walk_forward_enabled": bool(walk_forward_rows),
            "walk_forward_train_size": args.walk_forward_train_size if walk_forward_rows else None,
            "walk_forward_test_size": args.walk_forward_test_size if walk_forward_rows else None,
            "walk_forward_step_size": _walk_forward_step_size(args) if walk_forward_rows else None,
        },
        "market_summary": market_summary,
        "label_coverage": label_coverage,
        "aspect_count": dict(aspect_counts),
        "join_summary": timestamp_join_summary_row(joined),
        "event_study_summary": summary.to_dict(),
        "event_study_baseline_comparison": event_study_baseline_comparison_row(summary),
        "validated_event_study": validated.to_dict(),
        "validated_event_study_row": validated_event_study_report_row(validated),
        "permutation_test": permutation.to_dict() if permutation is not None else None,
        "walk_forward_summary": walk_forward_rows,
        "walk_forward_permutation_rows": walk_forward_permutation_rows,
    }

    csv_rows = [
        _with_report_type(market_summary, "market_summary"),
        _with_report_type(label_coverage, "label_coverage"),
        {
            "report_type": "aspect_count",
            **{f"count_{aspect}": count for aspect, count in aspect_counts.items()},
        },
        {
            "report_type": "full_window_join",
            **timestamp_join_summary_row(joined),
        },
        {
            "report_type": "full_window_baseline",
            **event_study_baseline_comparison_row(summary),
        },
        {
            "report_type": "full_window_validated",
            **validated_event_study_report_row(validated),
        },
        {
            "report_type": "full_window_permutation",
            **permutation_row,
        },
    ]
    csv_rows.extend(walk_forward_rows)
    csv_rows.extend(walk_forward_permutation_rows)

    return {
        "report": report,
        "csv_rows": csv_rows,
    }


def run_case() -> None:
    args = _parse_args()
    start, end = _ensure_date_order(args.start, args.end)

    assets = _collect_assets(args.asset, args.assets)
    bodies = _split_csv_values(args.bodies)
    aspects = _split_csv_values(args.aspects)

    if not all(
        value > 0 for value in [args.max_orb, args.bootstrap_samples, args.minimum_events, args.permutations]
    ):
        raise ValueError("parameter bootstrap/permutation/minimum-events/horizon harus positif")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_reports: list[dict[str, object]] = []
    all_csv_rows: list[dict[str, object]] = []

    for asset in assets:
        print(f"\n== asset {asset} ==")
        case = run_case_for_asset(asset, start, end, bodies, aspects, args)

        all_reports.append(case["report"])
        all_csv_rows.extend(case["csv_rows"])

    combined_report = {
        "meta": {
            "run_window": {
                "start": start,
                "end": end,
                "assets": assets,
            },
            "pipeline": {
                "horizon": args.horizon,
                "aspects": aspects,
                "bodies": bodies,
                "positions_mode": "ephemeris" if not args.skip_ephemeris else "synthetic_fallback",
            },
            "walk_forward_enabled": bool(args.walk_forward_train_size and args.walk_forward_test_size),
        },
        "cases": all_reports,
    }

    csv_report = to_csv(all_csv_rows)
    json_report = to_json(combined_report)

    output_basename = f"market_multi_asset_{start}_{end}_{args.horizon}d"
    csv_path = output_dir / f"{output_basename}.csv"
    json_path = output_dir / f"{output_basename}.json"
    csv_path.write_text(csv_report, encoding="utf-8")
    json_path.write_text(json_report, encoding="utf-8")

    print(f"\nLaporan CSV: {csv_path}")
    print(f"Laporan JSON: {json_path}")


if __name__ == "__main__":
    run_case()
