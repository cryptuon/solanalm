# Docker Deployment

Deploy SolanaLM using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- GPU support (optional, requires NVIDIA Container Toolkit)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/solanalm/solanalm.git
cd solanalm

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Docker Compose Configuration

### Basic Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile.gateway
    ports:
      - "8001:8001"
    environment:
      - SOLANA_NETWORK=devnet
      - GATEWAY_HOST=0.0.0.0
      - GATEWAY_PORT=8001
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/solanalm
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: unless-stopped

  inference-node:
    build:
      context: .
      dockerfile: docker/Dockerfile.node
    environment:
      - NODE_TYPE=inference
      - NODE_ID=inference-1
      - GATEWAY_URL=http://gateway:8001
      - WALLET_ADDRESS=${WALLET_ADDRESS}
    depends_on:
      - gateway
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  training-node:
    build:
      context: .
      dockerfile: docker/Dockerfile.node
    environment:
      - NODE_TYPE=training
      - NODE_ID=training-1
      - GATEWAY_URL=http://gateway:8001
      - WALLET_ADDRESS=${WALLET_ADDRESS}
    depends_on:
      - gateway
    restart: unless-stopped

  proxy-node:
    build:
      context: .
      dockerfile: docker/Dockerfile.node
    environment:
      - NODE_TYPE=proxy
      - NODE_ID=proxy-1
      - GATEWAY_URL=http://gateway:8001
      - WALLET_ADDRESS=${WALLET_ADDRESS}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - gateway
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=solanalm
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Dockerfiles

### Gateway Dockerfile

```dockerfile
# docker/Dockerfile.gateway
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run gateway
CMD ["python", "scripts/run_gateway.py"]
```

### Node Dockerfile

```dockerfile
# docker/Dockerfile.node
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction

# Copy application code
COPY . .

# Expose port
EXPOSE 8100

# Run node
CMD ["python", "scripts/run_node.py", "--node-type", "${NODE_TYPE}", "--node-id", "${NODE_ID}"]
```

### GPU-Enabled Dockerfile

```dockerfile
# docker/Dockerfile.gpu
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA
RUN pip3 install torch --index-url https://download.pytorch.org/whl/cu121

# Install Poetry and dependencies
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction

COPY . .

EXPOSE 8100

CMD ["python3", "scripts/run_node.py", "--node-type", "inference"]
```

## Environment Configuration

Create a `.env` file:

```bash
# .env
# Solana Configuration
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com

# Wallet (for nodes)
WALLET_ADDRESS=YourSolanaWalletAddress

# API Keys (for proxy nodes)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
DATABASE_URL=postgresql://postgres:your-secure-password@db:5432/solanalm

# Redis
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET=your-jwt-secret-key
```

## Scaling Nodes

### Scale Inference Nodes

```bash
# Scale to 3 inference nodes
docker-compose up -d --scale inference-node=3

# Check running containers
docker-compose ps
```

### Custom Scaling Configuration

```yaml
# docker-compose.override.yml
version: '3.8'

services:
  inference-node:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## GPU Support

### Install NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### GPU Docker Compose

```yaml
# docker-compose.gpu.yml
version: '3.8'

services:
  inference-node-gpu:
    build:
      context: .
      dockerfile: docker/Dockerfile.gpu
    environment:
      - NODE_TYPE=inference
      - NODE_ID=gpu-inference-1
      - GATEWAY_URL=http://gateway:8001
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

```bash
# Run with GPU support
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## Monitoring

### Add Prometheus and Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gateway'
    static_configs:
      - targets: ['gateway:8001']

  - job_name: 'nodes'
    static_configs:
      - targets: ['inference-node:8100']
```

## Networking

### Custom Network

```yaml
version: '3.8'

networks:
  solanalm-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  gateway:
    networks:
      solanalm-net:
        ipv4_address: 172.20.0.2
```

### External Access

```yaml
services:
  gateway:
    ports:
      - "0.0.0.0:8001:8001"  # All interfaces
    # Or specific IP
    # - "192.168.1.100:8001:8001"
```

## Persistent Storage

### Volume Configuration

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/postgres

  model_cache:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/models
```

### Model Caching

```yaml
services:
  inference-node:
    volumes:
      - model_cache:/app/models
    environment:
      - MODEL_CACHE_DIR=/app/models
```

## Health Checks

### Custom Health Checks

```yaml
services:
  gateway:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  inference-node:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Common Operations

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart gateway

# Restart with rebuild
docker-compose up -d --build gateway
```

### View Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f gateway

# Last 100 lines
docker-compose logs --tail=100 gateway
```

### Update Containers

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build
```

### Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (caution: deletes data)
docker-compose down -v

# Remove unused resources
docker system prune -a
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs gateway

# Check container status
docker-compose ps

# Inspect container
docker inspect solanalm_gateway_1
```

### Connection Issues

```bash
# Check network
docker network inspect solanalm_default

# Test connectivity
docker-compose exec gateway ping db
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Inspect specific container
docker stats solanalm_inference-node_1
```

## Next Steps

- [Kubernetes Deployment](kubernetes.md) - Scale with K8s
- [Production Guide](production.md) - Production best practices
