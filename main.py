"""
WeatherNext Pro — Main Entry Point
Orchestrates the scan loop: fetch weather → compute edge → log signal → execute trade.
"""
import asyncio
import json
import os
from pathlib import Path
import yaml
from datetime import datetime, timezone
from dotenv import load_dotenv
from loguru import logger
import httpx

from services.weather_client import WeatherClient
from services.market_scanner import MarketScanner
from services.ensemble_client import EnsembleClient
from services.portfolio import Portfolio, Position

SIGNALS_PATH = Path("data/signals.jsonl")
TELEGRAM_API = "https://api.telegram.org"

load_dotenv()

# ── Logging setup ──────────────────────────────────────────────
logger.add(
    "logs/weathernext_pro.log",
    rotation="50 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)


async def run_scan_cycle(weather_client: WeatherClient, ensemble: EnsembleClient, scanner: MarketScanner, portfolio: Portfolio, config: dict):
    """One full scan cycle: discover markets → fetch weather → compute edge → log signal."""
    trading_cfg = config.get("trading", {})
    min_edge = trading_cfg.get("min_edge_pct", 10.0)
    paper_trading = trading_cfg.get("paper_trading", True)
    ensemble_weight = config.get("scanner", {}).get("ensemble_weight", 0.5)

    # 1. Auto-discover active temperature markets on Polymarket
    markets = await scanner.discover_temp_markets()
    mode_label = "PAPER" if paper_trading else "LIVE"
    logger.info(f"{mode_label} scan cycle — {len(markets)} markets discovered")

    if not markets:
        logger.warning("No active temperature markets found on Polymarket")
        return

    # Cache forecasts per city to avoid redundant API calls
    google_cache: dict[str, object] = {}
    ensemble_cache: dict[str, object] = {}

    signals = []
    for market in markets:
        # Skip illiquid markets (hard to execute)
        if market.liquidity < 1000:
            logger.debug(f"Skipping {market.city} — insufficient liquidity (${market.liquidity:.0f})")
            continue

        city_key = market.city_key
        coords = scanner.CITY_COORDS.get(city_key)
        if not coords:
            logger.debug(f"No coordinates for city: {market.city}")
            continue

        # 2. Get weather forecasts (cached per city)
        if city_key not in google_cache:
            google_cache[city_key] = await weather_client.get_daily_forecast(coords["lat"], coords["lng"], market.city)
        forecast = google_cache[city_key]

        if not forecast:
            logger.warning(f"Skipping {market.city} — no forecast available")
            continue

        # Sanity check: skip if forecast uncertainty is too high
        uncertainty = forecast.high_temp_c - forecast.low_temp_c
        if uncertainty > 4.0:
            logger.warning(f"Skipping {market.city} — forecast uncertainty too high ({uncertainty:.1f}°C)")
            continue

        if city_key not in ensemble_cache:
            ensemble_cache[city_key] = await ensemble.get_ensemble_forecast(coords["lat"], coords["lng"], market.city)
        ens_forecast = ensemble_cache[city_key]

        # 3. Compute signal (blended if ensemble available)
        signal = scanner.compute_signal(market, forecast, min_edge_pct=min_edge,
                                         ensemble_forecast=ens_forecast,
                                         ensemble_weight=ensemble_weight)

        # 4. Log signal
        bracket_label = f"{market.bracket_type} [{market.temp_low_c:.1f}, {market.temp_high_c:.1f}]°C"
        log_line = (
            f"[{market.city}] {bracket_label} | "
            f"our_prob={signal.our_probability:.1%} | "
            f"market_prob={signal.market_probability:.1%} | "
            f"edge={signal.edge_pct:.1f}% | action={signal.action}"
        )
        if signal.action != "SKIP":
            logger.success(f"🎯 {log_line}")
            signals.append(signal)
        else:
            logger.info(f"   {log_line}")

        # 5. Record prediction for later scoring
        _log_signal(signal, market, forecast)

        # 6. Execute with portfolio risk checks
        if signal.action != "SKIP":
            position_size = trading_cfg.get("max_position_usdc", 20.0)
            can_trade, reason = portfolio.can_trade(position_size)

            if can_trade:
                pos = Position(
                    market_id=f"{market.question.replace(' ', '-').lower()}-{market.city.replace(' ', '-').lower()}",
                    city=signal.city,
                    question=signal.question,
                    action=signal.action,
                    entry_price=signal.price,
                    entry_size=position_size,
                    entry_time=datetime.now(timezone.utc).isoformat(),
                    our_prob=signal.our_probability,
                    market_prob=signal.market_probability,
                    edge_pct=signal.edge_pct,
                )
                portfolio.add_position(pos)
                logger.info(f"[SIM] Opened {signal.action} {signal.city} | ${position_size:.0f} @ {signal.price:.3f}")
            else:
                logger.warning(f"Trade rejected: {reason}")

        await asyncio.sleep(1)  # Polite pause between market queries

    logger.info(f"Scan complete: {len(signals)} actionable signals from {len(markets)} markets")
    print(f"\a\n{'='*60}\n  SCAN CYCLE DONE — {len(signals)} signals from {len(markets)} markets\n{'='*60}\n")

    # Telegram alert (top 3 best opportunities)
    top_signals = sorted(signals, key=lambda s: s.edge_pct, reverse=True)[:3] if signals else []
    lines = [f"Scan Complete - {len(markets)} markets, {len(signals)} actionable\n"]
    for s in top_signals:
        # Build precise URL from question text
        # Question format: "Will the [highest/lowest] temperature in [City] be [condition] on [Date]?"
        import re
        question_lower = s.question.lower()
        
        # Extract highest/lowest
        temp_type = "highest" if "highest" in question_lower else "lowest"
        
        # Extract city (already in s.city)
        city_slug = s.city.lower().replace(" ", "-")
        
        # Extract date (e.g., "May 12, 2026" or "May 12 2026")
        # Look for month name followed by day and year
        date_match = re.search(r'(?:on\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+(?:,\s*\d{4})?', s.question, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(0).replace(",", "").replace(" ", "-").lower()
            # Remove "on" prefix if present
            date_str = date_str.replace("on-", "")
            # Add year if missing (questions often don't include year)
            if not re.search(r'\d{4}', date_str):
                date_str = f"{date_str}-{datetime.now().year}"
        else:
            date_str = "unknown"
        
        # Build URL
        url = f"https://polymarket.com/event/{temp_type}-temperature-in-{city_slug}-on-{date_str}"
        # Add temperature bracket for clarity
        temp_bracket = f"{s.temp_low_c}°C" if s.temp_low_c == s.temp_high_c else f"{s.temp_low_c}-{s.temp_high_c}°C"
        lines.append(f"{s.city} {temp_bracket} | {s.edge_pct:.1f}% | {s.action}\n{url}")
    pf = portfolio.get_summary()
    lines.append(f"\nPortfolio: ${pf['cash']:.0f} cash | {pf['open_positions']} open | ${pf['total_exposure']:.0f} exposure")
    lines.append(f"\nNext scan in {config.get('scanner', {}).get('interval_minutes', 30)} min")
    await _telegram_alert("\n".join(lines))


async def _telegram_alert(message: str):
    """Send a Telegram message. Silently skips if credentials are not set."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        logger.debug("Telegram: no credentials, skipping")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{TELEGRAM_API}/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message},
            )
            if resp.status_code == 200:
                logger.info("Telegram alert sent")
            else:
                logger.warning(f"Telegram API returned {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")


def _log_signal(signal, market, forecast):
    """Append one prediction row to data/signals.jsonl for later scoring."""
    row = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "market_id": signal.market_id,
        "condition_id": signal.condition_id,
        "slug": market.slug,
        "city": signal.city,
        "question": signal.question,
        "temp_type": market.temp_type,
        "bracket_type": market.bracket_type,
        "temp_low_c": market.temp_low_c,
        "temp_high_c": market.temp_high_c,
        "our_prob": signal.our_probability,
        "google_prob": signal.google_prob,
        "ensemble_prob": signal.ensemble_prob,
        "market_prob": signal.market_probability,
        "edge_pct": signal.edge_pct,
        "action": signal.action,
        "token_id": signal.token_id,
        "price": signal.price,
        "forecast_max_c": forecast.forecast_max_temp_c,
        "forecast_min_c": forecast.forecast_min_temp_c,
        "forecast_low_c": forecast.low_temp_c,
        "forecast_high_c": forecast.high_temp_c,
        "forecast_date": forecast.date,
        "liquidity": market.liquidity,
        "outcome": None,          # filled by resolve_signals.py after market closes
        "resolved_at": None,
    }
    SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SIGNALS_PATH, "a") as f:
        f.write(json.dumps(row) + "\n")


async def main():
    # Load config
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        logger.warning(f"Config not found at {config_path}. Using example config.")
        config_path = "config/config.example.yaml"

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    scanner_cfg = config.get("scanner", {})
    interval = scanner_cfg.get("interval_minutes", 15) * 60

    weather = WeatherClient()
    ensemble = EnsembleClient()
    scanner = MarketScanner(min_edge_pct=config.get("trading", {}).get("min_edge_pct", 10.0))
    portfolio = Portfolio(
        cash=1000.0,
        max_position_size=config.get("trading", {}).get("max_position_usdc", 20.0),
        max_total_exposure=config.get("risk_management", {}).get("max_total_exposure", 500.0),
        max_daily_loss=config.get("risk_management", {}).get("max_daily_loss", 100.0),
    )

    logger.info("🌦️ WeatherNext Pro started — scanning every {} minutes (ensemble enabled)", interval // 60)

    try:
        while True:
            start = datetime.now(timezone.utc)
            await run_scan_cycle(weather, ensemble, scanner, portfolio, config)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            wait = max(0, interval - elapsed)
            logger.info(f"Next scan in {wait/60:.1f} minutes")
            await asyncio.sleep(wait)
    except KeyboardInterrupt:
        logger.info("Shutting down WeatherNext Pro.")
    finally:
        await weather.close()
        await ensemble.close()
        await scanner.close()


if __name__ == "__main__":
    asyncio.run(main())
