#!/usr/bin/env python3
"""
PROJECT SENTINEL - GCP Bridge
Phase 3: Secure HTTPS/Tailscale bridge from Tokyo to Hong Kong
Feeds weather delta scores to Gemini Pro for trade validation
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class WeatherDelta:
    """Weather delta data structure"""
    timestamp: datetime
    max_delta: float
    min_delta: float
    mean_delta: float
    std_delta: float
    region: str
    confidence_score: float

@dataclass
class TradeSignal:
    """Trade signal from Gemini Pro"""
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    reasoning: str
    market_contract: str
    weather_impact_score: float

class GCPBridge:
    """Secure bridge to GCP Cloud Run with Gemini Pro"""
    
    def __init__(self, cloud_run_url: str, timeout_seconds: int = 30):
        self.cloud_run_url = cloud_run_url
        self.timeout_seconds = timeout_seconds
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Project-Sentinel/1.0'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def calculate_weather_delta_score(self, delta: WeatherDelta) -> float:
        """Calculate weather impact score from delta data"""
        try:
            # Normalize delta values to 0-1 scale
            max_abs_delta = abs(delta.max_delta)
            mean_abs_delta = abs(delta.mean_delta)
            std_normalized = min(delta.std_delta / max_abs_delta, 1.0) if max_abs_delta > 0 else 0
            
            # Weighted scoring algorithm
            impact_score = (
                0.4 * min(max_abs_delta / 10.0, 1.0) +  # Max temperature anomaly
                0.3 * min(mean_abs_delta / 5.0, 1.0) +  # Mean anomaly
                0.2 * std_normalized +                   # Variability
                0.1 * delta.confidence_score             # Ensemble confidence
            )
            
            logger.info(f"Weather impact score calculated: {impact_score:.3f}")
            return min(impact_score, 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate weather delta score: {e}")
            return 0.0
    
    async def send_weather_delta_to_gemini(self, delta: WeatherDelta, 
                                         market_sentiment: Dict[str, Any]) -> Optional[TradeSignal]:
        """Send weather delta to Gemini Pro for trade validation"""
        try:
            weather_score = self.calculate_weather_delta_score(delta)
            
            payload = {
                "timestamp": delta.timestamp.isoformat(),
                "weather_data": {
                    "max_delta": delta.max_delta,
                    "min_delta": delta.min_delta,
                    "mean_delta": delta.mean_delta,
                    "std_delta": delta.std_delta,
                    "region": delta.region,
                    "confidence_score": delta.confidence_score,
                    "impact_score": weather_score
                },
                "market_sentiment": market_sentiment,
                "request_type": "trade_validation"
            }
            
            logger.info(f"Sending weather delta to Gemini Pro: {delta.region}")
            
            async with self.session.post(
                f"{self.cloud_run_url}/validate-trade",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    return TradeSignal(
                        timestamp=datetime.fromisoformat(result['timestamp']),
                        action=result['action'],
                        confidence=result['confidence'],
                        reasoning=result['reasoning'],
                        market_contract=result['market_contract'],
                        weather_impact_score=result['weather_impact_score']
                    )
                else:
                    logger.error(f"Gemini Pro request failed: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("GCP Cloud Run request timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to send weather delta to Gemini: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check GCP Cloud Run service health"""
        try:
            async with self.session.get(f"{self.cloud_run_url}/health") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"GCP health check failed: {e}")
            return False

class WeatherDeltaProcessor:
    """Processes weather deltas and coordinates with GCP bridge"""
    
    def __init__(self, gcp_bridge: GCPBridge):
        self.gcp_bridge = gcp_bridge
        self.processed_deltas = []
        
    def create_weather_delta_from_data(self, delta_data: Dict, timestamp: datetime) -> WeatherDelta:
        """Create WeatherDelta object from processed data"""
        try:
            # Calculate confidence score based on ensemble consistency
            confidence = min(1.0 - (delta_data['std_delta'] / max(abs(delta_data['max_delta']), 0.1)), 1.0)
            
            return WeatherDelta(
                timestamp=timestamp,
                max_delta=float(delta_data['max_delta']),
                min_delta=float(delta_data['min_delta']),
                mean_delta=float(delta_data['mean_delta']),
                std_delta=float(delta_data['std_delta']),
                region="Tokyo",  # Can be made configurable
                confidence_score=confidence
            )
        except Exception as e:
            logger.error(f"Failed to create WeatherDelta: {e}")
            raise
    
    async def process_weather_delta(self, delta_data: Dict, 
                                  market_sentiment: Dict[str, Any]) -> Optional[TradeSignal]:
        """Process weather delta and get trade validation from Gemini"""
        try:
            timestamp = datetime.now()
            weather_delta = self.create_weather_delta_from_data(delta_data, timestamp)
            
            # Send to Gemini Pro for validation
            trade_signal = await self.gcp_bridge.send_weather_delta_to_gemini(
                weather_delta, market_sentiment
            )
            
            if trade_signal:
                self.processed_deltas.append({
                    'timestamp': timestamp,
                    'weather_delta': weather_delta,
                    'trade_signal': trade_signal
                })
                
                logger.info(f"Trade signal received: {trade_signal.action} "
                          f"(confidence: {trade_signal.confidence:.2f})")
            
            return trade_signal
            
        except Exception as e:
            logger.error(f"Failed to process weather delta: {e}")
            return None
    
    def get_processed_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of processed deltas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_deltas = [d for d in self.processed_deltas if d['timestamp'] > cutoff_time]
        
        if not recent_deltas:
            return {"total_processed": 0}
        
        actions = [d['trade_signal'].action for d in recent_deltas]
        confidence_scores = [d['trade_signal'].confidence for d in recent_deltas]
        
        return {
            "total_processed": len(recent_deltas),
            "action_distribution": {
                "BUY": actions.count("BUY"),
                "SELL": actions.count("SELL"),
                "HOLD": actions.count("HOLD")
            },
            "avg_confidence": np.mean(confidence_scores),
            "max_confidence": max(confidence_scores),
            "min_confidence": min(confidence_scores)
        }

async def test_gcp_bridge():
    """Test the GCP bridge functionality"""
    cloud_run_url = "https://sentinel-reasoning-xxxxx-uc.a.run.app"
    
    async with GCPBridge(cloud_run_url) as bridge:
        # Health check
        if await bridge.health_check():
            logger.info("✓ GCP Cloud Run service is healthy")
        else:
            logger.error("✗ GCP Cloud Run service is unavailable")
            return
        
        # Test weather delta processing
        processor = WeatherDeltaProcessor(bridge)
        
        test_delta = {
            "max_delta": 8.5,
            "min_delta": -3.2,
            "mean_delta": 2.1,
            "std_delta": 1.8
        }
        
        test_sentiment = {
            "polymarket_volume": 150000,
            "price_movement": 0.05,
            "social_sentiment": 0.65
        }
        
        signal = await processor.process_weather_delta(test_delta, test_sentiment)
        
        if signal:
            logger.info(f"✓ Test successful: {signal.action}")
        else:
            logger.error("✗ Test failed")

if __name__ == "__main__":
    asyncio.run(test_gcp_bridge())
