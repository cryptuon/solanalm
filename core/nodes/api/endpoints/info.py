"""
Node information endpoints
"""

from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends

router = APIRouter(tags=["info"])


def get_node_info_endpoint(node: Any):
    """Create info endpoint with node reference"""

    @router.get("/info")
    async def get_node_info() -> Dict[str, Any]:
        """Get node identity and configuration"""
        node_type = getattr(node, 'node_type', 'unknown')
        if hasattr(node_type, 'value'):
            node_type = node_type.value

        return {
            "node_id": getattr(node, 'node_id', 'unknown'),
            "node_type": node_type,
            "version": "0.1.0",
            "wallet_address": getattr(node, 'wallet_address', 'unknown'),
            "endpoint_url": f"http://{getattr(node, 'host', 'localhost')}:{getattr(node, 'port', 8100)}",
            "gateway_url": getattr(node, 'gateway_url', None),
            "started_at": getattr(node, 'start_time', datetime.utcnow()).isoformat() if hasattr(node, 'start_time') else datetime.utcnow().isoformat(),
            "uptime_seconds": _calculate_uptime(node),
            "supported_models": getattr(node, 'supported_models', [getattr(node, 'model_name', 'unknown')]),
            "backend_type": getattr(node, 'backend_type', None),
        }

    @router.get("/health")
    async def get_health() -> Dict[str, Any]:
        """Get detailed health status"""
        stats = getattr(node, 'stats', {})
        model_loaded = getattr(node, 'model', None) is not None or getattr(node, 'tokenizer', None) is not None

        return {
            "status": "healthy" if model_loaded else "initializing",
            "is_ready": model_loaded,
            "is_paused": getattr(node, 'is_paused', False),
            "model_loaded": model_loaded,
            "gateway_connected": getattr(node, 'gateway_connected', False),
            "last_gateway_heartbeat": getattr(node, 'last_heartbeat', None),
            "device": str(getattr(node, 'device', 'cpu')),
            "model": getattr(node, 'model_name', 'unknown'),
            "stats": stats,
            "error_message": getattr(node, 'last_error', None),
        }

    @router.get("/capabilities")
    async def get_capabilities() -> Dict[str, Any]:
        """Get node capabilities including hardware and pricing"""
        # Try to get capabilities from node method
        if hasattr(node, 'get_node_capabilities'):
            try:
                caps = await node.get_node_capabilities()
                if hasattr(caps, 'dict'):
                    return caps.dict()
                return caps
            except Exception:
                pass

        # Fallback to building from node attributes
        hardware = {}
        if hasattr(node, 'hardware_detector'):
            try:
                hardware = {
                    "cpu": node.hardware_detector.get_cpu_info(),
                    "memory": node.hardware_detector.get_memory_info(),
                    "gpu": node.hardware_detector.get_gpu_info(),
                    "storage": node.hardware_detector.get_storage_info(),
                }
            except Exception:
                pass

        pricing = getattr(node, 'pricing_config', {
            "per_request": 0.001,
            "per_token": 0.0001,
            "per_training_round": 0.0,
            "minimum_payment": 0.0005,
        })
        if hasattr(pricing, 'dict'):
            pricing = pricing.dict()

        return {
            "node_id": getattr(node, 'node_id', 'unknown'),
            "node_type": _get_node_type(node),
            "wallet_address": getattr(node, 'wallet_address', 'unknown'),
            "endpoint_url": f"http://{getattr(node, 'host', 'localhost')}:{getattr(node, 'port', 8100)}",
            "hardware": hardware,
            "pricing": pricing,
            "supported_models": getattr(node, 'supported_models', [getattr(node, 'model_name', 'unknown')]),
            "max_concurrent_requests": getattr(node, 'max_concurrent_requests', 1),
            "status": "online",
        }

    return router


def _calculate_uptime(node: Any) -> float:
    """Calculate node uptime in seconds"""
    start_time = getattr(node, 'start_time', None)
    if start_time is None:
        return 0.0
    if isinstance(start_time, datetime):
        return (datetime.utcnow() - start_time).total_seconds()
    return 0.0


def _get_node_type(node: Any) -> str:
    """Get node type as string"""
    node_type = getattr(node, 'node_type', 'unknown')
    if hasattr(node_type, 'value'):
        return node_type.value
    return str(node_type)
