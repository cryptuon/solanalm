#!/usr/bin/env python3
"""
Training Node Implementation

Participates in federated learning rounds, trains on local data,
and shares model updates while preserving privacy.
"""

import asyncio
import logging
import time
import os
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI, HTTPException
import uvicorn
import aiohttp
import json
import random

from core.models.schemas import (
    NodeCapabilities,
    NodeType,
    NodeStatus,
    HardwareSpecs,
    PricingConfig,
    TrainingUpdate,
    TrainingRound
)
from core.training.federated_learning import fl_manager, FederatedUpdate
from core.nodes.api import NodeAPIRouter

logger = logging.getLogger(__name__)


class TrainingNode:
    """Federated learning training node"""

    def __init__(
        self,
        node_id: str,
        wallet_address: str,
        gateway_url: str,
        model_name: str = "gpt2",  # Small model for training
        host: str = "0.0.0.0",
        port: int = 8200
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

        # Training state
        self.current_round: Optional[TrainingRound] = None
        self.training_data: List[str] = []
        self.optimizer: Optional[torch.optim.Optimizer] = None

        # FastAPI app
        self.app = FastAPI(title=f"SolanaLM Training Node {node_id}")
        self._setup_routes()

        # Status
        self.is_ready = False
        self.is_paused = False
        self.gateway_connected = False
        self.start_time = datetime.utcnow()
        self.node_type = NodeType.TRAINING
        self.training_history: List[Dict[str, Any]] = []

        self.stats = {
            "rounds_participated": 0,
            "total_training_time": 0.0,
            "samples_trained": 0,
            "rewards_earned": 0.0,
            "average_loss": 0.0
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
                "current_round": self.current_round.round_id if self.current_round else None,
                "stats": self.stats
            }

        @self.app.post("/training/join")
        async def join_training_round(training_round: TrainingRound):
            """Join a federated training round"""
            return await self.join_training_round(training_round)

        @self.app.post("/training/start")
        async def start_training(round_config: Dict[str, Any]):
            """Start training for current round"""
            return await self.start_training(round_config)

        @self.app.get("/training/update")
        async def get_training_update():
            """Get model updates for current round"""
            return await self.get_training_update()

        @self.app.get("/capabilities")
        async def get_capabilities():
            return await self.get_node_capabilities()

        @self.app.post("/federated/participate")
        async def participate_in_federated_learning(round_config: Dict[str, Any]):
            """Participate in federated learning round"""
            return await self.participate_in_federated_round(round_config)

    async def initialize(self):
        """Initialize the training node"""
        logger.info(f"Initializing training node {self.node_id}")

        try:
            # Load tokenizer and model for training
            logger.info(f"Loading model for training: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)

            # Add padding token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Move model to device
            self.model = self.model.to(self.device)

            # Setup optimizer
            self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-5)

            # Generate some mock training data
            self._generate_mock_training_data()

            self.is_ready = True
            logger.info(f"Training node loaded successfully on {self.device}")

            # Register with gateway
            await self.register_with_gateway()

        except Exception as e:
            logger.error(f"Failed to initialize training node: {e}")
            raise

    def _generate_mock_training_data(self):
        """Generate mock training data for demonstration"""
        # In production, this would load actual training datasets
        mock_prompts = [
            "The quick brown fox jumps over the lazy dog.",
            "Artificial intelligence is transforming the world.",
            "Machine learning enables computers to learn from data.",
            "Neural networks are inspired by the human brain.",
            "Deep learning uses multiple layers of neural networks.",
            "Natural language processing helps computers understand text.",
            "Computer vision enables machines to interpret visual information.",
            "Reinforcement learning trains agents through trial and error.",
            "Supervised learning uses labeled examples for training.",
            "Unsupervised learning finds patterns in unlabeled data."
        ]

        # Expand the dataset
        self.training_data = mock_prompts * 10  # 100 samples
        logger.info(f"Generated {len(self.training_data)} training samples")

    async def join_training_round(self, training_round: TrainingRound) -> Dict[str, Any]:
        """Join a federated training round"""
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Node not ready")

        if training_round.model != self.model_name:
            raise HTTPException(
                status_code=400,
                detail=f"Round model {training_round.model} doesn't match node model {self.model_name}"
            )

        self.current_round = training_round
        logger.info(f"Joined training round {training_round.round_id}")

        return {
            "status": "joined",
            "round_id": training_round.round_id,
            "node_id": self.node_id,
            "expected_reward": training_round.reward_per_node
        }

    async def start_training(self, round_config: Dict[str, Any]) -> Dict[str, Any]:
        """Start training for the current round"""
        if not self.current_round:
            raise HTTPException(status_code=400, detail="No active training round")

        logger.info(f"Starting training for round {self.current_round.round_id}")

        try:
            # Extract training parameters
            learning_rate = round_config.get("learning_rate", 1e-5)
            batch_size = round_config.get("batch_size", 2)
            local_epochs = round_config.get("local_epochs", 3)

            # Update optimizer learning rate
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = learning_rate

            # Emit training started event
            await self.node_api.emit_training_update(
                round_id=self.current_round.round_id,
                status="training",
                progress=0.0,
                loss=None
            )

            # Perform local training
            training_results = await self._train_local_model(
                batch_size=batch_size,
                epochs=local_epochs
            )

            self.stats["rounds_participated"] += 1
            self.stats["total_training_time"] += training_results["training_time"]
            self.stats["samples_trained"] += training_results["samples_processed"]
            self.stats["average_loss"] = training_results["final_loss"]

            # Record training history
            self.training_history.append({
                "round_id": self.current_round.round_id,
                "completed_at": datetime.utcnow().isoformat(),
                "loss": training_results["final_loss"],
                "samples": training_results["samples_processed"],
                "duration": training_results["training_time"]
            })

            # Emit training completed event
            await self.node_api.emit_training_update(
                round_id=self.current_round.round_id,
                status="completed",
                progress=1.0,
                loss=training_results["final_loss"]
            )

            # Record potential earnings from training
            if self.current_round.reward_per_node:
                await self.node_api.record_earning(
                    amount_sol=self.current_round.reward_per_node,
                    payment_type="training",
                    round_id=self.current_round.round_id
                )
                self.stats["rewards_earned"] += self.current_round.reward_per_node

            return {
                "status": "training_completed",
                "round_id": self.current_round.round_id,
                "training_metrics": training_results,
                "node_id": self.node_id
            }

        except Exception as e:
            logger.error(f"Training failed: {e}")
            # Emit training failed event
            await self.node_api.emit_training_update(
                round_id=self.current_round.round_id if self.current_round else "unknown",
                status="failed",
                progress=0.0,
                loss=None
            )
            raise HTTPException(status_code=500, detail=str(e))

    async def _train_local_model(
        self,
        batch_size: int = 2,
        epochs: int = 3
    ) -> Dict[str, Any]:
        """Perform local model training"""
        logger.info(f"Training local model for {epochs} epochs")

        start_time = time.time()
        total_loss = 0.0
        samples_processed = 0

        # Put model in training mode
        self.model.train()

        for epoch in range(epochs):
            epoch_loss = 0.0
            epoch_samples = 0

            # Create batches from training data
            for i in range(0, len(self.training_data), batch_size):
                batch_texts = self.training_data[i:i + batch_size]

                # Tokenize batch
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=128
                ).to(self.device)

                # Forward pass
                outputs = self.model(**inputs, labels=inputs.input_ids)
                loss = outputs.loss

                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                # Update statistics
                epoch_loss += loss.item()
                epoch_samples += len(batch_texts)

                # Simulate some processing time
                await asyncio.sleep(0.01)

            avg_epoch_loss = epoch_loss / max(epoch_samples // batch_size, 1)
            logger.debug(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_epoch_loss:.4f}")

            total_loss += epoch_loss
            samples_processed += epoch_samples

        training_time = time.time() - start_time
        final_loss = total_loss / max(samples_processed // batch_size, 1)

        logger.info(f"Training completed in {training_time:.2f}s - Final loss: {final_loss:.4f}")

        return {
            "training_time": training_time,
            "final_loss": final_loss,
            "samples_processed": samples_processed,
            "epochs_completed": epochs
        }

    async def get_training_update(self) -> TrainingUpdate:
        """Get model updates for federated aggregation"""
        if not self.current_round:
            raise HTTPException(status_code=400, detail="No active training round")

        logger.info("Generating training update for federated aggregation")

        # Extract model weights
        model_weights = {}
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                model_weights[name] = param.data.cpu().tolist()

        # Calculate update size (rough estimate)
        total_params = sum(len(str(weights)) for weights in model_weights.values())
        update_size_mb = total_params / (1024 * 1024)  # Convert to MB

        # Create training update
        training_update = TrainingUpdate(
            node_id=self.node_id,
            round_id=self.current_round.round_id,
            model_weights=model_weights,
            training_metrics={
                "loss": self.stats["average_loss"],
                "samples_trained": len(self.training_data),
                "training_time": self.stats["total_training_time"],
                "accuracy": random.uniform(0.7, 0.9),  # Mock accuracy
                "epochs_completed": 3
            },
            update_size_mb=update_size_mb,
            compression_method="none"
        )

        logger.info(f"Generated training update: {update_size_mb:.2f} MB")
        return training_update

    async def get_node_capabilities(self) -> NodeCapabilities:
        """Get training node capabilities"""
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
                cpu_cores=os.cpu_count() or 4,
                ram_gb=8,
                storage_gb=100,
                network_speed_mbps=100
            )

        pricing = PricingConfig(
            per_request=0.0,  # Training nodes don't charge per request
            per_token=0.0,
            per_training_round=0.01,  # Charge per training round participation
            minimum_payment=0.005
        )

        return NodeCapabilities(
            node_id=self.node_id,
            node_type=NodeType.TRAINING,
            wallet_address=self.wallet_address,
            endpoint_url=f"http://{self.host}:{self.port}",
            hardware=hardware,
            pricing=pricing,
            supported_models=[self.model_name],
            max_concurrent_requests=1,  # Training is sequential
            status=NodeStatus.ONLINE if self.is_ready else NodeStatus.OFFLINE,
            total_requests_served=self.stats["rounds_participated"],
            success_rate=1.0  # TODO: Calculate actual success rate
        )

    async def register_with_gateway(self):
        """Register this training node with the gateway"""
        try:
            capabilities = await self.get_node_capabilities()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.gateway_url}/nodes/register",
                    json=capabilities.dict()
                ) as response:
                    if response.status == 200:
                        self.gateway_connected = True
                        logger.info("Successfully registered training node with gateway")
                        await self.node_api.emit_event(
                            event_type="gateway_connected",
                            title="Gateway Connected",
                            description=f"Connected to gateway at {self.gateway_url}",
                            severity="info"
                        )
                    else:
                        self.gateway_connected = False
                        logger.error(f"Gateway registration failed: {response.status}")

        except Exception as e:
            self.gateway_connected = False
            logger.error(f"Failed to register with gateway: {e}")

    async def apply_global_model(self, global_weights: Dict[str, Any]):
        """Apply aggregated global model weights"""
        logger.info("Applying global model weights from federated aggregation")

        try:
            # Load global weights into local model
            for name, param in self.model.named_parameters():
                if name in global_weights and param.requires_grad:
                    param.data = torch.tensor(global_weights[name]).to(self.device)

            logger.info("Global model weights applied successfully")

        except Exception as e:
            logger.error(f"Failed to apply global weights: {e}")
            raise

    async def participate_in_federated_round(self, round_config: Dict[str, Any]) -> Dict[str, Any]:
        """Participate in federated learning round using the FL manager"""
        logger.info(f"Node {self.node_id} participating in federated learning round")

        try:
            # Use the federated learning manager to simulate training
            update = fl_manager.simulate_local_training(
                node_id=self.node_id,
                training_data=fl_manager.create_training_data(50)  # 50 samples for this node
            )

            # Convert to response format
            return {
                "node_id": self.node_id,
                "status": "completed",
                "loss": update.loss,
                "samples_processed": update.samples_processed,
                "epochs": update.epoch,
                "model_updated": True
            }

        except Exception as e:
            logger.error(f"Federated learning participation failed: {e}")
            return {
                "node_id": self.node_id,
                "status": "failed",
                "error": str(e)
            }

    async def run(self):
        """Start the training node server"""
        logger.info(f"Starting training node on {self.host}:{self.port}")

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main function to run a training node"""
    import argparse

    parser = argparse.ArgumentParser(description="Run SolanaLM Training Node")
    parser.add_argument("--node-id", required=True, help="Unique node identifier")
    parser.add_argument("--wallet", required=True, help="Solana wallet address")
    parser.add_argument("--gateway", default="http://localhost:8001", help="Gateway URL")
    parser.add_argument("--model", default="gpt2", help="Model to train")
    parser.add_argument("--port", type=int, default=8200, help="Port to run on")

    args = parser.parse_args()

    # Create and initialize node
    node = TrainingNode(
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
        logger.info("Shutting down training node...")
    except Exception as e:
        logger.error(f"Training node failed: {e}")
        return 1


if __name__ == "__main__":
    asyncio.run(main())