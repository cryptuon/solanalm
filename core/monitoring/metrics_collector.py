"""
Comprehensive Metrics Collection and Monitoring System
Tracks network performance, node health, and business metrics
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""


@dataclass
class NetworkMetrics:
    """Network-wide performance metrics"""
    total_nodes: int = 0
    active_nodes: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_tokens_generated: int = 0
    total_revenue_sol: float = 0.0
    federated_rounds_completed: int = 0
    active_training_nodes: int = 0


@dataclass
class NodeMetrics:
    """Individual node performance metrics"""
    node_id: str
    node_type: str
    status: str
    uptime: float = 0.0
    requests_served: int = 0
    errors: int = 0
    average_response_time: float = 0.0
    tokens_generated: int = 0
    revenue_earned: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    gpu_usage: float = 0.0
    last_heartbeat: Optional[datetime] = None


class MetricsCollector:
    """Centralized metrics collection and aggregation"""

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.network_metrics = NetworkMetrics()
        self.node_metrics: Dict[str, NodeMetrics] = {}

        # Real-time tracking
        self.request_times: deque = deque(maxlen=100)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.revenue_tracker: deque = deque(maxlen=1000)

        # Background tasks
        self._collection_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start metrics collection"""
        logger.info("Starting metrics collection system")
        self._collection_task = asyncio.create_task(self._collection_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop metrics collection"""
        if self._collection_task:
            self._collection_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()

    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
                     labels: Dict[str, str] = None, description: str = ""):
        """Record a metric with timestamp"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels or {},
            description=description
        )
        self.metrics[name].append(metric)

    def record_request(self, node_id: str, response_time: float, success: bool, tokens: int = 0, cost: float = 0.0):
        """Record an inference request"""
        self.request_times.append(response_time)

        if success:
            self.network_metrics.successful_requests += 1
            if cost > 0:
                self.revenue_tracker.append((datetime.utcnow(), cost))
                self.network_metrics.total_revenue_sol += cost
        else:
            self.network_metrics.failed_requests += 1
            self.error_counts[node_id] += 1

        self.network_metrics.total_requests += 1
        self.network_metrics.total_tokens_generated += tokens

        # Update node metrics
        if node_id in self.node_metrics:
            node = self.node_metrics[node_id]
            node.requests_served += 1
            node.tokens_generated += tokens
            node.revenue_earned += cost
            if not success:
                node.errors += 1

        # Record individual metrics
        self.record_metric(f"request_time", response_time, MetricType.HISTOGRAM, {"node_id": node_id})
        self.record_metric(f"request_success", 1 if success else 0, MetricType.COUNTER, {"node_id": node_id})

    def record_federated_round(self, round_id: str, participants: int, avg_loss: float, duration: float):
        """Record federated learning round metrics"""
        self.network_metrics.federated_rounds_completed += 1

        self.record_metric("fl_round_participants", participants, MetricType.GAUGE, {"round_id": round_id})
        self.record_metric("fl_round_loss", avg_loss, MetricType.GAUGE, {"round_id": round_id})
        self.record_metric("fl_round_duration", duration, MetricType.TIMER, {"round_id": round_id})

    def register_node(self, node_id: str, node_type: str, capabilities: Dict[str, Any]):
        """Register a new node"""
        self.node_metrics[node_id] = NodeMetrics(
            node_id=node_id,
            node_type=node_type,
            status="active",
            last_heartbeat=datetime.utcnow()
        )
        self._update_node_counts()

    def update_node_heartbeat(self, node_id: str, system_metrics: Dict[str, float] = None):
        """Update node heartbeat and system metrics"""
        if node_id in self.node_metrics:
            node = self.node_metrics[node_id]
            node.last_heartbeat = datetime.utcnow()
            node.status = "active"

            if system_metrics:
                node.cpu_usage = system_metrics.get("cpu_usage", 0.0)
                node.memory_usage = system_metrics.get("memory_usage", 0.0)
                node.gpu_usage = system_metrics.get("gpu_usage", 0.0)

    def get_network_summary(self) -> Dict[str, Any]:
        """Get network-wide metrics summary"""
        # Calculate average response time
        if self.request_times:
            self.network_metrics.average_response_time = sum(self.request_times) / len(self.request_times)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "network": {
                "total_nodes": self.network_metrics.total_nodes,
                "active_nodes": self.network_metrics.active_nodes,
                "total_requests": self.network_metrics.total_requests,
                "success_rate": self._calculate_success_rate(),
                "average_response_time": self.network_metrics.average_response_time,
                "requests_per_minute": self._calculate_requests_per_minute(),
                "total_tokens_generated": self.network_metrics.total_tokens_generated,
                "total_revenue_sol": self.network_metrics.total_revenue_sol,
                "federated_rounds": self.network_metrics.federated_rounds_completed,
            },
            "top_performers": self._get_top_performing_nodes(),
            "error_summary": dict(self.error_counts),
            "recent_revenue": self._calculate_recent_revenue()
        }

    def get_node_summary(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get individual node metrics"""
        if node_id not in self.node_metrics:
            return None

        node = self.node_metrics[node_id]
        return {
            "node_id": node.node_id,
            "type": node.node_type,
            "status": self._get_node_status(node),
            "uptime": (datetime.utcnow() - (node.last_heartbeat or datetime.utcnow())).total_seconds(),
            "performance": {
                "requests_served": node.requests_served,
                "error_rate": node.errors / max(node.requests_served, 1),
                "tokens_generated": node.tokens_generated,
                "revenue_earned": node.revenue_earned,
            },
            "system": {
                "cpu_usage": node.cpu_usage,
                "memory_usage": node.memory_usage,
                "gpu_usage": node.gpu_usage,
            },
            "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None
        }

    def get_metrics_export(self, format: str = "prometheus") -> str:
        """Export metrics in various formats"""
        if format == "prometheus":
            return self._export_prometheus()
        elif format == "json":
            return json.dumps(self.get_network_summary(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        # Network metrics
        lines.append(f"# HELP solanalm_total_requests Total inference requests")
        lines.append(f"# TYPE solanalm_total_requests counter")
        lines.append(f"solanalm_total_requests {self.network_metrics.total_requests}")

        lines.append(f"# HELP solanalm_active_nodes Number of active nodes")
        lines.append(f"# TYPE solanalm_active_nodes gauge")
        lines.append(f"solanalm_active_nodes {self.network_metrics.active_nodes}")

        lines.append(f"# HELP solanalm_success_rate Request success rate")
        lines.append(f"# TYPE solanalm_success_rate gauge")
        lines.append(f"solanalm_success_rate {self._calculate_success_rate()}")

        # Per-node metrics
        for node_id, node in self.node_metrics.items():
            lines.append(f"solanalm_node_requests{{node_id=\"{node_id}\"}} {node.requests_served}")
            lines.append(f"solanalm_node_errors{{node_id=\"{node_id}\"}} {node.errors}")
            lines.append(f"solanalm_node_revenue{{node_id=\"{node_id}\"}} {node.revenue_earned}")

        return "\n".join(lines)

    def _update_node_counts(self):
        """Update active node counts"""
        active_nodes = 0
        training_nodes = 0

        for node in self.node_metrics.values():
            if self._get_node_status(node) == "active":
                active_nodes += 1
                if node.node_type in ["training", "hybrid"]:
                    training_nodes += 1

        self.network_metrics.total_nodes = len(self.node_metrics)
        self.network_metrics.active_nodes = active_nodes
        self.network_metrics.active_training_nodes = training_nodes

    def _get_node_status(self, node: NodeMetrics) -> str:
        """Determine node status based on last heartbeat"""
        if not node.last_heartbeat:
            return "unknown"

        time_since_heartbeat = datetime.utcnow() - node.last_heartbeat
        if time_since_heartbeat > timedelta(minutes=5):
            return "inactive"
        elif time_since_heartbeat > timedelta(minutes=2):
            return "degraded"
        else:
            return "active"

    def _calculate_success_rate(self) -> float:
        """Calculate request success rate"""
        total = self.network_metrics.total_requests
        if total == 0:
            return 1.0
        return self.network_metrics.successful_requests / total

    def _calculate_requests_per_minute(self) -> float:
        """Calculate requests per minute over last hour"""
        recent_requests = [m for m in self.metrics.get("request_success", [])
                          if datetime.utcnow() - m.timestamp < timedelta(hours=1)]
        return len(recent_requests) / 60.0

    def _calculate_recent_revenue(self) -> float:
        """Calculate revenue in last 24 hours"""
        cutoff = datetime.utcnow() - timedelta(days=1)
        recent_revenue = sum(cost for timestamp, cost in self.revenue_tracker if timestamp > cutoff)
        return recent_revenue

    def _get_top_performing_nodes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing nodes by requests served"""
        sorted_nodes = sorted(
            self.node_metrics.values(),
            key=lambda n: n.requests_served,
            reverse=True
        )

        return [
            {
                "node_id": node.node_id,
                "requests_served": node.requests_served,
                "revenue_earned": node.revenue_earned,
                "error_rate": node.errors / max(node.requests_served, 1)
            }
            for node in sorted_nodes[:limit]
        ]

    async def _collection_loop(self):
        """Background metrics collection"""
        while True:
            try:
                self._update_node_counts()
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """Clean up old metrics data"""
        while True:
            try:
                # Remove old metrics (older than 24 hours)
                cutoff = datetime.utcnow() - timedelta(days=1)

                for metric_name, metric_list in self.metrics.items():
                    # Remove old metrics
                    while metric_list and metric_list[0].timestamp < cutoff:
                        metric_list.popleft()

                # Clean up old revenue data
                self.revenue_tracker = deque([
                    (ts, cost) for ts, cost in self.revenue_tracker
                    if ts > cutoff
                ], maxlen=1000)

                await asyncio.sleep(3600)  # Clean up every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(3600)


# Global metrics collector instance
metrics_collector = MetricsCollector()


async def start_metrics_collection():
    """Start the global metrics collector"""
    await metrics_collector.start()


async def stop_metrics_collection():
    """Stop the global metrics collector"""
    await metrics_collector.stop()