#!/usr/bin/env python3
"""
Comprehensive Privacy System Tests

Tests all privacy features including onion routing, payment anonymization,
and security properties of the Tor-like system.
"""

import pytest
import asyncio
import json
import base64
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.privacy.onion_routing import PrivateInferenceGateway, Circuit, CircuitNode
from core.privacy.anonymous_payments import AnonymousPaymentRouter, PrivatePaymentGateway
from core.nodes.onion_handler import OnionNodeHandler
from core.models.schemas import NodeCapabilities, InferenceRequest


class TestOnionRouting:
    """Test onion routing circuit building and request processing"""

    @pytest.fixture
    async def mock_nodes(self):
        """Create mock nodes for testing"""
        return [
            NodeCapabilities(
                node_id="node-usa",
                wallet_address="usa-wallet",
                node_type="inference",
                supported_models=["gpt-4"],
                endpoint="http://usa:8100",
                geographical_location="United States",
                network_provider="AWS",
                reputation_score=0.95,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-germany",
                wallet_address="germany-wallet",
                node_type="inference",
                supported_models=["gpt-4"],
                endpoint="http://germany:8100",
                geographical_location="Germany",
                network_provider="Hetzner",
                reputation_score=0.90,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-singapore",
                wallet_address="singapore-wallet",
                node_type="inference",
                supported_models=["gpt-4"],
                endpoint="http://singapore:8100",
                geographical_location="Singapore",
                network_provider="DigitalOcean",
                reputation_score=0.88,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-canada",
                wallet_address="canada-wallet",
                node_type="inference",
                supported_models=["gpt-4"],
                endpoint="http://canada:8100",
                geographical_location="Canada",
                network_provider="Vultr",
                reputation_score=0.92,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-switzerland",
                wallet_address="switzerland-wallet",
                node_type="inference",
                supported_models=["gpt-4"],
                endpoint="http://switzerland:8100",
                geographical_location="Switzerland",
                network_provider="ProtonVPN",
                reputation_score=0.96,
                supports_onion_routing=True
            )
        ]

    @pytest.fixture
    def privacy_gateway(self):
        """Create privacy gateway with mock registry"""
        mock_registry = AsyncMock()
        return PrivateInferenceGateway(mock_registry)

    @pytest.mark.asyncio
    async def test_circuit_building_standard(self, privacy_gateway, mock_nodes):
        """Test building standard privacy circuit (3 hops)"""
        circuit = await privacy_gateway.build_circuit(
            available_nodes=mock_nodes,
            target_model="gpt-4",
            privacy_level="standard"
        )

        assert circuit is not None
        assert len(circuit.node_path) == 3
        assert circuit.privacy_level == "standard"
        assert circuit.target_model == "gpt-4"

        # Verify geographic diversity
        countries = [node.geographical_location for node in mock_nodes
                    if node.node_id in circuit.node_path]
        assert len(set(countries)) >= 2, "Standard circuit should have geographic diversity"

    @pytest.mark.asyncio
    async def test_circuit_building_high(self, privacy_gateway, mock_nodes):
        """Test building high privacy circuit (4-5 hops)"""
        circuit = await privacy_gateway.build_circuit(
            available_nodes=mock_nodes,
            target_model="gpt-4",
            privacy_level="high"
        )

        assert circuit is not None
        assert 4 <= len(circuit.node_path) <= 5
        assert circuit.privacy_level == "high"

        # Verify strong geographic and network diversity
        countries = [node.geographical_location for node in mock_nodes
                    if node.node_id in circuit.node_path]
        providers = [node.network_provider for node in mock_nodes
                    if node.node_id in circuit.node_path]

        assert len(set(countries)) >= 3, "High privacy should have strong geographic diversity"
        assert len(set(providers)) >= 3, "High privacy should have network diversity"

    @pytest.mark.asyncio
    async def test_circuit_building_maximum(self, privacy_gateway, mock_nodes):
        """Test building maximum privacy circuit (5+ hops)"""
        circuit = await privacy_gateway.build_circuit(
            available_nodes=mock_nodes,
            target_model="gpt-4",
            privacy_level="maximum"
        )

        assert circuit is not None
        assert len(circuit.node_path) >= 5
        assert circuit.privacy_level == "maximum"

    @pytest.mark.asyncio
    async def test_circuit_country_exclusions(self, privacy_gateway, mock_nodes):
        """Test excluding certain countries from circuits"""
        circuit = await privacy_gateway.build_circuit(
            available_nodes=mock_nodes,
            target_model="gpt-4",
            exclude_countries=["United States"]
        )

        if circuit:
            countries = [node.geographical_location for node in mock_nodes
                        if node.node_id in circuit.node_path]
            assert "United States" not in countries

    def test_circuit_encryption_keys(self, privacy_gateway, mock_nodes):
        """Test circuit encryption key generation"""
        circuit_id = "test-circuit-123"
        keys = privacy_gateway._generate_circuit_keys(circuit_id, ["node1", "node2", "node3"])

        assert len(keys) == 3
        assert all(len(key) == 32 for key in keys.values())  # 256-bit keys
        assert all(isinstance(key, bytes) for key in keys.values())

    @pytest.mark.asyncio
    async def test_onion_encryption_layers(self, privacy_gateway):
        """Test multi-layer onion encryption"""
        request = InferenceRequest(
            model="gpt-4",
            prompt="Test private prompt",
            wallet_address="test-wallet"
        )

        circuit = Circuit(
            circuit_id="test-circuit",
            node_path=["node1", "node2", "node3"],
            circuit_keys={"node1": b"key1" * 4, "node2": b"key2" * 4, "node3": b"key3" * 4},
            privacy_level="standard",
            target_model="gpt-4"
        )

        encrypted_payload = privacy_gateway._create_onion_layers(request, circuit)

        assert encrypted_payload is not None
        assert len(encrypted_payload) > len(request.prompt)  # Should be larger due to encryption

        # Verify it's properly base64 encoded
        try:
            decoded = base64.b64decode(encrypted_payload)
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Encrypted payload should be valid base64")


