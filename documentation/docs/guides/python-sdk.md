# Python SDK Guide

The SolanaLM Python SDK provides both async and sync clients for interacting with the network.

## Installation

The SDK is included with the main SolanaLM package:

```bash
poetry install
# or
pip install -r requirements.txt
```

## Quick Start

### Async Client (Recommended)

```python
import asyncio
from client.python.solanalm_client import SolanaLMClient

async def main():
    async with SolanaLMClient("http://localhost:8001") as client:
        response = await client.inference(
            model="microsoft/DialoGPT-small",
            prompt="Hello, world!",
            wallet_address="your-wallet"
        )
        print(response.response)

asyncio.run(main())
```

### Sync Client

```python
from client.python.solanalm_client import SolanaLMSyncClient

client = SolanaLMSyncClient("http://localhost:8001")
response = client.inference(
    model="microsoft/DialoGPT-small",
    prompt="Hello, world!",
    wallet_address="your-wallet"
)
print(response.response)
```

## Client Reference

### SolanaLMClient

The async client with full functionality.

#### Initialization

```python
from client.python.solanalm_client import SolanaLMClient

# Basic initialization
client = SolanaLMClient("http://localhost:8001")

# Use as context manager (recommended)
async with SolanaLMClient("http://localhost:8001") as client:
    # Your code here
    pass
```

### Core Methods

#### inference()

Submit an inference request:

```python
response = await client.inference(
    model="microsoft/DialoGPT-small",
    prompt="Your prompt here",
    wallet_address="your-wallet-address",
    max_tokens=100,      # Maximum tokens to generate
    temperature=0.7,     # Creativity (0.0 - 1.0)
    top_p=0.9           # Nucleus sampling
)

# Response attributes
print(response.request_id)       # Unique request ID
print(response.model)            # Model used
print(response.response)         # Generated text
print(response.processing_time)  # Time in seconds
print(response.tokens_generated) # Token count
print(response.cost_sol)         # Cost in SOL
print(response.node_id)          # Processing node
```

#### private_inference()

Privacy-preserving inference with onion routing:

```python
response = await client.private_inference(
    model="microsoft/DialoGPT-small",
    prompt="Sensitive query",
    wallet_address="your-wallet",
    privacy_level="standard"  # "standard" or "high"
)
```

#### batch_inference()

Process multiple prompts concurrently:

```python
prompts = [
    "What is Python?",
    "Explain machine learning",
    "Define blockchain"
]

responses = await client.batch_inference(
    model="microsoft/DialoGPT-small",
    prompts=prompts,
    wallet_address="your-wallet",
    max_concurrent=5  # Concurrent request limit
)

for response in responses:
    print(f"{response.response[:50]}...")
```

#### stream_batch_inference()

Stream results as they complete:

```python
async for response in client.stream_batch_inference(
    model="microsoft/DialoGPT-small",
    prompts=prompts,
    wallet_address="your-wallet"
):
    print(f"Completed: {response.response[:50]}...")
```

### Network Operations

#### list_available_models()

Get all available models:

```python
models = await client.list_available_models()
for model in models:
    print(model)
```

#### get_network_status()

Check network status:

```python
status = await client.get_network_status()
print(f"Service: {status['service']}")
print(f"Version: {status['version']}")
print(f"Active nodes: {status['network_stats']['active_nodes']}")
```

#### get_network_health()

Get health metrics:

```python
health = await client.get_network_health()
print(f"Status: {health['status']}")
print(f"Gateway: {health['gateway']}")
```

### Training Operations

#### get_training_status()

Check federated learning status:

```python
status = await client.get_training_status()
print(f"Active rounds: {status['active_rounds']}")
print(f"Participants: {status['participating_nodes']}")
```

#### join_training_round()

Join a federated training round:

```python
result = await client.join_training_round(
    model_name="custom-model",
    node_capabilities={
        "compute_power": "high",
        "data_samples": 1000
    },
    reward_expectation=0.01  # Expected SOL reward
)
```

#### start_custom_training()

