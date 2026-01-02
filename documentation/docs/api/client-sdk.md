# Client SDK Reference

Complete reference for the SolanaLM Python SDK.

## Installation

```bash
# Included with SolanaLM
poetry install

# Or standalone
pip install solanalm-client
```

## Classes

### SolanaLMClient

Async client for the SolanaLM network.

```python
from client.python.solanalm_client import SolanaLMClient
```

#### Constructor

```python
SolanaLMClient(gateway_url: str = "http://localhost:8001")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gateway_url` | str | `http://localhost:8001` | Gateway URL |

#### Context Manager Usage

```python
async with SolanaLMClient("http://localhost:8001") as client:
    # Client is initialized and ready
    response = await client.inference(...)
# Client is automatically closed
```

---

### Methods

#### inference()

Submit an inference request.

```python
async def inference(
    self,
    model: str,
    prompt: str,
    wallet_address: str,
    max_tokens: int = 100,
    temperature: float = 0.7,
    top_p: float = 0.9,
    metadata: Optional[Dict[str, Any]] = None
) -> InferenceResponse
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | Required | Model identifier |
| `prompt` | str | Required | Input prompt |
| `wallet_address` | str | Required | Payment wallet |
| `max_tokens` | int | 100 | Max tokens to generate |
| `temperature` | float | 0.7 | Sampling temperature |
| `top_p` | float | 0.9 | Nucleus sampling |
| `metadata` | dict | None | Custom metadata |

**Returns:** `InferenceResponse`

**Example:**

```python
response = await client.inference(
    model="microsoft/DialoGPT-small",
    prompt="Hello!",
    wallet_address="my-wallet",
    max_tokens=50,
    temperature=0.8
)
print(response.response)
```

---

#### private_inference()

Privacy-preserving inference with onion routing.

```python
async def private_inference(
    self,
    model: str,
    prompt: str,
    wallet_address: str,
    privacy_level: str = "standard",
    **kwargs
) -> InferenceResponse
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `privacy_level` | str | `standard` | `standard` or `high` |
| Other params | - | - | Same as `inference()` |

**Example:**

```python
response = await client.private_inference(
    model="microsoft/DialoGPT-small",
    prompt="Sensitive query",
    wallet_address="my-wallet",
    privacy_level="high"
)
```

---

#### batch_inference()

Process multiple prompts concurrently.

```python
async def batch_inference(
    self,
    model: str,
    prompts: List[str],
    wallet_address: str,
    max_concurrent: int = 5,
    **kwargs
) -> List[InferenceResponse]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompts` | List[str] | Required | List of prompts |
| `max_concurrent` | int | 5 | Concurrent limit |
| Other params | - | - | Same as `inference()` |

**Example:**

```python
responses = await client.batch_inference(
    model="microsoft/DialoGPT-small",
    prompts=["Hello", "Hi", "Hey"],
    wallet_address="my-wallet",
    max_concurrent=3
)
for r in responses:
    print(r.response)
```

---

#### stream_batch_inference()

Stream results as they complete.

```python
async def stream_batch_inference(
    self,
    model: str,
    prompts: List[str],
    wallet_address: str,
    **kwargs
) -> AsyncGenerator[InferenceResponse, None]
```

**Example:**

```python
async for response in client.stream_batch_inference(
    model="microsoft/DialoGPT-small",
    prompts=prompts,
    wallet_address="my-wallet"
):
    print(f"Got: {response.response}")
```

---

#### list_available_models()

Get available models.

```python
async def list_available_models(self) -> List[str]
```

**Returns:** List of model identifiers

**Example:**

```python
models = await client.list_available_models()
print(models)  # ["microsoft/DialoGPT-small", "gpt2", ...]
```

---

#### get_network_status()

Get network status.

```python
async def get_network_status(self) -> Dict[str, Any]
```

**Returns:**

```python
{
    "service": "SolanaLM Gateway",
    "version": "1.0.0",
    "network_stats": {
        "total_nodes": 15,
        "active_nodes": 12,
        ...
    }
}
```

---

#### get_network_health()

Get health metrics.

```python
async def get_network_health(self) -> Dict[str, Any]
```

---

#### get_training_status()

Get federated learning status.

```python
async def get_training_status(self) -> Dict[str, Any]
```

**Returns:**

