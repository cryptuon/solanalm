#!/usr/bin/env python3

"""
SolanaLM Gateway Server

Main entry point for the hybrid inference + federated learning network.
Routes requests to nodes and handles Solana payments.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
import uvicorn

from core.registry.node_registry import NodeRegistry
from core.payments.solana_client import SolanaPaymentClient
from core.gateway.openai_compat import router as openai_router, init_openai_compat_router
from core.privacy.onion_routing import PrivateInferenceGateway
from core.models.schemas import (
    InferenceRequest,
    InferenceResponse,
    NodeCapabilities,
    PaymentRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SolanaLM Gateway",
    description="Hybrid LLM Inference + Federated Learning Network",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include OpenAI-compatible router
app.include_router(openai_router)

# Global instances
node_registry: Optional[NodeRegistry] = None
payment_client: Optional[SolanaPaymentClient] = None
private_gateway: Optional[PrivateInferenceGateway] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global node_registry, payment_client

    logger.info("Starting SolanaLM Gateway...")

    # Initialize node registry
    node_registry = NodeRegistry()
    await node_registry.initialize()

    # Initialize Solana payment client
    payment_client = SolanaPaymentClient()
    await payment_client.initialize()

    # Initialize OpenAI compatibility layer
    init_openai_compat_router(node_registry, payment_client)

    # Initialize private inference gateway
    private_gateway = PrivateInferenceGateway(node_registry)

    logger.info("Gateway services initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down SolanaLM Gateway...")

    if node_registry:
        await node_registry.close()
    if payment_client:
        await payment_client.close()


@app.get("/")
async def root():
    """Root endpoint with network status"""
    if not node_registry:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    stats = await node_registry.get_network_stats()
    return {
        "service": "SolanaLM Gateway",
        "version": "0.1.0",
        "status": "active",
        "network_stats": stats
    }


@app.post("/inference", response_model=InferenceResponse)
async def inference_request(request: InferenceRequest):
    """Route inference request to available node"""
    if not node_registry or not payment_client:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    # Find suitable node for the request
    node = await node_registry.find_best_node(
        model=request.model,
        node_type="inference"
    )

    if not node:
        raise HTTPException(
            status_code=503,
            detail="No available inference nodes for requested model"
        )

    try:
        # Process payment
        payment_result = await payment_client.process_payment(
            from_wallet=request.wallet_address,
            to_wallet=node.wallet_address,
            amount=node.pricing.per_request,
            metadata={"request_id": request.request_id}
        )

        # Forward request to node
        response = await node.process_inference(request)

        # Update node metrics
        await node_registry.update_node_metrics(
            node.node_id,
            request_count=1,
            success=True,
            latency=response.processing_time
        )

        return response

    except Exception as e:
        logger.error(f"Inference request failed: {str(e)}")

        # Update failure metrics
        if node:
            await node_registry.update_node_metrics(
                node.node_id,
                request_count=1,
                success=False
            )

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nodes", response_model=List[NodeCapabilities])
async def list_nodes():
    """List all registered nodes and their capabilities"""
    if not node_registry:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    return await node_registry.get_all_nodes()


@app.post("/nodes/register")
async def register_node(capabilities: NodeCapabilities):
    """Register a new node in the network"""
    if not node_registry:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    try:
        node_id = await node_registry.register_node(capabilities)
        return {"node_id": node_id, "status": "registered"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/training/status")
async def training_status():
    """Get current federated learning status"""
    # TODO: Implement training coordinator integration
    return {
        "active_rounds": 0,
        "participating_nodes": 0,
        "next_round_start": None
    }


@app.post("/private_inference", response_model=InferenceResponse)
async def private_inference_request(request: InferenceRequest, privacy_level: str = "standard"):
    """Submit a private inference request using Tor-like onion routing"""
    if not private_gateway:
        raise HTTPException(status_code=503, detail="Private gateway not initialized")

    try:
        response = await private_gateway.private_inference(request, privacy_level)

        return InferenceResponse(
            request_id=response.get("request_id", "private-unknown"),
            model=response.get("model", request.model),
            response=response.get("response", ""),
            processing_time=response.get("processing_time", 0.0),
            tokens_generated=response.get("tokens_generated", 0),
            cost_sol=response.get("cost_sol", 0.0),
            node_id="private-circuit"  # Don't reveal actual node
        )

    except Exception as e:
        logger.error(f"Private inference request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/privacy_status")
async def privacy_status():
    """Get privacy network status"""
    if not node_registry:
        raise HTTPException(status_code=503, detail="Gateway not initialized")

    nodes = await node_registry.get_all_nodes()
    privacy_capable_nodes = len([n for n in nodes if hasattr(n, 'supports_onion_routing')])

    return {
        "privacy_network_active": True,
        "total_nodes": len(nodes),
        "privacy_capable_nodes": privacy_capable_nodes,
        "min_circuit_length": 3,
        "max_circuit_length": 5,
        "privacy_levels": ["standard", "high", "maximum"],
        "estimated_latency": {
            "standard": "2-5 seconds",
            "high": "5-10 seconds",
            "maximum": "10-20 seconds"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}


if __name__ == "__main__":
    uvicorn.run(
        "core.gateway.server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )