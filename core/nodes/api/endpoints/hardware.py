"""
Hardware monitoring endpoints
"""

from typing import Any, Dict, List, TYPE_CHECKING
from fastapi import APIRouter, Query

if TYPE_CHECKING:
    from ..collectors import HardwareCollector

router = APIRouter(prefix="/hardware", tags=["hardware"])


def get_hardware_endpoints(hardware_collector: 'HardwareCollector'):
    """Create hardware endpoints with collector reference"""

    @router.get("")
    async def get_hardware() -> Dict[str, Any]:
        """Get current hardware utilization"""
        return hardware_collector.to_dict()

    @router.get("/history")
    async def get_hardware_history(
        minutes: int = Query(60, ge=1, le=1440),
    ) -> Dict[str, Any]:
        """Get historical hardware metrics"""
        history = hardware_collector.get_history(minutes=minutes)
        return {
            "history": history,
            "count": len(history),
            "minutes": minutes,
        }

    return router
