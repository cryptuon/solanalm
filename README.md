# SolanaLM: Decentralized AI Network on Solana

> **Active development.** SolanaLM is under active development. APIs,
> schemas, and on-chain layouts may change between releases.
> Production use at your own risk. Issues and PRs welcome.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency-poetry-blue)](https://python-poetry.org/)

Hybrid decentralized network combining LLM inference and federated learning on Solana. Nodes earn SOL through dual revenue streams: serving inference requests and participating in training rounds.

- **Docs:** <https://docs.cryptuon.com/solanalm/>
- **Marketing:** <https://solanalm.cryptuon.com/>
- **Repo:** <https://github.com/cryptuon/solanalm>

## Quick Start

```bash
# Clone and setup
git clone https://github.com/cryptuon/solanalm.git
cd solanalm && poetry install && poetry shell

# Start development environment
python scripts/quick_start.py

# Test the system
python scripts/test_end_to_end.py
```

## Key Features

### Multi-Backend AI Inference
- **Local Models**: PyTorch / Transformers, llama.cpp integration
- **API Proxies**: OpenAI, Anthropic, Cohere, Ollama support
- **Unified Interface**: Single API for all backends
- **Auto-scaling**: Dynamic node discovery and load balancing

### Federated Learning
- **Algorithms**: FedAvg, FedProx, FedAdam, SCAFFOLD
- **Privacy-Preserving**: Differential privacy and secure aggregation
- **Non-IID Data**: Handles heterogeneous data distributions
- **Fault Tolerant**: Circuit breakers and automatic recovery

### Security
- **Multi-Factor Auth**: JWT, API keys, Solana wallet signatures
- **Rate Limiting**: Configurable per-user and per-endpoint limits
- **Input Sanitization**: XSS and injection attack prevention
- **Audit Logging**: Comprehensive security event tracking

### Real-Time Monitoring
- **Live Dashboard**: WebSocket-based admin interface
- **Prometheus Metrics**: Industry-standard monitoring integration
- **Health Checks**: Automated system health monitoring
- **Performance Analytics**: Request tracing and performance insights

### Deployment
- **Docker / Kubernetes**: Container-native architecture
- **Auto-scaling**: HPA and VPA support
- **High Availability**: Multi-zone deployment support
- **Cloud Native**: AWS, GCP, Azure compatible

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client SDKs   │    │   Gateway API    │    │  Admin Dashboard│
│  Python/OpenAI  │◄──►│  Load Balancer   │◄──►│  Real-time UI   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                        ┌───────┴───────┐
                        │  Node Registry │
                        └───────┬───────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌─────────▼────────┐    ┌────────▼────────┐
│ Inference Nodes │    │ Training Nodes   │    │  Proxy Nodes    │
│ • PyTorch       │    │ • Federated FL   │    │ • OpenAI API    │
│ • llama.cpp     │    │ • Privacy FL     │    │ • Anthropic     │
│ • Transformers  │    │ • Model Training │    │ • Cohere        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Installation & Setup

### Prerequisites
- **Python**: 3.12+ with Poetry for dependency management
- **Hardware**: 8 GB RAM minimum (16 GB+ recommended)
- **GPU**: Optional but recommended for local inference
- **Solana**: Wallet for testnet / mainnet integration

### Development Setup
```bash
# 1. Install dependencies
poetry install && poetry shell
python scripts/verify_setup.py

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start components
python scripts/run_gateway.py                    # Terminal 1
python scripts/run_node.py --type inference      # Terminal 2
python scripts/run_node.py --type training       # Terminal 3

# 4. Access services
# Gateway API:     http://localhost:8001
# Admin Dashboard: http://localhost:8080
# Node Health:     http://localhost:8100/health
```

### Docker Deployment
```bash
# Start full stack
docker-compose up -d

# Scale nodes
docker-compose up -d --scale inference-node=3

# View logs
docker-compose logs -f gateway
```

### Kubernetes Deployment
```bash
# Generate manifests
python deployment/orchestrator.py --target kubernetes --replicas 3

# Deploy to cluster
kubectl apply -f k8s-manifests/

# Monitor deployment
kubectl get pods -n solanalm
```

## Usage Examples

### Python SDK
```python
import asyncio
from solanalm_client import SolanaLMClient

async def main():
    async with SolanaLMClient("http://localhost:8001") as client:
        # Standard inference
        response = await client.inference(
            model="microsoft/DialoGPT-small",
            prompt="Explain quantum computing",
            wallet_address="your-wallet-address",
        )
        print(f"Response: {response.response}")
        print(f"Cost: {response.cost_sol} SOL")

        # Private inference with onion routing
        private_response = await client.private_inference(
            model="microsoft/DialoGPT-small",
            prompt="Sensitive business query",
            wallet_address="your-wallet-address",
            circuit_length=3,  # 3-hop privacy circuit
        )

        # Join federated learning
        await client.join_training_round(
            model_name="custom-model",
            training_data=your_data,
            wallet_address="your-wallet-address",
        )

asyncio.run(main())
```

### OpenAI API Compatibility
```python
from solanalm_client import OpenAICompatibleClient

client = OpenAICompatibleClient(
    base_url="http://localhost:8001/v1",
    api_key="your-solana-wallet-address",  # Use wallet as API key
)

response = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
)

print(response.choices[0].message.content)
```

### Advanced Federated Learning
```python
from core.training.advanced_algorithms import (
    AdvancedFederatedLearningManager, FLAlgorithm,
)

# Initialize FL manager with SCAFFOLD algorithm
fl_manager = AdvancedFederatedLearningManager(FLAlgorithm.SCAFFOLD)

# Configure heterogeneous clients
client_configs = {
    "client-1": {"local_epochs": 3, "learning_rate": 0.01, "data_size": 1000},
    "client-2": {"local_epochs": 2, "learning_rate": 0.005, "data_size": 500},
}

# Run federated learning round
result = fl_manager.run_federated_round(
    participating_clients=["client-1", "client-2", "client-3"],
    client_configs=client_configs,
)

print(f"Round completed: Loss={result.global_loss:.4f}")
```

## Configuration

### Environment Variables
```bash
# Network Configuration
SOLANA_NETWORK=devnet|testnet|mainnet-beta
SOLANA_RPC_URL=https://api.devnet.solana.com
GATEWAY_HOST=localhost
GATEWAY_PORT=8001

# Security
JWT_SECRET=your-secret-key
API_KEY_SECRET=your-api-secret
RATE_LIMIT_PER_MINUTE=100

# Database (Production)
DATABASE_URL=postgresql://user:pass@host:5432/solanalm
REDIS_URL=redis://localhost:6379

# External APIs (Optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
COHERE_API_KEY=your-cohere-key
```

### Node Configuration
```python
from core.nodes.inference.enhanced_node import EnhancedInferenceNode, ModelBackend

node = EnhancedInferenceNode(
    node_id="my-node",
    wallet_address="wallet-address",
    gateway_url="http://localhost:8001",
    backend=ModelBackend.LLAMA_CPP,  # or TRANSFORMERS, OPENAI_API, etc.
    model_name="llama-2-7b-chat",
    port=8100,
)
```

## Monitoring & Observability

### Metrics Dashboard
Access the real-time dashboard at `http://localhost:8080`:
- **Network Overview**: Active nodes, request throughput, success rates
- **Federated Learning**: Training progress, convergence metrics
- **Node Performance**: Resource utilization, response times
- **Financial**: SOL earnings, transaction costs

### Prometheus Integration
```bash
# Scrape metrics
curl http://localhost:8001/metrics/prometheus

# Example metrics
solanalm_requests_total{node_type="inference"} 1500
solanalm_response_time_seconds{quantile="0.95"} 0.234
solanalm_training_rounds_total 25
```

### Health Checks
```bash
# System health
curl http://localhost:8001/health

# Node health
curl http://localhost:8100/health

# Training status
curl http://localhost:8001/training/status
```

## Testing

```bash
# Run all tests
poetry run pytest

# Specific test categories
poetry run pytest tests/test_inference.py -v        # Inference tests
poetry run pytest tests/test_federated.py -v        # FL tests
poetry run pytest tests/test_security.py -v         # Security tests
poetry run pytest tests/test_integration.py -v      # Integration tests

# End-to-end
python scripts/test_end_to_end.py
```

## Deployment Options

### Local Development
- **Quick Start**: Single command deployment with `python scripts/quick_start.py`
- **Manual Setup**: Individual component control for development
- **Simulated Payments**: No real SOL required for testing

### Docker Compose
- **Full Stack**: All components with dependencies (PostgreSQL, Redis)
- **Scalable**: Easy horizontal scaling of inference / training nodes
- **Persistent Storage**: Model caching and database persistence

### Kubernetes
- **Production**: High availability, auto-scaling, monitoring
- **Cloud Native**: Supports AWS EKS, Google GKE, Azure AKS
- **Helm Charts**: Parameterized deployment configurations

## Economic Model

### Dual Revenue Streams
1. **Inference Revenue**: Earn SOL for processing inference requests
2. **Training Revenue**: Earn SOL for participating in FL rounds

### Dynamic Pricing
- **Market-Based**: Prices adjust based on supply / demand
- **Reputation Weighted**: Higher reputation = higher rates
- **Quality Incentives**: Bonuses for fast, accurate responses

### Cost Structure
```python
# Example pricing (configurable)
INFERENCE_COST_PER_TOKEN = 0.000001  # SOL
TRAINING_COST_PER_SAMPLE = 0.00001   # SOL
NETWORK_FEE_PERCENTAGE = 0.05        # 5% network fee
```

## Privacy & Security

### Privacy Features
- **Onion Routing**: Multi-hop encrypted circuits for request privacy
- **Differential Privacy**: Mathematical privacy guarantees in FL
- **Secure Aggregation**: Encrypted model weight aggregation
- **Anonymous Payments**: Payment mixing to prevent correlation

### Security Measures
- **Input Sanitization**: XSS and injection prevention
- **Rate Limiting**: DDoS and abuse protection
- **Authentication**: Multi-factor auth options
- **Audit Logging**: Complete request / response logging

## Documentation

The canonical documentation lives at <https://docs.cryptuon.com/solanalm/>
(sources under [`documentation/docs/`](documentation/docs/)). Highlights:

- [Getting Started](https://docs.cryptuon.com/solanalm/getting-started/installation/)
- [Python SDK](https://docs.cryptuon.com/solanalm/guides/python-sdk/)
- [Running Nodes](https://docs.cryptuon.com/solanalm/guides/running-nodes/)
- [Federated Learning](https://docs.cryptuon.com/solanalm/guides/federated-learning/)
- [Privacy Features](https://docs.cryptuon.com/solanalm/guides/privacy/)
- [Gateway API](https://docs.cryptuon.com/solanalm/api/gateway/)
- [Architecture Overview](https://docs.cryptuon.com/solanalm/architecture/overview/)
- [Deployment](https://docs.cryptuon.com/solanalm/deployment/docker/)

Marketing site: <https://solanalm.cryptuon.com/>

## Contributing

Contributions are welcome. The basic workflow:

```bash
# Setup
git clone https://github.com/cryptuon/solanalm.git
cd solanalm && poetry install && poetry shell

# Feature branch
git checkout -b feature/amazing-feature

# Lint + test
poetry run pytest
poetry run black .
poetry run flake8 .

# PR
git push origin feature/amazing-feature
```

Please open an [issue](https://github.com/cryptuon/solanalm/issues) to discuss
larger changes before sending a pull request.

## License

Licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Acknowledgments

- **Solana Foundation** — blockchain infrastructure
- **Hugging Face** — model hosting and Transformers
- **PyTorch** — federated learning primitives
- **FastAPI** — high-performance API framework

## Support

- **Documentation**: <https://docs.cryptuon.com/solanalm/>
- **Issues**: <https://github.com/cryptuon/solanalm/issues>
- **Discussions**: <https://github.com/cryptuon/solanalm/discussions>
