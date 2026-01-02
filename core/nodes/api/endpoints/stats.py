"""
Statistics endpoints for node metrics
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from fastapi import APIRouter, Query

if TYPE_CHECKING:
    from ..collectors import StatsCollector

router = APIRouter(prefix="/stats", tags=["stats"])


def get_stats_endpoints(stats_collector: 'StatsCollector'):
    """Create stats endpoints with collector reference"""

    @router.get("")
    async def get_stats() -> Dict[str, Any]:
        """Get aggregated node statistics"""
        return stats_collector.get_current_stats()

    @router.get("/requests")
    async def get_request_history(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        success_only: bool = Query(False),
    ) -> Dict[str, Any]:
        """Get request history with pagination"""
        requests = stats_collector.get_request_history(
            limit=limit,
            offset=offset,
            success_only=success_only,
        )
        return {
            "requests": requests,
            "count": len(requests),
            "offset": offset,
            "limit": limit,
        }

    @router.get("/earnings")
    async def get_earnings_history(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        payment_type: Optional[str] = Query(None),
    ) -> Dict[str, Any]:
        """Get earnings/payment history"""
        earnings = stats_collector.get_earnings_history(
            limit=limit,
            offset=offset,
            payment_type=payment_type,
        )
        return {
            "earnings": earnings,
            "count": len(earnings),
            "offset": offset,
            "limit": limit,
        }

    @router.get("/earnings/summary")
    async def get_earnings_summary() -> Dict[str, Any]:
        """Get earnings summary with breakdown"""
        return stats_collector.get_earnings_summary()

    return router
