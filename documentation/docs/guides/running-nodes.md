# Running Nodes

Learn how to run different types of nodes on the SolanaLM network and earn SOL.

## Node Types Overview

| Node Type | Purpose | Revenue Stream | Requirements |
|-----------|---------|----------------|--------------|
| **Inference** | Process LLM requests | Per-request fees | GPU recommended |
| **Training** | Participate in FL | Training rewards | Data + compute |
| **Proxy** | Route to external APIs | Commission | API keys |
| **Hybrid** | Both inference & training | Dual revenue | All of above |

## Starting Nodes

### Using the CLI

The simplest way to start a node:

```bash
# Inference node
python scripts/run_node.py \
    --node-type inference \
    --node-id my-inference-node \
    --wallet YOUR_WALLET_ADDRESS \
    --port 8100

# Training node
python scripts/run_node.py \
    --node-type training \
    --node-id my-training-node \
    --wallet YOUR_WALLET_ADDRESS \
    --port 8200

# Proxy node
python scripts/run_node.py \
    --node-type proxy \
    --node-id my-proxy-node \
    --wallet YOUR_WALLET_ADDRESS \
    --port 8300
```

### CLI Options

```bash
python scripts/run_node.py --help

Options:
  --node-type     Node type: inference, training, proxy, hybrid
  --node-id       Unique identifier for this node
  --wallet        Solana wallet address for payments
  --port          Port to listen on
  --gateway-url   Gateway URL (default: http://localhost:8001)
  --model         Model to serve (inference nodes)
  --log-level     Logging verbosity
```

## Inference Nodes

Process LLM inference requests and earn fees per request.

### Basic Setup

```python
from core.nodes.inference.node import InferenceNode

node = InferenceNode(
    node_id="inference-node-1",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    model_name="microsoft/DialoGPT-small",
    port=8100
)

# Initialize and run
async def main():
    await node.initialize()
    await node.run()

asyncio.run(main())
```

### Configuration Options

```python
node = InferenceNode(
    node_id="inference-node-1",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    model_name="microsoft/DialoGPT-small",
    port=8100,

    # Performance settings
    max_concurrent_requests=10,
    request_timeout=60,
    batch_size=4,

    # Resource limits
    max_memory_gb=8,
    gpu_memory_fraction=0.8,

    # Caching
    enable_caching=True,
    cache_size_mb=512
)
```

### Supported Models

Out of the box, inference nodes support:

- **Transformers models**: Any Hugging Face model
- **DialoGPT**: Conversational models
- **GPT-2/GPT-Neo**: Text generation
- **Custom models**: Your own fine-tuned models

```python
# Using different models
node = InferenceNode(
    model_name="gpt2-medium",  # or
    # model_name="EleutherAI/gpt-neo-1.3B",
    # model_name="./path/to/custom/model",
    ...
)
```

## Training Nodes

Participate in federated learning rounds and earn training rewards.

### Basic Setup

```python
from core.nodes.training.node import TrainingNode

node = TrainingNode(
    node_id="training-node-1",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    port=8200
)

async def main():
    await node.initialize()
    await node.run()

asyncio.run(main())
```

### Configuration Options

```python
node = TrainingNode(
    node_id="training-node-1",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    port=8200,

    # Training parameters
    local_epochs=5,
    learning_rate=0.01,
    batch_size=32,

    # Privacy settings
    enable_differential_privacy=True,
    noise_multiplier=1.0,
    max_grad_norm=1.0,

    # Data settings
    data_path="./training_data/",
    validation_split=0.2
)
```

### Federated Learning Algorithms

Training nodes support multiple FL algorithms:

```python
from core.training.federation import FederatedTrainer, FLAlgorithm

trainer = FederatedTrainer(
    algorithm=FLAlgorithm.FEDAVG,  # or
    # algorithm=FLAlgorithm.FEDPROX,
    # algorithm=FLAlgorithm.SCAFFOLD,
    # algorithm=FLAlgorithm.FEDADAM,
    ...
)
```

## Proxy Nodes

