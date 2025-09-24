# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SolanaLM is a hybrid decentralized network combining LLM inference and federated learning on Solana. Nodes earn SOL through dual revenue streams: serving inference requests and participating in training rounds.

## Development Commands

### Environment Setup
```bash
# Install dependencies using Poetry
poetry install && poetry shell

# Verify setup (includes hardware detection and dependency checks)
python scripts/verify_setup.py

# Alternative: Install manually with pip (if Poetry unavailable)
pip install -r requirements.txt
```

### Running Components
```bash
# Start the gateway (required for all operations)
python scripts/run_gateway.py

# Run different node types
python scripts/run_node.py --node-type inference --node-id node1 --wallet WALLET_ADDR
python scripts/run_node.py --node-type training --node-id node2 --wallet WALLET_ADDR
python scripts/run_node.py --node-type proxy --node-id node3 --wallet WALLET_ADDR

# Quick development setup
python scripts/quick_start.py
```

### Testing
```bash
# Run full test suite
poetry run pytest

# End-to-end system test (requires gateway running)
python scripts/test_end_to_end.py

# Test individual components
python scripts/test_solana.py
pytest tests/test_integration.py -v
pytest tests/test_privacy.py::test_onion_routing -v
```

### Code Quality
```bash
# Format code
poetry run black .

# Lint code
poetry run flake8 .

# Type checking
poetry run mypy .
```

## Architecture Overview

### Core Network Components
- **Gateway** (`core/gateway/`): Central request router, load balancer, and OpenAI-compatible API layer
- **Node Registry** (`core/registry/`): Discovers and tracks node capabilities, handles health checks
- **Payment Client** (`core/payments/`): Solana blockchain integration for SOL micro-transactions
- **Training Coordinator** (`core/coordinator/`): Orchestrates federated learning rounds

### Node Types Architecture
- **Inference Nodes** (`core/nodes/inference/`): Local LLM serving with PyTorch/Transformers
- **Training Nodes** (`core/nodes/training/`): Federated learning participants with model weight sharing
- **Proxy Nodes** (`core/nodes/proxy/`): Gateway to external APIs (OpenAI, Anthropic, Cohere)
- **Hybrid Nodes** (`core/nodes/hybrid/`): Switch between inference and training modes

### Privacy Infrastructure
- **Onion Routing** (`core/privacy/onion_routing.py`): Tor-like multi-hop encrypted circuits
- **Anonymous Payments** (`core/privacy/anonymous_payments.py`): Payment mixing and obfuscation
- **Private Inference**: End-to-end encrypted inference requests

### Client SDKs
- **Python Client** (`client/python/solanalm_client.py`): AsyncIO client with context manager pattern
- **OpenAI Compatibility** (`client/python/openai_compat.py`): Drop-in replacement for OpenAI SDK

## Key Implementation Details

### Solana Integration Status
- **Current**: Hybrid architecture with simulated payments for development
- **Payment Layer**: Full Solana RPC integration (devnet/testnet/mainnet support)
- **Smart Contracts**: Infrastructure ready, contracts not yet deployed
- **Configuration**: Multi-network support via `core/config/settings.py`

### Hardware Detection
- **Auto-Discovery**: `core/utils/hardware_detection.py` detects CPU, GPU, memory, storage
- **Node Capabilities**: Hardware specs automatically reported to registry
- **Fallback Values**: Sensible defaults when detection fails

### Model Support
- **Local Models**: PyTorch/Transformers integration (DialoGPT, Qwen, custom models)
- **External APIs**: OpenAI, Anthropic, Cohere via proxy nodes
- **Federated Training**: PyTorch model weight extraction and aggregation

### Testing Framework
- **End-to-End Tests**: Comprehensive system validation with 10 test scenarios
- **Component Tests**: Individual unit tests for core functionality
- **Integration Tests**: Cross-component testing with mock data

## Configuration Management

### Environment Variables
Configure via `.env` file or environment variables:
- `SOLANA_NETWORK`: devnet, testnet, mainnet-beta
- `SOLANA_RPC_URL`: Blockchain RPC endpoint
- `GATEWAY_HOST/PORT`: Gateway server settings
- `NODE_ID/WALLET_ADDRESS`: Node identity
- `OPENAI_API_KEY`: For proxy nodes

### Network Environments
- **Development**: Local testing with simulated payments
- **Testnet**: Real Solana transactions with test SOL
- **Mainnet**: Production deployment with real SOL

## Common Development Patterns

### Adding New Node Types
1. Create node class in `core/nodes/{type}/node.py`
2. Inherit from base capabilities in `core/models/schemas.py`
3. Register node type in gateway router
4. Add configuration to `core/config/settings.py`

### Client Integration
```python
# Standard usage pattern
async with SolanaLMClient("http://localhost:8001") as client:
    response = await client.inference(
        model="model-name",
        prompt="Hello",
        wallet_address="wallet-addr"
    )
```

### Privacy Features
- All privacy methods use `private_` prefix (e.g., `private_inference`)
- Circuit-based routing hides node identity
- Payment mixing prevents transaction correlation

## Dependencies and Requirements

### Core Requirements
- Python 3.12+
- PyTorch (GPU support recommended)
- Transformers library
- Solana Python SDK
- FastAPI/Uvicorn

### Optional Dependencies
- CUDA for GPU acceleration
- Docker for containerized deployment
- PostgreSQL for production database
- Redis for caching