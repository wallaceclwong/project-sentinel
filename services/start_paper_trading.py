#!/usr/bin/env python3
"""
PROJECT SENTINEL - Paper Trading Launcher
Start live paper trading with optimized system
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from backtesting_engine import BacktestingEngine
from paper_trader import PaperTrader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_paper_trading():
    """Start paper trading with optimized system"""
    
    print("🚀 PROJECT SENTINEL - PAPER TRADING START")
    print("=" * 60)
    
    print("📊 SYSTEM CONFIGURATION:")
    print("   ✅ Optimized Win Rate: 64.4%")
    print("   ✅ Risk/Reward: 1:0.45")
    print("   ✅ Position Size: $10 per trade")
    print("   ✅ Market: Tokyo Temperature")
    print("   ✅ Strategy: Ensemble Consensus + Pattern Weighting")
    print()
    
    print("🎯 PAPER TRADING PARAMETERS:")
    print("   💰 Starting Capital: $10,000")
    print("   📊 Position Size: $10 per trade")
    print("   🔄 Update Interval: 5 minutes")
    print("   📈 Max Positions: 5 concurrent")
    print("   🎯 Target Win Rate: 65%+")
    print()
    
    # Initialize paper trader
    trader = PaperTrader()
    
    print("🔧 SYSTEM INITIALIZATION:")
    
    # Test system components
    try:
        print("   📊 Loading backtesting engine...")
        engine = BacktestingEngine(initial_capital=10000)
        print("   ✅ Backtesting engine loaded")
        
        print("   🌡️ Testing signal generation...")
        # Test signal generation
        from backtesting_engine import HistoricalWeatherPoint
        test_weather = HistoricalWeatherPoint(
            date=datetime.now().strftime("%Y-%m-%d"),
            region="Tokyo",
            actual_temp=22.5,
            forecast_temp=18.0,
            delta=4.5,
            ensemble_std=1.2,
            confidence=0.78
        )
        
        action, confidence = engine._generate_signal(test_weather, threshold=2.0)
        print(f"   ✅ Signal Generation: {action} ({confidence:.1%})")
        
        print("   📈 Paper trader ready...")
        print("   ✅ All systems operational")
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        print(f"   ❌ Error: {e}")
        return
    
    print()
    print("🎯 STARTING PAPER TRADING SESSION...")
    print("   📊 Monitoring Tokyo temperature markets")
    print("   💰 Using $10 position size")
    print("   🔄 Updates every 5 minutes")
    print("   📈 Real-time P&L tracking")
    print()
    
    print("⚠️  PAPER TRADING NOTES:")
    print("   • This is SIMULATION - no real money at risk")
    print("   • Signals based on optimized 64.4% win rate system")
    print("   • Monitor exit reasons for further optimization")
    print("   • Stop anytime with Ctrl+C")
    print()
    
    try:
        # Start paper trading
        await trader.start_paper_trading()
        
    except KeyboardInterrupt:
        print("\n🛑 Paper trading stopped by user")
        
        # Show final summary
        if hasattr(trader, 'paper_trades') and trader.paper_trades:
            print("\n📊 FINAL PAPER TRADING SUMMARY:")
            
            winning_trades = [t for t in trader.paper_trades if t.pnl > 0]
            losing_trades = [t for t in trader.paper_trades if t.pnl <= 0]
            
            win_rate = len(winning_trades) / len(trader.paper_trades) if trader.paper_trades else 0
            total_pnl = trader.total_pnl
            
            print(f"   Total Trades: {len(trader.paper_trades)}")
            print(f"   Win Rate: {win_rate:.1%}")
            print(f"   Total P&L: ${total_pnl:+.2f}")
            print(f"   Final Capital: ${trader.paper_capital:,.2f}")
            
            if win_rate >= 0.64:
                print("   🎉 Excellent performance! System working as expected.")
            elif win_rate >= 0.60:
                print("   📈 Good performance! Close to target.")
            else:
                print("   ⚠️  Performance below target. Consider optimization.")
        
        print("\n✅ Paper trading session completed")
        
    except Exception as e:
        logger.error(f"Paper trading error: {e}")
        print(f"\n❌ Error during paper trading: {e}")
        print("🔧 Check system logs for details")


def main():
    """Main entry point"""
    print("🌤️  PROJECT SENTINEL - Paper Trading System")
    print("   Optimized Weather Trading with 64.4% Win Rate")
    print("   Risk/Reward: 1:0.45 | Position: $10 | Market: Tokyo")
    print()
    
    try:
        asyncio.run(start_paper_trading())
    except KeyboardInterrupt:
        print("\n🛑 Paper trading terminated")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
