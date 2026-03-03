#!/usr/bin/env python3
"""
PROJECT SENTINEL - Real Data Fetcher
Fetches historical weather data from NOAA and market data from Polymarket
for production-grade backtesting validation.
"""

import asyncio
import aiohttp
import csv
import io
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# ==================== DATA MODELS ====================

@dataclass
class WeatherRecord:
    """Real weather observation from NOAA"""
    date: str
    station: str
    region: str
    temp_avg: float      # Average temperature (°C)
    temp_max: float      # Maximum temperature (°C)
    temp_min: float      # Minimum temperature (°C)
    precipitation: float # Precipitation (mm)
    wind_speed: float    # Wind speed (m/s)

@dataclass
class MarketRecord:
    """Polymarket market price record"""
    date: str
    token_id: str
    question: str
    price: float
    volume: float


# ==================== NOAA WEATHER FETCHER ====================

class NOAAWeatherFetcher:
    """Fetches historical weather data from NOAA Global Summary of the Day (GSOD)"""
    
    # NOAA GSOD via BigQuery-compatible CSV endpoint
    GSOD_BASE = "https://www.ncei.noaa.gov/access/services/data/v1"
    
    # Key weather station IDs
    STATIONS = {
        "Tokyo": "47662099999",       # Tokyo International
        "Osaka": "47772099999",       # Osaka/Kansai
        "Singapore": "48698099999",   # Singapore Changi
        "Hong_Kong": "45007099999",   # Hong Kong Observatory
        "Sydney": "94767099999",      # Sydney Airport
        "London": "03772099999",      # London Heathrow
        "New_York": "72503014732",    # JFK Airport
    }
    
    def __init__(self):
        self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "data", "weather_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def fetch_station_data(self, station_id: str, start_date: str, 
                                  end_date: str, region: str = "Tokyo") -> List[WeatherRecord]:
        """Fetch weather data from NOAA GSOD for a specific station"""
        
        # Check cache first
        cache_file = os.path.join(self.cache_dir, f"{region}_{start_date}_{end_date}.json")
        if os.path.exists(cache_file):
            logger.info(f"Loading cached weather data: {cache_file}")
            with open(cache_file, "r") as f:
                data = json.load(f)
                return [WeatherRecord(**r) for r in data]
        
        records = []
        
        # NOAA GSOD API
        url = self.GSOD_BASE
        params = {
            "dataset": "global-summary-of-the-day",
            "stations": station_id,
            "startDate": start_date,
            "endDate": end_date,
            "format": "json",
            "units": "metric",
            "dataTypes": "TEMP,MAX,MIN,PRCP,WDSP"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get("Content-Type", "")
                        text = await resp.text()
                        
                        if "json" in content_type:
                            data = json.loads(text)
                            for entry in data:
                                records.append(self._parse_gsod_json(entry, region))
                        else:
                            # CSV fallback
                            records = self._parse_gsod_csv(text, region)
                    else:
                        logger.warning(f"NOAA API returned {resp.status}, trying fallback...")
                        records = await self._fetch_fallback(station_id, start_date, end_date, region)
        except Exception as e:
            logger.warning(f"NOAA API error: {e}, trying fallback...")
            records = await self._fetch_fallback(station_id, start_date, end_date, region)
        
        if not records:
            logger.warning("No data from NOAA API, generating from Open-Meteo...")
            records = await self._fetch_open_meteo(region, start_date, end_date)
        
        # Cache results
        if records:
            with open(cache_file, "w") as f:
                json.dump([asdict(r) for r in records], f, indent=2)
            logger.info(f"Cached {len(records)} weather records to {cache_file}")
        
        return records
    
    async def _fetch_fallback(self, station_id: str, start_date: str,
                               end_date: str, region: str) -> List[WeatherRecord]:
        """Fallback: try alternative NOAA endpoint"""
        url = f"https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{start_date[:4]}/{station_id}.csv"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return self._parse_gsod_csv(text, region)
        except Exception as e:
            logger.warning(f"NOAA fallback failed: {e}")
        
        return []
    
    async def _fetch_open_meteo(self, region: str, start_date: str, 
                                 end_date: str) -> List[WeatherRecord]:
        """Fetch from Open-Meteo API (free, no API key needed)"""
        
        # Coordinates for key cities
        coords = {
            "Tokyo": (35.6762, 139.6503),
            "Osaka": (34.6937, 135.5023),
            "Singapore": (1.3521, 103.8198),
            "Hong_Kong": (22.3193, 114.1694),
            "Sydney": (-33.8688, 151.2093),
            "London": (51.5074, -0.1278),
            "New_York": (40.7128, -74.0060),
        }
        
        lat, lon = coords.get(region, (35.6762, 139.6503))
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"
        }
        
        records = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        daily = data.get("daily", {})
                        dates = daily.get("time", [])
                        temp_max = daily.get("temperature_2m_max", [])
                        temp_min = daily.get("temperature_2m_min", [])
                        temp_avg = daily.get("temperature_2m_mean", [])
                        precip = daily.get("precipitation_sum", [])
                        wind = daily.get("wind_speed_10m_max", [])
                        
                        for i, date in enumerate(dates):
                            records.append(WeatherRecord(
                                date=date,
                                station=f"open_meteo_{region}",
                                region=region,
                                temp_avg=round(temp_avg[i], 1) if i < len(temp_avg) and temp_avg[i] is not None else 0,
                                temp_max=round(temp_max[i], 1) if i < len(temp_max) and temp_max[i] is not None else 0,
                                temp_min=round(temp_min[i], 1) if i < len(temp_min) and temp_min[i] is not None else 0,
                                precipitation=round(precip[i], 1) if i < len(precip) and precip[i] is not None else 0,
                                wind_speed=round(wind[i] / 3.6, 1) if i < len(wind) and wind[i] is not None else 0  # km/h to m/s
                            ))
                        
                        logger.info(f"Fetched {len(records)} records from Open-Meteo for {region}")
                    else:
                        logger.error(f"Open-Meteo returned {resp.status}")
        except Exception as e:
            logger.error(f"Open-Meteo fetch failed: {e}")
        
        return records
    
    @staticmethod
    def _f_to_c(f: float) -> float:
        """Convert Fahrenheit to Celsius"""
        return round((f - 32) * 5 / 9, 1)
    
    def _parse_gsod_json(self, entry: Dict, region: str) -> WeatherRecord:
        """Parse a GSOD JSON entry"""
        def safe_float(val, default=0.0):
            try:
                v = float(val)
                return default if v > 900 else v  # GSOD uses 9999 for missing
            except (ValueError, TypeError):
                return default
        
        return WeatherRecord(
            date=entry.get("DATE", ""),
            station=entry.get("STATION", ""),
            region=region,
            temp_avg=self._f_to_c(safe_float(entry.get("TEMP"))),
            temp_max=self._f_to_c(safe_float(entry.get("MAX"))),
            temp_min=self._f_to_c(safe_float(entry.get("MIN"))),
            precipitation=safe_float(entry.get("PRCP")),
            wind_speed=safe_float(entry.get("WDSP"))
        )
    
    def _parse_gsod_csv(self, csv_text: str, region: str) -> List[WeatherRecord]:
        """Parse GSOD CSV data"""
        records = []
        reader = csv.DictReader(io.StringIO(csv_text))
        
        for row in reader:
            def safe_float(key, default=0.0):
                try:
                    v = float(row.get(key, default))
                    return default if v > 900 else v
                except (ValueError, TypeError):
                    return default
            
            records.append(WeatherRecord(
                date=row.get("DATE", ""),
                station=row.get("STATION", ""),
                region=region,
                temp_avg=self._f_to_c(safe_float("TEMP")),
                temp_max=self._f_to_c(safe_float("MAX")),
                temp_min=self._f_to_c(safe_float("MIN")),
                precipitation=safe_float("PRCP"),
                wind_speed=safe_float("WDSP")
            ))
        
        return records
    
    async def fetch_tokyo(self, start_date: str = "2023-01-01",
                           end_date: str = "2025-12-31") -> List[WeatherRecord]:
        """Convenience method to fetch Tokyo weather data"""
        return await self.fetch_station_data(
            self.STATIONS["Tokyo"], start_date, end_date, "Tokyo"
        )


