"""
Log and event endpoints
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from fastapi import APIRouter, Query

if TYPE_CHECKING:
    from ..collectors import LogCollector, EventEmitter

router = APIRouter(tags=["logs"])


def get_log_endpoints(
    log_collector: 'LogCollector',
    event_emitter: 'EventEmitter',
):
    """Create log and event endpoints"""

    @router.get("/logs")
    async def get_logs(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        level: Optional[str] = Query(None, description="Filter by level: DEBUG, INFO, WARNING, ERROR, CRITICAL"),
        source: Optional[str] = Query(None, description="Filter by source/logger name"),
        search: Optional[str] = Query(None, description="Search in message text"),
    ) -> Dict[str, Any]:
        """Get logs with filtering and pagination"""
        logs = log_collector.get_logs(
            limit=limit,
            offset=offset,
            level=level,
            source=source,
            search=search,
        )
        return {
            "logs": logs,
            "count": len(logs),
            "offset": offset,
            "limit": limit,
        }

    @router.get("/logs/summary")
    async def get_logs_summary() -> Dict[str, Any]:
        """Get log level summary"""
        return {
            "levels": log_collector.get_log_levels_summary(),
            "recent_errors": log_collector.get_recent_errors(limit=5),
        }

    @router.get("/events")
    async def get_events(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        event_type: Optional[str] = Query(None),
        severity: Optional[str] = Query(None),
    ) -> Dict[str, Any]:
        """Get node events with filtering"""
        events = event_emitter.get_events(
            limit=limit,
            offset=offset,
            event_type=event_type,
            severity=severity,
        )
        return {
            "events": events,
            "count": len(events),
            "offset": offset,
            "limit": limit,
        }

    return router
