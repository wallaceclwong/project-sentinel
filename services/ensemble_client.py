"""
WeatherNext Pro — Open-Meteo Ensemble Client
Fetches 51-member ensemble forecasts for more accurate probability estimates.
Uses multiple models: ICON (DWD), GFS (NOAA), ECMWF IFS.

Free, no API key required. ~10,000 calls/day.
"""
import httpx
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from loguru import logger


@dataclass
class EnsembleForecast:
    city: str
    date: str
    max_temps: list[float] = field(default_factory=list)  # 51 ensemble members max temp
    min_temps: list[float] = field(default_factory=list)  # 51 ensemble members min temp
    fetched_at: datetime = None

    @property
    def n_members(self) -> int:
        return len(self.max_temps)

    @property
    def mean_max(self) -> float:
        return sum(self.max_temps) / len(self.max_temps) if self.max_temps else 0

    @property
    def mean_min(self) -> float:
        return sum(self.min_temps) / len(self.min_temps) if self.min_temps else 0

    def prob_max_exceeds(self, threshold_c: float) -> float:
        """P(max_temp > threshold) — fraction of ensemble members above."""
        if not self.max_temps:
            return 0.5
        count = sum(1 for t in self.max_temps if t > threshold_c)
        return round(count / len(self.max_temps), 4)

    def prob_max_at_or_below(self, threshold_c: float) -> float:
        """P(max_temp <= threshold)."""
        return round(1.0 - self.prob_max_exceeds(threshold_c), 4)

    def prob_max_in_bracket(self, low_c: float, high_c: float) -> float:
        """P(low_c <= max_temp < high_c) — fraction in bracket."""
        if not self.max_temps:
            return 0.5
        count = sum(1 for t in self.max_temps if low_c <= t < high_c)
        return round(count / len(self.max_temps), 4)

    def prob_min_exceeds(self, threshold_c: float) -> float:
        """P(min_temp > threshold)."""
        if not self.min_temps:
            return 0.5
        count = sum(1 for t in self.min_temps if t > threshold_c)
        return round(count / len(self.min_temps), 4)

    def prob_min_at_or_below(self, threshold_c: float) -> float:
        """P(min_temp <= threshold)."""
        return round(1.0 - self.prob_min_exceeds(threshold_c), 4)

    def prob_min_in_bracket(self, low_c: float, high_c: float) -> float:
        """P(low_c <= min_temp < high_c)."""
        if not self.min_temps:
            return 0.5
        count = sum(1 for t in self.min_temps if low_c <= t < high_c)
        return round(count / len(self.min_temps), 4)


class EnsembleClient:
    """
    Fetches ensemble forecasts from Open-Meteo (free, no key needed).
    Uses multiple models for robustness.
    """
    BASE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"

    # ICON-EPS: 40 ensemble members with daily aggregation support
    MODELS = ["icon_seamless_eps"]

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=15.0)

    async def get_ensemble_forecast(
        self, lat: float, lng: float, city: str, forecast_days: int = 2
    ) -> Optional[EnsembleForecast]:
        """
        Fetch ensemble forecast. Returns combined members from multiple models.
        For a 1-day forecast we look at today (index 0) in the daily aggregation.
        """
        all_max_temps: list[float] = []
        all_min_temps: list[float] = []

        for model in self.MODELS:
            try:
                resp = await self._client.get(
                    self.BASE_URL,
                    params={
                        "latitude": lat,
                        "longitude": lng,
                        "daily": "temperature_2m_max,temperature_2m_min",
                        "models": model,
                        "forecast_days": forecast_days,
                        "timezone": "UTC",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                daily = data.get("daily", {})

                # Ensemble members come as temperature_2m_max_member01, etc.
                # Or as arrays in the daily block — depends on model response format
                # The API returns all members for the requested day
                max_keys = [k for k in daily if k.startswith("temperature_2m_max")]
                min_keys = [k for k in daily if k.startswith("temperature_2m_min")]

                if max_keys:
                    for key in max_keys:
                        values = daily[key]
                        if isinstance(values, list) and len(values) > 0 and values[0] is not None:
                            all_max_temps.append(float(values[0]))

                if min_keys:
                    for key in min_keys:
                        values = daily[key]
                        if isinstance(values, list) and len(values) > 0 and values[0] is not None:
                            all_min_temps.append(float(values[0]))

            except Exception as e:
                logger.debug(f"Ensemble {model} failed for {city}: {e}")
                continue

        if not all_max_temps:
            logger.debug(f"No ensemble data for {city}")
            return None

        forecast = EnsembleForecast(
            city=city,
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            max_temps=all_max_temps,
            min_temps=all_min_temps,
            fetched_at=datetime.now(timezone.utc),
        )
        logger.info(
            f"Ensemble {city}: {forecast.n_members} members | "
            f"max={forecast.mean_max:.1f}°C [{min(all_max_temps):.1f}, {max(all_max_temps):.1f}] | "
            f"min={forecast.mean_min:.1f}°C"
        )
        return forecast

    async def close(self):
        await self._client.aclose()
