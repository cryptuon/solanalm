#!/usr/bin/env python3

"""
Basic usage example for SolanaLM hybrid network

Demonstrates:
1. Starting a local inference node
2. Connecting to the gateway
3. Submitting inference requests
4. Viewing network statistics
"""

import asyncio
import logging
import sys
import os
import time

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from client.python.solanalm_client import SolanaLMClient
from core.nodes.inference.node import InferenceNode
from core.nodes.proxy.node import ProxyNode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_network_usage():
    """Demonstrate basic network usage"""

    print("🚀 SolanaLM Hybrid Network Demo")
    print("=" * 50)

    # Connect to gateway
    gateway_url = "http://localhost:8001"
    async with SolanaLMClient(gateway_url) as client:

        # 1. Check network status
        print("\n📊 Network Status:")
        try:
            status = await client.get_network_status()
            print(f"Service: {status.get('service', 'Unknown')}")
            print(f"Version: {status.get('version', 'Unknown')}")

            network_stats = status.get('network_stats', {})
            print(f"Total nodes: {network_stats.get('total_nodes', 0)}")
            print(f"Active nodes: {network_stats.get('active_nodes', 0)}")
            print(f"Inference nodes: {network_stats.get('inference_nodes', 0)}")
            print(f"Proxy nodes: {network_stats.get('proxy_nodes', 0)}")

        except Exception as e:
            print(f"❌ Could not connect to gateway: {e}")
            print("Make sure the gateway is running with: python scripts/run_gateway.py")
            return

        # 2. List available models
        print("\n🤖 Available Models:")
        try:
            models = await client.list_available_models()
            if models:
                for i, model in enumerate(models, 1):
                    print(f"{i}. {model}")
            else:
                print("No models available. Start some nodes first!")
                print("Example: python scripts/run_node.py --type inference --node-id test-node-1 --wallet FakeWallet123")
                return
        except Exception as e:
            print(f"❌ Could not list models: {e}")
            return

        # 3. Test inference requests
        print("\n💭 Testing Inference:")

        test_prompts = [
            "Hello, how are you today?",
            "What is the capital of France?",
            "Explain quantum computing in simple terms."
        ]

        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n{i}. Prompt: {prompt}")

            try:
                start_time = time.time()
                response = await client.inference(
                    model=models[0],  # Use first available model
                    prompt=prompt,
                    wallet_address="DemoWallet123456789",
                    max_tokens=100
                )
                end_time = time.time()

                print(f"   Response: {response.response[:100]}{'...' if len(response.response) > 100 else ''}")
                print(f"   Tokens: {response.tokens_generated}")
                print(f"   Cost: {response.cost_sol:.6f} SOL")
                print(f"   Node: {response.node_id}")
                print(f"   Latency: {end_time - start_time:.2f}s")

            except Exception as e:
                print(f"   ❌ Request failed: {e}")

        # 4. Training status
        print("\n🎓 Training Status:")
        try:
            training_status = await client.get_training_status()
            print(f"Active training rounds: {training_status.get('active_rounds', 0)}")
            print(f"Participating nodes: {training_status.get('participating_nodes', 0)}")

            next_round = training_status.get('next_round_start')
            if next_round:
                print(f"Next round starts: {next_round}")
            else:
                print("No training rounds scheduled")

        except Exception as e:
            print(f"❌ Could not get training status: {e}")


async def run_demo_inference_node():
    """Run a demo inference node for testing"""
    print("\n🔧 Starting demo inference node...")

    node = InferenceNode(
        node_id="demo-inference-node",
        wallet_address="DemoInferenceWallet123",
        gateway_url="http://localhost:8001",
        model_name="microsoft/DialoGPT-small",
        port=8100
    )

    try:
        await node.initialize()
        print("✅ Demo inference node initialized")

        # Run for a short time for demo purposes
        task = asyncio.create_task(node.run())

        # Let it run for 30 seconds
        await asyncio.sleep(30)

        task.cancel()
        print("🛑 Demo inference node stopped")

    except Exception as e:
        print(f"❌ Demo node failed: {e}")


async def run_demo_proxy_node():
    """Run a demo proxy node (requires API keys)"""
    print("\n🔧 Starting demo proxy node...")

    # Check if API keys are available
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

    if not (has_openai or has_anthropic):
        print("⚠️  No API keys found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test proxy functionality")
        return

    node = ProxyNode(
        node_id="demo-proxy-node",
        wallet_address="DemoProxyWallet123",
        gateway_url="http://localhost:8001",
        port=8200
    )

    try:
        await node.initialize()
        print("✅ Demo proxy node initialized")

        available_apis = []
        if has_openai:
            available_apis.append("OpenAI")
        if has_anthropic:
            available_apis.append("Anthropic")

        print(f"Available APIs: {', '.join(available_apis)}")

        # Run for a short time for demo purposes
        task = asyncio.create_task(node.run())

        # Let it run for 30 seconds
        await asyncio.sleep(30)

        task.cancel()
        print("🛑 Demo proxy node stopped")

    except Exception as e:
        print(f"❌ Demo proxy node failed: {e}")


async def main():
    """Main demo function"""
    import argparse

    parser = argparse.ArgumentParser(description="SolanaLM Network Demo")
    parser.add_argument(
        "--mode",
        choices=["client", "inference-node", "proxy-node", "full-demo"],
        default="client",
        help="Demo mode to run"
    )

    args = parser.parse_args()

    if args.mode == "client":
        await demo_network_usage()
    elif args.mode == "inference-node":
        await run_demo_inference_node()
    elif args.mode == "proxy-node":
        await run_demo_proxy_node()
    elif args.mode == "full-demo":
        print("🎯 Running full network demo...")

        # This would require running the gateway in background
        # For now, just show the client demo
        await demo_network_usage()

    print("\n✨ Demo complete!")
    print("\nNext steps:")
    print("1. Start the gateway: python scripts/run_gateway.py")
    print("2. Start nodes: python scripts/run_node.py --type inference --node-id node1 --wallet Wallet123")
    print("3. Test with client: python examples/basic_usage.py --mode client")


if __name__ == "__main__":
    asyncio.run(main())