#!/usr/bin/env python3
"""
PROJECT SENTINEL - Data Watcher
Phase 2: Weather Data Ingestion Engine
Processes WeatherNext 2 ensemble forecasts via .zarr streaming
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import dask
import dask.array as da
import xarray as xr
import zarr
import numpy as np
import pandas as pd
from dask.distributed import Client, as_completed

# Import GCP bridge for Phase 3 integration
try:
    from .gcp_bridge import GCPBridge, WeatherDeltaProcessor
except ImportError:
    # Fallback for direct execution
    from gcp_bridge import GCPBridge, WeatherDeltaProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/project-sentinel/logs/data_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeatherDataWatcher:
    """Watches and processes WeatherNext 2 ensemble forecast data"""
    
    def __init__(self, data_lake_path: str = "/home/ubuntu/project-sentinel/data", 
                 gcp_cloud_run_url: str = "https://sentinel-reasoning-xxxxx-uc.a.run.app"):
        self.data_lake_path = Path(data_lake_path)
        self.data_lake_path.mkdir(parents=True, exist_ok=True)
        self.client = None
        self.ensemble_members = 64
        self.gcp_cloud_run_url = gcp_cloud_run_url
        self.gcp_bridge = None
        self.delta_processor = None
        
    async def initialize_dask(self):
        """Initialize Dask client for parallel processing"""
        try:
            # Configure Dask for 2GB RAM instance
            self.client = Client(
                processes=True,
                n_workers=2,
                threads_per_worker=1,
                memory_limit='800MB',
                dashboard_address=':8787'
            )
            logger.info(f"Dask client started: {self.client}")
        except Exception as e:
            logger.error(f"Failed to start Dask client: {e}")
            raise
    
    async def initialize_gcp_bridge(self):
        """Initialize GCP bridge for Phase 3 reasoning"""
        try:
            self.gcp_bridge = GCPBridge(self.gcp_cloud_run_url)
            self.delta_processor = WeatherDeltaProcessor(self.gcp_bridge)
            logger.info(f"GCP bridge initialized: {self.gcp_cloud_run_url}")
        except Exception as e:
            logger.error(f"Failed to initialize GCP bridge: {e}")
            # Continue without GCP bridge for Phase 2 compatibility
            logger.warning("Continuing without GCP bridge (Phase 2 mode)")
    
    async def fetch_weather_data(self, timestamp: datetime) -> Optional[xr.Dataset]:
        """Fetch WeatherNext 2 ensemble forecast data for given timestamp"""
        try:
            # Mock URL - replace with actual WeatherNext 2 endpoint
            zarr_url = f"https://weathernext-api.com/ensemble/v2/{timestamp.strftime('%Y%m%d_%H')}.zarr"
            
            logger.info(f"Fetching ensemble data from {zarr_url}")
            
            # Open zarr store with Dask chunking for memory efficiency
            ds = xr.open_zarr(
                zarr_url,
                chunks={'time': 1, 'ensemble': 8, 'lat': 50, 'lon': 50},
                engine='zarr'
            )
            
            # Validate ensemble structure
            if 'ensemble' not in ds.dims or ds.sizes['ensemble'] != self.ensemble_members:
                logger.warning(f"Unexpected ensemble structure: {ds.dims}")
            
            return ds
            
        except Exception as e:
            logger.error(f"Failed to fetch weather data for {timestamp}: {e}")
            return None
    
    def calculate_weather_delta(self, current_ds: xr.Dataset, previous_ds: xr.Dataset) -> xr.Dataset:
        """Calculate delta between current and previous ensemble forecasts"""
        try:
            # Calculate ensemble mean differences
            current_mean = current_ds.mean(dim='ensemble')
            previous_mean = previous_ds.mean(dim='ensemble')
            
            delta = current_mean - previous_mean
            
            # Add delta statistics
            delta_stats = {
                'max_delta': delta.max().values,
                'min_delta': delta.min().values,
                'mean_delta': delta.mean().values,
                'std_delta': delta.std().values
            }
            
            logger.info(f"Weather delta calculated: {delta_stats}")
            return delta
            
        except Exception as e:
            logger.error(f"Failed to calculate weather delta: {e}")
            raise
    
    async def store_data_lake(self, data: xr.Dataset, data_type: str, timestamp: datetime):
        """Store data in rolling 24-hour data lake"""
        try:
            # Create timestamped file path
            file_path = self.data_lake_path / f"{data_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.zarr"
            
            # Store as zarr for efficient chunked access
            data.to_zarr(file_path, mode='w')
            
            logger.info(f"Stored {data_type} data to {file_path}")
            
            # Clean up old data (older than 24 hours)
            await self.cleanup_old_data()
            
        except Exception as e:
            logger.error(f"Failed to store {data_type} data: {e}")
            raise
    
    async def cleanup_old_data(self):
        """Remove data older than 24 hours from data lake"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for file_path in self.data_lake_path.glob("*.zarr"):
                file_time = datetime.strptime(file_path.stem.split('_')[1], '%Y%m%d_%H%M%S')
                if file_time < cutoff_time:
                    import shutil
                    shutil.rmtree(file_path)
                    logger.info(f"Cleaned up old data: {file_path}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    async def process_weather_cycle(self):
        """Main weather data processing cycle"""
        try:
            current_time = datetime.now()
            previous_time = current_time - timedelta(hours=1)
            
            logger.info(f"Starting weather processing cycle for {current_time}")
            
            # Fetch current and previous ensemble data
            current_ds = await self.fetch_weather_data(current_time)
            previous_ds = await self.fetch_weather_data(previous_time)
            
            if current_ds is None or previous_ds is None:
                logger.warning("Missing data, skipping cycle")
                return
            
            # Calculate weather deltas
            delta_ds = self.calculate_weather_delta(current_ds, previous_ds)
            
            # Store in data lake
            await asyncio.gather(
                self.store_data_lake(current_ds, "ensemble", current_time),
                self.store_data_lake(delta_ds, "delta", current_time)
            )
            
            # Phase 3: Send to GCP bridge for reasoning
            if self.delta_processor:
                try:
                    # Extract delta statistics
                    delta_stats = {
                        'max_delta': float(delta_ds.max().values),
                        'min_delta': float(delta_ds.min().values),
                        'mean_delta': float(delta_ds.mean().values),
                        'std_delta': float(delta_ds.std().values)
                    }
                    
                    # Mock market sentiment (replace with real Polymarket data)
                    market_sentiment = {
                        'polymarket_volume': 150000.0,
                        'price_movement': 0.05,
                        'social_sentiment': 0.65
                    }
                    
                    # Send to Gemini Pro for trade validation
                    trade_signal = await self.delta_processor.process_weather_delta(
                        delta_stats, market_sentiment
                    )
                    
                    if trade_signal:
                        logger.info(f"🎯 Trade signal: {trade_signal.action} "
                                  f"(confidence: {trade_signal.confidence:.2f})")
                    
                except Exception as e:
                    logger.error(f"GCP bridge processing failed: {e}")
            
            logger.info("Weather processing cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Weather processing cycle failed: {e}")
    
    async def start_monitoring(self):
        """Start continuous weather monitoring"""
        await self.initialize_dask()
        await self.initialize_gcp_bridge()  # Phase 3 integration
        
        # Schedule weather processing every hour
        schedule.every().hour.at(":00").do(
            lambda: asyncio.create_task(self.process_weather_cycle())
        )
        
        logger.info("Weather Data Watcher started - monitoring every hour")
        
        # Run initial cycle
        await self.process_weather_cycle()
        
        # Keep scheduler running
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    async def shutdown(self):
        """Graceful shutdown"""
        if self.client:
            self.client.close()
        logger.info("Weather Data Watcher shutdown complete")

if __name__ == "__main__":
    watcher = WeatherDataWatcher()
    
    try:
        asyncio.run(watcher.start_monitoring())
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        asyncio.run(watcher.shutdown())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        asyncio.run(watcher.shutdown())
