# SolanaLM Deployment Guide

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Configuration](#production-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

## Overview

SolanaLM can be deployed in various configurations:
- **Development**: Single machine with simulated payments
- **Testnet**: Multi-node network with Solana testnet integration
- **Production**: Enterprise deployment with high availability and monitoring

## Prerequisites

### System Requirements
- **CPU**: 4+ cores (8+ recommended for inference nodes)
- **RAM**: 8GB minimum (16GB+ for large models)
- **Storage**: 50GB minimum (500GB+ for model storage)
- **GPU**: Optional but recommended (8GB VRAM for local inference)
- **Network**: Stable internet connection with open ports

### Software Requirements
- Python 3.12+
- Poetry (dependency management)
- Docker and Docker Compose
- Kubernetes (for cluster deployment)
- PostgreSQL (production database)
- Redis (caching and queues)

## Local Development

### Quick Start
```bash
# Clone repository
git clone https://github.com/your-org/solanalm.git
cd solanalm

# Install dependencies
poetry install && poetry shell

# Verify setup
python scripts/verify_setup.py

# Start development environment
python scripts/quick_start.py
```

### Manual Setup
```bash
# 1. Start gateway
poetry run python scripts/run_gateway.py

# 2. Start nodes (in separate terminals)
poetry run python scripts/run_node.py --type inference --node-id node1 --wallet WALLET1
poetry run python scripts/run_node.py --type training --node-id node2 --wallet WALLET2

# 3. Test system
poetry run python scripts/test_end_to_end.py
```

### Environment Configuration
Create `.env` file:
```bash
# Network Configuration
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com
GATEWAY_HOST=localhost
GATEWAY_PORT=8001

# Security
JWT_SECRET=your-secret-key
API_KEY_SECRET=your-api-secret

# Database (optional for development)
DATABASE_URL=sqlite:///solanalm.db

# External APIs (optional)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## Docker Deployment

### Development Setup
```bash
# Build image
docker build -t solanalm:latest -f docker/Dockerfile .

# Run with development docker-compose
docker-compose -f docker/docker-compose.yml up -d
```

### Production Deployment with TLS

For production, use the dedicated production docker-compose with nginx TLS termination and Docker secrets:

```bash
# 1. Create Docker secrets (required before first run)
echo "your-very-secure-jwt-secret-key-at-least-32-chars" | docker secret create jwt_secret -
echo "your-secure-admin-api-key-at-least-32-characters" | docker secret create admin_api_key -
echo "your-secure-postgres-password" | docker secret create postgres_password -

# 2. Generate or copy SSL certificates to docker/nginx/ssl/
#    - fullchain.pem (certificate chain)
#    - privkey.pem (private key)

# 3. Create treasury keypair (or use existing)
solana-keygen new -o treasury-keypair.json --no-bip39-passphrase
cat treasury-keypair.json | docker secret create treasury_keyfile -

# 4. Deploy production stack
docker-compose -f docker/docker-compose.production.yml up -d

# 5. Verify deployment
docker-compose -f docker/docker-compose.production.yml ps
curl -k https://localhost/health
```

### Production Docker Compose Features

The production configuration (`docker/docker-compose.production.yml`) includes:

- **Nginx reverse proxy** with TLS 1.2/1.3 termination
- **Docker secrets** for sensitive credentials (no env vars in plaintext)
- **Health checks** for all services with proper dependency ordering
- **Rate limiting** at nginx level (30 req/min for inference, 10 req/min for private inference)
- **Security headers** (HSTS, CSP, X-Frame-Options, etc.)
- **Resource limits** to prevent container resource exhaustion
- **Redis persistence** with AOF for durability
- **Non-root user** in application containers

### Docker Compose (Development)
```yaml
# docker/docker-compose.yml - Development configuration
version: '3.8'

services:
  coordinator:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: solanalm-coordinator
    ports:
      - "8001:8001"
    environment:
      - SOLANA_NETWORK=devnet
    depends_on:
      - redis
      - postgres
    networks:
      - solanalm-network

  redis:
    image: redis:7-alpine
    container_name: solanalm-redis
    ports:
      - "6379:6379"
    networks:
      - solanalm-network

  postgres:
    image: postgres:15-alpine
    container_name: solanalm-postgres
    environment:
      POSTGRES_DB: solanalm
      POSTGRES_USER: solanalm
      POSTGRES_PASSWORD: solanalm
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - solanalm-network

networks:
  solanalm-network:
    driver: bridge

volumes:
  postgres_data:
```

### Deployment Commands
```bash
# Start full stack
docker-compose up -d

# View logs
docker-compose logs -f gateway

# Scale nodes
docker-compose up -d --scale inference-node-1=3

# Update configuration
docker-compose restart gateway

# Stop all services
docker-compose down
```

## Kubernetes Deployment

### Prerequisites
```bash
# Install kubectl and helm
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Deployment with Orchestrator
```bash
# Generate Kubernetes manifests
poetry run python deployment/orchestrator.py \
  --target kubernetes \
  --replicas 3 \
  --output-dir k8s-manifests

# Apply manifests
kubectl apply -f k8s-manifests/

# Check deployment status
kubectl get pods -n solanalm

# Scale deployment
kubectl scale deployment solanalm-inference --replicas=5 -n solanalm
```

### Manual Kubernetes Setup

#### Namespace
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: solanalm
```

#### ConfigMap
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: solanalm-config
  namespace: solanalm
data:
  SOLANA_NETWORK: "devnet"
  GATEWAY_HOST: "0.0.0.0"
  GATEWAY_PORT: "8001"
  DATABASE_URL: "postgresql://solanalm:password@postgres:5432/solanalm"
  REDIS_URL: "redis://redis:6379"
```

#### Deployment
```yaml
# gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: solanalm-gateway
  namespace: solanalm
spec:
  replicas: 2
  selector:
    matchLabels:
      app: solanalm-gateway
  template:
    metadata:
      labels:
        app: solanalm-gateway
    spec:
      containers:
      - name: gateway
        image: solanalm:latest
        command: ["python", "scripts/run_gateway.py"]
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: solanalm-config
        - secretRef:
            name: solanalm-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service
```yaml
# gateway-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: solanalm-gateway
  namespace: solanalm
spec:
  selector:
    app: solanalm-gateway
  ports:
  - port: 8001
    targetPort: 8001
  type: LoadBalancer
```

## Cloud Deployment

### AWS EKS
```bash
# Create EKS cluster
eksctl create cluster --name solanalm-cluster --region us-west-2

# Deploy with Helm
helm install solanalm ./helm/solanalm \
  --set image.tag=latest \
  --set solana.network=mainnet-beta \
  --set ingress.enabled=true \
  --set autoscaling.enabled=true
```

### Google GKE
```bash
# Create GKE cluster
gcloud container clusters create solanalm-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10

# Deploy
kubectl apply -f k8s-manifests/
```

### Azure AKS
```bash
# Create AKS cluster
az aks create \
  --resource-group solanalm-rg \
  --name solanalm-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Deploy
kubectl apply -f k8s-manifests/
```

## Production Configuration

### Required Environment Variables

For production (testnet/mainnet), the following environment variables are **required** and validated:

```bash
# Security (REQUIRED - minimum 32 characters, no weak patterns)
JWT_SECRET_KEY=your-secure-jwt-secret-at-least-32-characters
ADMIN_API_KEY=your-secure-admin-api-key-at-least-32-characters

# Database
DATABASE_URL=postgresql://solanalm:password@postgres:5432/solanalm
REDIS_URL=redis://redis:6379/0

# CORS (comma-separated origins - no wildcards allowed in production)
ALLOWED_ORIGINS=https://app.solanalm.io,https://dashboard.solanalm.io

# Solana Configuration
SOLANA_NETWORK=testnet
SOLANA_RPC_URL=https://api.testnet.solana.com
SOLANALM_ENVIRONMENT=testnet

# Treasury Wallet (file path to Solana keypair JSON)
TREASURY_KEYFILE_PATH=/path/to/treasury-keypair.json
```

### Docker Secrets Support

For Docker deployments, use the `_FILE` suffix pattern for secrets:

```bash
# Environment variables with _FILE suffix read from Docker secrets
JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
ADMIN_API_KEY_FILE=/run/secrets/admin_api_key
TREASURY_KEYFILE_PATH=/run/secrets/treasury_keyfile
```

### Security Hardening
```bash
# Generate secure secrets (production-grade)
python -c "import secrets; print(secrets.token_urlsafe(48))"  # For JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"  # For ADMIN_API_KEY
```

### Database Configuration
```sql
-- Create production database
CREATE DATABASE solanalm;
CREATE USER solanalm WITH ENCRYPTED PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE solanalm TO solanalm;

-- Configure connection pooling
-- max_connections = 200
-- shared_preload_libraries = 'pg_stat_statements'
```

### Load Balancer Configuration
```nginx
# nginx.conf
upstream solanalm_gateway {
    server gateway-1:8001;
    server gateway-2:8001;
    server gateway-3:8001;
}

server {
    listen 80;
    server_name solanalm.example.com;

    location / {
        proxy_pass http://solanalm_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
}
```

### SSL/TLS Configuration
```bash
# Generate certificates with Let's Encrypt
certbot --nginx -d solanalm.example.com

# Or use existing certificates
kubectl create secret tls solanalm-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n solanalm
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'solanalm'
    static_configs:
      - targets: ['gateway:8001', 'node-1:8100', 'node-2:8200']
    metrics_path: /metrics/prometheus
    scrape_interval: 10s
```

### Grafana Dashboard
```bash
# Import SolanaLM dashboard
curl -X POST \
  http://admin:admin@grafana:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana-dashboard.json
```

### Alerting Rules
```yaml
# alerts.yml
groups:
  - name: solanalm
    rules:
      - alert: HighErrorRate
        expr: rate(solanalm_errors_total[5m]) > 0.1
        for: 2m
        annotations:
          summary: "High error rate detected"

      - alert: NodeDown
        expr: up{job="solanalm"} == 0
        for: 1m
        annotations:
          summary: "SolanaLM node is down"

      - alert: HighLatency
        expr: solanalm_response_time_seconds > 5
        for: 5m
        annotations:
          summary: "High response latency"
```

## Troubleshooting

### Common Issues

#### Gateway Not Starting
```bash
# Check logs
docker logs solanalm-gateway

# Common causes:
# 1. Port already in use
sudo netstat -tlnp | grep :8001

# 2. Database connection failed
ping postgres-host

# 3. Missing environment variables
env | grep SOLANA
```

#### Nodes Not Registering
```bash
# Check node logs
kubectl logs -f deployment/solanalm-inference -n solanalm

# Verify gateway connectivity
curl http://gateway:8001/health

# Check node configuration
kubectl describe configmap solanalm-config -n solanalm
```

#### High Memory Usage
```bash
# Monitor memory usage
kubectl top pods -n solanalm

# Reduce model cache size
kubectl set env deployment/solanalm-inference TRANSFORMERS_CACHE=/tmp/cache -n solanalm

# Configure resource limits
kubectl patch deployment solanalm-inference -p '{"spec":{"template":{"spec":{"containers":[{"name":"inference","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

#### Slow Response Times
```bash
# Check network latency
ping gateway-host

# Monitor request queues
curl http://gateway:8001/metrics | grep queue

# Scale up nodes
kubectl scale deployment solanalm-inference --replicas=5 -n solanalm
```

### Performance Tuning

#### Database Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM requests WHERE created_at > NOW() - INTERVAL '1 hour';

-- Create indexes
CREATE INDEX idx_requests_created_at ON requests(created_at);
CREATE INDEX idx_nodes_status ON nodes(status, last_seen);
```

#### Application Tuning
```python
# Increase worker processes
# uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Configure connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

#### Kubernetes Tuning
```yaml
# Configure resource quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: solanalm-quota
  namespace: solanalm
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
```

### Health Checks

#### Gateway Health
```bash
curl http://gateway:8001/health
# Should return 200 with status: healthy
```

#### Node Health
```bash
curl http://node:8100/health
# Should return node status and capabilities
```

#### Database Health
```bash
# Check connection
psql -h postgres-host -U solanalm -d solanalm -c "SELECT 1;"

# Check table sizes
psql -h postgres-host -U solanalm -d solanalm -c "
  SELECT schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
  FROM pg_tables WHERE schemaname = 'public';"
```

### Backup and Recovery

#### Database Backup
```bash
# Create backup
pg_dump -h postgres-host -U solanalm solanalm > solanalm_backup.sql

# Automated backups
0 2 * * * pg_dump -h postgres-host -U solanalm solanalm | gzip > /backups/solanalm_$(date +\%Y\%m\%d).sql.gz
```

#### Configuration Backup
```bash
# Backup Kubernetes resources
kubectl get all,configmap,secret -n solanalm -o yaml > solanalm_k8s_backup.yaml

# Backup environment files
cp .env .env.backup
```

#### Recovery Procedure
```bash
# 1. Stop services
kubectl scale deployment --all --replicas=0 -n solanalm

# 2. Restore database
psql -h postgres-host -U solanalm -d solanalm < solanalm_backup.sql

# 3. Restore configuration
kubectl apply -f solanalm_k8s_backup.yaml

# 4. Start services
kubectl scale deployment --all --replicas=1 -n solanalm
```