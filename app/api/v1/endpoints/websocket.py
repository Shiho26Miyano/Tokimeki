"""
WebSocket endpoints for real-time data streaming
"""
import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from datetime import datetime, timedelta
import random

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "price_updates": [],
            "signal_updates": [],
            "trade_updates": [],
            "job_updates": []
        }
        self.connection_types: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, connection_type: str = "price_updates"):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[connection_type].append(websocket)
        self.connection_types[websocket] = connection_type
        logger.info(f"WebSocket connected for {connection_type}. Total connections: {len(self.active_connections[connection_type])}")
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        connection_type = self.connection_types.get(websocket)
        if connection_type and websocket in self.active_connections[connection_type]:
            self.active_connections[connection_type].remove(websocket)
            del self.connection_types[websocket]
            logger.info(f"WebSocket disconnected from {connection_type}. Total connections: {len(self.active_connections[connection_type])}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str, connection_type: str = "price_updates"):
        """Broadcast a message to all connections of a specific type"""
        if connection_type not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[connection_type]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_all(self, message: str):
        """Broadcast a message to all active connections"""
        for connection_type in self.active_connections:
            await self.broadcast(message, connection_type)

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time data"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for client message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(websocket, message)
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from client")
                continue
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/price")
async def price_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint specifically for price updates"""
    await manager.connect(websocket, "price_updates")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Price WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/signals")
async def signals_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint specifically for signal updates"""
    await manager.connect(websocket, "signal_updates")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Signals WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/trades")
async def trades_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint specifically for trade updates"""
    await manager.connect(websocket, "trade_updates")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Trades WebSocket error: {e}")
        manager.disconnect(websocket)

@router.websocket("/ws/jobs")
async def jobs_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint specifically for job updates"""
    await manager.connect(websocket, "job_updates")
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Jobs WebSocket error: {e}")
        manager.disconnect(websocket)

async def handle_client_message(websocket: WebSocket, message: dict):
    """Handle incoming client messages"""
    try:
        message_type = message.get("type")
        
        if message_type == "subscribe":
            # Client wants to subscribe to specific data types
            data_types = message.get("data_types", [])
            for data_type in data_types:
                if data_type in manager.active_connections:
                    await manager.send_personal_message(
                        json.dumps({"type": "subscribed", "data_type": data_type}),
                        websocket
                    )
        
        elif message_type == "ping":
            # Client ping, send pong
            await manager.send_personal_message(
                json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                websocket
            )
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling client message: {e}")

# Background task for generating mock data
async def generate_mock_data():
    """Generate and broadcast mock data for testing"""
    symbols = ["ES=F", "NQ=F", "YM=F", "RTY=F", "CL=F", "GC=F"]
    
    while True:
        try:
            # Generate mock price updates
            for symbol in symbols:
                price_update = {
                    "type": "price_update",
                    "symbol": symbol,
                    "price": round(random.uniform(4000, 5000) if "ES" in symbol else random.uniform(80, 90), 2),
                    "change": round(random.uniform(-50, 50), 2),
                    "volume": random.randint(100000, 2000000),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.broadcast(
                    json.dumps(price_update),
                    "price_updates"
                )
            
            # Generate mock signal updates
            signal_update = {
                "type": "signal_update",
                "symbol": random.choice(symbols),
                "signals": {
                    "q10": round(random.uniform(-0.02, 0.02), 4),
                    "q25": round(random.uniform(-0.01, 0.01), 4),
                    "q50": round(random.uniform(-0.005, 0.005), 4),
                    "q75": round(random.uniform(-0.01, 0.01), 4),
                    "q90": round(random.uniform(-0.02, 0.02), 4)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.broadcast(
                json.dumps(signal_update),
                "signal_updates"
            )
            
            # Generate mock trade updates
            trade_update = {
                "type": "trade_update",
                "trades": [
                    {
                        "id": random.randint(1000, 9999),
                        "symbol": random.choice(symbols),
                        "side": random.choice(["buy", "sell"]),
                        "quantity": random.randint(1, 100),
                        "price": round(random.uniform(4000, 5000), 2),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            }
            
            await manager.broadcast(
                json.dumps(trade_update),
                "trade_updates"
            )
            
            # Generate mock job updates
            job_update = {
                "type": "job_update",
                "jobs": [
                    {
                        "id": random.randint(1, 10),
                        "name": "Model Training",
                        "status": random.choice(["running", "completed", "pending"]),
                        "progress": random.randint(0, 100),
                        "type": "training",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            }
            
            await manager.broadcast(
                json.dumps(job_update),
                "job_updates"
            )
            
            # Wait before next update
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            await asyncio.sleep(5)

# Start mock data generation when the module loads
@router.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(generate_mock_data())
    logger.info("WebSocket mock data generation started")

# Utility functions for external use
async def broadcast_price_update(symbol: str, price: float, change: float, volume: int):
    """Broadcast price update to all price subscribers"""
    price_update = {
        "type": "price_update",
        "symbol": symbol,
        "price": price,
        "change": change,
        "volume": volume,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(
        json.dumps(price_update),
        "price_updates"
    )

async def broadcast_signal_update(symbol: str, signals: dict):
    """Broadcast signal update to all signal subscribers"""
    signal_update = {
        "type": "signal_update",
        "symbol": symbol,
        "signals": signals,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(
        json.dumps(signal_update),
        "signal_updates"
    )

async def broadcast_trade_update(trades: List[dict]):
    """Broadcast trade update to all trade subscribers"""
    trade_update = {
        "type": "trade_update",
        "trades": trades,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(
        json.dumps(trade_update),
        "trade_updates"
    )

async def broadcast_job_update(jobs: List[dict]):
    """Broadcast job update to all job subscribers"""
    job_update = {
        "type": "job_update",
        "jobs": jobs,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(
        json.dumps(job_update),
        "job_updates"
    )

# Export manager for external use
__all__ = [
    "manager",
    "broadcast_price_update",
    "broadcast_signal_update", 
    "broadcast_trade_update",
    "broadcast_job_update"
]
