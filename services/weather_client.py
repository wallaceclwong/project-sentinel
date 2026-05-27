"""
WeatherNext Pro — Weather Client
Fetches probabilistic forecasts from Google Maps Weather API (WeatherNext 2 backend).
Computes P(max_temp > threshold) from hourly forecast spread.
"""
import os
import httpx
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from loguru import logger


@dataclass
class DailyForecast:
    city: str
    date: str                        # "YYYY-MM-DD"
    forecast_max_temp_c: float       # best-estimate max temp for the day
    low_temp_c: float                # lower bound (uncertainty)
    high_temp_c: float               # upper bound (uncertainty)
    precip_prob: float               # probability of precipitation 0–1
    fetched_at: datetime = None
    # Min temp fields (for lowest-temperature markets)
    forecast_min_temp_c: float = None
    min_low_c: float = None
    min_high_c: float = None

    def _cdf(self, x: float) -> float:
        """P(max_temp <= x) — internal Gaussian CDF."""
        import math
        mean  = self.forecast_max_temp_c
        sigma = (self.high_temp_c - self.low_temp_c) / (2 * 1.645)
        if sigma <= 0:
            return 0.0 if mean > x else 1.0
        z = (x - mean) / (sigma * math.sqrt(2))
        return 0.5 * (1 + math.erf(z))

    def _cdf_min(self, x: float) -> float:
        """P(min_temp <= x) — Gaussian CDF for min temperature."""
        import math
        if self.forecast_min_temp_c is None:
            return 0.5
        mean = self.forecast_min_temp_c
        low = self.min_low_c if self.min_low_c is not None else mean - 2
        high = self.min_high_c if self.min_high_c is not None else mean + 2
        sigma = (high - low) / (2 * 1.645)
        if sigma <= 0:
            return 0.0 if mean > x else 1.0
        z = (x - mean) / (sigma * math.sqrt(2))
        return 0.5 * (1 + math.erf(z))

    def prob_exceeds(self, threshold_c: float) -> float:
        """P(max_temp > threshold) — for simple YES/NO markets."""
        return round(1.0 - self._cdf(threshold_c), 4)

    def prob_at_or_below(self, threshold_c: float) -> float:
        """P(max_temp <= threshold) — for lower-bound bracket markets."""
        return round(self._cdf(threshold_c), 4)

    def prob_in_bracket(self, low_c: float, high_c: float) -> float:
        """
        P(low_c <= max_temp < high_c) — for exact / range bracket markets.
        Each 1°C Polymarket bucket is treated as a half-open interval.
        E.g. bracket '10°C' → low=9.5, high=10.5
        """
        return round(max(0.0, self._cdf(high_c) - self._cdf(low_c)), 4)

    def prob_min_exceeds(self, threshold_c: float) -> float:
        """P(min_temp > threshold) — for lowest-temp 'or higher' markets."""
        return round(1.0 - self._cdf_min(threshold_c), 4)

    def prob_min_at_or_below(self, threshold_c: float) -> float:
        """P(min_temp <= threshold) — for lowest-temp 'or below' markets."""
        return round(self._cdf_min(threshold_c), 4)

    def prob_min_in_bracket(self, low_c: float, high_c: float) -> float:
        """P(low_c <= min_temp < high_c) — for lowest-temp exact/range markets."""
        return round(max(0.0, self._cdf_min(high_c) - self._cdf_min(low_c)), 4)


class WeatherClient:
    """
    Fetches weather forecasts from Google Maps Weather API.
    The API is powered by WeatherNext 2 — we get AI-quality forecasts
    without needing raw Zarr access.
    """
    BASE_URL = "https://weather.googleapis.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GMAPS_API_KEY")
        if not self.api_key:
            raise ValueError("GMAPS_API_KEY not set. See .env.example for setup instructions.")
        self._client = httpx.AsyncClient(timeout=10.0)

    async def get_daily_forecast(self, lat: float, lng: float, city: str, days: int = 1) -> Optional[DailyForecast]:
        """
        Fetch today's daily max temperature forecast for a location.
        Returns a DailyForecast with uncertainty bounds for probability computation.
        """
        url = f"{self.BASE_URL}/forecast/days:lookup"
        params = {
            "key": self.api_key,
            "location.latitude": lat,
            "location.longitude": lng,
            "days": days,
            "unitsSystem": "METRIC",
        }

        try:
            resp = await self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            day = data.get("forecastDays", [{}])[0]
            daytime = day.get("daytimeForecast", {})
            temp_info = day.get("maxTemperature", {})
            temp_range = day.get("temperatureRange", {})

            max_temp = temp_info.get("degrees", None)
            if max_temp is None:
                logger.warning(f"No max temp in forecast for {city}")
                return None

            low = temp_range.get("minTemperature", {}).get("degrees", max_temp - 2)
            high = temp_range.get("maxTemperature", {}).get("degrees", max_temp + 2)
            precip_prob = daytime.get("precipitationProbability", 0) / 100.0

            # Min temperature
            min_temp_info = day.get("minTemperature", {})
            min_temp = min_temp_info.get("degrees", None)
            min_low = None
            min_high = None
            if min_temp is not None:
                min_low = min_temp - 2
                min_high = min_temp + 2

            forecast = DailyForecast(
                city=city,
                date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                forecast_max_temp_c=float(max_temp),
                low_temp_c=float(low),
                high_temp_c=float(high),
                precip_prob=precip_prob,
                fetched_at=datetime.now(timezone.utc),
                forecast_min_temp_c=float(min_temp) if min_temp else None,
                min_low_c=float(min_low) if min_low else None,
                min_high_c=float(min_high) if min_high else None,
            )
            logger.info(f"{city}: max={max_temp}°C range=[{low}, {high}] min={min_temp}°C precip={precip_prob:.0%}")
            return forecast

        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API error for {city}: {e.response.status_code} — {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error fetching weather for {city}: {e}")
            return None

    async def close(self):
        await self._client.aclose()
