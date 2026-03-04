#!/usr/bin/env python3
"""
PROJECT SENTINEL - Backtesting Engine
Phase 4: Historical simulation and strategy validation
"""

import asyncio
import json
import logging
import math
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from data_fetcher import SentinelDataFetcher
from polymarket_client import PolymarketClient
from risk_manager import RiskManager
from risk_reward_optimizer import RiskRewardOptimizer, MarketConditions, ExitStrategy
from weathernext2_client import WeatherNext2Client

logger = logging.getLogger(__name__)

@dataclass
class HistoricalWeatherPoint:
    """Historical weather data point"""
    date: str
    region: str
    actual_temp: float
    forecast_temp: float
    delta: float  # actual - forecast
    ensemble_std: float
    confidence: float

@dataclass
class SimulatedPrice:
    """Simulated market price based on weather impact"""
    date: str
    token_id: str
    price: float
    volume: float

@dataclass
class BacktestTrade:
    """A trade executed during backtesting"""
    date: str
    action: str
    price: float
    size: float
    cost: float
    fee: float
    weather_delta: float
    confidence: float
    pnl: float = 0.0
    exit_price: float = 0.0
    exit_date: str = ""
    holding_days: int = 0

@dataclass
class BacktestResult:
    """Complete backtesting result"""
    strategy_name: str
    start_date: str
    end_date: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    avg_trade_pnl: float
    avg_win: float
    avg_loss: float
    avg_holding_days: float
    total_fees: float
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)


class WeatherPriceModel:
    """Models the relationship between weather anomalies and market prices"""
    
    def __init__(self, base_price: float = 0.50, sensitivity: float = 0.05,
                 noise_std: float = 0.02, mean_reversion: float = 0.1):
        self.base_price = base_price
        self.sensitivity = sensitivity
        self.noise_std = noise_std
        self.mean_reversion = mean_reversion
        self.current_price = base_price
    
    def generate_price(self, weather_delta: float, confidence: float) -> float:
        """Generate a simulated price based on weather delta"""
        # Weather impact on price
        weather_impact = weather_delta * self.sensitivity * confidence
        
        # Mean reversion toward base price
        reversion = (self.base_price - self.current_price) * self.mean_reversion
        
        # Random noise
        noise = random.gauss(0, self.noise_std)
        
        # Calculate new price
        new_price = self.current_price + weather_impact + reversion + noise
        new_price = max(0.01, min(0.99, new_price))  # Clamp to valid range
        
        self.current_price = new_price
        return new_price


