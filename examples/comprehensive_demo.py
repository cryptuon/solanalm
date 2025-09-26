#!/usr/bin/env python3
"""
Comprehensive SolanaLM Demo
Demonstrates all key features: Federated Learning, Multiple Backends, and Network Operations
"""

import asyncio
import logging
import sys
import os
import time
from typing import List, Dict, Any

# Add core to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.training.federated_learning import run_training_demo, fl_manager
from core.nodes.inference.enhanced_node import (
    EnhancedInferenceNode,
    ModelBackend,
    create_transformers_node
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SolanaLMDemo:
    """Comprehensive demonstration of SolanaLM capabilities"""

    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.demo_results: Dict[str, Any] = {}

    async def run_federated_learning_demo(self):
        """Demonstrate federated learning capabilities"""
        print("\n🤖 FEDERATED LEARNING DEMONSTRATION")
        print("=" * 50)

        # Simulate multiple training nodes
        node_ids = ["fl-node-1", "fl-node-2", "fl-node-3", "fl-node-4"]

        print(f"📊 Starting federated learning with {len(node_ids)} nodes")

        # Run multiple federated learning rounds
        for round_num in range(3):
            print(f"\n🔄 Running federated learning round {round_num + 1}")

            # Run training round
            result = run_training_demo(node_ids)

            print(f"   ✅ Round {result['round']} completed:")
            print(f"   📈 Average loss: {result['avg_loss']:.4f}")
            print(f"   📝 Total samples: {result['total_samples']}")
            print(f"   🔗 Participating nodes: {len(result['participating_nodes'])}")

            self.demo_results[f"fl_round_{round_num + 1}"] = result

            # Brief pause between rounds
            await asyncio.sleep(1)

        print("\n✨ Federated learning demonstration completed!")
        print(f"🎯 Final model trained on {sum(r['total_samples'] for r in self.demo_results.values() if 'fl_round' in r)} total samples")

    def demonstrate_multiple_backends(self):
        """Show supported backends and their configurations"""
        print("\n🚀 SUPPORTED INFERENCE BACKENDS")
        print("=" * 50)

        backends_info = {
            "transformers": {
                "description": "PyTorch + Hugging Face Transformers",
                "models": ["microsoft/DialoGPT-small", "gpt2", "distilbert-base-uncased"],
                "use_case": "Local GPU/CPU inference with open-source models"
            },
            "llama_cpp": {
                "description": "llama.cpp Python bindings",
                "models": ["llama-7b.gguf", "vicuna-7b.gguf", "alpaca-7b.gguf"],
                "use_case": "Efficient CPU inference with quantized models"
            },
            "openai": {
                "description": "OpenAI API proxy",
                "models": ["gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                "use_case": "High-quality responses via OpenAI API"
            },
            "anthropic": {
                "description": "Anthropic Claude API proxy",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "use_case": "Advanced reasoning via Anthropic API"
            },
            "ollama": {
                "description": "Ollama local server proxy",
                "models": ["llama2", "codellama", "mistral", "neural-chat"],
                "use_case": "Local models via Ollama server"
            },
            "custom_api": {
                "description": "Custom API endpoint proxy",
                "models": ["any-custom-model"],
                "use_case": "Integration with existing inference APIs"
            }
        }

        for backend, info in backends_info.items():
            print(f"\n🔧 {backend.upper()}")
            print(f"   📝 {info['description']}")
            print(f"   🤖 Example models: {', '.join(info['models'][:2])}")
            print(f"   💡 Use case: {info['use_case']}")

        self.demo_results["supported_backends"] = backends_info

    async def run_inference_demo(self):
        """Demonstrate inference capabilities"""
        print("\n💬 INFERENCE DEMONSTRATION")
        print("=" * 50)

        try:
            # Create a simple inference node for demo
            print("🚀 Starting Transformers-based inference node...")

            node = EnhancedInferenceNode(
                node_id="demo-inference-node",
                wallet_address="DemoWallet123",
                gateway_url="http://localhost:8001",
                backend=ModelBackend.TRANSFORMERS,
                model_name="microsoft/DialoGPT-small",
                port=8199  # Use different port to avoid conflicts
            )

            await node.initialize()

            # Test some inference examples
            test_prompts = [
                "Hello, how are you today?",
                "What is machine learning?",
                "Tell me about decentralized networks."
            ]

            print("🧪 Testing inference with sample prompts:")

            for i, prompt in enumerate(test_prompts, 1):
                print(f"\n📝 Test {i}: '{prompt}'")

                # Create mock inference request
                from core.models.schemas import InferenceRequest
                request = InferenceRequest(
                    prompt=prompt,
                    max_tokens=50,
                    temperature=0.7,
                    model="microsoft/DialoGPT-small",
                    wallet_address="DemoWallet123"
                )

                try:
                    start_time = time.time()
                    response = await node.process_inference(request)
                    end_time = time.time()

                    print(f"   🤖 Response: {response.response}")
                    print(f"   ⏱️  Processing time: {end_time - start_time:.2f}s")
                    print(f"   📊 Tokens generated: {response.tokens_generated}")

                except Exception as e:
                    print(f"   ❌ Error: {e}")

                await asyncio.sleep(0.5)

            # Store node info
            self.nodes["demo_inference"] = {
                "node_id": node.node_id,
                "backend": node.backend.value,
                "model": node.model_name,
                "requests_served": node.requests_served
            }

            print("\n✨ Inference demonstration completed!")

        except Exception as e:
            print(f"❌ Inference demo failed: {e}")
            print("💡 Note: This requires model downloads and may need GPU/sufficient RAM")

    def show_network_architecture(self):
        """Display the SolanaLM network architecture"""
        print("\n🏗️  SOLANALM NETWORK ARCHITECTURE")
        print("=" * 50)

        architecture = {
            "Gateway": {
                "role": "Request routing, load balancing, payment processing",
                "components": ["Node Registry", "Payment Client", "OpenAI Compatibility Layer"]
            },
            "Inference Nodes": {
                "role": "Serve ML model inference requests",
                "types": ["Transformers (local)", "llama.cpp (quantized)", "API Proxies"]
            },
            "Training Nodes": {
                "role": "Participate in federated learning rounds",
                "features": ["Local training", "Gradient aggregation", "Model updates"]
            },
            "Proxy Nodes": {
                "role": "Gateway to external ML APIs",
                "targets": ["OpenAI", "Anthropic", "Ollama", "Custom APIs"]
            },
            "Hybrid Nodes": {
                "role": "Switch between inference and training modes",
                "benefit": "Maximize earnings from both revenue streams"
            }
        }

        for component, details in architecture.items():
            print(f"\n🔧 {component}")
            print(f"   📝 Role: {details['role']}")

            if 'components' in details:
                print(f"   🧩 Components: {', '.join(details['components'])}")
            if 'types' in details:
                print(f"   🤖 Types: {', '.join(details['types'])}")
            if 'features' in details:
                print(f"   ⭐ Features: {', '.join(details['features'])}")
            if 'targets' in details:
                print(f"   🎯 Targets: {', '.join(details['targets'])}")
            if 'benefit' in details:
                print(f"   💰 Benefit: {details['benefit']}")

    def show_economic_model(self):
        """Display the economic incentive model"""
        print("\n💰 ECONOMIC INCENTIVE MODEL")
        print("=" * 50)

        economics = {
            "Dual Revenue Streams": [
                "💸 Inference Revenue: 0.001-0.01 SOL per request",
                "🎓 Training Revenue: 0.1-1.0 SOL per federated learning round",
                "⚡ Efficiency: Same hardware earns from both streams"
            ],
            "Payment Flow": [
                "👤 User pays for inference request",
                "🏦 Gateway processes SOL micro-transaction",
                "🤖 Node receives payment after successful response",
                "📈 Training rewards distributed after each FL round"
            ],
            "Network Effects": [
                "📊 More nodes = Better load distribution",
                "🚀 More training participants = Faster model improvement",
                "🔄 Better models = More inference demand",
                "💎 Higher quality = Premium pricing potential"
            ]
        }

        for category, items in economics.items():
            print(f"\n💡 {category}")
            for item in items:
                print(f"   {item}")

    async def run_comprehensive_demo(self):
        """Run the complete demonstration"""
        print("🌟 SOLANALM COMPREHENSIVE DEMONSTRATION")
        print("=" * 60)
        print("Hybrid Decentralized Network: LLM Inference + Federated Learning")
        print("=" * 60)

        # Show architecture
        self.show_network_architecture()

        # Show economic model
        self.show_economic_model()

        # Show supported backends
        self.demonstrate_multiple_backends()

        # Run federated learning demo
        await self.run_federated_learning_demo()

        # Run inference demo
        await self.run_inference_demo()

        # Summary
        print("\n🎉 DEMONSTRATION SUMMARY")
        print("=" * 50)
        print("✅ Federated Learning: Multi-node training simulation completed")
        print("✅ Multiple Backends: 6 different inference backends supported")
        print("✅ Network Architecture: Complete hybrid system demonstrated")
        print("✅ Economic Model: Dual revenue streams explained")

        if self.nodes:
            print(f"✅ Live Demo: {len(self.nodes)} node(s) demonstrated")

        print("\n🚀 Next Steps:")
        print("   1. Deploy on Solana devnet/testnet")
        print("   2. Add more sophisticated federated learning algorithms")
        print("   3. Implement advanced privacy features")
        print("   4. Scale to production with real economic incentives")

        return self.demo_results


async def main():
    """Main demo entry point"""
    demo = SolanaLMDemo()

    try:
        results = await demo.run_comprehensive_demo()

        print("\n📊 Demo completed successfully!")
        print(f"Results collected: {len(results)} categories")

    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())