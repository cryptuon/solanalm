"""
Event emitter for real-time node events
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class NodeEvent:
    """Structured node event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: str = "info"
    severity: str = "info"  # info, warning, error
    title: str = ""
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "data": self.data,
        }


class EventEmitter:
    """Emits and manages node events for dashboard notifications"""

    # Common event types
    REQUEST_STARTED = "request_started"
    REQUEST_COMPLETED = "request_completed"
    REQUEST_FAILED = "request_failed"
    TRAINING_ROUND_JOINED = "training_round_joined"
    TRAINING_ROUND_COMPLETED = "training_round_completed"
    TRAINING_ROUND_FAILED = "training_round_failed"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_PENDING = "payment_pending"
    GATEWAY_CONNECTED = "gateway_connected"
    GATEWAY_DISCONNECTED = "gateway_disconnected"
    MODEL_LOADED = "model_loaded"
    MODEL_UNLOADED = "model_unloaded"
    NODE_PAUSED = "node_paused"
    NODE_RESUMED = "node_resumed"
    ERROR = "error"
    WARNING = "warning"

    def __init__(self, max_events: int = 1000):
        """
        Args:
            max_events: Maximum number of events to retain
        """
        self.events: deque[NodeEvent] = deque(maxlen=max_events)
        self._subscribers: Set[Callable[[NodeEvent], Any]] = set()
        self._lock = asyncio.Lock()

    async def emit(
        self,
        event_type: str,
        title: str,
        description: str = "",
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> NodeEvent:
        """
        Emit a new event.

        Args:
            event_type: Type of event (use class constants)
            title: Short event title
            description: Longer description
            severity: Event severity (info, warning, error)
            data: Additional event data

        Returns:
            The created event
        """
        event = NodeEvent(
            event_type=event_type,
            severity=severity,
            title=title,
            description=description,
            data=data or {},
        )

        async with self._lock:
            self.events.append(event)

        # Notify subscribers
        await self._notify_subscribers(event)

        logger.debug(f"Emitted event: {event_type} - {title}")
        return event

    async def _notify_subscribers(self, event: NodeEvent) -> None:
        """Notify all subscribers of a new event"""
        for callback in list(self._subscribers):
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error notifying event subscriber: {e}")

    def subscribe(self, callback: Callable[[NodeEvent], Any]) -> None:
        """Subscribe to events"""
        self._subscribers.add(callback)

    def unsubscribe(self, callback: Callable[[NodeEvent], Any]) -> None:
        """Unsubscribe from events"""
        self._subscribers.discard(callback)

    def get_events(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get events with filtering and pagination.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            event_type: Filter by event type
            severity: Filter by severity
            since: Only return events after this timestamp

        Returns:
            List of events as dictionaries
        """
        filtered = list(self.events)

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        if severity:
            filtered = [e for e in filtered if e.severity == severity]

        if since:
            filtered = [e for e in filtered if e.timestamp > since]

        # Sort by timestamp descending
        filtered.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        paginated = filtered[offset:offset + limit]

        return [e.to_dict() for e in paginated]

    def get_unread_count(self, since: datetime) -> int:
        """Get count of events since a timestamp"""
        return len([e for e in self.events if e.timestamp > since])

    # Convenience methods for common events

    async def emit_request_completed(
        self,
        request_id: str,
        tokens: int,
        processing_time: float,
        cost_sol: float,
    ) -> NodeEvent:
        """Emit a request completed event"""
        return await self.emit(
            event_type=self.REQUEST_COMPLETED,
            title="Request Completed",
            description=f"Generated {tokens} tokens in {processing_time:.2f}s",
            severity="info",
            data={
                "request_id": request_id,
                "tokens": tokens,
                "processing_time": processing_time,
                "cost_sol": cost_sol,
            },
        )

    async def emit_request_failed(
        self,
        request_id: str,
        error: str,
    ) -> NodeEvent:
        """Emit a request failed event"""
        return await self.emit(
            event_type=self.REQUEST_FAILED,
            title="Request Failed",
            description=error,
            severity="error",
            data={"request_id": request_id, "error": error},
        )

    async def emit_payment_received(
        self,
        amount_sol: float,
        transaction_signature: Optional[str] = None,
    ) -> NodeEvent:
        """Emit a payment received event"""
        return await self.emit(
            event_type=self.PAYMENT_RECEIVED,
            title="Payment Received",
            description=f"Received {amount_sol:.6f} SOL",
            severity="info",
            data={
                "amount_sol": amount_sol,
                "transaction_signature": transaction_signature,
            },
        )

    async def emit_training_round_joined(
        self,
        round_id: str,
        model: str,
    ) -> NodeEvent:
        """Emit a training round joined event"""
        return await self.emit(
            event_type=self.TRAINING_ROUND_JOINED,
            title="Joined Training Round",
            description=f"Joined round {round_id[:8]} for model {model}",
            severity="info",
            data={"round_id": round_id, "model": model},
        )

    async def emit_error(
        self,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> NodeEvent:
        """Emit an error event"""
        return await self.emit(
            event_type=self.ERROR,
            title="Error",
            description=error,
            severity="error",
            data=details or {},
        )

    async def emit_gateway_status(self, connected: bool) -> NodeEvent:
        """Emit gateway connection status change"""
        if connected:
            return await self.emit(
                event_type=self.GATEWAY_CONNECTED,
                title="Gateway Connected",
                description="Successfully connected to gateway",
                severity="info",
            )
        else:
            return await self.emit(
                event_type=self.GATEWAY_DISCONNECTED,
                title="Gateway Disconnected",
                description="Lost connection to gateway",
                severity="warning",
            )
