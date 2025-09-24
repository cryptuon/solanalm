# 🏭 Production Deployment Guide

Comprehensive guide for deploying SolanaLM in production environments with security, scalability, and reliability.

## 📋 Pre-deployment Checklist

### Infrastructure Requirements

**Minimum Production Setup:**
- **Gateway Servers**: 2+ instances (load balanced)
- **Inference Nodes**: 5+ instances (geographic distribution)
- **Training Nodes**: 3+ instances (GPU-enabled recommended)
- **Monitoring**: 1 dedicated instance
- **Database**: PostgreSQL cluster (optional but recommended)

**Hardware Specifications:**

```yaml
Gateway Servers:
  CPU: 4+ cores
  RAM: 8+ GB
  Storage: 100+ GB SSD
  Network: 1+ Gbps

Inference Nodes:
  CPU: 8+ cores
  RAM: 16+ GB
  Storage: 200+ GB SSD
  Network: 1+ Gbps
  GPU: Optional (for local model hosting)

Training Nodes:
  CPU: 16+ cores
  RAM: 32+ GB
  Storage: 500+ GB SSD
  Network: 1+ Gbps
  GPU: Recommended (24+ GB VRAM)
```

### Security Prerequisites

**TLS Certificates:**
```bash
# Generate production TLS certificates
openssl req -new -newkey rsa:4096 -x509 -sha256 -days 365 \
  -nodes -out solanalm.crt -keyout solanalm.key \
  -subj "/C=US/ST=CA/L=SF/O=SolanaLM/CN=api.solanalm.com"

# Or use Let's Encrypt
certbot certonly --standalone -d api.solanalm.com
```

**Environment Variables:**
```bash
# Security keys
export SOLANALM_ADMIN_KEY="$(openssl rand -hex 32)"
export SOLANALM_JWT_SECRET="$(openssl rand -hex 64)"
export SOLANALM_ENCRYPTION_KEY="$(openssl rand -hex 32)"

# Solana configuration
export SOLANALM_SOLANA_NETWORK="mainnet-beta"
export SOLANALM_HOT_WALLET_PRIVATE_KEY="your-hot-wallet-key"
export SOLANALM_COLD_WALLET_ADDRESS="your-cold-wallet-address"

# Database configuration
export SOLANALM_DATABASE_URL="postgresql://user:password@localhost:5432/solanalm"
```

## 🚀 Deployment Process

### 1. Infrastructure Setup

