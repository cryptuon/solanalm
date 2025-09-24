#!/usr/bin/env python3
"""
Pytest Configuration and Shared Fixtures

Provides common test fixtures and configuration for all SolanaLM tests.
"""

import pytest
import asyncio
import tempfile
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models.schemas import NodeCapabilities, InferenceRequest, TrainingUpdate


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_solana_client():
    """Mock Solana client for testing payments"""
    client = AsyncMock()

    # Mock successful payment
    payment_result = MagicMock()
    payment_result.transaction_signature = "test-tx-signature-123"
    payment_result.amount = 0.001
    payment_result.status = "confirmed"

    client.process_payment.return_value = payment_result
    client.get_balance.return_value = 1.0
    client.initialize.return_value = None
    client.close.return_value = None

    return client


@pytest.fixture
async def mock_node_registry():
    """Mock node registry for testing"""
    registry = AsyncMock()

    # Mock network stats
    registry.get_network_stats.return_value = {
        "total_nodes": 10,
        "active_nodes": 8,
        "inference_nodes": 6,
        "training_nodes": 4,
        "average_reputation": 0.85
    }

    registry.initialize.return_value = None
    registry.close.return_value = None

    return registry


@pytest.fixture
def sample_inference_nodes():
    """Sample inference nodes for testing"""
    return [
        NodeCapabilities(
            node_id="inference-node-1",
            wallet_address="inf-wallet-1",
            node_type="inference",
            supported_models=["gpt-3.5-turbo", "gpt-4"],
            endpoint="http://inf-node-1:8100",
            geographical_location="United States",
            network_provider="AWS",
            reputation_score=0.95,
            pricing={"per_request": 0.001, "per_token": 0.00001},
            compute_capacity={"gpu_memory": 24, "cpu_cores": 16},
            supports_onion_routing=True
        ),
        NodeCapabilities(
            node_id="inference-node-2",
            wallet_address="inf-wallet-2",
            node_type="inference",
            supported_models=["claude-3", "gpt-4"],
            endpoint="http://inf-node-2:8100",
            geographical_location="Germany",
            network_provider="Hetzner",
            reputation_score=0.92,
            pricing={"per_request": 0.0008, "per_token": 0.000008},
            compute_capacity={"gpu_memory": 48, "cpu_cores": 32},
            supports_onion_routing=True
        ),
        NodeCapabilities(
            node_id="inference-node-3",
            wallet_address="inf-wallet-3",
            node_type="inference",
            supported_models=["llama-2", "gpt-3.5-turbo"],
            endpoint="http://inf-node-3:8100",
            geographical_location="Singapore",
            network_provider="DigitalOcean",
            reputation_score=0.88,
            pricing={"per_request": 0.0012, "per_token": 0.000012},
            compute_capacity={"gpu_memory": 16, "cpu_cores": 8},
            supports_onion_routing=True
        )
    ]


@pytest.fixture
def sample_training_nodes():
    """Sample training nodes for testing"""
    return [
        NodeCapabilities(
            node_id="training-node-1",
            wallet_address="train-wallet-1",
            node_type="training",
            supported_models=["gpt-2", "llama-7b"],
            endpoint="http://train-node-1:8100",
            geographical_location="Canada",
            network_provider="Vultr",
            reputation_score=0.90,
            compute_capacity={"gpu_memory": 80, "cpu_cores": 64},
            training_capabilities={
                "max_batch_size": 64,
                "supported_optimizers": ["adam", "sgd", "rmsprop"],
                "precision": ["fp16", "fp32", "bf16"],
                "gradient_compression": True
            }
        ),
        NodeCapabilities(
            node_id="training-node-2",
            wallet_address="train-wallet-2",
            node_type="training",
            supported_models=["llama-7b", "gpt-3.5-turbo"],
            endpoint="http://train-node-2:8100",
            geographical_location="Switzerland",
            network_provider="ProtonVPN",
            reputation_score=0.96,
            compute_capacity={"gpu_memory": 40, "cpu_cores": 32},
            training_capabilities={
                "max_batch_size": 32,
                "supported_optimizers": ["adam", "adamw"],
                "precision": ["fp16", "fp32"],
                "gradient_compression": False
            }
        )
    ]


@pytest.fixture
def sample_inference_request():
    """Sample inference request for testing"""
    return InferenceRequest(
        model="gpt-4",
        prompt="Test prompt for inference",
        wallet_address="user-wallet-123",
        max_tokens=100,
        temperature=0.7,
        request_id="test-request-456"
    )


