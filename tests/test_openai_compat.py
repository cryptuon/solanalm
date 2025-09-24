"""
Tests for OpenAI-compatible API endpoints
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from core.gateway.server import app
from core.gateway.openai_compat import init_openai_compat_router
from core.models.schemas import NodeCapabilities, NodeType, HardwareSpecs, PricingConfig


@pytest.fixture
def mock_registry():
    """Mock node registry for testing"""
    registry = AsyncMock()

    # Mock available models
    mock_node = NodeCapabilities(
        node_id="test-node",
        node_type=NodeType.INFERENCE,
        wallet_address="test-wallet",
        endpoint_url="http://localhost:8100",
        hardware=HardwareSpecs(cpu_cores=4, ram_gb=8, storage_gb=100, network_speed_mbps=100),
        pricing=PricingConfig(per_request=0.001, per_token=0.0001),
        supported_models=["gpt-3.5-turbo", "test-model"]
    )

    registry.get_all_nodes.return_value = [mock_node]

    # Mock node finding
    mock_network_node = AsyncMock()
    mock_response = AsyncMock()
    mock_response.response = "Hello! How can I help you today?"
    mock_response.tokens_generated = 10
    mock_response.cost_sol = 0.001
    mock_response.node_id = "test-node"
    mock_response.processing_time = 0.5

    mock_network_node.process_inference.return_value = mock_response
    registry.find_best_node.return_value = mock_network_node

    return registry


@pytest.fixture
def mock_payment_client():
    """Mock payment client for testing"""
    return AsyncMock()


@pytest.fixture
def test_client(mock_registry, mock_payment_client):
    """Test client with mocked dependencies"""
    # Initialize the OpenAI compat router with mocks
    init_openai_compat_router(mock_registry, mock_payment_client)

    return TestClient(app)


class TestOpenAICompat:
    """Test OpenAI-compatible endpoints"""

    def test_list_models(self, test_client):
        """Test /v1/models endpoint"""
        response = test_client.get("/v1/models")

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "list"
        assert len(data["data"]) == 2
        assert any(model["id"] == "gpt-3.5-turbo" for model in data["data"])
        assert any(model["id"] == "test-model" for model in data["data"])

    def test_chat_completions(self, test_client):
        """Test /v1/chat/completions endpoint"""
        request_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }

        response = test_client.post(
            "/v1/chat/completions",
            json=request_data,
            headers={"Authorization": "Bearer test-wallet-123"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "chat.completion"
        assert data["model"] == "gpt-3.5-turbo"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert "usage" in data
        assert data["usage"]["completion_tokens"] == 10

    def test_chat_completions_no_auth(self, test_client):
        """Test chat completions without authorization header"""
        request_data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }

        response = test_client.post("/v1/chat/completions", json=request_data)

        # Should still work with anonymous wallet
        assert response.status_code == 200

    def test_completions_legacy(self, test_client):
        """Test legacy /v1/completions endpoint"""
        request_data = {
            "model": "test-model",
            "prompt": "Once upon a time",
            "max_tokens": 20,
            "temperature": 0.5
        }

        response = test_client.post(
            "/v1/completions",
            json=request_data,
            headers={"Authorization": "Bearer sk-wallet456"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "text_completion"
        assert data["model"] == "test-model"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["text"] == "Hello! How can I help you today?"

    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["api_version"] == "v1"
        assert data["compatibility"] == "openai"

    def test_invalid_model(self, test_client, mock_registry):
        """Test request with invalid model"""
        # Mock no nodes available for this model
        mock_registry.find_best_node.return_value = None

        request_data = {
            "model": "nonexistent-model",
            "messages": [
                {"role": "user", "content": "Test"}
            ]
        }

        response = test_client.post("/v1/chat/completions", json=request_data)

        assert response.status_code == 503
        assert "No available nodes" in response.json()["detail"]


class TestAuthExtraction:
    """Test wallet extraction from authorization headers"""

    def test_bearer_wallet_extraction(self, test_client):
        """Test various bearer token formats"""
        from core.gateway.openai_compat import extract_wallet_from_auth

        # Standard wallet address
        assert extract_wallet_from_auth("Bearer wallet123") == "wallet123"

        # OpenAI-style API key with wallet
        assert extract_wallet_from_auth("Bearer sk-wallet456") == "wallet456"

        # No authorization
        assert extract_wallet_from_auth("") == "anonymous_wallet"
        assert extract_wallet_from_auth(None) == "anonymous_wallet"

        # Invalid format
        assert extract_wallet_from_auth("Invalid format") == "anonymous_wallet"


class TestMessageConversion:
    """Test chat message to prompt conversion"""

    def test_message_to_prompt_conversion(self):
        """Test converting chat messages to single prompt"""
        from core.gateway.openai_compat import convert_messages_to_prompt, ChatMessage

        messages = [
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello!"),
            ChatMessage(role="assistant", content="Hi there!"),
            ChatMessage(role="user", content="How are you?")
        ]

        prompt = convert_messages_to_prompt(messages)

        expected = (
            "System: You are a helpful assistant.\n"
            "User: Hello!\n"
            "Assistant: Hi there!\n"
            "User: How are you?\n"
            "Assistant:"
        )

        assert prompt == expected


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling multiple concurrent requests"""
    from core.gateway.openai_compat import router

    # This would test the actual async behavior
    # For now, just verify the router is properly configured
    assert router.prefix == "/v1"
    assert len(router.routes) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])