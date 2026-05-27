"""Fetch normalized Yahoo Finance BTC candles and cache them as JSON."""

from __future__ import annotations

import argparse
from pathlib import Path

from hermetic_alpha.market import YahooFinanceProvider, write_candles_json


def write_btc_daily_cache(
    output_path: str | Path,
    *,
    start: str,
    end: str,
    provider: YahooFinanceProvider | None = None,
) -> Path:
    """Fetch BTC-USD daily candles and write them through the library cache helper."""

    destination = Path(output_path)
    market_provider = provider or YahooFinanceProvider()
    candles = market_provider.fetch_daily_btc(start, end)
    write_candles_json(destination, candles)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_path", help="Destination JSON cache path")
    parser.add_argument("--start", required=True, help="Inclusive UTC start date, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="Inclusive UTC end date, YYYY-MM-DD")
    args = parser.parse_args()

    path = write_btc_daily_cache(args.output_path, start=args.start, end=args.end)
    print(path)


if __name__ == "__main__":
    main()
