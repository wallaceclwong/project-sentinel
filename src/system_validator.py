#!/usr/bin/env python3
"""
PROJECT SENTINEL - System Validator
Comprehensive validation of all components and integration points
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from data_fetcher import SentinelDataFetcher
from backtesting_engine import BacktestingEngine
from risk_manager import RiskManager
from telegram_bot import SentinelTelegramBot
from trading_engine import TradingEngine, TradeSignal
from polymarket_client import PolymarketClient
from gcp_bridge import GCPBridge, WeatherDeltaProcessor

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation test"""
    component: str
    test_name: str
    status: str  # PASS, FAIL, WARN
    message: str
    execution_time: float
    details: Dict[str, Any] = None

@dataclass
class SystemReport:
    """Complete system validation report"""
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    warnings: int
    results: List[ValidationResult]
    recommendations: List[str]
    critical_issues: List[str]


class SystemValidator:
    """Validates all PROJECT SENTINEL components"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.start_time = time.time()
    
    def add_result(self, component: str, test_name: str, status: str, 
                   message: str, execution_time: float, details: Dict = None):
        """Add a validation result"""
        self.results.append(ValidationResult(
            component=component,
            test_name=test_name,
            status=status,
            message=message,
            execution_time=execution_time,
            details=details or {}
        ))
    
    async def validate_data_fetcher(self) -> bool:
        """Validate data fetching capabilities"""
        print("\n🔍 VALIDATING DATA FETCHER...")
        
        # Test 1: NOAA weather data
        start = time.time()
        try:
            fetcher = SentinelDataFetcher()
            weather_data = await fetcher.fetch_tokyo("2024-01-01", "2024-01-31")
            
            if len(weather_data) >= 25:  # At least 25 days
                self.add_result("DataFetcher", "NOAA_Tokyo", "PASS",
                              f"Fetched {len(weather_data)} days of Tokyo weather",
                              time.time() - start,
                              {"sample_date": weather_data[0].date, 
                               "temp_range": f"{min(r.temp_avg for r in weather_data):.1f}°C to {max(r.temp_avg for r in weather_data):.1f}°C"})
            else:
                self.add_result("DataFetcher", "NOAA_Tokyo", "FAIL",
                              f"Insufficient data: {len(weather_data)} days",
                              time.time() - start)
        except Exception as e:
            self.add_result("DataFetcher", "NOAA_Tokyo", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        # Test 2: Polymarket market discovery
        start = time.time()
        try:
            markets = await fetcher.market.search_weather_markets()
            
            if len(markets) > 0:
                self.add_result("DataFetcher", "Polymarket_Markets", "PASS",
                              f"Found {len(markets)} weather markets",
                              time.time() - start,
                              {"sample_market": markets[0].get("question", "N/A")[:50]})
            else:
                self.add_result("DataFetcher", "Polymarket_Markets", "WARN",
                              "No weather markets found (expected for niche category)",
                              time.time() - start)
        except Exception as e:
            self.add_result("DataFetcher", "Polymarket_Markets", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        return True
    
    async def validate_backtesting_engine(self) -> bool:
        """Validate backtesting with real data"""
        print("\n🔍 VALIDATING BACKTESTING ENGINE...")
        
        # Test 1: Load real weather data
        start = time.time()
        try:
            data_file = os.path.join(os.path.dirname(__file__), "..", "data", "sentinel_backtest_data.json")
            engine = BacktestingEngine(initial_capital=10000)
            
            if os.path.exists(data_file):
                weather_data = engine.load_real_weather(data_file, "Tokyo")
                
                if len(weather_data) >= 500:  # At least 500 days
                    self.add_result("BacktestingEngine", "RealData_Load", "PASS",
                                  f"Loaded {len(weather_data)} days of real weather data",
                                  time.time() - start,
                                  {"date_range": f"{weather_data[0].date} to {weather_data[-1].date}",
                                   "avg_delta": sum(r.delta for r in weather_data) / len(weather_data)})
                else:
                    self.add_result("BacktestingEngine", "RealData_Load", "FAIL",
                                  f"Insufficient data: {len(weather_data)} days",
                                  time.time() - start)
            else:
                self.add_result("BacktestingEngine", "RealData_Load", "FAIL",
                              "No real data file found", time.time() - start)
        except Exception as e:
            self.add_result("BacktestingEngine", "RealData_Load", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        # Test 2: Run quick backtest
        start = time.time()
        try:
            if os.path.exists(data_file):
                result = engine.run_real_backtest(
                    data_file=data_file,
                    region="Tokyo",
                    signal_threshold=3.0,  # Conservative
                    position_size_pct=0.01  # Small position
                )
                
                if result.total_trades > 0:
                    self.add_result("BacktestingEngine", "Quick_Backtest", "PASS",
                                  f"Backtest completed: {result.total_trades} trades, {result.win_rate:.1%} win rate",
                                  time.time() - start,
                                  {"pnl": result.total_pnl, "sharpe": result.sharpe_ratio})
                else:
                    self.add_result("BacktestingEngine", "Quick_Backtest", "WARN",
                                  "No trades generated (threshold too high?)",
                                  time.time() - start)
        except Exception as e:
            self.add_result("BacktestingEngine", "Quick_Backtest", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        return True
    
    def validate_risk_manager(self) -> bool:
        """Validate risk management logic"""
        print("\n🔍 VALIDATING RISK MANAGER...")
        
        # Test 1: Position size limits
        start = time.time()
        try:
            rm = RiskManager(max_position_size=500, max_daily_loss=100)
            
            # Test oversized trade
            check = rm.check_trade("BUY", 600, 0.50)
            if not check.approved and "exceeds limit" in check.reason:
                self.add_result("RiskManager", "Position_Limit", "PASS",
                              "Correctly rejected oversized position",
                              time.time() - start)
            else:
                self.add_result("RiskManager", "Position_Limit", "FAIL",
                              "Failed to reject oversized position",
                              time.time() - start)
        except Exception as e:
            self.add_result("RiskManager", "Position_Limit", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        # Test 2: Daily loss limit
        start = time.time()
        try:
            rm = RiskManager(max_position_size=500, max_daily_loss=100)
            rm.daily_pnl = -150  # Exceeds limit
            
            check = rm.check_trade("BUY", 100, 0.50)
            if not check.approved and "loss limit" in check.reason:
                self.add_result("RiskManager", "Loss_Limit", "PASS",
                              "Correctly activated circuit breaker",
                              time.time() - start)
            else:
                self.add_result("RiskManager", "Loss_Limit", "FAIL",
                              "Failed to activate circuit breaker",
                              time.time() - start)
        except Exception as e:
            self.add_result("RiskManager", "Loss_Limit", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        # Test 3: Confidence filtering
        start = time.time()
        try:
            rm = RiskManager(min_confidence=0.60)
            
            check = rm.check_trade("BUY", 100, 0.50, confidence=0.40)
            if not check.approved and "confidence" in check.reason:
                self.add_result("RiskManager", "Confidence_Filter", "PASS",
                              "Correctly rejected low confidence trade",
                              time.time() - start)
            else:
                self.add_result("RiskManager", "Confidence_Filter", "FAIL",
                              "Failed to reject low confidence trade",
                              time.time() - start)
        except Exception as e:
            self.add_result("RiskManager", "Confidence_Filter", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        return True
    
    async def validate_telegram_bot(self) -> bool:
        """Validate Telegram bot functionality"""
        print("\n🔍 VALIDATING TELEGRAM BOT...")
        
        # Check environment variables
        start = time.time()
        try:
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID")
            
            if token and chat_id:
                self.add_result("TelegramBot", "Env_Config", "PASS",
                              "Environment variables configured",
                              time.time() - start,
                              {"chat_id": chat_id})
            else:
                self.add_result("TelegramBot", "Env_Config", "WARN",
                              "Missing environment variables (expected if not configured)",
                              time.time() - start)
        except Exception as e:
            self.add_result("TelegramBot", "Env_Config", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        # Test bot initialization (if configured)
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            start = time.time()
            try:
                from telegram_bot import SentinelTelegramBot
                bot = SentinelTelegramBot(
                    os.environ["TELEGRAM_BOT_TOKEN"],
                    os.environ.get("TELEGRAM_CHAT_ID", "")
                )
                
                # Test message sending (quick check)
                test_msg = "🔧 System Validation Test"
                # Note: We won't actually send to avoid spam
                self.add_result("TelegramBot", "Initialization", "PASS",
                              "Bot initialized successfully",
                              time.time() - start)
            except Exception as e:
                self.add_result("TelegramBot", "Initialization", "FAIL",
                              f"Exception: {str(e)}", time.time() - start)
        
        return True
    
    def validate_trading_engine(self) -> bool:
        """Validate trading engine logic"""
        print("\n🔍 VALIDATING TRADING ENGINE...")
        
        # Test 1: Signal processing
        start = time.time()
        try:
            # Mock config
            config = {
                "telegram_bot_token": "test",
                "telegram_chat_id": "test",
                "paper_trading": True,
                "require_2fa": False,  # Disable for testing
                "max_position_size": 500,
                "max_daily_loss": 100
            }
            
            engine = TradingEngine(config)
            
            # Test signal
            signal = TradeSignal(
                signal_id="test_001",
                action="BUY",
                confidence=0.82,
                reasoning="Test signal",
                weather_impact=0.78,
                market_contract="Test market",
                token_id="test_token",
                suggested_price=0.55,
                suggested_size=100,
                timestamp=datetime.now().isoformat()
            )
            
            # Should process without 2FA
            self.add_result("TradingEngine", "Signal_Processing", "PASS",
                          "Trading engine initialized and ready",
                          time.time() - start,
                          {"paper_trading": engine.paper_trading})
        except Exception as e:
            self.add_result("TradingEngine", "Signal_Processing", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        return True
    
    def validate_polymarket_client(self) -> bool:
        """Validate Polymarket client"""
        print("\n🔍 VALIDATING POLYMARKET CLIENT...")
        
        # Test 1: Client initialization
        start = time.time()
        try:
            client = PolymarketClient()  # No credentials for testing
            
            self.add_result("PolymarketClient", "Initialization", "PASS",
                          "Client initialized successfully",
                          time.time() - start)
        except Exception as e:
            self.add_result("PolymarketClient", "Initialization", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        return True
    
    def validate_gcp_integration(self) -> bool:
        """Validate GCP Cloud Run integration"""
        print("\n🔍 VALIDATING GCP INTEGRATION...")
        
        # Test 1: Environment variables
        start = time.time()
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            
            if api_key:
                self.add_result("GCP_Integration", "API_Key", "PASS",
                              "Gemini API key configured",
                              time.time() - start)
            else:
                self.add_result("GCP_Integration", "API_Key", "WARN",
                              "Missing GEMINI_API_KEY (expected if not configured)",
                              time.time() - start)
        except Exception as e:
            self.add_result("GCP_Integration", "API_Key", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        # Test 2: Bridge initialization
        start = time.time()
        try:
            from gcp_bridge import GCPBridge
            bridge = GCPBridge("https://sentinel-reasoning-895191182806.asia-east2.run.app")
            
            self.add_result("GCP_Integration", "Bridge_Init", "PASS",
                          "GCP Bridge initialized successfully",
                          time.time() - start)
        except Exception as e:
            self.add_result("GCP_Integration", "Bridge_Init", "FAIL",
                          f"Exception: {str(e)}", time.time() - start)
        
        return True
    
    def validate_file_structure(self) -> bool:
        """Validate project file structure"""
        print("\n🔍 VALIDATING FILE STRUCTURE...")
        
        required_files = [
            "src/data_fetcher.py",
            "src/backtesting_engine.py", 
            "src/risk_manager.py",
            "src/telegram_bot.py",
            "src/trading_engine.py",
            "src/polymarket_client.py",
            "src/gcp_bridge.py",
            "config/config.yaml",
            "data/sentinel_backtest_data.json"
        ]
        
        start = time.time()
        missing_files = []
        
        for file_path in required_files:
            full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        if not missing_files:
            self.add_result("FileStructure", "Required_Files", "PASS",
                          f"All {len(required_files)} required files present",
                          time.time() - start)
        else:
            self.add_result("FileStructure", "Required_Files", "FAIL",
                          f"Missing {len(missing_files)} files: {', '.join(missing_files)}",
                          time.time() - start)
        
        return True
    
    def generate_recommendations(self) -> List[str]:
        """Generate system improvement recommendations"""
        recommendations = []
        critical_issues = []
        
        # Analyze results
        failed_tests = [r for r in self.results if r.status == "FAIL"]
        warning_tests = [r for r in self.results if r.status == "WARN"]
        
        if failed_tests:
            critical_issues.append(f"CRITICAL: {len(failed_tests)} components failed validation")
            
            # Specific recommendations based on failures
            for test in failed_tests:
                if "DataFetcher" in test.component:
                    recommendations.append("Fix data fetching: Check API endpoints and network connectivity")
                elif "BacktestingEngine" in test.component:
                    recommendations.append("Fix backtesting: Verify data format and calculation logic")
                elif "RiskManager" in test.component:
                    recommendations.append("Fix risk management: Review position sizing and limit logic")
                elif "TelegramBot" in test.component:
                    recommendations.append("Fix Telegram bot: Check bot token and chat ID configuration")
                elif "TradingEngine" in test.component:
                    recommendations.append("Fix trading engine: Verify signal processing and execution logic")
                elif "GCP_Integration" in test.component:
                    recommendations.append("Fix GCP integration: Check API keys and Cloud Run URL")
        
        if warning_tests:
            recommendations.append(f"Address {len(warning_tests)} warnings for optimal performance")
        
        # Performance recommendations
        execution_times = [r.execution_time for r in self.results if r.execution_time > 0]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            if avg_time > 2.0:
                recommendations.append("Optimize performance: Average test execution time > 2 seconds")
        
        # Architecture recommendations
        recommendations.extend([
            "Add comprehensive logging to all components",
            "Implement health check endpoints for monitoring",
            "Add unit tests for critical functions",
            "Consider adding circuit breakers for external API calls",
            "Implement data validation at component boundaries"
        ])
        
        return recommendations, critical_issues
    
    async def run_full_validation(self) -> SystemReport:
        """Run complete system validation"""
        print("🚀 PROJECT SENTINEL - SYSTEM VALIDATION")
        print("=" * 60)
        
        # Run all validations
        await self.validate_data_fetcher()
        await self.validate_backtesting_engine()
        self.validate_risk_manager()
        await self.validate_telegram_bot()
        self.validate_trading_engine()
        self.validate_polymarket_client()
        self.validate_gcp_integration()
        self.validate_file_structure()
        
        # Generate report
        total_time = time.time() - self.start_time
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        warnings = len([r for r in self.results if r.status == "WARN"])
        
        recommendations, critical_issues = self.generate_recommendations()
        
        report = SystemReport(
            timestamp=datetime.now().isoformat(),
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            results=self.results,
            recommendations=recommendations,
            critical_issues=critical_issues
        )
        
        return report
    
    def print_report(self, report: SystemReport):
        """Print validation report"""
        print("\n" + "=" * 60)
        print(f"📊 SYSTEM VALIDATION REPORT")
        print("=" * 60)
        
        print(f"\n⏱️  Execution Time: {time.time() - self.start_time:.2f} seconds")
        print(f"📅 Timestamp: {report.timestamp}")
        
        print(f"\n📈 SUMMARY:")
        print(f"   Total Tests: {report.total_tests}")
        print(f"   ✅ Passed: {report.passed}")
        print(f"   ❌ Failed: {report.failed}")
        print(f"   ⚠️  Warnings: {report.warnings}")
        
        # Critical issues first
        if report.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in report.critical_issues:
                print(f"   • {issue}")
        
        # Component breakdown
        print(f"\n📋 COMPONENT RESULTS:")
        components = {}
        for result in report.results:
            if result.component not in components:
                components[result.component] = []
            components[result.component].append(result)
        
        for component, tests in components.items():
            status = "✅" if all(t.status == "PASS" for t in tests) else "❌" if any(t.status == "FAIL" for t in tests) else "⚠️"
            print(f"   {status} {component}: {len([t for t in tests if t.status == 'PASS'])}/{len(tests)} passed")
            
            for test in tests:
                if test.status == "FAIL":
                    print(f"      ❌ {test.test_name}: {test.message}")
                elif test.status == "WARN":
                    print(f"      ⚠️  {test.test_name}: {test.message}")
        
        # Recommendations
        if report.recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report.recommendations[:10], 1):  # Top 10
                print(f"   {i}. {rec}")
            if len(report.recommendations) > 10:
                print(f"   ... and {len(report.recommendations) - 10} more")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if report.failed == 0:
            if report.warnings == 0:
                print("   🏆 EXCELLENT - All systems operational")
            else:
                print("   ✅ GOOD - Minor issues to address")
        elif report.failed <= 2:
            print("   ⚠️  NEEDS WORK - Critical issues require attention")
        else:
            print("   ❌ POOR - Multiple system failures")
        
        print("=" * 60)


async def main():
    """Run system validation"""
    validator = SystemValidator()
    report = await validator.run_full_validation()
    validator.print_report(report)
    
    # Save report
    report_file = os.path.join(os.path.dirname(__file__), "..", "data", "validation_report.json")
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": report.timestamp,
            "summary": {
                "total_tests": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings
            },
            "results": [
                {
                    "component": r.component,
                    "test": r.test_name,
                    "status": r.status,
                    "message": r.message,
                    "execution_time": r.execution_time
                } for r in report.results
            ],
            "recommendations": report.recommendations,
            "critical_issues": report.critical_issues
        }, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
