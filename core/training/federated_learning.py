"""
Simple Federated Learning Implementation
Compatible with existing SolanaLM architecture - minimal code changes
"""

import torch
import torch.nn as nn
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FederatedUpdate:
    """Represents a federated learning update from a node"""
    node_id: str
    model_weights: Dict[str, torch.Tensor]
    loss: float
    samples_processed: int
    epoch: int


class SimpleLanguageModel(nn.Module):
    """Simple language model for federated learning demo"""

    def __init__(self, vocab_size: int = 1000, embed_dim: int = 128, hidden_dim: int = 256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.output = nn.Linear(hidden_dim, vocab_size)
        self.vocab_size = vocab_size

    def forward(self, x):
        embedded = self.embedding(x)
        lstm_out, _ = self.lstm(embedded)
        output = self.output(lstm_out)
        return output


class FederatedLearningManager:
    """Manages federated learning rounds with minimal complexity"""

    def __init__(self, model_config: Dict[str, Any] = None):
        self.model_config = model_config or {
            "vocab_size": 1000,
            "embed_dim": 128,
            "hidden_dim": 256
        }
        self.global_model = SimpleLanguageModel(**self.model_config)
        self.round_number = 0
        self.participating_nodes: List[str] = []
        self.updates: List[FederatedUpdate] = []

    def get_global_model_weights(self) -> Dict[str, Any]:
        """Get serializable global model weights"""
        weights = {}
        for name, param in self.global_model.state_dict().items():
            weights[name] = param.cpu().numpy().tolist()
        return weights

    def create_training_data(self, num_samples: int = 100) -> List[Dict]:
        """Create simple synthetic training data"""
        # Simple synthetic text data for demo
        data = []
        for i in range(num_samples):
            # Generate random sequences
            input_seq = torch.randint(0, self.model_config["vocab_size"], (10,))
            target_seq = torch.randint(0, self.model_config["vocab_size"], (10,))

            data.append({
                "input": input_seq.tolist(),
                "target": target_seq.tolist()
            })
        return data

    def simulate_local_training(self, node_id: str, training_data: List[Dict]) -> FederatedUpdate:
        """Simulate local training on a node"""
        logger.info(f"Simulating training on node {node_id} with {len(training_data)} samples")

        # Create local model copy
        local_model = SimpleLanguageModel(**self.model_config)
        local_model.load_state_dict(self.global_model.state_dict())

        optimizer = torch.optim.Adam(local_model.parameters(), lr=0.01)
        criterion = nn.CrossEntropyLoss()

        local_model.train()
        total_loss = 0.0

        # Simple training loop
        for epoch in range(2):  # Just 2 epochs for demo
            epoch_loss = 0.0
            for sample in training_data[:10]:  # Only use first 10 samples
                optimizer.zero_grad()

                input_tensor = torch.tensor([sample["input"]])
                target_tensor = torch.tensor([sample["target"]])

                output = local_model(input_tensor)
                loss = criterion(output.reshape(-1, output.size(-1)),
                               target_tensor.reshape(-1))

                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            total_loss += epoch_loss

        avg_loss = total_loss / (2 * min(10, len(training_data)))

        return FederatedUpdate(
            node_id=node_id,
            model_weights=local_model.state_dict(),
            loss=avg_loss,
            samples_processed=min(10, len(training_data)),
            epoch=2
        )

    def aggregate_updates(self, updates: List[FederatedUpdate]) -> Dict[str, torch.Tensor]:
        """Simple federated averaging"""
        if not updates:
            return self.global_model.state_dict()

        logger.info(f"Aggregating {len(updates)} federated updates")

        # Weighted averaging based on samples processed
        total_samples = sum(update.samples_processed for update in updates)
        aggregated_weights = {}

        # Initialize with zeros
        for name in updates[0].model_weights.keys():
            aggregated_weights[name] = torch.zeros_like(updates[0].model_weights[name])

        # Weighted sum
        for update in updates:
            weight = update.samples_processed / total_samples
            for name, param in update.model_weights.items():
                aggregated_weights[name] += weight * param

        return aggregated_weights

    def run_federated_round(self, participating_nodes: List[str]) -> Dict[str, Any]:
        """Run a complete federated learning round"""
        self.round_number += 1
        self.participating_nodes = participating_nodes
        self.updates = []

        logger.info(f"Starting federated round {self.round_number} with {len(participating_nodes)} nodes")

        # Create training data for each node
        training_data = self.create_training_data(100)

        # Simulate training on each node
        for node_id in participating_nodes:
            # Each node gets a subset of data
            node_data = training_data[:len(training_data)//len(participating_nodes)]
            update = self.simulate_local_training(node_id, node_data)
            self.updates.append(update)

        # Aggregate updates
        new_weights = self.aggregate_updates(self.updates)
        self.global_model.load_state_dict(new_weights)

        # Calculate average metrics
        avg_loss = sum(update.loss for update in self.updates) / len(self.updates)
        total_samples = sum(update.samples_processed for update in self.updates)

        result = {
            "round": self.round_number,
            "participating_nodes": participating_nodes,
            "avg_loss": avg_loss,
            "total_samples": total_samples,
            "global_model_weights": self.get_global_model_weights()
        }

        logger.info(f"Completed federated round {self.round_number}: avg_loss={avg_loss:.4f}, samples={total_samples}")
        return result


# Singleton instance for easy access
fl_manager = FederatedLearningManager()


def run_training_demo(nodes: List[str] = None) -> Dict[str, Any]:
    """Run a federated learning demo"""
    if nodes is None:
        nodes = ["node-1", "node-2", "node-3"]

    logger.info("Running federated learning demonstration")
    return fl_manager.run_federated_round(nodes)


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    result = run_training_demo()
    print(f"Federated Learning Demo Result: {result}")