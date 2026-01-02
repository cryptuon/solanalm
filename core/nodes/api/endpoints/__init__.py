"""
REST API endpoints for node dashboard
"""

from .info import router as info_router
from .stats import router as stats_router
from .hardware import router as hardware_router
from .logs import router as logs_router
from .control import router as control_router
from .training import router as training_router

__all__ = [
    "info_router",
    "stats_router",
    "hardware_router",
    "logs_router",
    "control_router",
    "training_router",
]
