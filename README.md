# WeatherNext Pro — Polymarket Temperature Prediction

Automated system that finds mispriced temperature markets on Polymarket using Google's WeatherNext 2 forecasts as an informational edge.

## How It Works

```
Google WeatherNext 2 API → Probability Model → Polymarket Scanner → Edge Detection → Trade Signal
```

1. **Discover** active temperature bracket markets on Polymarket (auto-discovery via Gamma API)
2. **Fetch** weather forecasts for each city from Google Maps Weather API (WeatherNext 2 backend)
3. **Compute** our probability using a Gaussian CDF model over the forecast uncertainty range
4. **Compare** our probability vs. market implied probability (YES price)
5. **Signal** BUY_YES or BUY_NO when edge exceeds threshold (default: 10%)

## Quick Start

```bash
# Install dependencies
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Configure
cp .env.example .env         # Fill in your GMAPS_API_KEY

# Run scanner
python main.py
```

## Project Structure

```
main.py                      # Entry point — scan loop
config/config.yaml           # Configuration
services/
  weather_client.py          # Google Maps Weather API + Gaussian CDF probability model
  market_scanner.py          # Polymarket discovery + bracket parsing + signal logic
  risk_manager.py            # Position sizing, circuit breakers, loss limits
  scanner_runner.py          # Standalone scanner (one-shot or --loop)
cloud_run/                   # GCP Cloud Run service (Gemini AI reasoning)
find_markets.py              # Quick utility — search Polymarket for weather markets
inspect_markets.py           # Quick utility — inspect current temperature events
```

## Configuration

Edit `config/config.yaml`:

```yaml
scanner:
  interval_minutes: 15       # scan frequency

trading:
  paper_trading: true        # set false for live
  min_edge_pct: 10.0         # minimum edge to trade
  max_position_usdc: 20.0    # max per trade
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GMAPS_API_KEY` | Yes | Google Maps Weather API key |
| `GEMINI_API_KEY` | No | Gemini AI for narrative generation |
| `TELEGRAM_BOT_TOKEN` | No | Telegram alert bot |
| `POLY_API_KEY` | No | Polymarket CLOB (live trading only) |

## Status

- **Working**: Market discovery, weather forecasts, probability model, edge detection, paper trading
- **TODO**: Live CLOB execution (EIP-712 signing), Telegram 2FA confirmation, historical backtesting with real data
