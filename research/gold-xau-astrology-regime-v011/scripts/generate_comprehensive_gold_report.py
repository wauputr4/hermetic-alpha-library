#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DATA = Path('/tmp/gold-xau-astrology-research-v011.json')
OUTDIR = Path('/tmp/hermetic-alpha-library-main/research/gold-xau-astrology-regime-v011')
SCRIPT_SRC = Path('/tmp/hermetic-alpha-v011-recheck/gold_xau_astrology_research.py')


def pct(v):
    if v is None:
        return 'n/a'
    return f"{float(v):.3f}%"


def val(v):
    if v is None:
        return 'n/a'
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def md_table(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for row in rows:
        out.append('| ' + ' | '.join(str(x) for x in row) + ' |')
    return '\n'.join(out) + '\n'


def enrich_rows(rows, label, n=12):
    body = []
    for i, r in enumerate(rows[:n], 1):
        m = r['regime_metrics'][label]
        rm = r.get('return_metrics', {})
        body.append([
            i,
            f"`{r['name'].replace('theme:', '').replace('pair:', '').replace('planet_aspect:', '').replace('feature:', '')}`",
            r.get('event_count', m.get('n')),
            m.get('observed'),
            pct(m.get('rate_pct')),
            pct(m.get('base_rate_pct')),
            val(m.get('lift')),
            val(m.get('z_approx')),
            rm.get('best_horizon', 'n/a'),
            pct(rm.get('best_train_edge_pp')) if rm else 'n/a',
            pct(rm.get('best_test_edge_pp')) if rm else 'n/a',
        ])
    return md_table(['Rank','Bucket','Events','Inside label','Rate','Baseline','Lift','z','Best h','Train edge','Test edge'], body)


def return_rows(rows, n=15):
    body = []
    for i, r in enumerate(rows[:n], 1):
        rm = r['return_metrics']
        h = str(rm['best_horizon'])
        hs = rm['horizons'][h]
        allm = hs['all']
        body.append([
            i,
            f"`{r['name'].replace('theme:', '').replace('pair:', '').replace('planet_aspect:', '').replace('feature:', '')}`",
            r.get('event_count', rm.get('event_count')),
            f"{h}d",
            pct(rm.get('best_train_edge_pp')),
            pct(rm.get('best_test_edge_pp')),
            pct(allm.get('avg_pct')),
            pct(allm.get('median_pct')),
            pct(allm.get('bullish_pct')),
            'yes' if hs.get('median_agrees') else 'no',
        ])
    return md_table(['Rank','Bucket','Events','Best horizon','Train edge','Test edge','Avg return','Median','Bullish','Median agrees'], body)


def horizon_detail(name, r):
    rm = r['return_metrics']
    rows = []
    for h in ['3','7','14','30','60','90','180']:
        if h not in rm['horizons']:
            continue
        hs = rm['horizons'][h]
        rows.append([
            f"{h}d",
            pct(hs.get('baseline_avg_pct')),
            pct(hs.get('train', {}).get('avg_pct')),
            pct(hs.get('train_edge_pp')),
            pct(hs.get('test', {}).get('avg_pct')),
            pct(hs.get('test_edge_pp')),
            pct(hs.get('all', {}).get('median_pct')),
            pct(hs.get('all', {}).get('bullish_pct')),
            'yes' if hs.get('same_direction') else 'no',
        ])
    return f"### Horizon profile: `{name}`\n\n" + md_table(['Horizon','Baseline avg','Train avg','Train edge','Test avg','Test edge','All median','All bullish','Same direction'], rows)


def watchlist_rows(windows, n=None):
    rows = []
    seq = windows if n is None else windows[:n]
    for w in seq:
        rows.append([
            w['exact_date'],
            f"{w['start_date']} to {w['end_date']}",
            f"`{w['feature']}`",
            ', '.join(w['categories']),
            f"{w.get('score', w.get('priority_score', 0)):.3f}",
        ])
    return md_table(['Exact date','Window','Feature','Categories','Score'], rows)


def by_year_highlights(windows):
    out = []
    for year in range(2026, 2032):
        rows = [w for w in windows if w['exact_date'].startswith(str(year))]
        if not rows:
            continue
        # keep category-diverse, higher score first
        pick = sorted(rows, key=lambda x: (-x.get('score', x.get('priority_score', 0)), x['exact_date']))[:12]
        out.append(f"### {year}\n")
        out.append(watchlist_rows(pick))
    return '\n'.join(out)


def main():
    d = json.loads(DATA.read_text())
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / 'scripts').mkdir(exist_ok=True)

    pr = d['primary_result']
    period = pr['period']
    outer = next(u for u in pr['universes'] if u['universe'] == 'gold_outer_big_cycles')
    full = next(u for u in pr['universes'] if u['universe'] == 'gold_no_moon_full')
    proj = d['projection_5y']
    windows = proj['highlight_windows']

    today = date.today().isoformat()
    lines = []
    lines.append('---')
    lines.append('title: "Gold/XAU Astrology Regime, Forward-Return, and 5-Year Cycle Study"')
    lines.append('subtitle: "Hermetic Alpha v0.1.1 exact-window event study on GC=F with GLD/IAU validation summaries"')
    lines.append('author: "Hermes Agent for Wauputra"')
    lines.append(f'date: "{today}"')
    lines.append('geometry: margin=0.75in')
    lines.append('fontsize: 9pt')
    lines.append('---\n')

    lines.append('# Executive Summary\n')
    lines.append('This paper expands the initial Gold/XAU experiment into a more complete, repo-ready research package. It applies the same Hermetic Alpha workflow previously used for Bitcoin and S&P 500: convert planetary aspects into exact-date market events, compare those events against Gold futures returns and regime labels, then freeze a simple interpretation map for a 2026-2031 watchlist.\n')
    lines.append('The report is intentionally exploratory. It does not claim astrology causes price movement and it is not financial advice. The useful output is a set of testable hypotheses: which aspect families coincided with Gold bear pressure, peak-risk, bottom/reversal zones, and above/below-baseline forward returns.\n')
    lines.append('Main takeaways:\n')
    lines.append(f"- Primary data: Yahoo Finance `GC=F` / COMEX Gold Futures, {period['actual_start']} to {period['actual_end']}, {period['candles']:,} daily candles. Yahoo did not return a usable `XAUUSD=X` series in the run, so futures are the primary proxy.\n")
    lines.append(f"- Major regime labels: {len(pr['bear_cycles'])} drawdown cycles of at least 20%, with bear/pressure days equal to {pct(pr['base_day_shares']['bear'])} of the sample.\n")
    lines.append('- Gold is not S&P 500. Stress themes are not automatically bearish because Gold can receive safe-haven flows. The best practical reading is four buckets: pressure/volatility, peak-risk, bottom/reversal watch, and constructive support.\n')
    lines.append('- The most consistent constructive forward-return themes in this run include `jupiter_saturn`, `sun_venus`, outer-outer soft themes, and selected Mars/Saturn or Mars/Uranus sextile/trine features.\n')
    lines.append('- The clearest instability/underperformance candidate is `jupiter_uranus`, especially around 30-day horizons, where test-period behavior lagged baseline.\n')
    lines.append('- The 2026-2031 future table is a watchlist, not a forecast. 2027 has the densest mix of peak-risk and constructive windows; it should be monitored as a high-information year rather than interpreted one-directionally.\n')

    lines.append('# Research Questions\n')
    lines.append('1. Which large-cycle aspect themes are over-represented during Gold bear/pressure regimes?\n')
    lines.append('2. Which themes cluster around historically defined peak-risk and bottom/reversal windows?\n')
    lines.append('3. Which exact aspect windows show same-direction train/test forward-return edges versus Gold baseline?\n')
    lines.append('4. Can those findings be converted into a simple 5-year watchlist without pretending to predict price?\n')

    lines.append('# Data Provenance\n')
    lines.append(md_table(['Item','Value'], [
        ['Primary asset','`GC=F` / COMEX Gold Futures via Yahoo Finance'],
        ['Requested start','1990-01-01'],
        ['Actual start',period['actual_start']],
        ['Actual end',period['actual_end']],
        ['Candles',f"{period['candles']:,}"],
        ['Train/test split',f"Train through {period['train_end']} ({period['train_candles']:,} candles); test after ({period['test_candles']:,} candles)"],
        ['Validation proxies','`GLD`, `IAU` summary checks'],
        ['Library','`hermetic-alpha` / `hermetic-alpha-library` v0.1.1 workspace'],
    ]))
    lines.append('Why `GC=F`: the first attempted spot-like Yahoo symbol, `XAUUSD=X`, returned a market-data provider error. `GC=F` is not identical to spot XAU/USD; it can include futures contract and roll artifacts. The result should be treated as a Gold-proxy study until a cleaner spot source is added.\n')

    lines.append('# Methodology\n')
    lines.append('## Aspect event construction\n')
    lines.append('- Generate daily planetary positions over the asset date range.\n- Scan conjunction, opposition, trine, square, and sextile aspects.\n- Collapse consecutive active aspect days into one event window.\n- Use the minimum-orb day as the exact event date.\n- Map non-trading exact dates to the same or next available Gold candle within a documented 3-calendar-day tolerance.\n- Measure forward returns from exact event dates only, avoiding the mistake of counting every active day in a multi-day aspect as an independent observation.\n')
    lines.append('## Universes scanned\n')
    lines.append(md_table(['Universe','Bodies','Exact windows mapped','Raw aspect days','Feature buckets','Theme buckets'], [
        ['Outer big cycles', ', '.join(outer['config']['bodies']), outer['counts']['exact_windows_mapped'], outer['counts']['raw_aspect_days'], outer['counts']['feature_buckets_scored'], outer['counts']['theme_buckets_scored']],
        ['Full no-moon scan', ', '.join(full['config']['bodies']), full['counts']['exact_windows_mapped'], full['counts']['raw_aspect_days'], full['counts']['feature_buckets_scored'], full['counts']['theme_buckets_scored']],
    ]))
    lines.append('## Regime labels\n')
    lines.append('Regimes are hindsight labels based on >=20% drawdown cycles. `bear` is the peak-to-bottom decline. `peak_window_30td` and `bottom_window_30td` are +/-30 trading-day windows around detected major peaks/bottoms. `pre_peak_30td` and `post_bottom_30td` are one-sided context labels.\n')
    lines.append('## Return scoring\n')
    lines.append('Forward-return horizons are 3, 7, 14, 30, 60, 90, and 180 trading days. Each event return is compared against the same-asset baseline for the same horizon. A candidate is more interesting when train edge and test edge have the same direction, median does not contradict average, and event count is not tiny.\n')

    lines.append('# Gold Baseline\n')
    base_rows = []
    for h in ['3','7','14','30','60','90','180']:
        b = pr['baseline_forward_returns'][h]
        base_rows.append([f'{h}d', b['n'], pct(b['avg_pct']), pct(b['median_pct']), pct(b['bullish_pct']), pct(b['min_pct']), pct(b['max_pct'])])
    lines.append(md_table(['Horizon','Valid days','Avg','Median','Bullish','Min','Max'], base_rows))
    lines.append('Gold has a positive long-run drift in this sample, especially at 90d and 180d horizons. This is why raw positive post-event returns are not sufficient; the event must beat Gold baseline to be interesting.\n')

    lines.append('## Detected >=20% drawdown cycles\n')
    cyc_rows = []
    for c in pr['bear_cycles']:
        cyc_rows.append([c['peak_date'], c['bottom_date'], c.get('recovery_date') or 'not recovered', pct(c['max_drawdown_pct']), c.get('peak_to_bottom_trading_days', c.get('peak_to_bottom_days', 'n/a'))])
    lines.append(md_table(['Peak','Bottom','Recovery','Max drawdown','Peak-to-bottom trading days'], cyc_rows))
    lines.append('Base day shares:\n')
    share_rows = [[k, pct(v)] for k, v in pr['base_day_shares'].items()]
    lines.append(md_table(['Label','Share of trading days'], share_rows))

    lines.append('# Regime Enrichment Results\n')
    lines.append('The enrichment tables show which aspect/theme buckets appeared inside a regime label more often than the label baseline. `Lift` > 1 means the bucket appeared more frequently inside that label than random trading days did. The z-score is approximate and used only for screening.\n')
    labels = [
        ('bear','Bear / pressure'),
        ('peak_window_30td','Peak-risk window'),
        ('pre_peak_30td','Pre-peak 30 trading days'),
        ('bottom_window_30td','Bottom / reversal window'),
        ('post_bottom_30td','Post-bottom 30 trading days'),
        ('bull','Bull / constructive background'),
    ]
    for label, title in labels:
        lines.append(f'## {title}: outer big-cycle themes\n')
        lines.append(enrich_rows(outer['ranked'][f'top_{label}_themes'], label, 10))
        lines.append(f'## {title}: full no-moon themes\n')
        lines.append(enrich_rows(full['ranked'][f'top_{label}_themes'], label, 10))

    lines.append('# Forward-Return Results\n')
    lines.append('These tables rank candidates by robust same-direction train/test edge. Positive candidates are not necessarily trade signals; they are hypothesis candidates for further validation. Negative candidates are underperformance or caution themes versus Gold baseline.\n')
    lines.append('## Robust bullish / constructive themes\n')
    lines.append(return_rows(full['ranked']['top_bullish_return_themes'], 18))
    lines.append('## Robust bearish / underperforming themes\n')
    lines.append(return_rows(full['ranked']['top_bearish_return_themes'], 18))
    lines.append('## Robust bullish exact features\n')
    lines.append(return_rows(full['ranked']['top_bullish_return_features'], 18))
    lines.append('## Robust bearish exact features\n')
    lines.append(return_rows(full['ranked']['top_bearish_return_features'], 18))

    # Add detailed horizon profiles for headline candidates
    headline_names = ['jupiter_saturn', 'sun_venus', 'jupiter_uranus', 'pluto_uranus_square']
    lines.append('# Headline Candidate Profiles\n')
    all_candidates = full['ranked']['top_bullish_return_themes'] + full['ranked']['top_bearish_return_themes'] + full['ranked']['top_bullish_return_features'] + full['ranked']['top_bearish_return_features']
    for name in headline_names:
        match = None
        for r in all_candidates:
            clean = r['name'].replace('theme:', '').replace('pair:', '').replace('planet_aspect:', '').replace('feature:', '')
            if clean == name:
                match = r; break
        if match:
            lines.append(horizon_detail(name, match))

    lines.append('# Interpretation Map\n')
    lines.append('## 1. Pressure / bear watch\n')
    lines.append('The clearest large-cycle pressure candidate is `jupiter_uranus`. In the outer-cycle scan it had 26 events, with 46.154% inside bear regimes versus a 29.374% bear baseline. It also appeared in peak and bottom windows at roughly 2x baseline, which makes it an instability marker rather than a simple bearish signal. In forward returns, `jupiter_uranus` was a same-direction underperformer at the 30d horizon in the full no-moon theme screen.\n')
    lines.append('Other pressure-enriched full-scan themes include `neptune_opposition`, `pluto_trine`, `saturn_conjunction`, `uranus_opposition`, `pluto_square`, and `venus_opposition`. These should be read as volatility and stress markers first.\n')
    lines.append('## 2. Peak-risk watch\n')
    lines.append('Peak-risk enrichment leans toward opposition/square language: `pluto_opposition`, broad `opposition`, `mars_square`, `sun_opposition`, `mercury_opposition`, and `jupiter_opposition`. In Gold this can mean late-cycle speculative acceleration, macro stress, or exhaustion depending on the prior price path.\n')
    lines.append('## 3. Bottom / reversal watch\n')
    lines.append('Bottom-window enrichment is not purely soft. The outer-cycle scan highlights `square`, `hard`, and `outer_outer_hard`, while the full scan highlights `uranus_trine`, `neptune_square`, `pluto_conjunction`, `jupiter_sextile`, and `outer_personal_soft`. This supports a reset/rebuild interpretation: Gold bottoms may form around both hard capitulation windows and soft release windows.\n')
    lines.append('## 4. Constructive windows\n')
    lines.append('Forward-return candidates make `jupiter_saturn` the cleanest constructive theme in this run: 27 events, best horizon 180d, train edge +2.775pp, test edge +7.260pp, average return 14.023%, median 12.098%, bullish 80.769%. `sun_venus` is shorter horizon but also notable: 32 events, best horizon 60d, train edge +0.429pp, test edge +2.246pp, average return 4.321%, median 4.514%, bullish 81.250%.\n')
    lines.append('## 5. Gold versus S&P 500\n')
    lines.append('For equities, pressure windows often map more directly to downside risk. For Gold, the same macro-stress window can produce either pressure or a defensive bid. Therefore the Gold framework should not be used as a one-line long/short engine. It is better as a context layer: identify historically interesting dates, then check trend, real rates, USD strength, inflation expectations, liquidity, and geopolitical stress.\n')

    lines.append('# Validation Proxies: GLD and IAU\n')
    lines.append('The current run includes GLD and IAU as regime/data sanity checks, not full replicated aspect scans. They broadly confirm that ETF Gold proxies have similar major drawdown structure but shorter histories than `GC=F`.\n')
    vrows = []
    for v in d['validation_result_summaries']:
        p = v['period']
        shares = v['base_day_shares']
        vrows.append([v['asset'], p['actual_start'], p['actual_end'], p['candles'], pct(shares.get('bull')), pct(shares.get('bear')), pct(shares.get('peak_window_30td')), pct(shares.get('bottom_window_30td')), v['bear_cycles']])
    lines.append(md_table(['Asset','Start','End','Candles','Bull share','Bear share','Peak window','Bottom window','Drawdown cycles'], vrows))
    lines.append('Next validation should run the complete event/return scan on `GLD`, `IAU`, `GDX`, `GDXJ`, `UUP`, and `TLT`, then test whether the same frozen Gold rules remain directionally useful.\n')

    lines.append('# Five-Year Projection Watchlist: 2026-2031\n')
    lines.append('The future projection freezes the historical interpretation map into category rules and applies it to future exact aspect windows. It is not a price forecast. It is a dated research checklist.\n')
    lines.append(md_table(['Item','Value'], [
        ['Projection start', proj['period']['start']],
        ['Projection end', proj['period']['end']],
        ['Future exact aspect windows generated', proj['counts'].get('future_exact_windows', proj['counts'].get('exact_windows'))],
        ['Classified watchlist windows', proj['counts'].get('classified_watchlist_windows', proj['counts'].get('classified_windows'))],
    ]))
    crows = []
    for year, counts in sorted(proj['category_counts_by_year'].items()):
        crows.append([year, counts.get('peak_risk',0), counts.get('pressure',0), counts.get('bottom_reversal_watch',0), counts.get('constructive_bull_window',0)])
    lines.append('## Category counts by year\n')
    lines.append(md_table(['Year','Peak-risk','Pressure','Bottom/reversal watch','Constructive window'], crows))
    lines.append('Interpretation: 2027 is the busiest year by both peak-risk and constructive markers. That does not mean “up” or “down”; it means more historically interesting windows where Gold should be monitored closely. 2028-2030 remain active but more balanced. 2031 is partial-year only in this projection.\n')
    lines.append('## Category definitions\n')
    lines.append('- `peak_risk`: euphoria, instability, exhaustion, or fragile-structure candidates.\n- `pressure`: stress, drawdown, volatility, or macro-risk candidates. In Gold, pressure may also coincide with safe-haven demand.\n- `bottom_reversal_watch`: capitulation, reset, or rebuild candidates; most useful after a preceding decline.\n- `constructive_bull_window`: historically supportive or relief-oriented candidates, not standalone buy signals.\n')
    lines.append('## Highest-score highlights by year\n')
    lines.append(by_year_highlights(windows))
    lines.append('## Full classified highlight table\n')
    lines.append(watchlist_rows(windows))

    lines.append('# Practical Research Workflow\n')
    lines.append('A practical way to use this research without over-trusting it:\n')
    lines.append('1. Keep the 2026-2031 dates as a watchlist.\n2. Before each window, check whether Gold is extended, basing, or already drawing down.\n3. Pair the astrology bucket with non-astrology context: real rates, USD, inflation expectations, central-bank policy, liquidity, and geopolitical stress.\n4. Record what actually happened after each window without changing the rules.\n5. After enough future windows pass, evaluate the frozen rules out-of-sample.\n')

    lines.append('# Caveats and Failure Modes\n')
    for c in d['caveats']:
        lines.append(f'- {c}\n')
    lines.append('- Futures data can differ from spot Gold because of contract roll, liquidity, adjustment, and Yahoo data choices.\n- Hindsight drawdown labels are useful for research, but they are not known in real time.\n- Multiple testing is severe. A pattern that looks good after scanning many bodies/aspects/horizons can be a false positive.\n- Outer-planet aspects have small event counts; treat them as narrative hypotheses unless validated elsewhere.\n- Average returns can be distorted by a few large moves; median and bullish percentage must be checked alongside averages.\n- The future calendar can look authoritative because it has exact dates. It should be read as a watchlist, not a prediction.\n')

    lines.append('# Suggested Next Steps\n')
    lines.append('1. Add a cleaner spot XAU/USD provider and rerun the same pipeline.\n2. Run full scans on `GLD`, `IAU`, `GDX`, `GDXJ`, `UUP`, `TLT`, and real-rate proxies.\n3. Convert the frozen interpretation rules into code under Hermetic Alpha so future watchlist generation is reproducible.\n4. Create a prospective tracking issue/discussion that logs each 2026-2031 window outcome without changing criteria.\n5. Compare Gold rules against S&P 500 and Bitcoin rules to separate asset-specific behavior from broad macro-cycle behavior.\n')

    lines.append('# Reproducibility\n')
    lines.append('Artifacts in this research package:\n')
    lines.append('- `README.md`: this paper.\n- `gold-xau-astrology-research-hermetic-alpha-v011.pdf`: PDF version.\n- `scripts/gold_xau_astrology_research.py`: reproduction script used for the experiment.\n')
    lines.append('The source script writes a JSON results file and then the paper generator converts selected tables and interpretation into Markdown/PDF artifacts.\n')

    lines.append('# Disclaimer\n')
    lines.append('This is exploratory market research and library dogfooding. It is not investment advice, financial advice, or a recommendation to buy, sell, short, or leverage Gold or any related instrument.\n')

    md = '\n'.join(lines)
    (OUTDIR / 'README.md').write_text(md)
    if SCRIPT_SRC.exists():
        (OUTDIR / 'scripts' / 'gold_xau_astrology_research.py').write_text(SCRIPT_SRC.read_text())
    print(OUTDIR / 'README.md')
    print(len(md), 'chars')

if __name__ == '__main__':
    main()
