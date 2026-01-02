# Production Deployment

Best practices for deploying SolanaLM in production environments.

## Production Checklist

Before going to production, ensure:

- [ ] Security hardening complete
- [ ] TLS/SSL configured
- [ ] Rate limiting enabled
- [ ] Monitoring and alerting set up
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan tested
- [ ] Load testing completed
- [ ] Documentation updated

## Infrastructure Requirements

### Minimum Production Setup

| Component | Specification | Count |
|-----------|---------------|-------|
| Gateway | 4 vCPU, 8GB RAM | 2+ |
| Inference Node | 8 vCPU, 16GB RAM, GPU | 3+ |
| Training Node | 8 vCPU, 32GB RAM | 2+ |
| Database | 4 vCPU, 16GB RAM, SSD | 1 (HA) |
| Redis | 2 vCPU, 8GB RAM | 1 (HA) |
| Load Balancer | - | 1 |

### Recommended Production Setup

| Component | Specification | Count |
|-----------|---------------|-------|
| Gateway | 8 vCPU, 16GB RAM | 3+ |
| Inference Node | 16 vCPU, 32GB RAM, A100 | 5+ |
| Training Node | 16 vCPU, 64GB RAM, A100 | 3+ |
| Database | 8 vCPU, 32GB RAM, NVMe | 3 (HA) |
| Redis | 4 vCPU, 16GB RAM | 3 (cluster) |
| Load Balancer | HA pair | 2 |

## Security Hardening

### Network Security

```yaml
# Firewall rules (example)
Inbound:
  - Port 443: HTTPS (public)
  - Port 22: SSH (bastion only)

Internal:
  - Port 8001: Gateway (internal LB)
  - Port 8100-8199: Inference nodes
  - Port 8200-8299: Training nodes
  - Port 5432: PostgreSQL (internal only)
  - Port 6379: Redis (internal only)

Outbound:
  - Port 443: External APIs, Solana RPC
  - Port 8899: Solana RPC
```

### TLS Configuration

```python
# Enable TLS in gateway
from core.gateway.server import GatewayServer
import ssl

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(
    certfile='/etc/ssl/certs/solanalm.crt',
    keyfile='/etc/ssl/private/solanalm.key'
)

gateway = GatewayServer(
    host="0.0.0.0",
    port=443,
    ssl=ssl_context
)
```

### Secret Management

```python
# Use environment variables or secrets manager
import os
from azure.keyvault.secrets import SecretClient
from google.cloud import secretmanager

# Azure Key Vault
def get_secret_azure(name):
    client = SecretClient(vault_url=os.getenv("VAULT_URL"))
    return client.get_secret(name).value

# Google Secret Manager
def get_secret_gcp(name):
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(name=name)
    return response.payload.data.decode()

# AWS Secrets Manager
import boto3

def get_secret_aws(name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=name)
    return response['SecretString']
```

### Authentication

```python
# JWT configuration for production
JWT_CONFIG = {
    "algorithm": "RS256",
    "public_key_path": "/etc/solanalm/jwt-public.pem",
    "private_key_path": "/etc/solanalm/jwt-private.pem",
    "expiration": 3600,  # 1 hour
    "refresh_expiration": 86400 * 7,  # 7 days
    "issuer": "solanalm.io"
}
```

## High Availability

### Gateway HA

```yaml
# HAProxy configuration
frontend gateway_frontend
    bind *:443 ssl crt /etc/ssl/solanalm.pem
    default_backend gateway_backend

backend gateway_backend
    balance roundrobin
    option httpchk GET /health
    server gateway1 10.0.1.10:8001 check
    server gateway2 10.0.1.11:8001 check
    server gateway3 10.0.1.12:8001 check
```

### Database HA

```yaml
# PostgreSQL with Patroni
bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
  postgresql:
    use_pg_rewind: true
    parameters:
      wal_level: replica
      hot_standby: "on"
      max_wal_senders: 10
      max_replication_slots: 10
```

### Redis Cluster

```yaml
# Redis Sentinel configuration
sentinel monitor solanalm-master 10.0.2.10 6379 2
sentinel down-after-milliseconds solanalm-master 5000
sentinel failover-timeout solanalm-master 60000
sentinel parallel-syncs solanalm-master 1
```

