# WeatherNext Pro 🌦️

**AI-powered weather intelligence for Polymarket temperature prediction markets.**

## Strategy
Use Google's WeatherNext 2 model (via Maps Weather API) to compute the true probabilistic
forecast for daily max temperature thresholds. Compare against Polymarket implied odds.
When our edge exceeds 10%, execute a trade.

## Architecture
```
Google Maps Weather API (WeatherNext 2 backend)
          ↓  hourly + daily probabilistic forecast
    services/weather_client.py
          ↓  P(max_temp > threshold)
    services/market_scanner.py
          ↓  compare vs Polymarket YES price
    services/signal_engine.py
          ↓  TradeSignal (if edge > threshold)
    services/polymarket_client.py
          ↓  CLOB limit order
       Polymarket
```

## Target Markets
- Shanghai daily max temp (liquidity ~$30K)
- Singapore daily max temp (liquidity ~$27K)
- Seoul daily max temp (liquidity ~$33K)
- London daily max temp (liquidity ~$10K)
- Hong Kong monthly precipitation (liquidity ~$4K)

## Setup
```bash
pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
# Fill in your API keys
python main.py
```

## Environment Variables
- `GMAPS_API_KEY` — Google Maps Platform Weather API key
- `POLY_PRIVATE_KEY` — Polymarket wallet private key (Polygon)
- `POLY_API_KEY` — Polymarket CLOB API key
