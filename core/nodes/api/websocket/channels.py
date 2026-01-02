"""
Channel broadcasters for real-time updates
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import asyncio
import logging

if TYPE_CHECKING:
    from .manager import WebSocketManager
    from ..collectors import StatsCollector, HardwareCollector, LogCollector, EventEmitter

logger = logging.getLogger(__name__)


class ChannelBroadcaster:
    """Handles periodic broadcasts on different channels"""

    # Channel names
    STATS = "stats"
    HARDWARE = "hardware"
    LOGS = "logs"
    EVENTS = "events"
    TRAINING = "training"
    EARNINGS = "earnings"

    def __init__(
        self,
        ws_manager: 'WebSocketManager',
        stats_collector: Optional['StatsCollector'] = None,
        hardware_collector: Optional['HardwareCollector'] = None,
        log_collector: Optional['LogCollector'] = None,
        event_emitter: Optional['EventEmitter'] = None,
    ):
        self.ws_manager = ws_manager
        self.stats_collector = stats_collector
        self.hardware_collector = hardware_collector
        self.log_collector = log_collector
        self.event_emitter = event_emitter

        self._tasks: List[asyncio.Task] = []
        self._running = False

        # Subscribe to real-time events from collectors
        if log_collector:
            log_collector.subscribe(self._on_log_entry)
        if event_emitter:
            event_emitter.subscribe(self._on_event)

    async def start(self) -> None:
        """Start all broadcast tasks"""
        if self._running:
            return

        self._running = True
        self._tasks = [
            asyncio.create_task(self._broadcast_stats_loop()),
            asyncio.create_task(self._broadcast_hardware_loop()),
        ]
        logger.info("Channel broadcaster started")

    async def stop(self) -> None:
        """Stop all broadcast tasks"""
        self._running = False
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        logger.info("Channel broadcaster stopped")

    async def _broadcast_stats_loop(self) -> None:
        """Broadcast stats every 5 seconds"""
        while self._running:
            try:
                if self.stats_collector:
                    stats = self.stats_collector.get_current_stats()
                    await self.ws_manager.broadcast_to_channel(self.STATS, stats)
            except Exception as e:
                logger.error(f"Error broadcasting stats: {e}")

            await asyncio.sleep(5)

    async def _broadcast_hardware_loop(self) -> None:
        """Broadcast hardware metrics every 2 seconds"""
        while self._running:
            try:
                if self.hardware_collector:
                    metrics = self.hardware_collector.to_dict()
                    await self.ws_manager.broadcast_to_channel(self.HARDWARE, metrics)
            except Exception as e:
                logger.error(f"Error broadcasting hardware: {e}")

            await asyncio.sleep(2)

    def _on_log_entry(self, entry: Any) -> None:
        """Handle new log entry - broadcast immediately"""
        asyncio.create_task(self._broadcast_log(entry))

    async def _broadcast_log(self, entry: Any) -> None:
        """Broadcast a log entry"""
        try:
            await self.ws_manager.broadcast_to_channel(
                self.LOGS,
                entry.to_dict() if hasattr(entry, 'to_dict') else dict(entry)
            )
        except Exception as e:
            logger.error(f"Error broadcasting log: {e}")

    def _on_event(self, event: Any) -> None:
        """Handle new event - broadcast immediately"""
        asyncio.create_task(self._broadcast_event(event))

    async def _broadcast_event(self, event: Any) -> None:
        """Broadcast an event"""
        try:
            await self.ws_manager.broadcast_to_channel(
                self.EVENTS,
                event.to_dict() if hasattr(event, 'to_dict') else dict(event)
            )
        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")

    async def broadcast_training_update(self, data: Dict[str, Any]) -> None:
        """Broadcast training round update"""
        await self.ws_manager.broadcast_to_channel(self.TRAINING, data)

    async def broadcast_earnings_update(self, data: Dict[str, Any]) -> None:
        """Broadcast earnings update"""
        await self.ws_manager.broadcast_to_channel(self.EARNINGS, data)