```python
{
    "active_rounds": 1,
    "participating_nodes": 5,
    "next_round_start": "2024-01-15T11:00:00Z"
}
```

---

#### join_training_round()

Join a training round.

```python
async def join_training_round(
    self,
    model_name: str,
    node_capabilities: Dict[str, Any],
    reward_expectation: float = 0.0
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_name` | str | Target model |
| `node_capabilities` | dict | Node capabilities |
| `reward_expectation` | float | Expected SOL reward |

---

#### start_custom_training()

Start custom training.

```python
async def start_custom_training(
    self,
    config: Dict[str, Any],
    wallet_address: str
) -> Dict[str, Any]
```

---

#### get_usage_analytics()

Get usage statistics.

```python
async def get_usage_analytics(
    self,
    wallet_address: str,
    period: str = "last_7_days"
) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Options |
|-----------|------|---------|
| `period` | str | `last_7_days`, `last_30_days`, `all_time` |

---

#### get_privacy_metrics()

Get privacy network metrics.

```python
async def get_privacy_metrics(self) -> Dict[str, Any]
```

**Returns:**

```python
{
    "anonymity_set_size": 50,
    "circuit_diversity_score": 0.85,
    "geographic_coverage": 5
}
```

---

#### get_circuit_info()

Get circuit info for a private request.

```python
async def get_circuit_info(self, request_id: str) -> Dict[str, Any]
```

---

#### configure_webhook()

Configure event webhooks.

```python
async def configure_webhook(
    self,
    webhook_config: Dict[str, Any]
) -> Dict[str, Any]
```

---

### SolanaLMSyncClient

Synchronous wrapper for simpler usage.

```python
from client.python.solanalm_client import SolanaLMSyncClient

client = SolanaLMSyncClient("http://localhost:8001")
response = client.inference(...)
```

#### Methods

| Method | Description |
|--------|-------------|
| `inference()` | Sync inference |
| `list_available_models()` | Sync model list |
| `get_network_status()` | Sync status |

---

## Data Classes

### InferenceRequest

```python
@dataclass
class InferenceRequest:
    model: str
    prompt: str
    wallet_address: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.9
    metadata: Optional[Dict[str, Any]] = None
```

### InferenceResponse

```python
@dataclass
class InferenceResponse:
    request_id: str
    model: str
    response: str
    processing_time: float
    tokens_generated: int
    cost_sol: float
    node_id: str
```

---

## Exceptions

### RuntimeError

Raised when client not initialized:

```python
try:
    response = await client.inference(...)
except RuntimeError as e:
    print("Use async context manager")
```

### Exception

General request failures:

```python
try:
    response = await client.inference(...)
except Exception as e:
    print(f"Request failed: {e}")
```

---

## Type Hints

```python
from typing import Dict, Any, List, Optional
from client.python.solanalm_client import (
    SolanaLMClient,
    InferenceRequest,
    InferenceResponse
)

async def example(client: SolanaLMClient) -> InferenceResponse:
    return await client.inference(
        model="model",
        prompt="prompt",
        wallet_address="wallet"
    )
```

---

## Complete Example

```python
import asyncio
from client.python.solanalm_client import SolanaLMClient

async def main():
    async with SolanaLMClient("http://localhost:8001") as client:
        # Check network
        status = await client.get_network_status()
        print(f"Network: {status['service']}")

        # List models
        models = await client.list_available_models()
        print(f"Models: {models}")

        if not models:
            print("No models available")
            return

        # Single inference
        response = await client.inference(
            model=models[0],
            prompt="Hello, world!",
            wallet_address="my-wallet"
        )
        print(f"Response: {response.response}")
        print(f"Cost: {response.cost_sol} SOL")

        # Batch inference
        prompts = ["Question 1?", "Question 2?", "Question 3?"]
        responses = await client.batch_inference(
            model=models[0],
            prompts=prompts,
            wallet_address="my-wallet"
        )
        for i, r in enumerate(responses):
            print(f"{i+1}: {r.response[:50]}...")

        # Private inference
        private_response = await client.private_inference(
            model=models[0],
            prompt="Sensitive query",
            wallet_address="my-wallet",
            privacy_level="high"
        )
        print(f"Private: {private_response.response}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- [OpenAI Compatibility](openai-compat.md) - Use OpenAI SDK
- [Gateway API](gateway.md) - REST API reference
