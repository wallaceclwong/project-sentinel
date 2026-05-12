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
    "sao paulo":  {"lat":-23.5505,  "lng": -46.6333, "display": "Sao Paulo"},
    "buenos aires":{"lat":-34.6037, "lng": -58.3816, "display": "Buenos Aires"},
    "toronto":    {"lat": 43.6510,  "lng": -79.3470, "display": "Toronto"},
    "seattle":    {"lat": 47.6062,  "lng":-122.3321, "display": "Seattle"},
    "dallas":     {"lat": 32.7767,  "lng": -96.7970, "display": "Dallas"},
    "nyc":        {"lat": 40.7128,  "lng": -74.0060, "display": "NYC"},
}


@dataclass
class MarketInfo:
    market_id: str
    condition_id: str
    question: str
    city: str
    city_key: str                  # lowercase key for CITY_COORDS lookup
    bracket_type: str              # "below", "exact", "range", "above"
    temp_low_c: float              # lower bound
    temp_high_c: float             # upper bound
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
    Discovers and scans Polymarket temperature markets using the events API.
    """
    GAMMA_URL = "https://gamma-api.polymarket.com"

    def __init__(self, min_edge_pct: float = 10.0, request_delay: float = 0.3):
        self.min_edge_pct  = min_edge_pct
        self.request_delay = request_delay        # seconds between API calls
        self._client = httpx.AsyncClient(timeout=15.0)

    # ── Market discovery ─────────────────────────────────────────────────────

    async def discover_temp_markets(self) -> list[MarketInfo]:
        """
        Auto-discover all currently active temperature/highest-temp markets
        on Polymarket by querying events with tag_slug=temperature.
        """
        raw_markets: list[dict] = []

        await asyncio.sleep(self.request_delay)
        try:
            resp = await self._client.get(
                f"{self.GAMMA_URL}/events",
                params={"tag_slug": "temperature", "active": "true", "closed": "false", "limit": 100}
            )
            resp.raise_for_status()
            events = resp.json()
            for event in events:
                for m in event.get("markets", []):
                    # Filter out closed/archived markets and resolved prices
                    if not m.get("closed") and not m.get("archived"):
                        prices = m.get("outcomePrices", "[]")
                        try:
                            p = eval(prices)
                            if float(p[0]) not in (0.0, 1.0):
                                raw_markets.append(m)
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Discovery query failed: {e}")

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

        bracket_info = self._parse_bracket(question)
        if not bracket_info:
            return None

        bracket_type, temp_low_c, temp_high_c = bracket_info

        city_key, city_display = self._extract_city(question, m.get("slug", ""))
        if city_key is None:
            return None

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
            bracket_type   = bracket_type,
            temp_low_c     = temp_low_c,
            temp_high_c    = temp_high_c,
            yes_token_id   = token_ids[0] if token_ids else "",
            no_token_id    = token_ids[1] if len(token_ids) > 1 else "",
            yes_price      = prices[0],
            liquidity      = float(m.get("liquidity", 0)),
            slug           = m.get("slug", ""),
        )

    def _parse_bracket(self, question: str) -> Optional[tuple[str, float, float]]:
        """
        Parse bracket markets for their temperature bounds in Celsius.
        Returns (bracket_type, low_c, high_c)
        """
        q = question.lower()
        
        # 1. "or below" (e.g. "9°C or below")
        m_below = re.search(r'(\d+(?:\.\d+)?)\s*°?\s*([cf])\s+or\s+below', q)
        if m_below:
            val, unit = float(m_below.group(1)), m_below.group(2)
            c_val = val if unit == 'c' else (val - 32) * 5/9
            offset = 0.5 if unit == 'c' else (0.5 * 5/9)
            return ("below", -999.0, round(c_val + offset, 2))

        # 2. "or higher" / "or above"
        m_above = re.search(r'(\d+(?:\.\d+)?)\s*°?\s*([cf])\s+or\s+(?:higher|above)', q)
        if m_above:
            val, unit = float(m_above.group(1)), m_above.group(2)
            c_val = val if unit == 'c' else (val - 32) * 5/9
            offset = 0.5 if unit == 'c' else (0.5 * 5/9)
            return ("above", round(c_val - offset, 2), 999.0)

        # 3. "between X-Y" (e.g. "between 44-45°F")
        m_between = re.search(r'between\s+(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*°?\s*([cf])', q)
        if m_between:
            low, high, unit = float(m_between.group(1)), float(m_between.group(2)), m_between.group(3)
            low_c = low if unit == 'c' else (low - 32) * 5/9
            high_c = high if unit == 'c' else (high - 32) * 5/9
            offset = 0.5 if unit == 'c' else (0.5 * 5/9)
            return ("range", round(low_c - offset, 2), round(high_c + offset, 2))

        # 4. exact "be 10°C"
        m_exact = re.search(r'be\s+(\d+(?:\.\d+)?)\s*°?\s*([cf])', q)
        if m_exact:
            val, unit = float(m_exact.group(1)), m_exact.group(2)
            c_val = val if unit == 'c' else (val - 32) * 5/9
            offset = 0.5 if unit == 'c' else (0.5 * 5/9)
            return ("exact", round(c_val - offset, 2), round(c_val + offset, 2))

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
          - Compute P(bracket) from WeatherNext 2 forecast
          - Compare to market YES price
          - If |edge| > threshold → BUY_YES or BUY_NO
        """
        min_edge  = min_edge_pct or self.min_edge_pct
        
        # Calculate our probability based on the bracket type
        if market.bracket_type == "below":
            our_prob = forecast.prob_at_or_below(market.temp_high_c)
        elif market.bracket_type == "above":
            our_prob = forecast.prob_exceeds(market.temp_low_c)
        else: # "exact" or "range"
            our_prob = forecast.prob_in_bracket(market.temp_low_c, market.temp_high_c)
            
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
