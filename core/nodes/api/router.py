"""
Main Node API Router - Unified API for node dashboards

This router provides REST and WebSocket endpoints that both
the TUI and web dashboard consume. Also serves the Vue.js frontend.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import logging
import uuid

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from .collectors import StatsCollector, HardwareCollector, LogCollector, EventEmitter
from .websocket import WebSocketManager, ChannelBroadcaster
from .endpoints.info import get_node_info_endpoint
from .endpoints.stats import get_stats_endpoints
from .endpoints.hardware import get_hardware_endpoints
from .endpoints.logs import get_log_endpoints
from .endpoints.control import get_control_endpoints
from .endpoints.training import get_training_endpoints

logger = logging.getLogger(__name__)


class NodeAPIRouter:
    """
    Unified API router for node dashboards.

    Provides REST and WebSocket endpoints for monitoring and controlling
    a SolanaLM node. Both the Textual TUI and Vue.js web dashboard
    consume this same API.

    Usage:
        node_api = NodeAPIRouter(node)
        node_api.mount_to_app(app)
    """

    def __init__(self, node: Any, prefix: str = "/api/v1/node"):
        """
        Initialize the Node API Router.

        Args:
            node: The node instance (InferenceNode, TrainingNode, ProxyNode)
            prefix: URL prefix for all endpoints (default: /api/v1/node)
        """
        self.node = node
        self.prefix = prefix
        self.router = APIRouter(prefix=prefix)

        # Initialize collectors
        self.stats_collector = StatsCollector(node)
        self.hardware_collector = HardwareCollector()
        self.log_collector = LogCollector()
        self.event_emitter = EventEmitter()

        # Initialize WebSocket manager
        self.ws_manager = WebSocketManager()
        self.channel_broadcaster = ChannelBroadcaster(
            ws_manager=self.ws_manager,
            stats_collector=self.stats_collector,
            hardware_collector=self.hardware_collector,
            log_collector=self.log_collector,
            event_emitter=self.event_emitter,
        )

        # Background tasks
        self._tasks: List[asyncio.Task] = []

        # Setup routes
        self._setup_routes()

        logger.info(f"NodeAPIRouter initialized with prefix: {prefix}")

    def _setup_routes(self) -> None:
        """Setup all API routes"""
        # Info endpoints (no collector needed)
        info_router = get_node_info_endpoint(self.node)
        self.router.include_router(info_router)

        # Stats endpoints
        stats_router = get_stats_endpoints(self.stats_collector)
        self.router.include_router(stats_router)

        # Hardware endpoints
        hardware_router = get_hardware_endpoints(self.hardware_collector)
        self.router.include_router(hardware_router)

        # Logs and events endpoints
        logs_router = get_log_endpoints(self.log_collector, self.event_emitter)
        self.router.include_router(logs_router)

        # Control endpoints
        control_router = get_control_endpoints(self.node, self.event_emitter)
        self.router.include_router(control_router)

        # Training endpoints (conditional based on node type)
        if self._is_training_capable():
            training_router = get_training_endpoints(self.node)
            self.router.include_router(training_router)

        # Gateway status endpoint
        @self.router.get("/gateway")
        async def get_gateway_status() -> Dict[str, Any]:
            """Get gateway connection status"""
            return {
                "connected": getattr(self.node, 'gateway_connected', False),
                "gateway_url": getattr(self.node, 'gateway_url', None),
                "last_heartbeat": getattr(self.node, 'last_heartbeat', None),
                "registered": getattr(self.node, 'registered_with_gateway', False),
            }

    def _is_training_capable(self) -> bool:
        """Check if node supports training operations"""
        return hasattr(self.node, 'current_round') or hasattr(self.node, 'training_history')

    def mount_to_app(self, app: FastAPI, serve_frontend: bool = True) -> None:
        """
        Mount the API router to a FastAPI application.

        Args:
            app: The FastAPI application instance
            serve_frontend: Whether to serve the Vue.js frontend (default: True)
        """
        # Mount REST API
        app.include_router(self.router)

        # Add WebSocket endpoint
        @app.websocket("/ws/v1/node")
        async def websocket_endpoint(websocket: WebSocket):
            client_id = f"ws_{uuid.uuid4().hex[:8]}"
            await self.ws_manager.connect(websocket, client_id)

            try:
                while True:
                    data = await websocket.receive_json()
                    await self.ws_manager.handle_message(client_id, data)
            except WebSocketDisconnect:
                await self.ws_manager.disconnect(client_id)
            except Exception as e:
                logger.error(f"WebSocket error for {client_id}: {e}")
                await self.ws_manager.disconnect(client_id)

        # Serve Vue.js frontend
        if serve_frontend:
            self._mount_frontend(app)

        # Add startup/shutdown events
        @app.on_event("startup")
        async def startup_node_api():
            await self.start()

        @app.on_event("shutdown")
        async def shutdown_node_api():
            await self.stop()

        logger.info("NodeAPIRouter mounted to FastAPI app")

    def _mount_frontend(self, app: FastAPI) -> None:
        """
        Mount the Vue.js frontend static files.

        The frontend is served from the 'frontend/dist' directory.
        For SPA routing, all non-API routes serve index.html.
        """
        # Determine frontend dist path
        # Look for frontend relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        frontend_dist = project_root / "frontend" / "dist"

        if not frontend_dist.exists():
            logger.warning(
                f"Frontend dist not found at {frontend_dist}. "
                "Run 'npm run build' in frontend/ to build the dashboard."
            )
            # Serve a placeholder page
            @app.get("/", response_class=HTMLResponse)
            async def frontend_placeholder():
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>SolanaLM Node Dashboard</title>
                    <style>
                        body {
                            font-family: system-ui, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                            background: #1a1a2e;
                            color: #fff;
                        }
                        .container { text-align: center; }
                        h1 { color: #14f195; }
                        code {
                            background: #2d2d44;
                            padding: 2px 8px;
                            border-radius: 4px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>SolanaLM Node Dashboard</h1>
                        <p>The web dashboard is not built yet.</p>
                        <p>To build it, run:</p>
                        <p><code>cd frontend && npm install && npm run build</code></p>
                        <p style="margin-top: 2em">
                            API is available at <a href="/api/v1/node/info" style="color: #9945ff">/api/v1/node/info</a>
                        </p>
                    </div>
                </body>
                </html>
                """
            return

        logger.info(f"Serving frontend from {frontend_dist}")

        # Serve index.html for SPA routes (must be defined before static mount)
        index_path = frontend_dist / "index.html"

        @app.get("/", response_class=FileResponse)
        async def serve_index():
            return FileResponse(index_path)

        # Define SPA catch-all for client-side routing
        # This must match all frontend routes that aren't API or static files
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Don't intercept API or WebSocket routes
            if full_path.startswith(("api/", "ws/")):
                return None

            # Check if it's a static file request
            static_path = frontend_dist / full_path
            if static_path.exists() and static_path.is_file():
                return FileResponse(static_path)

            # Serve index.html for SPA routing
            return FileResponse(index_path)

        # Mount static assets directory
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            logger.info("Mounted /assets static files")

    async def start(self) -> None:
        """Start background tasks and collectors"""
        # Attach log collector to root logger
        self.log_collector.attach_to_logger(level=logging.INFO)

        # Start channel broadcaster
        await self.channel_broadcaster.start()

        # Emit startup event
        await self.event_emitter.emit(
            event_type="node_started",
            title="Node Started",
            description="Node API is now available",
            severity="info",
        )

        logger.info("NodeAPIRouter started")

    async def stop(self) -> None:
        """Stop background tasks and cleanup"""
        # Stop broadcaster
        await self.channel_broadcaster.stop()

        # Detach log collector
        self.log_collector.detach_from_logger()

        # Cancel any remaining tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        logger.info("NodeAPIRouter stopped")

    # Helper methods for node integration

    async def record_request(
        self,
        request_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        processing_time: float,
        cost_sol: float,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a completed request for stats tracking"""
        from .collectors.stats_collector import RequestRecord

        record = RequestRecord(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            processing_time=processing_time,
            cost_sol=cost_sol,
            success=success,
            error_message=error_message,
        )
        await self.stats_collector.record_request(record)

        # Emit event
        if success:
            await self.event_emitter.emit_request_completed(
                request_id=request_id,
                tokens=completion_tokens,
                processing_time=processing_time,
                cost_sol=cost_sol,
            )
        else:
            await self.event_emitter.emit_request_failed(
                request_id=request_id,
                error=error_message or "Unknown error",
            )

    async def record_earning(
        self,
        amount_sol: float,
        payment_type: str = "inference",
        transaction_signature: Optional[str] = None,
        request_id: Optional[str] = None,
        round_id: Optional[str] = None,
    ) -> None:
        """Record an earning for stats tracking"""
        from .collectors.stats_collector import EarningsRecord

        record = EarningsRecord(
            timestamp=datetime.utcnow(),
            amount_sol=amount_sol,
            transaction_signature=transaction_signature,
            request_id=request_id,
            round_id=round_id,
            payment_type=payment_type,
            status="confirmed" if transaction_signature else "pending",
        )
        await self.stats_collector.record_earning(record)

        # Emit event
        if transaction_signature:
            await self.event_emitter.emit_payment_received(
                amount_sol=amount_sol,
                transaction_signature=transaction_signature,
            )

        # Broadcast earnings update
        await self.channel_broadcaster.broadcast_earnings_update({
            "amount_sol": amount_sol,
            "payment_type": payment_type,
            "total_earnings": self.stats_collector._total_earnings_sol,
        })

    async def emit_training_update(
        self,
        round_id: str,
        status: str,
        progress: float,
        loss: Optional[float] = None,
    ) -> None:
        """Emit a training round update"""
        await self.channel_broadcaster.broadcast_training_update({
            "round_id": round_id,
            "status": status,
            "progress": progress,
            "loss": loss,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def add_log(
        self,
        message: str,
        level: str = "INFO",
        source: str = "node",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a log entry manually"""
        self.log_collector.add_log(
            message=message,
            level=level,
            source=source,
            extra=extra,
        )

    async def emit_event(
        self,
        event_type: str,
        title: str,
        description: str = "",
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit a custom event"""
        await self.event_emitter.emit(
            event_type=event_type,
            title=title,
            description=description,
            severity=severity,
            data=data,
        )
