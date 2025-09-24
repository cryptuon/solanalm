#!/usr/bin/env python3
"""
SolanaLM Deployment Script

Automated deployment of SolanaLM components:
- Gateway server with privacy features
- Inference nodes with onion routing
- Training nodes with federated learning
- Monitoring and health checks
"""

import asyncio
import argparse
import logging
import os
import sys
import subprocess
import time
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class SolanaLMDeployment:
    """Handles deployment of SolanaLM network components"""

    def __init__(self, config_file: str = "config/deployment.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
        self.processes = []
        self.deploy_id = f"deploy-{int(time.time())}"

    def load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return default configuration
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default deployment configuration"""
        return {
            "network": {
                "name": "solanalm-local",
                "solana_network": "devnet",
                "gateway_port": 8001
            },
            "gateway": {
                "host": "0.0.0.0",
                "port": 8001,
                "workers": 1,
                "privacy_enabled": True,
                "monitoring_enabled": True
            },
            "nodes": {
                "inference": {
                    "count": 3,
                    "base_port": 8100,
                    "privacy_enabled": True,
                    "models": ["gpt-3.5-turbo", "gpt-4"]
                },
                "training": {
                    "count": 2,
                    "base_port": 8200,
                    "gpu_enabled": False,
                    "models": ["gpt-2", "llama-7b"]
                }
            },
            "monitoring": {
                "enabled": True,
                "port": 8300,
                "metrics_interval": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/deployment.log"
            }
        }

    async def deploy_full_network(self):
        """Deploy complete SolanaLM network"""
        print(f"🚀 Deploying SolanaLM Network - {self.deploy_id}")
        print("=" * 60)

        try:
            # Setup logging and directories
            await self.setup_deployment_environment()

            # Deploy core components
            await self.deploy_gateway()
            await self.deploy_inference_nodes()
            await self.deploy_training_nodes()

            # Setup monitoring
            if self.config["monitoring"]["enabled"]:
                await self.deploy_monitoring()

            # Health checks
            await self.run_health_checks()

            print("\n✅ SolanaLM Network Deployed Successfully!")
            print(f"🌐 Gateway: http://localhost:{self.config['gateway']['port']}")
            print(f"📊 Monitoring: http://localhost:{self.config['monitoring']['port']}")
            print(f"📋 Deployment ID: {self.deploy_id}")

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            await self.cleanup_deployment()
            raise

    async def setup_deployment_environment(self):
        """Setup deployment directories and logging"""
        print("🔧 Setting up deployment environment...")

        # Create directories
        directories = ["logs", "data", "config", "tmp"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

        # Setup logging
        log_level = getattr(logging, self.config["logging"]["level"].upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config["logging"]["file"]),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Save deployment config
        with open(f"tmp/deployment-{self.deploy_id}.yaml", 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

        print("✅ Environment setup complete")

    async def deploy_gateway(self):
        """Deploy the main gateway server"""
        print("\n🌐 Deploying Gateway Server...")

        gateway_config = self.config["gateway"]
        cmd = [
            sys.executable, "core/gateway/server.py",
            "--host", gateway_config["host"],
            "--port", str(gateway_config["port"])
        ]

        if gateway_config.get("privacy_enabled", True):
            cmd.append("--enable-privacy")

        if gateway_config.get("monitoring_enabled", True):
            cmd.append("--enable-monitoring")

        # Set environment variables
        env = os.environ.copy()
        env.update({
            "SOLANALM_NETWORK": self.config["network"]["solana_network"],
            "SOLANALM_DEPLOY_ID": self.deploy_id,
            "PYTHONPATH": str(Path(__file__).parent.parent)
        })

        # Start gateway process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self.processes.append(("gateway", process))

        # Wait for gateway to start
        await asyncio.sleep(3)

        # Verify gateway is running
        if process.returncode is None:
            print(f"✅ Gateway deployed on port {gateway_config['port']}")
        else:
            stdout, stderr = await process.communicate()
            raise Exception(f"Gateway failed to start: {stderr.decode()}")

    async def deploy_inference_nodes(self):
        """Deploy inference nodes"""
        print("\n🧠 Deploying Inference Nodes...")

        node_config = self.config["nodes"]["inference"]
        base_port = node_config["base_port"]

        for i in range(node_config["count"]):
            node_id = f"inference-node-{i+1}"
            port = base_port + i

            print(f"   Deploying {node_id} on port {port}...")

            cmd = [
                sys.executable, "scripts/run_node.py",
                "--type", "inference",
                "--node-id", node_id,
                "--port", str(port),
                "--gateway-url", f"http://localhost:{self.config['gateway']['port']}"
            ]

            if node_config.get("privacy_enabled", True):
                cmd.append("--privacy-enabled")

            # Add supported models
            for model in node_config.get("models", []):
                cmd.extend(["--model", model])

            # Set environment variables
            env = os.environ.copy()
            env.update({
                "SOLANALM_NODE_ID": node_id,
                "SOLANALM_DEPLOY_ID": self.deploy_id,
                "PYTHONPATH": str(Path(__file__).parent.parent)
            })

            # Start node process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.processes.append((node_id, process))

            # Brief delay between node deployments
            await asyncio.sleep(1)

        print(f"✅ Deployed {node_config['count']} inference nodes")

    async def deploy_training_nodes(self):
        """Deploy training nodes for federated learning"""
        print("\n🎓 Deploying Training Nodes...")

        node_config = self.config["nodes"]["training"]
        base_port = node_config["base_port"]

        for i in range(node_config["count"]):
            node_id = f"training-node-{i+1}"
            port = base_port + i

            print(f"   Deploying {node_id} on port {port}...")

            cmd = [
                sys.executable, "scripts/run_node.py",
                "--type", "training",
                "--node-id", node_id,
                "--port", str(port),
                "--gateway-url", f"http://localhost:{self.config['gateway']['port']}"
            ]

            if node_config.get("gpu_enabled", False):
                cmd.append("--gpu-enabled")

            # Add supported models
            for model in node_config.get("models", []):
                cmd.extend(["--model", model])

            # Set environment variables
            env = os.environ.copy()
            env.update({
                "SOLANALM_NODE_ID": node_id,
                "SOLANALM_DEPLOY_ID": self.deploy_id,
                "PYTHONPATH": str(Path(__file__).parent.parent)
            })

            # Start node process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self.processes.append((node_id, process))

            # Brief delay between node deployments
            await asyncio.sleep(1)

        print(f"✅ Deployed {node_config['count']} training nodes")

    async def deploy_monitoring(self):
        """Deploy monitoring and metrics collection"""
        print("\n📊 Deploying Monitoring System...")

        monitoring_config = self.config["monitoring"]

        cmd = [
            sys.executable, "scripts/run_monitoring.py",
            "--port", str(monitoring_config["port"]),
            "--gateway-url", f"http://localhost:{self.config['gateway']['port']}",
            "--metrics-interval", str(monitoring_config["metrics_interval"])
        ]

        # Set environment variables
        env = os.environ.copy()
        env.update({
            "SOLANALM_DEPLOY_ID": self.deploy_id,
            "PYTHONPATH": str(Path(__file__).parent.parent)
        })

        # Start monitoring process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self.processes.append(("monitoring", process))

        # Wait for monitoring to start
        await asyncio.sleep(2)

        print(f"✅ Monitoring deployed on port {monitoring_config['port']}")

    async def run_health_checks(self):
        """Run comprehensive health checks"""
        print("\n🏥 Running Health Checks...")

        checks = [
            self.check_gateway_health,
            self.check_node_connectivity,
            self.check_privacy_network,
            self.check_training_capability
        ]

        for check in checks:
            try:
                await check()
            except Exception as e:
                logger.warning(f"Health check failed: {e}")

        print("✅ Health checks completed")

    async def check_gateway_health(self):
        """Check gateway health and endpoints"""
        import aiohttp

        gateway_url = f"http://localhost:{self.config['gateway']['port']}"

        async with aiohttp.ClientSession() as session:
            # Check root endpoint
            async with session.get(f"{gateway_url}/") as response:
                if response.status == 200:
                    print("   ✅ Gateway root endpoint responding")
                else:
                    raise Exception(f"Gateway health check failed: {response.status}")

            # Check privacy status
            async with session.get(f"{gateway_url}/privacy_status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Privacy network: {data['privacy_capable_nodes']} nodes")
                else:
                    print("   ⚠️ Privacy network not fully ready")

    async def check_node_connectivity(self):
        """Check that nodes are registered and responding"""
        import aiohttp

        gateway_url = f"http://localhost:{self.config['gateway']['port']}"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{gateway_url}/nodes") as response:
                if response.status == 200:
                    nodes = await response.json()
                    inference_nodes = [n for n in nodes if n["node_type"] == "inference"]
                    training_nodes = [n for n in nodes if n["node_type"] == "training"]

                    print(f"   ✅ {len(inference_nodes)} inference nodes registered")
                    print(f"   ✅ {len(training_nodes)} training nodes registered")
                else:
                    raise Exception("Failed to fetch node list")

    async def check_privacy_network(self):
        """Check privacy network capability"""
        import aiohttp

        gateway_url = f"http://localhost:{self.config['gateway']['port']}"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{gateway_url}/privacy_status") as response:
                if response.status == 200:
                    data = await response.json()
                    if data["privacy_capable_nodes"] >= 3:
                        print(f"   ✅ Privacy network ready: {data['privacy_capable_nodes']} nodes")
                    else:
                        print(f"   ⚠️ Privacy network limited: {data['privacy_capable_nodes']} nodes (need 3+)")
                else:
                    print("   ⚠️ Privacy status check failed")

    async def check_training_capability(self):
        """Check federated learning readiness"""
        import aiohttp

        gateway_url = f"http://localhost:{self.config['gateway']['port']}"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{gateway_url}/training/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Training capability: {data['participating_nodes']} nodes available")
                else:
                    print("   ⚠️ Training status check failed")

    async def cleanup_deployment(self):
        """Clean up deployment processes"""
        print("\n🧹 Cleaning up deployment...")

        for name, process in self.processes:
            if process.returncode is None:
                print(f"   Terminating {name}...")
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    print(f"   Force killing {name}...")
                    process.kill()

        self.processes.clear()
        print("✅ Cleanup completed")

    async def scale_deployment(self, component: str, count: int):
        """Scale deployment components"""
        print(f"⚡ Scaling {component} to {count} instances...")

        if component == "inference":
            # Stop existing inference nodes
            inference_processes = [(n, p) for n, p in self.processes if "inference" in n]
            for name, process in inference_processes:
                process.terminate()
                await process.wait()
                self.processes.remove((name, process))

            # Update config and redeploy
            self.config["nodes"]["inference"]["count"] = count
            await self.deploy_inference_nodes()

        elif component == "training":
            # Similar scaling for training nodes
            training_processes = [(n, p) for n, p in self.processes if "training" in n]
            for name, process in training_processes:
                process.terminate()
                await process.wait()
                self.processes.remove((name, process))

            self.config["nodes"]["training"]["count"] = count
            await self.deploy_training_nodes()

        print(f"✅ Scaled {component} to {count} instances")

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        status = {
            "deploy_id": self.deploy_id,
            "total_processes": len(self.processes),
            "running_processes": sum(1 for _, p in self.processes if p.returncode is None),
            "components": {}
        }

        for name, process in self.processes:
            component_type = name.split("-")[0] if "-" in name else name
            if component_type not in status["components"]:
                status["components"][component_type] = {"count": 0, "running": 0}

            status["components"][component_type]["count"] += 1
            if process.returncode is None:
                status["components"][component_type]["running"] += 1

        return status

    async def monitor_deployment(self, duration: int = 300):
        """Monitor deployment for specified duration"""
        print(f"\n👀 Monitoring deployment for {duration} seconds...")

        start_time = time.time()
        while time.time() - start_time < duration:
            status = self.get_deployment_status()
            print(f"\r   Running: {status['running_processes']}/{status['total_processes']} processes", end="")

            # Check for failed processes
            failed_processes = [(n, p) for n, p in self.processes if p.returncode is not None]
            if failed_processes:
                print(f"\n   ⚠️ {len(failed_processes)} processes failed")
                for name, process in failed_processes:
                    print(f"     {name}: exit code {process.returncode}")

            await asyncio.sleep(5)

        print(f"\n✅ Monitoring completed")


async def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy SolanaLM Network")
    parser.add_argument("command", choices=["deploy", "cleanup", "scale", "status", "monitor"],
                       help="Deployment command")
    parser.add_argument("--config", default="config/deployment.yaml",
                       help="Deployment configuration file")
    parser.add_argument("--component", choices=["inference", "training"],
                       help="Component to scale (for scale command)")
    parser.add_argument("--count", type=int, default=1,
                       help="Number of instances (for scale command)")
    parser.add_argument("--duration", type=int, default=300,
                       help="Monitoring duration in seconds")

    args = parser.parse_args()

    deployment = SolanaLMDeployment(args.config)

    try:
        if args.command == "deploy":
            await deployment.deploy_full_network()

        elif args.command == "cleanup":
            await deployment.cleanup_deployment()

        elif args.command == "scale":
            if not args.component:
                print("❌ --component required for scale command")
                return
            await deployment.scale_deployment(args.component, args.count)

        elif args.command == "status":
            status = deployment.get_deployment_status()
            print(f"📊 Deployment Status:")
            print(f"   Deploy ID: {status['deploy_id']}")
            print(f"   Total processes: {status['total_processes']}")
            print(f"   Running processes: {status['running_processes']}")
            for component, info in status["components"].items():
                print(f"   {component}: {info['running']}/{info['count']}")

        elif args.command == "monitor":
            await deployment.monitor_deployment(args.duration)

    except KeyboardInterrupt:
        print("\n🛑 Deployment interrupted")
        await deployment.cleanup_deployment()
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        await deployment.cleanup_deployment()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())