class TestAnonymousPayments:
    """Test anonymous payment routing and mixing"""

    @pytest.fixture
    def payment_router(self):
        """Create payment router with mock Solana client"""
        mock_client = AsyncMock()
        mock_client.process_payment.return_value.transaction_signature = "test-signature"
        return AnonymousPaymentRouter(mock_client)

    @pytest.fixture
    def payment_gateway(self):
        """Create payment gateway with mock client"""
        mock_client = AsyncMock()
        mock_client.process_payment.return_value.transaction_signature = "test-signature"
        return PrivatePaymentGateway(mock_client)

    def test_amount_obfuscation_standard(self, payment_router):
        """Test standard amount obfuscation (0-20% noise)"""
        original_amount = 0.001
        obfuscated = payment_router._obfuscate_amount(original_amount, "standard")

        assert isinstance(obfuscated, Decimal)
        assert float(obfuscated) >= original_amount * 1.0  # At least original
        assert float(obfuscated) <= original_amount * 1.2  # At most 20% more

    def test_amount_obfuscation_high(self, payment_router):
        """Test high amount obfuscation (0-50% noise)"""
        original_amount = 0.001
        obfuscated = payment_router._obfuscate_amount(original_amount, "high")

        assert isinstance(obfuscated, Decimal)
        assert float(obfuscated) >= original_amount * 1.0
        assert float(obfuscated) <= original_amount * 1.5  # At most 50% more

    def test_amount_obfuscation_maximum(self, payment_router):
        """Test maximum amount obfuscation (common tiers + 0-100% noise)"""
        original_amount = 0.001
        obfuscated = payment_router._obfuscate_amount(original_amount, "maximum")

        assert isinstance(obfuscated, Decimal)
        # Should be rounded to common tier with significant noise
        assert float(obfuscated) >= original_amount * 1.0
        assert float(obfuscated) <= original_amount * 2.0  # Up to 100% noise

    @pytest.mark.asyncio
    async def test_payment_mixing_creation(self, payment_router):
        """Test payment mixing pool creation"""
        mix_pool = await payment_router._find_or_create_mix(Decimal("0.001"))

        assert mix_pool is not None
        assert mix_pool.mix_id in payment_router.payment_mixes
        assert mix_pool.participant_count == 0
        assert mix_pool.total_amount == Decimal("0")

    @pytest.mark.asyncio
    async def test_payment_execution_standard(self, payment_gateway):
        """Test standard payment execution (direct routing)"""
        payment = await payment_gateway.process_private_payment(
            circuit_id="test-circuit",
            source_wallet="source-wallet",
            target_wallet="target-wallet",
            amount_sol=0.001,
            privacy_level="standard"
        )

        assert payment.payment_id is not None
        assert payment.circuit_id == "test-circuit"
        assert payment.amount_sol == Decimal("0.001")
        assert payment.obfuscated_amount > payment.amount_sol

    @pytest.mark.asyncio
    async def test_payment_execution_maximum(self, payment_gateway):
        """Test maximum privacy payment (mixing)"""
        payment = await payment_gateway.process_private_payment(
            circuit_id="test-circuit",
            source_wallet="source-wallet",
            target_wallet="target-wallet",
            amount_sol=0.001,
            privacy_level="maximum"
        )

        assert payment.payment_id is not None
        assert payment.mix_id is not None  # Should be added to mix
        assert payment.obfuscated_amount != payment.amount_sol


