"""
Node control endpoints
"""

from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..collectors import EventEmitter

router = APIRouter(prefix="/control", tags=["control"])


class ControlAction(BaseModel):
    """Control action request"""
    params: Dict[str, Any] = {}


class PricingUpdate(BaseModel):
    """Pricing update request"""
    per_request: Optional[float] = None
    per_token: Optional[float] = None
    per_training_round: Optional[float] = None
    minimum_payment: Optional[float] = None


def get_control_endpoints(node: Any, event_emitter: 'EventEmitter'):
    """Create control endpoints with node reference"""

    @router.post("/pause")
    async def pause_node() -> Dict[str, Any]:
        """Pause accepting new requests"""
        if hasattr(node, 'is_paused'):
            node.is_paused = True
            await event_emitter.emit(
                event_type=event_emitter.NODE_PAUSED,
                title="Node Paused",
                description="Node is no longer accepting new requests",
            )
            return {
                "success": True,
                "action": "pause",
                "message": "Node paused successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }
        raise HTTPException(status_code=400, detail="Node does not support pausing")

    @router.post("/resume")
    async def resume_node() -> Dict[str, Any]:
        """Resume accepting requests"""
        if hasattr(node, 'is_paused'):
            node.is_paused = False
            await event_emitter.emit(
                event_type=event_emitter.NODE_RESUMED,
                title="Node Resumed",
                description="Node is now accepting requests",
            )
            return {
                "success": True,
                "action": "resume",
                "message": "Node resumed successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }
        raise HTTPException(status_code=400, detail="Node does not support resuming")

    @router.post("/restart")
    async def restart_node() -> Dict[str, Any]:
        """Request graceful restart"""
        # Signal restart - actual restart handled by process manager
        if hasattr(node, 'request_restart'):
            await node.request_restart()
        return {
            "success": True,
            "action": "restart",
            "message": "Restart requested - node will restart shortly",
            "timestamp": datetime.utcnow().isoformat(),
        }

    @router.post("/update-pricing")
    async def update_pricing(pricing: PricingUpdate) -> Dict[str, Any]:
        """Update node pricing configuration"""
        if not hasattr(node, 'pricing_config'):
            raise HTTPException(status_code=400, detail="Node does not support pricing updates")

        updated = {}
        if pricing.per_request is not None:
            node.pricing_config.per_request = pricing.per_request
            updated["per_request"] = pricing.per_request
        if pricing.per_token is not None:
            node.pricing_config.per_token = pricing.per_token
            updated["per_token"] = pricing.per_token
        if pricing.per_training_round is not None:
            node.pricing_config.per_training_round = pricing.per_training_round
            updated["per_training_round"] = pricing.per_training_round
        if pricing.minimum_payment is not None:
            node.pricing_config.minimum_payment = pricing.minimum_payment
            updated["minimum_payment"] = pricing.minimum_payment

        return {
            "success": True,
            "action": "update_pricing",
            "message": "Pricing updated successfully",
            "updated": updated,
            "timestamp": datetime.utcnow().isoformat(),
        }

    return router
