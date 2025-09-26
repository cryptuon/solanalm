"""
Advanced Federated Learning Algorithms
Implements state-of-the-art FL algorithms beyond basic FedAvg
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import copy
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


class FLAlgorithm(str, Enum):
    """Supported federated learning algorithms"""
    FEDAVG = "fedavg"
    FEDPROX = "fedprox"
    FEDADAM = "fedadam"
    SCAFFOLD = "scaffold"
    FEDNOVA = "fednova"
    FEDOPT = "fedopt"
    MOON = "moon"


@dataclass
class ClientState:
    """Client-specific state for advanced FL algorithms"""
    client_id: str
    local_epochs: int = 1
    learning_rate: float = 0.01
    momentum: float = 0.9
    weight_decay: float = 1e-4

    # Algorithm-specific states
    control_variates: Optional[Dict[str, torch.Tensor]] = None  # SCAFFOLD
    momentum_buffer: Optional[Dict[str, torch.Tensor]] = None   # FedAdam
    previous_gradient: Optional[Dict[str, torch.Tensor]] = None  # FedNova
    representation: Optional[torch.Tensor] = None              # MOON

    # Statistics
    data_size: int = 0
    local_loss: float = 0.0
    local_accuracy: float = 0.0
    communication_cost: int = 0


@dataclass
class FLRoundResult:
    """Results from a federated learning round"""
    round_number: int
    algorithm: FLAlgorithm
    participating_clients: List[str]
    global_loss: float
    global_accuracy: float
    convergence_metrics: Dict[str, float]
    communication_cost: int
    computation_time: float
    client_states: Dict[str, ClientState]


class AdvancedFLAlgorithm(ABC):
    """Abstract base class for advanced FL algorithms"""

    def __init__(self, name: str, global_model: nn.Module):
        self.name = name
        self.global_model = global_model
        self.round_number = 0
        self.client_states: Dict[str, ClientState] = {}

    @abstractmethod
    def client_update(self, client_id: str, local_data: List[Dict],
                     client_state: ClientState) -> Tuple[Dict[str, torch.Tensor], ClientState]:
        """Perform client-side update"""
        pass

    @abstractmethod
    def server_aggregate(self, client_updates: List[Tuple[str, Dict[str, torch.Tensor], ClientState]]) -> Dict[str, torch.Tensor]:
        """Perform server-side aggregation"""
        pass

    def get_client_state(self, client_id: str) -> ClientState:
        """Get or create client state"""
        if client_id not in self.client_states:
            self.client_states[client_id] = ClientState(client_id=client_id)
        return self.client_states[client_id]


class FedAvgAlgorithm(AdvancedFLAlgorithm):
    """Standard FedAvg algorithm with improvements"""

    def __init__(self, global_model: nn.Module, learning_rate: float = 0.01):
        super().__init__("FedAvg", global_model)
        self.learning_rate = learning_rate

    def client_update(self, client_id: str, local_data: List[Dict],
                     client_state: ClientState) -> Tuple[Dict[str, torch.Tensor], ClientState]:
        """Standard FedAvg client update"""
        model = copy.deepcopy(self.global_model)
        optimizer = optim.SGD(model.parameters(), lr=client_state.learning_rate)

        model.train()
        total_loss = 0.0

        for epoch in range(client_state.local_epochs):
            for batch in self._create_batches(local_data, batch_size=32):
                optimizer.zero_grad()

                # Forward pass
                inputs = torch.tensor([item['input'] for item in batch], dtype=torch.float32)
                targets = torch.tensor([item['target'] for item in batch], dtype=torch.float32)

                outputs = model(inputs)
                loss = nn.MSELoss()(outputs, targets)

                # Backward pass
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

        # Update client state
        client_state.local_loss = total_loss / len(local_data)
        client_state.data_size = len(local_data)
        client_state.communication_cost += self._calculate_comm_cost(model)

        # Return model weights
        return {name: param.data.clone() for name, param in model.named_parameters()}, client_state

    def server_aggregate(self, client_updates: List[Tuple[str, Dict[str, torch.Tensor], ClientState]]) -> Dict[str, torch.Tensor]:
        """Weighted aggregation by data size"""
        total_samples = sum(state.data_size for _, _, state in client_updates)

        aggregated_weights = {}

        for name in client_updates[0][1].keys():
            weighted_sum = torch.zeros_like(client_updates[0][1][name])

            for client_id, weights, state in client_updates:
                weight = state.data_size / total_samples
                weighted_sum += weight * weights[name]

            aggregated_weights[name] = weighted_sum

        return aggregated_weights

    def _create_batches(self, data: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Create mini-batches from data"""
        batches = []
        for i in range(0, len(data), batch_size):
            batches.append(data[i:i + batch_size])
        return batches

    def _calculate_comm_cost(self, model: nn.Module) -> int:
        """Calculate communication cost (number of parameters)"""
        return sum(p.numel() for p in model.parameters())


