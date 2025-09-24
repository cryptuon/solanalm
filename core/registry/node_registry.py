"""
Node Registry System

Manages node registration, discovery, and load balancing for the SolanaLM network.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import aiohttp
import json

from core.models.schemas import (
    NodeCapabilities,
    NodeType,
    NodeStatus,
    NetworkStats,
    InferenceRequest
)

logger = logging.getLogger(__name__)


class NodeRegistry:
    """Registry for managing network nodes"""

    def __init__(self):
        self.nodes: Dict[str, NodeCapabilities] = {}
        self.node_metrics: Dict[str, Dict[str, Any]] = {}
        self.last_health_check = datetime.utcnow()
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the registry and start background tasks"""
        logger.info("Initializing Node Registry")

        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def close(self):
        """Clean up registry resources"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

    async def register_node(self, capabilities: NodeCapabilities) -> str:
        """Register a new node in the network"""
        node_id = capabilities.node_id

        # Validate node endpoint
        if not await self._validate_node_endpoint(capabilities.endpoint_url):
            raise ValueError(f"Node endpoint {capabilities.endpoint_url} is not accessible")

        # Initialize metrics
        self.node_metrics[node_id] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "last_request_time": None,
            "health_checks_passed": 0,
            "health_checks_failed": 0
        }

        # Store node
        self.nodes[node_id] = capabilities

        logger.info(f"Registered new {capabilities.node_type} node: {node_id}")
        return node_id

    async def unregister_node(self, node_id: str):
        """Remove a node from the registry"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            if node_id in self.node_metrics:
                del self.node_metrics[node_id]
            logger.info(f"Unregistered node: {node_id}")

    async def find_best_node(
        self,
        model: str,
        node_type: Optional[NodeType] = None
    ) -> Optional['NetworkNode']:
        """Find the best available node for a request"""

        # Filter nodes by criteria
        candidates = []
        for node_id, node in self.nodes.items():
            if node.status != NodeStatus.ONLINE:
                continue

            if model not in node.supported_models:
                continue

            if node_type and node.node_type != node_type:
                # Allow hybrid nodes to serve any type
                if node.node_type != NodeType.HYBRID:
                    continue

            candidates.append((node_id, node))

        if not candidates:
            return None

        # Score nodes based on performance and load
        scored_nodes = []
        for node_id, node in candidates:
            metrics = self.node_metrics.get(node_id, {})

            # Calculate score based on multiple factors
            score = self._calculate_node_score(node, metrics)
            scored_nodes.append((score, node_id, node))

        # Sort by score (higher is better)
        scored_nodes.sort(key=lambda x: x[0], reverse=True)

        best_node_id, best_node = scored_nodes[0][1], scored_nodes[0][2]
        return NetworkNode(best_node, self)

    def _calculate_node_score(self, node: NodeCapabilities, metrics: Dict[str, Any]) -> float:
        """Calculate a score for node selection"""
        score = 0.0

        # Base score from reputation
        score += node.reputation_score * 50

        # Penalty for high response time
        avg_response_time = metrics.get("total_response_time", 0) / max(metrics.get("total_requests", 1), 1)
        if avg_response_time > 0:
            score -= min(avg_response_time * 10, 30)

        # Bonus for successful requests
        total_requests = metrics.get("total_requests", 0)
        if total_requests > 0:
            success_rate = metrics.get("successful_requests", 0) / total_requests
            score += success_rate * 20

        # Penalty for being busy (TODO: track concurrent requests)
        # score -= current_load_factor * 10

        return score

    async def update_node_metrics(
        self,
        node_id: str,
        request_count: int = 0,
        success: bool = True,
        latency: Optional[float] = None
    ):
        """Update node performance metrics"""
        if node_id not in self.node_metrics:
            return

        metrics = self.node_metrics[node_id]

        metrics["total_requests"] += request_count
        if success:
            metrics["successful_requests"] += request_count
        else:
            metrics["failed_requests"] += request_count

        if latency is not None:
            metrics["total_response_time"] += latency
            metrics["last_request_time"] = datetime.utcnow()

        # Update node reputation
        if node_id in self.nodes:
            node = self.nodes[node_id]
            if metrics["total_requests"] > 0:
                node.success_rate = metrics["successful_requests"] / metrics["total_requests"]
                node.average_response_time = metrics["total_response_time"] / metrics["total_requests"]

    async def get_all_nodes(self) -> List[NodeCapabilities]:
        """Get all registered nodes"""
        return list(self.nodes.values())

    async def get_network_stats(self) -> NetworkStats:
        """Calculate network-wide statistics"""
        total_nodes = len(self.nodes)
        active_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.ONLINE])

        # Count by type
        inference_nodes = len([n for n in self.nodes.values() if n.node_type == NodeType.INFERENCE])
        training_nodes = len([n for n in self.nodes.values() if n.node_type == NodeType.TRAINING])
        hybrid_nodes = len([n for n in self.nodes.values() if n.node_type == NodeType.HYBRID])
        proxy_nodes = len([n for n in self.nodes.values() if n.node_type == NodeType.PROXY])

        # Calculate aggregate metrics
        total_requests_24h = sum(
            metrics.get("total_requests", 0)
            for metrics in self.node_metrics.values()
        )

        all_models = set()
        total_response_time = 0.0
        total_requests = 0

        for node in self.nodes.values():
            all_models.update(node.supported_models)
            total_response_time += node.average_response_time * node.total_requests_served
            total_requests += node.total_requests_served

        average_response_time = total_response_time / max(total_requests, 1)

        return NetworkStats(
            total_nodes=total_nodes,
            active_nodes=active_nodes,
            inference_nodes=inference_nodes,
            training_nodes=training_nodes,
            hybrid_nodes=hybrid_nodes,
            proxy_nodes=proxy_nodes,
            total_requests_24h=total_requests_24h,
            active_training_rounds=0,  # TODO: Integrate with training coordinator
            total_models_available=len(all_models),
            average_response_time=average_response_time,
            network_uptime=1.0  # TODO: Calculate actual uptime
        )

    async def _validate_node_endpoint(self, endpoint: str) -> bool:
        """Validate that a node endpoint is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{endpoint}/health", timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Node endpoint validation failed for {endpoint}: {e}")
            return False

    async def _health_check_loop(self):
        """Background task to check node health"""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _perform_health_checks(self):
        """Check health of all registered nodes"""
        if not self.nodes:
            return

        logger.debug("Performing health checks on registered nodes")

        tasks = []
        for node_id, node in self.nodes.items():
            task = asyncio.create_task(self._check_node_health(node_id, node))
            tasks.append(task)

        # Wait for all health checks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        self.last_health_check = datetime.utcnow()

    async def _check_node_health(self, node_id: str, node: NodeCapabilities):
        """Check health of a specific node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{node.endpoint_url}/health", timeout=10) as response:
                    if response.status == 200:
                        node.status = NodeStatus.ONLINE
                        node.last_seen = datetime.utcnow()
                        self.node_metrics[node_id]["health_checks_passed"] += 1
                    else:
                        node.status = NodeStatus.OFFLINE
                        self.node_metrics[node_id]["health_checks_failed"] += 1

        except Exception as e:
            logger.warning(f"Health check failed for node {node_id}: {e}")
            node.status = NodeStatus.OFFLINE
            self.node_metrics[node_id]["health_checks_failed"] += 1


class NetworkNode:
    """Wrapper for interacting with a specific network node"""

    def __init__(self, capabilities: NodeCapabilities, registry: NodeRegistry):
        self.capabilities = capabilities
        self.registry = registry

    @property
    def node_id(self) -> str:
        return self.capabilities.node_id

    @property
    def wallet_address(self) -> str:
        return self.capabilities.wallet_address

    @property
    def pricing(self):
        return self.capabilities.pricing

    async def process_inference(self, request: InferenceRequest) -> Any:
        """Forward inference request to this node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.capabilities.endpoint_url}/inference",
                    json=request.dict(),
                    timeout=60
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"Node returned status {response.status}")

        except Exception as e:
            logger.error(f"Failed to process inference on node {self.node_id}: {e}")
            raise