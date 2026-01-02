# Privacy Features

SolanaLM provides comprehensive privacy features for sensitive AI workloads.

## Privacy Overview

SolanaLM implements multiple privacy layers:

| Layer | Feature | Protection |
|-------|---------|------------|
| **Network** | Onion Routing | Hides request origin |
| **Payment** | Anonymous Payments | Breaks payment correlation |
| **Training** | Differential Privacy | Protects training data |
| **Inference** | End-to-End Encryption | Secures request content |

## Onion Routing

Tor-like multi-hop encryption that hides request origin and destination.

### How It Works

```
Client → Entry Node → Relay Node → Exit Node → Destination
         (Layer 3)    (Layer 2)    (Layer 1)

Each hop only knows:
- Previous hop
- Next hop
- Nothing about origin or final destination
```

### Using Private Inference

```python
from client.python.solanalm_client import SolanaLMClient

async with SolanaLMClient("http://localhost:8001") as client:
    response = await client.private_inference(
        model="microsoft/DialoGPT-small",
        prompt="Sensitive business query",
        wallet_address="your-wallet",
        privacy_level="standard"  # or "high"
    )
```

### Privacy Levels

| Level | Circuit Length | Latency | Anonymity |
|-------|---------------|---------|-----------|
| `standard` | 3 hops | ~500ms | Good |
| `high` | 5 hops | ~1000ms | Excellent |

### Circuit Configuration

```python
# Custom circuit configuration
response = await client.private_inference(
    model="microsoft/DialoGPT-small",
    prompt="query",
    wallet_address="wallet",
    privacy_level="high",
    circuit_config={
        "min_hops": 5,
        "max_hops": 7,
        "prefer_diverse_regions": True,
        "exclude_nodes": ["untrusted-node-1"]
    }
)
```

## Anonymous Payments

Break the correlation between requests and payments.

### Payment Mixing

```python
from core.privacy.anonymous_payments import AnonymousPaymentManager

payment_manager = AnonymousPaymentManager(
    mixing_pool_size=100,
    mixing_rounds=3,
    delay_range=(10, 60)  # Random delay in seconds
)

# Submit anonymous payment
tx_id = await payment_manager.pay_anonymously(
    amount=0.01,
    recipient="destination-wallet",
    source_wallet="your-wallet"
)
```

### Payment Privacy Modes

```python
# Standard - fast but traceable
await client.inference(..., payment_mode="standard")

# Mixed - adds delay, breaks direct correlation
await client.inference(..., payment_mode="mixed")

# Anonymous - full mixing pool, maximum privacy
await client.inference(..., payment_mode="anonymous")
```

## Differential Privacy in Training

Protect individual data points during federated learning.

### Enabling DP

```python
from core.nodes.training.node import TrainingNode

node = TrainingNode(
    node_id="private-trainer",
    wallet_address="wallet",
    gateway_url="http://localhost:8001",

    # Differential Privacy settings
    enable_differential_privacy=True,
    noise_multiplier=1.0,
    max_grad_norm=1.0,
    target_epsilon=8.0,
    target_delta=1e-5
)
```

### Privacy Budget

```python
# Monitor privacy budget
status = await node.get_privacy_status()

print(f"Epsilon spent: {status['epsilon_spent']}")
print(f"Delta: {status['delta']}")
print(f"Remaining budget: {status['epsilon_remaining']}")
print(f"Rounds until budget exhausted: {status['rounds_remaining']}")
```

### Noise Calibration

| Use Case | Epsilon | Noise Multiplier | Privacy |
|----------|---------|------------------|---------|
| High privacy | ≤ 1.0 | 2.0+ | Maximum |
| Balanced | 2-8 | 1.0 | Good |
| Utility focus | > 8 | 0.5 | Moderate |

## Secure Aggregation

Encrypt model updates during federated learning.

### How It Works

```
┌─────────────────────────────────────────────────────┐
│                     Nodes                           │
│  ┌───────┐    ┌───────┐    ┌───────┐               │
│  │Node A │    │Node B │    │Node C │               │
│  │Update │    │Update │    │Update │               │
│  │  +    │    │  +    │    │  +    │               │
│  │Mask_A │    │Mask_B │    │Mask_C │               │
│  └───┬───┘    └───┬───┘    └───┬───┘               │
│      │            │            │                    │
│      └────────────┼────────────┘                    │
│                   ▼                                 │
│         ┌─────────────────┐                         │
│         │   Aggregator    │                         │
│         │ Sum of masked   │                         │
│         │ updates = Real  │  Masks cancel out!      │
│         │ aggregate       │                         │
│         └─────────────────┘                         │
└─────────────────────────────────────────────────────┘
```

