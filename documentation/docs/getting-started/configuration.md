# Configuration

SolanaLM uses environment variables and configuration files for customization.

## Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### Core Settings

```bash
# Network Configuration
SOLANA_NETWORK=devnet          # devnet, testnet, mainnet-beta
SOLANA_RPC_URL=https://api.devnet.solana.com

# Gateway Settings
GATEWAY_HOST=localhost
GATEWAY_PORT=8001

# Node Identity
NODE_ID=my-node-1
WALLET_ADDRESS=YourSolanaWalletAddress
```

### Security Settings

```bash
# Authentication
JWT_SECRET=your-secure-jwt-secret-key
API_KEY_SECRET=your-api-key-secret

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
```

### Database Settings (Production)

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/solanalm

# Redis Cache
REDIS_URL=redis://localhost:6379
```

### External API Keys (Optional)

```bash
# For proxy nodes
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...
```

## Configuration Reference

### Full Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SOLANA_NETWORK` | `devnet` | Solana network to connect to |
| `SOLANA_RPC_URL` | Auto | RPC endpoint URL |
| `GATEWAY_HOST` | `localhost` | Gateway bind address |
| `GATEWAY_PORT` | `8001` | Gateway port |
| `NODE_ID` | Auto-generated | Unique node identifier |
| `WALLET_ADDRESS` | Required | Solana wallet for payments |
| `JWT_SECRET` | Required | Secret for JWT tokens |
| `API_KEY_SECRET` | Required | Secret for API key generation |
| `RATE_LIMIT_PER_MINUTE` | `100` | Requests per minute limit |
| `DATABASE_URL` | SQLite | Database connection string |
| `REDIS_URL` | None | Redis connection for caching |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `DEBUG` | `false` | Enable debug mode |

## Network Environments

### Development (Default)

Local testing with simulated payments:

```bash
SOLANA_NETWORK=devnet
DATABASE_URL=sqlite:///./dev.db
DEBUG=true
LOG_LEVEL=DEBUG
```

### Testnet

Real Solana transactions with test SOL:

```bash
SOLANA_NETWORK=testnet
SOLANA_RPC_URL=https://api.testnet.solana.com
DATABASE_URL=postgresql://user:pass@localhost:5432/solanalm_test
```

### Production

Full production deployment:

```bash
SOLANA_NETWORK=mainnet-beta
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
DATABASE_URL=postgresql://user:pass@prod-db:5432/solanalm
REDIS_URL=redis://prod-redis:6379
DEBUG=false
LOG_LEVEL=WARNING
```

## Node Configuration

### Inference Node

```python
from core.nodes.inference.node import InferenceNode

node = InferenceNode(
    node_id="my-inference-node",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    model_name="microsoft/DialoGPT-small",
    port=8100,

    # Optional settings
    max_concurrent_requests=10,
    request_timeout=60,
    enable_caching=True
)
```

### Training Node

```python
from core.nodes.training.node import TrainingNode

node = TrainingNode(
    node_id="my-training-node",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    port=8200,

    # Training settings
    local_epochs=5,
    learning_rate=0.01,
    batch_size=32
)
```

### Proxy Node

```python
from core.nodes.proxy.node import ProxyNode

node = ProxyNode(
    node_id="my-proxy-node",
    wallet_address="YourWalletAddress",
    gateway_url="http://localhost:8001",
    port=8300,

    # API configurations
    openai_api_key="sk-...",
    anthropic_api_key="sk-ant-...",
    default_provider="openai"
)
```

## Pricing Configuration

Configure pricing for your node:

```python
# Example pricing configuration
PRICING = {
    "inference_cost_per_token": 0.000001,  # SOL per token
    "training_cost_per_sample": 0.00001,   # SOL per training sample
    "network_fee_percentage": 0.05,        # 5% network fee
    "minimum_request_cost": 0.0001,        # Minimum charge per request
}
```

## Logging Configuration

Customize logging behavior:

```python
import logging

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('solanalm.log'),
        logging.StreamHandler()
    ]
)

# Set specific loggers
logging.getLogger('core.gateway').setLevel(logging.DEBUG)
logging.getLogger('core.nodes').setLevel(logging.INFO)
```

## Hardware Auto-Detection

SolanaLM automatically detects hardware capabilities:

```python
from core.utils.hardware_detection import detect_hardware

hardware = detect_hardware()
print(f"CPU cores: {hardware['cpu_cores']}")
print(f"RAM: {hardware['ram_gb']} GB")
print(f"GPU: {hardware.get('gpu_name', 'None')}")
print(f"VRAM: {hardware.get('vram_gb', 0)} GB")
```

Override detection with environment variables:

```bash
FORCE_CPU_ONLY=true
MAX_GPU_MEMORY=8  # GB
CUDA_VISIBLE_DEVICES=0,1
```

## Security Best Practices

!!! warning "Production Security"

    For production deployments:

    - Never commit `.env` files to version control
    - Use secrets management (Vault, AWS Secrets Manager)
    - Enable TLS/SSL for all endpoints
    - Rotate JWT secrets regularly
    - Use strong, unique API keys

### Generating Secure Secrets

```python
import secrets

# Generate a secure JWT secret
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET={jwt_secret}")

# Generate API key secret
api_secret = secrets.token_urlsafe(32)
print(f"API_KEY_SECRET={api_secret}")
```

## Next Steps

- [Run your first node](../guides/running-nodes.md)
- [Deploy with Docker](../deployment/docker.md)
- [Production deployment guide](../deployment/production.md)
