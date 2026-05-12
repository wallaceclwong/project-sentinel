"""
WeatherNext Pro — Scanner Runner
Ties together WeatherClient + MarketScanner into a live scanning loop.

Usage:
    python services/scanner_runner.py            # One scan, then exit
    python services/scanner_runner.py --loop     # Continuous, every 15 min
"""
import asyncio
import argparse
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from loguru import logger

# ── Path setup ───────────────────────────────────────────────────────────────
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_root, ".env"))
if _root not in sys.path:
    sys.path.insert(0, _root)

from services.weather_client import WeatherClient, DailyForecast
from services.market_scanner import MarketScanner, MarketInfo, TradeSignal, CITY_COORDS

# ── Config from env ──────────────────────────────────────────────────────────
MIN_EDGE_PCT    = float(os.getenv("MIN_EDGE_PCT",           "10.0"))
MIN_LIQUIDITY   = float(os.getenv("MIN_LIQUIDITY",          "500.0"))
SCAN_INTERVAL   = int(os.getenv("SCAN_INTERVAL_MINUTES",    "15")) * 60
WEATHER_DELAY   = float(os.getenv("WEATHER_API_DELAY_SEC",  "0.8"))  # between weather calls


async def run_scan(weather: WeatherClient, scanner: MarketScanner) -> list[TradeSignal]:
    """Execute one full discovery scan. Returns actionable signals."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    _header(f"WEATHERNEXT PRO  |  {now}")

    # ── Step 1: Discover active markets on Polymarket ─────────────────────────
    print("  [1/3] Discovering active temperature markets on Polymarket...")
    active_markets: list[MarketInfo] = await scanner.discover_temp_markets()

    if not active_markets:
        print("        No active temperature markets found today.")
        print("        Markets open daily — check back later or run with --loop.")
        _footer(scanned=0, no_market=0, low_liq=0, signals=0)
        return []

    print(f"        Found {len(active_markets)} active markets.\n")

    # ── Step 2: Fetch weather forecasts for each discovered city ──────────────
    print("  [2/3] Fetching WeatherNext 2 forecasts...")
    forecasts: dict[str, DailyForecast] = {}          # city_key → forecast

    for market in active_markets:
        city_key = market.city_key
        if city_key in forecasts:
            continue                                   # already fetched

        coords = CITY_COORDS.get(city_key)
        if coords is None:
            logger.warning(f"No coordinates for city key '{city_key}', skipping")
            continue

        await asyncio.sleep(WEATHER_DELAY)             # rate-limit protection
        forecast = await weather.get_daily_forecast(
            coords["lat"], coords["lng"], coords["display"]
        )
        if forecast:
            forecasts[city_key] = forecast
            print(
                f"        {coords['display']:<14} "
                f"max={forecast.forecast_max_temp_c:.1f}°C  "
                f"range=[{forecast.low_temp_c:.1f}, {forecast.high_temp_c:.1f}]"
            )
        else:
            logger.warning(f"Weather fetch failed for {coords['display']}")

    # ── Step 3: Compute signals ───────────────────────────────────────────────
    print(f"\n  [3/3] Computing edges (min edge={MIN_EDGE_PCT:.0f}%, "
          f"min liquidity=${MIN_LIQUIDITY:,.0f})...")

    signals:         list[TradeSignal] = []
    skipped_low_liq: int = 0
    skipped_no_wx:   int = 0

    for market in active_markets:
        # Skip thin markets
        if market.liquidity < MIN_LIQUIDITY:
            skipped_low_liq += 1
            logger.debug(
                f"{market.city}: liquidity ${market.liquidity:.0f} "
                f"< ${MIN_LIQUIDITY:.0f}, skipping"
            )
            continue

        forecast = forecasts.get(market.city_key)
        if forecast is None:
            skipped_no_wx += 1
            continue

        signal = scanner.compute_signal(market, forecast, min_edge_pct=MIN_EDGE_PCT)
        _print_signal_row(market, forecast, signal)
        if signal.action != "SKIP":
            signals.append(signal)

    # ── Summary ───────────────────────────────────────────────────────────────
    _footer(
        scanned   = len(active_markets),
        no_market = skipped_no_wx,
        low_liq   = skipped_low_liq,
        signals   = len(signals),
    )

    if signals:
        print(f"  {'─'*56}")
        print(f"  ACTIONABLE SIGNALS (edge > {MIN_EDGE_PCT:.0f}%)")
        print(f"  {'─'*56}")
        for s in signals:
            _print_action_detail(s)

    return signals


# ── Print helpers ─────────────────────────────────────────────────────────────

def _header(title: str):
    print(f"\n{'='*62}")
    print(f"  {title}")
    print(f"{'='*62}")


def _footer(scanned, no_market, low_liq, signals):
    print(f"\n  {'─'*58}")
    print(f"  Markets discovered : {scanned}")
    print(f"  No weather data    : {no_market}")
    print(f"  Low liquidity skip : {low_liq}")
    print(f"  Trade signals      : {signals}")
    print(f"{'='*62}\n")


def _print_signal_row(market: MarketInfo, forecast: DailyForecast, signal: TradeSignal):
    flag = ">>" if signal.action != "SKIP" else "  "
    print(
        f"  {flag} {market.city:<14} "
        f"thresh={market.temp_threshold_c:>5.1f}C  "
        f"ours={signal.our_probability:>6.1%}  "
        f"mkt={signal.market_probability:>6.1%}  "
        f"edge={signal.edge_pct:>5.1f}%  "
        f"liq=${market.liquidity:>7,.0f}  "
        f"-> {signal.action}"
    )


def _print_action_detail(s: TradeSignal):
    print(f"\n  ** {s.city}  |  {s.action}")
    print(f"     Q   : {s.question}")
    print(f"     Ours: {s.our_probability:.1%}   Market: {s.market_probability:.1%}   Edge: {s.edge_pct:.1f}%")
    print(f"     Buy : token {s.token_id}  @ {s.price:.3f} USDC")
    print(f"     Why : {s.reason}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main(loop_mode: bool):
    weather = WeatherClient()
    scanner = MarketScanner(min_edge_pct=MIN_EDGE_PCT, request_delay=0.3)

    try:
        if loop_mode:
            logger.info(
                f"Continuous mode: scanning every {SCAN_INTERVAL//60} min. "
                f"Ctrl+C to stop."
            )
            while True:
                await run_scan(weather, scanner)
                logger.info(f"Sleeping {SCAN_INTERVAL//60} min until next scan...")
                await asyncio.sleep(SCAN_INTERVAL)
        else:
            await run_scan(weather, scanner)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        await weather.close()
        await scanner.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WeatherNext Pro Market Scanner")
    parser.add_argument(
        "--loop", action="store_true",
        help="Run continuously every SCAN_INTERVAL_MINUTES (default 15)"
    )
    args = parser.parse_args()
    asyncio.run(main(loop_mode=args.loop))
