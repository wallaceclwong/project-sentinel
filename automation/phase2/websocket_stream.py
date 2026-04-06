"""
SENTINEL-RACING AI - PHASE 2: WEBSOCKET STREAMING
Real-time data streaming for live odds and race updates
"""

import asyncio
import websockets
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketManager:
    """WebSocket manager for real-time data streaming"""
    
    def __init__(self):
        self.clients = set()
        self.data_streams = {}
        self.running = False
        
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"✅ Client registered. Total clients: {len(self.clients)}")
        
        # Send initial data
        await self.send_to_client(websocket, {
            'type': 'welcome',
            'message': 'Connected to SENTINEL-RACING AI WebSocket',
            'timestamp': datetime.now().isoformat()
        })
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"❌ Client disconnected. Total clients: {len(self.clients)}")
    
    async def send_to_client(self, websocket, data):
        """Send data to a specific client"""
        try:
            message = json.dumps(data)
            await websocket.send(message)
        except Exception as e:
            logger.error(f"❌ Failed to send to client: {e}")
    
    async def broadcast(self, data):
        """Broadcast data to all connected clients"""
        if not self.clients:
            return
        
        message = json.dumps(data)
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.error(f"❌ Failed to broadcast to client: {e}")
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected
    
    async def start_odds_stream(self):
        """Start streaming odds updates"""
        logger.info("📡 Starting odds stream...")
        
        while self.running:
            try:
                # Simulate odds updates
                odds_update = {
                    'type': 'odds_update',
                    'race_id': 'HK_HV_2026-03-11_R3',
                    'timestamp': datetime.now().isoformat(),
                    'data': self.generate_odds_update()
                }
                
                await self.broadcast(odds_update)
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Odds stream error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def generate_odds_update(self):
        """Generate simulated odds update"""
        import random
        
        horses = [
            'KING OF SELECTION', 'STELLAR SWIFT', 'HARMONY GALAXY',
            'FORTUNE STAR', 'AMAZING AWARD', 'THE AZURE',
            'TO INFINITY', 'STAR ELEGANCE', 'NINTH HORSE',
            'TENTH HORSE', 'ELEVENTH HORSE', 'TWELFTH HORSE'
        ]
        
        odds = {}
        
        for horse in horses:
            # Generate realistic odds with small changes
            base_odds = random.uniform(2.5, 8.0)
            change = random.uniform(-0.2, 0.2)
            current_odds = max(1.1, base_odds + change)
            
            odds[horse] = {
                'place_odds': round(current_odds, 2),
                'change': round(change, 2),
                'trend': 'up' if change > 0 else 'down'
            }
        
        return odds
    
    async def start_race_updates(self):
        """Start streaming race updates"""
        logger.info("📡 Starting race updates stream...")
        
        while self.running:
            try:
                # Simulate race updates
                race_update = {
                    'type': 'race_update',
                    'race_id': 'HK_HV_2026-03-11_R3',
                    'timestamp': datetime.now().isoformat(),
                    'data': self.generate_race_update()
                }
                
                await self.broadcast(race_update)
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"❌ Race updates error: {e}")
                await asyncio.sleep(120)  # Wait longer on error
    
    def generate_race_update(self):
        """Generate simulated race update"""
        import random
        
        updates = [
            'Horses parading to the starting gate',
            'Jockeys making final adjustments',
            'Weather: Good going, firm track',
            'Crowd building at Happy Valley',
            'Barrier draw completed',
            'Final jockey changes confirmed'
        ]
        
        return {
            'status': random.choice(['preparing', 'ready', 'delayed']),
            'message': random.choice(updates),
            'time_to_post': random.randint(5, 30)
        }
    
    async def start_ai_recommendations(self):
        """Start streaming AI recommendations"""
        logger.info("🤖 Starting AI recommendations stream...")
        
        while self.running:
            try:
                # Generate AI recommendation updates
                ai_update = {
                    'type': 'ai_recommendation',
                    'race_id': 'HK_HV_2026-03-11_R3',
                    'timestamp': datetime.now().isoformat(),
                    'data': self.generate_ai_recommendation()
                }
                
                await self.broadcast(ai_update)
                await asyncio.sleep(45)  # Update every 45 seconds
                
            except Exception as e:
                logger.error(f"❌ AI recommendations error: {e}")
                await asyncio.sleep(90)  # Wait longer on error
    
    def generate_ai_recommendation(self):
        """Generate AI recommendation update"""
        import random
        
        horses = [
            'KING OF SELECTION', 'STELLAR SWIFT', 'HARMONY GALAXY',
            'FORTUNE STAR', 'AMAZING AWARD', 'THE AZURE',
            'TO INFINITY', 'STAR ELEGANCE', 'NINTH HORSE',
            'TENTH HORSE', 'ELEVENTH HORSE', 'TWELFTH HORSE'
        ]
        
        # Select top 3 horses
        top_horses = random.sample(horses, 3)
        
        recommendations = []
        
        for i, horse in enumerate(top_horses, 1):
            confidence = random.uniform(70, 95)
            
            recommendations.append({
                'rank': i,
                'horse': horse,
                'confidence': round(confidence, 1),
                'recommendation': 'STRONG' if confidence > 85 else 'MODERATE',
                'reason': self.generate_recommendation_reason()
            })
        
        return {
            'race_type': 'PLACE',
            'recommendations': recommendations,
            'overall_confidence': round(random.uniform(75, 90), 1)
        }
    
    def generate_recommendation_reason(self):
        """Generate recommendation reason"""
        reasons = [
            'Excellent barrier position',
            'Strong jockey assignment',
            'Good recent form',
            'Favorable track conditions',
            'Value odds available',
            'Historical performance strong'
        ]
        
        import random
        return random.choice(reasons)
    
    async def start_server(self, host='localhost', port=8765):
        """Start WebSocket server"""
        logger.info(f"🚀 Starting WebSocket server on {host}:{port}")
        
        self.running = True
        
        # Start data streams
        asyncio.create_task(self.start_odds_stream())
        asyncio.create_task(self.start_race_updates())
        asyncio.create_task(self.start_ai_recommendations())
        
        # Start WebSocket server
        async with websockets.serve(
            self.handle_client,
            host,
            port
        ):
            logger.info(f"✅ WebSocket server started on ws://{host}:{port}")
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection"""
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.handle_client_message(websocket, data)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def handle_client_message(self, websocket, data):
        """Handle messages from clients"""
        message_type = data.get('type')
        
        if message_type == 'subscribe':
            # Handle subscription requests
            stream_type = data.get('stream')
            await self.send_to_client(websocket, {
                'type': 'subscription_confirmed',
                'stream': stream_type,
                'timestamp': datetime.now().isoformat()
            })
        
        elif message_type == 'get_current_data':
            # Send current data snapshot
            await self.send_to_client(websocket, {
                'type': 'current_data',
                'data': {
                    'odds': self.generate_odds_update(),
                    'race': self.generate_race_update(),
                    'ai': self.generate_ai_recommendation()
                },
                'timestamp': datetime.now().isoformat()
            })
    
    def stop_server(self):
        """Stop the WebSocket server"""
        logger.info("🛑 Stopping WebSocket server...")
        self.running = False

async def main():
    """Main execution function"""
    print("🚀 SENTINEL-RACING AI - PHASE 2: WEBSOCKET STREAMING")
    print("=" * 60)
    
    manager = WebSocketManager()
    
    try:
        print("📡 Starting WebSocket server...")
        print("🌐 Server will be available at: ws://localhost:8765")
        print("📊 Streaming: odds, race updates, AI recommendations")
        print("⏹️  Press Ctrl+C to stop")
        
        await manager.start_server()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        manager.stop_server()

if __name__ == "__main__":
    asyncio.run(main())