Route requests to external APIs and earn commission.

### Basic Setup

```python
from core.nodes.proxy.node import ProxyNode

node = ProxyNode(
    node_id="proxy-node-1",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    port=8300
)

async def main():
    await node.initialize()
    await node.run()

asyncio.run(main())
```

### Configuring API Providers

```python
node = ProxyNode(
    node_id="proxy-node-1",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    port=8300,

    # API keys
    openai_api_key="sk-...",
    anthropic_api_key="sk-ant-...",
    cohere_api_key="...",

    # Default provider
    default_provider="openai",

    # Rate limiting
    requests_per_minute=60,

    # Commission
    commission_percentage=0.05  # 5% markup
)
```

### Supported Providers

| Provider | Models | API Key Required |
|----------|--------|------------------|
| OpenAI | GPT-4, GPT-3.5, etc. | Yes |
| Anthropic | Claude 3, Claude 2 | Yes |
| Cohere | Command, Embed | Yes |
| Ollama | Local models | No |

## Node Lifecycle

### Initialization

```python
await node.initialize()
# - Loads model (inference nodes)
# - Connects to gateway
# - Registers capabilities
# - Starts health reporting
```

### Running

```python
await node.run()
# - Listens for requests
# - Processes tasks
# - Reports metrics
# - Handles payments
```

### Shutdown

```python
await node.shutdown()
# - Completes pending requests
# - Deregisters from gateway
# - Cleans up resources
```

## Health Monitoring

Nodes expose health endpoints:

```bash
# Check node health
curl http://localhost:8100/health

# Response
{
    "status": "healthy",
    "node_id": "inference-node-1",
    "uptime": 3600,
    "requests_processed": 150,
    "current_load": 0.3
}
```

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8100/metrics

# Available metrics
solanalm_requests_total
solanalm_request_duration_seconds
solanalm_errors_total
solanalm_gpu_memory_usage
solanalm_earnings_sol
```

## Running Multiple Nodes

### On Same Machine

```bash
# Terminal 1 - Inference node
python scripts/run_node.py --node-type inference --port 8100 --node-id inf-1

# Terminal 2 - Inference node
python scripts/run_node.py --node-type inference --port 8101 --node-id inf-2

# Terminal 3 - Training node
python scripts/run_node.py --node-type training --port 8200 --node-id train-1
```

### With Docker

```yaml
# docker-compose.yml
services:
  inference-1:
    build: .
    command: python scripts/run_node.py --node-type inference --node-id inf-1
    ports:
      - "8100:8100"

  inference-2:
    build: .
    command: python scripts/run_node.py --node-type inference --node-id inf-2
    ports:
      - "8101:8100"

  training-1:
    build: .
    command: python scripts/run_node.py --node-type training --node-id train-1
    ports:
      - "8200:8200"
```

## Earning SOL

### Revenue Sources

1. **Inference fees**: Paid per request based on tokens generated
2. **Training rewards**: Paid for participating in FL rounds
3. **Quality bonuses**: Extra for fast, accurate responses

### Payment Flow

```
Client Request → Gateway → Node → Response
                    ↓
              Payment Processed
                    ↓
              SOL → Your Wallet
```

### Checking Earnings

```python
async with SolanaLMClient(gateway_url) as client:
    analytics = await client.get_usage_analytics(
        wallet_address="YourWallet",
        period="last_30_days"
    )
    print(f"Total earned: {analytics['total_earned']} SOL")
```

## Best Practices

### Performance

- Use GPU for inference nodes
- Set appropriate batch sizes
- Enable caching for repeated queries
- Monitor memory usage

### Reliability

- Implement graceful shutdown
- Handle network interruptions
- Log errors for debugging
- Set up alerting

### Security

- Keep API keys secure
- Use firewall rules
- Enable TLS in production
- Regular security updates

## Next Steps

- [Federated Learning Guide](federated-learning.md) - Deep dive into FL
- [Privacy Features](privacy.md) - Enable privacy features
- [Docker Deployment](../deployment/docker.md) - Containerized deployment
