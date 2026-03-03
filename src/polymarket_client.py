#!/usr/bin/env python3
"""
PROJECT SENTINEL - Polymarket CLOB API Client
Phase 4: Market data and order execution via Polymarket's Central Limit Order Book
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

CLOB_BASE_URL = "https://clob.polymarket.com"
GAMMA_BASE_URL = "https://gamma-api.polymarket.com"

@dataclass
class MarketInfo:
    """Polymarket market information"""
    condition_id: str
    question: str
    tokens: List[Dict]
    active: bool
    closed: bool
    volume: float
    liquidity: float
    end_date: Optional[str] = None

@dataclass 
class OrderBookEntry:
    """Order book price level"""
    price: float
    size: float

@dataclass
class OrderBook:
    """Full order book for a token"""
    token_id: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    best_bid: float
    best_ask: float
    spread: float
    mid_price: float

@dataclass
class TradeOrder:
    """Trade order to be placed"""
    token_id: str
    side: str  # BUY or SELL
    price: float
    size: float
    order_type: str = "limit"  # limit or market
    timestamp: str = ""

@dataclass
class TradeResult:
    """Result of a trade execution"""
    order_id: str
    status: str  # filled, partial, pending, rejected
    filled_size: float
    filled_price: float
    fee: float
    timestamp: str


class PolymarketClient:
    """Client for Polymarket CLOB API - market data and order execution"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.base_url = CLOB_BASE_URL
        self.gamma_url = GAMMA_BASE_URL
        self.api_key = api_key
        self.api_secret = api_secret
        self.session: Optional[aiohttp.ClientSession] = None
        self.weather_market_cache: Dict[str, MarketInfo] = {}
        self.cache_ttl = 300  # 5 minute cache
        self.last_cache_update = 0
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"Content-Type": "application/json"}
            )
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    # ==================== MARKET DATA ====================
    
    async def get_markets(self, next_cursor: str = "") -> Dict:
        """Fetch available markets from CLOB"""
        session = await self._get_session()
        params = {}
        if next_cursor:
            params["next_cursor"] = next_cursor
            
        try:
            async with session.get(f"{self.base_url}/markets", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"Failed to fetch markets: {resp.status}")
                    return {"data": [], "next_cursor": ""}
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return {"data": [], "next_cursor": ""}
    
    async def search_weather_markets(self) -> List[MarketInfo]:
        """Search for weather-related markets on Polymarket"""
        session = await self._get_session()
        
        # Check cache
        if time.time() - self.last_cache_update < self.cache_ttl and self.weather_market_cache:
            logger.info(f"Returning {len(self.weather_market_cache)} cached weather markets")
            return list(self.weather_market_cache.values())
        
        weather_keywords = [
            "weather", "temperature", "hurricane", "storm", "tornado",
            "flood", "drought", "heat wave", "cold", "snow", "rainfall",
            "climate", "el nino", "la nina", "celsius", "fahrenheit"
        ]
        
        weather_markets = []
        
        try:
            # Search via Gamma API for event discovery
            async with session.get(
                f"{self.gamma_url}/events",
                params={"limit": 100, "active": True}
            ) as resp:
                if resp.status == 200:
                    events = await resp.json()
                    for event in events:
                        title = event.get("title", "").lower()
                        description = event.get("description", "").lower()
                        
                        if any(kw in title or kw in description for kw in weather_keywords):
                            for market in event.get("markets", []):
                                market_info = MarketInfo(
                                    condition_id=market.get("conditionId", ""),
                                    question=market.get("question", ""),
                                    tokens=market.get("clobTokenIds", []),
                                    active=market.get("active", False),
                                    closed=market.get("closed", False),
                                    volume=float(market.get("volume", 0)),
                                    liquidity=float(market.get("liquidity", 0)),
                                    end_date=market.get("endDate")
                                )
                                weather_markets.append(market_info)
                                self.weather_market_cache[market_info.condition_id] = market_info
                else:
                    logger.warning(f"Gamma API returned {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error searching weather markets: {e}")
        
        self.last_cache_update = time.time()
        logger.info(f"Found {len(weather_markets)} weather-related markets")
        return weather_markets
    
    async def get_order_book(self, token_id: str) -> Optional[OrderBook]:
        """Fetch order book for a specific token"""
        session = await self._get_session()
        
        try:
            async with session.get(
                f"{self.base_url}/book",
                params={"token_id": token_id}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    bids = [OrderBookEntry(float(b["price"]), float(b["size"])) 
                            for b in data.get("bids", [])]
                    asks = [OrderBookEntry(float(a["price"]), float(a["size"])) 
                            for a in data.get("asks", [])]
                    
                    best_bid = bids[0].price if bids else 0.0
                    best_ask = asks[0].price if asks else 1.0
                    spread = best_ask - best_bid
                    mid_price = (best_bid + best_ask) / 2
                    
                    return OrderBook(
                        token_id=token_id,
                        bids=bids,
                        asks=asks,
                        best_bid=best_bid,
                        best_ask=best_ask,
                        spread=spread,
                        mid_price=mid_price
                    )
                else:
                    logger.error(f"Failed to fetch order book: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return None
    
    async def get_price(self, token_id: str, side: str = "BUY") -> Optional[float]:
        """Get current price for a token"""
        session = await self._get_session()
        
        try:
            async with session.get(
                f"{self.base_url}/price",
                params={"token_id": token_id, "side": side}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data.get("price", 0))
                return None
        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return None

    async def get_midpoint(self, token_id: str) -> Optional[float]:
        """Get midpoint price for a token"""
        session = await self._get_session()
        
        try:
            async with session.get(
                f"{self.base_url}/midpoint",
                params={"token_id": token_id}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data.get("mid", 0))
                return None
        except Exception as e:
            logger.error(f"Error fetching midpoint: {e}")
            return None

    # ==================== MARKET ANALYSIS ====================
    
    async def analyze_market(self, token_id: str) -> Dict[str, Any]:
        """Comprehensive market analysis for a token"""
        order_book = await self.get_order_book(token_id)
        
        if not order_book:
            return {"error": "Failed to fetch order book"}
        
        # Calculate liquidity metrics
        bid_depth = sum(b.size for b in order_book.bids[:5])
        ask_depth = sum(a.size for a in order_book.asks[:5])
        
        # Calculate imbalance
        total_depth = bid_depth + ask_depth
        imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0
        
        return {
            "token_id": token_id,
            "best_bid": order_book.best_bid,
            "best_ask": order_book.best_ask,
            "mid_price": order_book.mid_price,
            "spread": order_book.spread,
            "spread_pct": (order_book.spread / order_book.mid_price * 100) if order_book.mid_price > 0 else 0,
            "bid_depth_5": bid_depth,
            "ask_depth_5": ask_depth,
            "order_imbalance": imbalance,
            "liquidity_score": min(total_depth / 1000, 1.0),
            "tradeable": order_book.spread < 0.10 and total_depth > 100,
            "timestamp": datetime.now().isoformat()
        }

    # ==================== ORDER MANAGEMENT ====================
    
    async def create_order(self, order: TradeOrder) -> Optional[TradeResult]:
        """Create a new order on Polymarket CLOB
        
        NOTE: Requires API key, secret, and wallet signer for live trading.
        Currently implements paper trading simulation.
        """
        if not self.api_key:
            logger.info(f"PAPER TRADE: {order.side} {order.size} @ {order.price} on {order.token_id}")
            return TradeResult(
                order_id=f"paper_{int(time.time())}",
                status="simulated",
                filled_size=order.size,
                filled_price=order.price,
                fee=order.size * order.price * 0.002,  # 0.2% fee estimate
                timestamp=datetime.now().isoformat()
            )
        
        # Live trading implementation
        session = await self._get_session()
        
        try:
            payload = {
                "tokenID": order.token_id,
                "side": order.side,
                "price": str(order.price),
                "size": str(order.size),
                "type": order.order_type
            }
            
            headers = {
                "POLY-ADDRESS": self.api_key,
                "POLY-SIGNATURE": self._sign_order(payload),
                "POLY-TIMESTAMP": str(int(time.time())),
                "POLY-NONCE": str(int(time.time() * 1000))
            }
            
            async with session.post(
                f"{self.base_url}/order",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return TradeResult(
                        order_id=data.get("orderID", ""),
                        status=data.get("status", "pending"),
                        filled_size=float(data.get("filledSize", 0)),
                        filled_price=float(data.get("filledPrice", 0)),
                        fee=float(data.get("fee", 0)),
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    error = await resp.text()
                    logger.error(f"Order creation failed: {resp.status} - {error}")
                    return None
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return None
    
    def _sign_order(self, payload: Dict) -> str:
        """Sign order for authentication (placeholder for EIP-712 signing)"""
        # TODO: Implement proper EIP-712 signing with web3
        return "placeholder_signature"
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        if not self.api_key:
            logger.info(f"PAPER TRADE: Cancel order {order_id}")
            return True
            
        session = await self._get_session()
        try:
            async with session.delete(
                f"{self.base_url}/order/{order_id}",
                headers={"POLY-ADDRESS": self.api_key}
            ) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    async def get_open_orders(self) -> List[Dict]:
        """Get all open orders"""
        if not self.api_key:
            return []
            
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}/orders",
                headers={"POLY-ADDRESS": self.api_key}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    # ==================== PORTFOLIO ====================
    
    async def get_positions(self) -> List[Dict]:
        """Get current portfolio positions"""
        if not self.api_key:
            return []
            
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}/positions",
                headers={"POLY-ADDRESS": self.api_key}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []


async def test_polymarket_client():
    """Test the Polymarket client with public endpoints"""
    client = PolymarketClient()
    
    print("🔍 Searching for weather-related markets...")
    weather_markets = await client.search_weather_markets()
    print(f"Found {len(weather_markets)} weather markets")
    
    for market in weather_markets[:3]:
        print(f"\n📊 Market: {market.question}")
        print(f"   Volume: ${market.volume:,.2f}")
        print(f"   Liquidity: ${market.liquidity:,.2f}")
        print(f"   Active: {market.active}")
        
        if market.tokens:
            token_id = market.tokens[0] if isinstance(market.tokens[0], str) else market.tokens[0].get("token_id", "")
            if token_id:
                analysis = await client.analyze_market(token_id)
                print(f"   Mid Price: ${analysis.get('mid_price', 0):.4f}")
                print(f"   Spread: {analysis.get('spread_pct', 0):.2f}%")
                print(f"   Tradeable: {analysis.get('tradeable', False)}")
    
    # Test paper trading
    print("\n📝 Testing paper trade...")
    order = TradeOrder(
        token_id="test_token",
        side="BUY",
        price=0.55,
        size=100,
        timestamp=datetime.now().isoformat()
    )
    result = await client.create_order(order)
    if result:
        print(f"   Order ID: {result.order_id}")
        print(f"   Status: {result.status}")
        print(f"   Filled: {result.filled_size} @ ${result.filled_price}")
        print(f"   Fee: ${result.fee:.4f}")
    
    await client.close()
    print("\n✅ Polymarket client test complete")


if __name__ == "__main__":
    asyncio.run(test_polymarket_client())
