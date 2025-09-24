#!/usr/bin/env python3
"""
Federated Learning Coordinator

Orchestrates federated learning across the SolanaLM network:
- Manages training rounds and node recruitment
- Coordinates model aggregation and distribution
- Handles training incentives and payments
- Ensures privacy-preserving collaborative learning
"""

import asyncio
import logging
import time
import secrets
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json

from core.models.schemas import NodeCapabilities, TrainingUpdate
from core.training.model_aggregation import ModelAggregator

logger = logging.getLogger(__name__)


@dataclass
class TrainingRound:
    """Represents a federated training round"""
    round_id: str
    model_name: str
    round_number: int
    status: str  # recruiting, active, aggregating, completed, failed

    # Configuration
    target_participants: int
    max_participants: int
    min_participants: int = 3
    learning_rate: float = 0.001
    batch_size: int = 32
    local_epochs: int = 3

    # Incentives
    reward_per_update: float = 0.01
    quality_bonus_pool: float = 0.0

    # Participants
    participating_nodes: List[str] = field(default_factory=list)
    submitted_updates: Dict[str, TrainingUpdate] = field(default_factory=dict)

    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    timeout_at: Optional[float] = None

    # Results
    global_model_hash: Optional[str] = None
    aggregation_metrics: Dict[str, Any] = field(default_factory=dict)