**Using Docker Compose (Recommended):**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  gateway:
    build: .
    environment:
      - ENVIRONMENT=production
      - SOLANALM_ADMIN_KEY=${SOLANALM_ADMIN_KEY}
      - SOLANALM_DATABASE_URL=${SOLANALM_DATABASE_URL}
    ports:
      - "443:8001"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - /etc/ssl/certs:/etc/ssl/certs:ro
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 8G
          cpus: '4'
    healthcheck:
      test: ["CMD", "curl", "-f", "https://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  inference-node:
    build: .
    environment:
      - NODE_TYPE=inference
      - ENVIRONMENT=production
    deploy:
      replicas: 5
      resources:
        limits:
          memory: 16G
          cpus: '8'

  training-node:
    build: .
    environment:
      - NODE_TYPE=training
      - ENVIRONMENT=production
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 32G
          cpus: '16'

  monitoring:
    build: .
    environment:
      - SERVICE=monitoring
      - ENVIRONMENT=production
    ports:
      - "8300:8300"

  database:
    image: postgres:15
    environment:
      - POSTGRES_DB=solanalm
      - POSTGRES_USER=solanalm
      - POSTGRES_PASSWORD=${DATABASE_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'

volumes:
  postgres_data:
```

**Deploy with Docker Compose:**
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Check deployment status
docker-compose ps
docker-compose logs gateway
```

### 2. Using Kubernetes (Advanced)

**Kubernetes Deployment:**

```yaml
# k8s/gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: solanalm-gateway
spec:
  replicas: 3
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
        ports:
        - containerPort: 8001
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: SOLANALM_ADMIN_KEY
          valueFrom:
            secretKeyRef:
              name: solanalm-secrets
              key: admin-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
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

---
apiVersion: v1
kind: Service
metadata:
  name: solanalm-gateway-service
spec:
  selector:
    app: solanalm-gateway
  ports:
  - protocol: TCP
    port: 443
    targetPort: 8001
  type: LoadBalancer
```

**Deploy to Kubernetes:**
```bash
# Apply configurations
kubectl apply -f k8s/

# Check deployment
kubectl get pods
kubectl get services
kubectl logs -f deployment/solanalm-gateway
```

### 3. Manual Deployment

**Production Deployment Script:**

```bash
#!/bin/bash
# production-deploy.sh

set -e

# Configuration
DEPLOY_ENV="production"
GATEWAY_INSTANCES=2
INFERENCE_NODES=5
TRAINING_NODES=3

echo "🏭 Starting SolanaLM Production Deployment"

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx postgresql-client

# Create application user
sudo useradd -m -s /bin/bash solanalm
sudo usermod -aG sudo solanalm

# Setup application directory
sudo mkdir -p /opt/solanalm
sudo chown solanalm:solanalm /opt/solanalm

# Switch to application user
sudo -u solanalm bash << 'EOF'
cd /opt/solanalm

# Clone and setup application
git clone https://github.com/yourusername/solanalm.git .
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup configuration
cp config/deployment.yaml config/production.yaml
cp config/security.yaml config/production-security.yaml

# Create logs directory
mkdir -p logs data tmp

# Setup environment
cat > .env << 'ENVEOF'
ENVIRONMENT=production
SOLANALM_CONFIG_FILE=config/production.yaml
SOLANALM_SECURITY_CONFIG=config/production-security.yaml
SOLANALM_ADMIN_KEY=$SOLANALM_ADMIN_KEY
SOLANALM_DATABASE_URL=$SOLANALM_DATABASE_URL
ENVEOF

EOF

# Deploy using the deployment script
sudo -u solanalm python3 /opt/solanalm/scripts/deploy.py deploy \
  --config /opt/solanalm/config/production.yaml

echo "✅ Production deployment completed"
```

## 🔒 Security Hardening

### 1. Network Security

**Firewall Configuration:**
```bash
# UFW firewall setup
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (restrict to your IP)
sudo ufw allow from YOUR_IP_ADDRESS to any port 22

# Allow HTTPS traffic
sudo ufw allow 443/tcp

# Allow monitoring (restrict to internal network)
sudo ufw allow from 10.0.0.0/8 to any port 8300

# Enable firewall
sudo ufw enable
```

**Nginx Reverse Proxy:**
```nginx
# /etc/nginx/sites-available/solanalm
server {
    listen 443 ssl http2;
    server_name api.solanalm.com;

    # SSL configuration
    ssl_certificate /etc/ssl/certs/solanalm.crt;
    ssl_certificate_key /etc/ssl/private/solanalm.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Proxy to SolanaLM gateway
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Block suspicious requests
    location ~* \.(php|asp|aspx|jsp)$ {
        return 404;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.solanalm.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. Application Security

**Security Configuration:**
```yaml
# config/production-security.yaml
tls:
  enabled: true
  cert_file: "/etc/ssl/certs/solanalm.crt"
  key_file: "/etc/ssl/private/solanalm.key"

auth:
  api_keys:
    enabled: true
    key_rotation_days: 30
  wallet_auth:
    enabled: true
    signature_verification: true

rate_limiting:
  enabled: true
  default_limits:
    requests_per_minute: 30
    requests_per_hour: 500

input_validation:
  enabled: true
  max_prompt_length: 5000
  blocked_patterns:
    - "eval\\("
    - "exec\\("
    - "<script"

privacy:
  logging:
    log_requests: false
    log_responses: false
    log_metadata_only: true
```

### 3. Database Security

**PostgreSQL Security:**
```sql
-- Create production database and user
CREATE DATABASE solanalm;
CREATE USER solanalm_app WITH PASSWORD 'secure_password_here';

-- Grant minimal permissions
GRANT CONNECT ON DATABASE solanalm TO solanalm_app;
GRANT USAGE ON SCHEMA public TO solanalm_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO solanalm_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO solanalm_app;

-- Enable row-level security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
```

**Database Configuration:**
```ini
# /etc/postgresql/15/main/postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'

# Connection security
listen_addresses = 'localhost'
port = 5432
max_connections = 200

# Logging
log_connections = on
log_disconnections = on
log_statement = 'mod'  # Log data modification statements

# Performance
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

## 📊 Monitoring and Observability

### 1. Application Monitoring

**Prometheus Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'solanalm-gateway'
    static_configs:
      - targets: ['localhost:8001']
    scrape_interval: 5s
    metrics_path: '/metrics'

  - job_name: 'solanalm-nodes'
    static_configs:
      - targets: ['localhost:8100', 'localhost:8101', 'localhost:8102']

  - job_name: 'solanalm-monitoring'
    static_configs:
      - targets: ['localhost:8300']
```

**Grafana Dashboard:**
```json
{
  "dashboard": {
    "title": "SolanaLM Production Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(solanalm_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Privacy Network Health",
        "type": "singlestat",
        "targets": [
          {
            "expr": "solanalm_privacy_capable_nodes",
            "legendFormat": "Privacy Nodes"
          }
        ]
      }
    ]
  }
}
```

### 2. Log Management

**Centralized Logging with ELK Stack:**
```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    volumes:
      - elastic_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

