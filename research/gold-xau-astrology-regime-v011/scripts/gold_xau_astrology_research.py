from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import bisect
import json
import math
import statistics

from hermetic_alpha.astro import SwissEphemerisAdapter, generate_planet_positions, scan_aspect_series
from hermetic_alpha.labels import add_candle_forward_returns
from hermetic_alpha.market.providers import YahooFinanceProvider

PRIMARY_ASSET = "GC=F"  # COMEX Gold Futures, Yahoo Finance
VALIDATION_ASSETS = ["GLD", "IAU"]
START = "1990-01-01"
END = date.today().isoformat()
FUTURE_START = (date.today() + timedelta(days=1)).isoformat()
FUTURE_END = (date.today().replace(year=date.today().year + 5)).isoformat()
TRAIN_END = "2013-12-31"  # approx midpoint for GC=F history, before 2015-2020 and 2020+ regimes
HORIZONS = [3, 7, 14, 30, 60, 90, 180]
ASPECTS = ["conjunction", "opposition", "trine", "square", "sextile"]
FULL_BODIES = ["sun", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
OUTER_BODIES = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
MAX_TRADING_DAY_MAP_LAG = 3
PEAK_BOTTOM_WINDOW = 30
MIN_FEATURE_EVENTS = 5
MIN_THEME_EVENTS = 20
MIN_TRAIN_EVENTS = 3
MIN_TEST_EVENTS = 3


def pct(x):
    return None if x is None else round(float(x) * 100, 3)


def valid(v):
    return isinstance(v, (int, float)) and math.isfinite(float(v))


def parse_feature(f: str):
    parts = f.split("_")
    return parts[0], parts[1], "_".join(parts[2:])


def canonical_feature(e):
    a, b = sorted([e.body_a, e.body_b])
    return f"{a}_{b}_{e.aspect}"


def ret(labels, idx, h):
    if idx < 0 or idx >= len(labels):
        return None
    v = labels[idx].get(f"return_{h}d")
    return float(v) if valid(v) else None


def summarize(vals):
    vals = [float(v) for v in vals if valid(v)]
    if not vals:
        return {"n": 0, "avg_pct": None, "median_pct": None, "bullish_pct": None, "min_pct": None, "max_pct": None}
    return {
        "n": len(vals),
        "avg_pct": pct(statistics.mean(vals)),
        "median_pct": pct(statistics.median(vals)),
        "bullish_pct": pct(sum(v > 0 for v in vals) / len(vals)),
        "min_pct": pct(min(vals)),
        "max_pct": pct(max(vals)),
    }


def score_binomial(obs, n, p):
    if n <= 0 or p <= 0 or p >= 1:
        return None
    sd = math.sqrt(n * p * (1 - p))
    if sd == 0:
        return None
    return round((obs - n * p) / sd, 3)


def summarize_rate(idxs, label_set, base_share):
    idxs = sorted(set(idxs))
    n = len(idxs)
    obs = sum(1 for i in idxs if i in label_set)
    rate = obs / n if n else 0
    return {
        "n": n,
        "observed": obs,
        "rate_pct": pct(rate),
        "base_rate_pct": pct(base_share),
        "edge_pp": round((rate - base_share) * 100, 3),
        "lift": round(rate / base_share, 3) if base_share else None,
        "z_approx": score_binomial(obs, n, base_share),
    }


@dataclass(frozen=True)
class WindowEvent:
    feature: str
    exact_idx: int
    exact_date: str
    mapped_candle_date: str
    map_lag_days: int
    start_date: str
    end_date: str
    min_orb: float
    max_strength: float


@dataclass(frozen=True)
class FutureWindowEvent:
    feature: str
    exact_date: str
    start_date: str
    end_date: str
    min_orb: float
    max_strength: float


def candle_index_mapper(candles):
    candle_dates = [c.timestamp.date() for c in candles]
    def map_date(d):
        pos = bisect.bisect_left(candle_dates, d)
        if pos >= len(candle_dates):
            return None, None
        lag = (candle_dates[pos] - d).days
        if lag < 0 or lag > MAX_TRADING_DAY_MAP_LAG:
            return None, None
        return pos, lag
    return map_date


def block_to_event(feature, block, candles, map_date):
    exact_i, exact_e = min(block, key=lambda x: (float(x[1].orb), x[0]))
    exact_day = exact_e.timestamp.date()
    candle_idx, lag = map_date(exact_day)
    if candle_idx is None:
        return None
    return WindowEvent(
        feature=feature,
        exact_idx=candle_idx,
        exact_date=exact_day.isoformat(),
        mapped_candle_date=candles[candle_idx].timestamp.date().isoformat(),
        map_lag_days=lag,
        start_date=block[0][1].timestamp.date().isoformat(),
        end_date=block[-1][1].timestamp.date().isoformat(),
        min_orb=round(float(exact_e.orb), 6),
        max_strength=round(max(float(e.strength) for _, e in block), 6),
    )


def build_window_events(aspect_days, candles):
    map_date = candle_index_mapper(candles)
    by_feature = defaultdict(list)
    for seq_idx, e in enumerate(sorted(aspect_days, key=lambda x: (canonical_feature(x), x.timestamp))):
        by_feature[canonical_feature(e)].append((seq_idx, e))

    out = []
    skipped_no_candle = 0
    for feature, rows in by_feature.items():
        rows = sorted(rows, key=lambda x: x[1].timestamp)
        block, prev_day = [], None
        for seq_idx, e in rows:
            day = e.timestamp.date()
            if prev_day is None or (day - prev_day).days <= 1:
                block.append((seq_idx, e))
            else:
                ev = block_to_event(feature, block, candles, map_date)
                if ev is None:
                    skipped_no_candle += 1
                else:
                    out.append(ev)
                block = [(seq_idx, e)]
            prev_day = day
        if block:
            ev = block_to_event(feature, block, candles, map_date)
            if ev is None:
                skipped_no_candle += 1
            else:
                out.append(ev)
    return out, skipped_no_candle


def future_block_to_event(feature, block):
    exact_i, exact_e = min(block, key=lambda x: (float(x[1].orb), x[0]))
    return FutureWindowEvent(
        feature=feature,
        exact_date=exact_e.timestamp.date().isoformat(),
        start_date=block[0][1].timestamp.date().isoformat(),
        end_date=block[-1][1].timestamp.date().isoformat(),
        min_orb=round(float(exact_e.orb), 6),
        max_strength=round(max(float(e.strength) for _, e in block), 6),
    )


def build_future_window_events(aspect_days):
    by_feature = defaultdict(list)
    for seq_idx, e in enumerate(sorted(aspect_days, key=lambda x: (canonical_feature(x), x.timestamp))):
        by_feature[canonical_feature(e)].append((seq_idx, e))
    out = []
    for feature, rows in by_feature.items():
        rows = sorted(rows, key=lambda x: x[1].timestamp)
        block, prev_day = [], None
        for seq_idx, e in rows:
            day = e.timestamp.date()
            if prev_day is None or (day - prev_day).days <= 1:
                block.append((seq_idx, e))
            else:
                out.append(future_block_to_event(feature, block))
                block = [(seq_idx, e)]
            prev_day = day
        if block:
            out.append(future_block_to_event(feature, block))
    return out


def detect_drawdown_cycles(candles, threshold=-0.20):
    closes = [float(c.close) for c in candles]
    ath_idx = 0
    ath = closes[0]
    in_bear = False
    peak_idx = bottom_idx = None
    peak_price = bottom_price = None
    cycles = []

    for i, close in enumerate(closes):
        if not in_bear:
            if close >= ath:
                ath = close
                ath_idx = i
            if close / ath - 1 <= threshold:
                in_bear = True
                peak_idx = ath_idx
                peak_price = ath
                bottom_idx = i
                bottom_price = close
        else:
            if close < bottom_price:
                bottom_idx = i
                bottom_price = close
            if close >= peak_price:
                cycles.append({
                    "peak_idx": peak_idx,
                    "peak_date": candles[peak_idx].timestamp.date().isoformat(),
                    "peak_close": round(peak_price, 4),
                    "bottom_idx": bottom_idx,
                    "bottom_date": candles[bottom_idx].timestamp.date().isoformat(),
                    "bottom_close": round(bottom_price, 4),
                    "recovery_idx": i,
                    "recovery_date": candles[i].timestamp.date().isoformat(),
                    "max_drawdown_pct": pct(bottom_price / peak_price - 1),
                    "peak_to_bottom_days": bottom_idx - peak_idx,
                    "underwater_trading_days": i - peak_idx + 1,
                    "status": "recovered",
                })
                in_bear = False
                ath_idx = i
                ath = close
                peak_idx = bottom_idx = None
                peak_price = bottom_price = None
    if in_bear:
        cycles.append({
            "peak_idx": peak_idx,
            "peak_date": candles[peak_idx].timestamp.date().isoformat(),
            "peak_close": round(peak_price, 4),
            "bottom_idx": bottom_idx,
            "bottom_date": candles[bottom_idx].timestamp.date().isoformat(),
            "bottom_close": round(bottom_price, 4),
            "recovery_idx": None,
            "recovery_date": None,
            "max_drawdown_pct": pct(bottom_price / peak_price - 1),
            "peak_to_bottom_days": bottom_idx - peak_idx,
            "underwater_trading_days": len(candles) - peak_idx,
            "status": "open",
        })
    return cycles


def make_label_sets(candles, cycles, window=PEAK_BOTTOM_WINDOW):
    n = len(candles)
    bear = set()
    peaks = set()
    bottoms = set()
    peak_pre = set()
    bottom_post = set()
    for c in cycles:
        bear.update(range(c["peak_idx"], c["bottom_idx"] + 1))
        for j in range(max(0, c["peak_idx"] - window), min(n, c["peak_idx"] + window + 1)):
            peaks.add(j)
        for j in range(max(0, c["bottom_idx"] - window), min(n, c["bottom_idx"] + window + 1)):
            bottoms.add(j)
        for j in range(max(0, c["peak_idx"] - window), c["peak_idx"] + 1):
            peak_pre.add(j)
        for j in range(c["bottom_idx"], min(n, c["bottom_idx"] + window + 1)):
            bottom_post.add(j)
    bull = set(range(n)) - bear
    return {
        "bull": bull,
        "bear": bear,
        "peak_window_30td": peaks,
        "bottom_window_30td": bottoms,
        "pre_peak_30td": peak_pre,
        "post_bottom_30td": bottom_post,
    }


def base_shares(labels, n):
    return {k: len(v) / n for k, v in labels.items()}


THEME_RULES = {
    "jupiter_neptune_liquidity": lambda a,b,asp: {a,b} == {"jupiter","neptune"} and asp in {"conjunction","opposition","trine","square","sextile"},
    "jupiter_uranus_instability": lambda a,b,asp: {a,b} == {"jupiter","uranus"} and asp in {"conjunction","opposition","trine","square","sextile"},
    "jupiter_pluto_power": lambda a,b,asp: {a,b} == {"jupiter","pluto"} and asp in {"conjunction","opposition","trine","square","sextile"},
    "saturn_neptune_macro_stress": lambda a,b,asp: {a,b} == {"saturn","neptune"} and asp in {"conjunction","opposition","trine","square","sextile"},
    "saturn_uranus_dislocation": lambda a,b,asp: {a,b} == {"saturn","uranus"} and asp in {"conjunction","opposition","trine","square","sextile"},
    "saturn_pluto_stress": lambda a,b,asp: {a,b} == {"saturn","pluto"} and asp in {"conjunction","opposition","trine","square","sextile"},
    "mars_pluto_capitulation": lambda a,b,asp: {a,b} == {"mars","pluto"} and asp in {"conjunction","opposition","square"},
    "mars_uranus_shock": lambda a,b,asp: {a,b} == {"mars","uranus"} and asp in {"conjunction","opposition","square"},
    "venus_gold_sentiment": lambda a,b,asp: "venus" in (a,b) and bool({a,b} & {"jupiter","saturn","uranus","neptune","pluto"}) and asp in {"conjunction","opposition","trine","square","sextile"},
    "sun_venus_relief": lambda a,b,asp: {a,b} == {"sun","venus"} and asp in {"conjunction","sextile","trine"},
    "outer_hard_pressure": lambda a,b,asp: bool({a,b} & {"jupiter","saturn","uranus","neptune","pluto"}) and asp in {"conjunction","square","opposition"},
    "outer_soft_release": lambda a,b,asp: bool({a,b} & {"jupiter","saturn","uranus","neptune","pluto"}) and asp in {"trine","sextile"},
}


def aggregate_buckets(events):
    buckets = defaultdict(set)
    bucket_features = defaultdict(set)
    outer = {"jupiter", "saturn", "uranus", "neptune", "pluto"}
    personal = {"sun", "mercury", "venus", "mars"}
    hard = {"conjunction", "square", "opposition"}
    soft = {"trine", "sextile"}
    for e in events:
        a, b, asp = parse_feature(e.feature)
        idx = e.exact_idx
        buckets[f"feature:{e.feature}"].add(idx)
        bucket_features[f"feature:{e.feature}"].add(e.feature)
        tags = [
            f"aspect:{asp}", f"planet:{a}", f"planet:{b}", f"pair:{a}_{b}",
            f"planet_aspect:{a}_{asp}", f"planet_aspect:{b}_{asp}",
        ]
        if asp in hard:
            tags.append("aspect_family:hard")
        if asp in soft:
            tags.append("aspect_family:soft")
        if {a,b} <= outer:
            tags.append("pair_family:outer_outer")
            tags.append("pair_family:outer_outer_hard" if asp in hard else "pair_family:outer_outer_soft")
        if bool({a,b} & outer) and bool({a,b} & personal):
            tags.append("pair_family:outer_personal")
            tags.append("pair_family:outer_personal_hard" if asp in hard else "pair_family:outer_personal_soft")
        if {a,b} <= personal:
            tags.append("pair_family:personal_personal")
        for name, fn in THEME_RULES.items():
            if fn(a, b, asp):
                tags.append(f"theme:{name}")
        for t in tags:
            buckets[t].add(idx)
            bucket_features[t].add(e.feature)
    return buckets, bucket_features


def baseline_for(labels):
    out = {}
    for h in HORIZONS:
        vals = [ret(labels, i, h) for i in range(len(labels))]
        out[h] = [v for v in vals if v is not None]
    return out


def score_return_bucket(name, idxs, labels, train_cut_idx, baseline):
    idxs = sorted(set(idxs))
    train = [i for i in idxs if i <= train_cut_idx]
    test = [i for i in idxs if i > train_cut_idx]
    if len(train) < MIN_TRAIN_EVENTS or len(test) < MIN_TEST_EVENTS:
        return None
    horizons = {}
    best = None
    best_h = None
    for h in HORIZONS:
        bvals = baseline[h]
        if not bvals:
            continue
        bavg = statistics.mean(bvals)
        bmed = statistics.median(bvals)
        train_vals = [ret(labels, i, h) for i in train]
        test_vals = [ret(labels, i, h) for i in test]
        all_vals = [ret(labels, i, h) for i in idxs]
        train_vals = [v for v in train_vals if v is not None]
        test_vals = [v for v in test_vals if v is not None]
        all_vals = [v for v in all_vals if v is not None]
        if len(train_vals) < MIN_TRAIN_EVENTS or len(test_vals) < MIN_TEST_EVENTS:
            continue
        train_edge = statistics.mean(train_vals) - bavg
        test_edge = statistics.mean(test_vals) - bavg
        same = (train_edge >= 0 and test_edge >= 0) or (train_edge <= 0 and test_edge <= 0)
        robustness = (abs(train_edge) * 0.4 + abs(test_edge) * 0.6) if same else -abs(train_edge - test_edge)
        all_avg = statistics.mean(all_vals) if all_vals else None
        all_median = statistics.median(all_vals) if all_vals else None
        median_agrees = None
        if all_avg is not None and all_median is not None:
            median_agrees = (all_avg >= bavg and all_median >= bmed) or (all_avg <= bavg and all_median <= bmed)
        horizons[str(h)] = {
            "baseline_avg_pct": pct(bavg),
            "baseline_median_pct": pct(bmed),
            "baseline_bullish_pct": pct(sum(v > 0 for v in bvals) / len(bvals)),
            "all": summarize(all_vals),
            "train": summarize(train_vals),
            "test": summarize(test_vals),
            "all_edge_pp": round((statistics.mean(all_vals) - bavg) * 100, 3) if all_vals else None,
            "train_edge_pp": round(train_edge * 100, 3),
            "test_edge_pp": round(test_edge * 100, 3),
            "same_direction": same,
            "median_agrees": median_agrees,
            "robustness_score_pp": round(robustness * 100, 3),
        }
        key = (robustness, abs(test_edge), h)
        if best is None or key > best:
            best = key
            best_h = h
    if not horizons:
        return None
    return {
        "name": name,
        "event_count": len(idxs),
        "train_events": len(train),
        "test_events": len(test),
        "best_horizon": best_h,
        "best_robustness_score_pp": horizons[str(best_h)]["robustness_score_pp"],
        "best_train_edge_pp": horizons[str(best_h)]["train_edge_pp"],
        "best_test_edge_pp": horizons[str(best_h)]["test_edge_pp"],
        "horizons": horizons,
    }


def score_buckets(buckets, bucket_features, regime_labels, base, market_labels, train_cut_idx, min_events):
    rows = []
    baseline = baseline_for(market_labels)
    for name, idxs in buckets.items():
        if len(idxs) < min_events:
            continue
        regime_metrics = {label: summarize_rate(idxs, label_set, base[label]) for label, label_set in regime_labels.items()}
        returns = score_return_bucket(name, idxs, market_labels, train_cut_idx, baseline)
        rows.append({
            "name": name,
            "event_count": len(set(idxs)),
            "feature_count": len(bucket_features[name]),
            "features_sample": sorted(bucket_features[name])[:12],
            "regime_metrics": regime_metrics,
            "return_metrics": returns,
        })
    return rows


def top_regime(rows, label, n=15):
    return sorted(rows, key=lambda r: (r["regime_metrics"][label]["z_approx"] or -999, r["regime_metrics"][label]["lift"] or 0, r["event_count"]), reverse=True)[:n]


def top_returns(rows, direction="bullish", n=15):
    pool = [r for r in rows if r.get("return_metrics")]
    def key(r):
        rm = r["return_metrics"]
        h = str(rm["best_horizon"])
        m = rm["horizons"][h]
        signed = m["test_edge_pp"]
        if direction == "bearish":
            signed = -signed
        return (m["same_direction"], signed, abs(m["train_edge_pp"]), r["event_count"])
    return sorted(pool, key=key, reverse=True)[:n]


def run_asset(asset, include_universes=True):
    provider = YahooFinanceProvider(timeout=60)
    candles = provider.fetch_daily(asset, START, END)
    market_labels = add_candle_forward_returns(candles, HORIZONS)
    cycles = detect_drawdown_cycles(candles)
    regime_labels = make_label_sets(candles, cycles)
    base = base_shares(regime_labels, len(candles))
    train_cut_idx = max(i for i, c in enumerate(candles) if c.timestamp.date().isoformat() <= TRAIN_END)
    baseline_summary = {str(h): summarize(vals) for h, vals in baseline_for(market_labels).items()}
    result = {
        "asset": asset,
        "period": {
            "requested_start": START,
            "actual_start": candles[0].timestamp.date().isoformat(),
            "actual_end": candles[-1].timestamp.date().isoformat(),
            "candles": len(candles),
            "train_end": TRAIN_END,
            "train_candles": train_cut_idx + 1,
            "test_candles": len(candles) - train_cut_idx - 1,
        },
        "base_day_shares": {k: pct(v) for k, v in base.items()},
        "bear_cycles": cycles,
        "baseline_forward_returns": baseline_summary,
        "universes": [],
    }
    if not include_universes:
        return result

    adapter = SwissEphemerisAdapter()
    for universe_name, bodies, orb in [
        ("gold_outer_big_cycles", OUTER_BODIES, 3.0),
        ("gold_no_moon_full", FULL_BODIES, 2.5),
    ]:
        positions = generate_planet_positions(
            adapter,
            candles[0].timestamp.astimezone(timezone.utc),
            candles[-1].timestamp.astimezone(timezone.utc),
            timedelta(days=1),
            bodies,
        )
        aspect_days = scan_aspect_series(positions, {a: orb for a in ASPECTS})
        windows, skipped = build_window_events(aspect_days, candles)
        buckets, bucket_features = aggregate_buckets(windows)
        feature_rows = score_buckets({k: v for k, v in buckets.items() if k.startswith("feature:")}, bucket_features, regime_labels, base, market_labels, train_cut_idx, MIN_FEATURE_EVENTS)
        theme_rows = score_buckets({k: v for k, v in buckets.items() if not k.startswith("feature:")}, bucket_features, regime_labels, base, market_labels, train_cut_idx, MIN_THEME_EVENTS)
        ranked = {}
        for lab in ["bull", "bear", "peak_window_30td", "bottom_window_30td", "pre_peak_30td", "post_bottom_30td"]:
            ranked[f"top_{lab}_features"] = top_regime(feature_rows, lab, 20)
            ranked[f"top_{lab}_themes"] = top_regime(theme_rows, lab, 20)
        ranked["top_bullish_return_features"] = top_returns(feature_rows, "bullish", 20)
        ranked["top_bearish_return_features"] = top_returns(feature_rows, "bearish", 20)
        ranked["top_bullish_return_themes"] = top_returns(theme_rows, "bullish", 20)
        ranked["top_bearish_return_themes"] = top_returns(theme_rows, "bearish", 20)
        result["universes"].append({
            "universe": universe_name,
            "config": {"bodies": bodies, "aspects": ASPECTS, "orb_degrees": orb},
            "counts": {
                "positions": len(positions),
                "raw_aspect_days": len(aspect_days),
                "exact_windows_mapped": len(windows),
                "exact_windows_skipped_no_candle": skipped,
                "feature_buckets_scored": len(feature_rows),
                "theme_buckets_scored": len(theme_rows),
            },
            "ranked": ranked,
        })
    return result


# Manually frozen classifier refined after historical screen. It is intentionally simple:
# matches exact discovered features plus larger recurring theme buckets.
PROJECTION_RULES = {
    "peak_risk": lambda f: f in {"jupiter_neptune_square", "jupiter_neptune_sextile", "jupiter_uranus_square", "jupiter_uranus_opposition", "mars_pluto_square", "saturn_uranus_square"} or ("neptune" in f and f.endswith("_square")) or ("uranus" in f and f.endswith("_square")),
    "pressure": lambda f: f in {"pluto_saturn_opposition", "pluto_saturn_square", "saturn_neptune_opposition", "saturn_neptune_square", "jupiter_uranus_sextile", "jupiter_pluto_opposition"} or f.endswith("_opposition") and any(p in f for p in ["saturn", "uranus", "pluto"]),
    "bottom_reversal_watch": lambda f: f in {"mars_pluto_conjunction", "mars_uranus_conjunction", "jupiter_saturn_trine", "sun_venus_conjunction", "mercury_uranus_conjunction", "neptune_pluto_sextile", "jupiter_pluto_trine"},
    "constructive_bull_window": lambda f: f in {"jupiter_pluto_trine", "jupiter_saturn_trine", "jupiter_neptune_trine", "jupiter_neptune_sextile", "pluto_saturn_sextile", "sun_venus_trine", "sun_venus_sextile"} or f.endswith("_trine") and any(p in f for p in ["jupiter", "venus"]),
}


def classify_future_event(feature):
    cats = [name for name, fn in PROJECTION_RULES.items() if fn(feature)]
    if not cats:
        return ["mixed_watch"]
    # If a window is both constructive and peak-risk, label as mixed/late-cycle rather than pure bullish.
    if "peak_risk" in cats and "constructive_bull_window" in cats:
        return ["mixed_watch", "peak_risk", "constructive_bull_window"]
    return cats


def generate_projection():
    adapter = SwissEphemerisAdapter()
    positions = generate_planet_positions(
        adapter,
        datetime.fromisoformat(FUTURE_START).replace(tzinfo=timezone.utc),
        datetime.fromisoformat(FUTURE_END).replace(tzinfo=timezone.utc),
        timedelta(days=1),
        FULL_BODIES,
    )
    aspect_days = scan_aspect_series(positions, {a: 2.5 for a in ASPECTS})
    windows = build_future_window_events(aspect_days)
    classified = []
    for e in sorted(windows, key=lambda x: x.exact_date):
        cats = classify_future_event(e.feature)
        if cats == ["mixed_watch"]:
            continue
        classified.append({
            "feature": e.feature,
            "categories": cats,
            "start_date": e.start_date,
            "exact_date": e.exact_date,
            "end_date": e.end_date,
            "min_orb": e.min_orb,
            "max_strength": e.max_strength,
        })
    by_year = defaultdict(lambda: defaultdict(int))
    highlights = []
    for e in classified:
        y = e["exact_date"][:4]
        for c in e["categories"]:
            by_year[y][c] += 1
        priority = {"peak_risk": 4, "pressure": 3, "bottom_reversal_watch": 3, "constructive_bull_window": 2, "mixed_watch": 1}
        score = sum(priority.get(c, 0) for c in e["categories"]) + e["max_strength"] / 10
        if score >= 3:
            ee = dict(e)
            ee["priority_score"] = round(score, 3)
            highlights.append(ee)
    highlights = sorted(highlights, key=lambda x: (-x["priority_score"], x["exact_date"]))[:80]
    return {
        "period": {"start": FUTURE_START, "end": FUTURE_END},
        "config": {"bodies": FULL_BODIES, "aspects": ASPECTS, "orb_degrees": 2.5, "rules": "simple category rules derived from historical Gold/XAU screen; watchlist only"},
        "counts": {"future_positions": len(positions), "raw_aspect_days": len(aspect_days), "exact_windows": len(windows), "classified_windows": len(classified)},
        "category_counts_by_year": {y: dict(v) for y, v in sorted(by_year.items())},
        "highlight_windows": sorted(highlights, key=lambda x: x["exact_date"]),
    }


def main():
    primary = run_asset(PRIMARY_ASSET, include_universes=True)
    validations = [run_asset(a, include_universes=False) for a in VALIDATION_ASSETS]
    out = {
        "experiment": "Gold/XAU astrology regime enrichment, forward-return event study, and 5-year watchlist projection using hermetic-alpha v0.1.1",
        "primary_asset": PRIMARY_ASSET,
        "validation_assets": VALIDATION_ASSETS,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": {
            "event_construction": "Consecutive active aspect days are collapsed into one exact-date window using minimum orb; non-trading exact dates map to same/next candle within 3 calendar days.",
            "regime_labels": "Bull/bear/peak/bottom use >=20% drawdown cycles. Bear is active peak-to-bottom decline; peak/bottom windows are +/-30 trading days.",
            "forward_returns": f"Forward returns are measured over {HORIZONS} trading-day horizons and compared against same-asset baselines with chronological train/test split through {TRAIN_END}.",
            "projection": "Future windows are watchlist categories based on simple rules derived from historical themes; not a price forecast or trading signal.",
        },
        "primary_result": primary,
        "validation_result_summaries": validations,
        "projection_5y": generate_projection(),
        "caveats": [
            "Exploratory research only; not financial advice.",
            "Yahoo Finance commodity futures data is convenient but not audit-grade and may include contract/roll artifacts.",
            "Peak and bottom labels are hindsight-defined by drawdown cycles.",
            "Multiple testing is severe; future projection is a watchlist, not a prediction.",
            "The projection should be validated against spot XAU/USD, GLD, and gold-miner equities when better data is available.",
        ],
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
