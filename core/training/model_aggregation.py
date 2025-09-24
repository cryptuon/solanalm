#!/usr/bin/env python3
"""
Model Aggregation for Federated Learning

Implements various aggregation algorithms for combining model updates
from distributed training nodes while maintaining privacy and handling
Byzantine faults.
"""

import logging
import statistics
import json
import gzip
import base64
from typing import Dict, List, Any, Optional, Union
import numpy as np
from copy import deepcopy

from core.models.schemas import TrainingUpdate

logger = logging.getLogger(__name__)


class ModelAggregator:
    """Base class for model aggregation algorithms"""

    def __init__(self):
        self.supported_methods = ["federated_averaging", "weighted_average", "median"]

    def aggregate(
        self,
        updates: List[TrainingUpdate],
        weighting_strategy: str = "equal",
        exclude_byzantine: bool = True
    ) -> Dict[str, Any]:
        """
        Aggregate model updates using specified strategy

        Args:
            updates: List of training updates from nodes
            weighting_strategy: How to weight updates ("equal", "samples", "performance")
            exclude_byzantine: Whether to detect and exclude Byzantine updates

        Returns:
            Aggregated model weights
        """
        if not updates:
            raise ValueError("No updates provided for aggregation")

        # Validate updates structure
        if not self.validate_updates(updates):
            raise ValueError("Updates failed validation")

        # Detect and exclude Byzantine updates if requested
        if exclude_byzantine:
            byzantine_nodes = self.detect_byzantine_updates(updates)
            if byzantine_nodes:
                logger.warning(f"Detected Byzantine updates from nodes: {byzantine_nodes}")
                updates = [u for u in updates if u.node_id not in byzantine_nodes]

        if not updates:
            raise ValueError("No valid updates remaining after Byzantine filtering")

        # Calculate weights for aggregation
        weights = self._calculate_aggregation_weights(updates, weighting_strategy)

        # Perform aggregation
        return self._weighted_average_aggregation(updates, weights)

    def validate_updates(self, updates: List[TrainingUpdate]) -> bool:
        """Validate that all updates have compatible structure"""
        if not updates:
            return False

        # Check that all updates have the same model structure
        reference_keys = set(updates[0].model_weights.keys())

        for update in updates[1:]:
            if set(update.model_weights.keys()) != reference_keys:
                logger.error(f"Mismatched model keys in update from {update.node_id}")
                return False

        # Check tensor shapes
        for layer_name in reference_keys:
            reference_shape = self._get_tensor_shape(updates[0].model_weights[layer_name])

            for update in updates[1:]:
                if self._get_tensor_shape(update.model_weights[layer_name]) != reference_shape:
                    logger.error(f"Mismatched tensor shape for {layer_name} in update from {update.node_id}")
                    return False

        return True

    def detect_byzantine_updates(self, updates: List[TrainingUpdate]) -> List[str]:
        """Detect Byzantine (malicious/faulty) updates"""
        byzantine_nodes = []

        if len(updates) < 3:
            # Need at least 3 updates for Byzantine detection
            return byzantine_nodes

        # Analyze weight magnitudes for outliers
        for layer_name in updates[0].model_weights.keys():
            layer_magnitudes = []

            for update in updates:
                magnitude = self._calculate_weight_magnitude(update.model_weights[layer_name])
                layer_magnitudes.append((update.node_id, magnitude))

            # Detect outliers using IQR method
            magnitudes = [mag for _, mag in layer_magnitudes]
            q1, q3 = np.percentile(magnitudes, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 3 * iqr  # More aggressive outlier detection
            upper_bound = q3 + 3 * iqr

            for node_id, magnitude in layer_magnitudes:
                if magnitude < lower_bound or magnitude > upper_bound:
                    if node_id not in byzantine_nodes:
                        byzantine_nodes.append(node_id)
                        logger.warning(f"Byzantine update detected from {node_id}: magnitude {magnitude:.4f}")

        # Check loss values for suspiciously good results
        losses = [(u.node_id, u.training_metrics.get("loss", float('inf'))) for u in updates]
        loss_values = [loss for _, loss in losses]

        if loss_values:
            median_loss = statistics.median(loss_values)
            for node_id, loss in losses:
                # Suspiciously low loss compared to others
                if loss < median_loss * 0.1 and loss < 0.5:
                    if node_id not in byzantine_nodes:
                        byzantine_nodes.append(node_id)
                        logger.warning(f"Suspicious loss value from {node_id}: {loss:.4f}")

        return byzantine_nodes

    def _calculate_aggregation_weights(
        self,
        updates: List[TrainingUpdate],
        strategy: str
    ) -> List[float]:
        """Calculate weights for aggregating updates"""

        if strategy == "equal":
            # Equal weighting
            return [1.0 / len(updates)] * len(updates)

        elif strategy == "samples":
            # Weight by number of training samples
            sample_counts = [u.training_metrics.get("samples_trained", 1) for u in updates]
            total_samples = sum(sample_counts)
            return [count / total_samples for count in sample_counts]

        elif strategy == "performance":
            # Weight by training performance (inverse of loss)
            losses = [u.training_metrics.get("loss", float('inf')) for u in updates]

            # Convert losses to performance scores (lower loss = higher score)
            max_loss = max(losses) if losses else 1.0
            performance_scores = [max_loss - loss + 0.1 for loss in losses]  # +0.1 to avoid zero
            total_score = sum(performance_scores)

            return [score / total_score for score in performance_scores]

        elif strategy == "reputation":
            # Weight by node reputation (if available)
            # This would require access to node registry - simplified for now
            return [1.0 / len(updates)] * len(updates)

        else:
            raise ValueError(f"Unknown weighting strategy: {strategy}")

    def _weighted_average_aggregation(
        self,
        updates: List[TrainingUpdate],
        weights: List[float]
    ) -> Dict[str, Any]:
        """Perform weighted average aggregation"""

        if len(updates) != len(weights):
            raise ValueError("Mismatch between updates and weights")

        # Initialize aggregated weights with zeros
        aggregated = {}
        reference_update = updates[0]

        for layer_name, layer_weights in reference_update.model_weights.items():
            aggregated[layer_name] = self._create_zero_tensor_like(layer_weights)

        # Aggregate weights
        for update, weight in zip(updates, weights):
            for layer_name, layer_weights in update.model_weights.items():
                aggregated[layer_name] = self._add_weighted_tensor(
                    aggregated[layer_name],
                    layer_weights,
                    weight
                )

        return aggregated

    def _get_tensor_shape(self, tensor: Union[List, float, int]) -> tuple:
        """Get shape of tensor (nested list structure)"""
        if isinstance(tensor, (int, float)):
            return ()
        elif isinstance(tensor, list):
            if not tensor:
                return (0,)
            elif isinstance(tensor[0], (int, float)):
                return (len(tensor),)
            else:
                # Assume all sublists have same length
                return (len(tensor),) + self._get_tensor_shape(tensor[0])
        else:
            raise ValueError(f"Unsupported tensor type: {type(tensor)}")

    def _calculate_weight_magnitude(self, weights: Any) -> float:
        """Calculate magnitude of weight tensor"""
        if isinstance(weights, (int, float)):
            return abs(weights)
        elif isinstance(weights, list):
            if not weights:
                return 0.0
            elif isinstance(weights[0], (int, float)):
                return sum(abs(w) for w in weights)
            else:
                return sum(self._calculate_weight_magnitude(w) for w in weights)
        else:
            return 0.0

    def _create_zero_tensor_like(self, tensor: Any) -> Any:
        """Create zero tensor with same structure"""
        if isinstance(tensor, (int, float)):
            return 0.0
        elif isinstance(tensor, list):
            return [self._create_zero_tensor_like(item) for item in tensor]
        else:
            raise ValueError(f"Unsupported tensor type: {type(tensor)}")

    def _add_weighted_tensor(self, target: Any, source: Any, weight: float) -> Any:
        """Add weighted source tensor to target tensor"""
        if isinstance(target, (int, float)) and isinstance(source, (int, float)):
            return target + source * weight
        elif isinstance(target, list) and isinstance(source, list):
            if len(target) != len(source):
                raise ValueError("Tensor dimension mismatch")
            return [
                self._add_weighted_tensor(t, s, weight)
                for t, s in zip(target, source)
            ]
        else:
            raise ValueError("Tensor type mismatch")

    def compress_model(self, weights: Dict[str, Any], method: str = "quantization", bits: int = 8) -> str:
        """Compress model weights for efficient transmission"""

        if method == "quantization":
            # Quantize weights to reduce precision
            quantized = {}
            for layer_name, layer_weights in weights.items():
                quantized[layer_name] = self._quantize_weights(layer_weights, bits)

            # Serialize and compress
            serialized = json.dumps(quantized)
            compressed = gzip.compress(serialized.encode())
            return base64.b64encode(compressed).decode()

        elif method == "sparsification":
            # Remove small weights (magnitude below threshold)
            threshold = 0.001
            sparsified = {}
            for layer_name, layer_weights in weights.items():
                sparsified[layer_name] = self._sparsify_weights(layer_weights, threshold)

            serialized = json.dumps(sparsified)
            compressed = gzip.compress(serialized.encode())
            return base64.b64encode(compressed).decode()

        else:
            raise ValueError(f"Unknown compression method: {method}")

    def decompress_model(self, compressed_data: str) -> Dict[str, Any]:
        """Decompress model weights"""
        try:
            compressed_bytes = base64.b64decode(compressed_data.encode())
            decompressed = gzip.decompress(compressed_bytes)
            return json.loads(decompressed.decode())
        except Exception as e:
            raise ValueError(f"Failed to decompress model: {e}")

    def _quantize_weights(self, weights: Any, bits: int) -> Any:
        """Quantize weights to specified bit precision"""
        if isinstance(weights, (int, float)):
            # Quantize scalar value
            max_val = 2**(bits-1) - 1
            min_val = -2**(bits-1)
            quantized = round(weights * max_val)
            return max(min_val, min(max_val, quantized)) / max_val

        elif isinstance(weights, list):
            return [self._quantize_weights(w, bits) for w in weights]
        else:
            return weights

    def _sparsify_weights(self, weights: Any, threshold: float) -> Any:
        """Remove weights below threshold magnitude"""
        if isinstance(weights, (int, float)):
            return weights if abs(weights) >= threshold else 0.0
        elif isinstance(weights, list):
            return [self._sparsify_weights(w, threshold) for w in weights]
        else:
            return weights


class FederatedAveraging(ModelAggregator):
    """Federated Averaging (FedAvg) algorithm"""

    def __init__(self):
        super().__init__()

    def aggregate(
        self,
        updates: List[TrainingUpdate],
        weighting_strategy: str = "samples",
        exclude_byzantine: bool = True
    ) -> Dict[str, Any]:
        """
        Federated Averaging with sample-based weighting

        Classic FedAvg algorithm where updates are weighted by
        the number of local training samples.
        """
        return super().aggregate(updates, weighting_strategy, exclude_byzantine)


class SecureAggregation(ModelAggregator):
    """Secure aggregation with privacy preservation"""

    def __init__(self):
        super().__init__()
        self.noise_scale = 0.001  # Differential privacy noise

    def aggregate(
        self,
        updates: List[TrainingUpdate],
        weighting_strategy: str = "equal",
        add_noise: bool = True
    ) -> Dict[str, Any]:
        """
        Secure aggregation with differential privacy

        Adds calibrated noise to protect individual contributions
        """
        # Standard aggregation
        aggregated = super().aggregate(updates, weighting_strategy, exclude_byzantine=True)

        if add_noise:
            # Add differential privacy noise
            aggregated = self._add_dp_noise(aggregated)

        return aggregated

    def _add_dp_noise(self, weights: Dict[str, Any]) -> Dict[str, Any]:
        """Add differential privacy noise to aggregated weights"""
        import random

        noisy_weights = {}

        for layer_name, layer_weights in weights.items():
            noisy_weights[layer_name] = self._add_noise_to_tensor(layer_weights)

        return noisy_weights

    def _add_noise_to_tensor(self, tensor: Any) -> Any:
        """Add Gaussian noise to tensor"""
        import random

        if isinstance(tensor, (int, float)):
            noise = random.gauss(0, self.noise_scale)
            return tensor + noise
        elif isinstance(tensor, list):
            return [self._add_noise_to_tensor(item) for item in tensor]
        else:
            return tensor


class RobustAggregation(ModelAggregator):
    """Robust aggregation resistant to Byzantine attacks"""

    def __init__(self):
        super().__init__()

    def aggregate(
        self,
        updates: List[TrainingUpdate],
        weighting_strategy: str = "equal",
        robustness_method: str = "coordinate_wise_median"
    ) -> Dict[str, Any]:
        """
        Robust aggregation using coordinate-wise median or trimmed mean

        More resistant to Byzantine attacks than simple averaging
        """
        if not updates:
            raise ValueError("No updates provided")

        if len(updates) < 3:
            logger.warning("Robust aggregation requires at least 3 updates, falling back to standard aggregation")
            return super().aggregate(updates, weighting_strategy)

        if robustness_method == "coordinate_wise_median":
            return self._coordinate_wise_median(updates)
        elif robustness_method == "trimmed_mean":
            return self._trimmed_mean_aggregation(updates, trim_ratio=0.2)
        else:
            raise ValueError(f"Unknown robustness method: {robustness_method}")

    def _coordinate_wise_median(self, updates: List[TrainingUpdate]) -> Dict[str, Any]:
        """Aggregate using coordinate-wise median"""
        aggregated = {}
        reference_update = updates[0]

        for layer_name in reference_update.model_weights.keys():
            # Collect all values for this layer across updates
            layer_values = [update.model_weights[layer_name] for update in updates]
            aggregated[layer_name] = self._median_tensor(layer_values)

        return aggregated

    def _trimmed_mean_aggregation(
        self,
        updates: List[TrainingUpdate],
        trim_ratio: float = 0.2
    ) -> Dict[str, Any]:
        """Aggregate using trimmed mean (remove outliers)"""
        aggregated = {}
        reference_update = updates[0]

        for layer_name in reference_update.model_weights.keys():
            layer_values = [update.model_weights[layer_name] for update in updates]
            aggregated[layer_name] = self._trimmed_mean_tensor(layer_values, trim_ratio)

        return aggregated

    def _median_tensor(self, tensor_list: List[Any]) -> Any:
        """Calculate coordinate-wise median of tensors"""
        if not tensor_list:
            raise ValueError("Empty tensor list")

        if isinstance(tensor_list[0], (int, float)):
            return statistics.median(tensor_list)
        elif isinstance(tensor_list[0], list):
            # Recursive median for each position
            length = len(tensor_list[0])
            result = []
            for i in range(length):
                position_values = [tensor[i] for tensor in tensor_list]
                result.append(self._median_tensor(position_values))
            return result
        else:
            raise ValueError("Unsupported tensor type")

    def _trimmed_mean_tensor(self, tensor_list: List[Any], trim_ratio: float) -> Any:
        """Calculate coordinate-wise trimmed mean of tensors"""
        if not tensor_list:
            raise ValueError("Empty tensor list")

        if isinstance(tensor_list[0], (int, float)):
            values = sorted(tensor_list)
            trim_count = int(len(values) * trim_ratio / 2)
            if trim_count > 0:
                values = values[trim_count:-trim_count]
            return sum(values) / len(values) if values else 0.0

        elif isinstance(tensor_list[0], list):
            length = len(tensor_list[0])
            result = []
            for i in range(length):
                position_values = [tensor[i] for tensor in tensor_list]
                result.append(self._trimmed_mean_tensor(position_values, trim_ratio))
            return result
        else:
            raise ValueError("Unsupported tensor type")


# Factory function for creating aggregators
def create_aggregator(algorithm: str = "federated_averaging") -> ModelAggregator:
    """Create model aggregator instance"""

    if algorithm == "federated_averaging":
        return FederatedAveraging()
    elif algorithm == "secure_aggregation":
        return SecureAggregation()
    elif algorithm == "robust_aggregation":
        return RobustAggregation()
    else:
        raise ValueError(f"Unknown aggregation algorithm: {algorithm}")


# Testing and validation functions
def test_aggregation_algorithms():
    """Test different aggregation algorithms"""
    print("🧮 Testing Model Aggregation Algorithms")
    print("=" * 40)

    # Create mock training updates
    mock_updates = [
        TrainingUpdate(
            node_id=f"node-{i}",
            round_id="test-round",
            model_weights={
                "layer1.weight": [[1.0 + i*0.1, 2.0 + i*0.1], [3.0 + i*0.1, 4.0 + i*0.1]],
                "layer1.bias": [0.1 + i*0.01, 0.2 + i*0.01]
            },
            training_metrics={
                "loss": 2.5 - i*0.1,
                "samples_trained": 1000 + i*200
            },
            update_size_mb=10.0
        ) for i in range(5)
    ]

    # Test different algorithms
    algorithms = ["federated_averaging", "secure_aggregation", "robust_aggregation"]

    for algorithm in algorithms:
        print(f"\n🔄 Testing {algorithm}:")
        aggregator = create_aggregator(algorithm)

        try:
            result = aggregator.aggregate(mock_updates)
            print(f"  ✅ Aggregation successful")
            print(f"  📊 Layer1 weight[0][0]: {result['layer1.weight'][0][0]:.4f}")
            print(f"  📊 Layer1 bias[0]: {result['layer1.bias'][0]:.4f}")

        except Exception as e:
            print(f"  ❌ Aggregation failed: {e}")

    print("\n✨ Aggregation testing complete")


if __name__ == "__main__":
    test_aggregation_algorithms()