**Logstash Configuration:**
```ruby
# logstash.conf
input {
  file {
    path => "/var/log/solanalm/*.log"
    start_position => "beginning"
  }
}

filter {
  if [path] =~ /access/ {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
  }

  if [path] =~ /error/ {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "solanalm-logs-%{+YYYY.MM.dd}"
  }
}
```

## 🔄 Backup and Recovery

### 1. Database Backup

**Automated Backup Script:**
```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/opt/backups/solanalm"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="solanalm_backup_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U solanalm_app -d solanalm \
  --no-password --verbose --format=custom \
  --file="${BACKUP_DIR}/${BACKUP_FILE}"

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# Upload to cloud storage (S3 example)
aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}.gz" \
  s3://solanalm-backups/database/

# Clean up old backups (keep last 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Database backup completed: ${BACKUP_FILE}.gz"
```

**Schedule with Cron:**
```bash
# Add to crontab
0 2 * * * /opt/solanalm/scripts/backup-database.sh
```

### 2. Application State Backup

**Configuration Backup:**
```bash
#!/bin/bash
# backup-config.sh

BACKUP_DIR="/opt/backups/solanalm/config"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration files
tar -czf "${BACKUP_DIR}/config_${DATE}.tar.gz" \
  /opt/solanalm/config/ \
  /opt/solanalm/.env \
  /etc/nginx/sites-available/solanalm

# Upload to cloud storage
aws s3 cp "${BACKUP_DIR}/config_${DATE}.tar.gz" \
  s3://solanalm-backups/config/

echo "Configuration backup completed"
```

### 3. Disaster Recovery

**Recovery Procedure:**
```bash
#!/bin/bash
# disaster-recovery.sh

echo "🚨 Starting SolanaLM Disaster Recovery"

# 1. Restore database
echo "Restoring database..."
LATEST_BACKUP=$(aws s3 ls s3://solanalm-backups/database/ | sort | tail -1 | awk '{print $4}')
aws s3 cp "s3://solanalm-backups/database/${LATEST_BACKUP}" /tmp/
gunzip "/tmp/${LATEST_BACKUP}"

# Restore database
pg_restore -h localhost -U solanalm_app -d solanalm \
  --clean --if-exists --verbose "/tmp/${LATEST_BACKUP%.gz}"

# 2. Restore configuration
echo "Restoring configuration..."
LATEST_CONFIG=$(aws s3 ls s3://solanalm-backups/config/ | sort | tail -1 | awk '{print $4}')
aws s3 cp "s3://solanalm-backups/config/${LATEST_CONFIG}" /tmp/
tar -xzf "/tmp/${LATEST_CONFIG}" -C /

# 3. Restart services
echo "Restarting services..."
sudo systemctl restart nginx
sudo systemctl restart solanalm-gateway
sudo systemctl restart solanalm-nodes

# 4. Verify recovery
echo "Verifying recovery..."
curl -f https://api.solanalm.com/health || echo "❌ Health check failed"

echo "✅ Disaster recovery completed"
```

## 📈 Scaling and Performance

### 1. Horizontal Scaling

