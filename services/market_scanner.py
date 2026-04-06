"""
WeatherNext Pro — Polymarket Market Scanner
Scans target markets, fetches current YES prices, compares vs our weather forecast probability.
Generates TradeSignals when edge exceeds threshold.
"""
import httpx
from dataclasses import dataclass
from typing import Optional
from loguru import logger

from services.weather_client import DailyForecast


@dataclass
class MarketInfo:
    market_id: str
    condition_id: str
    question: str
    city: str
    temp_threshold_c: float        # The threshold the market is asking about
    yes_token_id: str
    no_token_id: str
    yes_price: float               # Current market price (= implied probability)
    liquidity: float               # Total liquidity in USDC


@dataclass
class TradeSignal:
    market_id: str
    condition_id: str
    city: str
    question: str
    our_probability: float         # Our WeatherNext 2 derived probability
    market_probability: float      # Market's implied probability (YES price)
    edge_pct: float                # Absolute difference (our edge)
    action: str                    # "BUY_YES", "BUY_NO", or "SKIP"
    token_id: str
    price: float
    reason: str


class MarketScanner:
    """
    Polls the Polymarket Gamma API for weather/temperature markets,
    extracts the temperature threshold from the question text,
    and computes edge against our weather forecast.
    """
    GAMMA_URL = "https://gamma-api.polymarket.com"

    # Known daily temperature markets — updated manually or via auto-discovery
    WATCHED_SLUGS = [
        "highest-temp-shanghai",
        "highest-temp-singapore",
        "highest-temp-seoul",
        "highest-temp-london",
        "highest-temp-tel-aviv",
        "highest-temp-paris",
        "highest-temp-wellington",
        "highest-temp-atlanta",
    ]

    def __init__(self, min_edge_pct: float = 10.0):
        self.min_edge_pct = min_edge_pct
        self._client = httpx.AsyncClient(timeout=15.0)

    async def fetch_market(self, slug: str) -> Optional[MarketInfo]:
        """Fetch market details and current price from Gamma API."""
        try:
            resp = await self._client.get(
                f"{self.GAMMA_URL}/markets",
                params={"slug": slug, "active": "true", "closed": "false"}
            )
            resp.raise_for_status()
            markets = resp.json()
            if not markets:
                logger.debug(f"No active market found for slug: {slug}")
                return None

            m = markets[0]
            prices = [float(p) for p in eval(m.get("outcomePrices", "[0.5, 0.5]"))]
            token_ids = eval(m.get("clobTokenIds", "['', '']"))

            # Extract temperature threshold from question text (e.g. "at least 12°C")
            threshold = self._parse_threshold(m.get("question", ""))
            if threshold is None:
                logger.debug(f"Could not parse threshold from: {m.get('question')}")
                return None

            city = self._city_from_slug(slug)
            return MarketInfo(
                market_id=m["id"],
                condition_id=m["conditionId"],
                question=m["question"],
                city=city,
                temp_threshold_c=threshold,
                yes_token_id=token_ids[0],
                no_token_id=token_ids[1],
                yes_price=prices[0],
                liquidity=float(m.get("liquidity", 0)),
            )
        except Exception as e:
            logger.warning(f"Failed to fetch market {slug}: {e}")
            return None

    def _parse_threshold(self, question: str) -> Optional[float]:
        """
        Extract the temperature threshold from market question text.
        Examples:
          "Highest temp in Shanghai at least 12°C on Mar 17?" -> 12.0
          "Highest temp in Seoul (54°F or higher)?" -> 12.2 (converted)
        """
        import re
        # Match Celsius patterns: "12°C", "12 °C", "12C"
        match = re.search(r'(\d+(?:\.\d+)?)\s*°?\s*C\b', question, re.IGNORECASE)
        if match:
            return float(match.group(1))
        # Match Fahrenheit patterns and convert
        match_f = re.search(r'(\d+(?:\.\d+)?)\s*°?\s*F\b', question, re.IGNORECASE)
        if match_f:
            f = float(match_f.group(1))
            return round((f - 32) * 5 / 9, 1)
        return None

    def _city_from_slug(self, slug: str) -> str:
        """Extract city name from market slug."""
        city_map = {
            "shanghai": "Shanghai", "singapore": "Singapore",
            "seoul": "Seoul", "london": "London",
            "tel-aviv": "Tel Aviv", "paris": "Paris",
            "wellington": "Wellington", "atlanta": "Atlanta",
        }
        for key, name in city_map.items():
            if key in slug.lower():
                return name
        return slug.replace("-", " ").title()

    def compute_signal(
        self,
        market: MarketInfo,
        forecast: DailyForecast,
        min_edge_pct: Optional[float] = None
    ) -> TradeSignal:
        """
        Core signal logic:
          - Compute our P(max_temp > threshold) from the forecast
          - Compare to market YES price
          - If edge > threshold → generate BUY_YES or BUY_NO signal
        """
        threshold = market.temp_threshold_c
        min_edge = min_edge_pct or self.min_edge_pct

        our_prob = forecast.prob_exceeds(threshold)
        market_prob = market.yes_price
        edge_pct = abs(our_prob - market_prob) * 100

        if edge_pct < min_edge:
            return TradeSignal(
                market_id=market.market_id,
                condition_id=market.condition_id,
                city=market.city,
                question=market.question,
                our_probability=our_prob,
                market_probability=market_prob,
                edge_pct=edge_pct,
                action="SKIP",
                token_id="",
                price=0.0,
                reason=f"Edge {edge_pct:.1f}% < minimum {min_edge}%",
            )

        if our_prob > market_prob:
            # Market underprices YES — BUY YES
            action = "BUY_YES"
            token_id = market.yes_token_id
            price = market_prob + 0.01  # Slightly above current to ensure fill
            reason = (
                f"Our P={our_prob:.1%} vs market P={market_prob:.1%}. "
                f"Market underprices YES by {edge_pct:.1f}%."
            )
        else:
            # Market overprices YES — BUY NO (= sell YES)
            action = "BUY_NO"
            token_id = market.no_token_id
            price = (1 - market_prob) + 0.01
            reason = (
                f"Our P={our_prob:.1%} vs market P={market_prob:.1%}. "
                f"Market overprices YES by {edge_pct:.1f}%."
            )

        logger.info(f"🎯 SIGNAL [{market.city}] {action} | edge={edge_pct:.1f}% | {reason}")
        return TradeSignal(
            market_id=market.market_id,
            condition_id=market.condition_id,
            city=market.city,
            question=market.question,
            our_probability=our_prob,
            market_probability=market_prob,
            edge_pct=edge_pct,
            action=action,
            token_id=token_id,
            price=min(price, 0.97),  # Cap at 97c to avoid obvious mispricing
            reason=reason,
        )

    async def close(self):
        await self._client.aclose()
