#!/usr/bin/env python3
"""
PROJECT SENTINEL - NOAA Ensemble Weather System
Enhanced weather data with ensemble forecasts and synthetic ensembles
"""

import asyncio
import json
import logging
import math
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import aiohttp
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class EnsembleMember:
    """Individual ensemble forecast member"""
    member_id: int
    temperature: float
    precipitation: float
    wind_speed: float
    confidence: float

@dataclass
class EnsembleForecast:
    """Complete ensemble forecast for a date"""
    date: str
    region: str
    members: List[EnsembleMember]
    mean_temp: float
    std_temp: float
    spread: float
    consensus: float

@dataclass
class WeatherPattern:
    """Recognized weather pattern"""
    pattern_type: str
    confidence: float
    description: str
    typical_duration: int  # days
    temperature_trend: str  # warming, cooling, stable

class NOAAEnsembleSystem:
    """Enhanced NOAA weather system with ensemble capabilities"""
    
    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent / "data" / "ensemble_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # NOAA API endpoints
        self.NOAA_API_BASE = "https://www.ncdc.noaa.gov/cdo-web/api/v2"
        self.GEFS_API = "https://www.ncei.noaa.gov/data/global-ensemble-forecast-system/access"
        
        # Pattern recognition templates
        self.patterns = {
            "heat_wave": {
                "temp_threshold": 32.0,  # °C
                "duration": 3,
                "persistence": 0.8
            },
            "cold_snap": {
                "temp_threshold": 0.0,
                "duration": 3,
                "persistence": 0.7
            },
            "unusual_warming": {
                "temp_anomaly": 5.0,
                "duration": 2,
                "persistence": 0.6
            },
            "unusual_cooling": {
                "temp_anomaly": -5.0,
                "duration": 2,
                "persistence": 0.6
            }
        }
    
    async def fetch_gefs_ensemble(self, date: str, region: str) -> Optional[EnsembleForecast]:
        """Fetch GEFS ensemble forecast data from NOAA"""
        cache_file = self.cache_dir / f"gefs_{region}_{date}.json"
        
        # Check cache first
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return self._parse_gefs_data(data, date, region)
        
        try:
            # GEFS ensemble data (mock implementation - real would need NOAA API key)
            # For now, we'll create synthetic ensemble based on historical variance
            return await self._create_synthetic_ensemble(date, region)
            
        except Exception as e:
            logger.error(f"Failed to fetch GEFS ensemble for {date}: {e}")
            return None
    
    async def _create_synthetic_ensemble(self, date: str, region: str) -> EnsembleForecast:
        """Create synthetic ensemble from historical variance patterns"""
        
        # Load historical data for variance calculation
        data_file = Path(__file__).parent.parent / "data" / "sentinel_backtest_data.json"
        
        if not data_file.exists():
            # Fallback to basic synthetic ensemble
            return self._basic_synthetic_ensemble(date, region)
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        records = data.get('weather', {}).get(region, [])
        if not records:
            return self._basic_synthetic_ensemble(date, region)
        
        # Calculate historical variance by season
        seasonal_variance = self._calculate_seasonal_variance(records)
        
        # Find similar historical dates for pattern matching
        target_date = datetime.strptime(date, "%Y-%m-%d")
        similar_dates = self._find_similar_dates(records, target_date)
        
        # Generate ensemble members based on historical patterns
        members = []
        base_temp = self._estimate_base_temperature(records, target_date)
        
        for i in range(31):  # 31 ensemble members (GEFS standard)
            # Add seasonal variance + random perturbation
            seasonal_var = seasonal_variance.get(target_date.month, 2.0)
            random_var = random.gauss(0, seasonal_var * 0.5)
            
            # Pattern-based adjustment
            pattern_adj = self._calculate_pattern_adjustment(similar_dates, i)
            
            temp = base_temp + random_var + pattern_adj
            
            # Calculate confidence based on ensemble spread
            confidence = max(0.3, min(0.95, 1.0 - abs(random_var) / 10))
            
            members.append(EnsembleMember(
                member_id=i,
                temperature=round(temp, 1),
                precipitation=random.uniform(0, 5),  # Synthetic precipitation
                wind_speed=random.uniform(5, 25),    # Synthetic wind
                confidence=round(confidence, 2)
            ))
        
        # Calculate ensemble statistics
        temps = [m.temperature for m in members]
        mean_temp = statistics.mean(temps)
        std_temp = statistics.stdev(temps)
        spread = max(temps) - min(temps)
        consensus = 1.0 - (spread / 20.0)  # Normalized consensus score
        
        forecast = EnsembleForecast(
            date=date,
            region=region,
            members=members,
            mean_temp=round(mean_temp, 1),
            std_temp=round(std_temp, 2),
            spread=round(spread, 1),
            consensus=round(consensus, 2)
        )
        
        # Cache the result
        cache_file = self.cache_dir / f"synthetic_{region}_{date}.json"
        with open(cache_file, 'w') as f:
            json.dump({
                'date': date,
                'region': region,
                'mean_temp': forecast.mean_temp,
                'std_temp': forecast.std_temp,
                'spread': forecast.spread,
                'consensus': forecast.consensus,
                'members': [
                    {
                        'member_id': m.member_id,
                        'temperature': m.temperature,
                        'confidence': m.confidence
                    } for m in members
                ]
            }, f, indent=2)
        
        return forecast
    
    def _basic_synthetic_ensemble(self, date: str, region: str) -> EnsembleForecast:
        """Basic synthetic ensemble when no historical data available"""
        members = []
        base_temp = 15.0  # Default temperature
        
        for i in range(31):
            # Simple random variation
            temp = base_temp + random.gauss(0, 3.0)
            confidence = max(0.3, min(0.95, 1.0 - abs(temp - base_temp) / 10))
            
            members.append(EnsembleMember(
                member_id=i,
                temperature=round(temp, 1),
                precipitation=random.uniform(0, 5),
                wind_speed=random.uniform(5, 25),
                confidence=round(confidence, 2)
            ))
        
        temps = [m.temperature for m in members]
        mean_temp = statistics.mean(temps)
        std_temp = statistics.stdev(temps)
        spread = max(temps) - min(temps)
        consensus = 1.0 - (spread / 20.0)
        
        return EnsembleForecast(
            date=date,
            region=region,
            members=members,
            mean_temp=round(mean_temp, 1),
            std_temp=round(std_temp, 2),
            spread=round(spread, 1),
            consensus=round(consensus, 2)
        )
    
    def _calculate_seasonal_variance(self, records: List[Dict]) -> Dict[int, float]:
        """Calculate temperature variance by month"""
        monthly_temps = {}
        
        for record in records:
            try:
                date = datetime.strptime(record['date'], "%Y-%m-%d")
                month = date.month
                temp = record['temp_avg']
                
                if month not in monthly_temps:
                    monthly_temps[month] = []
                monthly_temps[month].append(temp)
            except:
                continue
        
        variance = {}
        for month, temps in monthly_temps.items():
            if len(temps) > 1:
                variance[month] = statistics.stdev(temps)
            else:
                variance[month] = 2.0  # Default variance
        
        return variance
    
    def _find_similar_dates(self, records: List[Dict], target_date: datetime) -> List[Dict]:
        """Find historically similar dates for pattern matching"""
        target_month = target_date.month
        target_day = target_date.day
        
        similar = []
        for record in records:
            try:
                date = datetime.strptime(record['date'], "%Y-%m-%d")
                # Same month, within 7 days
                if date.month == target_month and abs(date.day - target_day) <= 7:
                    similar.append(record)
            except:
                continue
        
        return similar[:10]  # Top 10 similar dates
    
    def _estimate_base_temperature(self, records: List[Dict], target_date: datetime) -> float:
        """Estimate base temperature from historical averages"""
        target_month = target_month = target_date.month
        month_temps = []
        
        for record in records:
            try:
                date = datetime.strptime(record['date'], "%Y-%m-%d")
                if date.month == target_month:
                    month_temps.append(record['temp_avg'])
            except:
                continue
        
        if month_temps:
            return statistics.mean(month_temps)
        else:
            # Seasonal temperature estimation
            day_of_year = target_date.timetuple().tm_yday
            return 15 + 15 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    
    def _calculate_pattern_adjustment(self, similar_dates: List[Dict], member_id: int) -> float:
        """Calculate temperature adjustment based on historical patterns"""
        if not similar_dates:
            return 0.0
        
        # Use member_id to create deterministic but varied adjustments
        random.seed(member_id)
        
        # Sample from similar dates' deviations
        adjustments = []
        base_temp = self._estimate_base_temperature(similar_dates, datetime.now())
        
        for record in similar_dates:
            deviation = record['temp_avg'] - base_temp
            adjustments.append(deviation)
        
        if adjustments:
            return random.choice(adjustments) * random.uniform(0.5, 1.5)
        else:
            return random.gauss(0, 1.0)
    
    def _parse_gefs_data(self, data: Dict, date: str, region: str) -> EnsembleForecast:
        """Parse real GEFS ensemble data (when available)"""
        members = []
        
        for i, member_data in enumerate(data.get('ensemble_members', [])):
            members.append(EnsembleMember(
                member_id=i,
                temperature=member_data.get('temperature', 15.0),
                precipitation=member_data.get('precipitation', 0.0),
                wind_speed=member_data.get('wind_speed', 10.0),
                confidence=member_data.get('confidence', 0.7)
            ))
        
        temps = [m.temperature for m in members]
        mean_temp = statistics.mean(temps) if temps else 15.0
        std_temp = statistics.stdev(temps) if len(temps) > 1 else 1.0
        spread = max(temps) - min(temps) if temps else 0.0
        consensus = 1.0 - (spread / 20.0)
        
        return EnsembleForecast(
            date=date,
            region=region,
            members=members,
            mean_temp=round(mean_temp, 1),
            std_temp=round(std_temp, 2),
            spread=round(spread, 1),
            consensus=round(consensus, 2)
        )
    
    def detect_weather_patterns(self, forecasts: List[EnsembleForecast]) -> List[WeatherPattern]:
        """Detect weather patterns from ensemble forecasts"""
        patterns = []
        
        if len(forecasts) < 3:
            return patterns
        
        # Analyze temperature trends
        temps = [f.mean_temp for f in forecasts[-7:]]  # Last 7 days
        
        # Heat wave detection
        if all(t > self.patterns["heat_wave"]["temp_threshold"] for t in temps[-3:]):
            patterns.append(WeatherPattern(
                pattern_type="heat_wave",
                confidence=0.8,
                description="Extended period of unusually high temperatures",
                typical_duration=self.patterns["heat_wave"]["duration"],
                temperature_trend="warming"
            ))
        
        # Cold snap detection
        if all(t < self.patterns["cold_snap"]["temp_threshold"] for t in temps[-3:]):
            patterns.append(WeatherPattern(
                pattern_type="cold_snap",
                confidence=0.7,
                description="Extended period of unusually low temperatures",
                typical_duration=self.patterns["cold_snap"]["duration"],
                temperature_trend="cooling"
            ))
        
        # Unusual warming/cooling
        if len(temps) >= 2:
            recent_change = temps[-1] - temps[-2]
            if recent_change > self.patterns["unusual_warming"]["temp_anomaly"]:
                patterns.append(WeatherPattern(
                    pattern_type="unusual_warming",
                    confidence=0.6,
                    description="Rapid temperature increase detected",
                    typical_duration=self.patterns["unusual_warming"]["duration"],
                    temperature_trend="warming"
                ))
            elif recent_change < self.patterns["unusual_cooling"]["temp_anomaly"]:
                patterns.append(WeatherPattern(
                    pattern_type="unusual_cooling",
                    confidence=0.6,
                    description="Rapid temperature decrease detected",
                    typical_duration=self.patterns["unusual_cooling"]["duration"],
                    temperature_trend="cooling"
                ))
        
        return patterns
    
    def calculate_ensemble_confidence(self, forecast: EnsembleForecast) -> float:
        """Calculate ensemble confidence based on spread and consensus"""
        # High confidence = low spread, high consensus
        spread_factor = max(0, 1.0 - (forecast.spread / 10.0))
        consensus_factor = forecast.consensus
        
        return (spread_factor + consensus_factor) / 2.0
    
    def get_ensemble_statistics(self, forecasts: List[EnsembleForecast]) -> Dict[str, Any]:
        """Get comprehensive ensemble statistics"""
        if not forecasts:
            return {}
        
        recent = forecasts[-7:]  # Last 7 days
        temps = [f.mean_temp for f in recent]
        spreads = [f.spread for f in recent]
        confidences = [self.calculate_ensemble_confidence(f) for f in recent]
        
        return {
            "period": f"{recent[0].date} to {recent[-1].date}",
            "temperature_stats": {
                "mean": statistics.mean(temps),
                "std": statistics.stdev(temps) if len(temps) > 1 else 0,
                "min": min(temps),
                "max": max(temps),
                "trend": "warming" if temps[-1] > temps[0] else "cooling"
            },
            "ensemble_stats": {
                "avg_spread": statistics.mean(spreads),
                "avg_consensus": statistics.mean([f.consensus for f in recent]),
                "avg_confidence": statistics.mean(confidences)
            },
            "forecast_quality": "high" if statistics.mean(confidences) > 0.7 else "medium" if statistics.mean(confidences) > 0.5 else "low"
        }


async def main():
    """Test the NOAA ensemble system"""
    print("🌤️ NOAA Ensemble System Test")
    print("=" * 40)
    
    ensemble_system = NOAAEnsembleSystem()
    
    # Test synthetic ensemble generation
    test_date = "2024-03-15"
    forecast = await ensemble_system.fetch_gefs_ensemble(test_date, "Tokyo")
    
    if forecast:
        print(f"✅ Ensemble forecast for {test_date}:")
        print(f"   Mean Temp: {forecast.mean_temp}°C")
        print(f"   Std Dev: {forecast.std_temp}°C")
        print(f"   Spread: {forecast.spread}°C")
        print(f"   Consensus: {forecast.consensus}")
        print(f"   Members: {len(forecast.members)}")
        
        # Test pattern detection
        patterns = ensemble_system.detect_weather_patterns([forecast])
        if patterns:
            print(f"   Patterns: {[p.pattern_type for p in patterns]}")
        
        # Test statistics
        stats = ensemble_system.get_ensemble_statistics([forecast])
        print(f"   Quality: {stats.get('forecast_quality', 'unknown')}")
    
    print("\n✅ NOAA Ensemble System operational")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
