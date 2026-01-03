"""
Node Repository

Database operations for node registry and metrics.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.repositories.base import BaseRepository
from core.database.models.node import NodeModel, NodeMetricsModel


class NodeRepository(BaseRepository[NodeModel]):
    """Repository for node operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, NodeModel)

    async def get_by_node_id(self, node_id: str) -> Optional[NodeModel]:
        """Get node by node_id"""
        result = await self.session.execute(
            select(NodeModel).where(NodeModel.node_id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_by_wallet(self, wallet_address: str) -> Optional[NodeModel]:
        """Get node by wallet address"""
        result = await self.session.execute(
            select(NodeModel).where(NodeModel.wallet_address == wallet_address)
        )
        return result.scalar_one_or_none()

    async def find_nodes_by_type(
        self,
        node_type: str,
        status: str = "online"
    ) -> List[NodeModel]:
        """Find nodes by type and status"""
        result = await self.session.execute(
            select(NodeModel).where(
                and_(
                    NodeModel.node_type == node_type,
                    NodeModel.status == status
                )
            ).order_by(NodeModel.reputation_score.desc())
        )
        return list(result.scalars().all())

    async def find_nodes_supporting_model(
        self,
        model: str,
        status: str = "online"
    ) -> List[NodeModel]:
        """Find nodes that support a specific model"""
        result = await self.session.execute(
            select(NodeModel).where(
                and_(
                    NodeModel.status == status,
                    NodeModel.supported_models.contains([model])
                )
            ).order_by(NodeModel.reputation_score.desc())
        )
        return list(result.scalars().all())

    async def find_best_node(
        self,
        model: str,
        node_type: str = "inference"
    ) -> Optional[NodeModel]:
        """Find best available node for a model"""
        result = await self.session.execute(
            select(NodeModel).where(
                and_(
                    NodeModel.status == "online",
                    NodeModel.node_type == node_type,
                    NodeModel.supported_models.contains([model])
                )
            ).order_by(
                NodeModel.reputation_score.desc(),
                NodeModel.average_response_time.asc()
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_online_nodes(self) -> List[NodeModel]:
        """Get all online nodes"""
        result = await self.session.execute(
            select(NodeModel).where(NodeModel.status == "online")
        )
        return list(result.scalars().all())

    async def update_node_status(self, node_id: str, status: str) -> bool:
        """Update node status"""
        node = await self.get_by_node_id(node_id)
        if node:
            node.status = status
            node.last_seen = datetime.utcnow()
            await self.session.flush()
            return True
        return False

    async def update_node_metrics(
        self,
        node_id: str,
        request_count: int = 0,
        success: bool = True,
        latency: Optional[float] = None
    ) -> None:
        """Update node metrics after request"""
        # Get or create metrics
        result = await self.session.execute(
            select(NodeMetricsModel).where(NodeMetricsModel.node_id == node_id)
        )
        metrics = result.scalar_one_or_none()

        if not metrics:
            metrics = NodeMetricsModel(node_id=node_id)
            self.session.add(metrics)

        metrics.total_requests += request_count
        if success:
            metrics.successful_requests += request_count
        else:
            metrics.failed_requests += request_count

        if latency is not None:
            metrics.total_response_time += latency

        metrics.last_request_time = datetime.utcnow()
        await self.session.flush()

        # Update node's aggregated metrics
        node = await self.get_by_node_id(node_id)
        if node:
            node.total_requests_served = metrics.total_requests
            node.success_rate = metrics.success_rate
            node.average_response_time = metrics.average_response_time
            node.last_seen = datetime.utcnow()
            await self.session.flush()

    async def record_health_check(
        self,
        node_id: str,
        passed: bool
    ) -> None:
        """Record health check result"""
        result = await self.session.execute(
            select(NodeMetricsModel).where(NodeMetricsModel.node_id == node_id)
        )
        metrics = result.scalar_one_or_none()

        if not metrics:
            metrics = NodeMetricsModel(node_id=node_id)
            self.session.add(metrics)

        if passed:
            metrics.health_checks_passed += 1
        else:
            metrics.health_checks_failed += 1

        metrics.last_heartbeat = datetime.utcnow()
        await self.session.flush()

    async def get_network_stats(self) -> dict:
        """Get overall network statistics"""
        all_nodes = await self.get_all(limit=1000)
        online_nodes = [n for n in all_nodes if n.status == "online"]

        return {
            "total_nodes": len(all_nodes),
            "online_nodes": len(online_nodes),
            "nodes_by_type": self._count_by_type(all_nodes),
            "total_requests_served": sum(n.total_requests_served for n in all_nodes),
            "average_success_rate": self._average_success_rate(online_nodes)
        }

    def _count_by_type(self, nodes: List[NodeModel]) -> dict:
        """Count nodes by type"""
        counts = {}
        for node in nodes:
            counts[node.node_type] = counts.get(node.node_type, 0) + 1
        return counts

    def _average_success_rate(self, nodes: List[NodeModel]) -> float:
        """Calculate average success rate"""
        if not nodes:
            return 1.0
        return sum(n.success_rate for n in nodes) / len(nodes)
