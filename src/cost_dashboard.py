#!/usr/bin/env python3
"""
PROJECT SENTINEL - Cost Control Dashboard
Real-time monitoring of AI usage and costs
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from usage_monitor import get_usage_dashboard

logger = logging.getLogger(__name__)

class CostDashboard:
    """Real-time cost monitoring and control dashboard"""
    
    def __init__(self):
        self.daily_budget = 2.0  # $2/day budget
        self.monthly_budget = 50.0  # $50/month budget
        self.alert_threshold = 0.8  # Alert at 80% of budget
        
    def display_dashboard(self):
        """Display comprehensive cost dashboard"""
        print("\n" + "="*60)
        print("🚀 PROJECT SENTINEL - AI COST DASHBOARD")
        print("="*60)
        
        # Get usage data
        usage_data = get_usage_dashboard()
        
        # Display daily stats
        daily = usage_data['daily']
        print(f"\n📅 DAILY USAGE ({datetime.now().strftime('%Y-%m-%d')})")
        print("-" * 40)
        print(f"API Calls: {daily['total_calls']}")
        print(f"Successful: {daily['successful_calls']} | Failed: {daily['failed_calls']}")
        print(f"Tokens Used: {daily['total_tokens']:,}")
        print(f"Est. Cost: ${daily['total_cost_usd']:.4f}")
        print(f"Avg Response: {daily['avg_response_time']:.2f}s")
        
        # Daily budget status
        daily_budget_pct = (daily['total_cost_usd'] / self.daily_budget) * 100
        daily_status = "🟢 SAFE" if daily_budget_pct < 70 else "🟡 WARNING" if daily_budget_pct < 90 else "🔴 CRITICAL"
        print(f"Daily Budget: ${daily['total_cost_usd']:.4f} / ${self.daily_budget:.2f} ({daily_budget_pct:.1f}%) {daily_status}")
        
        # Display monthly stats
        monthly = usage_data['monthly']
        print(f"\n📊 MONTHLY USAGE ({datetime.now().strftime('%Y-%m')})")
        print("-" * 40)
        print(f"API Calls: {monthly['total_calls']}")
        print(f"Successful: {monthly['successful_calls']} | Failed: {monthly['failed_calls']}")
        print(f"Tokens Used: {monthly['total_tokens']:,}")
        print(f"Est. Cost: ${monthly['total_cost_usd']:.2f}")
        print(f"Avg Response: {monthly['avg_response_time']:.2f}s")
        
        # Monthly budget status
        monthly_budget_pct = (monthly['total_cost_usd'] / self.monthly_budget) * 100
        monthly_status = "🟢 SAFE" if monthly_budget_pct < 70 else "🟡 WARNING" if monthly_budget_pct < 90 else "🔴 CRITICAL"
        print(f"Monthly Budget: ${monthly['total_cost_usd']:.2f} / ${self.monthly_budget:.2f} ({monthly_budget_pct:.1f}%) {monthly_status}")
        
        # Display limits and status
        status = usage_data['status']
        print(f"\n⚠️ LIMITS & STATUS")
        print("-" * 40)
        print(f"Daily Calls Remaining: {status['daily_remaining']}")
        print(f"Budget Remaining: ${status['budget_remaining']:.2f}")
        print(f"Within Limits: {'✅ YES' if status['within_limits'] else '❌ NO'}")
        
        # Pro tier benefits
        limits = usage_data['limits']
        print(f"\n💎 PRO TIER BENEFITS")
        print("-" * 40)
        print(f"Rate Limit: 60 requests/minute")
        print(f"Context Window: 1M tokens")
        print(f"Model: Gemini 2.5 Pro (latest)")
        print(f"Cost per 1K tokens: ${limits['cost_per_1k_tokens']}")
        
        # Recommendations
        self._show_recommendations(usage_data)
        
        print("\n" + "="*60)
        
    def _show_recommendations(self, usage_data: Dict[str, Any]):
        """Show cost optimization recommendations"""
        daily = usage_data['daily']
        monthly = usage_data['monthly']
        
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 40)
        
        recommendations = []
        
        # Check daily usage patterns
        if daily['total_calls'] > 20:
            recommendations.append("Consider implementing request batching to reduce API calls")
        
        if daily['avg_response_time'] > 3.0:
            recommendations.append("High response times detected - consider prompt optimization")
        
        if daily['failed_calls'] / max(daily['total_calls'], 1) > 0.1:
            recommendations.append("High failure rate - check error handling and retry logic")
        
        # Check monthly budget usage
        monthly_budget_pct = (monthly['total_cost_usd'] / self.monthly_budget) * 100
        if monthly_budget_pct > 80:
            recommendations.append("Approaching monthly budget - consider reducing analysis frequency")
        
        # Cost efficiency
        if daily['total_calls'] > 0:
            cost_per_call = daily['total_cost_usd'] / daily['total_calls']
            if cost_per_call > 0.01:
                recommendations.append("High cost per call - optimize prompts for fewer tokens")
        
        if not recommendations:
            recommendations.append("✅ Usage is optimal - no changes needed")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    def check_alerts(self):
        """Check for budget alerts"""
        usage_data = get_usage_dashboard()
        daily = usage_data['daily']
        monthly = usage_data['monthly']
        
        alerts = []
        
        # Daily budget alerts
        daily_budget_pct = (daily['total_cost_usd'] / self.daily_budget) * 100
        if daily_budget_pct >= 90:
            alerts.append(f"🔴 CRITICAL: Daily budget {daily_budget_pct:.1f}% used")
        elif daily_budget_pct >= 80:
            alerts.append(f"🟡 WARNING: Daily budget {daily_budget_pct:.1f}% used")
        
        # Monthly budget alerts
        monthly_budget_pct = (monthly['total_cost_usd'] / self.monthly_budget) * 100
        if monthly_budget_pct >= 90:
            alerts.append(f"🔴 CRITICAL: Monthly budget {monthly_budget_pct:.1f}% used")
        elif monthly_budget_pct >= 80:
            alerts.append(f"🟡 WARNING: Monthly budget {monthly_budget_pct:.1f}% used")
        
        # Rate limit alerts
        if not usage_data['status']['within_limits']:
            alerts.append("🔴 Rate limits or budget exceeded - API calls blocked")
        
        # Display alerts
        if alerts:
            print("\n🚨 BUDGET ALERTS")
            print("-" * 40)
            for alert in alerts:
                print(alert)
            print()
        
        return alerts
    
    def export_report(self, filename: str = None):
        """Export usage report to file"""
        if not filename:
            filename = f"sentinel_usage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        usage_data = get_usage_dashboard()
        
        report = {
            "report_generated": datetime.now().isoformat(),
            "dashboard_data": usage_data,
            "budget_settings": {
                "daily_budget": self.daily_budget,
                "monthly_budget": self.monthly_budget,
                "alert_threshold": self.alert_threshold
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Report exported to: {filename}")
        except Exception as e:
            logger.error(f"Failed to export report: {e}")

def main():
    """Run the cost dashboard"""
    dashboard = CostDashboard()
    
    print("🚀 Starting PROJECT SENTINEL Cost Dashboard...")
    
    try:
        # Check for alerts first
        alerts = dashboard.check_alerts()
        
        # Display full dashboard
        dashboard.display_dashboard()
        
        # Export report
        dashboard.export_report()
        
        # Show next steps
        print("\n🎯 NEXT STEPS")
        print("-" * 40)
        print("1. Monitor usage daily with: python src/cost_dashboard.py")
        print("2. Check Cloud Run usage: curl YOUR_CLOUD_RUN_URL/usage")
        print("3. Adjust budgets in config.yaml if needed")
        print("4. Set up automated alerts for production")
        
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
