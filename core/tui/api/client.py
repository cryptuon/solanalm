"""
Async API client for communicating with the Node API
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import asyncio
import json
import logging

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class NodeHealth:
    """Node health status"""
    status: str = "unknown"
    is_ready: bool = False
    is_paused: bool = False
    model_loaded: bool = False
    gateway_connected: bool = False
    device: str = "cpu"
    model: str = "unknown"
    stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeStats:
    """Node statistics"""
    requests_served: int = 0
    requests_succeeded: int = 0
    requests_failed: int = 0
    total_tokens_generated: int = 0
    total_processing_time: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 1.0
    total_earnings_sol: float = 0.0
    pending_earnings_sol: float = 0.0
    uptime_seconds: float = 0.0


@dataclass
class HardwareMetrics:
    """Hardware metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    gpu_available: bool = False
    gpu_percent: Optional[float] = None
    gpu_memory_used_gb: Optional[float] = None
    gpu_memory_total_gb: Optional[float] = None
    storage_percent: float = 0.0


@dataclass
class NodeInfo:
    """Node information"""
    node_id: str = "unknown"
    node_type: str = "unknown"
    version: str = "0.1.0"
    wallet_address: str = ""
    endpoint_url: str = ""
    gateway_url: Optional[str] = None
    uptime_seconds: float = 0.0
    supported_models: List[str] = field(default_factory=list)