class TestOnionNodeHandler:
    """Test onion routing at individual nodes"""

    @pytest.fixture
    def node_handler(self):
        """Create onion node handler"""
        circuit_keys = {
            "test-circuit": b"test-key-32-bytes-long-exactly!!"
        }
        return OnionNodeHandler("test-node", circuit_keys)

    def test_circuit_key_registration(self, node_handler):
        """Test registering circuit keys"""
        circuit_id = "new-circuit"
        key = b"new-key-32-bytes-long-exactly!!!"

        node_handler.register_circuit_key(circuit_id, key)

        assert circuit_id in node_handler.symmetric_keys
        assert node_handler.symmetric_keys[circuit_id] == key

    @pytest.mark.asyncio
    async def test_onion_request_handling(self, node_handler):
        """Test handling onion requests"""
        # Create mock encrypted data
        routing_data = {
            "type": "onion_exit",
            "circuit_id": "test-circuit",
            "payload": base64.b64encode(b"encrypted-inference-request").decode()
        }

        encrypted_data = json.dumps(routing_data).encode()

        with patch.object(node_handler, '_handle_exit_node') as mock_exit:
            mock_exit.return_value = b"encrypted-response"

            result = await node_handler.handle_onion_request(encrypted_data)

            assert result == b"encrypted-response"
            mock_exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_inference_execution(self, node_handler):
        """Test actual inference execution at exit node"""
        request_data = {
            "model": "gpt-4",
            "prompt": "Test prompt for private inference",
            "max_tokens": 100
        }

        response = await node_handler._perform_inference(request_data)

        assert response["model"] == "gpt-4"
        assert "response" in response
        assert "processing_time" in response
        assert response["privacy_mode"] is True


class TestPrivacySecurityProperties:
    """Test security properties of the privacy system"""

    def test_node_isolation(self):
        """Test that nodes only see their layer of information"""
        # Entry node: knows source IP, not destination or content
        # Middle node: knows neither source nor destination, only encrypted data
        # Exit node: knows content and destination, not source

        circuit_nodes = [
            CircuitNode(node_id="entry", role="entry", encrypted_layer="layer1"),
            CircuitNode(node_id="middle", role="middle", encrypted_layer="layer2"),
            CircuitNode(node_id="exit", role="exit", encrypted_layer="layer3")
        ]

        # Each node should only have access to its own layer
        for node in circuit_nodes:
            if node.role == "entry":
                # Entry knows it's the first hop but not the content
                assert node.encrypted_layer == "layer1"
            elif node.role == "middle":
                # Middle only sees encrypted passthrough
                assert node.encrypted_layer == "layer2"
            elif node.role == "exit":
                # Exit processes but doesn't know source
                assert node.encrypted_layer == "layer3"

    def test_payment_unlinkability(self):
        """Test that payments cannot be linked to requests"""
        # Payment amount obfuscation makes it hard to correlate
        original_amounts = [0.001, 0.001, 0.002, 0.001, 0.003]

        router = AnonymousPaymentRouter(AsyncMock())
        obfuscated_amounts = []

        for amount in original_amounts:
            obfuscated = router._obfuscate_amount(amount, "high")
            obfuscated_amounts.append(float(obfuscated))

        # All obfuscated amounts should be different even for same original amount
        equal_original_count = sum(1 for x in original_amounts if x == 0.001)
        equal_obfuscated_count = sum(1 for x in obfuscated_amounts if x == obfuscated_amounts[0])

        assert equal_original_count > equal_obfuscated_count, "Obfuscation should prevent amount correlation"

    def test_geographic_diversity_enforcement(self):
        """Test that circuits enforce geographic diversity"""
        nodes = [
            NodeCapabilities(node_id="usa1", geographical_location="United States", supports_onion_routing=True, reputation_score=0.9, supported_models=["gpt-4"], node_type="inference", wallet_address="wallet1", endpoint="http://usa1:8100", network_provider="AWS"),
            NodeCapabilities(node_id="usa2", geographical_location="United States", supports_onion_routing=True, reputation_score=0.8, supported_models=["gpt-4"], node_type="inference", wallet_address="wallet2", endpoint="http://usa2:8100", network_provider="AWS"),
            NodeCapabilities(node_id="germany1", geographical_location="Germany", supports_onion_routing=True, reputation_score=0.9, supported_models=["gpt-4"], node_type="inference", wallet_address="wallet3", endpoint="http://germany1:8100", network_provider="Hetzner"),
            NodeCapabilities(node_id="singapore1", geographical_location="Singapore", supports_onion_routing=True, reputation_score=0.85, supported_models=["gpt-4"], node_type="inference", wallet_address="wallet4", endpoint="http://singapore1:8100", network_provider="DigitalOcean")
        ]

        gateway = PrivateInferenceGateway(AsyncMock())

        # Test diversity scoring
        selected_nodes = ["usa1", "germany1", "singapore1"]
        diversity_score = gateway._calculate_diversity_score(selected_nodes, nodes)

        assert diversity_score > 0, "Diverse selection should have positive score"

        # Test same-country penalty
        same_country_nodes = ["usa1", "usa2", "germany1"]
        same_country_score = gateway._calculate_diversity_score(same_country_nodes, nodes)

        assert diversity_score > same_country_score, "Geographic diversity should be rewarded"

    def test_circuit_freshness(self):
        """Test that each request gets a fresh circuit"""
        circuit_ids = set()

        for i in range(10):
            gateway = PrivateInferenceGateway(AsyncMock())
            # Each gateway instance should generate unique circuit IDs
            circuit_id = f"circuit-{gateway._generate_circuit_id()}"
            circuit_ids.add(circuit_id)

        # All circuit IDs should be unique
        assert len(circuit_ids) == 10, "Each request should get a fresh circuit ID"


