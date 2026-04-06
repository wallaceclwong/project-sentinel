#!/usr/bin/env python3
"""
PROJECT SENTINEL - Risk Manager
Phase 4: Position sizing, loss limits, and circuit breakers
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RiskCheck:
    """Result of a risk check"""
    approved: bool
    reason: str
    adjusted_size: float = 0.0
    risk_score: float = 0.0

@dataclass
class TradeRecord:
    """Internal record of a trade for risk tracking"""
    action: str
    size: float
    price: float
    cost: float
    timestamp: float
    pnl: float = 0.0


class RiskManager:
    """Manages trading risk with position limits and circuit breakers"""
    
    def __init__(self, max_position_size: float = 500,
                 max_daily_loss: float = 100,
                 max_total_exposure: float = 2000,
                 max_trades_per_day: int = 20,
                 min_confidence: float = 0.60,
                 max_spread_pct: float = 5.0):
        
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.max_total_exposure = max_total_exposure
        self.max_trades_per_day = max_trades_per_day
        self.min_confidence = min_confidence
        self.max_spread_pct = max_spread_pct
        
        self.trade_records: List[TradeRecord] = []
        self.daily_pnl: float = 0.0
        self.total_exposure: float = 0.0
        self.circuit_breaker_active: bool = False
        self.circuit_breaker_until: float = 0
        self._last_daily_reset: str = ""
    
    def _reset_daily_if_needed(self):
        """Reset daily counters at midnight"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._last_daily_reset:
            self.daily_pnl = 0.0
            self._last_daily_reset = today
            logger.info("Daily risk counters reset")
    
    def check_trade(self, action: str, size: float, price: float, 
                    confidence: float = 1.0, spread_pct: float = 0.0) -> RiskCheck:
        """Check if a trade passes all risk criteria"""
        self._reset_daily_if_needed()
        
        trade_cost = size * price
        
        # Circuit breaker check
        if self.circuit_breaker_active:
            if time.time() < self.circuit_breaker_until:
                remaining = int(self.circuit_breaker_until - time.time())
                return RiskCheck(
                    approved=False,
                    reason=f"Circuit breaker active ({remaining}s remaining)",
                    risk_score=1.0
                )
            else:
                self.circuit_breaker_active = False
                logger.info("Circuit breaker deactivated")
        
        # Position size limit
        if size > self.max_position_size:
            return RiskCheck(
                approved=False,
                reason=f"Position size ${size:.2f} exceeds limit ${self.max_position_size:.2f}",
                adjusted_size=self.max_position_size,
                risk_score=0.8
            )
        
        # Daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            self._activate_circuit_breaker(3600)  # 1 hour cooldown
            return RiskCheck(
                approved=False,
                reason=f"Daily loss limit reached: ${self.daily_pnl:.2f} / -${self.max_daily_loss:.2f}",
                risk_score=1.0
            )
        
        # Total exposure limit
        new_exposure = self.total_exposure + trade_cost
        if new_exposure > self.max_total_exposure:
            max_allowed = self.max_total_exposure - self.total_exposure
            if max_allowed <= 0:
                return RiskCheck(
                    approved=False,
                    reason=f"Exposure limit reached: ${self.total_exposure:.2f} / ${self.max_total_exposure:.2f}",
                    risk_score=0.9
                )
            adjusted_size = max_allowed / price if price > 0 else 0
            return RiskCheck(
                approved=True,
                reason=f"Size reduced to stay within exposure limit",
                adjusted_size=adjusted_size,
                risk_score=0.7
            )
        
        # Daily trade count limit
        today_trades = self._count_today_trades()
        if today_trades >= self.max_trades_per_day:
            return RiskCheck(
                approved=False,
                reason=f"Daily trade limit reached: {today_trades}/{self.max_trades_per_day}",
                risk_score=0.6
            )
        
        # Confidence threshold
        if confidence < self.min_confidence:
            return RiskCheck(
                approved=False,
                reason=f"Confidence {confidence:.0%} below minimum {self.min_confidence:.0%}",
                risk_score=0.5
            )
        
        # Spread check
        if spread_pct > self.max_spread_pct:
            return RiskCheck(
                approved=False,
                reason=f"Spread {spread_pct:.2f}% exceeds maximum {self.max_spread_pct:.2f}%",
                risk_score=0.4
            )
        
        # Calculate adaptive position size based on confidence
        adaptive_size = self._calculate_adaptive_position_size(size, confidence, price)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(adaptive_size, price, confidence)
        
        return RiskCheck(
            approved=True,
            reason="Trade approved with adaptive sizing",
            adjusted_size=adaptive_size,
            risk_score=risk_score
        )
    
    def record_trade(self, action: str, size: float, price: float, pnl: float = 0.0):
        """Record a completed trade for risk tracking"""
        cost = size * price
        
        record = TradeRecord(
            action=action,
            size=size,
            price=price,
            cost=cost,
            timestamp=time.time(),
            pnl=pnl
        )
        
        self.trade_records.append(record)
        self.daily_pnl += pnl
        
        if action == "BUY":
            self.total_exposure += cost
        elif action == "SELL":
            self.total_exposure = max(0, self.total_exposure - cost)
        
        # Check if we need to activate circuit breaker
        if self.daily_pnl <= -self.max_daily_loss * 0.8:
            logger.warning(f"Approaching daily loss limit: ${self.daily_pnl:.2f}")
        
        if self.daily_pnl <= -self.max_daily_loss:
            self._activate_circuit_breaker(3600)
    
    def update_pnl(self, trade_id: str, pnl: float):
        """Update P&L for a trade (when position is closed)"""
        self.daily_pnl += pnl
        
        if self.daily_pnl <= -self.max_daily_loss:
            self._activate_circuit_breaker(3600)
            logger.warning(f"Daily loss limit hit: ${self.daily_pnl:.2f}")
    
    def _activate_circuit_breaker(self, duration_seconds: int):
        """Activate circuit breaker to halt trading"""
        self.circuit_breaker_active = True
        self.circuit_breaker_until = time.time() + duration_seconds
        logger.warning(f"Circuit breaker activated for {duration_seconds}s")
    
    def _count_today_trades(self) -> int:
        """Count trades executed today"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()
        return sum(1 for r in self.trade_records if r.timestamp >= today_start)
    
    def _calculate_risk_score(self, size: float, price: float, confidence: float) -> float:
        """Calculate overall risk score (0=low risk, 1=high risk)"""
        cost = size * price
        
        size_risk = min(cost / self.max_position_size, 1.0) * 0.3
        exposure_risk = min(self.total_exposure / self.max_total_exposure, 1.0) * 0.3
        loss_risk = min(abs(self.daily_pnl) / self.max_daily_loss, 1.0) * 0.2
        confidence_risk = (1 - confidence) * 0.2
        
        return size_risk + exposure_risk + loss_risk + confidence_risk
    
    def _calculate_adaptive_position_size(self, base_size: float, confidence: float, price: float) -> float:
        """Calculate adaptive position size based on confidence and market conditions"""
        
        # Confidence-based scaling
        if confidence >= 0.9:
            confidence_multiplier = 1.5  # Very high confidence = larger position
        elif confidence >= 0.8:
            confidence_multiplier = 1.2  # High confidence = slightly larger
        elif confidence >= 0.6:
            confidence_multiplier = 1.0  # Normal confidence = base size
        elif confidence >= 0.4:
            confidence_multiplier = 0.7  # Low confidence = smaller position
        else:
            confidence_multiplier = 0.4  # Very low confidence = much smaller
        
        # Daily PNL adjustment (reduce size when losing)
        pnl_adjustment = 1.0
        if self.daily_pnl < 0:
            pnl_factor = abs(self.daily_pnl) / self.max_daily_loss
            pnl_adjustment = max(0.5, 1.0 - pnl_factor * 0.5)  # Reduce size up to 50%
        
        # Exposure adjustment (reduce size as we approach limits)
        exposure_ratio = self.total_exposure / self.max_total_exposure
        exposure_adjustment = max(0.3, 1.0 - exposure_ratio * 0.7)  # Reduce size up to 70%
        
        # Trade count adjustment (reduce size if many trades today)
        today_trades = self._count_today_trades()
        trade_adjustment = 1.0
        if today_trades > self.max_trades_per_day * 0.7:
            trade_factor = (today_trades / self.max_trades_per_day - 0.7) / 0.3
            trade_adjustment = max(0.6, 1.0 - trade_factor * 0.4)  # Reduce size up to 40%
        
        # Calculate final adaptive size
        adaptive_size = base_size * confidence_multiplier * pnl_adjustment * exposure_adjustment * trade_adjustment
        
        # Ensure we don't exceed maximum position size
        max_allowed = min(self.max_position_size, self.max_total_exposure - self.total_exposure)
        adaptive_size = min(adaptive_size, max_allowed / price if price > 0 else base_size)
        
        # Minimum size check
        min_size = base_size * 0.1  # Don't go below 10% of base size
        adaptive_size = max(adaptive_size, min_size)
        
        logger.debug(f"Adaptive sizing: {base_size:.2f} -> {adaptive_size:.2f} "
                    f"(conf: {confidence:.2f}, pnl_adj: {pnl_adjustment:.2f}, "
                    f"exp_adj: {exposure_adjustment:.2f}, trade_adj: {trade_adjustment:.2f})")
        
        return adaptive_size
    
    def get_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        self._reset_daily_if_needed()
        today_trades = self._count_today_trades()
        
        return {
            "circuit_breaker": self.circuit_breaker_active,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_limit": -self.max_daily_loss,
            "daily_pnl_pct": abs(self.daily_pnl / self.max_daily_loss * 100) if self.max_daily_loss > 0 else 0,
            "total_exposure": self.total_exposure,
            "exposure_limit": self.max_total_exposure,
            "exposure_pct": self.total_exposure / self.max_total_exposure * 100 if self.max_total_exposure > 0 else 0,
            "trades_today": today_trades,
            "trades_limit": self.max_trades_per_day,
            "max_position": self.max_position_size,
            "status": "🔴 HALTED" if self.circuit_breaker_active else "🟢 ACTIVE"
        }
    
    def get_risk_report(self) -> str:
        """Get formatted risk report"""
        status = self.get_status()
        
        return (
            f"Risk Status: {status['status']}\n"
            f"Daily P&L: ${status['daily_pnl']:.2f} / -${self.max_daily_loss:.2f} "
            f"({status['daily_pnl_pct']:.1f}%)\n"
            f"Exposure: ${status['total_exposure']:.2f} / ${self.max_total_exposure:.2f} "
            f"({status['exposure_pct']:.1f}%)\n"
            f"Trades Today: {status['trades_today']} / {self.max_trades_per_day}\n"
            f"Circuit Breaker: {'ACTIVE' if status['circuit_breaker'] else 'OFF'}"
        )
