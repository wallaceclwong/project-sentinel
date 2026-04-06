#!/usr/bin/env python3
"""
PROJECT SENTINEL - Service Manager
Manages the Data Watcher service with proper daemonization
"""

import os
import sys
import signal
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_watcher import WeatherDataWatcher

class SentinelService:
    """Service manager for PROJECT SENTINEL"""
    
    def __init__(self):
        self.watcher = None
        self.running = False
        self.setup_logging()
        
    def setup_logging(self):
        """Setup service logging"""
        log_dir = Path("/home/ubuntu/project-sentinel/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/home/ubuntu/project-sentinel/logs/sentinel_service.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
    
    async def start(self):
        """Start the sentinel service"""
        self.logger.info("Starting PROJECT SENTINEL service...")
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.watcher = WeatherDataWatcher()
        self.running = True
        
        try:
            await self.watcher.start_monitoring()
        except Exception as e:
            self.logger.error(f"Service error: {e}")
        finally:
            if self.watcher:
                await self.watcher.shutdown()
            self.logger.info("PROJECT SENTINEL service stopped")
    
    def stop(self):
        """Stop the sentinel service"""
        self.logger.info("Stopping PROJECT SENTINEL service...")
        self.running = False

if __name__ == "__main__":
    import asyncio
    
    service = SentinelService()
    
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        service.stop()
    except Exception as e:
        logging.error(f"Fatal service error: {e}")
        service.stop()
