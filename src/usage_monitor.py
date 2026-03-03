#!/usr/bin/env python3
"""
PROJECT SENTINEL - AI Usage Monitor
Tracks and controls Google Gemini Pro API usage and costs
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class APICallRecord:
    """Record of individual API call"""
    timestamp: datetime
    model: str
    tokens_used: int
    response_time: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class UsageStats:
    """Usage statistics for a time period"""
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_tokens: int
    total_cost_usd: float
    avg_response_time: float
    period_start: datetime
    period_end: datetime

class AIUsageMonitor:
    """Monitors and controls AI API usage and costs"""
    
    def __init__(self, data_dir: str = "/home/ubuntu/project-sentinel/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.usage_file = self.data_dir / "ai_usage.json"
        self.daily_limit = 1000  # Maximum API calls per day
        self.monthly_budget = 50.0  # Maximum monthly budget in USD
        self.cost_per_1k_tokens = 0.00025  # Gemini Pro pricing
        
        # Load existing usage data
        self.usage_data = self._load_usage_data()
        
    def _load_usage_data(self) -> Dict:
        """Load usage data from file"""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load usage data: {e}")
        
        return {
            "calls": [],
            "daily_stats": {},
            "monthly_stats": {},
            "last_reset": datetime.now().isoformat()
        }
    
    def _save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def record_api_call(self, model: str, tokens_used: int, response_time: float, 
                       success: bool = True, error_message: Optional[str] = None):
        """Record an API call"""
        record = APICallRecord(
            timestamp=datetime.now(),
            model=model,
            tokens_used=tokens_used,
            response_time=response_time,
            success=success,
            error_message=error_message
        )
        
        self.usage_data["calls"].append(asdict(record))
        self._save_usage_data()
        
        logger.info(f"API call recorded: {model}, {tokens_used} tokens, "
                   f"{response_time:.2f}s, success={success}")
    
    def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        today = datetime.now().date()
        today_str = today.isoformat()
        
        # Count calls today
        today_calls = [
            call for call in self.usage_data["calls"]
            if datetime.fromisoformat(call["timestamp"]).date() == today
        ]
        
        calls_today = len(today_calls)
        
        if calls_today >= self.daily_limit:
            logger.warning(f"Daily rate limit reached: {calls_today}/{self.daily_limit}")
            return False
        
        # Check monthly budget
        current_month = today.replace(day=1)
        month_calls = [
            call for call in self.usage_data["calls"]
            if datetime.fromisoformat(call["timestamp"]) >= current_month
        ]
        
        month_tokens = sum(call["tokens_used"] for call in month_calls)
        month_cost = (month_tokens / 1000) * self.cost_per_1k_tokens
        
        if month_cost >= self.monthly_budget:
            logger.warning(f"Monthly budget reached: ${month_cost:.2f}/${self.monthly_budget:.2f}")
            return False
        
        logger.info(f"Rate limit check passed: {calls_today}/{self.daily_limit} calls, "
                   f"${month_cost:.2f}/${self.monthly_budget:.2f} budget")
        return True
    
    def get_daily_stats(self) -> UsageStats:
        """Get today's usage statistics"""
        today = datetime.now().date()
        day_start = datetime.combine(today, datetime.min.time())
        day_end = datetime.combine(today, datetime.max.time())
        
        day_calls = [
            call for call in self.usage_data["calls"]
            if day_start <= datetime.fromisoformat(call["timestamp"]) <= day_end
        ]
        
        if not day_calls:
            return UsageStats(
                total_calls=0, successful_calls=0, failed_calls=0,
                total_tokens=0, total_cost_usd=0.0, avg_response_time=0.0,
                period_start=day_start, period_end=day_end
            )
        
        successful_calls = [c for c in day_calls if c["success"]]
        total_tokens = sum(c["tokens_used"] for c in day_calls)
        total_cost = (total_tokens / 1000) * self.cost_per_1k_tokens
        avg_response_time = sum(c["response_time"] for c in day_calls) / len(day_calls)
        
        return UsageStats(
            total_calls=len(day_calls),
            successful_calls=len(successful_calls),
            failed_calls=len(day_calls) - len(successful_calls),
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            avg_response_time=avg_response_time,
            period_start=day_start,
            period_end=day_end
        )
    
    def get_monthly_stats(self) -> UsageStats:
        """Get current month's usage statistics"""
        today = datetime.now().date()
        month_start = today.replace(day=1)
        month_end = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        month_calls = [
            call for call in self.usage_data["calls"]
            if month_start <= datetime.fromisoformat(call["timestamp"]).date() <= month_end
        ]
        
        if not month_calls:
            return UsageStats(
                total_calls=0, successful_calls=0, failed_calls=0,
                total_tokens=0, total_cost_usd=0.0, avg_response_time=0.0,
                period_start=datetime.combine(month_start, datetime.min.time()),
                period_end=datetime.combine(month_end, datetime.max.time())
            )
        
        successful_calls = [c for c in month_calls if c["success"]]
        total_tokens = sum(c["tokens_used"] for c in month_calls)
        total_cost = (total_tokens / 1000) * self.cost_per_1k_tokens
        avg_response_time = sum(c["response_time"] for c in month_calls) / len(month_calls)
        
        return UsageStats(
            total_calls=len(month_calls),
            successful_calls=len(successful_calls),
            failed_calls=len(month_calls) - len(successful_calls),
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            avg_response_time=avg_response_time,
            period_start=datetime.combine(month_start, datetime.min.time()),
            period_end=datetime.combine(month_end, datetime.max.time())
        )
    
    def get_usage_report(self) -> Dict:
        """Get comprehensive usage report"""
        daily_stats = self.get_daily_stats()
        monthly_stats = self.get_monthly_stats()
        
        return {
            "daily": asdict(daily_stats),
            "monthly": asdict(monthly_stats),
            "limits": {
                "daily_calls": self.daily_limit,
                "monthly_budget_usd": self.monthly_budget,
                "cost_per_1k_tokens": self.cost_per_1k_tokens
            },
            "status": {
                "daily_remaining": max(0, self.daily_limit - daily_stats.total_calls),
                "budget_remaining": max(0, self.monthly_budget - monthly_stats.total_cost_usd),
                "within_limits": self.check_rate_limit()
            }
        }
    
    def cleanup_old_records(self, days_to_keep: int = 90):
        """Clean up old usage records"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        original_count = len(self.usage_data["calls"])
        self.usage_data["calls"] = [
            call for call in self.usage_data["calls"]
            if datetime.fromisoformat(call["timestamp"]) >= cutoff_date
        ]
        
        removed_count = original_count - len(self.usage_data["calls"])
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old usage records")
            self._save_usage_data()

# Global monitor instance
usage_monitor = AIUsageMonitor()

def monitor_api_call(model: str, tokens_used: int, response_time: float, 
                    success: bool = True, error_message: Optional[str] = None):
    """Convenience function to record API calls"""
    usage_monitor.record_api_call(model, tokens_used, response_time, success, error_message)

def can_make_api_call() -> bool:
    """Check if we can make an API call within limits"""
    return usage_monitor.check_rate_limit()

def get_usage_dashboard() -> Dict:
    """Get usage dashboard data"""
    return usage_monitor.get_usage_report()
