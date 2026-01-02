# Installation

This guide covers installing SolanaLM for development and production use.

## Prerequisites

Before installing SolanaLM, ensure you have the following:

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.12+ | Required for all components |
| **Poetry** | Latest | Recommended for dependency management |
| **RAM** | 8GB+ | 16GB+ recommended for local inference |
| **GPU** | Optional | CUDA-compatible GPU for faster inference |
| **Solana CLI** | Optional | For mainnet/testnet integration |

## Installation Methods

=== "Poetry (Recommended)"

    Poetry provides the best dependency management experience:

    ```bash
    # Clone the repository
    git clone https://github.com/solanalm/solanalm.git
    cd solanalm

    # Install dependencies
    poetry install

    # Activate the virtual environment
    poetry shell

    # Verify installation
    python scripts/verify_setup.py
    ```

=== "pip"

    For environments where Poetry isn't available:

    ```bash
    # Clone the repository
    git clone https://github.com/solanalm/solanalm.git
    cd solanalm

    # Create and activate virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

    # Verify installation
    python scripts/verify_setup.py
    ```

=== "Docker"

    For containerized deployment:

    ```bash
    # Clone the repository
    git clone https://github.com/solanalm/solanalm.git
    cd solanalm

    # Build and run with Docker Compose
    docker-compose up -d

    # Verify services are running
    docker-compose ps
    ```

## Verify Installation

Run the verification script to check your setup:

```bash
python scripts/verify_setup.py
```

Expected output:

```
✓ Python version: 3.12.0
✓ Poetry installed
✓ Dependencies installed
✓ PyTorch available
✓ CUDA available (optional)
✓ Solana SDK available
✓ Hardware detection working
  - CPU: 8 cores
  - RAM: 16 GB
  - GPU: NVIDIA RTX 3080 (optional)
```

## GPU Support

For GPU-accelerated inference, ensure you have:

1. **NVIDIA GPU** with CUDA support
2. **CUDA Toolkit** 11.8 or higher
3. **cuDNN** library

Install PyTorch with CUDA support:

```bash
# For CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Verify GPU availability:

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

## Optional Dependencies

### External API Support

For proxy nodes that connect to external APIs:

```bash
# Install API client libraries
pip install openai anthropic cohere
```

Set API keys in your environment:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export COHERE_API_KEY="..."
```

### Development Tools

For contributing to SolanaLM:

```bash
# Install development dependencies
poetry install --with dev

# Or with pip
pip install black flake8 mypy pytest pytest-asyncio
```

## Troubleshooting

### Common Issues

??? question "Poetry install fails with dependency conflicts"

    Try clearing the cache and reinstalling:

    ```bash
    poetry cache clear pypi --all
    poetry lock --no-update
    poetry install
    ```

??? question "PyTorch not detecting GPU"

    1. Verify CUDA installation: `nvidia-smi`
    2. Check PyTorch CUDA version matches system CUDA
    3. Reinstall PyTorch with correct CUDA version

??? question "Import errors after installation"

    Ensure you're in the correct virtual environment:

    ```bash
    # With Poetry
    poetry shell

    # With venv
    source venv/bin/activate
    ```

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/solanalm/solanalm/issues)
2. Join our [Discord community](https://discord.gg/solanalm)
3. Run diagnostics: `python scripts/verify_setup.py --verbose`

## Next Steps

- [Quick Start Guide](quickstart.md) - Get your first inference running
- [Configuration](configuration.md) - Configure your environment
- [Running Nodes](../guides/running-nodes.md) - Start contributing to the network
