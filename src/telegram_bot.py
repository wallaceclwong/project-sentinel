#!/usr/bin/env python3
"""
PROJECT SENTINEL - Telegram Bot
Phase 4: Mobile alerts and 2FA trade confirmation via Telegram
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Telegram Bot API base URL
TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

@dataclass
class PendingTrade:
    """Trade awaiting 2FA confirmation"""
    trade_id: str
    action: str  # BUY or SELL
    token_id: str
    market_question: str
    price: float
    size: float
    confidence: float
    reasoning: str
    weather_impact: float
    created_at: float
    timeout_seconds: int = 120
    status: str = "pending"  # pending, approved, rejected, expired


class SentinelTelegramBot:
    """Telegram bot for trade alerts and 2FA confirmation"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.pending_trades: Dict[str, PendingTrade] = {}
        self.trade_history: list = []
        self.on_trade_approved: Optional[Callable] = None
        self.on_trade_rejected: Optional[Callable] = None
        self._polling = False
        self._last_update_id = 0
    
    # ==================== CORE MESSAGING ====================
    
    async def _api_call(self, method: str, data: Dict = None) -> Optional[Dict]:
        """Make a Telegram Bot API call"""
        import aiohttp
        
        url = TELEGRAM_API.format(token=self.bot_token, method=method)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data or {}) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("result")
                    else:
                        error = await resp.text()
                        logger.error(f"Telegram API error: {resp.status} - {error}")
                        return None
        except Exception as e:
            logger.error(f"Telegram API call failed: {e}")
            return None
    
    async def send_message(self, text: str, reply_markup: Dict = None) -> Optional[Dict]:
        """Send a message to the configured chat"""
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        return await self._api_call("sendMessage", data)
    
    async def edit_message(self, message_id: int, text: str, reply_markup: Dict = None) -> Optional[Dict]:
        """Edit an existing message"""
        data = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
            
        return await self._api_call("editMessageText", data)
    
    async def answer_callback(self, callback_id: str, text: str = "") -> Optional[Dict]:
        """Answer a callback query (button press)"""
        return await self._api_call("answerCallbackQuery", {
            "callback_query_id": callback_id,
            "text": text
        })
    
    # ==================== TRADE ALERTS ====================
    
    async def send_trade_signal(self, trade: PendingTrade) -> Optional[int]:
        """Send a trade signal with 2FA confirmation buttons"""
        self.pending_trades[trade.trade_id] = trade
        
        # Format signal message
        action_emoji = "🟢" if trade.action == "BUY" else "🔴" if trade.action == "SELL" else "⚪"
        confidence_bar = "█" * int(trade.confidence * 10) + "░" * (10 - int(trade.confidence * 10))
        
        message = (
            f"{action_emoji} <b>TRADE SIGNAL: {trade.action}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 <b>Market:</b> {trade.market_question[:80]}\n"
            f"💰 <b>Price:</b> ${trade.price:.4f}\n"
            f"📦 <b>Size:</b> ${trade.size:.2f}\n"
            f"🌡️ <b>Weather Impact:</b> {trade.weather_impact:.1%}\n\n"
            f"🎯 <b>Confidence:</b> [{confidence_bar}] {trade.confidence:.0%}\n"
            f"📝 <b>Reasoning:</b> {trade.reasoning[:150]}\n\n"
            f"⏰ <i>Expires in {trade.timeout_seconds}s</i>"
        )
        
        # Inline keyboard for 2FA
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ APPROVE", "callback_data": f"approve:{trade.trade_id}"},
                    {"text": "❌ REJECT", "callback_data": f"reject:{trade.trade_id}"}
                ],
                [
                    {"text": "📊 Details", "callback_data": f"details:{trade.trade_id}"},
                    {"text": "📈 Market", "callback_data": f"market:{trade.trade_id}"}
                ]
            ]
        }
        
        result = await self.send_message(message, reply_markup=keyboard)
        
        if result:
            message_id = result.get("message_id")
            logger.info(f"Trade signal sent: {trade.trade_id} (msg: {message_id})")
            
            # Start expiry timer
            asyncio.create_task(self._trade_expiry_timer(trade.trade_id, message_id))
            
            return message_id
        return None
    
    async def _trade_expiry_timer(self, trade_id: str, message_id: int):
        """Timer to expire pending trades"""
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return
            
        await asyncio.sleep(trade.timeout_seconds)
        
        if trade_id in self.pending_trades and self.pending_trades[trade_id].status == "pending":
            self.pending_trades[trade_id].status = "expired"
            
            await self.edit_message(
                message_id,
                f"⏰ <b>TRADE EXPIRED</b>\n\n"
                f"Trade {trade.action} ${trade.size:.2f} @ ${trade.price:.4f}\n"
                f"<i>No response within {trade.timeout_seconds}s</i>"
            )
            
            logger.info(f"Trade expired: {trade_id}")
    
    # ==================== CALLBACK HANDLING ====================
    
    async def handle_callback(self, callback_query: Dict):
        """Process inline keyboard button presses"""
        callback_id = callback_query.get("id", "")
        data = callback_query.get("data", "")
        message_id = callback_query.get("message", {}).get("message_id", 0)
        
        if ":" not in data:
            return
        
        action, trade_id = data.split(":", 1)
        trade = self.pending_trades.get(trade_id)
        
        if not trade:
            await self.answer_callback(callback_id, "Trade not found")
            return
        
        if trade.status != "pending":
            await self.answer_callback(callback_id, f"Trade already {trade.status}")
            return
        
        if action == "approve":
            trade.status = "approved"
            self.trade_history.append(asdict(trade))
            
            await self.answer_callback(callback_id, "✅ Trade approved!")
            await self.edit_message(
                message_id,
                f"✅ <b>TRADE APPROVED</b>\n\n"
                f"{trade.action} ${trade.size:.2f} @ ${trade.price:.4f}\n"
                f"Market: {trade.market_question[:60]}\n"
                f"<i>Executing order...</i>"
            )
            
            if self.on_trade_approved:
                await self.on_trade_approved(trade)
            
            logger.info(f"Trade approved: {trade_id}")
            
        elif action == "reject":
            trade.status = "rejected"
            self.trade_history.append(asdict(trade))
            
            await self.answer_callback(callback_id, "❌ Trade rejected")
            await self.edit_message(
                message_id,
                f"❌ <b>TRADE REJECTED</b>\n\n"
                f"{trade.action} ${trade.size:.2f} @ ${trade.price:.4f}\n"
                f"<i>Trade cancelled by user</i>"
            )
            
            if self.on_trade_rejected:
                await self.on_trade_rejected(trade)
            
            logger.info(f"Trade rejected: {trade_id}")
            
        elif action == "details":
            detail_text = (
                f"📊 <b>Trade Details</b>\n\n"
                f"<b>Action:</b> {trade.action}\n"
                f"<b>Token:</b> {trade.token_id[:20]}...\n"
                f"<b>Price:</b> ${trade.price:.4f}\n"
                f"<b>Size:</b> ${trade.size:.2f}\n"
                f"<b>Total Cost:</b> ${trade.price * trade.size:.2f}\n"
                f"<b>Confidence:</b> {trade.confidence:.0%}\n"
                f"<b>Weather Impact:</b> {trade.weather_impact:.1%}\n\n"
                f"<b>Full Reasoning:</b>\n{trade.reasoning}"
            )
            await self.answer_callback(callback_id, "📊 Details shown")
            await self.send_message(detail_text)
            
        elif action == "market":
            await self.answer_callback(callback_id, "📈 Fetching market data...")
            await self.send_message(
                f"📈 <b>Market Info</b>\n\n"
                f"<b>Question:</b> {trade.market_question}\n"
                f"<b>Token ID:</b> <code>{trade.token_id[:30]}...</code>\n"
                f"<b>Current Price:</b> ${trade.price:.4f}"
            )
    
    # ==================== STATUS & REPORTING ====================
    
    async def send_daily_report(self, stats: Dict[str, Any]):
        """Send daily performance report"""
        message = (
            f"📊 <b>DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 <b>Trades:</b> {stats.get('total_trades', 0)}\n"
            f"✅ <b>Wins:</b> {stats.get('wins', 0)} | "
            f"❌ <b>Losses:</b> {stats.get('losses', 0)}\n"
            f"🎯 <b>Win Rate:</b> {stats.get('win_rate', 0):.0%}\n\n"
            f"💰 <b>P&L:</b> ${stats.get('pnl', 0):+.2f}\n"
            f"📊 <b>Total Volume:</b> ${stats.get('volume', 0):,.2f}\n"
            f"💵 <b>Fees Paid:</b> ${stats.get('fees', 0):.2f}\n\n"
            f"🤖 <b>AI Calls:</b> {stats.get('ai_calls', 0)}\n"
            f"💳 <b>AI Cost:</b> ${stats.get('ai_cost', 0):.4f}\n\n"
            f"🌡️ <b>Weather Events:</b> {stats.get('weather_events', 0)}\n"
            f"⚡ <b>Signals Generated:</b> {stats.get('signals', 0)}"
        )
        
        await self.send_message(message)
    
    async def send_position_update(self, position: Dict[str, Any]):
        """Send position P&L update"""
        pnl = position.get('pnl', 0)
        pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        
        message = (
            f"{pnl_emoji} <b>POSITION UPDATE</b>\n\n"
            f"📊 {position.get('market', 'Unknown')[:60]}\n"
            f"💰 Entry: ${position.get('entry_price', 0):.4f}\n"
            f"📈 Current: ${position.get('current_price', 0):.4f}\n"
            f"💵 P&L: ${pnl:+.2f} ({position.get('pnl_pct', 0):+.1f}%)\n"
            f"📦 Size: ${position.get('size', 0):.2f}"
        )
        
        await self.send_message(message)
    
    async def send_alert(self, alert_type: str, message_text: str):
        """Send a general alert"""
        type_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅",
            "weather": "🌡️"
        }
        
        emoji = type_emoji.get(alert_type, "📢")
        
        await self.send_message(
            f"{emoji} <b>ALERT: {alert_type.upper()}</b>\n\n{message_text}"
        )
    
    # ==================== POLLING ====================
    
    async def start_polling(self):
        """Start polling for updates (callback queries)"""
        self._polling = True
        logger.info("Telegram bot polling started")
        
        await self.send_message(
            "🚀 <b>PROJECT SENTINEL Bot Active</b>\n\n"
            "Ready to receive trade signals and confirmations.\n"
            "Type /help for available commands."
        )
        
        while self._polling:
            try:
                updates = await self._api_call("getUpdates", {
                    "offset": self._last_update_id + 1,
                    "timeout": 30,
                    "allowed_updates": ["message", "callback_query"]
                })
                
                if updates:
                    for update in updates:
                        self._last_update_id = update.get("update_id", self._last_update_id)
                        
                        # Handle callback queries (button presses)
                        if "callback_query" in update:
                            await self.handle_callback(update["callback_query"])
                        
                        # Handle text commands
                        elif "message" in update:
                            await self._handle_command(update["message"])
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
    
    def stop_polling(self):
        """Stop polling"""
        self._polling = False
        logger.info("Telegram bot polling stopped")
    
    async def _handle_command(self, message: Dict):
        """Handle text commands"""
        text = message.get("text", "").strip()
        
        if text == "/start":
            await self.send_message(
                "🚀 <b>PROJECT SENTINEL</b>\n\n"
                "AI-Powered Weather Derivatives Trading\n\n"
                "Commands:\n"
                "/status - System status\n"
                "/positions - Current positions\n"
                "/history - Trade history\n"
                "/budget - Cost & budget info\n"
                "/help - Show help"
            )
        
        elif text == "/status":
            pending = sum(1 for t in self.pending_trades.values() if t.status == "pending")
            approved = sum(1 for t in self.trade_history if t.get("status") == "approved")
            rejected = sum(1 for t in self.trade_history if t.get("status") == "rejected")
            
            await self.send_message(
                f"📊 <b>System Status</b>\n\n"
                f"🟢 Bot: Active\n"
                f"⏳ Pending: {pending}\n"
                f"✅ Approved: {approved}\n"
                f"❌ Rejected: {rejected}\n"
                f"📝 Total Signals: {len(self.trade_history)}"
            )
        
        elif text == "/history":
            if not self.trade_history:
                await self.send_message("📝 No trade history yet")
            else:
                history_text = "📝 <b>Recent Trades</b>\n\n"
                for t in self.trade_history[-5:]:
                    status_emoji = "✅" if t["status"] == "approved" else "❌"
                    history_text += (
                        f"{status_emoji} {t['action']} ${t['size']:.2f} "
                        f"@ ${t['price']:.4f} - {t['status']}\n"
                    )
                await self.send_message(history_text)
        
        elif text == "/help":
            await self.send_message(
                "📖 <b>Help</b>\n\n"
                "<b>How it works:</b>\n"
                "1. AI detects weather anomaly\n"
                "2. You receive a trade signal\n"
                "3. Tap ✅ Approve or ❌ Reject\n"
                "4. Approved trades execute automatically\n\n"
                "<b>Commands:</b>\n"
                "/status - System status\n"
                "/positions - Current positions\n"
                "/history - Trade history\n"
                "/budget - Cost info\n"
                "/help - This message"
            )


async def test_telegram_bot():
    """Test the Telegram bot"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        print("   1. Create bot via @BotFather on Telegram")
        print("   2. Get chat_id by messaging the bot and checking /getUpdates")
        return
    
    bot = SentinelTelegramBot(token, chat_id)
    
    # Send test alert
    await bot.send_message("🧪 <b>Test message from PROJECT SENTINEL</b>\n\nBot is working!")
    
    # Send test trade signal
    trade = PendingTrade(
        trade_id=f"test_{int(time.time())}",
        action="BUY",
        token_id="test_token_123",
        market_question="Will Tokyo temperature exceed 35°C in March 2026?",
        price=0.65,
        size=100.00,
        confidence=0.82,
        reasoning="Weather anomaly detected: +8.5°C delta in Tokyo region with high ensemble confidence.",
        weather_impact=0.78,
        created_at=time.time(),
        timeout_seconds=120
    )
    
    await bot.send_trade_signal(trade)
    print("✅ Test trade signal sent - check your Telegram!")
    
    # Start polling for responses
    print("📡 Listening for responses (Ctrl+C to stop)...")
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        bot.stop_polling()
        print("\n👋 Bot stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_telegram_bot())