class FederatedLearningCoordinator:
    """Coordinates federated learning across the network"""

    def __init__(self, node_registry, payment_client):
        self.node_registry = node_registry
        self.payment_client = payment_client
        self.model_aggregator = ModelAggregator()

        # Active training rounds
        self.active_rounds: Dict[str, TrainingRound] = {}

        # Configuration
        self.min_reputation_threshold = 0.8
        self.max_concurrent_rounds = 5
        self.default_round_timeout = 3600  # 1 hour

    async def create_training_round(self, config: Dict[str, Any]) -> TrainingRound:
        """Create a new federated training round"""

        if len(self.active_rounds) >= self.max_concurrent_rounds:
            raise Exception(f"Maximum concurrent rounds ({self.max_concurrent_rounds}) reached")

        round_id = f"round-{secrets.token_hex(8)}"

        training_round = TrainingRound(
            round_id=round_id,
            model_name=config["model_name"],
            round_number=config.get("round_number", 1),
            status="recruiting",
            target_participants=config["target_participants"],
            max_participants=config.get("max_participants", config["target_participants"] * 2),
            min_participants=config.get("min_participants", max(3, config["target_participants"] // 2)),
            learning_rate=config.get("learning_rate", 0.001),
            batch_size=config.get("batch_size", 32),
            local_epochs=config.get("local_epochs", 3),
            reward_per_update=config.get("reward_per_update", 0.01),
            quality_bonus_pool=config.get("quality_bonus_pool", 0.0),
            timeout_at=time.time() + config.get("timeout_seconds", self.default_round_timeout)
        )

        self.active_rounds[round_id] = training_round

        logger.info(f"Created training round {round_id} for model {config['model_name']}")
        logger.debug(f"Round config: {config}")

        return training_round

    async def recruit_nodes(self, round_id: str) -> List[str]:
        """Recruit nodes for a training round"""

        if round_id not in self.active_rounds:
            raise ValueError(f"Training round {round_id} not found")

        training_round = self.active_rounds[round_id]

        if training_round.status != "recruiting":
            raise ValueError(f"Round {round_id} is not in recruiting status")

        # Get available training nodes
        available_nodes = await self.node_registry.get_training_nodes()

        # Filter eligible nodes
        eligible_nodes = self._filter_eligible_nodes(
            available_nodes,
            training_round.model_name,
            min_reputation=self.min_reputation_threshold
        )

        if len(eligible_nodes) < training_round.min_participants:
            raise Exception(f"Insufficient eligible nodes: {len(eligible_nodes)} < {training_round.min_participants}")

        # Select nodes for training
        selected_nodes = self._select_training_nodes(
            eligible_nodes,
            training_round.target_participants,
            training_round.max_participants,
            strategy="geographic_diversity"
        )

        # Register nodes for the round
        for node in selected_nodes:
            training_round.participating_nodes.append(node.node_id)

            # Notify node about training round
            await self._notify_node_training_start(node, training_round)

        logger.info(f"Recruited {len(selected_nodes)} nodes for round {round_id}")

        return [node.node_id for node in selected_nodes]

    def _filter_eligible_nodes(
        self,
        nodes: List[NodeCapabilities],
        model_name: str,
        min_reputation: float
    ) -> List[NodeCapabilities]:
        """Filter nodes eligible for training"""

        eligible = []

        for node in nodes:
            # Check node type
            if node.node_type != "training":
                continue

            # Check model support
            if model_name not in node.supported_models:
                continue

            # Check reputation
            if node.reputation_score < min_reputation:
                continue

            # Check training capabilities
            if not hasattr(node, 'training_capabilities') or not node.training_capabilities:
                continue

            eligible.append(node)

        return eligible

    def _select_training_nodes(
        self,
        eligible_nodes: List[NodeCapabilities],
        target_count: int,
        max_count: int,
        strategy: str = "reputation"
    ) -> List[NodeCapabilities]:
        """Select nodes for training based on strategy"""

        if strategy == "reputation":
            # Sort by reputation and take top nodes
            sorted_nodes = sorted(eligible_nodes, key=lambda n: n.reputation_score, reverse=True)
            return sorted_nodes[:min(target_count, len(sorted_nodes))]

        elif strategy == "geographic_diversity":
            # Prefer geographic diversity
            selected = []
            used_locations = set()

            # First pass: one node per location
            for node in sorted(eligible_nodes, key=lambda n: n.reputation_score, reverse=True):
                if len(selected) >= target_count:
                    break

                if node.geographical_location not in used_locations:
                    selected.append(node)
                    used_locations.add(node.geographical_location)

            # Second pass: fill remaining slots with best reputation
            remaining_nodes = [n for n in eligible_nodes if n not in selected]
            remaining_nodes.sort(key=lambda n: n.reputation_score, reverse=True)

            while len(selected) < target_count and remaining_nodes:
                selected.append(remaining_nodes.pop(0))

            return selected[:min(max_count, len(selected))]

        elif strategy == "random":
            # Random selection for fairness
            import random
            return random.sample(eligible_nodes, min(target_count, len(eligible_nodes)))

        else:
            raise ValueError(f"Unknown selection strategy: {strategy}")

    async def execute_training_round(self, round_id: str) -> Dict[str, Any]:
        """Execute a complete training round"""

        if round_id not in self.active_rounds:
            raise ValueError(f"Training round {round_id} not found")

        training_round = self.active_rounds[round_id]

        try:
            # Update status
            training_round.status = "active"
            training_round.started_at = time.time()

            logger.info(f"Starting training round {round_id} with {len(training_round.participating_nodes)} nodes")

            # Collect training updates from nodes
            updates = await self._collect_training_updates(training_round)

            if len(updates) < training_round.min_participants:
                raise Exception(f"Insufficient updates: {len(updates)} < {training_round.min_participants}")

            # Update status for aggregation
            training_round.status = "aggregating"

            # Aggregate model updates
            aggregated_model = await self._aggregate_model_updates(updates, training_round)

            # Calculate and distribute rewards
            rewards = self.calculate_training_rewards(
                updates,
                training_round.reward_per_update,
                quality_bonus=training_round.quality_bonus_pool > 0
            )

            payment_results = await self.distribute_training_rewards(rewards, round_id)

            # Update node reputations
            await self._update_node_reputations(updates)

            # Complete the round
            training_round.status = "completed"
            training_round.completed_at = time.time()
            training_round.global_model_hash = self._hash_model(aggregated_model)

            # Store aggregation metrics
            training_round.aggregation_metrics = {
                "participants": len(updates),
                "average_loss": sum(u.training_metrics.get("loss", 0) for u in updates) / len(updates),
                "total_samples": sum(u.training_metrics.get("samples_trained", 0) for u in updates),
                "aggregation_time": time.time() - training_round.started_at
            }

            logger.info(f"Completed training round {round_id}")

            return {
                "status": "completed",
                "round_id": round_id,
                "participants": len(updates),
                "aggregated_model": aggregated_model,
                "global_model_hash": training_round.global_model_hash,
                "rewards_distributed": payment_results,
                "metrics": training_round.aggregation_metrics
            }

        except Exception as e:
            logger.error(f"Training round {round_id} failed: {e}")
            training_round.status = "failed"
            training_round.completed_at = time.time()
            raise

    async def _collect_training_updates(self, training_round: TrainingRound) -> List[TrainingUpdate]:
        """Collect training updates from participating nodes"""

        logger.info(f"Collecting updates from {len(training_round.participating_nodes)} nodes")

        # In production, this would communicate with actual nodes
        # For now, simulate the collection process

        collected_updates = []

        for node_id in training_round.participating_nodes:
            try:
                # Simulate update collection with timeout
                await asyncio.sleep(0.1)  # Simulate network delay

                # Mock training update (in production, would receive from node)
                update = self._create_mock_training_update(node_id, training_round.round_id)
                collected_updates.append(update)

                logger.debug(f"Collected update from {node_id}")

            except Exception as e:
                logger.warning(f"Failed to collect update from {node_id}: {e}")
                continue

        return collected_updates

    def _create_mock_training_update(self, node_id: str, round_id: str) -> TrainingUpdate:
        """Create mock training update for testing"""

        # Generate realistic mock weights
        import random
        random.seed(hash(node_id + round_id) % 2**32)  # Deterministic but varied

        mock_weights = {
            "layer1.weight": [[random.gauss(0, 0.1) for _ in range(10)] for _ in range(8)],
            "layer1.bias": [random.gauss(0, 0.01) for _ in range(8)],
            "layer2.weight": [[random.gauss(0, 0.1) for _ in range(8)] for _ in range(4)],
            "layer2.bias": [random.gauss(0, 0.01) for _ in range(4)]
        }

        # Generate realistic metrics
        base_loss = 2.5
        loss_variance = random.gauss(0, 0.2)

        return TrainingUpdate(
            node_id=node_id,
            round_id=round_id,
            model_weights=mock_weights,
            training_metrics={
                "loss": max(0.1, base_loss + loss_variance),
                "accuracy": min(0.95, max(0.5, 0.75 + random.gauss(0, 0.05))),
                "samples_trained": random.randint(500, 2000),
                "training_time": random.randint(180, 600),
                "epochs_completed": random.randint(2, 5)
            },
            update_size_mb=random.uniform(8.0, 25.0),
            compression_method="quantization"
        )

    async def _aggregate_model_updates(
        self,
        updates: List[TrainingUpdate],
        training_round: TrainingRound
    ) -> Dict[str, Any]:
        """Aggregate model updates using federated learning algorithms"""

        logger.info(f"Aggregating {len(updates)} model updates")

        # Validate updates
        if not self.model_aggregator.validate_updates(updates):
            raise ValueError("Model updates failed validation")

        # Perform federated averaging
        aggregated_weights = self.model_aggregator.aggregate(
            updates,
            weighting_strategy="samples",  # Weight by number of training samples
            exclude_byzantine=True  # Remove outlier updates
        )

        # Create aggregated model
        aggregated_model = {
            "model_name": training_round.model_name,
            "round_number": training_round.round_number,
            "weights": aggregated_weights,
            "metadata": {
                "participants": len(updates),
                "aggregation_method": "federated_averaging",
                "total_samples": sum(u.training_metrics.get("samples_trained", 0) for u in updates),
                "average_loss": sum(u.training_metrics.get("loss", 0) for u in updates) / len(updates),
                "timestamp": time.time()
            }
        }

        return aggregated_model

    def calculate_training_rewards(
        self,
        updates: List[TrainingUpdate],
        base_reward: float,
        quality_bonus: bool = True
    ) -> Dict[str, float]:
        """Calculate rewards for training participants"""

        rewards = {}

        if not updates:
            return rewards

        # Base rewards for participation
        for update in updates:
            rewards[update.node_id] = base_reward

        if quality_bonus:
            # Quality bonuses based on performance metrics
            losses = [u.training_metrics.get("loss", float('inf')) for u in updates]
            best_loss = min(losses)

            for update in updates:
                node_loss = update.training_metrics.get("loss", float('inf'))
                samples = update.training_metrics.get("samples_trained", 1)

                # Bonus for good performance
                if node_loss <= best_loss * 1.1:  # Within 10% of best
                    performance_bonus = base_reward * 0.5
                    rewards[update.node_id] += performance_bonus

                # Bonus for training more samples
                sample_bonus = min(base_reward * 0.3, samples / 1000 * base_reward * 0.1)
                rewards[update.node_id] += sample_bonus

        return rewards

    async def distribute_training_rewards(
        self,
        rewards: Dict[str, float],
        round_id: str
    ) -> List[Dict[str, Any]]:
        """Distribute SOL rewards to training participants"""

        logger.info(f"Distributing rewards to {len(rewards)} participants")

        payment_results = []

        for node_id, reward_amount in rewards.items():
            try:
                # Get node wallet address
                node = await self.node_registry.get_node(node_id)
                if not node:
                    logger.error(f"Node {node_id} not found for reward distribution")
                    continue

                # Process payment
                result = await self.payment_client.process_payment(
                    from_wallet="training-pool-wallet",  # Pool wallet for training rewards
                    to_wallet=node.wallet_address,
                    amount=reward_amount,
                    metadata={
                        "type": "training_reward",
                        "round_id": round_id,
                        "node_id": node_id
                    }
                )

                payment_results.append({
                    "node_id": node_id,
                    "amount": reward_amount,
                    "transaction_signature": result.transaction_signature,
                    "status": "success"
                })

                logger.debug(f"Paid {reward_amount} SOL to {node_id}")

            except Exception as e:
                logger.error(f"Failed to pay reward to {node_id}: {e}")
                payment_results.append({
                    "node_id": node_id,
                    "amount": reward_amount,
                    "status": "failed",
                    "error": str(e)
                })

        return payment_results

    def update_node_reputation(
        self,
        node_id: str,
        current_reputation: float,
        performance_metrics: Dict[str, Any]
    ) -> float:
        """Update node reputation based on training performance"""

        # Reputation adjustment factors
        loss = performance_metrics.get("loss", float('inf'))
        samples = performance_metrics.get("samples_trained", 0)
        training_time = performance_metrics.get("training_time", float('inf'))

        # Calculate performance score (0-1)
        performance_score = 0.5  # Default neutral score

        if loss < 3.0:  # Good loss
            performance_score += 0.2
        elif loss > 5.0:  # Poor loss
            performance_score -= 0.2

        if samples > 1500:  # Good sample count
            performance_score += 0.15
        elif samples < 500:  # Low sample count
            performance_score -= 0.15

        if training_time < 300:  # Fast training
            performance_score += 0.1
        elif training_time > 900:  # Slow training
            performance_score -= 0.1

        # Apply reputation update with momentum
        momentum = 0.9  # Keep 90% of old reputation, 10% new performance
        new_reputation = current_reputation * momentum + performance_score * (1 - momentum)

        # Clamp to valid range
        return max(0.0, min(1.0, new_reputation))

    async def _update_node_reputations(self, updates: List[TrainingUpdate]):
        """Update reputation for all participating nodes"""

        for update in updates:
            try:
                node = await self.node_registry.get_node(update.node_id)
                if node:
                    new_reputation = self.update_node_reputation(
                        update.node_id,
                        node.reputation_score,
                        update.training_metrics
                    )

                    await self.node_registry.update_node_reputation(
                        update.node_id,
                        new_reputation
                    )

                    logger.debug(f"Updated reputation for {update.node_id}: {node.reputation_score:.3f} -> {new_reputation:.3f}")

            except Exception as e:
                logger.error(f"Failed to update reputation for {update.node_id}: {e}")

    async def _notify_node_training_start(self, node: NodeCapabilities, training_round: TrainingRound):
        """Notify node about training round start"""

        # In production, this would send training configuration to the node
        logger.debug(f"Notifying {node.node_id} about training round {training_round.round_id}")

        # Mock notification (in production, would be HTTP request to node)
        training_config = {
            "round_id": training_round.round_id,
            "model_name": training_round.model_name,
            "learning_rate": training_round.learning_rate,
            "batch_size": training_round.batch_size,
            "local_epochs": training_round.local_epochs,
            "expected_reward": training_round.reward_per_update
        }

        # Simulate sending config to node
        await asyncio.sleep(0.01)

    def _hash_model(self, model: Dict[str, Any]) -> str:
        """Create hash of aggregated model for verification"""

        # Create deterministic hash of model weights
        model_str = json.dumps(model["weights"], sort_keys=True)
        return hashlib.sha256(model_str.encode()).hexdigest()

    def _calculate_diversity_score(self, selected_nodes: List[str], all_nodes: List[NodeCapabilities]) -> float:
        """Calculate diversity score for node selection"""

        if not selected_nodes:
            return 0.0

        node_details = {n.node_id: n for n in all_nodes}
        selected_details = [node_details[nid] for nid in selected_nodes if nid in node_details]

        if not selected_details:
            return 0.0

        # Geographic diversity
        countries = set(node.geographical_location for node in selected_details)
        geo_score = len(countries) / len(selected_details)

        # Network provider diversity
        providers = set(node.network_provider for node in selected_details)
        provider_score = len(providers) / len(selected_details)

        # Combined diversity score
        return (geo_score + provider_score) / 2

    async def get_round_status(self, round_id: str) -> Dict[str, Any]:
        """Get status of a training round"""

        if round_id not in self.active_rounds:
            raise ValueError(f"Training round {round_id} not found")

        training_round = self.active_rounds[round_id]

        return {
            "round_id": round_id,
            "model_name": training_round.model_name,
            "status": training_round.status,
            "participants": len(training_round.participating_nodes),
            "submitted_updates": len(training_round.submitted_updates),
            "created_at": training_round.created_at,
            "started_at": training_round.started_at,
            "completed_at": training_round.completed_at,
            "metrics": training_round.aggregation_metrics
        }

    async def list_active_rounds(self) -> List[Dict[str, Any]]:
        """List all active training rounds"""

        return [
            await self.get_round_status(round_id)
            for round_id in self.active_rounds.keys()
        ]

    async def cleanup_completed_rounds(self, max_age_hours: int = 24):
        """Clean up old completed training rounds"""

        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)

        to_remove = []

        for round_id, training_round in self.active_rounds.items():
            if (training_round.status in ["completed", "failed"] and
                training_round.completed_at and
                training_round.completed_at < cutoff_time):
                to_remove.append(round_id)

        for round_id in to_remove:
            del self.active_rounds[round_id]
            logger.debug(f"Cleaned up training round {round_id}")

        return len(to_remove)