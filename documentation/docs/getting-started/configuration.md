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
# Authentication (REQUIRED in production - minimum 32 characters)
JWT_SECRET_KEY=your-secure-jwt-secret-key-at-least-32-chars
ADMIN_API_KEY=your-secure-admin-api-key-at-least-32-chars

# CORS Origins (comma-separated, no wildcards in production)
ALLOWED_ORIGINS=https://app.yoursite.com,https://dashboard.yoursite.com

# Treasury Wallet (for Solana transactions)
TREASURY_KEYFILE_PATH=/path/to/treasury-keypair.json

# Solana Transaction Settings
SOLANA_TX_TIMEOUT_SECONDS=60
SOLANA_TX_MAX_RETRIES=3
```

### Docker Secrets (Production)

For Docker deployments, use the `_FILE` suffix pattern:

```bash
# Secrets are read from files instead of environment variables
JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
ADMIN_API_KEY_FILE=/run/secrets/admin_api_key
TREASURY_KEYFILE_PATH=/run/secrets/treasury_keyfile
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
| `SOLANALM_ENVIRONMENT` | `development` | Environment: development, testnet, mainnet |
| `SOLANA_NETWORK` | `devnet` | Solana network to connect to |
| `SOLANA_RPC_URL` | Auto | RPC endpoint URL |
| `GATEWAY_HOST` | `localhost` | Gateway bind address |
| `GATEWAY_PORT` | `8001` | Gateway port |
| `GATEWAY_WORKERS` | `1` | Number of Uvicorn workers |
| `NODE_ID` | Auto-generated | Unique node identifier |
| `WALLET_ADDRESS` | Required | Solana wallet for payments |
| `JWT_SECRET_KEY` | Required* | Secret for JWT tokens (min 32 chars in production) |
| `ADMIN_API_KEY` | Required* | Admin API key (min 32 chars in production) |
| `ALLOWED_ORIGINS` | localhost | Comma-separated CORS origins |
| `DATABASE_URL` | PostgreSQL | Database connection string |
| `REDIS_URL` | localhost | Redis connection for caching |
| `TREASURY_KEYFILE_PATH` | None | Path to Solana keypair JSON |
| `SOLANA_TX_TIMEOUT_SECONDS` | `60` | Transaction confirmation timeout |
| `SOLANA_TX_MAX_RETRIES` | `3` | Max transaction retry attempts |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

*Required in production environments with strict validation

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

Full production deployment with security validation:

```bash
# Environment (triggers security validation)
SOLANALM_ENVIRONMENT=mainnet

# Solana Configuration
SOLANA_NETWORK=mainnet-beta
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Security (REQUIRED - validated at startup)
JWT_SECRET_KEY=your-production-jwt-secret-at-least-32-characters
ADMIN_API_KEY=your-production-admin-api-key-at-least-32-chars
ALLOWED_ORIGINS=https://app.solanalm.io,https://dashboard.solanalm.io

# Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/solanalm
REDIS_URL=redis://prod-redis:6379

# Treasury Wallet
TREASURY_KEYFILE_PATH=/etc/solanalm/treasury-keypair.json

# Logging
LOG_LEVEL=WARNING
```

#### Production Validation Rules

In production environments (`SOLANALM_ENVIRONMENT=testnet` or `mainnet`):

1. **JWT_SECRET_KEY** and **ADMIN_API_KEY** must be at least 32 characters
2. Secrets cannot contain weak patterns: `your-secret-key`, `dev-only-`, `admin123`, `secret123`
3. **ALLOWED_ORIGINS** cannot contain `*` (wildcard)
4. Localhost origins generate warnings

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

    - Never commit `.env` files or keypairs to version control
    - Use Docker secrets or secrets management (Vault, AWS Secrets Manager)
    - Enable TLS/SSL for all endpoints (use `docker/nginx/nginx.conf`)
    - Use secrets at least 32 characters long
    - Rotate JWT secrets regularly
    - Fund treasury wallet before processing payments

### Generating Secure Secrets

```bash
# Generate production-grade secrets
python -c "import secrets; print(secrets.token_urlsafe(48))"  # JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"  # ADMIN_API_KEY

# Create treasury wallet
solana-keygen new -o treasury-keypair.json --no-bip39-passphrase

# Fund on testnet
solana airdrop 2 $(solana-keygen pubkey treasury-keypair.json) --url testnet
```

### Docker Secrets Setup

```bash
# Initialize Docker Swarm
docker swarm init

# Create secrets from generated values
echo "your-48-char-jwt-secret" | docker secret create jwt_secret -
echo "your-48-char-admin-key" | docker secret create admin_api_key -
cat treasury-keypair.json | docker secret create treasury_keyfile -
echo "postgres-password" | docker secret create postgres_password -

# Deploy with secrets
docker stack deploy -c docker/docker-compose.production.yml solanalm
```

## Next Steps

- [Run your first node](../guides/running-nodes.md)
- [Deploy with Docker](../deployment/docker.md)
- [Production deployment guide](../deployment/production.md)