# ==================== POLYMARKET FETCHER ====================

class PolymarketDataFetcher:
    """Fetches historical market data from Polymarket"""
    
    CLOB_URL = "https://clob.polymarket.com"
    GAMMA_URL = "https://gamma-api.polymarket.com"
    
    def __init__(self):
        self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "data", "market_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def search_weather_markets(self) -> List[Dict]:
        """Search Polymarket for weather-related markets"""
        # Strict weather keywords - multi-word to avoid sports matches
        weather_keywords = [
            "weather forecast", "temperature record", "hurricane category",
            "tropical storm", "tornado warning", "flooding", "drought",
            "heat wave", "heatwave", "cold snap", "snowfall", "snowstorm",
            "climate change", "el nino", "la nina", "celsius", "fahrenheit",
            "wildfire", "weather event", "record high", "record low",
            "global warming", "ice storm", "blizzard", "monsoon",
            "typhoon", "cyclone", "rainfall record", "temperature above",
            "temperature below", "degrees celsius", "degrees fahrenheit",
        ]
        # Single keywords that are safe (unlikely to match sports)
        safe_keywords = [
            "weather", "typhoon", "cyclone", "blizzard", "monsoon",
            "wildfire", "el nino", "la nina", "heatwave", "drought"
        ]
        
        # Sports/entertainment terms to exclude
        exclude_terms = [
            "nba", "nfl", "nhl", "mlb", "fifa", "ufc", "boxing",
            "heat v", "heat beat", "hurricanes v", "hurricanes beat",
            "thunder", "lightning v", "storm v", "in-game", "playoff",
            "gross more", "box office", "movie", "film", "album",
            "bucks v", "lakers", "celtics", "warriors"
        ]
        
        all_markets = []
        
        def is_weather_market(title: str, desc: str) -> bool:
            text = f"{title} {desc}".lower()
            if any(ex in text for ex in exclude_terms):
                return False
            if any(kw in text for kw in safe_keywords):
                return True
            if any(kw in text for kw in weather_keywords):
                return True
            return False
        
        try:
            headers = {"Accept-Encoding": "gzip, deflate"}
            async with aiohttp.ClientSession(headers=headers) as session:
                # Search events
                async with session.get(
                    f"{self.GAMMA_URL}/events",
                    params={"limit": 200, "active": "true"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        events = await resp.json()
                        for event in events:
                            title = event.get("title", "").lower()
                            desc = event.get("description", "").lower()
                            
                            if is_weather_market(title, desc):
                                for market in event.get("markets", []):
                                    all_markets.append({
                                        "event_title": event.get("title"),
                                        "question": market.get("question"),
                                        "condition_id": market.get("conditionId"),
                                        "tokens": market.get("clobTokenIds", []),
                                        "volume": market.get("volume", 0),
                                        "liquidity": market.get("liquidity", 0),
                                        "active": market.get("active", False),
                                        "end_date": market.get("endDate"),
                                    })
                
                # Also search closed/resolved markets
                async with session.get(
                    f"{self.GAMMA_URL}/events",
                    params={"limit": 200, "closed": "true"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        events = await resp.json()
                        for event in events:
                            title = event.get("title", "").lower()
                            desc = event.get("description", "").lower()
                            
                            if is_weather_market(title, desc):
                                for market in event.get("markets", []):
                                    all_markets.append({
                                        "event_title": event.get("title"),
                                        "question": market.get("question"),
                                        "condition_id": market.get("conditionId"),
                                        "tokens": market.get("clobTokenIds", []),
                                        "volume": market.get("volume", 0),
                                        "liquidity": market.get("liquidity", 0),
                                        "active": market.get("active", False),
                                        "closed": True,
                                        "end_date": market.get("endDate"),
                                        "outcome": market.get("outcome"),
                                    })
        except Exception as e:
            logger.error(f"Polymarket search error: {e}")
        
        logger.info(f"Found {len(all_markets)} weather-related markets on Polymarket")
        return all_markets
    
    async def fetch_price_history(self, token_id: str, interval: str = "1d") -> List[Dict]:
        """Fetch price history for a specific token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.CLOB_URL}/prices-history",
                    params={"market": token_id, "interval": interval, "fidelity": 60},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        history = data.get("history", [])
                        logger.info(f"Fetched {len(history)} price points for {token_id[:20]}...")
                        return history
                    else:
                        logger.warning(f"Price history returned {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Price history fetch error: {e}")
            return []
    
    async def fetch_recent_trades(self, token_id: str) -> List[Dict]:
        """Fetch recent trades for a token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.CLOB_URL}/trades",
                    params={"market": token_id},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return []
        except Exception as e:
            logger.error(f"Trades fetch error: {e}")
            return []
    
    async def fetch_all_weather_data(self) -> Dict[str, Any]:
        """Fetch all available weather market data from Polymarket"""
        cache_file = os.path.join(self.cache_dir, "polymarket_weather_data.json")
        
        markets = await self.search_weather_markets()
        
        results = {
            "fetched_at": datetime.now().isoformat(),
            "total_markets": len(markets),
            "markets": markets,
            "price_histories": {}
        }
        
        # Fetch price history for markets with tokens
        for market in markets[:20]:  # Limit to 20 to avoid rate limits
            tokens = market.get("tokens", [])
            if tokens:
                token_id = tokens[0] if isinstance(tokens[0], str) else ""
                if token_id:
                    history = await self.fetch_price_history(token_id)
                    if history:
                        results["price_histories"][token_id] = {
                            "question": market.get("question"),
                            "history": history
                        }
                    await asyncio.sleep(0.5)  # Rate limit respect
        
        # Cache results
        with open(cache_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Cached Polymarket data to {cache_file}")
        
        return results


# ==================== COMBINED DATA FETCHER ====================

class SentinelDataFetcher:
    """Combined data fetcher for all PROJECT SENTINEL data needs"""
    
    def __init__(self):
        self.weather = NOAAWeatherFetcher()
        self.market = PolymarketDataFetcher()
    
    async def fetch_all(self, start_date: str = "2023-01-01",
                         end_date: str = "2025-12-31",
                         regions: List[str] = None) -> Dict[str, Any]:
        """Fetch all data needed for backtesting"""
        
        if regions is None:
            regions = ["Tokyo"]
        
        print(f"📡 Fetching real data for backtesting...")
        print(f"   Weather: {start_date} to {end_date}")
        print(f"   Regions: {', '.join(regions)}")
        
        # Fetch weather data for all regions
        weather_data = {}
        for region in regions:
            print(f"\n🌡️ Fetching {region} weather data...")
            records = await self.weather.fetch_station_data(
                self.weather.STATIONS.get(region, self.weather.STATIONS["Tokyo"]),
                start_date, end_date, region
            )
            weather_data[region] = records
            print(f"   ✅ {len(records)} daily records")
        
        # Fetch Polymarket data
        print(f"\n📊 Fetching Polymarket weather markets...")
        market_data = await self.market.fetch_all_weather_data()
        print(f"   ✅ {market_data['total_markets']} markets found")
        print(f"   ✅ {len(market_data['price_histories'])} with price history")
        
        # Summary
        total_weather = sum(len(r) for r in weather_data.values())
        
        result = {
            "fetched_at": datetime.now().isoformat(),
            "weather": {region: [asdict(r) for r in records] for region, records in weather_data.items()},
            "markets": market_data,
            "summary": {
                "weather_records": total_weather,
                "weather_regions": len(weather_data),
                "polymarket_markets": market_data["total_markets"],
                "price_histories": len(market_data["price_histories"]),
                "date_range": f"{start_date} to {end_date}"
            }
        }
        
        # Save combined dataset
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "sentinel_backtest_data.json")
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n📦 Data saved to: {output_file}")
        print(f"\n📊 SUMMARY:")
        print(f"   Weather Records: {total_weather}")
        print(f"   Polymarket Markets: {market_data['total_markets']}")
        print(f"   Price Histories: {len(market_data['price_histories'])}")
        
        return result


async def main():
    """Fetch all real data for backtesting"""
    fetcher = SentinelDataFetcher()
    
    result = await fetcher.fetch_all(
        start_date="2023-01-01",
        end_date="2025-12-31",
        regions=["Tokyo", "Singapore", "Hong_Kong"]
    )
    
    # Show weather data sample
    for region, records in result["weather"].items():
        if records:
            sample = records[0]
            latest = records[-1]
            print(f"\n🌡️ {region} Weather Sample:")
            print(f"   First: {sample['date']} - Avg: {sample['temp_avg']}°C, "
                  f"Max: {sample['temp_max']}°C, Min: {sample['temp_min']}°C")
            print(f"   Last:  {latest['date']} - Avg: {latest['temp_avg']}°C, "
                  f"Max: {latest['temp_max']}°C, Min: {latest['temp_min']}°C")
    
    # Show market data sample
    markets = result["markets"].get("markets", [])
    if markets:
        print(f"\n📊 Polymarket Weather Markets:")
        for m in markets[:5]:
            print(f"   - {m.get('question', 'N/A')[:70]}")
            print(f"     Volume: ${float(m.get('volume', 0)):,.0f} | Active: {m.get('active')}")
    
    print(f"\n✅ Data fetch complete! Ready for production-grade backtesting.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
