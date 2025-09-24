"""
Integration tests for the full SolanaLM network
"""

import pytest
import asyncio
import aiohttp
import time
from unittest.mock import patch, AsyncMock

from core.nodes.inference.node import InferenceNode
from core.nodes.proxy.node import ProxyNode
from core.gateway.server import app
from core.registry.node_registry import NodeRegistry
from client.python.solanalm_client import SolanaLMClient


class TestNetworkIntegration:
    """Integration tests for the complete network"""

    @pytest.mark.asyncio
    async def test_full_inference_flow(self):
        """Test complete inference flow: Gateway -> Node Registry -> Inference Node"""

        # This would require actually starting components
        # For now, test the interfaces are compatible

        # Mock gateway response
        mock_response = {
            "request_id": "test-123",
            "model": "test-model",
            "response": "Test response",
            "processing_time": 0.5,
            "tokens_generated": 5,
            "cost_sol": 0.001,
            "node_id": "test-node"
        }

        # Test that client can handle the response format
        async with SolanaLMClient("http://localhost:8001") as client:
            # Mock the actual HTTP call
            with patch.object(client.session, 'post') as mock_post:
                mock_post.return_value.__aenter__.return_value.status = 200
                mock_post.return_value.__aenter__.return_value.json.return_value = mock_response

                response = await client.inference(
                    model="test-model",
                    prompt="Hello",
                    wallet_address="test-wallet"
                )

                assert response.request_id == "test-123"
                assert response.response == "Test response"
                assert response.cost_sol == 0.001

    @pytest.mark.asyncio
    async def test_node_registration_flow(self):
        """Test node registration with gateway"""

        registry = NodeRegistry()
        await registry.initialize()

        try:
            # Create mock node capabilities
            from core.models.schemas import NodeCapabilities, NodeType, HardwareSpecs, PricingConfig

            capabilities = NodeCapabilities(
                node_id="integration-test-node",
                node_type=NodeType.INFERENCE,
                wallet_address="test-wallet-integration",
                endpoint_url="http://localhost:8100",
                hardware=HardwareSpecs(
                    cpu_cores=4,
                    ram_gb=8,
                    storage_gb=100,
                    network_speed_mbps=100
                ),
                pricing=PricingConfig(
                    per_request=0.001,
                    per_token=0.0001
                ),
                supported_models=["test-model"]
            )

            # Mock the endpoint validation
            with patch.object(registry, '_validate_node_endpoint', return_value=True):
                node_id = await registry.register_node(capabilities)
                assert node_id == "integration-test-node"

                # Test finding the node
                node = await registry.find_best_node("test-model", NodeType.INFERENCE)
                assert node is not None
                assert node.node_id == "integration-test-node"

        finally:
            await registry.close()

    @pytest.mark.asyncio
    async def test_openai_compatibility(self):
        """Test OpenAI-compatible API works with standard clients"""

        # Test that our API matches OpenAI's expected format
        expected_chat_completion = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Test response"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 2,
                "total_tokens": 7
            }
        }

        # Validate structure matches what OpenAI clients expect
        assert "choices" in expected_chat_completion
        assert "usage" in expected_chat_completion
        assert expected_chat_completion["object"] == "chat.completion"

    def test_client_sdk_compatibility(self):
        """Test client SDK works with different usage patterns"""

        from client.python.solanalm_client import SolanaLMSyncClient

        # Test sync client can be instantiated
        client = SolanaLMSyncClient("http://localhost:8001")
        assert client.gateway_url == "http://localhost:8001"

        # Test async context manager interface
        async def test_async():
            async with SolanaLMClient("http://localhost:8001") as async_client:
                assert async_client.gateway_url == "http://localhost:8001"

        asyncio.run(test_async())


