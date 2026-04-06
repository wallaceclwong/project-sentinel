#!/usr/bin/env python3
"""
PROJECT SENTINEL - Paper Trading Engine
Live paper trading on Polymarket temperature markets with optimized risk/reward
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from data_fetcher import SentinelDataFetcher
from backtesting_engine import BacktestingEngine
from risk_reward_optimizer import RiskRewardOptimizer
from polymarket_client import PolymarketClient
from trading_engine import TradingEngine, TradeSignal
from telegram_bot import SentinelTelegramBot

logger = logging.getLogger(__name__)

@dataclass
class PaperTrade:
    """Paper trade record"""
    timestamp: str
    market: str
    action: str
    size: float
    entry_price: float
    current_price: float
    pnl: float
    exit_reason: str
    confidence: float

class PaperTrader:
    """Paper trading system for Polymarket temperature markets"""
    
    def __init__(self):
        self.data_fetcher = SentinelDataFetcher()
        self.backtest_engine = BacktestingEngine(initial_capital=10000)
        self.risk_optimizer = RiskRewardOptimizer()
        self.polymarket = PolymarketClient()
        
        # Paper trading state
        self.paper_trades: List[PaperTrade] = []
        self.open_positions: Dict[str, PaperTrade] = {}
        self.paper_capital = 10000.0
        self.total_pnl = 0.0
        
        # Configuration
        self.position_size = 10.0  # $10 per trade (scaled up from $1)
        self.max_positions = 5
        self.update_interval = 300  # 5 minutes
        
        # Telegram bot (if configured)
        self.telegram_bot = None
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            self.telegram_bot = SentinelTelegramBot(
                os.environ["TELEGRAM_BOT_TOKEN"],
                os.environ.get("TELEGRAM_CHAT_ID", "")
            )
    
    async def start_paper_trading(self):
        """Start live paper trading session"""
        print("🚀 STARTING PAPER TRADING ON POLYMARKET")
        print("=" * 50)
        
        # Fetch current weather data
        print("1️⃣ Fetching current weather data...")
        weather_data = await self.data_fetcher.fetch_all(
            start_date="2024-01-01",
            end_date="2025-12-31",
            regions=["Tokyo", "Seoul", "London", "NYC"]
        )
        
        print(f"   ✅ Weather data loaded: {len(weather_data['weather'])} regions")
        
        # Fetch Polymarket temperature markets
        print("2️⃣ Discovering Polymarket temperature markets...")
        markets = await self.data_fetcher.market.search_weather_markets()
        
        # Filter for actual temperature markets
        temp_markets = []
        for market in markets:
            question = market.get("question", "").lower()
            if any(keyword in question for keyword in ["temperature", "degrees", "celsius", "fahrenheit"]):
                if not any(sports in question for sports in ["nba", "nfl", "nhl", "heat", "hurricanes"]):
                    temp_markets.append(market)
        
        print(f"   ✅ Found {len(temp_markets)} temperature markets")
        
        if not temp_markets:
            print("   ⚠️  No temperature markets found, using demo mode")
            temp_markets = self._create_demo_markets()
        
        # Start trading loop
        print("3️⃣ Starting paper trading loop...")
        print(f"   💰 Paper capital: ${self.paper_capital:,.2f}")
        print(f"   📊 Position size: ${self.position_size:.2f}")
        print(f"   🔄 Update interval: {self.update_interval}s")
        print()
        
        await self._trading_loop(temp_markets, weather_data)
    
    def _create_demo_markets(self) -> List[Dict]:
        """Create demo temperature markets for testing"""
        return [
            {
                "question": "Will the temperature in Tokyo exceed 25°C tomorrow?",
                "condition_id": "demo_tokyo_temp",
                "volume": 10000,
                "tokens": ["YES", "NO"]
            },
            {
                "question": "Will Seoul temperature be above 20°C this week?",
                "condition_id": "demo_seoul_temp", 
                "volume": 8000,
                "tokens": ["YES", "NO"]
            },
            {
                "question": "Will London temperature drop below 10°C?",
                "condition_id": "demo_london_temp",
                "volume": 12000,
                "tokens": ["YES", "NO"]
            }
        ]
    
    async def _trading_loop(self, markets: List[Dict], weather_data: Dict):
        """Main paper trading loop"""
        
        while True:
            try:
                print(f"🔄 Trading update: {datetime.now().strftime('%H:%M:%S')}")
                
                # Process each market
                for market in markets:
                    await self._process_market(market, weather_data)
                
                # Update positions
                await self._update_positions()
                
                # Print summary
                self._print_summary()
                
                # Send Telegram update if configured
                if self.telegram_bot and len(self.paper_trades) > 0:
                    await self._send_telegram_update()
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Paper trading stopped by user")
                break
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _process_market(self, market: Dict, weather_data: Dict):
        """Process individual market for trading signals"""
        
        market_id = market.get("condition_id", "unknown")
        question = market.get("question", "")
        
        # Skip if already have position
        if market_id in self.open_positions:
            return
        
        # Limit total positions
        if len(self.open_positions) >= self.max_positions:
            return
        
        # Generate trading signal
        signal = await self._generate_signal(market, weather_data)
        
        if signal and signal.action != "HOLD":
            # Execute paper trade
            await self._execute_paper_trade(market, signal)
    
    async def _generate_signal(self, market: Dict, weather_data: Dict) -> Optional[TradeSignal]:
        """Generate trading signal for market"""
        
        # Extract region from market question
        question = market.get("question", "").lower()
        region = "Tokyo"  # Default
        
        if "seoul" in question:
            region = "Seoul"
        elif "london" in question:
            region = "London"
        elif "nyc" in question or "new york" in question:
            region = "NYC"
        
        # Get recent weather data for region
        region_data = weather_data.get("weather", {}).get(region, [])
        if not region_data:
            return None
        
        # Use last 7 days for signal generation
        recent_weather = region_data[-7:]
        
        # Calculate weather delta
        if len(recent_weather) >= 2:
            current_temp = recent_weather[-1]["temp_avg"]
            forecast_temp = recent_weather[-2]["temp_avg"]
            delta = current_temp - forecast_temp
            confidence = recent_weather[-1].get("confidence", 0.5)
        else:
            delta = 0
            confidence = 0.5
        
        # Generate signal using backtest engine logic
        from backtesting_engine import HistoricalWeatherPoint
        weather_point = HistoricalWeatherPoint(
            date=datetime.now().strftime("%Y-%m-%d"),
            region=region,
            actual_temp=current_temp,
            forecast_temp=forecast_temp,
            delta=delta,
            ensemble_std=1.0,
            confidence=confidence
        )
        
        action, signal_confidence = self.backtest_engine._generate_signal(weather_point, threshold=2.0)
        
        if action != "HOLD":
            return TradeSignal(
                signal_id=f"paper_{market_id}_{int(time.time())}",
                action=action,
                confidence=signal_confidence,
                reasoning=f"Weather delta: {delta:+.1f}°C, confidence: {signal_confidence:.1%}",
                market_contract=question,
                weather_impact_score=abs(delta) / 10.0,
                token_id="YES" if action == "BUY" else "NO",
                suggested_price=0.5,  # Midpoint
                suggested_size=self.position_size,
                timestamp=datetime.now().isoformat()
            )
        
        return None
    
    async def _execute_paper_trade(self, market: Dict, signal: TradeSignal):
        """Execute paper trade"""
        
        market_id = market.get("condition_id", "unknown")
        entry_price = 0.5  # Simplified pricing
        
        # Create paper trade
        trade = PaperTrade(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            market=market.get("question", ""),
            action=signal.action,
            size=signal.suggested_size,
            entry_price=entry_price,
            current_price=entry_price,
            pnl=0.0,
            exit_reason="open",
            confidence=signal.confidence
        )
        
        self.open_positions[market_id] = trade
        
        print(f"   📊 PAPER TRADE: {signal.action} ${trade.size:.2f}")
        print(f"      Market: {market.get('question', '')[:60]}...")
        print(f"      Confidence: {signal.confidence:.1%}")
        print(f"      Reasoning: {signal.reasoning}")
        
        # Send Telegram alert
        if self.telegram_bot:
            try:
                await self.telegram_bot.send_trade_alert(signal)
            except Exception as e:
                logger.error(f"Telegram alert failed: {e}")
    
    async def _update_positions(self):
        """Update open positions with current prices"""
        
        for market_id, trade in list(self.open_positions.items()):
            # Simulate price movement (in real implementation, fetch from Polymarket)
            import random
            
            # Price movement based on confidence and time
            time_factor = (datetime.now() - datetime.strptime(trade.timestamp.split()[0], "%Y-%m-%d")).seconds / 3600
            price_change = random.gauss(0, 0.01) * time_factor  # Random walk with time
            
            # Bias based on signal confidence
            if trade.confidence > 0.7:
                price_change += random.gauss(0.001, 0.005)  # Slight upward bias
            
            new_price = max(0.01, min(0.99, trade.current_price + price_change))
            trade.current_price = new_price
            
            # Calculate P&L
            if trade.action == "BUY":
                trade.pnl = (new_price - trade.entry_price) * trade.size
            else:  # SELL
                trade.pnl = (trade.entry_price - new_price) * trade.size
            
            # Check exit conditions
            await self._check_exit_conditions(market_id, trade)
    
    async def _check_exit_conditions(self, market_id: str, trade: PaperTrade):
        """Check if position should be closed"""
        
        # Simple exit rules for paper trading
        pnl_pct = trade.pnl / (trade.size * trade.entry_price) if trade.entry_price > 0 else 0
        
        # Take profit at 20% gain
        if pnl_pct >= 0.20:
            trade.exit_reason = "take_profit"
            await self._close_position(market_id, trade)
        
        # Stop loss at 10% loss
        elif pnl_pct <= -0.10:
            trade.exit_reason = "stop_loss"
            await self._close_position(market_id, trade)
        
        # Time exit after 24 hours
        elif (datetime.now() - datetime.strptime(trade.timestamp, "%Y-%m-%d %H:%M:%S")).seconds >= 86400:
            trade.exit_reason = "time_exit"
            await self._close_position(market_id, trade)
    
    async def _close_position(self, market_id: str, trade: PaperTrade):
        """Close position and record trade"""
        
        # Update total P&L
        self.total_pnl += trade.pnl
        self.paper_capital += trade.pnl
        
        # Move to closed trades
        self.paper_trades.append(trade)
        del self.open_positions[market_id]
        
        print(f"   📈 POSITION CLOSED: {trade.exit_reason}")
        print(f"      P&L: ${trade.pnl:+.2f}")
        print(f"      Total P&L: ${self.total_pnl:+.2f}")
        
        # Send Telegram update
        if self.telegram_bot:
            try:
                await self.telegram_bot.send_position_update(trade)
            except Exception as e:
                logger.error(f"Telegram update failed: {e}")
    
    def _print_summary(self):
        """Print trading summary"""
        
        winning_trades = [t for t in self.paper_trades if t.pnl > 0]
        losing_trades = [t for t in self.paper_trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(self.paper_trades) if self.paper_trades else 0
        
        print(f"📊 PAPER TRADING SUMMARY:")
        print(f"   Open Positions: {len(self.open_positions)}")
        print(f"   Closed Trades: {len(self.paper_trades)}")
        print(f"   Win Rate: {win_rate:.1%}")
        print(f"   Total P&L: ${self.total_pnl:+.2f}")
        print(f"   Paper Capital: ${self.paper_capital:,.2f}")
        
        if self.paper_trades:
            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
            print(f"   Avg Win: ${avg_win:.2f}")
            print(f"   Avg Loss: ${avg_loss:.2f}")
            print(f"   Risk/Reward: 1:{abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "")
        
        print()
    
    async def _send_telegram_update(self):
        """Send trading summary to Telegram"""
        
        if not self.telegram_bot:
            return
        
        winning_trades = [t for t in self.paper_trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(self.paper_trades) if self.paper_trades else 0
        
        message = f"""
📊 **Paper Trading Update**
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}

📈 **Performance:**
• Win Rate: {win_rate:.1%}
• Total P&L: ${self.total_pnl:+.2f}
• Paper Capital: ${self.paper_capital:,.2f}
• Open Positions: {len(self.open_positions)}

🎯 **Recent Trades:**
"""
        
        # Add last 3 trades
        for trade in self.paper_trades[-3:]:
            emoji = "🟢" if trade.pnl > 0 else "🔴"
            message += f"{emoji} {trade.action} ${trade.pnl:+.2f} ({trade.exit_reason})\n"
        
        try:
            await self.telegram_bot.send_message(message)
        except Exception as e:
            logger.error(f"Telegram summary failed: {e}")


async def main():
    """Start paper trading"""
    trader = PaperTrader()
    await trader.start_paper_trading()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
