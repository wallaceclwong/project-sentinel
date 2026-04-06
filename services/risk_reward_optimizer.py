#!/usr/bin/env python3
"""
PROJECT SENTINEL - Risk/Reward Optimizer
Advanced exit strategies and risk management for improved profitability
"""

import math
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExitStrategy:
    """Optimized exit strategy parameters"""
    stop_loss_pct: float
    take_profit_pct: float
    max_holding_days: int
    trailing_stop_pct: float
    confidence_multiplier: float
    weather_informed: bool

@dataclass
class MarketConditions:
    """Current market and weather conditions"""
    volatility: float
    trend_strength: float
    ensemble_spread: float
    weather_confidence: float
    pattern_type: Optional[str]

class RiskRewardOptimizer:
    """Optimizes risk/reward ratios for profitable trading"""
    
    def __init__(self):
        self.volatility_window = 20  # Days for volatility calculation
        self.min_risk_reward = 3.0   # Minimum risk/reward ratio (increased)
        self.max_stop_loss = 0.08     # Maximum 8% stop loss
        self.min_take_profit = 0.30    # Minimum 30% take profit (increased)
        
        # Pattern-based adjustments - optimized for profitability
        self.pattern_adjustments = {
            "heat_wave": {"stop_loss": 0.05, "take_profit": 0.40, "holding": 7},  # +2 days
            "cold_snap": {"stop_loss": 0.06, "take_profit": 0.35, "holding": 6},  # +2 days
            "unusual_warming": {"stop_loss": 0.07, "take_profit": 0.30, "holding": 5},  # +2 days
            "unusual_cooling": {"stop_loss": 0.07, "take_profit": 0.30, "holding": 5},  # +2 days
            "normal": {"stop_loss": 0.08, "take_profit": 0.30, "holding": 4}  # +2 days
        }
    
    def calculate_market_conditions(self, price_history: List[float], 
                                   ensemble_spread: float,
                                   weather_confidence: float,
                                   pattern_type: Optional[str] = None) -> MarketConditions:
        """Calculate current market conditions"""
        
        # Calculate volatility
        if len(price_history) >= self.volatility_window:
            recent_prices = price_history[-self.volatility_window:]
            returns = [(recent_prices[i] / recent_prices[i-1] - 1) for i in range(1, len(recent_prices))]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0.02
        else:
            volatility = 0.02  # Default volatility
        
        # Calculate trend strength
        if len(price_history) >= 10:
            recent_trend = (price_history[-1] - price_history[-10]) / price_history[-10]
            trend_strength = abs(recent_trend)
        else:
            trend_strength = 0.01
        
        return MarketConditions(
            volatility=volatility,
            trend_strength=trend_strength,
            ensemble_spread=ensemble_spread,
            weather_confidence=weather_confidence,
            pattern_type=pattern_type
        )
    
    def optimize_exit_strategy(self, conditions: MarketConditions,
                              signal_confidence: float,
                              trade_direction: str) -> ExitStrategy:
        """Generate optimized exit strategy based on conditions"""
        
        # Base parameters from pattern
        if conditions.pattern_type and conditions.pattern_type in self.pattern_adjustments:
            pattern_params = self.pattern_adjustments[conditions.pattern_type]
            base_stop_loss = pattern_params["stop_loss"]
            base_take_profit = pattern_params["take_profit"]
            base_holding = pattern_params["holding"]
        else:
            pattern_params = self.pattern_adjustments["normal"]
            base_stop_loss = pattern_params["stop_loss"]
            base_take_profit = pattern_params["take_profit"]
            base_holding = pattern_params["holding"]
        
        # Adjust holding period based on pattern
        if conditions.pattern_type and conditions.pattern_type in self.pattern_adjustments:
            pattern_config = self.pattern_adjustments[conditions.pattern_type]
            max_holding_days = pattern_config["holding"]
        else:
            max_holding_days = 4  # Default increased
        
        # Dynamic holding period optimization
        if signal_confidence > 0.9:
            max_holding_days = int(max_holding_days * 1.5)  # 50% longer for high confidence
        elif signal_confidence < 0.6:
            max_holding_days = max(2, int(max_holding_days * 0.7))  # 30% shorter for low confidence
        
        # Extend holding for strong weather patterns
        if conditions.pattern_type in ["heat_wave", "cold_snap"]:
            max_holding_days = int(max_holding_days * 1.2)  # 20% longer for extreme patterns
        
        # Minimum holding period to avoid premature exits
        max_holding_days = max(3, max_holding_days)
        
        # Volatility adjustment
        volatility_factor = min(1.5, max(0.5, conditions.volatility / 0.02))
        
        # High volatility = wider stops, lower targets
        if conditions.volatility > 0.03:
            stop_loss_adj = 1.2
            take_profit_adj = 0.8
        elif conditions.volatility < 0.01:
            stop_loss_adj = 0.8
            take_profit_adj = 1.2
        else:
            stop_loss_adj = 1.0
            take_profit_adj = 1.0
        
        # Ensemble spread adjustment
        if conditions.ensemble_spread > 5.0:  # High uncertainty
            spread_adj_stop = 1.3
            spread_adj_profit = 0.7
        elif conditions.ensemble_spread < 2.0:  # High confidence
            spread_adj_stop = 0.7
            spread_adj_profit = 1.3
        else:
            spread_adj_stop = 1.0
            spread_adj_profit = 1.0
        
        # Weather confidence adjustment
        confidence_multiplier = min(2.0, max(0.5, conditions.weather_confidence))
        
        # Calculate final parameters
        stop_loss_pct = min(self.max_stop_loss, 
                          base_stop_loss * stop_loss_adj * spread_adj_stop)
        take_profit_pct = max(self.min_take_profit,
                             base_take_profit * take_profit_adj * spread_adj_profit)
        
        # Ensure minimum risk/reward ratio
        if take_profit_pct / stop_loss_pct < self.min_risk_reward:
            take_profit_pct = stop_loss_pct * self.min_risk_reward
        
        # Confidence-based holding period
        max_holding_days = max(2, min(10, base_holding * confidence_multiplier))
        
        # Ultra-aggressive take-profit for elite signals
        if conditions.weather_confidence > 0.90:
            take_profit_pct = max(take_profit_pct, 0.50)  # Minimum 50% for elite confidence
        elif conditions.weather_confidence > 0.85:
            take_profit_pct = max(take_profit_pct, 0.45)  # Minimum 45% for high confidence
        elif conditions.weather_confidence > 0.75:
            take_profit_pct = max(take_profit_pct, 0.35)  # Minimum 35% for good confidence
        
        # Add trailing stop for strong trends
        if conditions.trend_strength > 0.03:
            trailing_stop_pct = stop_loss_pct * 0.6  # Much tighter trailing stop for strong trends
        else:
            trailing_stop_pct = stop_loss_pct * 0.8  # Tighter trailing stop for weak trends      
        
        return ExitStrategy(
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            max_holding_days=int(max_holding_days),
            trailing_stop_pct=trailing_stop_pct,
            confidence_multiplier=confidence_multiplier,
            weather_informed=conditions.pattern_type is not None
        )
    
    def calculate_dynamic_position_size(self, base_size: float,
                                      conditions: MarketConditions,
                                      strategy: ExitStrategy) -> float:
        """Calculate position size based on risk and conditions"""
        
        # Risk-adjusted position sizing
        risk_per_trade = base_size * strategy.stop_loss_pct
        
        # Volatility adjustment
        if conditions.volatility > 0.03:
            volatility_adj = 0.7  # Reduce size in high volatility
        elif conditions.volatility < 0.01:
            volatility_adj = 1.3  # Increase size in low volatility
        else:
            volatility_adj = 1.0
        
        # Confidence adjustment
        confidence_adj = strategy.confidence_multiplier
        
        # Pattern adjustment
        if conditions.pattern_type in ["heat_wave", "cold_snap"]:
            pattern_adj = 1.2  # Increase size for strong patterns
        else:
            pattern_adj = 1.0
        
        # Calculate final position size
        adjusted_size = base_size * volatility_adj * confidence_adj * pattern_adj
        
        # Ensure maximum risk doesn't exceed 2% of portfolio
        max_risk = base_size * 0.02
        if risk_per_trade > max_risk:
            adjusted_size = max_risk / strategy.stop_loss_pct
        
        return adjusted_size
    
    def should_exit_trade(self, entry_price: float, current_price: float,
                         entry_date: str, current_date: str,
                         strategy: ExitStrategy, highest_price: float = None,
                         lowest_price: float = None) -> Tuple[bool, str]:
        """Determine if trade should be exited"""
        
        # Calculate P&L percentage
        if current_price > entry_price:  # Long position
            pnl_pct = (current_price - entry_price) / entry_price
        else:  # Short position
            pnl_pct = (entry_price - current_price) / entry_price
        
        # Take profit check
        if pnl_pct >= strategy.take_profit_pct:
            return True, "take_profit"
        
        # Stop loss check
        if pnl_pct <= -strategy.stop_loss_pct:
            return True, "stop_loss"
        
        # Trailing stop check
        if strategy.trailing_stop_pct > 0 and highest_price:
            trailing_stop = highest_price * (1 - strategy.trailing_stop_pct)
            if current_price <= trailing_stop:
                return True, "trailing_stop"
        
        # Time-based exit
        entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        holding_days = (current_dt - entry_dt).days
        
        if holding_days >= strategy.max_holding_days:
            return True, "time_exit"
        
        return False, "hold"
    
    def analyze_trade_performance(self, trades: List[Dict]) -> Dict[str, Any]:
        """Analyze trade performance and suggest improvements"""
        
        if not trades:
            return {"error": "No trades to analyze"}
        
        wins = [t for t in trades if t.get("pnl", 0) > 0]
        losses = [t for t in trades if t.get("pnl", 0) <= 0]
        
        win_rate = len(wins) / len(trades) if trades else 0
        avg_win = statistics.mean([t["pnl"] for t in wins]) if wins else 0
        avg_loss = statistics.mean([t["pnl"] for t in losses]) if losses else 0
        risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        # Holding period analysis
        holding_periods = [t.get("holding_days", 0) for t in trades]
        avg_holding = statistics.mean(holding_periods) if holding_periods else 0
        
        # Exit reason analysis
        exit_reasons = {}
        for trade in trades:
            reason = trade.get("exit_reason", "unknown")
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        # Recommendations
        recommendations = []
        
        if risk_reward < 2.0:
            recommendations.append("Increase take-profit targets or reduce stop-loss")
        
        if win_rate < 0.4:
            recommendations.append("Improve signal generation or increase confidence threshold")
        
        if avg_holding > 7:
            recommendations.append("Consider shorter holding periods or trend-following exits")
        
        if exit_reasons.get("stop_loss", 0) > len(trades) * 0.4:
            recommendations.append("Stop-loss too tight - consider volatility adjustment")
        
        return {
            "total_trades": len(trades),
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "risk_reward_ratio": risk_reward,
            "avg_holding_days": avg_holding,
            "exit_reasons": exit_reasons,
            "recommendations": recommendations,
            "performance_grade": self._grade_performance(win_rate, risk_reward)
        }
    
    def _grade_performance(self, win_rate: float, risk_reward: float) -> str:
        """Grade overall trading performance"""
        
        if win_rate >= 0.6 and risk_reward >= 3.0:
            return "A+ (Excellent)"
        elif win_rate >= 0.55 and risk_reward >= 2.5:
            return "A (Very Good)"
        elif win_rate >= 0.5 and risk_reward >= 2.0:
            return "B (Good)"
        elif win_rate >= 0.45 and risk_reward >= 1.5:
            return "C (Average)"
        elif win_rate >= 0.4 and risk_reward >= 1.2:
            return "D (Below Average)"
        else:
            return "F (Poor)"


