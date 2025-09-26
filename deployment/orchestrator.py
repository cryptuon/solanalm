"""
Comprehensive Deployment and Orchestration System
Docker, Kubernetes, monitoring, and production deployment tools
"""

import yaml
import json
import subprocess
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import tempfile
import shutil

logger = logging.getLogger(__name__)


class DeploymentTarget(str, Enum):
    LOCAL = "local"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    GCP = "gcp"


class ServiceType(str, Enum):
    GATEWAY = "gateway"
    INFERENCE_NODE = "inference-node"
    TRAINING_NODE = "training-node"
    PROXY_NODE = "proxy-node"
    DATABASE = "database"
    REDIS = "redis"
    MONITORING = "monitoring"


@dataclass
class ServiceConfig:
    name: str
    type: ServiceType
    image: str
    port: int
    replicas: int = 1
    resources: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[Dict[str, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class DeploymentOrchestrator:
    """Orchestrates SolanaLM deployment across different platforms"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.deployment_dir = self.project_root / "deployment"
        self.deployment_dir.mkdir(exist_ok=True)

        # Service configurations
        self.services = self._define_services()

    def _define_services(self) -> Dict[str, ServiceConfig]:
        """Define all SolanaLM services"""
        return {
            "gateway": ServiceConfig(
                name="solanalm-gateway",
                type=ServiceType.GATEWAY,
                image="solanalm:gateway",
                port=8001,
                replicas=2,
                resources={"memory": "512Mi", "cpu": "500m"},
                environment={
                    "ENVIRONMENT": "production",
                    "DATABASE_URL": "postgresql://solanalm:solanalm@postgres:5432/solanalm",
                    "REDIS_URL": "redis://redis:6379/0"
                },
                dependencies=["database", "redis"]
            ),
            "inference-node": ServiceConfig(
                name="solanalm-inference",
                type=ServiceType.INFERENCE_NODE,
                image="solanalm:inference",
                port=8100,
                replicas=3,
                resources={"memory": "2Gi", "cpu": "1000m", "nvidia.com/gpu": "1"},
                environment={
                    "NODE_TYPE": "inference",
                    "GATEWAY_URL": "http://gateway:8001"
                }
            ),
            "training-node": ServiceConfig(
                name="solanalm-training",
                type=ServiceType.TRAINING_NODE,
                image="solanalm:training",
                port=8200,
                replicas=2,
                resources={"memory": "4Gi", "cpu": "2000m", "nvidia.com/gpu": "1"},
                environment={
                    "NODE_TYPE": "training",
                    "GATEWAY_URL": "http://gateway:8001"
                }
            ),
            "proxy-node": ServiceConfig(
                name="solanalm-proxy",
                type=ServiceType.PROXY_NODE,
                image="solanalm:proxy",
                port=8300,
                replicas=1,
                environment={
                    "NODE_TYPE": "proxy",
                    "GATEWAY_URL": "http://gateway:8001"
                }
            ),
            "database": ServiceConfig(
                name="postgres",
                type=ServiceType.DATABASE,
                image="postgres:15",
                port=5432,
                replicas=1,
                resources={"memory": "1Gi", "cpu": "500m"},
                environment={
                    "POSTGRES_DB": "solanalm",
                    "POSTGRES_USER": "solanalm",
                    "POSTGRES_PASSWORD": "solanalm"
                },
                volumes=[{"name": "postgres-data", "mountPath": "/var/lib/postgresql/data"}]
            ),
            "redis": ServiceConfig(
                name="redis",
                type=ServiceType.REDIS,
                image="redis:7-alpine",
                port=6379,
                replicas=1,
                resources={"memory": "512Mi", "cpu": "250m"},
                volumes=[{"name": "redis-data", "mountPath": "/data"}]
            ),
            "monitoring": ServiceConfig(
                name="prometheus",
                type=ServiceType.MONITORING,
                image="prom/prometheus:latest",
                port=9090,
                replicas=1,
                resources={"memory": "1Gi", "cpu": "500m"},
                volumes=[{"name": "prometheus-config", "mountPath": "/etc/prometheus"}]
            )
        }

    def generate_dockerfiles(self):
        """Generate Dockerfiles for all services"""
        dockerfiles = {
            "gateway": self._generate_gateway_dockerfile(),
            "inference": self._generate_inference_dockerfile(),
            "training": self._generate_training_dockerfile(),
            "proxy": self._generate_proxy_dockerfile()
        }

        for service, dockerfile_content in dockerfiles.items():
            dockerfile_path = self.deployment_dir / f"Dockerfile.{service}"
            dockerfile_path.write_text(dockerfile_content)
            logger.info(f"Generated Dockerfile for {service}")

    def _generate_gateway_dockerfile(self) -> str:
        return """
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \\
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 solanalm
USER solanalm

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8001/health || exit 1

# Start gateway
CMD ["python", "-m", "uvicorn", "core.gateway.server:app", "--host", "0.0.0.0", "--port", "8001"]
"""

    def _generate_inference_dockerfile(self) -> str:
        return """
FROM nvidia/cuda:11.8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    python3.12 \\
    python3-pip \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \\
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 solanalm
USER solanalm

# Expose port
EXPOSE 8100

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \\
    CMD curl -f http://localhost:8100/health || exit 1

# Start inference node
CMD ["python", "scripts/run_enhanced_node.py", "--backend", "transformers", "--node-id", "$NODE_ID", "--wallet", "$WALLET_ADDRESS"]
"""

    def _generate_training_dockerfile(self) -> str:
        return """
FROM nvidia/cuda:11.8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    python3.12 \\
    python3-pip \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \\
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 solanalm
USER solanalm

# Expose port
EXPOSE 8200

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \\
    CMD curl -f http://localhost:8200/health || exit 1

# Start training node
CMD ["python", "scripts/run_node.py", "--type", "training", "--node-id", "$NODE_ID", "--wallet", "$WALLET_ADDRESS"]
"""

    def _generate_proxy_dockerfile(self) -> str:
        return """
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \\
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 solanalm
USER solanalm

# Expose port
EXPOSE 8300

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8300/health || exit 1

# Start proxy node
CMD ["python", "scripts/run_enhanced_node.py", "--backend", "$PROXY_BACKEND", "--node-id", "$NODE_ID", "--wallet", "$WALLET_ADDRESS"]
"""

    def generate_docker_compose(self) -> str:
        """Generate Docker Compose configuration"""
        compose_config = {
            "version": "3.8",
            "services": {},
            "volumes": {},
            "networks": {
                "solanalm-network": {
                    "driver": "bridge"
                }
            }
        }

        # Add volumes
        compose_config["volumes"] = {
            "postgres-data": {},
            "redis-data": {},
            "prometheus-data": {},
            "model-cache": {}
        }

        # Add services
        for service_name, service in self.services.items():
            service_config = {
                "image": service.image,
                "container_name": f"solanalm-{service_name}",
                "ports": [f"{service.port}:{service.port}"],
                "environment": service.environment,
                "networks": ["solanalm-network"],
                "restart": "unless-stopped"
            }

            # Add volumes
            if service.volumes:
                service_config["volumes"] = [
                    f"{vol['name']}:{vol['mountPath']}" for vol in service.volumes
                ]

            # Add dependencies
            if service.dependencies:
                service_config["depends_on"] = service.dependencies

            # Add resource limits for non-database services
            if service.type not in [ServiceType.DATABASE, ServiceType.REDIS]:
                service_config["deploy"] = {
                    "resources": {
                        "limits": {
                            "memory": service.resources.get("memory", "1Gi"),
                            "cpus": service.resources.get("cpu", "500m").rstrip("m")
                        }
                    }
                }

            compose_config["services"][service_name] = service_config

        compose_path = self.deployment_dir / "docker-compose.yml"
        compose_path.write_text(yaml.dump(compose_config, default_flow_style=False))
        logger.info("Generated Docker Compose configuration")

        return str(compose_path)

    def generate_kubernetes_manifests(self):
        """Generate Kubernetes manifests"""
        k8s_dir = self.deployment_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)

        # Generate namespace
        namespace = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": "solanalm"}
        }
        (k8s_dir / "namespace.yaml").write_text(yaml.dump(namespace))

        # Generate ConfigMap
        configmap = self._generate_configmap()
        (k8s_dir / "configmap.yaml").write_text(yaml.dump(configmap))

        # Generate services
        for service_name, service in self.services.items():
            if service.type not in [ServiceType.DATABASE, ServiceType.REDIS]:
                # Deployment
                deployment = self._generate_k8s_deployment(service)
                (k8s_dir / f"{service_name}-deployment.yaml").write_text(yaml.dump(deployment))

                # Service
                k8s_service = self._generate_k8s_service(service)
                (k8s_dir / f"{service_name}-service.yaml").write_text(yaml.dump(k8s_service))

        # Generate StatefulSets for databases
        postgres_statefulset = self._generate_postgres_statefulset()
        (k8s_dir / "postgres-statefulset.yaml").write_text(yaml.dump(postgres_statefulset))

        redis_statefulset = self._generate_redis_statefulset()
        (k8s_dir / "redis-statefulset.yaml").write_text(yaml.dump(redis_statefulset))

        # Generate Ingress
        ingress = self._generate_ingress()
        (k8s_dir / "ingress.yaml").write_text(yaml.dump(ingress))

        logger.info("Generated Kubernetes manifests")

    def _generate_configmap(self) -> Dict[str, Any]:
        """Generate Kubernetes ConfigMap"""
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "solanalm-config",
                "namespace": "solanalm"
            },
            "data": {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql://solanalm:solanalm@postgres:5432/solanalm",
                "REDIS_URL": "redis://redis:6379/0",
                "GATEWAY_URL": "http://gateway:8001"
            }
        }

    def _generate_k8s_deployment(self, service: ServiceConfig) -> Dict[str, Any]:
        """Generate Kubernetes Deployment"""
        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": service.name,
                "namespace": "solanalm",
                "labels": {"app": service.name}
            },
            "spec": {
                "replicas": service.replicas,
                "selector": {"matchLabels": {"app": service.name}},
                "template": {
                    "metadata": {"labels": {"app": service.name}},
                    "spec": {
                        "containers": [{
                            "name": service.name,
                            "image": service.image,
                            "ports": [{"containerPort": service.port}],
                            "env": [
                                {"name": k, "value": v} for k, v in service.environment.items()
                            ],
                            "resources": {
                                "limits": {
                                    "memory": service.resources.get("memory", "1Gi"),
                                    "cpu": service.resources.get("cpu", "500m")
                                },
                                "requests": {
                                    "memory": service.resources.get("memory", "512Mi"),
                                    "cpu": service.resources.get("cpu", "250m")
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/health", "port": service.port},
                                "initialDelaySeconds": 60,
                                "periodSeconds": 30
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/health", "port": service.port},
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            }
                        }]
                    }
                }
            }
        }

    def _generate_k8s_service(self, service: ServiceConfig) -> Dict[str, Any]:
        """Generate Kubernetes Service"""
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service.name,
                "namespace": "solanalm"
            },
            "spec": {
                "selector": {"app": service.name},
                "ports": [{
                    "port": service.port,
                    "targetPort": service.port
                }],
                "type": "ClusterIP" if service.type != ServiceType.GATEWAY else "LoadBalancer"
            }
        }

    def _generate_postgres_statefulset(self) -> Dict[str, Any]:
        """Generate PostgreSQL StatefulSet"""
        return {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {
                "name": "postgres",
                "namespace": "solanalm"
            },
            "spec": {
                "serviceName": "postgres",
                "replicas": 1,
                "selector": {"matchLabels": {"app": "postgres"}},
                "template": {
                    "metadata": {"labels": {"app": "postgres"}},
                    "spec": {
                        "containers": [{
                            "name": "postgres",
                            "image": "postgres:15",
                            "ports": [{"containerPort": 5432}],
                            "env": [
                                {"name": "POSTGRES_DB", "value": "solanalm"},
                                {"name": "POSTGRES_USER", "value": "solanalm"},
                                {"name": "POSTGRES_PASSWORD", "value": "solanalm"}
                            ],
                            "volumeMounts": [{
                                "name": "postgres-storage",
                                "mountPath": "/var/lib/postgresql/data"
                            }]
                        }]
                    }
                },
                "volumeClaimTemplates": [{
                    "metadata": {"name": "postgres-storage"},
                    "spec": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {"requests": {"storage": "10Gi"}}
                    }
                }]
            }
        }

    def _generate_redis_statefulset(self) -> Dict[str, Any]:
        """Generate Redis StatefulSet"""
        return {
            "apiVersion": "apps/v1",
            "kind": "StatefulSet",
            "metadata": {
                "name": "redis",
                "namespace": "solanalm"
            },
            "spec": {
                "serviceName": "redis",
                "replicas": 1,
                "selector": {"matchLabels": {"app": "redis"}},
                "template": {
                    "metadata": {"labels": {"app": "redis"}},
                    "spec": {
                        "containers": [{
                            "name": "redis",
                            "image": "redis:7-alpine",
                            "ports": [{"containerPort": 6379}],
                            "volumeMounts": [{
                                "name": "redis-storage",
                                "mountPath": "/data"
                            }]
                        }]
                    }
                },
                "volumeClaimTemplates": [{
                    "metadata": {"name": "redis-storage"},
                    "spec": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {"requests": {"storage": "5Gi"}}
                    }
                }]
            }
        }

    def _generate_ingress(self) -> Dict[str, Any]:
        """Generate Ingress for external access"""
        return {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "solanalm-ingress",
                "namespace": "solanalm",
                "annotations": {
                    "nginx.ingress.kubernetes.io/rewrite-target": "/",
                    "cert-manager.io/cluster-issuer": "letsencrypt-prod"
                }
            },
            "spec": {
                "tls": [{
                    "hosts": ["api.solanalm.com"],
                    "secretName": "solanalm-tls"
                }],
                "rules": [{
                    "host": "api.solanalm.com",
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": "solanalm-gateway",
                                    "port": {"number": 8001}
                                }
                            }
                        }]
                    }
                }]
            }
        }

    def build_images(self):
        """Build Docker images for all services"""
        self.generate_dockerfiles()

        for service in ["gateway", "inference", "training", "proxy"]:
            dockerfile_path = self.deployment_dir / f"Dockerfile.{service}"
            image_name = f"solanalm:{service}"

            logger.info(f"Building image: {image_name}")

            result = subprocess.run([
                "docker", "build",
                "-f", str(dockerfile_path),
                "-t", image_name,
                str(self.project_root)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Successfully built {image_name}")
            else:
                logger.error(f"Failed to build {image_name}: {result.stderr}")
                raise RuntimeError(f"Docker build failed for {service}")

    async def deploy_local(self):
        """Deploy locally using Docker Compose"""
        logger.info("Starting local deployment")

        compose_file = self.generate_docker_compose()

        # Build images first
        self.build_images()

        # Start services
        result = subprocess.run([
            "docker-compose", "-f", compose_file, "up", "-d"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Local deployment successful")
            return True
        else:
            logger.error(f"Local deployment failed: {result.stderr}")
            return False

    async def deploy_kubernetes(self, kubeconfig: Optional[str] = None):
        """Deploy to Kubernetes cluster"""
        logger.info("Starting Kubernetes deployment")

        self.generate_kubernetes_manifests()
        k8s_dir = self.deployment_dir / "k8s"

        # Apply manifests
        kubectl_cmd = ["kubectl"]
        if kubeconfig:
            kubectl_cmd.extend(["--kubeconfig", kubeconfig])

        for manifest_file in k8s_dir.glob("*.yaml"):
            result = subprocess.run(
                kubectl_cmd + ["apply", "-f", str(manifest_file)],
                capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info(f"Applied {manifest_file.name}")
            else:
                logger.error(f"Failed to apply {manifest_file.name}: {result.stderr}")
                return False

        logger.info("Kubernetes deployment successful")
        return True

    def generate_monitoring_config(self):
        """Generate monitoring configuration"""
        monitoring_dir = self.deployment_dir / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)

        # Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "solanalm-gateway",
                    "static_configs": [{"targets": ["gateway:9090"]}]
                },
                {
                    "job_name": "solanalm-nodes",
                    "static_configs": [
                        {"targets": ["inference-node:9090"]},
                        {"targets": ["training-node:9090"]},
                        {"targets": ["proxy-node:9090"]}
                    ]
                }
            ]
        }

        (monitoring_dir / "prometheus.yml").write_text(yaml.dump(prometheus_config))

        # Grafana dashboard
        dashboard_config = self._generate_grafana_dashboard()
        (monitoring_dir / "dashboard.json").write_text(json.dumps(dashboard_config, indent=2))

        logger.info("Generated monitoring configuration")

    def _generate_grafana_dashboard(self) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration"""
        return {
            "dashboard": {
                "title": "SolanaLM Network Dashboard",
                "panels": [
                    {
                        "title": "Total Requests",
                        "type": "graph",
                        "targets": [{"expr": "rate(solanalm_total_requests[5m])"}]
                    },
                    {
                        "title": "Active Nodes",
                        "type": "singlestat",
                        "targets": [{"expr": "solanalm_active_nodes"}]
                    },
                    {
                        "title": "Success Rate",
                        "type": "singlestat",
                        "targets": [{"expr": "solanalm_success_rate"}]
                    }
                ]
            }
        }

    def health_check(self, target: DeploymentTarget) -> Dict[str, bool]:
        """Check health of deployed services"""
        results = {}

        if target == DeploymentTarget.LOCAL:
            # Check local Docker containers
            for service_name in self.services.keys():
                result = subprocess.run([
                    "docker", "ps", "--filter", f"name=solanalm-{service_name}",
                    "--format", "table {{.Names}}\t{{.Status}}"
                ], capture_output=True, text=True)

                results[service_name] = "Up" in result.stdout

        elif target == DeploymentTarget.KUBERNETES:
            # Check Kubernetes pods
            result = subprocess.run([
                "kubectl", "get", "pods", "-n", "solanalm", "-o", "json"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                pods = json.loads(result.stdout)
                for pod in pods["items"]:
                    pod_name = pod["metadata"]["name"]
                    status = pod["status"]["phase"]
                    results[pod_name] = status == "Running"

        return results


# Command-line interface
async def main():
    """Main deployment CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="SolanaLM Deployment Orchestrator")
    parser.add_argument("action", choices=["build", "deploy", "health", "generate"])
    parser.add_argument("--target", choices=["local", "kubernetes"], default="local")
    parser.add_argument("--kubeconfig", help="Kubernetes config file")

    args = parser.parse_args()

    orchestrator = DeploymentOrchestrator(".")

    if args.action == "generate":
        orchestrator.generate_dockerfiles()
        orchestrator.generate_docker_compose()
        orchestrator.generate_kubernetes_manifests()
        orchestrator.generate_monitoring_config()
        print("Generated all deployment configurations")

    elif args.action == "build":
        orchestrator.build_images()
        print("Built all Docker images")

    elif args.action == "deploy":
        if args.target == "local":
            success = await orchestrator.deploy_local()
        elif args.target == "kubernetes":
            success = await orchestrator.deploy_kubernetes(args.kubeconfig)

        if success:
            print(f"Deployment to {args.target} successful")
        else:
            print(f"Deployment to {args.target} failed")

    elif args.action == "health":
        target = DeploymentTarget.LOCAL if args.target == "local" else DeploymentTarget.KUBERNETES
        health_status = orchestrator.health_check(target)

        print(f"Health check for {args.target}:")
        for service, healthy in health_status.items():
            status = "✅" if healthy else "❌"
            print(f"  {status} {service}")


if __name__ == "__main__":
    asyncio.run(main())