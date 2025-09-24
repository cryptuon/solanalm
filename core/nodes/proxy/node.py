"""
Proxy Node Implementation

Proxies requests to external LLM APIs (OpenAI, Anthropic, etc.) while handling
Solana payments and maintaining the same interface as inference nodes.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
import aiohttp
from fastapi import FastAPI, HTTPException
import uvicorn
import os

from core.models.schemas import (
    InferenceRequest,
    InferenceResponse,
    NodeCapabilities,
    NodeType,
    NodeStatus,
    HardwareSpecs,
    PricingConfig
)

logger = logging.getLogger(__name__)


class ProxyNode:
    """Proxy node that forwards requests to external LLM APIs"""

    def __init__(
        self,
        node_id: str,
        wallet_address: str,
        gateway_url: str,
        host: str = "0.0.0.0",
        port: int = 8200
    ):
        self.node_id = node_id
        self.wallet_address = wallet_address
        self.gateway_url = gateway_url
        self.host = host
        self.port = port

        # API configurations
        self.api_configs = {
            "openai-gpt-3.5": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key_env": "OPENAI_API_KEY",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "cost_per_token": 0.000002  # $0.002 per 1K tokens
            },
            "openai-gpt-4": {
                "provider": "openai",
                "model": "gpt-4",
                "api_key_env": "OPENAI_API_KEY",
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "cost_per_token": 0.00003  # $0.03 per 1K tokens
            },
            "anthropic-claude": {
                "provider": "anthropic",
                "model": "claude-3-haiku-20240307",
                "api_key_env": "ANTHROPIC_API_KEY",
                "endpoint": "https://api.anthropic.com/v1/messages",
                "cost_per_token": 0.000001  # $0.001 per 1K tokens
            }
        }

        # FastAPI app
        self.app = FastAPI(title=f"SolanaLM Proxy Node {node_id}")
        self._setup_routes()

        # Status
        self.is_ready = False
        self.stats = {
            "requests_served": 0,
            "total_tokens_generated": 0,
            "total_processing_time": 0.0,
            "errors": 0,
            "api_costs_usd": 0.0
        }

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy" if self.is_ready else "initializing",
                "supported_models": list(self.api_configs.keys()),
                "stats": self.stats
            }

        @self.app.post("/inference", response_model=InferenceResponse)
        async def inference_endpoint(request: InferenceRequest):
            return await self.process_inference(request)

        @self.app.get("/capabilities")
        async def get_capabilities():
            return await self.get_node_capabilities()

    async def initialize(self):
        """Initialize the proxy node"""
        logger.info(f"Initializing proxy node {self.node_id}")

        # Verify API keys are available
        available_models = []
        for model_name, config in self.api_configs.items():
            api_key = os.getenv(config["api_key_env"])
            if api_key:
                available_models.append(model_name)
                logger.info(f"API key found for {config['provider']}")
            else:
                logger.warning(f"No API key found for {config['provider']} ({config['api_key_env']})")

        if not available_models:
            logger.error("No API keys found! Set environment variables for API access.")
            # Continue anyway for demonstration purposes
            available_models = list(self.api_configs.keys())

        self.available_models = available_models
        self.is_ready = True
        logger.info(f"Proxy node initialized with models: {available_models}")

        # Register with gateway
        await self.register_with_gateway()

    async def process_inference(self, request: InferenceRequest) -> InferenceResponse:
        """Process an inference request by proxying to external API"""
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Node not ready")

        if request.model not in self.api_configs:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {request.model}")

        start_time = time.time()
        config = self.api_configs[request.model]

        try:
            # Route to appropriate provider
            if config["provider"] == "openai":
                response_data = await self._call_openai_api(request, config)
            elif config["provider"] == "anthropic":
                response_data = await self._call_anthropic_api(request, config)
            else:
                raise HTTPException(status_code=500, detail=f"Unknown provider: {config['provider']}")

            processing_time = time.time() - start_time

            # Extract response details
            response_text = response_data["response"]
            tokens_generated = response_data["tokens_generated"]
            api_cost_usd = response_data["api_cost_usd"]

            # Update stats
            self.stats["requests_served"] += 1
            self.stats["total_tokens_generated"] += tokens_generated
            self.stats["total_processing_time"] += processing_time
            self.stats["api_costs_usd"] += api_cost_usd

            # Calculate SOL cost (add markup for profit)
            markup_multiplier = 2.0  # 2x markup over API cost
            cost_sol = (api_cost_usd * markup_multiplier) / 50  # Assume 1 SOL = $50

            return InferenceResponse(
                request_id=request.request_id,
                model=request.model,
                response=response_text,
                processing_time=processing_time,
                tokens_generated=tokens_generated,
                cost_sol=cost_sol,
                node_id=self.node_id
            )

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Proxy inference failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _call_openai_api(self, request: InferenceRequest, config: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI API"""
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise HTTPException(status_code=503, detail="OpenAI API key not available")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config["model"],
            "messages": [
                {"role": "user", "content": request.prompt}
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                config["endpoint"],
                headers=headers,
                json=payload,
                timeout=60
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")

                data = await response.json()

                # Extract response
                response_text = data["choices"][0]["message"]["content"]
                tokens_generated = data["usage"]["completion_tokens"]
                api_cost_usd = tokens_generated * config["cost_per_token"]

                return {
                    "response": response_text,
                    "tokens_generated": tokens_generated,
                    "api_cost_usd": api_cost_usd
                }

    async def _call_anthropic_api(self, request: InferenceRequest, config: Dict[str, Any]) -> Dict[str, Any]:
        """Call Anthropic API"""
        api_key = os.getenv(config["api_key_env"])
        if not api_key:
            raise HTTPException(status_code=503, detail="Anthropic API key not available")

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": config["model"],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [
                {"role": "user", "content": request.prompt}
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                config["endpoint"],
                headers=headers,
                json=payload,
                timeout=60
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error: {response.status} - {error_text}")

                data = await response.json()

                # Extract response
                response_text = data["content"][0]["text"]
                tokens_generated = data["usage"]["output_tokens"]
                api_cost_usd = tokens_generated * config["cost_per_token"]

                return {
                    "response": response_text,
                    "tokens_generated": tokens_generated,
                    "api_cost_usd": api_cost_usd
                }

    async def get_node_capabilities(self) -> NodeCapabilities:
        """Get proxy node capabilities"""
        hardware = HardwareSpecs(
            cpu_cores=2,
            ram_gb=4,
            storage_gb=50,
            network_speed_mbps=1000  # High bandwidth for API calls
        )

        pricing = PricingConfig(
            per_request=0.01,   # Higher base cost for API proxying
            per_token=0.0005,   # Higher per-token cost
            minimum_payment=0.005
        )

        return NodeCapabilities(
            node_id=self.node_id,
            node_type=NodeType.PROXY,
            wallet_address=self.wallet_address,
            endpoint_url=f"http://{self.host}:{self.port}",
            hardware=hardware,
            pricing=pricing,
            supported_models=self.available_models,
            max_concurrent_requests=10,  # Can handle more concurrent API calls
            status=NodeStatus.ONLINE if self.is_ready else NodeStatus.OFFLINE,
            total_requests_served=self.stats["requests_served"],
            success_rate=self._calculate_success_rate()
        )

    def _calculate_success_rate(self) -> float:
        """Calculate success rate based on stats"""
        total_requests = self.stats["requests_served"] + self.stats["errors"]
        if total_requests == 0:
            return 1.0
        return self.stats["requests_served"] / total_requests

    async def register_with_gateway(self):
        """Register this proxy node with the gateway"""
        try:
            capabilities = await self.get_node_capabilities()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gateway_url}/nodes/register",
                    json=capabilities.dict()
                ) as response:
                    if response.status == 200:
                        logger.info("Successfully registered proxy node with gateway")
                    else:
                        logger.error(f"Gateway registration failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to register with gateway: {e}")

    async def run(self):
        """Start the proxy node server"""
        logger.info(f"Starting proxy node on {self.host}:{self.port}")

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main function to run a proxy node"""
    import argparse

    parser = argparse.ArgumentParser(description="Run SolanaLM Proxy Node")
    parser.add_argument("--node-id", required=True, help="Unique node identifier")
    parser.add_argument("--wallet", required=True, help="Solana wallet address")
    parser.add_argument("--gateway", default="http://localhost:8001", help="Gateway URL")
    parser.add_argument("--port", type=int, default=8200, help="Port to run on")

    args = parser.parse_args()

    # Create and initialize node
    node = ProxyNode(
        node_id=args.node_id,
        wallet_address=args.wallet,
        gateway_url=args.gateway,
        port=args.port
    )

    try:
        await node.initialize()
        await node.run()
    except KeyboardInterrupt:
        logger.info("Shutting down proxy node...")
    except Exception as e:
        logger.error(f"Proxy node failed: {e}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())