class NodeAPIClient:
    """Async client for communicating with Node API"""

    def __init__(self, node_url: str):
        self.node_url = node_url.rstrip('/')
        self.api_base = f"{self.node_url}/api/v1/node"
        self.ws_url = f"{self.node_url.replace('http', 'ws')}/ws/v1/node"
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._ws_task: Optional[asyncio.Task] = None
        self._ws_handlers: Dict[str, List[Callable]] = {}
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to node API"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        self._connected = True
        logger.info(f"Connected to node API at {self.node_url}")

    async def disconnect(self) -> None:
        """Close connection to node API"""
        self._connected = False
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        if self.ws:
            await self.ws.close()

        if self.session:
            await self.session.close()
            self.session = None

        logger.info("Disconnected from node API")

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure session is available"""
        if self.session is None:
            await self.connect()
        return self.session

    # REST API Methods

    async def get_info(self) -> NodeInfo:
        """Get node information"""
        session = await self._ensure_session()
        try:
            async with session.get(f"{self.api_base}/info") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return NodeInfo(
                        node_id=data.get("node_id", "unknown"),
                        node_type=data.get("node_type", "unknown"),
                        version=data.get("version", "0.1.0"),
                        wallet_address=data.get("wallet_address", ""),
                        endpoint_url=data.get("endpoint_url", ""),
                        gateway_url=data.get("gateway_url"),
                        uptime_seconds=data.get("uptime_seconds", 0.0),
                        supported_models=data.get("supported_models", []),
                    )
        except Exception as e:
            logger.error(f"Failed to get node info: {e}")
        return NodeInfo()

    async def get_health(self) -> NodeHealth:
        """Get node health status"""
        session = await self._ensure_session()
        try:
            async with session.get(f"{self.api_base}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return NodeHealth(
                        status=data.get("status", "unknown"),
                        is_ready=data.get("is_ready", False),
                        is_paused=data.get("is_paused", False),
                        model_loaded=data.get("model_loaded", False),
                        gateway_connected=data.get("gateway_connected", False),
                        device=data.get("device", "cpu"),
                        model=data.get("model", "unknown"),
                        stats=data.get("stats", {}),
                    )
        except Exception as e:
            logger.error(f"Failed to get health: {e}")
        return NodeHealth()

    async def get_stats(self) -> NodeStats:
        """Get node statistics"""
        session = await self._ensure_session()
        try:
            async with session.get(f"{self.api_base}/stats") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return NodeStats(
                        requests_served=data.get("requests_served", 0),
                        requests_succeeded=data.get("requests_succeeded", 0),
                        requests_failed=data.get("requests_failed", 0),
                        total_tokens_generated=data.get("total_tokens_generated", 0),
                        total_processing_time=data.get("total_processing_time", 0.0),
                        average_response_time=data.get("average_response_time", 0.0),
                        success_rate=data.get("success_rate", 1.0),
                        total_earnings_sol=data.get("total_earnings_sol", 0.0),
                        pending_earnings_sol=data.get("pending_earnings_sol", 0.0),
                        uptime_seconds=data.get("uptime_seconds", 0.0),
                    )
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
        return NodeStats()

    async def get_hardware(self) -> HardwareMetrics:
        """Get hardware metrics"""
        session = await self._ensure_session()
        try:
            async with session.get(f"{self.api_base}/hardware") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    cpu = data.get("cpu", {})
                    memory = data.get("memory", {})
                    gpu = data.get("gpu", {})
                    storage = data.get("storage", {})

                    return HardwareMetrics(
                        cpu_percent=cpu.get("percent", 0.0),
                        memory_percent=memory.get("percent", 0.0),
                        memory_used_gb=memory.get("used_gb", 0.0),
                        memory_total_gb=memory.get("total_gb", 0.0),
                        gpu_available=gpu.get("available", False),
                        gpu_percent=gpu.get("percent"),
                        gpu_memory_used_gb=gpu.get("memory_used_gb"),
                        gpu_memory_total_gb=gpu.get("memory_total_gb"),
                        storage_percent=storage.get("percent", 0.0),
                    )
        except Exception as e:
            logger.error(f"Failed to get hardware metrics: {e}")
        return HardwareMetrics()

    async def get_logs(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get logs"""
        session = await self._ensure_session()
        params = {"limit": limit}
        if level:
            params["level"] = level
        if search:
            params["search"] = search

        try:
            async with session.get(f"{self.api_base}/logs", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("logs", [])
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
        return []

    async def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get events"""
        session = await self._ensure_session()
        try:
            async with session.get(f"{self.api_base}/events", params={"limit": limit}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("events", [])
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
        return []

    async def get_earnings_summary(self) -> Dict[str, Any]:
        """Get earnings summary"""
        session = await self._ensure_session()
        try:
            async with session.get(f"{self.api_base}/stats/earnings/summary") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.error(f"Failed to get earnings: {e}")
        return {}

    async def get_training_current(self) -> Dict[str, Any]:
        """Get current training round (for training nodes)"""
        session = await self._ensure_session()
        try:
            async with session.get(f"{self.api_base}/training/current") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.debug(f"Training endpoint not available: {e}")
        return {"active": False}

    # Control Methods

    async def pause_node(self) -> bool:
        """Pause the node"""
        session = await self._ensure_session()
        try:
            async with session.post(f"{self.api_base}/control/pause") as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to pause node: {e}")
        return False

    async def resume_node(self) -> bool:
        """Resume the node"""
        session = await self._ensure_session()
        try:
            async with session.post(f"{self.api_base}/control/resume") as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to resume node: {e}")
        return False

    async def restart_node(self) -> bool:
        """Request node restart"""
        session = await self._ensure_session()
        try:
            async with session.post(f"{self.api_base}/control/restart") as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to restart node: {e}")
        return False

    # WebSocket Methods

    async def subscribe(self, channels: List[str], handler: Callable) -> None:
        """Subscribe to WebSocket channels"""
        for channel in channels:
            if channel not in self._ws_handlers:
                self._ws_handlers[channel] = []
            self._ws_handlers[channel].append(handler)

        # Start WebSocket connection if not running
        if self._ws_task is None or self._ws_task.done():
            self._ws_task = asyncio.create_task(self._ws_loop())

    async def _ws_loop(self) -> None:
        """WebSocket connection loop"""
        session = await self._ensure_session()

        while self._connected:
            try:
                async with session.ws_connect(self.ws_url) as ws:
                    self.ws = ws
                    logger.info("WebSocket connected")

                    # Subscribe to channels
                    channels = list(self._ws_handlers.keys())
                    if channels:
                        await ws.send_json({
                            "type": "subscribe",
                            "channels": channels,
                        })

                    # Handle messages
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                channel = data.get("type")
                                if channel in self._ws_handlers:
                                    for handler in self._ws_handlers[channel]:
                                        try:
                                            result = handler(data)
                                            if asyncio.iscoroutine(result):
                                                await result
                                        except Exception as e:
                                            logger.error(f"Handler error: {e}")
                            except json.JSONDecodeError:
                                pass
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break

            except Exception as e:
                logger.warning(f"WebSocket connection failed: {e}")

            if self._connected:
                await asyncio.sleep(5)  # Reconnect delay
