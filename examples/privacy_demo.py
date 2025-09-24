#!/usr/bin/env python3
"""
SolanaLM Privacy Demo

Demonstrates Tor-like onion routing for private AI inference.
Shows how to use privacy features without revealing your identity.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.privacy.onion_routing import PrivateInferenceGateway, Circuit
from core.privacy.anonymous_payments import PrivatePaymentGateway
from core.registry.node_registry import NodeRegistry
from core.models.schemas import NodeCapabilities, InferenceRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PrivacyDemo:
    """Demonstrates SolanaLM's Tor-like privacy features"""

    def __init__(self):
        self.node_registry = None
        self.private_gateway = None
        self.payment_gateway = None

    async def setup_demo_environment(self):
        """Set up a demo environment with mock nodes"""
        print("🔧 Setting up privacy demo environment...")

        # Create mock node registry
        self.node_registry = NodeRegistry()
        await self.node_registry.initialize()

        # Add mock privacy-capable nodes from different countries
        demo_nodes = [
            NodeCapabilities(
                node_id="node-usa-1",
                wallet_address="usa-wallet-1",
                node_type="inference",
                supported_models=["gpt-3.5-turbo", "gpt-4"],
                endpoint="http://usa-node-1:8100",
                geographical_location="United States",
                network_provider="CloudFlare",
                reputation_score=0.95,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-germany-1",
                wallet_address="germany-wallet-1",
                node_type="inference",
                supported_models=["gpt-3.5-turbo", "claude-3"],
                endpoint="http://germany-node-1:8100",
                geographical_location="Germany",
                network_provider="Hetzner",
                reputation_score=0.92,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-singapore-1",
                wallet_address="singapore-wallet-1",
                node_type="inference",
                supported_models=["gpt-4", "claude-3"],
                endpoint="http://singapore-node-1:8100",
                geographical_location="Singapore",
                network_provider="AWS",
                reputation_score=0.88,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-canada-1",
                wallet_address="canada-wallet-1",
                node_type="inference",
                supported_models=["gpt-3.5-turbo", "llama-2"],
                endpoint="http://canada-node-1:8100",
                geographical_location="Canada",
                network_provider="DigitalOcean",
                reputation_score=0.90,
                supports_onion_routing=True
            ),
            NodeCapabilities(
                node_id="node-switzerland-1",
                wallet_address="switzerland-wallet-1",
                node_type="inference",
                supported_models=["gpt-4", "claude-3"],
                endpoint="http://switzerland-node-1:8100",
                geographical_location="Switzerland",
                network_provider="ProtonVPN",
                reputation_score=0.96,
                supports_onion_routing=True
            )
        ]

        for node in demo_nodes:
            await self.node_registry.register_node(node)

        # Initialize privacy gateway
        self.private_gateway = PrivateInferenceGateway(self.node_registry)

        # Initialize payment gateway (mock)
        from unittest.mock import AsyncMock
        mock_solana_client = AsyncMock()
        mock_solana_client.process_payment.return_value.transaction_signature = "demo-tx-signature"
        self.payment_gateway = PrivatePaymentGateway(mock_solana_client)

        print("✅ Demo environment ready with 5 privacy nodes across 5 countries")

    async def demo_circuit_building(self):
        """Demonstrate how circuits are built for privacy"""
        print("\n🧅 CIRCUIT BUILDING DEMO")
        print("=" * 50)

        nodes = await self.node_registry.get_all_nodes()

        for privacy_level in ["standard", "high", "maximum"]:
            print(f"\n🔒 Building {privacy_level} privacy circuit:")

            circuit = await self.private_gateway.build_circuit(
                available_nodes=nodes,
                target_model="gpt-4",
                privacy_level=privacy_level
            )

            if circuit:
                print(f"  ✅ Circuit ID: {circuit.circuit_id}")
                print(f"  🌐 Path length: {len(circuit.node_path)} hops")
                print(f"  🗺️  Geographic path:")
                for i, node_id in enumerate(circuit.node_path):
                    node = next(n for n in nodes if n.node_id == node_id)
                    hop_type = "Entry" if i == 0 else "Exit" if i == len(circuit.node_path)-1 else "Middle"
                    print(f"     {i+1}. {hop_type}: {node.geographical_location} ({node.network_provider})")

                privacy_properties = self._analyze_circuit_privacy(circuit, nodes)
                print(f"  🛡️  Privacy properties:")
                for prop in privacy_properties:
                    print(f"     • {prop}")
            else:
                print(f"  ❌ Failed to build {privacy_level} circuit")

    def _analyze_circuit_privacy(self, circuit: Circuit, nodes) -> list:
        """Analyze privacy properties of a circuit"""
        node_details = {n.node_id: n for n in nodes}
        path_nodes = [node_details[node_id] for node_id in circuit.node_path]

        properties = []

        # Geographic diversity
        countries = set(node.geographical_location for node in path_nodes)
        properties.append(f"Geographic diversity: {len(countries)} countries")

        # Network diversity
        providers = set(node.network_provider for node in path_nodes)
        properties.append(f"Network diversity: {len(providers)} providers")

        # Reputation
        avg_reputation = sum(node.reputation_score for node in path_nodes) / len(path_nodes)
        properties.append(f"Average reputation: {avg_reputation:.2f}")

        # Privacy features
        properties.append("Entry node knows your IP, not your query")
        properties.append("Middle nodes see only encrypted data")
        properties.append("Exit node processes query, doesn't know source")

        return properties

    async def demo_private_inference(self):
        """Demonstrate private inference requests"""
        print("\n🤖 PRIVATE INFERENCE DEMO")
        print("=" * 50)

        # Sample sensitive queries that benefit from privacy
        sensitive_queries = [
            {
                "prompt": "What are the symptoms of depression and how is it treated?",
                "context": "Personal health query",
                "privacy_level": "high"
            },
            {
                "prompt": "How to safely report corporate fraud to authorities?",
                "context": "Whistleblowing inquiry",
                "privacy_level": "maximum"
            },
            {
                "prompt": "Market analysis for entering competitor's space",
                "context": "Business intelligence",
                "privacy_level": "high"
            },
            {
                "prompt": "Legal implications of patent infringement in AI",
                "context": "Legal research",
                "privacy_level": "standard"
            }
        ]

        for i, query in enumerate(sensitive_queries, 1):
            print(f"\n📝 Query {i}: {query['context']}")
            print(f"   Privacy level: {query['privacy_level']}")
            print(f"   Prompt: '{query['prompt'][:60]}...'")

            # Create inference request
            request = InferenceRequest(
                model="gpt-4",
                prompt=query["prompt"],
                wallet_address="demo-user-wallet",
                max_tokens=100
            )

            try:
                # Process private inference
                start_time = asyncio.get_event_loop().time()
                response = await self.private_gateway.private_inference(
                    request,
                    query["privacy_level"]
                )
                end_time = asyncio.get_event_loop().time()

                print(f"   ✅ Response received in {end_time - start_time:.1f}s")
                print(f"   🔒 Node identity hidden: {response.get('node_id', 'unknown')}")
                print(f"   📊 Tokens generated: {response.get('tokens_generated', 0)}")

                # Show privacy benefits
                self._explain_privacy_benefits(query["privacy_level"])

            except Exception as e:
                print(f"   ❌ Request failed: {e}")

    def _explain_privacy_benefits(self, privacy_level: str):
        """Explain what privacy protections are active"""
        benefits = {
            "standard": [
                "Your IP address is hidden from the AI service",
                "Your query is encrypted through 3 nodes",
                "Payment amount is obfuscated with noise"
            ],
            "high": [
                "Strong geographic diversity in routing path",
                "Advanced payment mixing with delays",
                "Excludes nodes from surveillance-heavy countries",
                "Multiple network providers prevent correlation"
            ],
            "maximum": [
                "Maximum circuit length with 5+ hops",
                "Payment mixing pools for full anonymity",
                "Temporal delays prevent timing analysis",
                "Strongest protection against state-level surveillance"
            ]
        }

        print(f"   🛡️  Active protections:")
        for benefit in benefits.get(privacy_level, []):
            print(f"      • {benefit}")

    async def demo_payment_privacy(self):
        """Demonstrate private payment features"""
        print("\n💰 PAYMENT PRIVACY DEMO")
        print("=" * 50)

        # Test different payment privacy levels
        for privacy_level in ["standard", "high", "maximum"]:
            print(f"\n💳 Testing {privacy_level} payment privacy:")

            original_amount = 0.001  # 0.001 SOL

            payment = await self.payment_gateway.process_private_payment(
                circuit_id="demo-circuit-123",
                source_wallet="demo-user-wallet",
                target_wallet="demo-node-wallet",
                amount_sol=original_amount,
                privacy_level=privacy_level
            )

            obfuscation_ratio = float(payment.obfuscated_amount) / original_amount

            print(f"  Original amount: {original_amount} SOL")
            print(f"  Obfuscated amount: {payment.obfuscated_amount} SOL")
            print(f"  Obfuscation ratio: {obfuscation_ratio:.2f}x")

            # Explain payment privacy techniques
            self._explain_payment_privacy(privacy_level)

    def _explain_payment_privacy(self, privacy_level: str):
        """Explain payment privacy techniques"""
        techniques = {
            "standard": [
                "Add 0-20% random noise to payment amount",
                "Basic temporal randomization (0-5s delays)"
            ],
            "high": [
                "Add 0-50% noise and round to common amounts",
                "Extended temporal delays (0-60s)",
                "Payment routing through different path than requests"
            ],
            "maximum": [
                "Payment mixing pools with other users",
                "Round to common payment tiers + significant noise",
                "Extended delays up to 5 minutes for mixing",
                "Multiple payment batches prevent correlation"
            ]
        }

        print(f"  🔐 Privacy techniques:")
        for technique in techniques.get(privacy_level, []):
            print(f"     • {technique}")

    async def demo_threat_model(self):
        """Demonstrate what threats are protected against"""
        print("\n🎯 THREAT MODEL DEMO")
        print("=" * 50)

        threats = {
            "Traffic Analysis": {
                "description": "ISP or government monitoring your network traffic",
                "protection": "✅ Your ISP only sees encrypted traffic to entry node",
                "example": "Government can't tell you're using AI for sensitive research"
            },
            "Content Surveillance": {
                "description": "AI provider building profile of your queries",
                "protection": "✅ Exit node sees query but not your identity",
                "example": "OpenAI equivalent can't correlate your business intelligence queries"
            },
            "Economic Surveillance": {
                "description": "Tracking spending patterns on AI services",
                "protection": "✅ Payment amounts obfuscated and mixed",
                "example": "Can't determine your AI usage budget or frequency"
            },
            "Correlation Attacks": {
                "description": "Linking multiple requests to same user",
                "protection": "✅ Each request uses different path and timing",
                "example": "Research queries can't be linked to your identity"
            },
            "Node Collusion": {
                "description": "Multiple nodes working together to deanonymize",
                "protection": "⚠️ Requires geographic and operator diversity",
                "example": "Use high/maximum privacy for sensitive queries"
            }
        }

        for threat_name, details in threats.items():
            print(f"\n🎯 {threat_name}:")
            print(f"   Description: {details['description']}")
            print(f"   Protection: {details['protection']}")
            print(f"   Example: {details['example']}")

    async def demo_comparison(self):
        """Compare privacy vs traditional AI services"""
        print("\n⚖️  PRIVACY COMPARISON")
        print("=" * 50)

        comparison = {
            "Traditional AI (OpenAI/Anthropic)": {
                "identity_privacy": "❌ Full identity exposure",
                "content_privacy": "❌ All queries logged and analyzed",
                "payment_privacy": "❌ Clear payment trails",
                "government_access": "❌ Subject to data requests",
                "corporate_profiling": "❌ Detailed usage profiles built"
            },
            "SolanaLM Private Mode": {
                "identity_privacy": "✅ Tor-like anonymity",
                "content_privacy": "✅ Exit node only, no logging",
                "payment_privacy": "✅ Obfuscated and mixed payments",
                "government_access": "✅ No single point of control",
                "corporate_profiling": "✅ Cannot correlate requests"
            }
        }

        for service, features in comparison.items():
            print(f"\n🔍 {service}:")
            for feature, status in features.items():
                feature_name = feature.replace('_', ' ').title()
                print(f"   {feature_name}: {status}")

    async def run_full_demo(self):
        """Run the complete privacy demonstration"""
        print("🕵️  SOLANALM TOR-LIKE PRIVACY DEMO")
        print("=" * 60)
        print("Demonstrating private AI inference that protects your identity,")
        print("queries, and payment patterns from surveillance.\n")

        try:
            await self.setup_demo_environment()
            await self.demo_circuit_building()
            await self.demo_private_inference()
            await self.demo_payment_privacy()
            await self.demo_threat_model()
            await self.demo_comparison()

            print("\n✨ DEMO COMPLETE")
            print("=" * 60)
            print("🎯 Key Takeaways:")
            print("• SolanaLM provides Tor-like privacy for AI inference")
            print("• Each request uses a fresh encrypted circuit")
            print("• Payments are obfuscated and mixed for anonymity")
            print("• No single entity can see both your identity and queries")
            print("• Perfect for sensitive business, personal, or research use cases")
            print("\n🚀 Ready to try private AI? See examples/basic_usage.py")

        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"❌ Demo failed: {e}")


async def test_private_inference():
    """Entry point for testing private inference"""
    demo = PrivacyDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    # Run the privacy demo
    asyncio.run(test_private_inference())