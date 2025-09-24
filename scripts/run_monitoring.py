#!/usr/bin/env python3
"""
SolanaLM Monitoring System

Real-time monitoring and metrics collection for the SolanaLM network:
- Network health and performance metrics
- Node status and availability
- Privacy network monitoring
- Training round progress tracking
- Cost and usage analytics
"""

import asyncio
import argparse
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

logger = logging.getLogger(__name__)


@dataclass
class NetworkMetrics:
    """Network-wide metrics"""
    timestamp: float
    total_nodes: int
    active_nodes: int
    inference_nodes: int
    training_nodes: int
    privacy_capable_nodes: int
    average_reputation: float
    total_requests_24h: int
    success_rate: float
    average_latency: float
    privacy_requests_percentage: float


@dataclass
class NodeMetrics:
    """Individual node metrics"""
    node_id: str
    node_type: str
    status: str
    last_seen: float
    reputation_score: float
    total_requests: int
    success_rate: float
    average_latency: float
    current_load: float
    supports_privacy: bool


@dataclass
class PrivacyMetrics:
    """Privacy network specific metrics"""
    timestamp: float
    active_circuits: int
    average_circuit_length: float
    geographic_diversity_score: float
    network_diversity_score: float
    anonymity_set_size: int
    privacy_success_rate: float
    average_privacy_latency: float


@dataclass
class TrainingMetrics:
    """Federated learning metrics"""
    timestamp: float
    active_rounds: int
    total_participants: int
    average_round_duration: float
    models_trained: List[str]
    total_rewards_distributed: float
    training_success_rate: float


