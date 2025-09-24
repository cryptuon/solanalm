#!/usr/bin/env python3

"""
Production Deployment Script for SolanaLM

Automates deployment of SolanaLM network components for production use.
"""

import os
import sys
import subprocess
import json
import time
import argparse
from pathlib import Path

# Add core to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config.settings import get_settings, NetworkEnvironment


class SolanaLMDeployment:
    """Production deployment manager"""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.settings = get_settings()
        self.project_root = Path(__file__).parent.parent

        # Deployment configuration
        self.services = {
            "gateway": {"port": 8001, "replicas": 2},
            "inference_node": {"port": 8100, "replicas": 1},
            "proxy_node": {"port": 8200, "replicas": 1},
            "redis": {"port": 6379, "replicas": 1},
            "postgres": {"port": 5432, "replicas": 1}
        }

    def check_requirements(self):
        """Check deployment requirements"""
        print("🔍 Checking deployment requirements...")

        required_commands = ["docker", "docker-compose", "poetry"]
        missing_commands = []

        for cmd in required_commands:
            try:
                subprocess.run([cmd, "--version"], capture_output=True, check=True)
                print(f"  ✅ {cmd} found")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_commands.append(cmd)
                print(f"  ❌ {cmd} not found")

        if missing_commands:
            print(f"\n❌ Missing required commands: {', '.join(missing_commands)}")
            return False

        # Check environment variables
        required_env = ["SOLANA_NETWORK", "DATABASE_URL"]
        missing_env = []

        for env_var in required_env:
            if not os.getenv(env_var):
                missing_env.append(env_var)

        if missing_env and self.environment == "production":
            print(f"⚠️  Missing environment variables (optional for testing): {', '.join(missing_env)}")

        return True

    def create_production_docker_compose(self):
        """Create production docker-compose configuration"""
        print("📝 Creating production docker-compose configuration...")

        compose_config = {
            "version": "3.8",
            "services": {
                "gateway": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile"
                    },
                    "ports": [f"{self.services['gateway']['port']}:8001"],
                    "environment": [
                        "SOLANALM_ENVIRONMENT=production",
                        "SOLANA_NETWORK=${SOLANA_NETWORK:-mainnet-beta}",
                        "DATABASE_URL=${DATABASE_URL}",
                        "REDIS_URL=redis://redis:6379",
                        "GATEWAY_HOST=0.0.0.0",
                        "GATEWAY_PORT=8001"
                    ],
                    "depends_on": ["redis", "postgres"],
                    "restart": "unless-stopped",
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8001/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3
                    },
                    "deploy": {
                        "replicas": self.services['gateway']['replicas']
                    },
                    "command": ["python3", "scripts/run_gateway.py"]
                },

                "inference-node": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile"
                    },
                    "ports": [f"{self.services['inference_node']['port']}:8100"],
                    "environment": [
                        "NODE_ID=production-inference-node-1",
                        "WALLET_ADDRESS=${INFERENCE_NODE_WALLET}",
                        "NODE_TYPE=inference",
                        "GATEWAY_URL=http://gateway:8001",
                        "GPU_ENABLED=true"
                    ],
                    "depends_on": ["gateway"],
                    "restart": "unless-stopped",
                    "deploy": {
                        "resources": {
                            "reservations": {
                                "devices": [
                                    {
                                        "driver": "nvidia",
                                        "count": "all",
                                        "capabilities": ["gpu"]
                                    }
                                ]
                            }
                        }
                    },
                    "command": ["python3", "scripts/run_node.py", "--type", "inference"]
                },

                "proxy-node": {
                    "build": {
                        "context": ".",
                        "dockerfile": "docker/Dockerfile"
                    },
                    "ports": [f"{self.services['proxy_node']['port']}:8200"],
                    "environment": [
                        "NODE_ID=production-proxy-node-1",
                        "WALLET_ADDRESS=${PROXY_NODE_WALLET}",
                        "NODE_TYPE=proxy",
                        "GATEWAY_URL=http://gateway:8001",
                        "OPENAI_API_KEY=${OPENAI_API_KEY}",
                        "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
                    ],
                    "depends_on": ["gateway"],
                    "restart": "unless-stopped",
                    "command": ["python3", "scripts/run_node.py", "--type", "proxy"]
                },

                "redis": {
                    "image": "redis:7-alpine",
                    "ports": ["6379:6379"],
                    "volumes": ["redis_data:/data"],
                    "restart": "unless-stopped",
                    "command": "redis-server --appendonly yes"
                },

                "postgres": {
                    "image": "postgres:15-alpine",
                    "environment": [
                        "POSTGRES_DB=solanalm",
                        "POSTGRES_USER=${POSTGRES_USER:-solanalm}",
                        "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
                    ],
                    "volumes": [
                        "postgres_data:/var/lib/postgresql/data",
                        "./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql"
                    ],
                    "restart": "unless-stopped"
                },

                "nginx": {
                    "image": "nginx:alpine",
                    "ports": ["80:80", "443:443"],
                    "volumes": [
                        "./nginx/nginx.conf:/etc/nginx/nginx.conf",
                        "./nginx/ssl:/etc/nginx/ssl"
                    ],
                    "depends_on": ["gateway"],
                    "restart": "unless-stopped"
                }
            },

            "volumes": ["redis_data:", "postgres_data:"],

            "networks": {
                "default": {
                    "name": "solanalm-production"
                }
            }
        }

        # Write docker-compose.production.yml
        compose_file = self.project_root / "docker-compose.production.yml"
        with open(compose_file, 'w') as f:
            import yaml
            yaml.dump(compose_config, f, default_flow_style=False)

        print(f"  ✅ Created {compose_file}")

    def create_nginx_config(self):
        """Create nginx configuration for load balancing"""
        print("📝 Creating nginx configuration...")

        nginx_dir = self.project_root / "nginx"
        nginx_dir.mkdir(exist_ok=True)

        nginx_config = """
events {
    worker_connections 1024;
}

http {
    upstream solanalm_gateway {
        server gateway:8001;
    }

    upstream solanalm_inference {
        server inference-node:8100;
    }

    server {
        listen 80;
        server_name _;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        limit_req zone=api burst=20 nodelay;

        # Gateway API
        location /v1/ {
            proxy_pass http://solanalm_gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeout settings
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check
        location /health {
            proxy_pass http://solanalm_gateway/health;
            access_log off;
        }

        # Admin interface (restrict access)
        location /admin {
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 192.168.0.0/16;
            deny all;

            proxy_pass http://solanalm_gateway;
            proxy_set_header Host $host;
        }
    }
}
"""

        nginx_conf = nginx_dir / "nginx.conf"
        with open(nginx_conf, 'w') as f:
            f.write(nginx_config)

        print(f"  ✅ Created {nginx_conf}")

    def create_env_template(self):
        """Create production environment template"""
        print("📝 Creating production environment template...")

        env_template = """# SolanaLM Production Environment Configuration

# Network Configuration
SOLANALM_ENVIRONMENT=production
SOLANA_NETWORK=mainnet-beta
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Database Configuration
DATABASE_URL=postgresql://solanalm:YOUR_PASSWORD@postgres:5432/solanalm
POSTGRES_USER=solanalm
POSTGRES_PASSWORD=YOUR_STRONG_PASSWORD_HERE

# Node Configuration
INFERENCE_NODE_WALLET=YOUR_INFERENCE_NODE_WALLET_ADDRESS
PROXY_NODE_WALLET=YOUR_PROXY_NODE_WALLET_ADDRESS

# API Keys (for proxy nodes)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Security
JWT_SECRET_KEY=your-jwt-secret-key-generate-random
ADMIN_API_KEY=your-admin-api-key-generate-random

# Logging
LOG_LEVEL=INFO

# Optional: Custom pricing
BASE_INFERENCE_COST_SOL=0.001
BASE_TRAINING_REWARD_SOL=0.1
PROXY_MARKUP_MULTIPLIER=2.0
"""

        env_file = self.project_root / ".env.production"
        with open(env_file, 'w') as f:
            f.write(env_template)

        print(f"  ✅ Created {env_file}")
        print("  ⚠️  Remember to update with your actual values!")

    def create_init_db_script(self):
        """Create database initialization script"""
        print("📝 Creating database initialization script...")

        init_sql = """
-- SolanaLM Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Node registry table
CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) UNIQUE NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    wallet_address VARCHAR(255) NOT NULL,
    endpoint_url VARCHAR(255) NOT NULL,
    supported_models JSONB NOT NULL,
    hardware_specs JSONB NOT NULL,
    pricing_config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'offline',
    reputation_score DECIMAL(3,2) DEFAULT 1.0,
    total_requests INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2) DEFAULT 1.0,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Training rounds table
CREATE TABLE IF NOT EXISTS training_rounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    round_id VARCHAR(255) UNIQUE NOT NULL,
    model VARCHAR(255) NOT NULL,
    participating_nodes JSONB NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER NOT NULL,
    reward_per_node DECIMAL(10,6) NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_signature VARCHAR(255) UNIQUE NOT NULL,
    from_wallet VARCHAR(255) NOT NULL,
    to_wallet VARCHAR(255) NOT NULL,
    amount_sol DECIMAL(12,6) NOT NULL,
    service_type VARCHAR(100) NOT NULL,
    metadata JSONB,
    block_height BIGINT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Request logs table
CREATE TABLE IF NOT EXISTS request_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(255) NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    processing_time DECIMAL(8,3),
    cost_sol DECIMAL(10,6),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nodes_node_id ON nodes(node_id);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_training_rounds_status ON training_rounds(status);
CREATE INDEX IF NOT EXISTS idx_transactions_signature ON transactions(transaction_signature);
CREATE INDEX IF NOT EXISTS idx_request_logs_created_at ON request_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_request_logs_node_id ON request_logs(node_id);

-- Insert default data
INSERT INTO nodes (node_id, node_type, wallet_address, endpoint_url, supported_models, hardware_specs, pricing_config)
VALUES (
    'system-proxy-node',
    'proxy',
    'SystemProxyWallet',
    'http://proxy-node:8200',
    '["gpt-3.5-turbo", "gpt-4", "claude-3-haiku"]',
    '{"cpu_cores": 4, "ram_gb": 8, "storage_gb": 100, "network_speed_mbps": 1000}',
    '{"per_request": 0.01, "per_token": 0.0005, "minimum_payment": 0.005}'
) ON CONFLICT (node_id) DO NOTHING;
"""

        scripts_dir = self.project_root / "scripts"
        init_file = scripts_dir / "init_db.sql"
        with open(init_file, 'w') as f:
            f.write(init_sql)

        print(f"  ✅ Created {init_file}")

    def build_images(self):
        """Build Docker images"""
        print("🔨 Building Docker images...")

        try:
            subprocess.run([
                "docker-compose", "-f", "docker-compose.production.yml",
                "build", "--no-cache"
            ], check=True, cwd=self.project_root)
            print("  ✅ Images built successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Image build failed: {e}")
            return False

        return True

    def deploy_services(self):
        """Deploy services using docker-compose"""
        print("🚀 Deploying services...")

        try:
            # Start core services first
            subprocess.run([
                "docker-compose", "-f", "docker-compose.production.yml",
                "up", "-d", "redis", "postgres"
            ], check=True, cwd=self.project_root)

            print("  ✅ Database services started")

            # Wait for databases to be ready
            print("  ⏳ Waiting for databases to be ready...")
            time.sleep(10)

            # Start application services
            subprocess.run([
                "docker-compose", "-f", "docker-compose.production.yml",
                "up", "-d"
            ], check=True, cwd=self.project_root)

            print("  ✅ All services started")

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Deployment failed: {e}")
            return False

        return True

    def verify_deployment(self):
        """Verify deployment is working"""
        print("✅ Verifying deployment...")

        import requests
        import time

        # Wait for services to start
        print("  ⏳ Waiting for services to start...")
        time.sleep(30)

        # Check gateway health
        try:
            response = requests.get("http://localhost:8001/health", timeout=10)
            if response.status_code == 200:
                print("  ✅ Gateway is healthy")
            else:
                print(f"  ❌ Gateway health check failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Gateway not accessible: {e}")

        # Check OpenAI compatibility
        try:
            response = requests.get("http://localhost:8001/v1/models", timeout=10)
            if response.status_code == 200:
                models = response.json()
                print(f"  ✅ OpenAI API working, {len(models.get('data', []))} models available")
            else:
                print(f"  ❌ OpenAI API check failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ OpenAI API not accessible: {e}")

    def show_deployment_info(self):
        """Show deployment information"""
        print("\n🎉 Deployment Complete!")
        print("=" * 50)

        print("\n📊 Service Status:")
        try:
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.production.yml", "ps"
            ], capture_output=True, text=True, cwd=self.project_root)
            print(result.stdout)
        except Exception as e:
            print(f"Error getting service status: {e}")

        print("\n🌐 Access Points:")
        print("  Gateway API: http://localhost:8001")
        print("  OpenAI Compatible API: http://localhost:8001/v1")
        print("  Health Check: http://localhost:8001/health")
        print("  API Documentation: http://localhost:8001/docs")

        print("\n🔧 Management Commands:")
        print("  View logs: docker-compose -f docker-compose.production.yml logs -f")
        print("  Restart: docker-compose -f docker-compose.production.yml restart")
        print("  Stop: docker-compose -f docker-compose.production.yml down")
        print("  Update: docker-compose -f docker-compose.production.yml pull && docker-compose up -d")

        print("\n⚙️  Configuration:")
        print("  Edit .env.production for environment variables")
        print("  Edit nginx/nginx.conf for load balancing")
        print("  Edit docker-compose.production.yml for service scaling")

        print("\n🔒 Security Reminders:")
        print("  - Update default passwords in .env.production")
        print("  - Configure SSL certificates in nginx/ssl/")
        print("  - Restrict admin access in nginx configuration")
        print("  - Monitor logs for suspicious activity")
        print("  - Keep Docker images updated")


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy SolanaLM to production")
    parser.add_argument("--environment", default="production", choices=["development", "staging", "production"])
    parser.add_argument("--skip-build", action="store_true", help="Skip Docker image build")
    parser.add_argument("--config-only", action="store_true", help="Only generate configuration files")

    args = parser.parse_args()

    print("🚀 SolanaLM Production Deployment")
    print("=" * 40)

    deployment = SolanaLMDeployment(args.environment)

    # Check requirements
    if not deployment.check_requirements():
        print("❌ Requirements check failed")
        return 1

    # Generate configuration files
    deployment.create_production_docker_compose()
    deployment.create_nginx_config()
    deployment.create_env_template()
    deployment.create_init_db_script()

    if args.config_only:
        print("✅ Configuration files generated")
        return 0

    # Build and deploy
    if not args.skip_build:
        if not deployment.build_images():
            return 1

    if not deployment.deploy_services():
        return 1

    deployment.verify_deployment()
    deployment.show_deployment_info()

    print(f"\n🎯 Next Steps:")
    print("1. Update .env.production with your actual values")
    print("2. Configure SSL certificates for production")
    print("3. Set up monitoring and alerting")
    print("4. Configure backup procedures")
    print("5. Set up CI/CD pipelines")

    return 0


if __name__ == "__main__":
    exit(main())