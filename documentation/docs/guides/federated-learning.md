# Federated Learning Guide

SolanaLM supports advanced federated learning for privacy-preserving model training across distributed nodes.

## Overview

Federated Learning (FL) enables training machine learning models without centralizing data:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Node A    │    │   Node B    │    │   Node C    │
│  Local Data │    │  Local Data │    │  Local Data │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       │   Local Training │                  │
       ▼                  ▼                  ▼
┌──────────────────────────────────────────────────┐
│              Training Coordinator                │
│         Aggregates Model Updates                 │
└──────────────────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Global Model  │
              └───────────────┘
```

**Benefits:**

- Data never leaves the node
- Privacy-preserving by design
- Supports heterogeneous data
- Fault-tolerant training

## Supported Algorithms

### FedAvg (Federated Averaging)

The standard FL algorithm. Simple and effective.

```python
from core.training.federation import FederatedTrainer, FLAlgorithm

trainer = FederatedTrainer(
    algorithm=FLAlgorithm.FEDAVG,
    aggregation_strategy="weighted_average"
)
```

### FedProx

Handles heterogeneous data distributions better than FedAvg.

```python
trainer = FederatedTrainer(
    algorithm=FLAlgorithm.FEDPROX,
    proximal_mu=0.01  # Proximal term weight
)
```

### SCAFFOLD

Reduces variance in gradient updates, faster convergence.

```python
trainer = FederatedTrainer(
    algorithm=FLAlgorithm.SCAFFOLD,
    server_learning_rate=1.0
)
```

### FedAdam

Adaptive optimization for federated settings.

```python
trainer = FederatedTrainer(
    algorithm=FLAlgorithm.FEDADAM,
    server_lr=0.01,
    beta1=0.9,
    beta2=0.99
)
```

## Participating as a Training Node

### Setup

1. Start a training node:

```bash
python scripts/run_node.py \
    --node-type training \
    --node-id training-1 \
    --wallet YOUR_WALLET
```

2. Configure training parameters:

```python
from core.nodes.training.node import TrainingNode

node = TrainingNode(
    node_id="training-1",
    wallet_address="YourWallet",
    gateway_url="http://localhost:8001",
    port=8200,

    # Training config
    local_epochs=5,
    learning_rate=0.01,
    batch_size=32,
    optimizer="adam"
)
```

### Joining a Training Round

```python
async with SolanaLMClient(gateway_url) as client:
    result = await client.join_training_round(
        model_name="target-model",
        node_capabilities={
            "compute_power": "high",
            "data_samples": 1000,
            "gpu_available": True
        },
        reward_expectation=0.01  # SOL
    )

    print(f"Joined round: {result['round_id']}")
```

### Training Lifecycle

```
1. Registration    → Node registers capabilities with coordinator
2. Selection       → Coordinator selects participating nodes
3. Model Download  → Nodes download current global model
4. Local Training  → Nodes train on local data
5. Update Upload   → Nodes send model updates (not data!)
6. Aggregation     → Coordinator aggregates updates
7. Reward          → Nodes receive SOL payment
```

## Configuring Training Rounds

### As a Coordinator

```python
from core.coordinator.training_coordinator import TrainingCoordinator

coordinator = TrainingCoordinator(
    model_name="custom-llm",
    min_nodes=3,
    max_nodes=10,
    rounds=100,

    # Aggregation settings
    aggregation_algorithm=FLAlgorithm.FEDAVG,
    client_fraction=0.5,  # 50% of nodes per round

    # Quality control
    min_samples_per_client=100,
    max_staleness=2,  # Rounds behind allowed
)

