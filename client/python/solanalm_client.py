"""
SolanaLM Python Client SDK

Simple client for interacting with the SolanaLM network.
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json


@dataclass
class InferenceRequest:
    """Request for LLM inference"""
    model: str
    prompt: str
    wallet_address: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.9
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class InferenceResponse:
    """Response from LLM inference"""
    request_id: str
    model: str
    response: str
    processing_time: float
    tokens_generated: int
    cost_sol: float
    node_id: str


class SolanaLMClient:
    """Client for the SolanaLM network"""

    def __init__(self, gateway_url: str = "http://localhost:8001"):
        self.gateway_url = gateway_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def inference(
        self,
        model: str,
        prompt: str,
        wallet_address: str,
        **kwargs
    ) -> InferenceResponse:
        """Submit an inference request"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        request = InferenceRequest(
            model=model,
            prompt=prompt,
            wallet_address=wallet_address,
            **kwargs
        )

        try:
            async with self.session.post(
                f"{self.gateway_url}/inference",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "wallet_address": request.wallet_address,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "metadata": request.metadata or {}
                },
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return InferenceResponse(
                        request_id=data["request_id"],
                        model=data["model"],
                        response=data["response"],
                        processing_time=data["processing_time"],
                        tokens_generated=data["tokens_generated"],
                        cost_sol=data["cost_sol"],
                        node_id=data["node_id"]
                    )
                else:
                    error_data = await response.text()
                    raise Exception(f"Inference failed: {response.status} - {error_data}")

        except Exception as e:
            self.logger.error(f"Inference request failed: {e}")
            raise

    async def list_available_models(self) -> List[str]:
        """Get list of available models in the network"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"{self.gateway_url}/nodes") as response:
                if response.status == 200:
                    nodes = await response.json()
                    models = set()
                    for node in nodes:
                        models.update(node.get("supported_models", []))
                    return list(models)
                else:
                    raise Exception(f"Failed to list nodes: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []

    async def get_network_status(self) -> Dict[str, Any]:
        """Get network status and statistics"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"{self.gateway_url}/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get network status: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get network status: {e}")
            return {}

    async def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"{self.gateway_url}/training/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get training status: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get training status: {e}")
            return {}

    async def private_inference(
        self,
        model: str,
        prompt: str,
        wallet_address: str,
        privacy_level: str = "standard",
        **kwargs
    ) -> InferenceResponse:
        """Submit a private inference request using Tor-like onion routing"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        request_data = {
            "model": model,
            "prompt": prompt,
            "wallet_address": wallet_address,
            "max_tokens": kwargs.get("max_tokens", 100),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
            "metadata": kwargs.get("metadata", {})
        }

        try:
            async with self.session.post(
                f"{self.gateway_url}/private_inference",
                json=request_data,
                params={"privacy_level": privacy_level},
                timeout=120  # Longer timeout for privacy routing
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return InferenceResponse(
                        request_id=data["request_id"],
                        model=data["model"],
                        response=data["response"],
                        processing_time=data["processing_time"],
                        tokens_generated=data["tokens_generated"],
                        cost_sol=data["cost_sol"],
                        node_id=data["node_id"]
                    )
                else:
                    error_data = await response.text()
                    raise Exception(f"Private inference failed: {response.status} - {error_data}")

        except Exception as e:
            self.logger.error(f"Private inference request failed: {e}")
            raise

    async def batch_inference(
        self,
        model: str,
        prompts: List[str],
        wallet_address: str,
        max_concurrent: int = 5,
        **kwargs
    ) -> List[InferenceResponse]:
        """Submit multiple inference requests concurrently"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def single_inference(prompt: str) -> InferenceResponse:
            async with semaphore:
                return await self.inference(
                    model=model,
                    prompt=prompt,
                    wallet_address=wallet_address,
                    **kwargs
                )

        tasks = [single_inference(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful responses
        successful_results = []
        for result in results:
            if isinstance(result, InferenceResponse):
                successful_results.append(result)
            else:
                self.logger.error(f"Batch inference error: {result}")

        return successful_results

    async def stream_batch_inference(
        self,
        model: str,
        prompts: List[str],
        wallet_address: str,
        **kwargs
    ):
        """Stream inference results as they complete"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        async def single_inference(prompt: str) -> InferenceResponse:
            return await self.inference(
                model=model,
                prompt=prompt,
                wallet_address=wallet_address,
                **kwargs
            )

        tasks = [asyncio.create_task(single_inference(prompt)) for prompt in prompts]

        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                yield result
            except Exception as e:
                self.logger.error(f"Stream inference error: {e}")

    async def join_training_round(
        self,
        model_name: str,
        node_capabilities: Dict[str, Any],
        reward_expectation: float = 0.0
    ) -> Dict[str, Any]:
        """Join a federated training round"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        request_data = {
            "model_name": model_name,
            "node_capabilities": node_capabilities,
            "reward_expectation": reward_expectation
        }

        try:
            async with self.session.post(
                f"{self.gateway_url}/training/join",
                json=request_data,
                timeout=30
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.text()
                    raise Exception(f"Failed to join training: {response.status} - {error_data}")

        except Exception as e:
            self.logger.error(f"Failed to join training round: {e}")
            raise

    async def start_custom_training(
        self,
        config: Dict[str, Any],
        wallet_address: str
    ) -> Dict[str, Any]:
        """Start custom model training"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        request_data = {
            "config": config,
            "wallet_address": wallet_address
        }

        try:
            async with self.session.post(
                f"{self.gateway_url}/training/custom",
                json=request_data,
                timeout=60
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.text()
                    raise Exception(f"Failed to start training: {response.status} - {error_data}")

        except Exception as e:
            self.logger.error(f"Failed to start custom training: {e}")
            raise

    async def get_usage_analytics(
        self,
        wallet_address: str,
        period: str = "last_7_days"
    ) -> Dict[str, Any]:
        """Get usage analytics for a wallet"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(
                f"{self.gateway_url}/analytics/usage",
                params={"wallet_address": wallet_address, "period": period}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    # Return empty analytics if endpoint doesn't exist
                    return {
                        "total_requests": 0,
                        "total_cost": 0.0,
                        "avg_latency": 0.0,
                        "privacy_requests": 0,
                        "privacy_percentage": 0.0,
                        "top_model": "Unknown"
                    }

        except Exception as e:
            self.logger.debug(f"Analytics not available: {e}")
            return {}

    async def get_network_health(self) -> Dict[str, Any]:
        """Get network health metrics"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"{self.gateway_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}

        except Exception as e:
            self.logger.debug(f"Health metrics not available: {e}")
            return {}

    async def get_circuit_info(self, request_id: str) -> Dict[str, Any]:
        """Get privacy circuit information for a request (for verification)"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(
                f"{self.gateway_url}/privacy/circuit/{request_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}

        except Exception as e:
            self.logger.debug(f"Circuit info not available: {e}")
            return {}

    async def get_payment_privacy_info(self, request_id: str) -> Dict[str, Any]:
        """Get payment privacy information for a request"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(
                f"{self.gateway_url}/privacy/payment/{request_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}

        except Exception as e:
            self.logger.debug(f"Payment privacy info not available: {e}")
            return {}

    async def get_privacy_metrics(self) -> Dict[str, Any]:
        """Get current privacy network metrics"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"{self.gateway_url}/privacy_status") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "anonymity_set_size": data.get("anonymity_set_size", 0),
                        "circuit_diversity_score": data.get("circuit_diversity_score", 0.0),
                        "geographic_coverage": data.get("geographic_coverage", 0)
                    }
                else:
                    return {}

        except Exception as e:
            self.logger.debug(f"Privacy metrics not available: {e}")
            return {}

    async def get_privacy_network_health(self) -> Dict[str, Any]:
        """Get privacy network health status"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.get(f"{self.gateway_url}/privacy_status") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "privacy_nodes": data.get("privacy_capable_nodes", 0),
                        "avg_circuit_length": data.get("avg_circuit_length", 0),
                        "privacy_success_rate": data.get("privacy_success_rate", 0.0)
                    }
                else:
                    return {}

        except Exception as e:
            self.logger.debug(f"Privacy network health not available: {e}")
            return {}

    async def configure_webhook(self, webhook_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure webhook for events"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")

        try:
            async with self.session.post(
                f"{self.gateway_url}/webhooks/configure",
                json=webhook_config
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.text()
                    raise Exception(f"Webhook configuration failed: {response.status} - {error_data}")

        except Exception as e:
            self.logger.error(f"Failed to configure webhook: {e}")
            raise


# Synchronous wrapper for easier usage
class SolanaLMSyncClient:
    """Synchronous wrapper for SolanaLM client"""

    def __init__(self, gateway_url: str = "http://localhost:8001"):
        self.gateway_url = gateway_url

    def inference(
        self,
        model: str,
        prompt: str,
        wallet_address: str,
        **kwargs
    ) -> InferenceResponse:
        """Submit a synchronous inference request"""
        async def _inference():
            async with SolanaLMClient(self.gateway_url) as client:
                return await client.inference(
                    model=model,
                    prompt=prompt,
                    wallet_address=wallet_address,
                    **kwargs
                )

        return asyncio.run(_inference())

    def list_available_models(self) -> List[str]:
        """Get list of available models synchronously"""
        async def _list_models():
            async with SolanaLMClient(self.gateway_url) as client:
                return await client.list_available_models()

        return asyncio.run(_list_models())

    def get_network_status(self) -> Dict[str, Any]:
        """Get network status synchronously"""
        async def _status():
            async with SolanaLMClient(self.gateway_url) as client:
                return await client.get_network_status()

        return asyncio.run(_status())


# Example usage functions
async def example_async_usage():
    """Example of async client usage"""
    async with SolanaLMClient() as client:
        # Get network status
        status = await client.get_network_status()
        print(f"Network status: {status}")

        # List available models
        models = await client.list_available_models()
        print(f"Available models: {models}")

        # Submit inference request
        if models:
            response = await client.inference(
                model=models[0],
                prompt="Hello, how are you?",
                wallet_address="FakeWalletAddress123",  # Replace with real wallet
                max_tokens=50
            )
            print(f"Response: {response.response}")
            print(f"Cost: {response.cost_sol} SOL")


def example_sync_usage():
    """Example of synchronous client usage"""
    client = SolanaLMSyncClient()

    # Get network status
    status = client.get_network_status()
    print(f"Network status: {status}")

    # List available models
    models = client.list_available_models()
    print(f"Available models: {models}")

    # Submit inference request
    if models:
        response = client.inference(
            model=models[0],
            prompt="Hello, how are you?",
            wallet_address="FakeWalletAddress123",  # Replace with real wallet
            max_tokens=50
        )
        print(f"Response: {response.response}")
        print(f"Cost: {response.cost_sol} SOL")


if __name__ == "__main__":
    import sys

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        print("Running synchronous example...")
        example_sync_usage()
    else:
        print("Running asynchronous example...")
        asyncio.run(example_async_usage())