### Enabling Secure Aggregation

```python
from core.coordinator.training_coordinator import TrainingCoordinator

coordinator = TrainingCoordinator(
    model_name="private-model",
    secure_aggregation=True,
    encryption_threshold=0.6,  # 60% nodes needed
    encryption_key_size=256
)
```

## Privacy Metrics

### Checking Network Privacy

```python
async with SolanaLMClient(gateway_url) as client:
    metrics = await client.get_privacy_metrics()

    print(f"Anonymity set size: {metrics['anonymity_set_size']}")
    print(f"Circuit diversity: {metrics['circuit_diversity_score']}")
    print(f"Geographic coverage: {metrics['geographic_coverage']}")
```

### Privacy Health

```python
health = await client.get_privacy_network_health()

print(f"Privacy nodes online: {health['privacy_nodes']}")
print(f"Avg circuit length: {health['avg_circuit_length']}")
print(f"Success rate: {health['privacy_success_rate']}%")
```

## Privacy Best Practices

### For Users

1. **Use private inference for sensitive queries**
   ```python
   # Sensitive data
   await client.private_inference(prompt="confidential...", ...)

   # Non-sensitive data (faster)
   await client.inference(prompt="general query...", ...)
   ```

2. **Rotate wallets for unlinkability**
   ```python
   # Use different wallets for different use cases
   work_wallet = "wallet-for-work-queries"
   personal_wallet = "wallet-for-personal"
   ```

3. **Verify circuit diversity**
   ```python
   circuit = await client.get_circuit_info(request_id)
   assert circuit['unique_regions'] >= 3
   ```

### For Node Operators

1. **Enable privacy features**
   ```python
   node = InferenceNode(
       ...
       enable_onion_routing=True,
       accept_relay_traffic=True  # Help the network
   )
   ```

2. **Maintain uptime for circuit stability**

3. **Don't log sensitive request content**
   ```python
   # Bad
   logger.info(f"Processing: {request.prompt}")

   # Good
   logger.info(f"Processing request: {request.request_id}")
   ```

### For Training Participants

1. **Always enable differential privacy**
   ```python
   node = TrainingNode(
       enable_differential_privacy=True,
       ...
   )
   ```

2. **Monitor privacy budget**
   ```python
   if privacy_status['epsilon_remaining'] < 1.0:
       logger.warning("Privacy budget nearly exhausted")
   ```

3. **Use secure aggregation when available**

## Privacy Trade-offs

### Latency vs Privacy

```
Standard inference: ~100ms
Privacy level standard: ~500ms (5x slower)
Privacy level high: ~1000ms (10x slower)
```

### Utility vs Privacy (Training)

```
No DP: 100% accuracy
ε = 8: ~95% accuracy
ε = 1: ~85% accuracy
```

### Cost vs Privacy

```
Standard: 1x cost
Mixed payments: 1.05x cost (mixing fees)
Anonymous: 1.1x cost (full anonymization)
```

## Compliance Considerations

SolanaLM privacy features help with:

- **GDPR**: Data minimization, right to be forgotten
- **HIPAA**: Protected health information handling
- **CCPA**: Consumer data privacy
- **FERPA**: Educational records privacy

!!! warning "Legal Disclaimer"

    Privacy features are tools to help protect data. Consult legal
    counsel for compliance requirements specific to your jurisdiction
    and use case.

## Troubleshooting Privacy

### Common Issues

??? question "Private inference times out"

    Circuit may have insufficient nodes. Check:
    ```python
    health = await client.get_privacy_network_health()
    if health['privacy_nodes'] < 10:
        # Not enough nodes for high-privacy circuits
        # Use privacy_level="standard" instead
    ```

??? question "Differential privacy degrades model too much"

    Lower noise multiplier:
    ```python
    node = TrainingNode(
        noise_multiplier=0.5,  # Less noise
        target_epsilon=16.0    # Higher epsilon
    )
    ```

??? question "Secure aggregation fails"

    Not enough participants:
    ```python
    # Need at least threshold % of nodes
    coordinator = TrainingCoordinator(
        encryption_threshold=0.5  # Lower threshold
    )
    ```

## Next Steps

- [Architecture Overview](../architecture/overview.md) - System design
- [Federated Learning](federated-learning.md) - Training details
- [API Reference](../api/gateway.md) - Full API documentation