@pytest.fixture
def sample_training_updates():
    """Sample training updates for testing"""
    return [
        TrainingUpdate(
            node_id="training-node-1",
            round_id="round-123",
            model_weights={
                "layer1.weight": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                "layer1.bias": [0.1, 0.2],
                "layer2.weight": [[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]],
                "layer2.bias": [0.05, 0.10, 0.15]
            },
            training_metrics={
                "loss": 2.5,
                "accuracy": 0.75,
                "samples_trained": 1000,
                "training_time": 300,
                "epochs_completed": 3
            },
            update_size_mb=12.5,
            compression_method="quantization"
        ),
        TrainingUpdate(
            node_id="training-node-2",
            round_id="round-123",
            model_weights={
                "layer1.weight": [[1.1, 1.9, 3.1], [3.9, 5.1, 5.9]],
                "layer1.bias": [0.12, 0.18],
                "layer2.weight": [[0.52, 0.58], [0.72, 0.78], [0.92, 0.98]],
                "layer2.bias": [0.06, 0.09, 0.14]
            },
            training_metrics={
                "loss": 2.3,
                "accuracy": 0.78,
                "samples_trained": 1200,
                "training_time": 280,
                "epochs_completed": 3
            },
            update_size_mb=11.8,
            compression_method="quantization"
        )
    ]


@pytest.fixture
def temp_model_file():
    """Create temporary model file for testing"""
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
        model_data = {
            "model_name": "test-model",
            "architecture": "transformer",
            "layers": {
                "layer1.weight": [[1.0, 2.0], [3.0, 4.0]],
                "layer1.bias": [0.1, 0.2]
            },
            "metadata": {
                "version": "1.0",
                "trained_samples": 10000,
                "accuracy": 0.85
            }
        }

        import json
        json.dump(model_data, f)
        f.flush()

        yield f.name

        # Clean up
        os.unlink(f.name)


@pytest.fixture
def mock_circuit():
    """Mock privacy circuit for testing"""
    from core.privacy.onion_routing import Circuit

    return Circuit(
        circuit_id="test-circuit-123",
        node_path=["entry-node", "middle-node", "exit-node"],
        circuit_keys={
            "entry-node": b"entry-key-32-bytes-long-test!",
            "middle-node": b"middle-key-32-bytes-long-test",
            "exit-node": b"exit-key-32-bytes-long-test!"
        },
        privacy_level="high",
        target_model="gpt-4"
    )


@pytest.fixture
def mock_payment_mix():
    """Mock payment mixing pool for testing"""
    from core.privacy.anonymous_payments import PaymentMix
    from decimal import Decimal
    import time

    return PaymentMix(
        mix_id="test-mix-456",
        total_amount=Decimal("0.005"),
        participant_count=3,
        created_at=time.time(),
        expires_at=time.time() + 300,  # 5 minutes
        participants=["wallet-1", "wallet-2", "wallet-3"]
    )


@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Clean up test environment after each test"""
    yield

    # Clean up any temporary files or state
    # This runs after each test
    pass


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings"""
    return {
        "solana_network": "devnet",
        "gateway_port": 8001,
        "node_port": 8100,
        "test_timeout": 30,
        "mock_payments": True,
        "log_level": "DEBUG"
    }


# Custom pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "privacy: mark test as privacy-related test"
    )
    config.addinivalue_line(
        "markers", "federation: mark test as federated learning test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_solana: mark test as requiring Solana connection"
    )


# Helper functions for tests
def assert_valid_solana_address(address: str):
    """Assert that a string is a valid Solana address format"""
    assert isinstance(address, str)
    assert len(address) >= 32  # Solana addresses are base58 encoded, typically 32-44 chars
    assert all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in address)


def assert_valid_model_weights(weights: dict):
    """Assert that model weights have valid structure"""
    assert isinstance(weights, dict)
    assert len(weights) > 0

    for layer_name, layer_weights in weights.items():
        assert isinstance(layer_name, str)
        assert layer_name.strip() != ""
        assert isinstance(layer_weights, (list, tuple))


def assert_privacy_circuit_properties(circuit):
    """Assert that a privacy circuit has required properties"""
    assert circuit.circuit_id is not None
    assert len(circuit.node_path) >= 3  # Minimum circuit length
    assert len(circuit.circuit_keys) == len(circuit.node_path)
    assert circuit.privacy_level in ["standard", "high", "maximum"]
    assert all(len(key) == 32 for key in circuit.circuit_keys.values())  # 256-bit keys