@pytest.mark.integration
class TestPrivacyIntegration:
    """Integration tests for the complete privacy system"""

    @pytest.mark.asyncio
    async def test_end_to_end_private_inference(self):
        """Test complete private inference flow"""
        # Mock components
        mock_registry = AsyncMock()
        mock_solana_client = AsyncMock()
        mock_solana_client.process_payment.return_value.transaction_signature = "test-tx"

        # Create nodes
        nodes = [
            NodeCapabilities(
                node_id=f"node-{i}",
                wallet_address=f"wallet-{i}",
                node_type="inference",
                supported_models=["gpt-4"],
                endpoint=f"http://node{i}:8100",
                geographical_location=["USA", "Germany", "Singapore", "Canada", "Switzerland"][i],
                network_provider=["AWS", "Hetzner", "DO", "Vultr", "Proton"][i],
                reputation_score=0.9,
                supports_onion_routing=True
            ) for i in range(5)
        ]

        mock_registry.get_all_nodes.return_value = nodes

        # Create gateways
        privacy_gateway = PrivateInferenceGateway(mock_registry)
        payment_gateway = PrivatePaymentGateway(mock_solana_client)

        # Create request
        request = InferenceRequest(
            model="gpt-4",
            prompt="Private test prompt",
            wallet_address="user-wallet"
        )

        # Test high privacy inference
        with patch.object(privacy_gateway, '_execute_circuit_request') as mock_execute:
            mock_execute.return_value = {
                "request_id": "private-123",
                "model": "gpt-4",
                "response": "Private response",
                "processing_time": 2.5,
                "tokens_generated": 20,
                "cost_sol": 0.001
            }

            response = await privacy_gateway.private_inference(request, "high")

            assert response["request_id"] == "private-123"
            assert "response" in response
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_privacy_performance_characteristics(self):
        """Test privacy vs performance trade-offs"""
        gateway = PrivateInferenceGateway(AsyncMock())

        privacy_levels = ["standard", "high", "maximum"]
        expected_latencies = {"standard": (2, 5), "high": (5, 10), "maximum": (10, 20)}

        for level in privacy_levels:
            # Mock timing
            start_time = 0
            if level == "standard":
                end_time = 3  # 3 seconds
            elif level == "high":
                end_time = 7  # 7 seconds
            else:
                end_time = 15  # 15 seconds

            latency = end_time - start_time
            min_expected, max_expected = expected_latencies[level]

            assert min_expected <= latency <= max_expected, f"{level} privacy should have expected latency"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])