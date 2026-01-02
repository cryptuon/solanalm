"""
Log collector for capturing and streaming node logs
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    level: str = "INFO"
    source: str = "node"
    message: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "extra": self.extra,
        }


class LogHandler(logging.Handler):
    """Custom logging handler that captures logs for the dashboard"""

    def __init__(self, collector: 'LogCollector'):
        super().__init__()
        self.collector = collector

    def emit(self, record: logging.LogRecord) -> None:
        """Capture a log record"""
        try:
            entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created),
                level=record.levelname,
                source=record.name,
                message=record.getMessage(),
                extra=getattr(record, 'extra', {}),
            )

            # Use asyncio to handle the callback if in async context
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.collector._add_entry(entry))
            except RuntimeError:
                # No running loop, add synchronously
                self.collector.entries.append(entry)

        except Exception as e:
            logger.error(f"Error in log handler: {e}")


class LogCollector:
    """Collects and manages node logs for dashboard display"""

    def __init__(self, max_entries: int = 5000):
        """
        Args:
            max_entries: Maximum number of log entries to retain
        """
        self.entries: deque[LogEntry] = deque(maxlen=max_entries)
        self._subscribers: Set[Callable[[LogEntry], Any]] = set()
        self._lock = asyncio.Lock()
        self._handler: Optional[LogHandler] = None

    def attach_to_logger(self, logger_name: Optional[str] = None, level: int = logging.DEBUG) -> None:
        """Attach collector to a Python logger"""
        self._handler = LogHandler(self)
        self._handler.setLevel(level)

        target_logger = logging.getLogger(logger_name)
        target_logger.addHandler(self._handler)
        logger.info(f"Log collector attached to logger: {logger_name or 'root'}")

    def detach_from_logger(self, logger_name: Optional[str] = None) -> None:
        """Detach collector from a Python logger"""
        if self._handler:
            target_logger = logging.getLogger(logger_name)
            target_logger.removeHandler(self._handler)
            self._handler = None

    async def _add_entry(self, entry: LogEntry) -> None:
        """Add a log entry and notify subscribers"""
        async with self._lock:
            self.entries.append(entry)

        # Notify subscribers
        for callback in list(self._subscribers):
            try:
                result = callback(entry)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error notifying log subscriber: {e}")

    def add_log(
        self,
        message: str,
        level: str = "INFO",
        source: str = "node",
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Manually add a log entry"""
        entry = LogEntry(
            level=level.upper(),
            source=source,
            message=message,
            extra=extra or {},
        )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._add_entry(entry))
        except RuntimeError:
            self.entries.append(entry)

    def subscribe(self, callback: Callable[[LogEntry], Any]) -> None:
        """Subscribe to new log entries"""
        self._subscribers.add(callback)

    def unsubscribe(self, callback: Callable[[LogEntry], Any]) -> None:
        """Unsubscribe from log entries"""
        self._subscribers.discard(callback)

    def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        level: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve logs with filtering and pagination.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            level: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            source: Filter by source/logger name
            search: Search in message text
            since: Only return logs after this timestamp

        Returns:
            List of log entries as dictionaries
        """
        filtered = list(self.entries)

        # Apply filters
        if level:
            level_upper = level.upper()
            filtered = [e for e in filtered if e.level == level_upper]

        if source:
            filtered = [e for e in filtered if source.lower() in e.source.lower()]

        if search:
            search_lower = search.lower()
            filtered = [e for e in filtered if search_lower in e.message.lower()]

        if since:
            filtered = [e for e in filtered if e.timestamp > since]

        # Sort by timestamp descending (newest first)
        filtered.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        paginated = filtered[offset:offset + limit]

        return [e.to_dict() for e in paginated]

    def get_log_levels_summary(self) -> Dict[str, int]:
        """Get count of logs by level"""
        counts: Dict[str, int] = {
            "DEBUG": 0,
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        }

        for entry in self.entries:
            if entry.level in counts:
                counts[entry.level] += 1

        return counts

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent error and critical logs"""
        errors = [
            e for e in self.entries
            if e.level in ("ERROR", "CRITICAL")
        ]
        errors.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in errors[:limit]]

    def clear(self) -> None:
        """Clear all log entries"""
        self.entries.clear()