await coordinator.start_training()
```

### Round Configuration

```python
round_config = {
    "model_name": "custom-model",
    "target_rounds": 100,
    "min_participants": 3,

    # Scheduling
    "round_timeout": 300,  # 5 minutes
    "rounds_per_epoch": 10,

    # Rewards
    "total_reward_pool": 10.0,  # SOL
    "reward_per_round": 0.1,

    # Quality
    "require_validation": True,
    "validation_fraction": 0.2
}
```

## Privacy Features

### Differential Privacy

Add noise to protect individual data points:

```python
node = TrainingNode(
    ...
    enable_differential_privacy=True,
    noise_multiplier=1.0,
    max_grad_norm=1.0,
    target_epsilon=8.0,
    target_delta=1e-5
)
```

### Secure Aggregation

Encrypt model updates so coordinator can't see individual contributions:

```python
coordinator = TrainingCoordinator(
    ...
    secure_aggregation=True,
    encryption_threshold=0.6  # 60% of nodes needed to decrypt
)
```

### Privacy Budget Tracking

```python
# Check privacy budget
privacy_status = await node.get_privacy_status()
print(f"Epsilon spent: {privacy_status['epsilon_spent']}")
print(f"Budget remaining: {privacy_status['epsilon_remaining']}")
```

## Handling Non-IID Data

Real-world data is often non-identically distributed across nodes.

### Data Distribution Strategies

```python
node = TrainingNode(
    ...
    # Handle class imbalance
    use_class_balanced_sampling=True,

    # Local data augmentation
    enable_augmentation=True,

    # Regularization
    weight_decay=0.01,
    dropout_rate=0.1
)
```

### Algorithm Selection for Non-IID

| Data Distribution | Recommended Algorithm |
|-------------------|----------------------|
| IID (uniform) | FedAvg |
| Mild non-IID | FedProx |
| Severe non-IID | SCAFFOLD |
| Adaptive | FedAdam |

## Model Aggregation

### Weighted Aggregation

```python
from core.training.model_aggregation import ModelAggregator

aggregator = ModelAggregator(
    strategy="weighted",
    weight_by="data_size"  # or "compute_time", "validation_accuracy"
)

global_model = aggregator.aggregate(
    models=[model1, model2, model3],
    weights=[1000, 500, 750]  # Data samples per node
)
```

### Quality-Based Selection

```python
aggregator = ModelAggregator(
    strategy="quality_filtered",
    min_accuracy=0.7,
    max_loss_increase=0.1
)
```

## Monitoring Training

### Training Status

```python
async with SolanaLMClient(gateway_url) as client:
    status = await client.get_training_status()

    print(f"Current round: {status['current_round']}")
    print(f"Participants: {status['participating_nodes']}")
    print(f"Global loss: {status['global_loss']}")
    print(f"Convergence: {status['convergence_rate']}")
```

### Metrics Dashboard

Access training metrics at `http://localhost:8080/training`:

- Round progress
- Loss curves
- Node participation
- Convergence metrics
- Reward distribution

## Fault Tolerance

### Handling Node Failures

```python
coordinator = TrainingCoordinator(
    ...
    # Retry settings
    max_retries=3,
    retry_delay=30,

    # Timeout handling
    round_timeout=300,
    node_timeout=60,

    # Minimum completion
    min_completion_rate=0.6  # 60% nodes must complete
)
```

### Checkpoint Management

```python
coordinator = TrainingCoordinator(
    ...
    checkpoint_frequency=5,  # Every 5 rounds
    checkpoint_path="./checkpoints/",
    keep_last_n_checkpoints=3
)
```

## Rewards and Incentives

### Earning Structure

```python
rewards = {
    "base_reward": 0.001,      # SOL per round
    "quality_bonus": 0.0005,   # For high-quality updates
    "speed_bonus": 0.0002,     # For fast completion
    "consistency_bonus": 0.001  # For consistent participation
}
```

### Checking Earnings

```python
async with SolanaLMClient(gateway_url) as client:
    earnings = await client.get_training_earnings(
        wallet_address="YourWallet",
        period="last_30_days"
    )

    print(f"Rounds participated: {earnings['rounds']}")
    print(f"Total earned: {earnings['total_sol']} SOL")
    print(f"Avg reward/round: {earnings['avg_per_round']} SOL")
```

## Best Practices

### Data Preparation

- Ensure consistent preprocessing across nodes
- Validate data quality before training
- Handle missing values uniformly

### Resource Management

- Monitor GPU memory during training
- Set appropriate batch sizes
- Use gradient accumulation for large models

### Communication Efficiency

- Compress model updates
- Use sparse gradients when possible
- Batch communication rounds

## Example: Complete Training Setup

```python
import asyncio
from core.nodes.training.node import TrainingNode
from core.training.federation import FederatedTrainer, FLAlgorithm

async def run_training_node():
    # Initialize node
    node = TrainingNode(
        node_id="my-training-node",
        wallet_address="MyWallet",
        gateway_url="http://localhost:8001",
        port=8200,

        # Training config
        local_epochs=5,
        learning_rate=0.01,
        batch_size=32,

        # Privacy
        enable_differential_privacy=True,
        noise_multiplier=0.5
    )

    # Initialize
    await node.initialize()

    # Start running (will automatically join rounds)
    await node.run()

if __name__ == "__main__":
    asyncio.run(run_training_node())
```

## Next Steps

- [Privacy Features](privacy.md) - Deep dive into privacy
- [Architecture Overview](../architecture/overview.md) - System design
- [Production Deployment](../deployment/production.md) - Scale your nodes
