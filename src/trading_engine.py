#!/usr/bin/env python3
"""
PROJECT SENTINEL - Trading Engine
Phase 4: Orchestrates the full trading pipeline from signal to execution
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from polymarket_client import PolymarketClient, TradeOrder, TradeResult, MarketInfo
from telegram_bot import SentinelTelegramBot, PendingTrade
from risk_manager import RiskManager, RiskCheck
from usage_monitor import monitor_api_call, can_make_api_call

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """AI-generated trade signal"""
    signal_id: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    weather_impact: float
    market_contract: str
    token_id: str
    suggested_price: float
    suggested_size: float
    timestamp: str

@dataclass
class ExecutedTrade:
    """Record of an executed trade"""
    trade_id: str
    signal_id: str
    action: str
    token_id: str
    market_question: str
    entry_price: float
    size: float
    fee: float
    status: str  # executed, failed, cancelled
    order_id: str
    confidence: float
    weather_impact: float
    timestamp: str
    pnl: float = 0.0


class TradingEngine:
    """Orchestrates the full trading pipeline"""
    
    def __init__(self, config: Dict[str, Any]):
        # Initialize components
        self.polymarket = PolymarketClient(
            api_key=config.get("polymarket_api_key"),
            api_secret=config.get("polymarket_api_secret")
        )
        
        self.telegram = SentinelTelegramBot(
            bot_token=config.get("telegram_bot_token", ""),
            chat_id=config.get("telegram_chat_id", "")
        )
        
        self.risk_manager = RiskManager(
            max_position_size=config.get("max_position_size", 500),
            max_daily_loss=config.get("max_daily_loss", 100),
            max_total_exposure=config.get("max_total_exposure", 2000),
            max_trades_per_day=config.get("max_trades_per_day", 20)
        )
        
        # State
        self.executed_trades: List[ExecutedTrade] = []
        self.active_positions: Dict[str, ExecutedTrade] = {}
        self.paper_trading = config.get("paper_trading", True)
        self.require_2fa = config.get("require_2fa", True)
        self._running = False
        
        # Register 2FA callbacks
        self.telegram.on_trade_approved = self._on_trade_approved
        self.telegram.on_trade_rejected = self._on_trade_rejected
        
        # Pending signals awaiting 2FA
        self._pending_signals: Dict[str, TradeSignal] = {}
    
    async def start(self):
        """Start the trading engine"""
        self._running = True
        mode = "PAPER" if self.paper_trading else "LIVE"
        twofa = "ON" if self.require_2fa else "OFF"
        
        logger.info(f"Trading engine started - Mode: {mode}, 2FA: {twofa}")
        
        await self.telegram.send_alert("success",
            f"Trading Engine Started\n"
            f"Mode: {mode}\n"
            f"2FA: {twofa}\n"
            f"Max Position: ${self.risk_manager.max_position_size}\n"
            f"Max Daily Loss: ${self.risk_manager.max_daily_loss}"
        )
        
        # Start Telegram polling in background
        asyncio.create_task(self.telegram.start_polling())
    
    async def stop(self):
        """Stop the trading engine"""
        self._running = False
        self.telegram.stop_polling()
        await self.polymarket.close()
        
        logger.info("Trading engine stopped")
        await self.telegram.send_alert("info", "Trading Engine Stopped")
    
    # ==================== SIGNAL PROCESSING ====================
    
    async def process_trade_signal(self, signal: TradeSignal) -> Optional[ExecutedTrade]:
        """Process an AI-generated trade signal through the full pipeline"""
        logger.info(f"Processing signal: {signal.signal_id} - {signal.action} "
                    f"(confidence: {signal.confidence:.0%})")
        
        if signal.action == "HOLD":
            logger.info("Signal is HOLD - no action needed")
            return None
        
        # Step 1: Risk check
        risk_check = self.risk_manager.check_trade(
            action=signal.action,
            size=signal.suggested_size,
            price=signal.suggested_price
        )
        
        if not risk_check.approved:
            logger.warning(f"Trade rejected by risk manager: {risk_check.reason}")
            await self.telegram.send_alert("warning",
                f"Trade Blocked by Risk Manager\n\n"
                f"Signal: {signal.action} ${signal.suggested_size:.2f}\n"
                f"Reason: {risk_check.reason}"
            )
            return None
        
        # Step 2: Market analysis
        market_analysis = await self.polymarket.analyze_market(signal.token_id)
        
        if not market_analysis.get("tradeable", False):
            logger.warning(f"Market not tradeable: spread too wide or low liquidity")
            await self.telegram.send_alert("warning",
                f"Market Not Tradeable\n\n"
                f"Spread: {market_analysis.get('spread_pct', 0):.2f}%\n"
                f"Liquidity: {market_analysis.get('liquidity_score', 0):.2f}"
            )
            return None
        
        # Adjust price based on current market
        execution_price = market_analysis.get("mid_price", signal.suggested_price)
        
        # Step 3: 2FA confirmation or direct execution
        if self.require_2fa:
            return await self._request_2fa(signal, execution_price, market_analysis)
        else:
            return await self._execute_trade(signal, execution_price)
    
    async def _request_2fa(self, signal: TradeSignal, price: float, 
                           market_analysis: Dict) -> Optional[ExecutedTrade]:
        """Request 2FA confirmation via Telegram"""
        trade_id = f"trade_{int(time.time())}_{signal.signal_id[:8]}"
        
        self._pending_signals[trade_id] = signal
        
        pending_trade = PendingTrade(
            trade_id=trade_id,
            action=signal.action,
            token_id=signal.token_id,
            market_question=signal.market_contract,
            price=price,
            size=signal.suggested_size,
            confidence=signal.confidence,
            reasoning=signal.reasoning,
            weather_impact=signal.weather_impact,
            created_at=time.time(),
            timeout_seconds=120
        )
        
        await self.telegram.send_trade_signal(pending_trade)
        logger.info(f"2FA requested for trade: {trade_id}")
        
        # Trade will be executed via callback when user approves
        return None
    
    async def _on_trade_approved(self, trade: PendingTrade):
        """Callback when user approves a trade via Telegram"""
        signal = self._pending_signals.pop(trade.trade_id, None)
        
        if signal:
            result = await self._execute_trade(signal, trade.price)
            
            if result:
                await self.telegram.send_message(
                    f"✅ <b>TRADE EXECUTED</b>\n\n"
                    f"Order ID: <code>{result.order_id}</code>\n"
                    f"{result.action} ${result.size:.2f} @ ${result.entry_price:.4f}\n"
                    f"Fee: ${result.fee:.4f}\n"
                    f"Status: {result.status}"
                )
            else:
                await self.telegram.send_alert("error", "Trade execution failed")
    
    async def _on_trade_rejected(self, trade: PendingTrade):
        """Callback when user rejects a trade via Telegram"""
        self._pending_signals.pop(trade.trade_id, None)
        logger.info(f"Trade rejected by user: {trade.trade_id}")
    
    # ==================== EXECUTION ====================
    
    async def _execute_trade(self, signal: TradeSignal, price: float) -> Optional[ExecutedTrade]:
        """Execute a trade on Polymarket"""
        trade_id = f"exec_{int(time.time())}_{signal.signal_id[:8]}"
        
        order = TradeOrder(
            token_id=signal.token_id,
            side=signal.action,
            price=price,
            size=signal.suggested_size,
            order_type="limit",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Executing order: {signal.action} {signal.suggested_size} @ {price}")
        
        result = await self.polymarket.create_order(order)
        
        if result:
            executed = ExecutedTrade(
                trade_id=trade_id,
                signal_id=signal.signal_id,
                action=signal.action,
                token_id=signal.token_id,
                market_question=signal.market_contract,
                entry_price=result.filled_price,
                size=result.filled_size,
                fee=result.fee,
                status=result.status,
                order_id=result.order_id,
                confidence=signal.confidence,
                weather_impact=signal.weather_impact,
                timestamp=datetime.now().isoformat()
            )
            
            self.executed_trades.append(executed)
            self.active_positions[trade_id] = executed
            self.risk_manager.record_trade(signal.action, result.filled_size, result.filled_price)
            
            logger.info(f"Trade executed: {trade_id} - {result.status}")
            return executed
        else:
            logger.error(f"Trade execution failed for signal: {signal.signal_id}")
            return None
    
    # ==================== PORTFOLIO ====================
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        total_pnl = sum(t.pnl for t in self.executed_trades)
        total_volume = sum(t.size * t.entry_price for t in self.executed_trades)
        total_fees = sum(t.fee for t in self.executed_trades)
        
        wins = sum(1 for t in self.executed_trades if t.pnl > 0)
        losses = sum(1 for t in self.executed_trades if t.pnl < 0)
        total = len(self.executed_trades)
        
        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": wins / total if total > 0 else 0,
            "pnl": total_pnl,
            "volume": total_volume,
            "fees": total_fees,
            "active_positions": len(self.active_positions),
            "risk_status": self.risk_manager.get_status()
        }
    
    async def send_daily_report(self):
        """Generate and send daily trading report"""
        summary = self.get_portfolio_summary()
        await self.telegram.send_daily_report(summary)


async def test_trading_engine():
    """Test the trading engine with paper trading"""
    config = {
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "paper_trading": True,
        "require_2fa": False,  # Disable for testing
        "max_position_size": 500,
        "max_daily_loss": 100,
        "max_total_exposure": 2000,
        "max_trades_per_day": 20
    }
    
    engine = TradingEngine(config)
    
    # Test with a simulated signal
    signal = TradeSignal(
        signal_id="test_001",
        action="BUY",
        confidence=0.82,
        reasoning="Tokyo temperature anomaly: +8.5°C delta with high ensemble confidence",
        weather_impact=0.78,
        market_contract="Will Tokyo exceed 35°C in March 2026?",
        token_id="test_token_123",
        suggested_price=0.55,
        suggested_size=100,
        timestamp=datetime.now().isoformat()
    )
    
    print("🔧 Testing trading engine (paper mode)...")
    result = await engine.process_trade_signal(signal)
    
    if result:
        print(f"✅ Trade executed: {result.action} ${result.size:.2f} @ ${result.entry_price:.4f}")
        print(f"   Order ID: {result.order_id}")
        print(f"   Fee: ${result.fee:.4f}")
    
    summary = engine.get_portfolio_summary()
    print(f"\n📊 Portfolio: {summary['total_trades']} trades, P&L: ${summary['pnl']:.2f}")
    
    await engine.polymarket.close()
    print("✅ Trading engine test complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_trading_engine())
