# SolanaLM

A **hybrid decentralized network** on Solana combining **LLM inference** and **federated learning**. Nodes earn SOL by serving inference requests AND participating in model training.

## 🚀 Core Concept

**Inference + Training Network**:
- **Inference Nodes**: Serve LLM requests, earn immediate SOL payments
- **Training Nodes**: Participate in federated learning, earn SOL per training round
- **Hybrid Nodes**: Switch between inference and training to maximize earnings
- **Proxy Nodes**: Gateway to external LLM APIs (OpenAI, Anthropic, etc.)

## 🏗️ Architecture

```
├── core/                    # Core network components
│   ├── gateway/            # Request routing & load balancing
│   ├── nodes/              # Node implementations
│   │   ├── inference/      # Local LLM serving
│   │   ├── training/       # Federated learning participation
│   │   ├── hybrid/         # Dual-mode nodes
│   │   └── proxy/          # API gateway nodes
│   ├── coordinator/        # Training round coordination
│   ├── registry/           # Node discovery & capabilities
│   └── payments/           # SOL micro-transactions
├── contracts/              # Solana smart contracts
├── client/                 # SDKs and interfaces
├── docs/                   # All documentation
└── examples/               # Usage examples
```

## 💰 Economics

**Dual Revenue Streams**:
- **Inference**: $0.001-0.01 SOL per request
- **Training**: 0.1-1 SOL per federated learning round
- **Efficiency**: Same GPU hardware serves both functions

## 🛠️ Quick Start

1. **Install dependencies**:
   ```bash
   poetry install && poetry shell
   ```

2. **Verify setup**:
   ```bash
   poetry run python scripts/verify_setup.py
   ```

3. **Start development environment**:
   ```bash
   docker-compose up -d
   ```

## 📖 Documentation

All documentation is in the [`docs/`](./docs/) directory:
- [Architecture Overview](./docs/abstraction_design.md)
- [Technical Specifications](./docs/phase1_technical_spec.md)
- [Implementation Plan](./docs/implementation_plan.md)
- [Project Roadmap](./docs/roadmap.md)

## 🧪 Development

- **Test**: `poetry run pytest`
- **Format**: `poetry run black .`
- **Lint**: `poetry run flake8 .`
- **Type check**: `poetry run mypy .`