class SolanaLMMonitor:
    """Main monitoring system"""

    def __init__(self, gateway_url: str, metrics_interval: int = 30):
        self.gateway_url = gateway_url.rstrip('/')
        self.metrics_interval = metrics_interval

        # Metrics storage (in production, use proper time-series DB)
        self.network_metrics_history: List[NetworkMetrics] = []
        self.node_metrics_history: Dict[str, List[NodeMetrics]] = {}
        self.privacy_metrics_history: List[PrivacyMetrics] = []
        self.training_metrics_history: List[TrainingMetrics] = []

        # Web server for dashboard
        self.app = FastAPI(title="SolanaLM Monitor", version="1.0.0")
        self.setup_routes()

        # Monitoring state
        self.monitoring_active = False
        self.last_collection_time = 0

    def setup_routes(self):
        """Setup monitoring dashboard routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Main monitoring dashboard"""
            return self.get_dashboard_html()

        @self.app.get("/api/network/metrics")
        async def network_metrics():
            """Get latest network metrics"""
            if not self.network_metrics_history:
                raise HTTPException(status_code=404, detail="No metrics available")
            return asdict(self.network_metrics_history[-1])

        @self.app.get("/api/network/history")
        async def network_history(hours: int = 24):
            """Get network metrics history"""
            cutoff_time = time.time() - (hours * 3600)
            filtered_metrics = [
                asdict(m) for m in self.network_metrics_history
                if m.timestamp >= cutoff_time
            ]
            return {"metrics": filtered_metrics}

        @self.app.get("/api/nodes")
        async def nodes_status():
            """Get current status of all nodes"""
            latest_metrics = {}
            for node_id, metrics_list in self.node_metrics_history.items():
                if metrics_list:
                    latest_metrics[node_id] = asdict(metrics_list[-1])
            return {"nodes": latest_metrics}

        @self.app.get("/api/privacy/metrics")
        async def privacy_metrics():
            """Get latest privacy network metrics"""
            if not self.privacy_metrics_history:
                raise HTTPException(status_code=404, detail="No privacy metrics available")
            return asdict(self.privacy_metrics_history[-1])

        @self.app.get("/api/training/metrics")
        async def training_metrics():
            """Get latest training metrics"""
            if not self.training_metrics_history:
                raise HTTPException(status_code=404, detail="No training metrics available")
            return asdict(self.training_metrics_history[-1])

        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get current system alerts"""
            return {"alerts": self.generate_alerts()}

        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy" if self.monitoring_active else "inactive",
                "last_collection": self.last_collection_time,
                "metrics_count": len(self.network_metrics_history)
            }

    async def start_monitoring(self):
        """Start the monitoring collection loop"""
        logger.info("Starting SolanaLM monitoring system...")
        self.monitoring_active = True

        try:
            while self.monitoring_active:
                start_time = time.time()

                try:
                    await self.collect_all_metrics()
                    self.last_collection_time = time.time()

                    # Clean up old metrics (keep last 7 days)
                    self.cleanup_old_metrics()

                except Exception as e:
                    logger.error(f"Metrics collection failed: {e}")

                # Wait for next collection interval
                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.metrics_interval - elapsed_time)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Monitoring cancelled")
        finally:
            self.monitoring_active = False

    async def collect_all_metrics(self):
        """Collect all types of metrics"""
        logger.debug("Collecting metrics...")

        # Collect in parallel for efficiency
        await asyncio.gather(
            self.collect_network_metrics(),
            self.collect_node_metrics(),
            self.collect_privacy_metrics(),
            self.collect_training_metrics(),
            return_exceptions=True
        )

    async def collect_network_metrics(self):
        """Collect network-wide metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get network stats
                async with session.get(f"{self.gateway_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        network_stats = data.get("network_stats", {})

                        metrics = NetworkMetrics(
                            timestamp=time.time(),
                            total_nodes=network_stats.get("total_nodes", 0),
                            active_nodes=network_stats.get("active_nodes", 0),
                            inference_nodes=network_stats.get("inference_nodes", 0),
                            training_nodes=network_stats.get("training_nodes", 0),
                            privacy_capable_nodes=network_stats.get("privacy_capable_nodes", 0),
                            average_reputation=network_stats.get("average_reputation", 0.0),
                            total_requests_24h=network_stats.get("total_requests_24h", 0),
                            success_rate=network_stats.get("success_rate", 0.0),
                            average_latency=network_stats.get("average_latency", 0.0),
                            privacy_requests_percentage=network_stats.get("privacy_requests_percentage", 0.0)
                        )

                        self.network_metrics_history.append(metrics)
                        logger.debug(f"Collected network metrics: {metrics.active_nodes} active nodes")

        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")

    async def collect_node_metrics(self):
        """Collect individual node metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get node list
                async with session.get(f"{self.gateway_url}/nodes") as response:
                    if response.status == 200:
                        nodes = await response.json()

                        for node_data in nodes:
                            node_id = node_data["node_id"]

                            metrics = NodeMetrics(
                                node_id=node_id,
                                node_type=node_data.get("node_type", "unknown"),
                                status=node_data.get("status", "unknown"),
                                last_seen=node_data.get("last_seen", time.time()),
                                reputation_score=node_data.get("reputation_score", 0.0),
                                total_requests=node_data.get("total_requests", 0),
                                success_rate=node_data.get("success_rate", 0.0),
                                average_latency=node_data.get("average_latency", 0.0),
                                current_load=node_data.get("current_load", 0.0),
                                supports_privacy=node_data.get("supports_onion_routing", False)
                            )

                            if node_id not in self.node_metrics_history:
                                self.node_metrics_history[node_id] = []

                            self.node_metrics_history[node_id].append(metrics)

                        logger.debug(f"Collected metrics for {len(nodes)} nodes")

        except Exception as e:
            logger.error(f"Failed to collect node metrics: {e}")

    async def collect_privacy_metrics(self):
        """Collect privacy network metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get privacy status
                async with session.get(f"{self.gateway_url}/privacy_status") as response:
                    if response.status == 200:
                        data = await response.json()

                        metrics = PrivacyMetrics(
                            timestamp=time.time(),
                            active_circuits=data.get("active_circuits", 0),
                            average_circuit_length=data.get("average_circuit_length", 0.0),
                            geographic_diversity_score=data.get("geographic_diversity_score", 0.0),
                            network_diversity_score=data.get("network_diversity_score", 0.0),
                            anonymity_set_size=data.get("anonymity_set_size", 0),
                            privacy_success_rate=data.get("privacy_success_rate", 0.0),
                            average_privacy_latency=data.get("average_privacy_latency", 0.0)
                        )

                        self.privacy_metrics_history.append(metrics)
                        logger.debug(f"Collected privacy metrics: {metrics.active_circuits} circuits")

        except Exception as e:
            logger.error(f"Failed to collect privacy metrics: {e}")

    async def collect_training_metrics(self):
        """Collect federated learning metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get training status
                async with session.get(f"{self.gateway_url}/training/status") as response:
                    if response.status == 200:
                        data = await response.json()

                        metrics = TrainingMetrics(
                            timestamp=time.time(),
                            active_rounds=data.get("active_rounds", 0),
                            total_participants=data.get("total_participants", 0),
                            average_round_duration=data.get("average_round_duration", 0.0),
                            models_trained=data.get("models_trained", []),
                            total_rewards_distributed=data.get("total_rewards_distributed", 0.0),
                            training_success_rate=data.get("training_success_rate", 0.0)
                        )

                        self.training_metrics_history.append(metrics)
                        logger.debug(f"Collected training metrics: {metrics.active_rounds} rounds")

        except Exception as e:
            logger.error(f"Failed to collect training metrics: {e}")

    def cleanup_old_metrics(self, max_age_hours: int = 168):  # 7 days
        """Clean up old metrics to prevent memory issues"""
        cutoff_time = time.time() - (max_age_hours * 3600)

        # Clean network metrics
        self.network_metrics_history = [
            m for m in self.network_metrics_history if m.timestamp >= cutoff_time
        ]

        # Clean node metrics
        for node_id in list(self.node_metrics_history.keys()):
            self.node_metrics_history[node_id] = [
                m for m in self.node_metrics_history[node_id] if m.timestamp >= cutoff_time
            ]
            # Remove empty node histories
            if not self.node_metrics_history[node_id]:
                del self.node_metrics_history[node_id]

        # Clean privacy metrics
        self.privacy_metrics_history = [
            m for m in self.privacy_metrics_history if m.timestamp >= cutoff_time
        ]

        # Clean training metrics
        self.training_metrics_history = [
            m for m in self.training_metrics_history if m.timestamp >= cutoff_time
        ]

    def generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate system alerts based on metrics"""
        alerts = []

        if not self.network_metrics_history:
            return alerts

        latest_network = self.network_metrics_history[-1]

        # Low node count alert
        if latest_network.active_nodes < 3:
            alerts.append({
                "severity": "high",
                "type": "low_node_count",
                "message": f"Only {latest_network.active_nodes} active nodes (need 3+ for reliability)",
                "timestamp": latest_network.timestamp
            })

        # Low success rate alert
        if latest_network.success_rate < 0.95:
            alerts.append({
                "severity": "medium",
                "type": "low_success_rate",
                "message": f"Network success rate is {latest_network.success_rate:.1%} (target: 95%+)",
                "timestamp": latest_network.timestamp
            })

        # High latency alert
        if latest_network.average_latency > 10.0:
            alerts.append({
                "severity": "medium",
                "type": "high_latency",
                "message": f"Average latency is {latest_network.average_latency:.1f}s (target: <5s)",
                "timestamp": latest_network.timestamp
            })

        # Privacy network alerts
        if self.privacy_metrics_history:
            latest_privacy = self.privacy_metrics_history[-1]

            if latest_privacy.privacy_success_rate < 0.90:
                alerts.append({
                    "severity": "medium",
                    "type": "privacy_issues",
                    "message": f"Privacy success rate is {latest_privacy.privacy_success_rate:.1%} (target: 90%+)",
                    "timestamp": latest_privacy.timestamp
                })

        # Node-specific alerts
        current_time = time.time()
        for node_id, metrics_list in self.node_metrics_history.items():
            if not metrics_list:
                continue

            latest_node = metrics_list[-1]

            # Node offline alert
            if current_time - latest_node.last_seen > 300:  # 5 minutes
                alerts.append({
                    "severity": "high",
                    "type": "node_offline",
                    "message": f"Node {node_id} has been offline for {(current_time - latest_node.last_seen)/60:.1f} minutes",
                    "timestamp": current_time
                })

            # Low node reputation alert
            if latest_node.reputation_score < 0.7:
                alerts.append({
                    "severity": "low",
                    "type": "low_reputation",
                    "message": f"Node {node_id} has low reputation: {latest_node.reputation_score:.2f}",
                    "timestamp": latest_node.last_seen
                })

        return alerts

    def get_dashboard_html(self) -> str:
        """Generate HTML dashboard"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>SolanaLM Monitor</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .metric-label { color: #7f8c8d; font-size: 0.9em; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .alert-high { background: #e74c3c; color: white; }
        .alert-medium { background: #f39c12; color: white; }
        .alert-low { background: #f1c40f; color: #2c3e50; }
        .status-good { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-error { color: #e74c3c; }
        #refresh-time { color: #7f8c8d; font-size: 0.8em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 SolanaLM Network Monitor</h1>
        <p>Real-time monitoring of the privacy-preserving AI network</p>
        <div id="refresh-time">Loading...</div>
    </div>

    <div id="alerts-container"></div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Active Nodes</div>
            <div class="metric-value" id="active-nodes">-</div>
            <div class="metric-label">Total: <span id="total-nodes">-</span></div>
        </div>

        <div class="metric-card">
            <div class="metric-label">Network Success Rate</div>
            <div class="metric-value" id="success-rate">-</div>
            <div class="metric-label">Target: 95%+</div>
        </div>

        <div class="metric-card">
            <div class="metric-label">Average Latency</div>
            <div class="metric-value" id="avg-latency">-</div>
            <div class="metric-label">Target: <5s</div>
        </div>

        <div class="metric-card">
            <div class="metric-label">Privacy Capable Nodes</div>
            <div class="metric-value" id="privacy-nodes">-</div>
            <div class="metric-label">Tor-like anonymity ready</div>
        </div>

        <div class="metric-card">
            <div class="metric-label">Active Training Rounds</div>
            <div class="metric-value" id="training-rounds">-</div>
            <div class="metric-label">Federated learning</div>
        </div>

        <div class="metric-card">
            <div class="metric-label">Privacy Usage</div>
            <div class="metric-value" id="privacy-usage">-</div>
            <div class="metric-label">% of requests</div>
        </div>
    </div>

    <script>
        async function updateMetrics() {
            try {
                // Fetch network metrics
                const networkResp = await fetch('/api/network/metrics');
                const network = await networkResp.json();

                document.getElementById('active-nodes').textContent = network.active_nodes;
                document.getElementById('total-nodes').textContent = network.total_nodes;
                document.getElementById('success-rate').textContent = (network.success_rate * 100).toFixed(1) + '%';
                document.getElementById('avg-latency').textContent = network.average_latency.toFixed(1) + 's';
                document.getElementById('privacy-nodes').textContent = network.privacy_capable_nodes;
                document.getElementById('privacy-usage').textContent = network.privacy_requests_percentage.toFixed(1) + '%';

                // Fetch training metrics
                try {
                    const trainingResp = await fetch('/api/training/metrics');
                    const training = await trainingResp.json();
                    document.getElementById('training-rounds').textContent = training.active_rounds;
                } catch {
                    document.getElementById('training-rounds').textContent = '0';
                }

                // Fetch alerts
                const alertsResp = await fetch('/api/alerts');
                const alerts = await alertsResp.json();
                updateAlerts(alerts.alerts);

                document.getElementById('refresh-time').textContent =
                    'Last updated: ' + new Date().toLocaleTimeString();

            } catch (error) {
                console.error('Failed to update metrics:', error);
                document.getElementById('refresh-time').textContent =
                    'Error updating metrics: ' + error.message;
            }
        }

        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            container.innerHTML = '';

            if (alerts.length === 0) {
                const noAlerts = document.createElement('div');
                noAlerts.className = 'alert status-good';
                noAlerts.innerHTML = '✅ All systems operational';
                container.appendChild(noAlerts);
                return;
            }

            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert alert-${alert.severity}`;
                alertDiv.innerHTML = `${getSeverityIcon(alert.severity)} ${alert.message}`;
                container.appendChild(alertDiv);
            });
        }

        function getSeverityIcon(severity) {
            switch(severity) {
                case 'high': return '🔴';
                case 'medium': return '🟡';
                case 'low': return '🟠';
                default: return '📊';
            }
        }

        // Update metrics every 30 seconds
        updateMetrics();
        setInterval(updateMetrics, 30000);
    </script>
</body>
</html>
        """

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False


async def main():
    """Main monitoring function"""
    parser = argparse.ArgumentParser(description="SolanaLM Monitoring System")
    parser.add_argument("--gateway-url", default="http://localhost:8001",
                       help="Gateway URL to monitor")
    parser.add_argument("--port", type=int, default=8300,
                       help="Port for monitoring dashboard")
    parser.add_argument("--host", default="0.0.0.0",
                       help="Host for monitoring dashboard")
    parser.add_argument("--metrics-interval", type=int, default=30,
                       help="Metrics collection interval in seconds")
    parser.add_argument("--log-level", default="INFO",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create monitor
    monitor = SolanaLMMonitor(args.gateway_url, args.metrics_interval)

    # Start monitoring task
    monitoring_task = asyncio.create_task(monitor.start_monitoring())

    try:
        # Start web server
        config = uvicorn.Config(
            monitor.app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower()
        )
        server = uvicorn.Server(config)

        print(f"🚀 SolanaLM Monitor starting...")
        print(f"📊 Dashboard: http://{args.host}:{args.port}")
        print(f"🎯 Monitoring: {args.gateway_url}")
        print(f"⏱️ Interval: {args.metrics_interval} seconds")

        await server.serve()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down monitor...")
    finally:
        monitoring_task.cancel()
        await monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(main())