Start custom model training:

```python
result = await client.start_custom_training(
    config={
        "model_type": "transformer",
        "epochs": 10,
        "batch_size": 32,
        "learning_rate": 0.001
    },
    wallet_address="your-wallet"
)
```

### Privacy Operations

#### get_privacy_metrics()

Get privacy network metrics:

```python
metrics = await client.get_privacy_metrics()
print(f"Anonymity set: {metrics['anonymity_set_size']}")
print(f"Circuit diversity: {metrics['circuit_diversity_score']}")
```

#### get_circuit_info()

Get circuit info for a private request:

```python
circuit = await client.get_circuit_info(request_id)
print(f"Hops: {circuit['hop_count']}")
print(f"Latency: {circuit['total_latency']}ms")
```

### Analytics

#### get_usage_analytics()

Get usage statistics:

```python
analytics = await client.get_usage_analytics(
    wallet_address="your-wallet",
    period="last_7_days"  # or "last_30_days", "all_time"
)

print(f"Total requests: {analytics['total_requests']}")
print(f"Total cost: {analytics['total_cost']} SOL")
print(f"Avg latency: {analytics['avg_latency']}s")
```

## Data Classes

### InferenceRequest

```python
from client.python.solanalm_client import InferenceRequest

request = InferenceRequest(
    model="microsoft/DialoGPT-small",
    prompt="Hello",
    wallet_address="wallet",
    max_tokens=100,
    temperature=0.7,
    top_p=0.9,
    metadata={"custom": "data"}
)
```

### InferenceResponse

```python
from client.python.solanalm_client import InferenceResponse

# Returned from inference methods
response: InferenceResponse

response.request_id       # str: Unique request ID
response.model            # str: Model used
response.response         # str: Generated text
response.processing_time  # float: Processing time
response.tokens_generated # int: Token count
response.cost_sol         # float: Cost in SOL
response.node_id          # str: Processing node ID
```

## Error Handling

```python
import asyncio
from client.python.solanalm_client import SolanaLMClient

async def safe_inference():
    try:
        async with SolanaLMClient("http://localhost:8001") as client:
            response = await client.inference(
                model="microsoft/DialoGPT-small",
                prompt="Test",
                wallet_address="wallet"
            )
            return response

    except RuntimeError as e:
        print(f"Client not initialized: {e}")

    except Exception as e:
        print(f"Request failed: {e}")

asyncio.run(safe_inference())
```

## Best Practices

### Use Context Managers

Always use the async context manager to ensure proper cleanup:

```python
# Good
async with SolanaLMClient(url) as client:
    response = await client.inference(...)

# Avoid
client = SolanaLMClient(url)
# Session not properly managed
```

### Handle Timeouts

Configure appropriate timeouts for your use case:

```python
import aiohttp

async with SolanaLMClient(url) as client:
    # The client uses 60s timeout by default
    # For long-running tasks, handle timeouts gracefully
    try:
        response = await asyncio.wait_for(
            client.inference(...),
            timeout=120.0
        )
    except asyncio.TimeoutError:
        print("Request timed out")
```

### Batch for Performance

Use batch methods for multiple requests:

```python
# Efficient - single connection, concurrent requests
responses = await client.batch_inference(
    model=model,
    prompts=many_prompts,
    wallet_address=wallet,
    max_concurrent=10
)

# Less efficient - sequential requests
for prompt in many_prompts:
    response = await client.inference(...)
```

### Monitor Costs

Track costs for budget management:

```python
total_cost = 0.0
async with SolanaLMClient(url) as client:
    for prompt in prompts:
        response = await client.inference(...)
        total_cost += response.cost_sol

        if total_cost > budget_limit:
            print("Budget exceeded!")
            break

print(f"Total spent: {total_cost} SOL")
```

## Next Steps

- [OpenAI Compatibility](../api/openai-compat.md) - Use OpenAI SDK with SolanaLM
- [Privacy Features](privacy.md) - Learn about private inference
- [Running Nodes](running-nodes.md) - Contribute to the network
