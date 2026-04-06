"""
WeatherNext Pro — Main Entry Point
Orchestrates the scan loop: fetch weather → compute edge → log signal → execute trade.
"""
import asyncio
import os
import yaml
from datetime import datetime, timezone
from dotenv import load_dotenv
from loguru import logger

from services.weather_client import WeatherClient
from services.market_scanner import MarketScanner

load_dotenv()

# ── Logging setup ──────────────────────────────────────────────
logger.add(
    "logs/weathernext_pro.log",
    rotation="50 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)


async def run_scan_cycle(weather_client: WeatherClient, scanner: MarketScanner, config: dict):
    """One full scan cycle: weather → signals → (optional) trade."""
    trading_cfg = config.get("trading", {})
    targets = trading_cfg.get("target_markets", [])
    min_edge = trading_cfg.get("min_edge_pct", 10.0)
    paper_trading = trading_cfg.get("paper_trading", True)

    logger.info(f"{'📄 PAPER' if paper_trading else '💰 LIVE'} scan cycle — {len(targets)} markets")

    for target in targets:
        city = target["city"]
        lat = target["lat"]
        lng = target["lng"]
        slug = target["slug"]

        # 1. Get weather forecast
        forecast = await weather_client.get_daily_forecast(lat, lng, city)
        if not forecast:
            logger.warning(f"Skipping {city} — no forecast available")
            continue

        # 2. Get market info
        market = await scanner.fetch_market(slug)
        if not market:
            logger.debug(f"No active market for {slug}")
            continue

        # 3. Compute signal
        signal = scanner.compute_signal(market, forecast, min_edge_pct=min_edge)

        # 4. Log signal
        log_line = (
            f"[{city}] threshold={market.temp_threshold_c}°C | "
            f"our_prob={signal.our_probability:.1%} | "
            f"market_prob={signal.market_probability:.1%} | "
            f"edge={signal.edge_pct:.1f}% | action={signal.action}"
        )
        if signal.action != "SKIP":
            logger.success(f"🎯 {log_line}")
        else:
            logger.info(f"   {log_line}")

        # 5. Execute (paper mode just logs, live mode will place CLOB order)
        if signal.action != "SKIP":
            if paper_trading:
                logger.info(f"[PAPER] Would place: {signal.action} {signal.token_id[:12]}... @ {signal.price:.3f}")
            else:
                # TODO: Integrate Polymarket CLOB client for live execution
                logger.warning("Live trading not yet enabled. Set paper_trading: false in config + add CLOB client.")

        await asyncio.sleep(1)  # Polite pause between market queries


async def main():
    # Load config
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        logger.warning(f"Config not found at {config_path}. Using example config.")
        config_path = "config/config.example.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    scanner_cfg = config.get("scanner", {})
    interval = scanner_cfg.get("interval_minutes", 15) * 60

    weather = WeatherClient()
    scanner = MarketScanner(min_edge_pct=config.get("trading", {}).get("min_edge_pct", 10.0))

    logger.info("🌦️ WeatherNext Pro started — scanning every {} minutes", interval // 60)

    try:
        while True:
            start = datetime.now(timezone.utc)
            await run_scan_cycle(weather, scanner, config)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            wait = max(0, interval - elapsed)
            logger.info(f"Next scan in {wait/60:.1f} minutes")
            await asyncio.sleep(wait)
    except KeyboardInterrupt:
        logger.info("Shutting down WeatherNext Pro.")
    finally:
        await weather.close()
        await scanner.close()


if __name__ == "__main__":
    asyncio.run(main())