class BacktestingEngine:
    """Runs historical simulations to validate trading strategies"""
    
    def __init__(self, initial_capital: float = 10000,
                 fee_rate: float = 0.002,
                 slippage_bps: float = 5):
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_bps = slippage_bps
        self.price_model = WeatherPriceModel()
        self.risk_manager = RiskManager(
            max_position_size=initial_capital * 0.05,
            max_daily_loss=initial_capital * 0.01,
            max_total_exposure=initial_capital * 0.20
        )
        self.risk_optimizer = RiskRewardOptimizer()
        self.weathernext2 = WeatherNext2Client()
    
    def generate_historical_weather(self, start_date: str, end_date: str,
                                     region: str = "Tokyo") -> List[HistoricalWeatherPoint]:
        """Generate synthetic historical weather data for backtesting
        
        In production, this would fetch real NOAA/ECMWF data.
        For now, generates realistic synthetic data with seasonal patterns.
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        weather_data = []
        current = start
        
        while current <= end:
            day_of_year = current.timetuple().tm_yday
            
            # Seasonal temperature pattern (Northern Hemisphere)
            seasonal_temp = 15 + 15 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
            
            # Add weather variability
            daily_variation = random.gauss(0, 3)
            actual_temp = seasonal_temp + daily_variation
            
            # Forecast with some error
            forecast_error = random.gauss(0, 1.5)
            forecast_temp = actual_temp - forecast_error
            
            delta = actual_temp - forecast_temp
            ensemble_std = abs(random.gauss(1.0, 0.5))
            confidence = max(0.3, min(0.95, 1.0 - ensemble_std / 5))
            
            weather_data.append(HistoricalWeatherPoint(
                date=current.strftime("%Y-%m-%d"),
                region=region,
                actual_temp=round(actual_temp, 1),
                forecast_temp=round(forecast_temp, 1),
                delta=round(delta, 2),
                ensemble_std=round(ensemble_std, 2),
                confidence=round(confidence, 2)
            ))
            
            current += timedelta(days=1)
        
        logger.info(f"Generated {len(weather_data)} weather data points "
                    f"({start_date} to {end_date})")
        return weather_data
    
    def _generate_signal(self, weather: HistoricalWeatherPoint,
                          threshold: float = 2.0) -> Tuple[str, float]:
        """Generate enhanced trading signal using ensemble consensus and confidence
        
        Returns (action, confidence) tuple
        """
        abs_delta = abs(weather.delta)
        
        # ENSEMBLE CONSENSUS FILTERING - NEW
        ensemble_consensus = self._calculate_ensemble_consensus(weather)
        if ensemble_consensus < 0.7:  # Require 70% consensus
            return "HOLD", weather.confidence
        
        # WEATHER PATTERN WEIGHTING - NEW
        pattern_weight = self._calculate_pattern_weight(weather)
        if pattern_weight < 0.8:  # Require strong weather pattern
            return "HOLD", weather.confidence
        
        # Dynamic threshold based on ensemble confidence
        if weather.confidence > 0.8:
            dynamic_threshold = threshold * 0.8  # Lower threshold for high confidence
        elif weather.confidence < 0.5:
            dynamic_threshold = threshold * 1.5  # Higher threshold for low confidence
        else:
            dynamic_threshold = threshold
        
        # Ensemble spread adjustment
        spread_factor = 1.0
        if hasattr(weather, 'ensemble_std') and weather.ensemble_std > 0:
            # High uncertainty = more conservative
            spread_factor = max(0.5, 1.0 - (weather.ensemble_std / 5.0))
        
        # Boost confidence for high consensus
        consensus_boost = min(1.2, 1.0 + (ensemble_consensus - 0.7) * 0.5)
        adjusted_confidence = weather.confidence * spread_factor * consensus_boost
        
        if abs_delta < dynamic_threshold:
            return "HOLD", adjusted_confidence
        
        # Enhanced signal logic with consensus weighting
        if weather.delta > dynamic_threshold:
            # Strong BUY signal with high confidence and consensus
            if adjusted_confidence > 0.7 and ensemble_consensus > 0.8:
                return "BUY", min(0.95, adjusted_confidence * 1.3)
            else:
                return "BUY", adjusted_confidence
        elif weather.delta < -dynamic_threshold:
            # Strong SELL signal with high confidence and consensus
            if adjusted_confidence > 0.7 and ensemble_consensus > 0.8:
                return "SELL", min(0.95, adjusted_confidence * 1.3)
            else:
                return "SELL", adjusted_confidence
        
        return "HOLD", adjusted_confidence
    
    def _calculate_ensemble_consensus(self, weather: HistoricalWeatherPoint) -> float:
        """Calculate ensemble consensus from weather data"""
        
        # Base consensus from confidence
        base_consensus = weather.confidence
        
        # Adjust based on ensemble spread if available
        if hasattr(weather, 'ensemble_std') and weather.ensemble_std > 0:
            # Lower spread = higher consensus
            spread_adjustment = max(0.5, 1.0 - (weather.ensemble_std / 10.0))
            base_consensus *= spread_adjustment
        
        # Adjust based on delta magnitude (stronger signals = higher consensus)
        delta_strength = min(1.0, abs(weather.delta) / 5.0)
        consensus_boost = 1.0 + (delta_strength * 0.2)
        
        final_consensus = min(0.95, base_consensus * consensus_boost)
        return final_consensus
    
    def _calculate_pattern_weight(self, weather: HistoricalWeatherPoint) -> float:
        """Calculate weather pattern weight for signal strength"""
        
        # Base weight from temperature anomaly
        temp_anomaly = abs(weather.actual_temp - 15.0)  # Tokyo average ~15°C
        
        # Pattern detection
        if temp_anomaly > 10.0:  # Extreme temperature
            pattern_weight = 1.3  # Heat wave or cold snap
        elif temp_anomaly > 5.0:  # Strong anomaly
            pattern_weight = 1.2  # Unusual warming/cooling
        elif temp_anomaly > 2.0:  # Moderate anomaly
            pattern_weight = 1.1  # Notable pattern
        else:
            pattern_weight = 1.0  # Normal conditions
        
        # Adjust based on delta strength
        delta_strength = min(1.0, abs(weather.delta) / 3.0)
        pattern_weight *= (1.0 + delta_strength * 0.2)
        
        # Adjust based on confidence
        confidence_factor = 0.8 + (weather.confidence * 0.4)
        pattern_weight *= confidence_factor
        
        return min(1.5, pattern_weight)
    
    async def generate_weathernext2_signal(self, location: str) -> Tuple[str, float]:
        """Generate enhanced trading signal using WeatherNext 2 real-time data"""
        
        try:
            # Get comprehensive trading signals from WeatherNext 2
            signals_data = await self.weathernext2.get_trading_signals(location)
            
            if "error" in signals_data:
                logger.warning(f"WeatherNext 2 error: {signals_data['error']}")
                return "HOLD", 0.5
            
            signals = signals_data["signals"]
            ensemble = signals_data["ensemble"]
            
            # Enhanced confidence calculation with real ensemble data
            base_confidence = signals["final_confidence"]
            
            # Apply our existing consensus and pattern filters
            if ensemble.consensus < 0.7:
                return "HOLD", base_confidence
            
            # Check signal strength
            if signals["signal_strength"] < 0.3:
                return "HOLD", base_confidence
            
            # Enhanced signal with WeatherNext 2 data
            action = signals["temperature_signal"]
            confidence = min(0.95, base_confidence * 1.1)  # Boost for real data
            
            return action, confidence
            
        except Exception as e:
            logger.error(f"Error generating WeatherNext 2 signal: {e}")
            return "HOLD", 0.5
    
    def _generate_ensemble_signal(self, ensemble_forecast, threshold: float = 2.0) -> Tuple[str, float]:
        """Generate signal from full ensemble forecast data"""
        
        # Use ensemble consensus and spread
        consensus = ensemble_forecast.consensus
        spread = ensemble_forecast.spread
        
        # Calculate ensemble-based confidence
        ensemble_confidence = (consensus + (1.0 - min(spread / 10.0, 1.0))) / 2.0
        
        # Find ensemble members that exceed threshold
        extreme_members = [m for m in ensemble_forecast.members 
                         if abs(m.temperature - ensemble_forecast.mean_temp) > threshold]
        
        if len(extreme_members) / len(ensemble_forecast.members) > 0.6:
            # Majority of ensemble agrees on extreme
            if ensemble_forecast.mean_temp > 20:  # Warm conditions
                return "BUY", ensemble_confidence
            else:  # Cool conditions
                return "SELL", ensemble_confidence
        elif len(extreme_members) / len(ensemble_forecast.members) > 0.3:
            # Significant minority agrees
            if ensemble_forecast.mean_temp > 20:
                return "BUY", ensemble_confidence * 0.8
            else:
                return "SELL", ensemble_confidence * 0.8
        else:
            return "HOLD", ensemble_confidence
    
    def run_backtest(self, start_date: str = "2024-01-01",
                     end_date: str = "2025-12-31",
                     region: str = "Tokyo",
                     signal_threshold: float = 2.0,
                     position_size_pct: float = 0.02,
                     stop_loss_pct: float = 0.10,
                     take_profit_pct: float = 0.20,
                     max_holding_days: int = 7) -> BacktestResult:
        """Run a complete backtest simulation"""
        
        # Generate data
        weather_data = self.generate_historical_weather(start_date, end_date, region)
        self.price_model = WeatherPriceModel()
        
        # State
        capital = self.initial_capital
        equity_curve = [capital]
        trades: List[BacktestTrade] = []
        open_position: Optional[BacktestTrade] = None
        peak_equity = capital
        max_drawdown = 0.0
        daily_returns: List[float] = []
        prev_equity = capital
        
        for weather in weather_data:
            # Generate price
            price = self.price_model.generate_price(weather.delta, weather.confidence)
            
            # Check open position for exit conditions
            if open_position:
                holding_days = (datetime.strptime(weather.date, "%Y-%m-%d") -
                               datetime.strptime(open_position.date, "%Y-%m-%d")).days
                
                pnl_pct = 0.0
                if open_position.action == "BUY":
                    pnl_pct = (price - open_position.price) / open_position.price
                elif open_position.action == "SELL":
                    pnl_pct = (open_position.price - price) / open_position.price
                
                # Exit conditions
                should_exit = False
                if pnl_pct <= -stop_loss_pct:
                    should_exit = True  # Stop loss
                elif pnl_pct >= take_profit_pct:
                    should_exit = True  # Take profit
                elif holding_days >= max_holding_days:
                    should_exit = True  # Max holding period
                
                if should_exit:
                    # Apply slippage
                    slippage = price * self.slippage_bps / 10000
                    exit_price = price - slippage if open_position.action == "BUY" else price + slippage
                    exit_fee = open_position.size * exit_price * self.fee_rate
                    
                    if open_position.action == "BUY":
                        pnl = (exit_price - open_position.price) * open_position.size - open_position.fee - exit_fee
                    else:
                        pnl = (open_position.price - exit_price) * open_position.size - open_position.fee - exit_fee
                    
                    open_position.pnl = round(pnl, 4)
                    open_position.exit_price = round(exit_price, 4)
                    open_position.exit_date = weather.date
                    open_position.holding_days = holding_days
                    
                    trades.append(open_position)
                    capital += pnl
                    open_position = None
            
            # Generate signal for new position
            if not open_position:
                action, confidence = self._generate_signal(weather, signal_threshold)
                
                if action != "HOLD":
                    position_size = capital * position_size_pct / price if price > 0 else 0
                    
                    if position_size > 0:
                        # Apply slippage
                        slippage = price * self.slippage_bps / 10000
                        entry_price = price + slippage if action == "BUY" else price - slippage
                        fee = position_size * entry_price * self.fee_rate
                        
                        open_position = BacktestTrade(
                            date=weather.date,
                            action=action,
                            price=round(entry_price, 4),
                            size=round(position_size, 2),
                            cost=round(position_size * entry_price, 4),
                            fee=round(fee, 4),
                            weather_delta=weather.delta,
                            confidence=weather.confidence
                        )
            
            # Track equity
            equity_curve.append(round(capital, 2))
            
            # Track drawdown
            if capital > peak_equity:
                peak_equity = capital
            drawdown = peak_equity - capital
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            
            # Track daily returns
            daily_return = (capital - prev_equity) / prev_equity if prev_equity > 0 else 0
            daily_returns.append(daily_return)
            prev_equity = capital
        
        # Close any remaining position at last price
        if open_position:
            last_price = self.price_model.current_price
            if open_position.action == "BUY":
                pnl = (last_price - open_position.price) * open_position.size - open_position.fee
            else:
                pnl = (open_position.price - last_price) * open_position.size - open_position.fee
            open_position.pnl = round(pnl, 4)
            open_position.exit_price = round(last_price, 4)
            open_position.exit_date = weather_data[-1].date
            trades.append(open_position)
            capital += pnl
        
        # Calculate metrics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        total_pnl = capital - self.initial_capital
        
        avg_daily_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0
        std_daily_return = (sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5 if daily_returns else 1
        downside_returns = [r for r in daily_returns if r < 0]
        std_downside = (sum(r ** 2 for r in downside_returns) / len(downside_returns)) ** 0.5 if downside_returns else 1
        
        sharpe = (avg_daily_return / std_daily_return * math.sqrt(252)) if std_daily_return > 0 else 0
        sortino = (avg_daily_return / std_downside * math.sqrt(252)) if std_downside > 0 else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return BacktestResult(
            strategy_name=f"WeatherDelta_{region}_t{signal_threshold}",
            start_date=start_date,
            end_date=end_date,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=len(winning_trades) / len(trades) if trades else 0,
            total_pnl=round(total_pnl, 2),
            total_return_pct=round(total_pnl / self.initial_capital * 100, 2),
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_pct=round(max_drawdown / peak_equity * 100, 2) if peak_equity > 0 else 0,
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            profit_factor=round(profit_factor, 2),
            avg_trade_pnl=round(total_pnl / len(trades), 2) if trades else 0,
            avg_win=round(gross_profit / len(winning_trades), 2) if winning_trades else 0,
            avg_loss=round(-gross_loss / len(losing_trades), 2) if losing_trades else 0,
            avg_holding_days=round(sum(t.holding_days for t in trades) / len(trades), 1) if trades else 0,
            total_fees=round(sum(t.fee for t in trades), 2),
            trades=trades,
            equity_curve=equity_curve
        )
    
    def print_report(self, result: BacktestResult):
        """Print a formatted backtest report"""
        print("\n" + "=" * 60)
        print(f"📊 BACKTEST REPORT: {result.strategy_name}")
        print("=" * 60)
        
        print(f"\n📅 Period: {result.start_date} to {result.end_date}")
        print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        
        print(f"\n--- PERFORMANCE ---")
        pnl_emoji = "🟢" if result.total_pnl > 0 else "🔴"
        print(f"{pnl_emoji} Total P&L: ${result.total_pnl:+,.2f} ({result.total_return_pct:+.2f}%)")
        print(f"📉 Max Drawdown: ${result.max_drawdown:,.2f} ({result.max_drawdown_pct:.2f}%)")
        print(f"📊 Sharpe Ratio: {result.sharpe_ratio}")
        print(f"📊 Sortino Ratio: {result.sortino_ratio}")
        print(f"📊 Profit Factor: {result.profit_factor}")
        
        print(f"\n--- TRADES ---")
        print(f"Total Trades: {result.total_trades}")
        print(f"✅ Winning: {result.winning_trades} | ❌ Losing: {result.losing_trades}")
        print(f"🎯 Win Rate: {result.win_rate:.1%}")
        print(f"📈 Avg Win: ${result.avg_win:+.2f} | 📉 Avg Loss: ${result.avg_loss:.2f}")
        print(f"📊 Avg Trade P&L: ${result.avg_trade_pnl:+.2f}")
        print(f"📅 Avg Holding: {result.avg_holding_days} days")
        print(f"💳 Total Fees: ${result.total_fees:.2f}")
        
        # Assessment
        print(f"\n--- ASSESSMENT ---")
        if result.sharpe_ratio > 1.0 and result.win_rate > 0.55 and result.max_drawdown_pct < 15:
            print("🏆 EXCELLENT - Strategy is production-ready")
        elif result.sharpe_ratio > 0.5 and result.win_rate > 0.50:
            print("✅ GOOD - Strategy shows promise, needs optimization")
        elif result.total_pnl > 0:
            print("⚠️ MARGINAL - Positive returns but needs improvement")
        else:
            print("❌ POOR - Strategy needs significant rework")
        
        print("=" * 60)
    
    def run_parameter_sweep(self, start_date: str = "2024-01-01",
                            end_date: str = "2025-12-31") -> List[BacktestResult]:
        """Run backtests across multiple parameter combinations"""
        results = []
        
        thresholds = [1.0, 1.5, 2.0, 2.5, 3.0]
        position_sizes = [0.01, 0.02, 0.03, 0.05]
        
        print(f"\n🔬 Running parameter sweep: {len(thresholds) * len(position_sizes)} combinations...")
        
        for threshold in thresholds:
            for pos_size in position_sizes:
                result = self.run_backtest(
                    start_date=start_date,
                    end_date=end_date,
                    signal_threshold=threshold,
                    position_size_pct=pos_size
                )
                results.append(result)
        
        # Sort by Sharpe ratio
        results.sort(key=lambda r: r.sharpe_ratio, reverse=True)
        
        print(f"\n📊 TOP 5 PARAMETER COMBINATIONS:")
        print(f"{'Strategy':<40} {'P&L':>10} {'Win%':>8} {'Sharpe':>8} {'MaxDD':>8}")
        print("-" * 80)
        for r in results[:5]:
            print(f"{r.strategy_name:<40} ${r.total_pnl:>+8.2f} {r.win_rate:>7.1%} "
                  f"{r.sharpe_ratio:>7.2f} {r.max_drawdown_pct:>6.1f}%")
        
        return results


    def load_real_weather(self, data_file: str, region: str = "Tokyo") -> List[HistoricalWeatherPoint]:
        """Load real NOAA weather data from data_fetcher output and convert to backtest format.
        
        Uses a rolling 7-day average as "forecast" and daily actual as "actual"
        to compute realistic deltas (forecast error).
        """
        with open(data_file, "r") as f:
            raw = json.load(f)
        
        records = raw.get("weather", {}).get(region, [])
        if not records:
            logger.warning(f"No weather data for {region} in {data_file}")
            return []
        
        # Build rolling 7-day average as proxy for forecast
        temps = [r["temp_avg"] for r in records]
        weather_data = []
        
        for i, record in enumerate(records):
            actual = record["temp_avg"]
            
            # Rolling 7-day mean as forecast proxy
            window_start = max(0, i - 7)
            window = temps[window_start:i] if i > 0 else [actual]
            forecast = sum(window) / len(window)
            
            delta = actual - forecast
            
            # Estimate ensemble spread from recent variability
            if i >= 7:
                recent = temps[i-7:i]
                import statistics
                ensemble_std = statistics.stdev(recent) if len(recent) > 1 else 1.0
            else:
                ensemble_std = 1.0
            
            confidence = max(0.3, min(0.95, 1.0 - ensemble_std / 10))
            
            weather_data.append(HistoricalWeatherPoint(
                date=record["date"],
                region=region,
                actual_temp=round(actual, 1),
                forecast_temp=round(forecast, 1),
                delta=round(delta, 2),
                ensemble_std=round(ensemble_std, 2),
                confidence=round(confidence, 2)
            ))
        
        logger.info(f"Loaded {len(weather_data)} real weather points for {region}")
        return weather_data
    
    def run_real_backtest(self, data_file: str, region: str = "Tokyo",
                          signal_threshold: float = 2.0,
                          position_size_pct: float = 0.02,
                          stop_loss_pct: float = 0.10,
                          take_profit_pct: float = 0.20,
                          max_holding_days: int = 7) -> BacktestResult:
        """Run backtest using real NOAA weather data"""
        
        weather_data = self.load_real_weather(data_file, region)
        if not weather_data:
            raise ValueError(f"No real weather data available for {region}")
        
        self.price_model = WeatherPriceModel()
        
        capital = self.initial_capital
        equity_curve = [capital]
        trades: List[BacktestTrade] = []
        open_position: Optional[BacktestTrade] = None
        peak_equity = capital
        max_drawdown = 0.0
        daily_returns: List[float] = []
        prev_equity = capital
        
        for weather in weather_data:
            price = self.price_model.generate_price(weather.delta, weather.confidence)
            
            if open_position:
                holding_days = (datetime.strptime(weather.date, "%Y-%m-%d") -
                               datetime.strptime(open_position.date, "%Y-%m-%d")).days
                
                if open_position.action == "BUY":
                    pnl_pct = (price - open_position.price) / open_position.price
                elif open_position.action == "SELL":
                    pnl_pct = (open_position.price - price) / open_position.price
                else:
                    pnl_pct = 0.0
                
                should_exit = (pnl_pct <= -stop_loss_pct or 
                              pnl_pct >= take_profit_pct or 
                              holding_days >= max_holding_days)
                
                if should_exit:
                    slippage = price * self.slippage_bps / 10000
                    exit_price = price - slippage if open_position.action == "BUY" else price + slippage
                    exit_fee = open_position.size * exit_price * self.fee_rate
                    
                    if open_position.action == "BUY":
                        pnl = (exit_price - open_position.price) * open_position.size - open_position.fee - exit_fee
                    else:
                        pnl = (open_position.price - exit_price) * open_position.size - open_position.fee - exit_fee
                    
                    open_position.pnl = round(pnl, 4)
                    open_position.exit_price = round(exit_price, 4)
                    open_position.exit_date = weather.date
                    open_position.holding_days = holding_days
                    trades.append(open_position)
                    capital += pnl
                    open_position = None
            
            if not open_position:
                action, confidence = self._generate_signal(weather, signal_threshold)
                
                if action != "HOLD":
                    position_size = capital * position_size_pct / price if price > 0 else 0
                    
                    if position_size > 0:
                        slippage = price * self.slippage_bps / 10000
                        entry_price = price + slippage if action == "BUY" else price - slippage
                        fee = position_size * entry_price * self.fee_rate
                        
                        open_position = BacktestTrade(
                            date=weather.date,
                            action=action,
                            price=round(entry_price, 4),
                            size=round(position_size, 2),
                            cost=round(position_size * entry_price, 4),
                            fee=round(fee, 4),
                            weather_delta=weather.delta,
                            confidence=weather.confidence
                        )
            
            equity_curve.append(round(capital, 2))
            if capital > peak_equity:
                peak_equity = capital
            drawdown = peak_equity - capital
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            daily_return = (capital - prev_equity) / prev_equity if prev_equity > 0 else 0
            daily_returns.append(daily_return)
            prev_equity = capital
        
        # Close remaining position
        if open_position:
            last_price = self.price_model.current_price
            if open_position.action == "BUY":
                pnl = (last_price - open_position.price) * open_position.size - open_position.fee
            else:
                pnl = (open_position.price - last_price) * open_position.size - open_position.fee
            open_position.pnl = round(pnl, 4)
            open_position.exit_price = round(last_price, 4)
            open_position.exit_date = weather_data[-1].date
            trades.append(open_position)
            capital += pnl
        
        # Calculate metrics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        total_pnl = capital - self.initial_capital
        
        avg_daily_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0
        std_daily = (sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5 if daily_returns else 1
        downside = [r for r in daily_returns if r < 0]
        std_down = (sum(r ** 2 for r in downside) / len(downside)) ** 0.5 if downside else 1
        
        sharpe = (avg_daily_return / std_daily * math.sqrt(252)) if std_daily > 0 else 0
        sortino = (avg_daily_return / std_down * math.sqrt(252)) if std_down > 0 else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        start_date = weather_data[0].date
        end_date = weather_data[-1].date
        
        return BacktestResult(
            strategy_name=f"REAL_{region}_t{signal_threshold}",
            start_date=start_date,
            end_date=end_date,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=len(winning_trades) / len(trades) if trades else 0,
            total_pnl=round(total_pnl, 2),
            total_return_pct=round(total_pnl / self.initial_capital * 100, 2),
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_pct=round(max_drawdown / peak_equity * 100, 2) if peak_equity > 0 else 0,
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            profit_factor=round(profit_factor, 2),
            avg_trade_pnl=round(total_pnl / len(trades), 2) if trades else 0,
            avg_win=round(gross_profit / len(winning_trades), 2) if winning_trades else 0,
            avg_loss=round(-gross_loss / len(losing_trades), 2) if losing_trades else 0,
            avg_holding_days=round(sum(t.holding_days for t in trades) / len(trades), 1) if trades else 0,
            total_fees=round(sum(t.fee for t in trades), 2),
            trades=trades,
            equity_curve=equity_curve
        )
    
    def run_optimized_backtest(self, data_file: str, region: str = "Tokyo",
                             signal_threshold: float = 2.0,
                             base_position_size_pct: float = 0.02) -> BacktestResult:
        """Run backtest with optimized risk/reward management"""
        
        weather_data = self.load_real_weather(data_file, region)
        if not weather_data:
            raise ValueError(f"No real weather data available for {region}")
        
        self.price_model = WeatherPriceModel()
        
        capital = self.initial_capital
        equity_curve = [capital]
        trades: List[BacktestTrade] = []
        open_position: Optional[BacktestTrade] = None
        peak_equity = capital
        max_drawdown = 0.0
        daily_returns: List[float] = []
        prev_equity = capital
        
        # Track price history for volatility calculation
        price_history = []
        
        for i, weather in enumerate(weather_data):
            price = self.price_model.generate_price(weather.delta, weather.confidence)
            price_history.append(price)
            
            # Calculate market conditions
            if len(price_history) >= 10:
                conditions = self.risk_optimizer.calculate_market_conditions(
                    price_history, weather.ensemble_std, weather.confidence
                )
            else:
                # Default conditions for early trades
                from risk_reward_optimizer import MarketConditions
                conditions = MarketConditions(
                    volatility=0.02,
                    trend_strength=0.01,
                    ensemble_spread=weather.ensemble_std,
                    weather_confidence=weather.confidence,
                    pattern_type=None
                )
            
            if open_position:
                # Track highest/lowest prices for trailing stops
                if open_position.action == "BUY":
                    if not hasattr(open_position, 'highest_price'):
                        open_position.highest_price = open_position.price
                    open_position.highest_price = max(open_position.highest_price, price)
                    highest_price = open_position.highest_price
                    lowest_price = None
                else:  # SELL
                    if not hasattr(open_position, 'lowest_price'):
                        open_position.lowest_price = open_position.price
                    open_position.lowest_price = min(open_position.lowest_price, price)
                    highest_price = None
                    lowest_price = open_position.lowest_price
                
                # Get exit strategy for this trade
                strategy = self.risk_optimizer.optimize_exit_strategy(
                    conditions, weather.confidence, open_position.action
                )
                
                # Check if should exit
                should_exit, exit_reason = self.risk_optimizer.should_exit_trade(
                    open_position.price, price, open_position.date, weather.date,
                    strategy, highest_price, lowest_price
                )
                
                if should_exit:
                    # Calculate exit price with slippage
                    slippage = price * self.slippage_bps / 10000
                    if open_position.action == "BUY":
                        exit_price = price - slippage
                        pnl = (exit_price - open_position.price) * open_position.size - open_position.fee
                    else:  # SELL
                        exit_price = price + slippage
                        pnl = (open_position.price - exit_price) * open_position.size - open_position.fee
                    
                    exit_fee = open_position.size * exit_price * self.fee_rate
                    pnl -= exit_fee
                    
                    # Calculate holding days
                    entry_dt = datetime.strptime(open_position.date, "%Y-%m-%d")
                    current_dt = datetime.strptime(weather.date, "%Y-%m-%d")
                    holding_days = (current_dt - entry_dt).days
                    
                    open_position.pnl = round(pnl, 4)
                    open_position.exit_price = round(exit_price, 4)
                    open_position.exit_date = weather.date
                    open_position.holding_days = holding_days
                    open_position.exit_reason = exit_reason
                    trades.append(open_position)
                    capital += pnl
                    open_position = None
            
            if not open_position:
                # Generate signal
                action, confidence = self._generate_signal(weather, signal_threshold)
                
                if action != "HOLD":
                    # Calculate optimized position size
                    base_position_size = capital * base_position_size_pct
                    strategy = self.risk_optimizer.optimize_exit_strategy(
                        conditions, confidence, action
                    )
                    optimized_size = self.risk_optimizer.calculate_dynamic_position_size(
                        base_position_size, conditions, strategy
                    )
                    
                    position_size = optimized_size / price if price > 0 else 0
                    
                    if position_size > 0:
                        slippage = price * self.slippage_bps / 10000
                        entry_price = price + slippage if action == "BUY" else price - slippage
                        fee = position_size * entry_price * self.fee_rate
                        
                        open_position = BacktestTrade(
                            date=weather.date,
                            action=action,
                            price=round(entry_price, 4),
                            size=round(position_size, 2),
                            cost=round(position_size * entry_price, 4),
                            fee=round(fee, 4),
                            weather_delta=weather.delta,
                            confidence=weather.confidence
                        )
            
            equity_curve.append(round(capital, 2))
            if capital > peak_equity:
                peak_equity = capital
            drawdown = peak_equity - capital
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            daily_return = (capital - prev_equity) / prev_equity if prev_equity > 0 else 0
            daily_returns.append(daily_return)
            prev_equity = capital
        
        # Close remaining position
        if open_position:
            last_price = self.price_model.current_price
            if open_position.action == "BUY":
                pnl = (last_price - open_position.price) * open_position.size - open_position.fee
            else:
                pnl = (open_position.price - last_price) * open_position.size - open_position.fee
            open_position.pnl = round(pnl, 4)
            open_position.exit_price = round(last_price, 4)
            open_position.exit_date = weather_data[-1].date
            open_position.holding_days = 1
            open_position.exit_reason = "end_of_data"
            trades.append(open_position)
            capital += pnl
        
        # Calculate metrics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        total_pnl = capital - self.initial_capital
        
        avg_daily_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0
        std_daily = (sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5 if daily_returns else 1
        downside = [r for r in daily_returns if r < 0]
        std_down = (sum(r ** 2 for r in downside) / len(downside)) ** 0.5 if downside else 1
        
        sharpe = (avg_daily_return / std_daily * math.sqrt(252)) if std_daily > 0 else 0
        sortino = (avg_daily_return / std_down * math.sqrt(252)) if std_down > 0 else 0
        
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        start_date = weather_data[0].date
        end_date = weather_data[-1].date
        
        return BacktestResult(
            strategy_name=f"OPTIMIZED_{region}_t{signal_threshold}",
            start_date=start_date,
            end_date=end_date,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=len(winning_trades) / len(trades) if trades else 0,
            total_pnl=round(total_pnl, 2),
            total_return_pct=round(total_pnl / self.initial_capital * 100, 2),
            max_drawdown=round(max_drawdown, 2),
            max_drawdown_pct=round(max_drawdown / peak_equity * 100, 2) if peak_equity > 0 else 0,
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            profit_factor=round(profit_factor, 2),
            avg_trade_pnl=round(total_pnl / len(trades), 2) if trades else 0,
            avg_win=round(gross_profit / len(winning_trades), 2) if winning_trades else 0,
            avg_loss=round(-gross_loss / len(losing_trades), 2) if losing_trades else 0,
            avg_holding_days=round(sum(t.holding_days for t in trades) / len(trades), 1) if trades else 0,
            total_fees=round(sum(t.fee for t in trades), 2),
            trades=trades,
            equity_curve=equity_curve
        )


def main():
    """Run backtesting with real NOAA data"""
    import os
    
    print("🚀 PROJECT SENTINEL - Backtesting Engine (REAL DATA)")
    
    data_file = os.path.join(os.path.dirname(__file__), "..", "data", "sentinel_backtest_data.json")
    
    engine = BacktestingEngine(initial_capital=10000)
    
    if os.path.exists(data_file):
        print("\n📊 REAL DATA BACKTEST (NOAA Tokyo Weather)")
        print("=" * 60)
        
        result = engine.run_real_backtest(
            data_file=data_file,
            region="Tokyo",
            signal_threshold=2.0,
            position_size_pct=0.02
        )
        engine.print_report(result)
        
        # Parameter sweep with real data
        thresholds = [1.5, 2.0, 2.5, 3.0, 4.0]
        position_sizes = [0.01, 0.02, 0.03, 0.05]
        
        print(f"\n🔬 REAL DATA PARAMETER SWEEP ({len(thresholds) * len(position_sizes)} combos)...")
        results = []
        for t in thresholds:
            for ps in position_sizes:
                r = engine.run_real_backtest(data_file, "Tokyo", t, ps)
                results.append(r)
        
        results.sort(key=lambda r: r.sharpe_ratio, reverse=True)
        
        print(f"\n📊 TOP 5 STRATEGIES (REAL DATA):")
        print(f"{'Strategy':<35} {'P&L':>10} {'Win%':>8} {'Sharpe':>8} {'MaxDD':>8} {'Trades':>7}")
        print("-" * 80)
        for r in results[:5]:
            print(f"{r.strategy_name:<35} ${r.total_pnl:>+8.2f} {r.win_rate:>7.1%} "
                  f"{r.sharpe_ratio:>7.2f} {r.max_drawdown_pct:>6.1f}% {r.total_trades:>6}")
        
        # Export best result
        best = results[0]
        export = {
            "strategy": best.strategy_name,
            "data_source": "NOAA GSOD (Real)",
            "period": f"{best.start_date} to {best.end_date}",
            "total_pnl": best.total_pnl,
            "return_pct": best.total_return_pct,
            "sharpe": best.sharpe_ratio,
            "sortino": best.sortino_ratio,
            "win_rate": round(best.win_rate, 4),
            "max_drawdown_pct": best.max_drawdown_pct,
            "profit_factor": best.profit_factor,
            "total_trades": best.total_trades,
            "avg_holding_days": best.avg_holding_days
        }
        print(f"\n📄 Best strategy: {json.dumps(export, indent=2)}")
    else:
        print(f"⚠️ No real data found at {data_file}")
        print("   Run: python data_fetcher.py to fetch real NOAA weather data first")
    
    print("\n✅ Backtesting complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
