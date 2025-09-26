"""
Real-time Dashboard and Admin Interface
Web-based administration with live monitoring, node management, and system control
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import uvicorn
from pathlib import Path

# Import SolanaLM components
from core.monitoring.metrics_collector import metrics_collector
from core.resilience.error_handling import error_handler
from core.security.authentication import get_security_manager, User, UserRole
from core.config.production_settings import get_settings

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # connection_id -> [channel_names]

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = []
        logger.info(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str):
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
        logger.info(f"WebSocket disconnected: {connection_id}")

    async def subscribe(self, connection_id: str, channel: str):
        """Subscribe connection to a channel"""
        if connection_id in self.subscriptions:
            if channel not in self.subscriptions[connection_id]:
                self.subscriptions[connection_id].append(channel)

    async def unsubscribe(self, connection_id: str, channel: str):
        """Unsubscribe connection from a channel"""
        if connection_id in self.subscriptions:
            if channel in self.subscriptions[connection_id]:
                self.subscriptions[connection_id].remove(channel)

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Broadcast message to all subscribers of a channel"""
        disconnected = []

        for connection_id, channels in self.subscriptions.items():
            if channel in channels:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending to {connection_id}: {e}")
                        disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                self.disconnect(connection_id)
        return False


class DashboardAPI:
    """Dashboard API endpoints"""

    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.app = FastAPI(title="SolanaLM Dashboard", version="1.0.0")
        self.templates = Jinja2Templates(directory="core/dashboard/templates")

        # Create templates directory if it doesn't exist
        templates_dir = Path("core/dashboard/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Create static directory if it doesn't exist
        static_dir = Path("core/dashboard/static")
        static_dir.mkdir(parents=True, exist_ok=True)

        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            return self.templates.TemplateResponse("dashboard.html", {"request": request})

        @self.app.get("/api/network/status")
        async def get_network_status():
            """Get current network status"""
            return metrics_collector.get_network_summary()

        @self.app.get("/api/nodes")
        async def get_nodes():
            """Get all registered nodes"""
            nodes = []
            for node_id in metrics_collector.node_metrics.keys():
                node_summary = metrics_collector.get_node_summary(node_id)
                if node_summary:
                    nodes.append(node_summary)
            return {"nodes": nodes}

        @self.app.get("/api/nodes/{node_id}")
        async def get_node_details(node_id: str):
            """Get detailed node information"""
            node_summary = metrics_collector.get_node_summary(node_id)
            if not node_summary:
                raise HTTPException(status_code=404, detail="Node not found")
            return node_summary

        @self.app.post("/api/nodes/{node_id}/action")
        async def node_action(node_id: str, action: Dict[str, str]):
            """Perform action on a node"""
            action_type = action.get("action")

            if action_type == "restart":
                # In production, implement actual node restart
                await self.ws_manager.broadcast_to_channel("system", {
                    "type": "notification",
                    "level": "info",
                    "message": f"Restarting node {node_id}"
                })
                return {"status": "success", "message": f"Restart initiated for {node_id}"}

            elif action_type == "stop":
                # In production, implement actual node stop
                await self.ws_manager.broadcast_to_channel("system", {
                    "type": "notification",
                    "level": "warning",
                    "message": f"Stopping node {node_id}"
                })
                return {"status": "success", "message": f"Stop initiated for {node_id}"}

            else:
                raise HTTPException(status_code=400, detail="Invalid action")

        @self.app.get("/api/errors")
        async def get_errors():
            """Get recent errors"""
            return error_handler.get_error_summary()

        @self.app.get("/api/federated-learning")
        async def get_federated_learning_status():
            """Get federated learning status"""
            # In production, get actual FL status
            return {
                "active_rounds": 1,
                "completed_rounds": 5,
                "participating_nodes": 8,
                "average_loss": 2.34,
                "next_round_eta": "15 minutes"
            }

        @self.app.post("/api/federated-learning/start")
        async def start_federated_learning():
            """Start a new federated learning round"""
            # In production, implement actual FL round start
            await self.ws_manager.broadcast_to_channel("federated_learning", {
                "type": "round_started",
                "round_id": "round_123",
                "participants": 8,
                "timestamp": datetime.utcnow().isoformat()
            })
            return {"status": "success", "message": "Federated learning round started"}

        @self.app.get("/api/metrics/export")
        async def export_metrics(format: str = "prometheus"):
            """Export metrics in various formats"""
            if format == "prometheus":
                content = metrics_collector.get_metrics_export("prometheus")
                return JSONResponse(content=content, media_type="text/plain")
            elif format == "json":
                content = metrics_collector.get_metrics_export("json")
                return JSONResponse(content=json.loads(content))
            else:
                raise HTTPException(status_code=400, detail="Unsupported format")

        @self.app.get("/api/security/summary")
        async def get_security_summary():
            """Get security system summary"""
            security_manager = get_security_manager()
            return security_manager.get_security_summary()

        @self.app.websocket("/ws/{connection_id}")
        async def websocket_endpoint(websocket: WebSocket, connection_id: str):
            """WebSocket endpoint for real-time updates"""
            await self.ws_manager.connect(websocket, connection_id)

            try:
                while True:
                    # Receive client messages
                    data = await websocket.receive_json()
                    await self.handle_websocket_message(connection_id, data)

            except WebSocketDisconnect:
                self.ws_manager.disconnect(connection_id)

        async def handle_websocket_message(self, connection_id: str, message: Dict[str, Any]):
            """Handle incoming WebSocket messages"""
            msg_type = message.get("type")

            if msg_type == "subscribe":
                channel = message.get("channel")
                if channel:
                    await self.ws_manager.subscribe(connection_id, channel)
                    await self.ws_manager.send_to_connection(connection_id, {
                        "type": "subscribed",
                        "channel": channel
                    })

            elif msg_type == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    await self.ws_manager.unsubscribe(connection_id, channel)
                    await self.ws_manager.send_to_connection(connection_id, {
                        "type": "unsubscribed",
                        "channel": channel
                    })

            elif msg_type == "get_status":
                # Send current network status
                status = metrics_collector.get_network_summary()
                await self.ws_manager.send_to_connection(connection_id, {
                    "type": "network_status",
                    "data": status
                })


class RealTimeDashboard:
    """Main dashboard application"""

    def __init__(self):
        self.ws_manager = WebSocketManager()
        self.dashboard_api = DashboardAPI(self.ws_manager)
        self.app = self.dashboard_api.app

        # Background tasks
        self._update_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None

        # Create dashboard templates
        self._create_templates()
        self._create_static_files()

    def _create_templates(self):
        """Create HTML templates for dashboard"""
        templates_dir = Path("core/dashboard/templates")
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Main dashboard template
        dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SolanaLM Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .status-active { color: #10B981; }
        .status-inactive { color: #EF4444; }
        .status-degraded { color: #F59E0B; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="min-h-screen">
        <!-- Header -->
        <header class="bg-blue-600 text-white p-4">
            <h1 class="text-2xl font-bold">SolanaLM Network Dashboard</h1>
            <div class="text-sm opacity-75" id="connection-status">Connecting...</div>
        </header>

        <!-- Main Content -->
        <div class="container mx-auto p-4">
            <!-- Network Overview -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="text-lg font-semibold mb-2">Total Nodes</h3>
                    <div class="text-3xl font-bold text-blue-600" id="total-nodes">0</div>
                </div>
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="text-lg font-semibold mb-2">Active Nodes</h3>
                    <div class="text-3xl font-bold text-green-600" id="active-nodes">0</div>
                </div>
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="text-lg font-semibold mb-2">Total Requests</h3>
                    <div class="text-3xl font-bold text-purple-600" id="total-requests">0</div>
                </div>
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="text-lg font-semibold mb-2">Success Rate</h3>
                    <div class="text-3xl font-bold text-indigo-600" id="success-rate">0%</div>
                </div>
            </div>

            <!-- Charts -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="text-lg font-semibold mb-4">Request Rate</h3>
                    <canvas id="request-chart" width="400" height="200"></canvas>
                </div>
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="text-lg font-semibold mb-4">Node Distribution</h3>
                    <canvas id="node-chart" width="400" height="200"></canvas>
                </div>
            </div>

            <!-- Nodes Table -->
            <div class="bg-white rounded-lg shadow">
                <div class="p-4 border-b">
                    <h3 class="text-lg font-semibold">Network Nodes</h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="min-w-full">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Node ID</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requests</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Revenue</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="nodes-table" class="bg-white divide-y divide-gray-200">
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Notifications -->
            <div id="notifications" class="fixed bottom-4 right-4 z-50"></div>
        </div>
    </div>

    <script src="/static/dashboard.js"></script>
</body>
</html>
        '''
        (templates_dir / "dashboard.html").write_text(dashboard_html)

    def _create_static_files(self):
        """Create static JavaScript and CSS files"""
        static_dir = Path("core/dashboard/static")
        static_dir.mkdir(parents=True, exist_ok=True)

        # Dashboard JavaScript
        dashboard_js = '''
class SolanaLMDashboard {
    constructor() {
        this.ws = null;
        this.charts = {};
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.initCharts();
        this.loadInitialData();
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const connectionId = 'dashboard_' + Date.now();
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/${connectionId}`);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            document.getElementById('connection-status').textContent = 'Connected';

            // Subscribe to channels
            this.ws.send(JSON.stringify({type: 'subscribe', channel: 'system'}));
            this.ws.send(JSON.stringify({type: 'subscribe', channel: 'metrics'}));
            this.ws.send(JSON.stringify({type: 'subscribe', channel: 'federated_learning'}));
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            document.getElementById('connection-status').textContent = 'Disconnected - Reconnecting...';

            // Reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleWebSocketMessage(data) {
        switch(data.type) {
            case 'network_status':
                this.updateNetworkStatus(data.data);
                break;
            case 'notification':
                this.showNotification(data.message, data.level);
                break;
            case 'round_started':
                this.showNotification(`FL Round ${data.round_id} started with ${data.participants} participants`, 'info');
                break;
        }
    }

    async loadInitialData() {
        try {
            const response = await fetch('/api/network/status');
            const data = await response.json();
            this.updateNetworkStatus(data);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }

        try {
            const response = await fetch('/api/nodes');
            const data = await response.json();
            this.updateNodesTable(data.nodes);
        } catch (error) {
            console.error('Error loading nodes:', error);
        }
    }

    updateNetworkStatus(data) {
        document.getElementById('total-nodes').textContent = data.network.total_nodes;
        document.getElementById('active-nodes').textContent = data.network.active_nodes;
        document.getElementById('total-requests').textContent = data.network.total_requests;
        document.getElementById('success-rate').textContent =
            (data.network.success_rate * 100).toFixed(1) + '%';
    }

    updateNodesTable(nodes) {
        const tbody = document.getElementById('nodes-table');
        tbody.innerHTML = '';

        nodes.forEach(node => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${node.node_id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${node.type}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="status-${node.status} text-sm font-semibold">${node.status}</span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${node.performance.requests_served}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${node.performance.revenue_earned.toFixed(4)} SOL</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="dashboard.nodeAction('${node.node_id}', 'restart')"
                            class="text-blue-600 hover:text-blue-900 mr-2">Restart</button>
                    <button onclick="dashboard.nodeAction('${node.node_id}', 'stop')"
                            class="text-red-600 hover:text-red-900">Stop</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async nodeAction(nodeId, action) {
        try {
            const response = await fetch(`/api/nodes/${nodeId}/action`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: action})
            });
            const result = await response.json();
            this.showNotification(result.message, 'success');
        } catch (error) {
            this.showNotification('Action failed: ' + error.message, 'error');
        }
    }

    initCharts() {
        // Request rate chart
        const requestCtx = document.getElementById('request-chart').getContext('2d');
        this.charts.requests = new Chart(requestCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Requests/min',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {beginAtZero: true}
                }
            }
        });

        // Node distribution chart
        const nodeCtx = document.getElementById('node-chart').getContext('2d');
        this.charts.nodes = new Chart(nodeCtx, {
            type: 'doughnut',
            data: {
                labels: ['Inference', 'Training', 'Proxy'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgb(34, 197, 94)',
                        'rgb(168, 85, 247)',
                        'rgb(249, 115, 22)'
                    ]
                }]
            },
            options: {responsive: true}
        });
    }

    showNotification(message, level = 'info') {
        const notification = document.createElement('div');
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        notification.className = `${colors[level]} text-white px-4 py-2 rounded-lg mb-2 shadow-lg`;
        notification.textContent = message;

        document.getElementById('notifications').appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => notification.remove(), 5000);
    }
}

// Initialize dashboard
const dashboard = new SolanaLMDashboard();
        '''
        (static_dir / "dashboard.js").write_text(dashboard_js)

    async def start_background_tasks(self):
        """Start background tasks for real-time updates"""
        self._update_task = asyncio.create_task(self._broadcast_updates())
        self._monitoring_task = asyncio.create_task(self._monitor_system())

    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self._update_task:
            self._update_task.cancel()
        if self._monitoring_task:
            self._monitoring_task.cancel()

    async def _broadcast_updates(self):
        """Broadcast periodic updates to connected clients"""
        while True:
            try:
                # Broadcast network status
                network_status = metrics_collector.get_network_summary()
                await self.ws_manager.broadcast_to_channel("metrics", {
                    "type": "network_status",
                    "data": network_status
                })

                # Wait 5 seconds before next update
                await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error broadcasting updates: {e}")
                await asyncio.sleep(10)

    async def _monitor_system(self):
        """Monitor system health and send alerts"""
        while True:
            try:
                # Check for system issues
                network_status = metrics_collector.get_network_summary()

                # Alert if success rate is low
                success_rate = network_status.get("network", {}).get("success_rate", 1.0)
                if success_rate < 0.9:
                    await self.ws_manager.broadcast_to_channel("system", {
                        "type": "notification",
                        "level": "warning",
                        "message": f"Low success rate: {success_rate*100:.1f}%"
                    })

                # Alert if nodes are offline
                active_nodes = network_status.get("network", {}).get("active_nodes", 0)
                total_nodes = network_status.get("network", {}).get("total_nodes", 0)
                if total_nodes > 0 and active_nodes < total_nodes * 0.8:
                    await self.ws_manager.broadcast_to_channel("system", {
                        "type": "notification",
                        "level": "error",
                        "message": f"Only {active_nodes}/{total_nodes} nodes active"
                    })

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring system: {e}")
                await asyncio.sleep(60)


# Global dashboard instance
dashboard: Optional[RealTimeDashboard] = None


def create_dashboard() -> RealTimeDashboard:
    """Create and configure the dashboard"""
    global dashboard
    dashboard = RealTimeDashboard()
    return dashboard


def get_dashboard() -> RealTimeDashboard:
    """Get the global dashboard instance"""
    if dashboard is None:
        raise RuntimeError("Dashboard not initialized")
    return dashboard


async def start_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Start the dashboard server"""
    dashboard = create_dashboard()
    await dashboard.start_background_tasks()

    config = uvicorn.Config(dashboard.app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)

    try:
        await server.serve()
    finally:
        await dashboard.stop_background_tasks()


if __name__ == "__main__":
    asyncio.run(start_dashboard())