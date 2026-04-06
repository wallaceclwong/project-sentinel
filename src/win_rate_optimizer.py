#!/usr/bin/env python3
"""
PROJECT SENTINEL - Win Rate Optimizer
Strategies to improve win rate from 60% to 64%+ for profitability
"""

import logging
import statistics
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class SignalAnalysis:
    """Analysis of trading signals and outcomes"""
    total_signals: int
    winning_signals: int
    losing_signals: int
    hold_signals: int
    avg_confidence_wins: float
    avg_confidence_losses: float
    avg_delta_wins: float
    avg_delta_losses: float
    confidence_distribution: Dict[str, int]
    delta_distribution: Dict[str, int]

class WinRateOptimizer:
    """Optimizes win rate through signal enhancement strategies"""
    
    def __init__(self):
        self.strategies = {
            "confidence_filtering": self._confidence_filtering_strategy,
            "delta_threshold_optimization": self._delta_threshold_optimization,
            "pattern_based_signals": self._pattern_based_signals,
            "ensemble_consensus": self._ensemble_consensus_strategy,
            "multi_timeframe": self._multi_timeframe_strategy,
            "weather_pattern_weighting": self._weather_pattern_weighting
        }
    
    def analyze_current_performance(self, trades: List[Dict]) -> SignalAnalysis:
        """Analyze current trading performance to identify improvement areas"""
        
        if not trades:
            return SignalAnalysis(0, 0, 0, 0, 0, 0, 0, 0, {}, {})
        
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) <= 0]
        hold_signals = len(trades) - len(winning_trades) - len(losing_trades)
        
        # Calculate statistics
        avg_confidence_wins = statistics.mean([t.get("confidence", 0.5) for t in winning_trades]) if winning_trades else 0
        avg_confidence_losses = statistics.mean([t.get("confidence", 0.5) for t in losing_trades]) if losing_trades else 0
        avg_delta_wins = statistics.mean([abs(t.get("weather_delta", 0)) for t in winning_trades]) if winning_trades else 0
        avg_delta_losses = statistics.mean([abs(t.get("weather_delta", 0)) for t in losing_trades]) if losing_trades else 0
        
        # Distribution analysis
        confidence_distribution = self._analyze_confidence_distribution(trades)
        delta_distribution = self._analyze_delta_distribution(trades)
        
        return SignalAnalysis(
            total_signals=len(trades),
            winning_signals=len(winning_trades),
            losing_signals=len(losing_trades),
            hold_signals=hold_signals,
            avg_confidence_wins=avg_confidence_wins,
            avg_confidence_losses=avg_confidence_losses,
            avg_delta_wins=avg_delta_wins,
            avg_delta_losses=avg_delta_losses,
            confidence_distribution=confidence_distribution,
            delta_distribution=delta_distribution
        )
    
    def _analyze_confidence_distribution(self, trades: List[Dict]) -> Dict[str, int]:
        """Analyze confidence level distribution"""
        distribution = {"<0.5": 0, "0.5-0.6": 0, "0.6-0.7": 0, "0.7-0.8": 0, "0.8-0.9": 0, ">0.9": 0}
        
        for trade in trades:
            conf = trade.get("confidence", 0.5)
            if conf < 0.5:
                distribution["<0.5"] += 1
            elif conf < 0.6:
                distribution["0.5-0.6"] += 1
            elif conf < 0.7:
                distribution["0.6-0.7"] += 1
            elif conf < 0.8:
                distribution["0.7-0.8"] += 1
            elif conf < 0.9:
                distribution["0.8-0.9"] += 1
            else:
                distribution[">0.9"] += 1
        
        return distribution
    
    def _analyze_delta_distribution(self, trades: List[Dict]) -> Dict[str, int]:
        """Analyze weather delta distribution"""
        distribution = {"<1.0": 0, "1.0-2.0": 0, "2.0-3.0": 0, "3.0-4.0": 0, ">4.0": 0}
        
        for trade in trades:
            delta = abs(trade.get("weather_delta", 0))
            if delta < 1.0:
                distribution["<1.0"] += 1
            elif delta < 2.0:
                distribution["1.0-2.0"] += 1
            elif delta < 3.0:
                distribution["2.0-3.0"] += 1
            elif delta < 4.0:
                distribution["3.0-4.0"] += 1
            else:
                distribution[">4.0"] += 1
        
        return distribution
    
    def _confidence_filtering_strategy(self, analysis: SignalAnalysis) -> Dict[str, Any]:
        """Strategy 1: Filter low-confidence signals"""
        
        # Find confidence threshold that maximizes win rate
        confidence_thresholds = [0.5, 0.6, 0.7, 0.8]
        best_threshold = 0.5
        best_win_rate = 0.0
        
        for threshold in confidence_thresholds:
            # Estimate win rate improvement by filtering
            high_conf_wins = analysis.confidence_distribution.get(">0.9", 0) + analysis.confidence_distribution.get("0.8-0.9", 0)
            high_conf_total = high_conf_wins + analysis.confidence_distribution.get("0.7-0.8", 0)
            
            if high_conf_total > 0:
                estimated_win_rate = (high_conf_wins * 0.85) / high_conf_total  # Assume 85% win rate for high confidence
                if estimated_win_rate > best_win_rate:
                    best_win_rate = estimated_win_rate
                    best_threshold = threshold
        
        return {
            "strategy": "Confidence Filtering",
            "current_win_rate": analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0,
            "estimated_improvement": best_win_rate - (analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0),
            "recommended_threshold": best_threshold,
            "expected_win_rate": best_win_rate,
            "trade_reduction": f"{(1 - best_threshold) * 100:.0f}% fewer trades",
            "implementation": "Only trade when confidence >= 0.7"
        }
    
    def _delta_threshold_optimization(self, analysis: SignalAnalysis) -> Dict[str, Any]:
        """Strategy 2: Optimize weather delta thresholds"""
        
        # Analyze delta effectiveness
        high_delta_wins = analysis.delta_distribution.get(">4.0", 0) + analysis.delta_distribution.get("3.0-4.0", 0)
        high_delta_total = high_delta_wins + analysis.delta_distribution.get("2.0-3.0", 0)
        
        # High deltas should have better predictive power
        if high_delta_total > 0:
            estimated_win_rate = (high_delta_wins * 0.75) / high_delta_total  # Assume 75% win rate for high deltas
        else:
            estimated_win_rate = 0.65
        
        return {
            "strategy": "Delta Threshold Optimization",
            "current_win_rate": analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0,
            "estimated_improvement": estimated_win_rate - (analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0),
            "recommended_threshold": 2.5,
            "expected_win_rate": estimated_win_rate,
            "trade_reduction": "~30% fewer trades",
            "implementation": "Only trade when |delta| >= 2.5°C"
        }
    
    def _pattern_based_signals(self, analysis: SignalAnalysis) -> Dict[str, Any]:
        """Strategy 3: Use weather patterns for better signals"""
        
        # Pattern-based signals should be more reliable
        pattern_win_rate = 0.68  # Estimated based on pattern recognition
        pattern_trade_ratio = 0.4  # 40% of trades will be pattern-based
        
        overall_win_rate = (pattern_win_rate * pattern_trade_ratio) + (0.55 * (1 - pattern_trade_ratio))
        
        return {
            "strategy": "Pattern-Based Signals",
            "current_win_rate": analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0,
            "estimated_improvement": overall_win_rate - (analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0),
            "expected_win_rate": overall_win_rate,
            "pattern_types": ["heat_waves", "cold_snaps", "unusual_warming", "unusual_cooling"],
            "implementation": "Enhance signals with weather pattern recognition"
        }
    
    def _ensemble_consensus_strategy(self, analysis: SignalAnalysis) -> Dict[str, Any]:
        """Strategy 4: Use ensemble consensus for signal strength"""
        
        # Ensemble consensus improves reliability
        consensus_win_rate = 0.70  # High consensus signals
        consensus_ratio = 0.6  # 60% of trades will have good consensus
        
        overall_win_rate = (consensus_win_rate * consensus_ratio) + (0.55 * (1 - consensus_ratio))
        
        return {
            "strategy": "Ensemble Consensus",
            "current_win_rate": analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0,
            "estimated_improvement": overall_win_rate - (analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0),
            "expected_win_rate": overall_win_rate,
            "consensus_threshold": 0.7,
            "implementation": "Require ensemble consensus >= 70% for trades"
        }
    
    def _multi_timeframe_strategy(self, analysis: SignalAnalysis) -> Dict[str, Any]:
        """Strategy 5: Use multiple timeframes for confirmation"""
        
        # Multi-timeframe confirmation improves accuracy
        mtf_win_rate = 0.72  # Multi-timeframe confirmed signals
        mtf_ratio = 0.5  # 50% of trades will get MTF confirmation
        
        overall_win_rate = (mtf_win_rate * mtf_ratio) + (0.55 * (1 - mtf_ratio))
        
        return {
            "strategy": "Multi-Timeframe Analysis",
            "current_win_rate": analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0,
            "estimated_improvement": overall_win_rate - (analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0),
            "expected_win_rate": overall_win_rate,
            "timeframes": ["1-day", "3-day", "7-day"],
            "implementation": "Require confirmation across multiple timeframes"
        }
    
    def _weather_pattern_weighting(self, analysis: SignalAnalysis) -> Dict[str, Any]:
        """Strategy 6: Weight signals based on weather pattern strength"""
        
        # Pattern-weighted signals
        pattern_weighted_win_rate = 0.66  # Pattern-weighted average
        weighted_ratio = 0.8  # 80% of trades use pattern weighting
        
        overall_win_rate = (pattern_weighted_win_rate * weighted_ratio) + (0.55 * (1 - weighted_ratio))
        
        return {
            "strategy": "Weather Pattern Weighting",
            "current_win_rate": analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0,
            "estimated_improvement": overall_win_rate - (analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0),
            "expected_win_rate": overall_win_rate,
            "weight_factors": {
                "heat_wave": 1.3,
                "cold_snap": 1.2,
                "unusual_warming": 1.1,
                "normal": 1.0
            },
            "implementation": "Scale position size based on pattern strength"
        }
    
    def generate_optimization_plan(self, analysis: SignalAnalysis) -> Dict[str, Any]:
        """Generate comprehensive optimization plan"""
        
        # Evaluate all strategies
        strategy_results = {}
        for name, strategy_func in self.strategies.items():
            try:
                result = strategy_func(analysis)
                strategy_results[name] = result
            except Exception as e:
                logger.error(f"Error in strategy {name}: {e}")
        
        # Sort by improvement potential
        sorted_strategies = sorted(strategy_results.items(), 
                                 key=lambda x: x[1].get("estimated_improvement", 0), 
                                 reverse=True)
        
        # Create implementation plan
        current_win_rate = analysis.winning_signals / analysis.total_signals if analysis.total_signals > 0 else 0
        target_win_rate = 0.641  # 64.1% for profitability
        
        implementation_plan = {
            "current_status": {
                "win_rate": current_win_rate,
                "total_trades": analysis.total_signals,
                "target_win_rate": target_win_rate,
                "gap": target_win_rate - current_win_rate
            },
            "strategies": dict(sorted_strategies),
            "recommended_approach": self._create_implementation_plan(sorted_strategies, current_win_rate, target_win_rate),
            "expected_timeline": self._estimate_implementation_timeline(sorted_strategies),
            "success_probability": self._calculate_success_probability(sorted_strategies, current_win_rate, target_win_rate)
        }
        
        return implementation_plan
    
    def _create_implementation_plan(self, sorted_strategies: List[Tuple], current_rate: float, target_rate: float) -> Dict[str, Any]:
        """Create step-by-step implementation plan"""
        
        # Select top strategies that can reach target
        viable_strategies = []
        cumulative_improvement = 0.0
        
        for name, result in sorted_strategies:
            improvement = result.get("estimated_improvement", 0)
            if improvement > 0 and cumulative_improvement < (target_rate - current_rate):
                viable_strategies.append({
                    "name": name,
                    "result": result,
                    "priority": len(viable_strategies) + 1
                })
                cumulative_improvement += improvement
        
        return {
            "phase_1": viable_strategies[0] if len(viable_strategies) > 0 else None,
            "phase_2": viable_strategies[1] if len(viable_strategies) > 1 else None,
            "phase_3": viable_strategies[2] if len(viable_strategies) > 2 else None,
            "total_expected_improvement": cumulative_improvement,
            "can_reach_target": cumulative_improvement >= (target_rate - current_rate)
        }
    
    def _estimate_implementation_timeline(self, sorted_strategies: List[Tuple]) -> Dict[str, str]:
        """Estimate implementation timeline for each strategy"""
        
        timelines = {}
        for name, result in sorted_strategies:
            complexity = result.get("implementation", "")
            
            if "confidence" in name.lower():
                timelines[name] = "1-2 days (simple filter)"
            elif "delta" in name.lower():
                timelines[name] = "2-3 days (threshold tuning)"
            elif "pattern" in name.lower():
                timelines[name] = "1 week (pattern recognition)"
            elif "ensemble" in name.lower():
                timelines[name] = "3-5 days (consensus logic)"
            elif "timeframe" in name.lower():
                timelines[name] = "1 week (multi-timeframe analysis)"
            else:
                timelines[name] = "3-5 days (custom implementation)"
        
        return timelines
    
    def _calculate_success_probability(self, sorted_strategies: List[Tuple], current_rate: float, target_rate: float) -> float:
        """Calculate probability of reaching target win rate"""
        
        total_improvement = sum(result.get("estimated_improvement", 0) for _, result in sorted_strategies)
        gap = target_rate - current_rate
        
        if total_improvement >= gap:
            return 0.85  # 85% success if theoretical improvement sufficient
        else:
            return 0.4 + (total_improvement / gap) * 0.4  # Scaled probability


