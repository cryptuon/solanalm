"""
Training-specific endpoints for training nodes
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/training", tags=["training"])


def get_training_endpoints(node: Any):
    """Create training endpoints for training nodes"""

    def _is_training_node() -> bool:
        """Check if node supports training"""
        return hasattr(node, 'current_round') or hasattr(node, 'training_history')

    @router.get("/current")
    async def get_current_round() -> Dict[str, Any]:
        """Get current training round status"""
        if not _is_training_node():
            raise HTTPException(status_code=404, detail="Not a training node")

        current_round = getattr(node, 'current_round', None)
        if current_round is None:
            return {
                "active": False,
                "round": None,
            }

        # Get training status
        status = "idle"
        if hasattr(node, 'training_status'):
            status = node.training_status
        elif hasattr(node, 'is_training') and node.is_training:
            status = "training"

        # Get progress info
        progress = 0.0
        if hasattr(node, 'training_progress'):
            progress = node.training_progress

        stats = getattr(node, 'stats', {})

        return {
            "active": True,
            "round": {
                "round_id": current_round if isinstance(current_round, str) else getattr(current_round, 'round_id', None),
                "model": getattr(node, 'model_name', 'unknown'),
                "status": status,
                "progress": progress,
                "current_epoch": getattr(node, 'current_epoch', 0),
                "total_epochs": getattr(node, 'total_epochs', 3),
                "current_loss": stats.get('average_loss', None),
                "samples_processed": stats.get('samples_trained', 0),
                "started_at": getattr(node, 'round_start_time', datetime.utcnow()).isoformat() if hasattr(node, 'round_start_time') else None,
                "expected_reward": getattr(node, 'expected_reward', 0.0),
            },
        }

    @router.get("/rounds")
    async def get_training_history(
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> Dict[str, Any]:
        """Get training round history"""
        if not _is_training_node():
            raise HTTPException(status_code=404, detail="Not a training node")

        history = getattr(node, 'training_history', [])
        stats = getattr(node, 'stats', {})

        # Convert to list of dicts
        rounds = []
        for i, round_data in enumerate(history):
            if isinstance(round_data, dict):
                rounds.append(round_data)
            elif hasattr(round_data, 'dict'):
                rounds.append(round_data.dict())

        # Apply pagination
        paginated = rounds[offset:offset + limit]

        return {
            "rounds": paginated,
            "count": len(paginated),
            "total": len(rounds),
            "offset": offset,
            "limit": limit,
            "summary": {
                "rounds_participated": stats.get('rounds_participated', 0),
                "total_samples_trained": stats.get('samples_trained', 0),
                "average_loss": stats.get('average_loss', 0.0),
                "total_rewards_earned": stats.get('rewards_earned', 0.0),
            },
        }

    @router.get("/model")
    async def get_model_info() -> Dict[str, Any]:
        """Get current model state and version info"""
        if not _is_training_node():
            raise HTTPException(status_code=404, detail="Not a training node")

        return {
            "model_name": getattr(node, 'model_name', 'unknown'),
            "model_loaded": getattr(node, 'model', None) is not None,
            "local_version": getattr(node, 'local_model_version', 0),
            "global_version": getattr(node, 'global_model_version', None),
            "last_aggregation": getattr(node, 'last_aggregation_time', None),
            "device": str(getattr(node, 'device', 'cpu')),
        }

    return router