## Monitoring

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - /etc/prometheus/alerts/*.yml

scrape_configs:
  - job_name: 'solanalm-gateway'
    static_configs:
      - targets: ['gateway-1:8001', 'gateway-2:8001']

  - job_name: 'solanalm-nodes'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: (inference|training)-node
        action: keep
```

### Alert Rules

```yaml
# alerts/solanalm.yml
groups:
  - name: solanalm
    rules:
      - alert: GatewayDown
        expr: up{job="solanalm-gateway"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Gateway {{ $labels.instance }} is down"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(solanalm_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"

      - alert: LowNodeCount
        expr: count(up{job=~".*-node"} == 1) < 3
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Less than 3 nodes available"

      - alert: HighErrorRate
        expr: rate(solanalm_errors_total[5m]) / rate(solanalm_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Error rate above 5%"
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "SolanaLM Production",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(solanalm_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Latency P95",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(solanalm_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Nodes",
        "type": "stat",
        "targets": [
          {
            "expr": "count(up{job=~\".*-node\"} == 1)"
          }
        ]
      }
    ]
  }
}
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"

# Create backup
pg_dump -h localhost -U solanalm -d solanalm | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://solanalm-backups/postgres/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete
```

### Point-in-Time Recovery

```bash
# Enable WAL archiving
archive_mode = on
archive_command = 'aws s3 cp %p s3://solanalm-backups/wal/%f'

# Recovery
restore_command = 'aws s3 cp s3://solanalm-backups/wal/%f %p'
recovery_target_time = '2024-01-15 12:00:00'
```

### Disaster Recovery

```python
# disaster_recovery.py
class DisasterRecovery:
    def __init__(self, config):
        self.primary_region = config.primary_region
        self.dr_region = config.dr_region

    async def initiate_failover(self):
        """Initiate failover to DR region"""
        # Stop primary
        await self.stop_primary()

        # Promote DR database
        await self.promote_dr_database()

        # Update DNS
        await self.update_dns(self.dr_region)

        # Start DR services
        await self.start_dr_services()

        return FailoverResult(success=True)
```

## Performance Tuning

### Gateway Optimization

```python
# Uvicorn production settings
import uvicorn

uvicorn.run(
    "core.gateway.server:app",
    host="0.0.0.0",
    port=8001,
    workers=4,
    loop="uvloop",
    http="httptools",
    access_log=False,
    limit_concurrency=1000,
    backlog=2048
)
```

### Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '64MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '64MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
ALTER SYSTEM SET max_worker_processes = 8;
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
```

### Caching Strategy

```python
# Redis caching configuration
CACHE_CONFIG = {
    "default_ttl": 300,
    "max_connections": 100,
    "socket_timeout": 5,
    "retry_on_timeout": True,

    # Cache keys
    "model_info_ttl": 3600,
    "node_status_ttl": 30,
    "user_session_ttl": 86400,
}
```

## Logging

### Structured Logging

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Usage
logger.info(
    "request_processed",
    request_id="req_123",
    model="gpt2",
    latency=0.234,
    tokens=100
)
```

### Log Aggregation

```yaml
# Fluentd configuration
<source>
  @type tail
  path /var/log/solanalm/*.log
  pos_file /var/log/fluentd/solanalm.pos
  tag solanalm
  <parse>
    @type json
  </parse>
</source>

<match solanalm.**>
  @type elasticsearch
  host elasticsearch.logging
  port 9200
  logstash_format true
  logstash_prefix solanalm
</match>
```

## Deployment Pipeline

### CI/CD Configuration

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          poetry install
          poetry run pytest

      - name: Build Docker images
        run: |
          docker build -t solanalm/gateway:${{ github.ref_name }} -f docker/Dockerfile.gateway .
          docker build -t solanalm/node:${{ github.ref_name }} -f docker/Dockerfile.node .

      - name: Push to registry
        run: |
          docker push solanalm/gateway:${{ github.ref_name }}
          docker push solanalm/node:${{ github.ref_name }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/gateway gateway=solanalm/gateway:${{ github.ref_name }} -n solanalm
          kubectl rollout status deployment/gateway -n solanalm
```

### Blue-Green Deployment

```bash
#!/bin/bash
# blue-green-deploy.sh

NEW_VERSION=$1
CURRENT=$(kubectl get service gateway -o jsonpath='{.spec.selector.version}')

if [ "$CURRENT" == "blue" ]; then
    TARGET="green"
else
    TARGET="blue"
fi

# Deploy new version
kubectl set image deployment/gateway-$TARGET gateway=solanalm/gateway:$NEW_VERSION

# Wait for rollout
kubectl rollout status deployment/gateway-$TARGET

# Run smoke tests
./smoke-tests.sh gateway-$TARGET

# Switch traffic
kubectl patch service gateway -p "{\"spec\":{\"selector\":{\"version\":\"$TARGET\"}}}"

echo "Deployed $NEW_VERSION to $TARGET"
```

## Cost Optimization

### Resource Right-sizing

```python
# Monitor and recommend sizing
def analyze_resource_usage():
    metrics = prometheus.query_range(
        'avg(container_cpu_usage_seconds_total{pod=~"gateway.*"})',
        start='-7d',
        step='1h'
    )

    avg_cpu = statistics.mean([m.value for m in metrics])
    max_cpu = max([m.value for m in metrics])

    if max_cpu < 0.5:
        return "Consider reducing CPU allocation"
    elif avg_cpu > 0.8:
        return "Consider increasing CPU allocation"
    return "Current sizing is appropriate"
```

### Spot Instances

```yaml
# Use spot/preemptible for inference nodes
nodeSelector:
  cloud.google.com/gke-spot: "true"
tolerations:
  - key: "cloud.google.com/gke-spot"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
```

## Runbook

### Incident Response

```markdown
## Gateway Unresponsive

1. Check pod status: `kubectl get pods -l app=gateway`
2. Check logs: `kubectl logs -l app=gateway --tail=100`
3. Check resources: `kubectl top pods -l app=gateway`
4. Restart if needed: `kubectl rollout restart deployment/gateway`
5. Scale if needed: `kubectl scale deployment/gateway --replicas=5`

## High Latency

1. Check node load: `kubectl top pods -l app=inference-node`
2. Check queue depth: Query Prometheus `solanalm_queue_depth`
3. Scale nodes: `kubectl scale deployment/inference-node --replicas=10`
4. Check database: `SELECT * FROM pg_stat_activity;`

## Node Failures

1. Check node status: `kubectl describe nodes`
2. Check pod distribution: `kubectl get pods -o wide`
3. Cordon failing node: `kubectl cordon <node>`
4. Drain node: `kubectl drain <node> --ignore-daemonsets`
```

## Next Steps

- [Docker Deployment](docker.md) - Container basics
- [Kubernetes Deployment](kubernetes.md) - K8s setup
- [Architecture Overview](../architecture/overview.md) - System design
