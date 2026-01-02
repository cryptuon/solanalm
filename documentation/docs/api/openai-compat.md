# OpenAI Compatibility

SolanaLM provides an OpenAI-compatible API, allowing you to use existing OpenAI client libraries.

## Overview

The compatibility layer maps OpenAI API calls to SolanaLM's infrastructure:

- Use your existing OpenAI SDK code
- Drop-in replacement for OpenAI API
- Automatic model routing
- Cost savings with decentralized inference

## Quick Start

### Using the OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="your-solana-wallet-address"
)

response = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Using the SolanaLM Compatibility Client

```python
from client.python.openai_compat import OpenAICompatibleClient

client = OpenAICompatibleClient(
    base_url="http://localhost:8001/v1",
    api_key="your-solana-wallet-address"
)

response = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## Endpoint Mapping

| OpenAI Endpoint | SolanaLM Endpoint | Status |
|-----------------|-------------------|--------|
| `/v1/chat/completions` | `/v1/chat/completions` | Supported |
| `/v1/completions` | `/v1/completions` | Supported |
| `/v1/models` | `/v1/models` | Supported |
| `/v1/embeddings` | `/v1/embeddings` | Planned |

## Chat Completions

### Basic Usage

```python
response = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)
```

### With Parameters

```python
response = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
    max_tokens=100,
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0
)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Text Completions (Legacy)

```python
response = client.completions.create(
    model="gpt2",
    prompt="Once upon a time",
    max_tokens=50,
    temperature=0.7
)

print(response.choices[0].text)
```

## Model Listing

```python
models = client.models.list()

for model in models.data:
    print(f"- {model.id}")
```

## Response Format

Responses follow the OpenAI format:

### Chat Completion Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1705312800,
  "model": "microsoft/DialoGPT-small",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}
```

### Extended Fields

SolanaLM adds extra fields:

```json
{
  "...": "standard OpenAI fields",
  "solanalm": {
    "cost_sol": 0.000018,
    "node_id": "inference-node-1",
    "processing_time": 0.234
  }
}
```

## Model Mapping

Map OpenAI model names to SolanaLM models:

```python
MODEL_MAP = {
    "gpt-3.5-turbo": "microsoft/DialoGPT-medium",
    "gpt-4": "proxy:openai:gpt-4",
    "text-davinci-003": "gpt2-large"
}
```

Use proxy nodes for actual OpenAI models:

```python
# Routes to OpenAI via proxy node
response = client.chat.completions.create(
    model="proxy:openai:gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Authentication

The API key is your Solana wallet address:

```python
client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="YourSolanaWalletAddress"  # Used for payments
)
```

For additional security:

```python
client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="YourWalletAddress",
    default_headers={
        "X-Signature": "wallet-signature"  # Optional: wallet signature
    }
)
```

## Error Handling

Errors follow OpenAI format:

```python
from openai import OpenAIError, RateLimitError, APIError

try:
    response = client.chat.completions.create(...)
except RateLimitError:
    print("Rate limited, waiting...")
except APIError as e:
    print(f"API error: {e}")
except OpenAIError as e:
    print(f"OpenAI error: {e}")
```

### SolanaLM-Specific Errors

```python
try:
    response = client.chat.completions.create(...)
except APIError as e:
    if "insufficient_funds" in str(e):
        print("Need more SOL in wallet")
    elif "no_nodes_available" in str(e):
        print("No nodes can serve this model")
```

## Cost Tracking

Track costs with the extended response:

```python
response = client.chat.completions.create(...)

# Standard usage
print(f"Tokens: {response.usage.total_tokens}")

# SolanaLM cost
if hasattr(response, 'solanalm'):
    print(f"Cost: {response.solanalm['cost_sol']} SOL")
```

## LangChain Integration

```python
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8001/v1",
    api_key="your-wallet-address",
    model="microsoft/DialoGPT-small"
)

response = llm.invoke("Hello!")
print(response.content)
```

## LlamaIndex Integration

```python
from llama_index.llms import OpenAI

llm = OpenAI(
    api_base="http://localhost:8001/v1",
    api_key="your-wallet-address",
    model="microsoft/DialoGPT-small"
)

response = llm.complete("Hello!")
print(response.text)
```

## Differences from OpenAI

| Feature | OpenAI | SolanaLM |
|---------|--------|----------|
| Payment | Credit card | SOL |
| Models | OpenAI models | Network models |
| Latency | ~100ms | ~100-500ms |
| Privacy | Centralized | Decentralized option |
| Uptime | 99.9% SLA | Best effort |

## Migration Guide

### From OpenAI

```python
# Before (OpenAI)
from openai import OpenAI
client = OpenAI(api_key="sk-...")

# After (SolanaLM)
from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:8001/v1",
    api_key="your-wallet"
)

# Rest of code stays the same!
```

### Handling Both

```python
import os
from openai import OpenAI

USE_SOLANALM = os.getenv("USE_SOLANALM", "false").lower() == "true"

if USE_SOLANALM:
    client = OpenAI(
        base_url="http://localhost:8001/v1",
        api_key=os.getenv("SOLANA_WALLET")
    )
else:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Same code works for both
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # Mapped to SolanaLM model
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Next Steps

- [Python SDK](client-sdk.md) - Full SDK reference
- [Gateway API](gateway.md) - REST API documentation
- [Running Nodes](../guides/running-nodes.md) - Contribute to the network