**Auto-scaling with Docker Swarm:**
```yaml
# docker-stack.yml
version: '3.8'

services:
  gateway:
    image: solanalm:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 8G
          cpus: '4'
        reservations:
          memory: 4G
          cpus: '2'

  inference-node:
    image: solanalm:latest
    deploy:
      replicas: 5
      placement:
        constraints:
          - node.role == worker
```

**Deploy Stack:**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-stack.yml solanalm

# Scale services
docker service scale solanalm_inference-node=10
```

### 2. Performance Optimization

**Application Performance:**
```python
# Production optimizations in core/gateway/server.py

# Use production ASGI server
if __name__ == "__main__":
    import gunicorn.app.wsgiapp as wsgi

    # Gunicorn configuration
    gunicorn_config = {
        'bind': '0.0.0.0:8001',
        'workers': 4,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'worker_connections': 1000,
        'max_requests': 1000,
        'max_requests_jitter': 100,
        'timeout': 60,
        'keepalive': 2,
        'preload_app': True
    }
```

**Database Optimization:**
```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_requests_timestamp ON requests(timestamp);
CREATE INDEX CONCURRENTLY idx_nodes_status ON nodes(status, node_type);
CREATE INDEX CONCURRENTLY idx_circuits_created_at ON circuits(created_at);

-- Update statistics
ANALYZE;

-- Configure connection pooling
-- Set in application configuration
DATABASE_URL="postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30"
```

### 3. Load Balancing

**HAProxy Configuration:**
```
# haproxy.cfg
global
    daemon
    chroot /var/lib/haproxy
    user haproxy
    group haproxy

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend solanalm_frontend
    bind *:443 ssl crt /etc/ssl/certs/solanalm.pem
    redirect scheme https if !{ ssl_fc }
    default_backend solanalm_gateway

backend solanalm_gateway
    balance roundrobin
    option httpchk GET /health
    server gateway1 10.0.1.10:8001 check
    server gateway2 10.0.1.11:8001 check
    server gateway3 10.0.1.12:8001 check
```

## 🔍 Production Troubleshooting

### Common Issues and Solutions

**1. High Latency**
```bash
# Check system resources
htop
iostat -x 1
netstat -tuln

# Check application metrics
curl https://api.solanalm.com/metrics

# Check database performance
psql -d solanalm -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

**2. Memory Issues**
```bash
# Monitor memory usage
free -h
cat /proc/meminfo

# Check for memory leaks
valgrind --tool=memcheck --leak-check=full python app.py

# Optimize garbage collection
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2
```

**3. Database Connection Issues**
```bash
# Check database connections
psql -d solanalm -c "SELECT count(*) FROM pg_stat_activity;"

# Check connection pool
curl https://api.solanalm.com/debug/db-pool

# Restart connection pool
sudo systemctl restart solanalm-gateway
```

### Emergency Response

**Incident Response Checklist:**

1. **Assess Impact**
   - Check monitoring dashboards
   - Verify service availability
   - Identify affected users/regions

2. **Immediate Mitigation**
   ```bash
   # Scale up resources
   docker service scale solanalm_gateway=6

   # Enable maintenance mode
   curl -X POST https://api.solanalm.com/admin/maintenance \
     -H "X-Admin-Key: $ADMIN_KEY"
   ```

3. **Root Cause Analysis**
   - Check logs: `journalctl -u solanalm-gateway -f`
   - Review metrics in Grafana
   - Analyze error patterns

4. **Recovery Actions**
   - Apply fixes
   - Gradual traffic restoration
   - Monitor for regression

**Contact Information:**
- **On-call Engineer**: +1-555-0123
- **Security Team**: security@solanalm.com
- **Infrastructure**: ops@solanalm.com

---

## 📝 Production Checklist

Before going live, ensure:

- [ ] TLS certificates installed and configured
- [ ] Security configurations applied
- [ ] Database properly secured and backed up
- [ ] Monitoring and alerting set up
- [ ] Load balancing configured
- [ ] Auto-scaling policies defined
- [ ] Backup and recovery procedures tested
- [ ] Incident response plan documented
- [ ] Performance benchmarks established
- [ ] Security audit completed
- [ ] Compliance requirements met
- [ ] Staff training completed

**🎉 Your SolanaLM production deployment is ready for the world of privacy-preserving AI!**