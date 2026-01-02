# Quick Start

Get SolanaLM running in under 5 minutes.

## One-Command Setup

The fastest way to start is using the quick start script:

```bash
python scripts/quick_start.py
```

This automatically:

- Starts the gateway server
- Launches a demo inference node
- Runs basic connectivity tests

## Manual Setup

For more control, start components individually:

### Step 1: Start the Gateway

The gateway is the central API server that routes requests to nodes:

```bash
python scripts/run_gateway.py
```

You should see:

```
INFO: Gateway starting on http://localhost:8001
INFO: Node registry initialized
INFO: Training coordinator initialized
INFO: Gateway ready to accept connections
```

### Step 2: Start an Inference Node

In a new terminal, start an inference node:

```bash
python scripts/run_node.py \
    --node-type inference \
    --node-id my-node-1 \
    --wallet YOUR_WALLET_ADDRESS
```

The node will:

1. Initialize the local model
2. Register with the gateway
3. Start accepting inference requests

### Step 3: Test the System

Run the end-to-end test suite:

```bash
python scripts/test_end_to_end.py
```

Or test manually with the Python SDK:

```python
import asyncio
from client.python.solanalm_client import SolanaLMClient

async def test():
    async with SolanaLMClient("http://localhost:8001") as client:
        # Check network status
        status = await client.get_network_status()
        print(f"Network: {status}")

        # List available models
        models = await client.list_available_models()
        print(f"Models: {models}")

        # Run inference
        if models:
            response = await client.inference(
                model=models[0],
                prompt="Hello, how are you?",
                wallet_address="test-wallet"
            )
            print(f"Response: {response.response}")

asyncio.run(test())
```

## Access Points

Once running, access these endpoints:

| Service | URL | Description |
|---------|-----|-------------|
| Gateway API | http://localhost:8001 | Main API endpoint |
| Health Check | http://localhost:8001/health | System health status |
| Metrics | http://localhost:8001/metrics | Prometheus metrics |
| Admin Dashboard | http://localhost:8080 | Real-time monitoring UI |

## Example: Complete Inference Flow

```python
import asyncio
from client.python.solanalm_client import SolanaLMClient

async def main():
    async with SolanaLMClient("http://localhost:8001") as client:

        # 1. Check network status
        status = await client.get_network_status()
        print(f"Service: {status.get('service')}")
        print(f"Active nodes: {status.get('network_stats', {}).get('active_nodes', 0)}")

        # 2. List available models
        models = await client.list_available_models()
        print(f"\nAvailable models: {models}")

        # 3. Run inference
        response = await client.inference(
            model="microsoft/DialoGPT-small",
            prompt="What is the meaning of life?",
            wallet_address="my-wallet-address",
            max_tokens=100,
            temperature=0.7
        )

        print(f"\nResponse: {response.response}")
        print(f"Tokens: {response.tokens_generated}")
        print(f"Cost: {response.cost_sol} SOL")
        print(f"Latency: {response.processing_time}s")

asyncio.run(main())
```

## Running Multiple Nodes

Scale your local network with multiple nodes:

=== "Terminal 1 - Gateway"

    ```bash
    python scripts/run_gateway.py
    ```

=== "Terminal 2 - Inference Node 1"

    ```bash
    python scripts/run_node.py \
        --node-type inference \
        --node-id inference-1 \
        --wallet wallet-1 \
        --port 8100
    ```

=== "Terminal 3 - Inference Node 2"

    ```bash
    python scripts/run_node.py \
        --node-type inference \
        --node-id inference-2 \
        --wallet wallet-2 \
        --port 8101
    ```

=== "Terminal 4 - Training Node"

    ```bash
    python scripts/run_node.py \
        --node-type training \
        --node-id training-1 \
        --wallet wallet-3 \
        --port 8200
    ```

## Using the OpenAI-Compatible API

SolanaLM provides an OpenAI-compatible endpoint:

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

## What's Next?

Now that you have SolanaLM running:

- [Configure your environment](configuration.md) for your use case
- [Explore the Python SDK](../guides/python-sdk.md) in depth
- [Set up nodes](../guides/running-nodes.md) for earning SOL
- [Learn about privacy features](../guides/privacy.md) for sensitive workloads