def main():
    """Test the risk/reward optimizer"""
    print("🎯 Risk/Reward Optimizer Test")
    print("=" * 40)
    
    optimizer = RiskRewardOptimizer()
    
    # Test market conditions calculation
    price_history = [100, 102, 98, 105, 103, 107, 104, 108, 106, 110]
    conditions = optimizer.calculate_market_conditions(
        price_history, ensemble_spread=3.2, weather_confidence=0.85, pattern_type="heat_wave"
    )
    
    print(f"📊 Market Conditions:")
    print(f"   Volatility: {conditions.volatility:.3f}")
    print(f"   Trend Strength: {conditions.trend_strength:.3f}")
    print(f"   Ensemble Spread: {conditions.ensemble_spread}°C")
    print(f"   Weather Confidence: {conditions.weather_confidence:.1%}")
    print(f"   Pattern: {conditions.pattern_type}")
    
    # Test exit strategy optimization
    strategy = optimizer.optimize_exit_strategy(conditions, signal_confidence=0.9, trade_direction="BUY")
    
    print(f"\n🎯 Optimized Exit Strategy:")
    print(f"   Stop Loss: {strategy.stop_loss_pct:.1%}")
    print(f"   Take Profit: {strategy.take_profit_pct:.1%}")
    print(f"   Risk/Reward: 1:{strategy.take_profit_pct/strategy.stop_loss_pct:.1f}")
    print(f"   Max Holding: {strategy.max_holding_days} days")
    print(f"   Trailing Stop: {strategy.trailing_stop_pct:.1%}")
    print(f"   Weather Informed: {strategy.weather_informed}")
    
    # Test position sizing
    base_size = 1000
    optimized_size = optimizer.calculate_dynamic_position_size(base_size, conditions, strategy)
    
    print(f"\n💰 Position Sizing:")
    print(f"   Base Size: ${base_size}")
    print(f"   Optimized Size: ${optimized_size:.0f}")
    print(f"   Adjustment Factor: {optimized_size/base_size:.2f}x")
    
    print("\n✅ Risk/Reward Optimizer operational")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