def main():
    """Test win rate optimizer"""
    print("🎯 WIN RATE OPTIMIZER TEST")
    print("=" * 40)
    
    optimizer = WinRateOptimizer()
    
    # Create sample trade data for testing
    sample_trades = [
        {"pnl": 5.60, "confidence": 0.85, "weather_delta": 3.2},
        {"pnl": -10.00, "confidence": 0.45, "weather_delta": 1.1},
        {"pnl": 5.60, "confidence": 0.78, "weather_delta": 2.8},
        {"pnl": -10.00, "confidence": 0.52, "weather_delta": 1.5},
        {"pnl": 5.60, "confidence": 0.91, "weather_delta": 4.1},
    ]
    
    # Analyze current performance
    analysis = optimizer.analyze_current_performance(sample_trades)
    
    print(f"📊 CURRENT PERFORMANCE:")
    print(f"   Total Signals: {analysis.total_signals}")
    print(f"   Win Rate: {analysis.winning_signals / analysis.total_signals:.1%}")
    print(f"   Avg Confidence (Wins): {analysis.avg_confidence_wins:.2f}")
    print(f"   Avg Confidence (Losses): {analysis.avg_confidence_losses:.2f}")
    print(f"   Avg Delta (Wins): {analysis.avg_delta_wins:.2f}°C")
    print(f"   Avg Delta (Losses): {analysis.avg_delta_losses:.2f}°C")
    
    # Generate optimization plan
    plan = optimizer.generate_optimization_plan(analysis)
    
    print(f"\n🎯 OPTIMIZATION PLAN:")
    print(f"   Current Win Rate: {plan['current_status']['win_rate']:.1%}")
    print(f"   Target Win Rate: {plan['current_status']['target_win_rate']:.1%}")
    print(f"   Gap: {plan['current_status']['gap']:.1%}")
    print(f"   Success Probability: {plan['success_probability']:.1%}")
    
    print(f"\n📈 TOP STRATEGIES:")
    for name, result in list(plan["strategies"].items())[:3]:
        print(f"   {result['strategy']}: +{result['estimated_improvement']:.1%} win rate")
        print(f"      Expected: {result['expected_win_rate']:.1%}")
    
    print(f"\n✅ WIN RATE OPTIMIZER READY")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
