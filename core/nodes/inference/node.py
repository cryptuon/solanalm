"""
Inference Node Implementation

Serves local LLM inference requests and handles registration with the gateway.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI, HTTPException
import uvicorn
import aiohttp

from core.models.schemas import (
    InferenceRequest,
    InferenceResponse,
    NodeCapabilities,
    NodeType,
    NodeStatus,
    HardwareSpecs,
    PricingConfig
)
from core.nodes.api import NodeAPIRouter

logger = logging.getLogger(__name__)


class InferenceNode:
    """Local inference node that serves LLM requests"""

    def __init__(
        self,
        node_id: str,
        wallet_address: str,
        gateway_url: str,
        model_name: str = "microsoft/DialoGPT-small",  # Lightweight model for testing
        host: str = "0.0.0.0",
        port: int = 8100
    ):
        self.node_id = node_id
        self.wallet_address = wallet_address
        self.gateway_url = gateway_url
        self.model_name = model_name
        self.host = host
        self.port = port

        # Model components
        self.tokenizer: Optional[Any] = None
        self.model: Optional[Any] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # FastAPI app
        self.app = FastAPI(title=f"SolanaLM Inference Node {node_id}")
        self._setup_routes()

        # Status
        self.is_ready = False
        self.is_paused = False
        self.gateway_connected = False
        self.start_time = datetime.utcnow()
        self.node_type = NodeType.INFERENCE
        self.stats = {
            "requests_served": 0,
            "total_tokens_generated": 0,
            "total_processing_time": 0.0,
            "errors": 0
        }

        # Initialize Node API Router for dashboard
        self.node_api = NodeAPIRouter(self)
        self.node_api.mount_to_app(self.app)

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy" if self.is_ready else "loading",
                "model": self.model_name,
                "device": self.device,
                "stats": self.stats
            }

        @self.app.post("/inference", response_model=InferenceResponse)
        async def inference_endpoint(request: InferenceRequest):
            return await self.process_inference(request)

        @self.app.get("/capabilities")
        async def get_capabilities():
            return await self.get_node_capabilities()

    async def initialize(self):
        """Initialize the node and load the model"""
        logger.info(f"Initializing inference node {self.node_id}")

        try:
            # Load tokenizer and model
            logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Move model to device
            self.model = self.model.to(self.device)
            self.model.eval()

            self.is_ready = True
            logger.info(f"Model loaded successfully on {self.device}")

            # Register with gateway
            await self.register_with_gateway()

        except Exception as e:
            logger.error(f"Failed to initialize inference node: {e}")
            raise

    async def process_inference(self, request: InferenceRequest) -> InferenceResponse:
        """Process an inference request"""
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Node not ready")

        if self.is_paused:
            raise HTTPException(status_code=503, detail="Node is paused")

        start_time = time.time()
        prompt_tokens = 0

        try:
            # Tokenize input
            inputs = self.tokenizer(
                request.prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)

            prompt_tokens = len(inputs.input_ids[0])

            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=min(request.max_tokens, 100),  # Limit for safety
                    temperature=request.temperature,
                    top_p=request.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # Decode response
            generated_text = self.tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

            # Extract only the new tokens (remove input prompt)
            if generated_text.startswith(request.prompt):
                response_text = generated_text[len(request.prompt):].strip()
            else:
                response_text = generated_text.strip()

            processing_time = time.time() - start_time
            tokens_generated = len(outputs[0]) - len(inputs.input_ids[0])

            # Update stats
            self.stats["requests_served"] += 1
            self.stats["total_tokens_generated"] += tokens_generated
            self.stats["total_processing_time"] += processing_time

            # Calculate cost (simple pricing for now)
            cost_sol = 0.001 + (tokens_generated * 0.0001)

            # Record request with NodeAPIRouter for dashboard
            await self.node_api.record_request(
                request_id=request.request_id,
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=tokens_generated,
                processing_time=processing_time,
                cost_sol=cost_sol,
                success=True,
            )

            # Record earning
            await self.node_api.record_earning(
                amount_sol=cost_sol,
                payment_type="inference",
                request_id=request.request_id,
            )

            return InferenceResponse(
                request_id=request.request_id,
                model=self.model_name,
                response=response_text,
                processing_time=processing_time,
                tokens_generated=tokens_generated,
                cost_sol=cost_sol,
                node_id=self.node_id
            )

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Inference processing failed: {e}")

            # Record failed request
            await self.node_api.record_request(
                request_id=request.request_id,
                model=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                processing_time=time.time() - start_time,
                cost_sol=0.0,
                success=False,
                error_message=str(e),
            )

            raise HTTPException(status_code=500, detail=str(e))

    async def get_node_capabilities(self) -> NodeCapabilities:
        """Get current node capabilities"""
        # Auto-detect hardware specs
        try:
            from core.utils.hardware_detection import HardwareDetector
            hardware_specs = HardwareDetector.get_hardware_specs_for_node()

            hardware = HardwareSpecs(
                gpu_model=hardware_specs.get("gpu_model"),
                gpu_memory_gb=hardware_specs.get("gpu_memory_gb", 0),
                cpu_cores=hardware_specs.get("cpu_cores", 4),
                ram_gb=hardware_specs.get("ram_gb", 8),
                storage_gb=hardware_specs.get("storage_gb", 100),
                network_speed_mbps=hardware_specs.get("network_speed_mbps", 100)
            )
        except ImportError:
            # Fallback if hardware detection is not available
            hardware = HardwareSpecs(
                gpu_model=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                gpu_memory_gb=torch.cuda.get_device_properties(0).total_memory // (1024**3) if torch.cuda.is_available() else 0,
                cpu_cores=4,
                ram_gb=8,
                storage_gb=100,
                network_speed_mbps=100
            )

        pricing = PricingConfig(
            per_request=0.001,
            per_token=0.0001,
            minimum_payment=0.0005
        )

        return NodeCapabilities(
            node_id=self.node_id,
            node_type=NodeType.INFERENCE,
            wallet_address=self.wallet_address,
            endpoint_url=f"http://{self.host}:{self.port}",
            hardware=hardware,
            pricing=pricing,
            supported_models=[self.model_name],
            max_concurrent_requests=1,
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
        """Register this node with the gateway"""
        try:
            capabilities = await self.get_node_capabilities()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gateway_url}/nodes/register",
                    json=capabilities.dict()
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully registered with gateway")
                        self.gateway_connected = True
                        self.registered_with_gateway = True
                        await self.node_api.event_emitter.emit_gateway_status(True)
                    else:
                        logger.error(f"Gateway registration failed: {response.status}")
                        self.gateway_connected = False

        except Exception as e:
            logger.error(f"Failed to register with gateway: {e}")
            self.gateway_connected = False
            await self.node_api.event_emitter.emit_gateway_status(False)

    async def run(self):
        """Start the inference node server"""
        logger.info(f"Starting inference node on {self.host}:{self.port}")

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main function to run an inference node"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Run SolanaLM Inference Node")
    parser.add_argument("--node-id", required=True, help="Unique node identifier")
    parser.add_argument("--wallet", required=True, help="Solana wallet address")
    parser.add_argument("--gateway", default="http://localhost:8001", help="Gateway URL")
    parser.add_argument("--model", default="microsoft/DialoGPT-small", help="Model to serve")
    parser.add_argument("--port", type=int, default=8100, help="Port to run on")

    args = parser.parse_args()

    # Create and initialize node
    node = InferenceNode(
        node_id=args.node_id,
        wallet_address=args.wallet,
        gateway_url=args.gateway,
        model_name=args.model,
        port=args.port
    )

    try:
        await node.initialize()
        await node.run()
    except KeyboardInterrupt:
        logger.info("Shutting down inference node...")
    except Exception as e:
        logger.error(f"Node failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())