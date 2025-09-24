"""
Training Coordinator

Manages federated learning rounds, participant selection, and reward distribution.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import uuid
import json

from core.models.schemas import (
    TrainingRound,
    GradientUpdate,
    NodeCapabilities,
    NodeType,
    NetworkStats
)
from core.payments.solana_client import SolanaPaymentClient

logger = logging.getLogger(__name__)


class TrainingCoordinator:
    """Coordinates federated learning across the network"""

    def __init__(self, payment_client: SolanaPaymentClient):
        self.payment_client = payment_client

        # Active training rounds
        self.active_rounds: Dict[str, TrainingRound] = {}
        self.round_participants: Dict[str, Dict[str, NodeCapabilities]] = {}
        self.gradient_updates: Dict[str, List[GradientUpdate]] = {}

        # Configuration
        self.min_participants = 3
        self.max_participants = 20
        self.round_duration_minutes = 15
        self.reward_per_node = 0.1  # SOL

        # Background task
        self._coordinator_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the training coordinator"""
        logger.info("Initializing Training Coordinator")

        # Start background coordination task
        self._coordinator_task = asyncio.create_task(self._coordination_loop())

    async def close(self):
        """Clean up coordinator resources"""
        if self._coordinator_task:
            self._coordinator_task.cancel()
            try:
                await self._coordinator_task
            except asyncio.CancelledError:
                pass

    async def register_training_node(self, node: NodeCapabilities) -> bool:
        """Register a node as available for training"""
        if node.node_type not in [NodeType.TRAINING, NodeType.HYBRID]:
            return False

        # TODO: Validate node hardware requirements
        # TODO: Check reputation score

        logger.info(f"Training node registered: {node.node_id}")
        return True

    async def schedule_training_round(
        self,
        model: str,
        available_nodes: List[NodeCapabilities]
    ) -> Optional[TrainingRound]:
        """Schedule a new federated learning round"""

        # Filter eligible nodes
        eligible_nodes = [
            node for node in available_nodes
            if node.node_type in [NodeType.TRAINING, NodeType.HYBRID]
            and node.status.value == "online"
            and model in node.supported_models
        ]

        if len(eligible_nodes) < self.min_participants:
            logger.warning(f"Not enough nodes for training round: {len(eligible_nodes)} < {self.min_participants}")
            return None

        # Select participants (limit to max_participants)
        participants = self._select_training_participants(eligible_nodes)

        # Create training round
        round_id = str(uuid.uuid4())
        training_round = TrainingRound(
            round_id=round_id,
            model=model,
            participating_nodes=[node.node_id for node in participants],
            start_time=datetime.utcnow(),
            duration_minutes=self.round_duration_minutes,
            reward_per_node=self.reward_per_node,
            status="scheduled"
        )

        # Store round data
        self.active_rounds[round_id] = training_round
        self.round_participants[round_id] = {node.node_id: node for node in participants}
        self.gradient_updates[round_id] = []

        logger.info(f"Scheduled training round {round_id} with {len(participants)} participants")

        # Notify participants
        await self._notify_round_participants(round_id, training_round)

        return training_round

    def _select_training_participants(self, eligible_nodes: List[NodeCapabilities]) -> List[NodeCapabilities]:
        """Select nodes for training based on various criteria"""

        # Sort by reputation score and success rate
        scored_nodes = []
        for node in eligible_nodes:
            score = (
                node.reputation_score * 0.6 +
                node.success_rate * 0.3 +
                min(node.average_response_time, 10) / 10 * 0.1  # Lower latency is better
            )
            scored_nodes.append((score, node))

        # Sort by score (higher is better) and take up to max_participants
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        selected = [node for _, node in scored_nodes[:self.max_participants]]

        return selected

    async def _notify_round_participants(self, round_id: str, training_round: TrainingRound):
        """Notify selected nodes about the training round"""
        participants = self.round_participants.get(round_id, {})

        notification_tasks = []
        for node_id, node in participants.items():
            task = asyncio.create_task(
                self._send_training_notification(node, training_round)
            )
            notification_tasks.append(task)

        # Wait for all notifications (with timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*notification_tasks, return_exceptions=True),
                timeout=30
            )
        except asyncio.TimeoutError:
            logger.warning(f"Training round notification timeout for round {round_id}")

    async def _send_training_notification(self, node: NodeCapabilities, training_round: TrainingRound):
        """Send training round notification to a specific node"""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{node.endpoint_url}/training/join",
                    json={
                        "round_id": training_round.round_id,
                        "model": training_round.model,
                        "start_time": training_round.start_time.isoformat(),
                        "duration_minutes": training_round.duration_minutes,
                        "reward_sol": training_round.reward_per_node
                    },
                    timeout=10
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Notified node {node.node_id} about training round")
                    else:
                        logger.warning(f"Failed to notify node {node.node_id}: {response.status}")

        except Exception as e:
            logger.error(f"Failed to notify training node {node.node_id}: {e}")

    async def submit_gradient_update(
        self,
        round_id: str,
        node_id: str,
        gradient_hash: str,
        gradient_size_bytes: int,
        upload_url: str
    ) -> bool:
        """Process gradient update submission from training node"""

        if round_id not in self.active_rounds:
            logger.warning(f"Gradient update for unknown round: {round_id}")
            return False

        if node_id not in self.round_participants.get(round_id, {}):
            logger.warning(f"Gradient update from non-participant: {node_id}")
            return False

        # Create gradient update record
        update = GradientUpdate(
            node_id=node_id,
            round_id=round_id,
            gradient_hash=gradient_hash,
            gradient_size_bytes=gradient_size_bytes,
            upload_url=upload_url
        )

        self.gradient_updates[round_id].append(update)

        logger.info(f"Received gradient update from {node_id} for round {round_id}")

        # Check if round is complete
        await self._check_round_completion(round_id)

        return True

    async def _check_round_completion(self, round_id: str):
        """Check if a training round is complete and process results"""

        training_round = self.active_rounds.get(round_id)
        if not training_round:
            return

        participants = self.round_participants.get(round_id, {})
        updates = self.gradient_updates.get(round_id, [])

        # Check if we have updates from all participants or time has expired
        expected_updates = len(participants)
        received_updates = len(updates)

        time_expired = (
            datetime.utcnow() - training_round.start_time
        ).total_seconds() > (training_round.duration_minutes * 60)

        if received_updates >= expected_updates or time_expired:
            await self._complete_training_round(round_id)

    async def _complete_training_round(self, round_id: str):
        """Complete a training round and distribute rewards"""

        training_round = self.active_rounds.get(round_id)
        if not training_round or training_round.status == "completed":
            return

        updates = self.gradient_updates.get(round_id, [])
        participants = self.round_participants.get(round_id, {})

        logger.info(f"Completing training round {round_id} with {len(updates)} updates")

        # Mark round as completed
        training_round.status = "completed"

        # Distribute rewards to nodes that submitted updates
        successful_nodes = {update.node_id for update in updates}
        reward_recipients = {}

        for node_id in successful_nodes:
            if node_id in participants:
                node = participants[node_id]
                reward_recipients[node.wallet_address] = training_round.reward_per_node

        if reward_recipients:
            try:
                # Distribute rewards via Solana
                payment_results = await self.payment_client.distribute_training_rewards(
                    reward_recipients, round_id
                )

                logger.info(f"Distributed rewards for round {round_id}: {len(payment_results)} payments")

            except Exception as e:
                logger.error(f"Failed to distribute rewards for round {round_id}: {e}")

        # TODO: Aggregate gradients and update global model
        await self._aggregate_gradients(round_id, updates)

        # Clean up completed round data (after some delay)
        asyncio.create_task(self._cleanup_round_data(round_id, delay=300))  # 5 minutes

    async def _aggregate_gradients(self, round_id: str, updates: List[GradientUpdate]):
        """Aggregate gradients from training round (placeholder implementation)"""

        logger.info(f"Aggregating {len(updates)} gradient updates for round {round_id}")

        # TODO: Implement actual gradient aggregation
        # 1. Download gradients from IPFS/Arweave URLs
        # 2. Verify gradient hashes
        # 3. Perform federated averaging
        # 4. Update global model
        # 5. Upload new model version

        # For now, just log the aggregation
        total_size = sum(update.gradient_size_bytes for update in updates)
        logger.info(f"Round {round_id} aggregation complete. Total gradient size: {total_size} bytes")

    async def _cleanup_round_data(self, round_id: str, delay: int = 0):
        """Clean up data from completed training round"""

        if delay > 0:
            await asyncio.sleep(delay)

        # Remove from active tracking
        self.active_rounds.pop(round_id, None)
        self.round_participants.pop(round_id, None)
        self.gradient_updates.pop(round_id, None)

        logger.debug(f"Cleaned up data for training round {round_id}")

    async def get_training_status(self) -> Dict[str, any]:
        """Get current training status"""

        active_rounds = len(self.active_rounds)
        total_participants = sum(
            len(participants) for participants in self.round_participants.values()
        )

        # Find next scheduled round
        next_round_start = None
        for round_data in self.active_rounds.values():
            if round_data.status == "scheduled":
                if next_round_start is None or round_data.start_time < next_round_start:
                    next_round_start = round_data.start_time

        return {
            "active_rounds": active_rounds,
            "participating_nodes": total_participants,
            "next_round_start": next_round_start.isoformat() if next_round_start else None,
            "completed_rounds_24h": 0,  # TODO: Track historical data
            "total_rewards_distributed": 0.0  # TODO: Track total rewards
        }

    async def _coordination_loop(self):
        """Background task for training coordination"""

        while True:
            try:
                # Check for expired rounds
                await self._check_expired_rounds()

                # TODO: Auto-schedule new rounds based on node availability
                # await self._auto_schedule_rounds()

                # Sleep for coordination interval
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Training coordination loop error: {e}")
                await asyncio.sleep(60)

    async def _check_expired_rounds(self):
        """Check for and complete expired training rounds"""

        current_time = datetime.utcnow()
        expired_rounds = []

        for round_id, training_round in self.active_rounds.items():
            if training_round.status != "completed":
                round_end_time = (
                    training_round.start_time +
                    timedelta(minutes=training_round.duration_minutes)
                )

                if current_time > round_end_time:
                    expired_rounds.append(round_id)

        # Complete expired rounds
        for round_id in expired_rounds:
            logger.info(f"Training round {round_id} expired, completing...")
            await self._complete_training_round(round_id)