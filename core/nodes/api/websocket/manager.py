"""
WebSocket connection manager for real-time updates
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and channel subscriptions"""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            self.connections[client_id] = websocket
        logger.info(f"WebSocket client connected: {client_id}")

    async def disconnect(self, client_id: str) -> None:
        """Disconnect and cleanup a WebSocket connection"""
        async with self._lock:
            if client_id in self.connections:
                del self.connections[client_id]

            # Remove from all subscriptions
            for channel in list(self.subscriptions.keys()):
                self.subscriptions[channel].discard(client_id)
                if not self.subscriptions[channel]:
                    del self.subscriptions[channel]

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def subscribe(self, client_id: str, channels: List[str]) -> None:
        """Subscribe a client to one or more channels"""
        async with self._lock:
            for channel in channels:
                self.subscriptions[channel].add(client_id)
                logger.debug(f"Client {client_id} subscribed to {channel}")

        # Send confirmation
        await self.send_to_connection(client_id, {
            "type": "subscribed",
            "channels": channels,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def unsubscribe(self, client_id: str, channels: List[str]) -> None:
        """Unsubscribe a client from one or more channels"""
        async with self._lock:
            for channel in channels:
                self.subscriptions[channel].discard(client_id)
                if not self.subscriptions[channel]:
                    del self.subscriptions[channel]
                logger.debug(f"Client {client_id} unsubscribed from {channel}")

        # Send confirmation
        await self.send_to_connection(client_id, {
            "type": "unsubscribed",
            "channels": channels,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]) -> None:
        """Broadcast a message to all subscribers of a channel"""
        subscribers = self.subscriptions.get(channel, set())
        if not subscribers:
            return

        # Add metadata
        message_with_meta = {
            "type": channel,
            "timestamp": datetime.utcnow().isoformat(),
            "data": message,
        }

        # Send to all subscribers
        disconnected = []
        for client_id in list(subscribers):
            websocket = self.connections.get(client_id)
            if websocket:
                try:
                    await websocket.send_json(message_with_meta)
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {e}")
                    disconnected.append(client_id)
            else:
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)

    async def send_to_connection(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection"""
        websocket = self.connections.get(client_id)
        if not websocket:
            return False

        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send to {client_id}: {e}")
            await self.disconnect(client_id)
            return False

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients"""
        message_with_meta = {
            "type": "broadcast",
            "timestamp": datetime.utcnow().isoformat(),
            "data": message,
        }

        disconnected = []
        for client_id, websocket in list(self.connections.items()):
            try:
                await websocket.send_json(message_with_meta)
            except Exception:
                disconnected.append(client_id)

        for client_id in disconnected:
            await self.disconnect(client_id)

    async def handle_message(self, client_id: str, data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message from client"""
        msg_type = data.get("type")

        if msg_type == "subscribe":
            channels = data.get("channels", [])
            if isinstance(channels, str):
                channels = [channels]
            await self.subscribe(client_id, channels)

        elif msg_type == "unsubscribe":
            channels = data.get("channels", [])
            if isinstance(channels, str):
                channels = [channels]
            await self.unsubscribe(client_id, channels)

        elif msg_type == "ping":
            await self.send_to_connection(client_id, {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
            })

        else:
            logger.debug(f"Unknown message type from {client_id}: {msg_type}")

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)

    def get_channel_subscribers(self, channel: str) -> int:
        """Get number of subscribers for a channel"""
        return len(self.subscriptions.get(channel, set()))

    def get_client_subscriptions(self, client_id: str) -> List[str]:
        """Get channels a client is subscribed to"""
        return [
            channel for channel, subscribers in self.subscriptions.items()
            if client_id in subscribers
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": len(self.connections),
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self.subscriptions.items()
            },
        }