class FedProxAlgorithm(AdvancedFLAlgorithm):
    """FedProx algorithm with proximal term"""

    def __init__(self, global_model: nn.Module, mu: float = 0.01):
        super().__init__("FedProx", global_model)
        self.mu = mu  # Proximal term coefficient

    def client_update(self, client_id: str, local_data: List[Dict],
                     client_state: ClientState) -> Tuple[Dict[str, torch.Tensor], ClientState]:
        """FedProx client update with proximal term"""
        model = copy.deepcopy(self.global_model)
        global_weights = {name: param.data.clone() for name, param in model.named_parameters()}

        optimizer = optim.SGD(model.parameters(), lr=client_state.learning_rate)

        model.train()
        total_loss = 0.0

        for epoch in range(client_state.local_epochs):
            for batch in self._create_batches(local_data, batch_size=32):
                optimizer.zero_grad()

                # Standard loss
                inputs = torch.tensor([item['input'] for item in batch], dtype=torch.float32)
                targets = torch.tensor([item['target'] for item in batch], dtype=torch.float32)

                outputs = model(inputs)
                loss = nn.MSELoss()(outputs, targets)

                # Proximal term
                proximal_term = 0.0
                for name, param in model.named_parameters():
                    proximal_term += torch.norm(param - global_weights[name]) ** 2

                total_loss_with_prox = loss + (self.mu / 2) * proximal_term

                # Backward pass
                total_loss_with_prox.backward()
                optimizer.step()

                total_loss += loss.item()

        client_state.local_loss = total_loss / len(local_data)
        client_state.data_size = len(local_data)

        return {name: param.data.clone() for name, param in model.named_parameters()}, client_state

    def server_aggregate(self, client_updates: List[Tuple[str, Dict[str, torch.Tensor], ClientState]]) -> Dict[str, torch.Tensor]:
        """Standard weighted aggregation"""
        return FedAvgAlgorithm.server_aggregate(self, client_updates)

    def _create_batches(self, data: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Create mini-batches from data"""
        batches = []
        for i in range(0, len(data), batch_size):
            batches.append(data[i:i + batch_size])
        return batches


class FedAdamAlgorithm(AdvancedFLAlgorithm):
    """FedAdam algorithm with adaptive server optimization"""

    def __init__(self, global_model: nn.Module, server_lr: float = 0.01,
                 beta1: float = 0.9, beta2: float = 0.999, epsilon: float = 1e-8):
        super().__init__("FedAdam", global_model)
        self.server_lr = server_lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon

        # Server-side momentum buffers
        self.server_momentum = {}
        self.server_velocity = {}
        self.server_step = 0

    def client_update(self, client_id: str, local_data: List[Dict],
                     client_state: ClientState) -> Tuple[Dict[str, torch.Tensor], ClientState]:
        """Standard client update"""
        return FedAvgAlgorithm.client_update(self, client_id, local_data, client_state)

    def server_aggregate(self, client_updates: List[Tuple[str, Dict[str, torch.Tensor], ClientState]]) -> Dict[str, torch.Tensor]:
        """Server aggregation with Adam optimizer"""
        self.server_step += 1

        # Standard weighted aggregation to get pseudo-gradients
        current_weights = {name: param.data.clone() for name, param in self.global_model.named_parameters()}
        aggregated_weights = FedAvgAlgorithm.server_aggregate(self, client_updates)

        # Compute pseudo-gradients
        pseudo_gradients = {}
        for name in current_weights.keys():
            pseudo_gradients[name] = current_weights[name] - aggregated_weights[name]

        # Initialize momentum buffers if needed
        if not self.server_momentum:
            for name in pseudo_gradients.keys():
                self.server_momentum[name] = torch.zeros_like(pseudo_gradients[name])
                self.server_velocity[name] = torch.zeros_like(pseudo_gradients[name])

        # Adam update
        updated_weights = {}
        for name in current_weights.keys():
            # Update momentum buffers
            self.server_momentum[name] = self.beta1 * self.server_momentum[name] + (1 - self.beta1) * pseudo_gradients[name]
            self.server_velocity[name] = self.beta2 * self.server_velocity[name] + (1 - self.beta2) * (pseudo_gradients[name] ** 2)

            # Bias correction
            momentum_corrected = self.server_momentum[name] / (1 - self.beta1 ** self.server_step)
            velocity_corrected = self.server_velocity[name] / (1 - self.beta2 ** self.server_step)

            # Update weights
            updated_weights[name] = current_weights[name] - self.server_lr * momentum_corrected / (torch.sqrt(velocity_corrected) + self.epsilon)

        return updated_weights


class SCAFFOLDAlgorithm(AdvancedFLAlgorithm):
    """SCAFFOLD algorithm with control variates"""

    def __init__(self, global_model: nn.Module, learning_rate: float = 0.01):
        super().__init__("SCAFFOLD", global_model)
        self.learning_rate = learning_rate
        self.server_control = {}  # Server control variates

    def client_update(self, client_id: str, local_data: List[Dict],
                     client_state: ClientState) -> Tuple[Dict[str, torch.Tensor], ClientState]:
        """SCAFFOLD client update with control variates"""
        model = copy.deepcopy(self.global_model)

        # Initialize client control variates if needed
        if client_state.control_variates is None:
            client_state.control_variates = {name: torch.zeros_like(param)
                                           for name, param in model.named_parameters()}

        # Initialize server control variates if needed
        if not self.server_control:
            self.server_control = {name: torch.zeros_like(param)
                                 for name, param in model.named_parameters()}

        optimizer = optim.SGD(model.parameters(), lr=client_state.learning_rate)

        model.train()
        total_loss = 0.0

        for epoch in range(client_state.local_epochs):
            for batch in self._create_batches(local_data, batch_size=32):
                optimizer.zero_grad()

                inputs = torch.tensor([item['input'] for item in batch], dtype=torch.float32)
                targets = torch.tensor([item['target'] for item in batch], dtype=torch.float32)

                outputs = model(inputs)
                loss = nn.MSELoss()(outputs, targets)
                loss.backward()

                # Apply control variates
                for name, param in model.named_parameters():
                    if param.grad is not None:
                        control_correction = self.server_control[name] - client_state.control_variates[name]
                        param.grad.data += control_correction

                optimizer.step()
                total_loss += loss.item()

        # Update client control variates
        new_control_variates = {}
        for name, param in model.named_parameters():
            # Approximate gradient with finite difference
            grad_estimate = (param.data - self.global_model.state_dict()[name]) / (client_state.learning_rate * client_state.local_epochs)
            new_control_variates[name] = grad_estimate

        client_state.control_variates = new_control_variates
        client_state.local_loss = total_loss / len(local_data)
        client_state.data_size = len(local_data)

        return {name: param.data.clone() for name, param in model.named_parameters()}, client_state

    def server_aggregate(self, client_updates: List[Tuple[str, Dict[str, torch.Tensor], ClientState]]) -> Dict[str, torch.Tensor]:
        """SCAFFOLD server aggregation with control variate updates"""
        # Standard weighted aggregation
        aggregated_weights = FedAvgAlgorithm.server_aggregate(self, client_updates)

        # Update server control variates
        total_clients = len(client_updates)
        for name in self.server_control.keys():
            control_sum = torch.zeros_like(self.server_control[name])

            for client_id, weights, state in client_updates:
                if state.control_variates and name in state.control_variates:
                    control_sum += state.control_variates[name]

            self.server_control[name] = control_sum / total_clients

        return aggregated_weights

    def _create_batches(self, data: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Create mini-batches from data"""
        batches = []
        for i in range(0, len(data), batch_size):
            batches.append(data[i:i + batch_size])
        return batches


class AdvancedFederatedLearningManager:
    """Advanced federated learning manager supporting multiple algorithms"""

    def __init__(self, algorithm: FLAlgorithm = FLAlgorithm.FEDAVG):
        self.algorithm = algorithm
        self.global_model = self._create_model()
        self.fl_algorithm = self._create_fl_algorithm()
        self.round_number = 0
        self.history: List[FLRoundResult] = []

    def _create_model(self) -> nn.Module:
        """Create the global model"""
        return nn.Sequential(
            nn.Linear(10, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

    def _create_fl_algorithm(self) -> AdvancedFLAlgorithm:
        """Create the FL algorithm instance"""
        if self.algorithm == FLAlgorithm.FEDAVG:
            return FedAvgAlgorithm(self.global_model)
        elif self.algorithm == FLAlgorithm.FEDPROX:
            return FedProxAlgorithm(self.global_model, mu=0.01)
        elif self.algorithm == FLAlgorithm.FEDADAM:
            return FedAdamAlgorithm(self.global_model)
        elif self.algorithm == FLAlgorithm.SCAFFOLD:
            return SCAFFOLDAlgorithm(self.global_model)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

    def create_training_data(self, size: int = 100, client_id: str = "default") -> List[Dict]:
        """Create synthetic training data for a client"""
        np.random.seed(hash(client_id) % 2**32)  # Different data per client

        data = []
        for i in range(size):
            # Create non-IID data by client
            client_bias = hash(client_id) % 10
            input_data = np.random.randn(10) + client_bias * 0.1
            target = np.sum(input_data) * 0.1 + np.random.randn() * 0.01

            data.append({
                "input": input_data.tolist(),
                "target": target
            })

        return data

    def run_federated_round(self, participating_clients: List[str],
                          client_configs: Optional[Dict[str, Dict]] = None) -> FLRoundResult:
        """Run a federated learning round with advanced algorithms"""
        import time
        start_time = time.time()

        self.round_number += 1
        client_updates = []

        # Client updates
        for client_id in participating_clients:
            # Get client configuration
            config = (client_configs or {}).get(client_id, {})
            client_state = self.fl_algorithm.get_client_state(client_id)

            # Update client state with config
            for key, value in config.items():
                if hasattr(client_state, key):
                    setattr(client_state, key, value)

            # Generate client data
            local_data = self.create_training_data(
                size=config.get('data_size', 100),
                client_id=client_id
            )

            # Perform client update
            weights, updated_state = self.fl_algorithm.client_update(
                client_id, local_data, client_state
            )

            client_updates.append((client_id, weights, updated_state))
            logger.info(f"Client {client_id} completed local training")

        # Server aggregation
        aggregated_weights = self.fl_algorithm.server_aggregate(client_updates)

        # Update global model
        with torch.no_grad():
            for name, param in self.global_model.named_parameters():
                param.data = aggregated_weights[name]

        # Calculate metrics
        global_loss = np.mean([state.local_loss for _, _, state in client_updates])
        communication_cost = sum(state.communication_cost for _, _, state in client_updates)
        computation_time = time.time() - start_time

        # Create result
        result = FLRoundResult(
            round_number=self.round_number,
            algorithm=self.algorithm,
            participating_clients=participating_clients,
            global_loss=global_loss,
            global_accuracy=0.0,  # Would calculate from validation set
            convergence_metrics={
                "loss_improvement": self._calculate_loss_improvement(),
                "gradient_norm": self._calculate_gradient_norm(),
                "model_variance": self._calculate_model_variance(client_updates)
            },
            communication_cost=communication_cost,
            computation_time=computation_time,
            client_states={client_id: state for client_id, _, state in client_updates}
        )

        self.history.append(result)
        logger.info(f"FL Round {self.round_number} completed with {len(participating_clients)} clients")

        return result

    def _calculate_loss_improvement(self) -> float:
        """Calculate loss improvement from previous round"""
        if len(self.history) < 2:
            return 0.0
        return self.history[-2].global_loss - self.history[-1].global_loss

    def _calculate_gradient_norm(self) -> float:
        """Calculate global gradient norm"""
        total_norm = 0.0
        for param in self.global_model.parameters():
            if param.grad is not None:
                param_norm = param.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
        return total_norm ** 0.5

    def _calculate_model_variance(self, client_updates: List[Tuple[str, Dict[str, torch.Tensor], ClientState]]) -> float:
        """Calculate variance across client models"""
        if len(client_updates) < 2:
            return 0.0

        # Calculate mean weights
        mean_weights = {}
        for name in client_updates[0][1].keys():
            weight_sum = torch.zeros_like(client_updates[0][1][name])
            for _, weights, _ in client_updates:
                weight_sum += weights[name]
            mean_weights[name] = weight_sum / len(client_updates)

        # Calculate variance
        total_variance = 0.0
        for _, weights, _ in client_updates:
            for name in weights.keys():
                variance = torch.norm(weights[name] - mean_weights[name]) ** 2
                total_variance += variance.item()

        return total_variance / len(client_updates)

    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get information about the current algorithm"""
        return {
            "algorithm": self.algorithm.value,
            "rounds_completed": self.round_number,
            "convergence_history": [r.convergence_metrics for r in self.history[-10:]],
            "performance_metrics": {
                "avg_communication_cost": np.mean([r.communication_cost for r in self.history]) if self.history else 0,
                "avg_computation_time": np.mean([r.computation_time for r in self.history]) if self.history else 0,
                "final_loss": self.history[-1].global_loss if self.history else float('inf')
            }
        }


def run_advanced_fl_demo(algorithm: FLAlgorithm = FLAlgorithm.FEDAVG,
                        num_clients: int = 5, num_rounds: int = 3) -> Dict[str, Any]:
    """Run demonstration of advanced federated learning"""
    logger.info(f"Starting advanced FL demo with {algorithm.value} algorithm")

    # Initialize FL manager
    fl_manager = AdvancedFederatedLearningManager(algorithm)

    # Client configurations (simulate heterogeneity)
    client_configs = {
        f"client-{i}": {
            "local_epochs": np.random.randint(1, 4),
            "learning_rate": 0.01 * (1 + np.random.normal(0, 0.1)),
            "data_size": np.random.randint(50, 200)
        }
        for i in range(num_clients)
    }

    # Run federated learning rounds
    results = []
    for round_num in range(num_rounds):
        # Simulate client participation (not all clients participate each round)
        participating_clients = [f"client-{i}" for i in range(num_clients)]
        if round_num > 0:  # Drop some clients in later rounds
            participating_clients = participating_clients[:max(3, int(num_clients * 0.8))]

        result = fl_manager.run_federated_round(participating_clients, client_configs)
        results.append(result)

        logger.info(f"Round {round_num + 1}: Loss={result.global_loss:.4f}, "
                   f"Clients={len(result.participating_clients)}, "
                   f"Time={result.computation_time:.2f}s")

    return {
        "algorithm": algorithm.value,
        "rounds": results,
        "algorithm_info": fl_manager.get_algorithm_info(),
        "final_model_state": {name: param.data.tolist() for name, param in fl_manager.global_model.named_parameters()}
    }


if __name__ == "__main__":
    # Demonstrate different algorithms
    algorithms = [FLAlgorithm.FEDAVG, FLAlgorithm.FEDPROX, FLAlgorithm.FEDADAM, FLAlgorithm.SCAFFOLD]

    for algo in algorithms:
        print(f"\n{'='*50}")
        print(f"Testing {algo.value} algorithm")
        print('='*50)

        try:
            result = run_advanced_fl_demo(algo, num_clients=5, num_rounds=3)
            print(f"✓ {algo.value} completed successfully")
            print(f"Final loss: {result['rounds'][-1].global_loss:.4f}")
            print(f"Total communication cost: {sum(r.communication_cost for r in result['rounds'])}")
        except Exception as e:
            print(f"✗ {algo.value} failed: {e}")
            logger.error(f"Algorithm {algo.value} failed", exc_info=True)