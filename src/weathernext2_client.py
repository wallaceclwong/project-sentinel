#!/usr/bin/env python3
"""
PROJECT SENTINEL - WeatherNext 2 API Client
Real-time ensemble forecasting and weather volatility data
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class WeatherNext2Ensemble:
    """WeatherNext 2 ensemble forecast data"""
    location: str
    timestamp: str
    forecast_hours: List[int]
    temperature_ensemble: List[float]
    ensemble_mean: float
    ensemble_std: float
    ensemble_spread: float
    consensus: float
    confidence: float
    volatility_index: float

@dataclass
class WeatherNext2Current:
    """Current weather conditions from WeatherNext 2"""
    location: str
    timestamp: str
    temperature: float
    feels_like: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    visibility: float
    uv_index: float
    weather_condition: str

class WeatherNext2Client:
    """WeatherNext 2 API client for real-time weather data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("WEATHERNEXT2_API_KEY")
        self.base_url = "https://api.weathernext2.com/v1"
        self.session = None
        
        # Rate limiting
        self.requests_per_minute = 60
        self.request_count = 0
        self.last_reset = datetime.now()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        if (now - self.last_reset).seconds >= 60:
            self.request_count = 0
            self.last_reset = now
        
        if self.request_count >= self.requests_per_minute:
            wait_time = 60 - (now - self.last_reset).seconds
            logger.warning(f"Rate limit reached, waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)
            self.request_count = 0
            self.last_reset = datetime.now()
        
        self.request_count += 1
    
    async def fetch_ensemble_forecast(self, location: str, hours: int = 168) -> Optional[WeatherNext2Ensemble]:
        """Fetch ensemble forecast for location"""
        
        await self._check_rate_limit()
        
        url = f"{self.base_url}/ensemble"
        params = {
            "location": location,
            "hours": hours,
            "variables": "temperature",
            "format": "json"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_ensemble_data(location, data)
                else:
                    logger.error(f"WeatherNext 2 API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching ensemble forecast: {e}")
            return None
    
    async def fetch_current_weather(self, location: str) -> Optional[WeatherNext2Current]:
        """Fetch current weather conditions"""
        
        await self._check_rate_limit()
        
        url = f"{self.base_url}/current"
        params = {
            "location": location,
            "format": "json"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_current_data(location, data)
                else:
                    logger.error(f"WeatherNext 2 API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return None
    
    async def fetch_weather_volatility_index(self, location: str, days: int = 30) -> Optional[float]:
        """Fetch weather volatility index for risk management"""
        
        await self._check_rate_limit()
        
        url = f"{self.base_url}/volatility"
        params = {
            "location": location,
            "days": days,
            "format": "json"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data.get("volatility_index", 0.5))
                else:
                    logger.error(f"WeatherNext 2 API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching volatility index: {e}")
            return None
    
    def _parse_ensemble_data(self, location: str, data: Dict) -> WeatherNext2Ensemble:
        """Parse ensemble forecast data from API response"""
        
        # Extract ensemble members
        ensemble_data = data.get("ensemble", {})
        temperature_ensemble = ensemble_data.get("temperature", [])
        
        # Calculate statistics
        if temperature_ensemble:
            import statistics
            ensemble_mean = statistics.mean(temperature_ensemble)
            ensemble_std = statistics.stdev(temperature_ensemble) if len(temperature_ensemble) > 1 else 0.0
            ensemble_spread = max(temperature_ensemble) - min(temperature_ensemble)
            
            # Calculate consensus (agreement between ensemble members)
            consensus = 1.0 - (ensemble_spread / 20.0)  # Normalize to 0-1
            consensus = max(0.0, min(1.0, consensus))
            
            # Calculate confidence based on ensemble spread
            confidence = 1.0 - (ensemble_std / 10.0)
            confidence = max(0.0, min(1.0, confidence))
        else:
            ensemble_mean = 0.0
            ensemble_std = 0.0
            ensemble_spread = 0.0
            consensus = 0.5
            confidence = 0.5
        
        return WeatherNext2Ensemble(
            location=location,
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            forecast_hours=data.get("forecast_hours", list(range(168))),
            temperature_ensemble=temperature_ensemble,
            ensemble_mean=ensemble_mean,
            ensemble_std=ensemble_std,
            ensemble_spread=ensemble_spread,
            consensus=consensus,
            confidence=confidence,
            volatility_index=data.get("volatility_index", 0.5)
        )
    
    def _parse_current_data(self, location: str, data: Dict) -> WeatherNext2Current:
        """Parse current weather data from API response"""
        
        current = data.get("current", {})
        
        return WeatherNext2Current(
            location=location,
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            temperature=float(current.get("temperature", 0.0)),
            feels_like=float(current.get("feels_like", 0.0)),
            humidity=float(current.get("humidity", 0.0)),
            pressure=float(current.get("pressure", 0.0)),
            wind_speed=float(current.get("wind_speed", 0.0)),
            wind_direction=float(current.get("wind_direction", 0.0)),
            visibility=float(current.get("visibility", 0.0)),
            uv_index=float(current.get("uv_index", 0.0)),
            weather_condition=current.get("condition", "unknown")
        )
    
    async def get_trading_signals(self, location: str) -> Dict[str, Any]:
        """Get comprehensive trading signals for location"""
        
        # Fetch ensemble forecast
        ensemble = await self.fetch_ensemble_forecast(location)
        if not ensemble:
            return {"error": "Failed to fetch ensemble forecast"}
        
        # Fetch current weather
        current = await self.fetch_current_weather(location)
        
        # Fetch volatility index
        volatility = await self.fetch_weather_volatility_index(location)
        
        # Generate trading signals
        signals = self._generate_trading_signals(ensemble, current, volatility)
        
        return {
            "location": location,
            "timestamp": datetime.now().isoformat(),
            "ensemble": ensemble,
            "current": current,
            "volatility_index": volatility,
            "signals": signals
        }
    
    def _generate_trading_signals(self, ensemble: WeatherNext2Ensemble, 
                                 current: Optional[WeatherNext2Current],
                                 volatility: Optional[float]) -> Dict[str, Any]:
        """Generate trading signals from weather data"""
        
        signals = {
            "temperature_signal": "HOLD",
            "signal_strength": 0.0,
            "confidence": ensemble.confidence,
            "volatility_adjustment": 1.0,
            "risk_level": "MEDIUM"
        }
        
        # Temperature signal based on ensemble forecast
        if ensemble.ensemble_mean > 20.0:  # Hot forecast
            signals["temperature_signal"] = "BUY"
            signals["signal_strength"] = min(1.0, (ensemble.ensemble_mean - 20.0) / 10.0)
        elif ensemble.ensemble_mean < 10.0:  # Cold forecast
            signals["temperature_signal"] = "SELL"
            signals["signal_strength"] = min(1.0, (10.0 - ensemble.ensemble_mean) / 10.0)
        
        # Adjust for volatility
        if volatility:
            if volatility > 0.7:
                signals["volatility_adjustment"] = 0.7  # Reduce position size
                signals["risk_level"] = "HIGH"
            elif volatility < 0.3:
                signals["volatility_adjustment"] = 1.3  # Increase position size
                signals["risk_level"] = "LOW"
        
        # Final confidence calculation
        signals["final_confidence"] = (
            signals["confidence"] * 
            signals["volatility_adjustment"] * 
            (1.0 + signals["signal_strength"] * 0.2)
        )
        
        return signals


async def main():
    """Test WeatherNext 2 client"""
    print("🌤️ WEATHERNEXT 2 CLIENT TEST")
    print("=" * 40)
    
    # Test with mock data (since we don't have real API key)
    client = WeatherNext2Client(api_key="test_key")
    
    async with client:
        print("📊 Testing ensemble forecast...")
        ensemble = await client.fetch_ensemble_forecast("Tokyo")
        if ensemble:
            print(f"   Location: {ensemble.location}")
            print(f"   Ensemble Mean: {ensemble.ensemble_mean:.1f}°C")
            print(f"   Consensus: {ensemble.consensus:.1%}")
            print(f"   Confidence: {ensemble.confidence:.1%}")
        else:
            print("   ❌ Failed to fetch ensemble (expected without API key)")
        
        print("\n🌡️ Testing current weather...")
        current = await client.fetch_current_weather("Tokyo")
        if current:
            print(f"   Location: {current.location}")
            print(f"   Temperature: {current.temperature:.1f}°C")
            print(f"   Condition: {current.weather_condition}")
        else:
            print("   ❌ Failed to fetch current weather (expected without API key)")
        
        print("\n📈 Testing trading signals...")
        signals = await client.get_trading_signals("Tokyo")
        if "error" not in signals:
            print(f"   Signal: {signals['signals']['temperature_signal']}")
            print(f"   Strength: {signals['signals']['signal_strength']:.2f}")
            print(f"   Confidence: {signals['signals']['final_confidence']:.1%}")
        else:
            print(f"   ❌ {signals['error']}")
    
    print("\n✅ WeatherNext 2 client ready for integration!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