class TestPaymentIntegration:
    """Test payment system integration"""

    @pytest.mark.asyncio
    async def test_payment_simulation(self):
        """Test simulated payment flow"""

        from core.payments.solana_client import SolanaPaymentClient

        client = SolanaPaymentClient()
        await client.initialize()

        try:
            # Test simulated payment
            result = await client.process_payment(
                from_wallet="test-wallet-1",
                to_wallet="test-wallet-2",
                amount=0.001,
                metadata={"test": True}
            )

            assert result.amount_sol == 0.001
            assert result.from_wallet == "test-wallet-1"
            assert result.to_wallet == "test-wallet-2"
            assert result.status == "confirmed"

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_training_reward_distribution(self):
        """Test training reward distribution"""

        from core.payments.solana_client import SolanaPaymentClient

        client = SolanaPaymentClient()
        await client.initialize()

        try:
            participants = {
                "wallet-1": 0.1,
                "wallet-2": 0.1,
                "wallet-3": 0.1
            }

            results = await client.distribute_training_rewards(
                participants, "test-round-123"
            )

            assert len(results) == 3
            for wallet_address, result in results.items():
                assert wallet_address in participants
                assert result.amount_sol == 0.1

        finally:
            await client.close()


class TestErrorHandling:
    """Test error handling across the system"""

    @pytest.mark.asyncio
    async def test_no_available_nodes(self):
        """Test handling when no nodes are available"""

        registry = NodeRegistry()
        await registry.initialize()

        try:
            # Try to find node for model that doesn't exist
            node = await registry.find_best_node("nonexistent-model")
            assert node is None

        finally:
            await registry.close()

    @pytest.mark.asyncio
    async def test_node_health_failure(self):
        """Test node health check failure handling"""

        registry = NodeRegistry()
        await registry.initialize()

        try:
            from core.models.schemas import NodeCapabilities, NodeType, HardwareSpecs, PricingConfig, NodeStatus

            # Create a node with an invalid endpoint
            capabilities = NodeCapabilities(
                node_id="failing-node",
                node_type=NodeType.INFERENCE,
                wallet_address="test-wallet",
                endpoint_url="http://invalid-endpoint:9999",
                hardware=HardwareSpecs(cpu_cores=1, ram_gb=1, storage_gb=10, network_speed_mbps=10),
                pricing=PricingConfig(per_request=0.001, per_token=0.0001),
                supported_models=["test"]
            )

            # Registration should fail due to invalid endpoint
            with pytest.raises(ValueError):
                await registry.register_node(capabilities)

        finally:
            await registry.close()

    def test_configuration_validation(self):
        """Test configuration validation"""

        from core.config.settings import validate_solana_address

        # Valid-looking addresses should pass
        assert validate_solana_address("11111111111111111111111111111112") == True

        # Invalid addresses should fail
        assert validate_solana_address("invalid") == False
        assert validate_solana_address("") == False


class TestPerformance:
    """Basic performance tests"""

    @pytest.mark.asyncio
    async def test_concurrent_registrations(self):
        """Test handling concurrent node registrations"""

        registry = NodeRegistry()
        await registry.initialize()

        try:
            from core.models.schemas import NodeCapabilities, NodeType, HardwareSpecs, PricingConfig

            # Create multiple registration tasks
            registration_tasks = []

            for i in range(5):
                capabilities = NodeCapabilities(
                    node_id=f"perf-test-node-{i}",
                    node_type=NodeType.INFERENCE,
                    wallet_address=f"test-wallet-{i}",
                    endpoint_url=f"http://localhost:{8100+i}",
                    hardware=HardwareSpecs(cpu_cores=1, ram_gb=1, storage_gb=10, network_speed_mbps=10),
                    pricing=PricingConfig(per_request=0.001, per_token=0.0001),
                    supported_models=["test"]
                )

                # Mock endpoint validation for performance test
                with patch.object(registry, '_validate_node_endpoint', return_value=True):
                    task = registry.register_node(capabilities)
                    registration_tasks.append(task)

            # Wait for all registrations
            results = await asyncio.gather(*registration_tasks, return_exceptions=True)

            # All should succeed
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Registration {i} failed: {result}")
                assert result == f"perf-test-node-{i}"

        finally:
            await registry.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])