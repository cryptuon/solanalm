#!/usr/bin/env python3
"""
Simple SolanaLM Gateway Runner

Runs a minimal gateway for testing without all the complex dependencies.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SolanaLM Gateway",
    description="Hybrid LLM Inference + Federated Learning Network",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
nodes = []

@app.get("/")
async def root():
    """Root endpoint with network status"""
    return {
        "service": "SolanaLM Gateway",
        "version": "1.0.0",
        "status": "online",
        "network_stats": {
            "total_nodes": len(nodes),
            "active_nodes": len(nodes),
            "total_requests": 0
        }
    }

@app.get("/nodes")
async def list_nodes():
    """List all registered nodes"""
    return nodes

@app.post("/nodes/register")
async def register_node(capabilities: dict):
    """Register a new node"""
    node_id = capabilities.get("node_id", f"node_{len(nodes)}")
    nodes.append(capabilities)
    logger.info(f"Registered node: {node_id}")
    return {"node_id": node_id, "status": "registered"}

@app.get("/training/status")
async def training_status():
    """Get training status"""
    return {
        "active_rounds": 0,
        "participating_nodes": 0,
        "next_round_start": None,
        "status": "idle"
    }

@app.get("/privacy_status")
async def privacy_status():
    """Get privacy network status"""
    return {
        "privacy_network_active": True,
        "total_nodes": len(nodes),
        "privacy_capable_nodes": 0,
        "anonymity_set_size": 10,
        "circuit_diversity_score": 0.8,
        "geographic_coverage": 3,
        "avg_circuit_length": 3,
        "privacy_success_rate": 0.95
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

@app.post("/inference")
async def inference_request(request: dict):
    """Mock inference endpoint"""
    raise HTTPException(status_code=404, detail="Not Found")

@app.post("/private_inference")
async def private_inference_request(request: dict):
    """Mock private inference endpoint"""
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    logger.info("Starting minimal SolanaLM Gateway for testing...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )