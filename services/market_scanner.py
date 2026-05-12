"""
WeatherNext Pro — Polymarket Market Scanner
Scans target markets, fetches current YES prices, compares vs our weather forecast probability.
Generates TradeSignals when edge exceeds threshold.
"""
import asyncio
import re
from dataclasses import dataclass
from typing import Optional
import httpx
from loguru import logger

from services.weather_client import DailyForecast


# ── Known city → lat/lng mapping ────────────────────────────────────────────
CITY_COORDS: dict[str, dict] = {
    "london":     {"lat": 51.5074,  "lng": -0.1278,  "display": "London"},
    "singapore":  {"lat":  1.3521,  "lng": 103.8198, "display": "Singapore"},
    "seoul":      {"lat": 37.5665,  "lng": 126.9780, "display": "Seoul"},
    "shanghai":   {"lat": 31.2304,  "lng": 121.4737, "display": "Shanghai"},
    "paris":      {"lat": 48.8566,  "lng":  2.3522,  "display": "Paris"},
    "tel aviv":   {"lat": 32.0853,  "lng": 34.7818,  "display": "Tel Aviv"},
    "tel-aviv":   {"lat": 32.0853,  "lng": 34.7818,  "display": "Tel Aviv"},
    "atlanta":    {"lat": 33.7490,  "lng": -84.3880, "display": "Atlanta"},
    "wellington": {"lat":-41.2866,  "lng": 174.7756, "display": "Wellington"},
    "tokyo":      {"lat": 35.6762,  "lng": 139.6503, "display": "Tokyo"},
    "new york":   {"lat": 40.7128,  "lng": -74.0060, "display": "New York"},
    "los angeles":{"lat": 34.0522,  "lng":-118.2437, "display": "Los Angeles"},
    "miami":      {"lat": 25.7617,  "lng": -80.1918, "display": "Miami"},
    "chicago":    {"lat": 41.8781,  "lng": -87.6298, "display": "Chicago"},
    "sydney":     {"lat":-33.8688,  "lng": 151.2093, "display": "Sydney"},
    "dubai":      {"lat": 25.2048,  "lng": 55.2708,  "display": "Dubai"},
    "berlin":     {"lat": 52.5200,  "lng": 13.4050,  "display": "Berlin"},
    "amsterdam":  {"lat": 52.3676,  "lng":  4.9041,  "display": "Amsterdam"},
    "istanbul":   {"lat": 41.0082,  "lng": 28.9784,  "display": "Istanbul"},
    "bangkok":    {"lat": 13.7563,  "lng": 100.5018, "display": "Bangkok"},
}


@dataclass
class MarketInfo:
    market_id: str
    condition_id: str
    question: str
    city: str
    city_key: str                  # lowercase key for CITY_COORDS lookup
    temp_threshold_c: float        # The threshold the market is asking about
    yes_token_id: str
    no_token_id: str
    yes_price: float               # Current market price (= implied probability)
    liquidity: float               # Total liquidity in USDC
    slug: str = ""


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
    Discovers and scans Polymarket temperature markets.
    Supports both direct slug lookup and broad auto-discovery.
    """
    GAMMA_URL = "https://gamma-api.polymarket.com"
    CLOB_URL  = "https://clob.polymarket.com"

    # Search terms that reliably surface temp markets (not sports teams)
    _DISCOVERY_QUERIES = ["highest temp", "highest temperature", "max temp"]

    def __init__(self, min_edge_pct: float = 10.0, request_delay: float = 0.3):
        self.min_edge_pct  = min_edge_pct
        self.request_delay = request_delay        # seconds between API calls
        self._client = httpx.AsyncClient(timeout=15.0)

    # ── Market discovery ─────────────────────────────────────────────────────

    async def discover_temp_markets(self) -> list[MarketInfo]:
        """
        Auto-discover all currently active temperature/highest-temp markets
        on Polymarket, regardless of slug. Returns only markets we can
        match to a known city with coordinates.
        """
        seen_ids: set[str] = set()
        raw_markets: list[dict] = []

        for query in self._DISCOVERY_QUERIES:
            await asyncio.sleep(self.request_delay)
            try:
                resp = await self._client.get(
                    f"{self.GAMMA_URL}/markets",
                    params={"active": "true", "closed": "false",
                            "limit": 100, "search": query}
                )
                resp.raise_for_status()
                for m in resp.json():
                    if m["id"] not in seen_ids:
                        seen_ids.add(m["id"])
                        raw_markets.append(m)
            except Exception as e:
                logger.warning(f"Discovery query '{query}' failed: {e}")

        logger.info(f"Discovery: found {len(raw_markets)} candidate markets")

        # Parse each into MarketInfo, drop ones we can't use
        results: list[MarketInfo] = []
        for m in raw_markets:
            mi = self._parse_raw_market(m)
            if mi:
                results.append(mi)

        logger.info(f"Discovery: {len(results)} usable temp markets after parsing")
        return results

    # ── Single-slug lookup (kept for backwards compatibility) ────────────────

    async def fetch_market(self, slug: str) -> Optional[MarketInfo]:
        """Fetch one market by exact slug."""
        await asyncio.sleep(self.request_delay)
        try:
            resp = await self._client.get(
                f"{self.GAMMA_URL}/markets",
                params={"slug": slug, "active": "true", "closed": "false"}
            )
            resp.raise_for_status()
            markets = resp.json()
            if not markets:
                logger.debug(f"No active market for slug: {slug}")
                return None
            return self._parse_raw_market(markets[0])
        except Exception as e:
            logger.warning(f"Failed to fetch market {slug}: {e}")
            return None

    # ── Parsing helpers ──────────────────────────────────────────────────────

    def _parse_raw_market(self, m: dict) -> Optional[MarketInfo]:
        """
        Parse a raw Gamma API market dict into MarketInfo.
        Returns None if we can't extract threshold or city.
        """
        question = m.get("question", "")

        # Must have a parseable temperature threshold
        threshold = self._parse_threshold(question)
        if threshold is None:
            return None

        # Must match a known city
        city_key, city_display = self._extract_city(question, m.get("slug", ""))
        if city_key is None:
            return None

        # Parse prices and token IDs (stored as JSON strings in Gamma API)
        try:
            prices    = [float(p) for p in eval(m.get("outcomePrices", "[0.5, 0.5]"))]
            token_ids = eval(m.get("clobTokenIds", "['', '']"))
        except Exception:
            prices    = [0.5, 0.5]
            token_ids = ["", ""]

        return MarketInfo(
            market_id      = m["id"],
            condition_id   = m.get("conditionId", ""),
            question       = question,
            city           = city_display,
            city_key       = city_key,
            temp_threshold_c = threshold,
            yes_token_id   = token_ids[0] if token_ids else "",
            no_token_id    = token_ids[1] if len(token_ids) > 1 else "",
            yes_price      = prices[0],
            liquidity      = float(m.get("liquidity", 0)),
            slug           = m.get("slug", ""),
        )

    def _parse_threshold(self, question: str) -> Optional[float]:
        """
        Extract temperature threshold from question text.
          "Highest temp in London at least 18°C?" → 18.0
          "Max temp Seoul 65°F or higher?"        → 18.3
        """
        # Celsius: "18°C", "18 C", "18C"
        m = re.search(r'(\d+(?:\.\d+)?)\s*°?\s*C\b', question, re.IGNORECASE)
        if m:
            return float(m.group(1))
        # Fahrenheit → convert
        m = re.search(r'(\d+(?:\.\d+)?)\s*°?\s*F\b', question, re.IGNORECASE)
        if m:
            return round((float(m.group(1)) - 32) * 5 / 9, 1)
        return None

    def _extract_city(self, question: str, slug: str) -> tuple[Optional[str], str]:
        """
        Match question text or slug against CITY_COORDS.
        Returns (city_key, display_name) or (None, "").
        """
        text = (question + " " + slug).lower()
        for key, info in CITY_COORDS.items():
            if key in text:
                return key, info["display"]
        return None, ""

    # ── Signal computation ───────────────────────────────────────────────────

    def compute_signal(
        self,
        market: MarketInfo,
        forecast: DailyForecast,
        min_edge_pct: Optional[float] = None,
    ) -> TradeSignal:
        """
        Core signal logic:
          - Compute P(max_temp > threshold) from WeatherNext 2 forecast
          - Compare to market YES price
          - If |edge| > threshold → BUY_YES or BUY_NO
        """
        min_edge  = min_edge_pct or self.min_edge_pct
        our_prob  = forecast.prob_exceeds(market.temp_threshold_c)
        mkt_prob  = market.yes_price
        edge_pct  = abs(our_prob - mkt_prob) * 100

        if edge_pct < min_edge:
            return TradeSignal(
                market_id        = market.market_id,
                condition_id     = market.condition_id,
                city             = market.city,
                question         = market.question,
                our_probability  = our_prob,
                market_probability = mkt_prob,
                edge_pct         = edge_pct,
                action           = "SKIP",
                token_id         = "",
                price            = 0.0,
                reason           = f"Edge {edge_pct:.1f}% < minimum {min_edge:.0f}%",
            )

        if our_prob > mkt_prob:
            action   = "BUY_YES"
            token_id = market.yes_token_id
            price    = min(mkt_prob + 0.01, 0.97)
            reason   = (
                f"Our P={our_prob:.1%} vs market P={mkt_prob:.1%}. "
                f"Market UNDERPRICES YES by {edge_pct:.1f}%."
            )
        else:
            action   = "BUY_NO"
            token_id = market.no_token_id
            price    = min((1 - mkt_prob) + 0.01, 0.97)
            reason   = (
                f"Our P={our_prob:.1%} vs market P={mkt_prob:.1%}. "
                f"Market OVERPRICES YES by {edge_pct:.1f}%."
            )

        logger.info(
            f"SIGNAL [{market.city}] {action} | edge={edge_pct:.1f}% | {reason}"
        )
        return TradeSignal(
            market_id        = market.market_id,
            condition_id     = market.condition_id,
            city             = market.city,
            question         = market.question,
            our_probability  = our_prob,
            market_probability = mkt_prob,
            edge_pct         = edge_pct,
            action           = action,
            token_id         = token_id,
            price            = price,
            reason           = reason,
        )

    async def close(self):
        await self._client.aclose()
