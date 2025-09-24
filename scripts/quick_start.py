#!/usr/bin/env python3

"""
SolanaLM Quick Start Script

One-command setup to get SolanaLM network running locally for development and testing.
"""

import os
import sys
import subprocess
import time
import asyncio
import signal
from pathlib import Path
import json


class QuickStart:
    """Quick start manager for SolanaLM network"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.processes = []
        self.ports = {
            "gateway": 8001,
            "inference_node": 8100,
            "proxy_node": 8200,
            "redis": 6379,
            "postgres": 5432
        }

    def check_dependencies(self):
        """Check if required dependencies are available"""
        print("🔍 Checking dependencies...")

        # Check Python
        try:
            result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
            print(f"  ✅ Python: {result.stdout.strip()}")
        except Exception as e:
            print(f"  ❌ Python check failed: {e}")
            return False

        # Check poetry
        try:
            result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
            print(f"  ✅ Poetry: {result.stdout.strip()}")
        except FileNotFoundError:
            print("  ❌ Poetry not found. Install with: curl -sSL https://install.python-poetry.org | python3 -")
            return False

        # Check if in poetry environment or dependencies installed
        try:
            import aiohttp
            print("  ✅ Dependencies: Available")
        except ImportError:
            print("  ⚠️  Dependencies not found. Will install with poetry...")

        return True

    def install_dependencies(self):
        """Install project dependencies"""
        print("📦 Installing dependencies...")

        try:
            # Install with poetry
            result = subprocess.run(
                ["poetry", "install"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True
            )
            print("  ✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Dependency installation failed: {e.stderr}")
            return False

    def check_ports(self):
        """Check if required ports are available"""
        print("🔌 Checking port availability...")

        import socket

        for service, port in self.ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            if result == 0:
                print(f"  ⚠️  Port {port} ({service}) is already in use")
                if service in ["redis", "postgres"]:
                    print(f"     This is OK if {service} is already running")
                else:
                    print(f"     You may need to stop the service using port {port}")
            else:
                print(f"  ✅ Port {port} ({service}) is available")

    def create_env_file(self):
        """Create development environment file"""
        print("⚙️  Creating development environment...")

        env_content = """# SolanaLM Development Environment
SOLANALM_ENVIRONMENT=development
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com

# Gateway
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8001

# Logging
LOG_LEVEL=INFO

# Development settings
MIN_TRAINING_PARTICIPANTS=2
"""

        env_file = self.project_root / ".env"
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(env_content)
            print("  ✅ Created .env file")
        else:
            print("  ✅ .env file already exists")

    def start_gateway(self):
        """Start the SolanaLM gateway"""
        print("🚀 Starting SolanaLM Gateway...")

        try:
            # Start gateway with poetry
            process = subprocess.Popen(
                ["poetry", "run", "python", "scripts/run_gateway.py"],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes.append(("gateway", process))
            print(f"  ✅ Gateway started (PID: {process.pid})")

            # Wait a moment for startup
            time.sleep(3)

            # Check if it's still running
            if process.poll() is None:
                print("  ✅ Gateway is running")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"  ❌ Gateway failed to start:")
                print(f"     stdout: {stdout}")
                print(f"     stderr: {stderr}")
                return False

        except Exception as e:
            print(f"  ❌ Failed to start gateway: {e}")
            return False

    def start_inference_node(self):
        """Start a demo inference node"""
        print("🤖 Starting Demo Inference Node...")

        try:
            # Start inference node
            process = subprocess.Popen(
                [
                    "poetry", "run", "python", "scripts/run_node.py",
                    "--type", "inference",
                    "--node-id", "quickstart-inference-node",
                    "--wallet", "QuickStartInferenceWallet123",
                    "--port", "8100"
                ],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes.append(("inference_node", process))
            print(f"  ✅ Inference node started (PID: {process.pid})")

            # Wait for startup
            time.sleep(5)

            if process.poll() is None:
                print("  ✅ Inference node is running")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"  ❌ Inference node failed to start:")
                print(f"     stdout: {stdout}")
                print(f"     stderr: {stderr}")
                return False

        except Exception as e:
            print(f"  ❌ Failed to start inference node: {e}")
            return False

    def start_proxy_node(self):
        """Start a demo proxy node (if API keys available)"""
        print("🔗 Starting Demo Proxy Node...")

        # Check for API keys
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

        if not (has_openai or has_anthropic):
            print("  ⚠️  No API keys found (OPENAI_API_KEY, ANTHROPIC_API_KEY)")
            print("     Skipping proxy node - set API keys to test external API integration")
            return True

        try:
            process = subprocess.Popen(
                [
                    "poetry", "run", "python", "scripts/run_node.py",
                    "--type", "proxy",
                    "--node-id", "quickstart-proxy-node",
                    "--wallet", "QuickStartProxyWallet123",
                    "--port", "8200"
                ],
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.processes.append(("proxy_node", process))
            print(f"  ✅ Proxy node started (PID: {process.pid})")

            time.sleep(3)

            if process.poll() is None:
                print("  ✅ Proxy node is running")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"  ❌ Proxy node failed to start:")
                print(f"     stderr: {stderr}")
                return False

        except Exception as e:
            print(f"  ❌ Failed to start proxy node: {e}")
            return False

    async def test_network(self):
        """Test the running network"""
        print("🧪 Testing network functionality...")

        try:
            import aiohttp

            # Test gateway health
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8001/health", timeout=10) as response:
                    if response.status == 200:
                        print("  ✅ Gateway health check passed")
                    else:
                        print(f"  ❌ Gateway health check failed: {response.status}")
                        return False

                # Test model listing
                async with session.get("http://localhost:8001/v1/models", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('data', [])
                        print(f"  ✅ Found {len(models)} available models")
                    else:
                        print(f"  ❌ Model listing failed: {response.status}")
                        return False

                # Test simple inference
                test_request = {
                    "model": "test-model",
                    "messages": [{"role": "user", "content": "Say 'Hello from SolanaLM!'"}],
                    "max_tokens": 20
                }

                async with session.post(
                    "http://localhost:8001/v1/chat/completions",
                    json=test_request,
                    headers={"Authorization": "Bearer test-wallet-123"},
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data["choices"][0]["message"]["content"]
                        print(f"  ✅ Inference test passed: '{response_text[:50]}...'")
                        return True
                    else:
                        print(f"  ❌ Inference test failed: {response.status}")
                        error_text = await response.text()
                        print(f"     Error: {error_text}")
                        return False

        except Exception as e:
            print(f"  ❌ Network test failed: {e}")
            return False

    def show_network_info(self):
        """Show information about the running network"""
        print("\n" + "=" * 60)
        print("🎉 SolanaLM Network is Running!")
        print("=" * 60)

        print("\n🌐 Access Points:")
        print(f"  Gateway API:           http://localhost:{self.ports['gateway']}")
        print(f"  OpenAI Compatible API: http://localhost:{self.ports['gateway']}/v1")
        print(f"  Health Check:          http://localhost:{self.ports['gateway']}/health")
        print(f"  API Documentation:     http://localhost:{self.ports['gateway']}/docs")

        print("\n🤖 Running Nodes:")
        for name, process in self.processes:
            status = "✅ Running" if process.poll() is None else "❌ Stopped"
            print(f"  {name}: {status} (PID: {process.pid})")

        print("\n🧪 Test Commands:")
        print("  # Test with Python client")
        print("  poetry run python examples/basic_usage.py")
        print()
        print("  # Test OpenAI compatibility")
        print("  poetry run python examples/drop_in_replacement.py")
        print()
        print("  # Run comprehensive tests")
        print("  poetry run python scripts/test_deployment.py")

        print("\n📚 Example Usage:")
        print("""
  # Python SDK
  from client.python.solanalm_client import SolanaLMClient

  async with SolanaLMClient() as client:
      response = await client.inference(
          model="gpt-3.5-turbo",
          prompt="Hello, SolanaLM!",
          wallet_address="your-wallet"
      )
      print(response.response)

  # OpenAI Compatibility
  from client.python.openai_compat import openai

  openai.api_key = "your-wallet-address"
  openai.api_base = "http://localhost:8001/v1"

  response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[{"role": "user", "content": "Hello!"}]
  )
