#!/usr/bin/env python3
"""
Federated Learning System Tests

Tests the federated learning coordination, model aggregation,
and distributed training capabilities.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.training.federation import FederatedLearningCoordinator, TrainingRound
from core.training.model_aggregation import ModelAggregator, FederatedAveraging
from core.models.schemas import NodeCapabilities, TrainingUpdate


class TestFederatedLearningCoordinator:
    """Test federated learning coordination logic"""

    @pytest.fixture
    def coordinator(self):
        """Create federated learning coordinator"""
        mock_registry = AsyncMock()
        mock_payment_client = AsyncMock()
        return FederatedLearningCoordinator(mock_registry, mock_payment_client)

    @pytest.fixture
    def training_nodes(self):
        """Create mock training nodes"""
        return [
            NodeCapabilities(
                node_id=f"training-node-{i}",
                wallet_address=f"training-wallet-{i}",
                node_type="training",
                supported_models=["gpt-2", "llama-7b"],
                endpoint=f"http://training-node-{i}:8100",
                geographical_location=["USA", "Germany", "Singapore"][i % 3],
                network_provider=["AWS", "Hetzner", "DO"][i % 3],
                reputation_score=0.85 + (i * 0.02),
                compute_capacity={"gpu_memory": 24, "cpu_cores": 16},
                training_capabilities={
                    "max_batch_size": 32,
                    "supported_optimizers": ["adam", "sgd"],
                    "precision": ["fp16", "fp32"]
                }
            ) for i in range(5)
        ]

    @pytest.mark.asyncio
    async def test_training_round_creation(self, coordinator, training_nodes):
        """Test creating a new training round"""
        # Mock node registry
        coordinator.node_registry.get_training_nodes.return_value = training_nodes

        round_config = {
            "model_name": "llama-7b",
            "target_participants": 3,
            "max_participants": 5,
            "learning_rate": 0.001,
            "batch_size": 16,
            "local_epochs": 3,
            "reward_per_update": 0.01
        }

        training_round = await coordinator.create_training_round(round_config)

        assert training_round is not None
        assert training_round.model_name == "llama-7b"
        assert training_round.status == "recruiting"
        assert len(training_round.participating_nodes) == 0
        assert training_round.round_id in coordinator.active_rounds

    @pytest.mark.asyncio
    async def test_node_recruitment(self, coordinator, training_nodes):
        """Test recruiting nodes for training"""
        coordinator.node_registry.get_training_nodes.return_value = training_nodes

        # Create training round
        round_config = {
            "model_name": "llama-7b",
            "target_participants": 3,
            "max_participants": 5,
            "learning_rate": 0.001,
            "batch_size": 16,
            "local_epochs": 3,
            "reward_per_update": 0.01
        }

        training_round = await coordinator.create_training_round(round_config)

        # Recruit nodes
        recruited = await coordinator.recruit_nodes(training_round.round_id)

        assert len(recruited) >= round_config["target_participants"]
        assert len(recruited) <= round_config["max_participants"]

        # Verify nodes were added to round
        updated_round = coordinator.active_rounds[training_round.round_id]
        assert len(updated_round.participating_nodes) == len(recruited)

    @pytest.mark.asyncio
    async def test_training_round_execution(self, coordinator, training_nodes):
        """Test executing a complete training round"""
        coordinator.node_registry.get_training_nodes.return_value = training_nodes

        round_config = {
            "model_name": "llama-7b",
            "target_participants": 3,
            "learning_rate": 0.001,
            "batch_size": 16,
            "local_epochs": 3,
            "reward_per_update": 0.01
        }

        training_round = await coordinator.create_training_round(round_config)
        await coordinator.recruit_nodes(training_round.round_id)

        # Mock training updates from nodes
        mock_updates = []
        for i, node_id in enumerate(training_round.participating_nodes[:3]):
            update = TrainingUpdate(
                node_id=node_id,
                round_id=training_round.round_id,
                model_weights={"layer1": [0.1 + i*0.01] * 100, "layer2": [0.2 + i*0.01] * 50},
                training_metrics={
                    "loss": 2.5 - i*0.1,
                    "accuracy": 0.7 + i*0.05,
                    "samples_trained": 1000
                },
                update_size_mb=15.2
            )
            mock_updates.append(update)

        # Mock the training execution
        with patch.object(coordinator, '_collect_training_updates') as mock_collect:
            mock_collect.return_value = mock_updates

            result = await coordinator.execute_training_round(training_round.round_id)

            assert result["status"] == "completed"
            assert result["participants"] == len(mock_updates)
            assert "aggregated_model" in result
            mock_collect.assert_called_once()

    def test_node_selection_strategy(self, coordinator, training_nodes):
        """Test node selection for training diversity"""
        # Test geographic diversity preference
        selected = coordinator._select_training_nodes(
            training_nodes,
            target_count=3,
            max_count=5,
            strategy="geographic_diversity"
        )

        assert len(selected) == 3

        # Check geographic diversity
        locations = [node.geographical_location for node in selected]
        assert len(set(locations)) >= 2, "Should prefer geographic diversity"

    def test_reputation_filtering(self, coordinator, training_nodes):
        """Test filtering nodes by reputation"""
        # Add low reputation node
        low_rep_node = NodeCapabilities(
            node_id="low-rep-node",
            wallet_address="low-rep-wallet",
            node_type="training",
            supported_models=["llama-7b"],
            endpoint="http://low-rep:8100",
            geographical_location="Unknown",
            network_provider="Unknown",
            reputation_score=0.3  # Low reputation
        )

        all_nodes = training_nodes + [low_rep_node]

        filtered = coordinator._filter_eligible_nodes(all_nodes, min_reputation=0.8)

        # Low reputation node should be filtered out
        assert len(filtered) == len(training_nodes)
        assert not any(node.node_id == "low-rep-node" for node in filtered)


class TestModelAggregation:
    """Test model aggregation algorithms"""

    @pytest.fixture
    def aggregator(self):
        """Create model aggregator"""
        return ModelAggregator()

    @pytest.fixture
    def federated_averaging(self):
        """Create federated averaging aggregator"""
        return FederatedAveraging()

    @pytest.fixture
    def mock_model_updates(self):
        """Create mock model updates from different nodes"""
        return [
            TrainingUpdate(
                node_id="node-1",
                round_id="round-123",
                model_weights={
                    "layer1.weight": [[1.0, 2.0], [3.0, 4.0]],
                    "layer1.bias": [0.1, 0.2],
                    "layer2.weight": [[0.5, 0.6], [0.7, 0.8]],
                    "layer2.bias": [0.05, 0.10]
                },
                training_metrics={"loss": 2.5, "samples_trained": 1000},
                update_size_mb=10.0
            ),
            TrainingUpdate(
                node_id="node-2",
                round_id="round-123",
                model_weights={
                    "layer1.weight": [[1.2, 1.8], [2.8, 4.2]],
                    "layer1.bias": [0.15, 0.18],
                    "layer2.weight": [[0.6, 0.5], [0.8, 0.7]],
                    "layer2.bias": [0.08, 0.12]
                },
                training_metrics={"loss": 2.3, "samples_trained": 1200},
                update_size_mb=10.5
            ),
            TrainingUpdate(
                node_id="node-3",
                round_id="round-123",
                model_weights={
                    "layer1.weight": [[0.8, 2.2], [3.2, 3.8]],
                    "layer1.bias": [0.08, 0.22],
                    "layer2.weight": [[0.4, 0.7], [0.6, 0.9]],
                    "layer2.bias": [0.03, 0.08]
                },
                training_metrics={"loss": 2.7, "samples_trained": 800},
                update_size_mb=9.8
            )
        ]

    def test_federated_averaging_simple(self, federated_averaging, mock_model_updates):
        """Test basic federated averaging"""
        aggregated = federated_averaging.aggregate(mock_model_updates)

        # Check that weights are properly averaged
        layer1_weight = aggregated["layer1.weight"]
        expected_00 = (1.0 + 1.2 + 0.8) / 3  # Average of first element
        assert abs(layer1_weight[0][0] - expected_00) < 0.001

        layer1_bias = aggregated["layer1.bias"]
        expected_bias_0 = (0.1 + 0.15 + 0.08) / 3
        assert abs(layer1_bias[0] - expected_bias_0) < 0.001

    def test_weighted_federated_averaging(self, federated_averaging, mock_model_updates):
        """Test federated averaging weighted by number of samples"""
        # Enable sample weighting
        aggregated = federated_averaging.aggregate(
            mock_model_updates,
            weighting_strategy="samples"
        )

        # Verify weights are different from simple average due to sample weighting
        total_samples = sum(update.training_metrics["samples_trained"] for update in mock_model_updates)

        # Node-2 has most samples (1200), so should have highest weight
        node2_weight = 1200 / total_samples
        assert node2_weight > 1/3, "Node with more samples should have higher weight"

    def test_model_validation(self, aggregator, mock_model_updates):
        """Test model update validation"""
        # Test valid updates
        valid = aggregator.validate_updates(mock_model_updates)
        assert valid, "Valid updates should pass validation"

        # Test updates with mismatched keys
        invalid_update = TrainingUpdate(
            node_id="node-invalid",
            round_id="round-123",
            model_weights={
                "different_layer": [[1.0, 2.0]],  # Different key structure
            },
            training_metrics={"loss": 2.0, "samples_trained": 500},
            update_size_mb=5.0
        )

        invalid_updates = mock_model_updates + [invalid_update]
        valid = aggregator.validate_updates(invalid_updates)
        assert not valid, "Updates with mismatched keys should fail validation"

    def test_byzantine_fault_tolerance(self, federated_averaging, mock_model_updates):
        """Test handling of Byzantine (malicious) updates"""
        # Add Byzantine update with extreme values
        byzantine_update = TrainingUpdate(
            node_id="byzantine-node",
            round_id="round-123",
            model_weights={
                "layer1.weight": [[1000.0, -1000.0], [500.0, -500.0]],  # Extreme values
                "layer1.bias": [100.0, -100.0],
                "layer2.weight": [[999.0, -999.0], [888.0, -888.0]],
                "layer2.bias": [50.0, -50.0]
            },
            training_metrics={"loss": 0.001, "samples_trained": 10000},  # Suspiciously good
            update_size_mb=12.0
        )

        updates_with_byzantine = mock_model_updates + [byzantine_update]

        # Test Byzantine detection
        detected_byzantine = federated_averaging.detect_byzantine_updates(updates_with_byzantine)
        assert "byzantine-node" in detected_byzantine, "Should detect Byzantine node"

        # Test robust aggregation (excluding Byzantine)
        aggregated = federated_averaging.aggregate(
            updates_with_byzantine,
            exclude_byzantine=True
        )

        # Aggregated weights should be reasonable (not extreme values)
        layer1_weight = aggregated["layer1.weight"]
        assert abs(layer1_weight[0][0]) < 10, "Aggregated weights should exclude Byzantine values"

    def test_compression_decompression(self, aggregator):
        """Test model compression for efficient transmission"""
        original_weights = {
            "layer1.weight": [[1.123456789, 2.987654321], [3.456789012, 4.111111111]],
            "layer1.bias": [0.123456789, 0.987654321],
        }

        # Test quantization compression
        compressed = aggregator.compress_model(original_weights, method="quantization", bits=8)
        decompressed = aggregator.decompress_model(compressed)

        # Values should be close but not identical due to quantization
        assert abs(decompressed["layer1.weight"][0][0] - original_weights["layer1.weight"][0][0]) < 0.1
        assert abs(decompressed["layer1.bias"][0] - original_weights["layer1.bias"][0]) < 0.1

        # Compressed size should be smaller
        assert len(str(compressed)) < len(str(original_weights))


class TestTrainingIncentives:
    """Test training incentive and payment systems"""

    @pytest.fixture
    def coordinator(self):
        """Create coordinator with mock payment client"""
        mock_registry = AsyncMock()
        mock_payment_client = AsyncMock()
        return FederatedLearningCoordinator(mock_registry, mock_payment_client)

    @pytest.mark.asyncio
    async def test_training_rewards_calculation(self, coordinator):
        """Test calculation of training rewards"""
        training_updates = [
            TrainingUpdate(
                node_id="node-1",
                round_id="round-123",
                model_weights={"layer1": [1.0] * 100},
                training_metrics={"loss": 2.5, "samples_trained": 1000, "training_time": 300},
                update_size_mb=15.0
            ),
            TrainingUpdate(
                node_id="node-2",
                round_id="round-123",
                model_weights={"layer1": [1.1] * 100},
                training_metrics={"loss": 2.3, "samples_trained": 1500, "training_time": 450},
                update_size_mb=15.2
            )
        ]

        rewards = coordinator.calculate_training_rewards(
            training_updates,
            base_reward=0.01,
            quality_bonus=True
        )

        assert len(rewards) == 2
        assert all(reward > 0 for reward in rewards.values())

        # Node with better loss should get higher reward
        assert rewards["node-2"] > rewards["node-1"], "Better performing node should get higher reward"

    @pytest.mark.asyncio
    async def test_payment_distribution(self, coordinator):
        """Test distributing payments to training nodes"""
        rewards = {
            "node-1": 0.012,
            "node-2": 0.015,
            "node-3": 0.010
        }

        # Mock successful payments
        coordinator.payment_client.process_payment.return_value.transaction_signature = "tx-signature"

        results = await coordinator.distribute_training_rewards(rewards, "round-123")

        assert len(results) == 3
        assert all(result["status"] == "success" for result in results)
        assert coordinator.payment_client.process_payment.call_count == 3

    def test_reputation_updates(self, coordinator):
        """Test updating node reputation based on training performance"""
        initial_reputation = 0.85

        # Good performance should increase reputation
        good_metrics = {"loss": 2.0, "samples_trained": 2000, "training_time": 300}
        new_reputation = coordinator.update_node_reputation(
            "node-1",
            initial_reputation,
            good_metrics
        )
        assert new_reputation > initial_reputation

        # Poor performance should decrease reputation
        poor_metrics = {"loss": 5.0, "samples_trained": 100, "training_time": 600}
        new_reputation = coordinator.update_node_reputation(
            "node-2",
            initial_reputation,
            poor_metrics
        )
        assert new_reputation < initial_reputation


@pytest.mark.integration
class TestFederatedLearningIntegration:
    """Integration tests for complete federated learning system"""

    @pytest.mark.asyncio
    async def test_complete_training_cycle(self):
        """Test a complete federated learning cycle"""
        # Setup
        mock_registry = AsyncMock()
        mock_payment_client = AsyncMock()
        coordinator = FederatedLearningCoordinator(mock_registry, mock_payment_client)

        # Mock training nodes
        training_nodes = [
            NodeCapabilities(
                node_id=f"node-{i}",
                wallet_address=f"wallet-{i}",
                node_type="training",
                supported_models=["gpt-2"],
                endpoint=f"http://node{i}:8100",
                geographical_location=["USA", "EU", "ASIA"][i % 3],
                reputation_score=0.9,
                training_capabilities={"max_batch_size": 32}
            ) for i in range(6)
        ]

        mock_registry.get_training_nodes.return_value = training_nodes
        mock_payment_client.process_payment.return_value.transaction_signature = "tx-123"

        # 1. Create training round
        round_config = {
            "model_name": "gpt-2",
            "target_participants": 4,
            "learning_rate": 0.001,
            "local_epochs": 3,
            "reward_per_update": 0.02
        }

        training_round = await coordinator.create_training_round(round_config)
        assert training_round.status == "recruiting"

        # 2. Recruit nodes
        recruited = await coordinator.recruit_nodes(training_round.round_id)
        assert len(recruited) == 4

        # 3. Mock training execution
        mock_updates = []
        for i, node_id in enumerate(recruited):
            update = TrainingUpdate(
                node_id=node_id,
                round_id=training_round.round_id,
                model_weights={"layer1": [0.1 + i*0.01] * 100},
                training_metrics={
                    "loss": 3.0 - i*0.1,
                    "accuracy": 0.6 + i*0.05,
                    "samples_trained": 1000 + i*100
                },
                update_size_mb=12.0
            )
            mock_updates.append(update)

        with patch.object(coordinator, '_collect_training_updates') as mock_collect:
            mock_collect.return_value = mock_updates

            # 4. Execute training round
            result = await coordinator.execute_training_round(training_round.round_id)

            assert result["status"] == "completed"
            assert result["participants"] == 4
            assert "global_model_hash" in result

        # 5. Verify payments were distributed
        assert mock_payment_client.process_payment.call_count == 4

    @pytest.mark.asyncio
    async def test_multi_round_training(self):
        """Test multiple consecutive training rounds"""
        coordinator = FederatedLearningCoordinator(AsyncMock(), AsyncMock())

        # Simulate 3 training rounds
        for round_num in range(3):
            round_config = {
                "model_name": "llama-7b",
                "target_participants": 3,
                "learning_rate": 0.001 * (0.9 ** round_num),  # Decay learning rate
                "round_number": round_num + 1
            }

            training_round = await coordinator.create_training_round(round_config)

            # Each round should have decaying learning rate
            expected_lr = 0.001 * (0.9 ** round_num)
            assert abs(training_round.learning_rate - expected_lr) < 0.0001

        # Should have 3 active rounds
        assert len(coordinator.active_rounds) == 3

    @pytest.mark.asyncio
    async def test_failure_recovery(self):
        """Test system recovery from node failures"""
        coordinator = FederatedLearningCoordinator(AsyncMock(), AsyncMock())

        # Create training round with 5 participants
        round_config = {"target_participants": 5, "min_participants": 3}
        training_round = await coordinator.create_training_round(round_config)

        # Simulate 2 nodes failing to submit updates
        successful_updates = [
            TrainingUpdate(
                node_id=f"node-{i}",
                round_id=training_round.round_id,
                model_weights={"layer1": [1.0] * 50},
                training_metrics={"loss": 2.5, "samples_trained": 1000},
                update_size_mb=10.0
            ) for i in range(3)  # Only 3 out of 5 submit
        ]

        with patch.object(coordinator, '_collect_training_updates') as mock_collect:
            mock_collect.return_value = successful_updates

            # Should still complete with minimum participants
            result = await coordinator.execute_training_round(
                training_round.round_id,
                timeout_seconds=60
            )

            assert result["status"] == "completed"
            assert result["participants"] == 3
            assert result["participants"] >= round_config["min_participants"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])