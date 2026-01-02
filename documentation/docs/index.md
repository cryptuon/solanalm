# SolanaLM Documentation

**Enterprise-Grade Decentralized AI Network on Solana**

SolanaLM is a hybrid decentralized network combining LLM inference and federated learning on Solana. Nodes earn SOL through dual revenue streams: serving inference requests and participating in training rounds.

---

## Key Features

<div class="grid cards" markdown>

-   :robot:{ .lg .middle } **Multi-Backend AI Inference**

    ---

    Run local models with PyTorch/Transformers or connect to external APIs like OpenAI, Anthropic, and Cohere through a unified interface.

    [:octicons-arrow-right-24: Learn more](guides/python-sdk.md)

-   :brain:{ .lg .middle } **Federated Learning**

    ---

    State-of-the-art algorithms (FedAvg, FedProx, SCAFFOLD) with differential privacy and secure aggregation.

    [:octicons-arrow-right-24: Federated Learning Guide](guides/federated-learning.md)

-   :lock:{ .lg .middle } **Privacy-Preserving**

    ---

    Onion routing, anonymous payments, and encrypted inference for sensitive workloads.

    [:octicons-arrow-right-24: Privacy Features](guides/privacy.md)

-   :coin:{ .lg .middle } **Earn SOL**

    ---

    Dual revenue streams from inference requests and training participation with dynamic pricing.

    [:octicons-arrow-right-24: Payment System](architecture/payments.md)

</div>

---

## Quick Start

Get up and running in minutes:

```bash
# Clone and setup
git clone https://github.com/solanalm/solanalm.git
cd solanalm && poetry install && poetry shell

# Start development environment
python scripts/quick_start.py

# Test the system
python scripts/test_end_to_end.py
```

[:octicons-arrow-right-24: Full Installation Guide](getting-started/installation.md)

---

## Basic Usage

### Python SDK

```python
import asyncio
from solanalm_client import SolanaLMClient

async def main():
    async with SolanaLMClient("http://localhost:8001") as client:
        response = await client.inference(
            model="microsoft/DialoGPT-small",
            prompt="Explain quantum computing",
            wallet_address="your-wallet-address"
        )
        print(f"Response: {response.response}")
        print(f"Cost: {response.cost_sol} SOL")

asyncio.run(main())
```

### OpenAI-Compatible API

```python
from solanalm_client import OpenAICompatibleClient

client = OpenAICompatibleClient(
    base_url="http://localhost:8001/v1",
    api_key="your-solana-wallet-address"
)

response = client.chat.completions.create(
    model="microsoft/DialoGPT-small",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

[:octicons-arrow-right-24: SDK Documentation](guides/python-sdk.md)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interfaces                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐   │
│  │Python SDK │  │ OpenAI API│  │Web Dashboard│ │Terminal TUI│   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └──────┬──────┘   │
└────────┼──────────────┼──────────────┼───────────────┼──────────┘
         └──────────────┴──────────────┴───────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Gateway API      │
                    │   Load Balancer     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Node Registry     │
                    └──────────┬──────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
┌──────▼───────┐    ┌──────────▼─────────┐    ┌───────▼───────┐
│ Inference    │    │ Training Nodes     │    │ Proxy Nodes   │
│ Nodes        │    │ • Federated FL     │    │ • OpenAI API  │
│ • PyTorch    │    │ • Privacy FL       │    │ • Anthropic   │
│ • llama.cpp  │    │ • Model Training   │    │ • Cohere      │
└──────────────┘    └────────────────────┘    └───────────────┘
```

[:octicons-arrow-right-24: Architecture Details](architecture/overview.md)

---

## Deployment Options

| Environment | Description | Use Case |
|-------------|-------------|----------|
| **Local** | Single-command setup | Development, testing |
| **Docker** | Full containerized stack | Staging, small deployments |
| **Kubernetes** | Production-grade orchestration | Enterprise, high availability |

[:octicons-arrow-right-24: Deployment Guide](deployment/docker.md)

---

## Community & Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/solanalm/solanalm/issues)
- **Discord**: [Join the community](https://discord.gg/solanalm)
- **Twitter**: [@SolanaLM](https://twitter.com/SolanaLM)

---

## License

SolanaLM is open-source software licensed under the [MIT License](https://opensource.org/licenses/MIT).