""")

        print("\n⚙️  Management:")
        print("  Stop network: Ctrl+C or python scripts/quick_start.py --stop")
        print("  View logs: Check terminal output")
        print("  Add nodes: python scripts/run_node.py --type <type>")

    def cleanup(self):
        """Clean up running processes"""
        print("\n🛑 Stopping SolanaLM network...")

        for name, process in self.processes:
            if process.poll() is None:
                print(f"  Stopping {name}...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    print(f"  ✅ {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"  ⚠️  Force killing {name}...")
                    process.kill()
                    process.wait()

        print("  ✅ All processes stopped")

    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n\n📡 Received signal {signum}")
        self.cleanup()
        sys.exit(0)

    async def start_network(self):
        """Start the complete network"""
        print("🚀 SolanaLM Quick Start")
        print("=" * 30)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Run all startup steps
        if not self.check_dependencies():
            return False

        if not self.install_dependencies():
            return False

        self.check_ports()
        self.create_env_file()

        # Start services
        if not self.start_gateway():
            return False

        if not self.start_inference_node():
            return False

        self.start_proxy_node()  # Optional

        # Test the network
        if await self.test_network():
            self.show_network_info()

            print("\n🎯 Network is ready! Press Ctrl+C to stop.")

            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)

                    # Check if any critical process died
                    critical_processes = ["gateway", "inference_node"]
                    for name, process in self.processes:
                        if name in critical_processes and process.poll() is not None:
                            print(f"\n❌ Critical process {name} stopped unexpectedly")
                            return False

            except KeyboardInterrupt:
                pass

        return True

    def stop_network(self):
        """Stop running network"""
        print("🛑 Stopping SolanaLM network...")

        # Find and kill processes by port
        import psutil

        for service, port in self.ports.items():
            if service in ["redis", "postgres"]:
                continue  # Don't kill system services

            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.info['connections']
                    if connections:
                        for conn in connections:
                            if conn.laddr.port == port:
                                print(f"  Stopping process on port {port} (PID: {proc.pid})")
                                proc.terminate()
                                proc.wait(timeout=5)
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass

        print("  ✅ Network stopped")


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="SolanaLM Quick Start")
    parser.add_argument("--stop", action="store_true", help="Stop running network")

    args = parser.parse_args()

    quick_start = QuickStart()

    if args.stop:
        quick_start.stop_network()
        return 0

    try:
        success = await quick_start.start_network()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Quick start failed: {e}")
        quick_start.cleanup()
        return 1
    finally:
        quick_start.cleanup()


if __name__ == "__main__":
    try:
        exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n⏹️  Quick start interrupted by user")
        exit(130)