#!/usr/bin/env python3
"""
Advanced SolanaLM Client Examples

Demonstrates advanced features including:
- Privacy-preserving inference with different levels
- Federated learning participation
- Batch processing and streaming
- Error handling and resilience
- Custom model fine-tuning
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
import json

from solanalm_client import SolanaLMClient
from openai_compat import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedSolanaLMExamples:
    """Advanced usage examples for SolanaLM"""

    def __init__(self):
        self.client = None

    async def __aenter__(self):
        self.client = SolanaLMClient()
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def private_inference_examples(self):
        """Demonstrate private inference with different privacy levels"""
        print("\n🕵️ PRIVATE INFERENCE EXAMPLES")
        print("=" * 50)

        # Example 1: Standard privacy for general queries
        print("\n1. 📝 Standard Privacy - General Business Query")
        response = await self.client.private_inference(
            model="gpt-4",
            prompt="What are the key trends in AI development for 2024?",
            privacy_level="standard",
            wallet_address="demo-wallet"
        )
        print(f"   Response: {response.response[:100]}...")
        print(f"   Latency: {response.processing_time:.2f}s")
        print(f"   Privacy: 3-hop circuit, basic anonymity")

        # Example 2: High privacy for sensitive business intelligence
        print("\n2. 🏢 High Privacy - Competitive Intelligence")
        response = await self.client.private_inference(
            model="gpt-4",
            prompt="Analyze potential market opportunities in fintech disruption",
            privacy_level="high",
            wallet_address="demo-wallet"
        )
        print(f"   Response: {response.response[:100]}...")
        print(f"   Latency: {response.processing_time:.2f}s")
        print(f"   Privacy: 4-5 hop circuit, geographic diversity")

        # Example 3: Maximum privacy for whistleblowing/journalism
        print("\n3. 🔒 Maximum Privacy - Investigative Research")
        response = await self.client.private_inference(
            model="gpt-4",
            prompt="How to safely report corporate fraud while protecting identity?",
            privacy_level="maximum",
            wallet_address="demo-wallet"
        )
        print(f"   Response: {response.response[:100]}...")
        print(f"   Latency: {response.processing_time:.2f}s")
        print(f"   Privacy: 5+ hop circuit, payment mixing, maximum anonymity")

        # Example 4: Comparing privacy vs performance
        print("\n4. ⚖️ Privacy vs Performance Comparison")
        privacy_levels = ["standard", "high", "maximum"]
        prompt = "Explain quantum computing in simple terms"

        for level in privacy_levels:
            start_time = time.time()
            response = await self.client.private_inference(
                model="gpt-3.5-turbo",
                prompt=prompt,
                privacy_level=level,
                wallet_address="demo-wallet"
            )
            end_time = time.time()

            print(f"   {level.capitalize()}: {end_time - start_time:.2f}s latency")

    async def batch_processing_examples(self):
        """Demonstrate batch processing capabilities"""
        print("\n📦 BATCH PROCESSING EXAMPLES")
        print("=" * 50)

        # Example 1: Batch inference for multiple prompts
        print("\n1. 🔄 Batch Inference - Multiple Prompts")
        prompts = [
            "Summarize the benefits of renewable energy",
            "Explain machine learning in 50 words",
            "What are the challenges of space exploration?",
            "Describe the impact of social media on society"
        ]

        batch_responses = await self.client.batch_inference(
            model="gpt-3.5-turbo",
            prompts=prompts,
            wallet_address="demo-wallet",
            max_concurrent=2  # Process 2 at a time
        )

        for i, response in enumerate(batch_responses):
            print(f"   Prompt {i+1}: {response.response[:60]}...")

        # Example 2: Streaming batch results
        print("\n2. 🌊 Streaming Batch Processing")
        async for i, response in enumerate(self.client.stream_batch_inference(
            model="gpt-3.5-turbo",
            prompts=prompts[:3],  # First 3 prompts
            wallet_address="demo-wallet"
        )):
            print(f"   Stream {i+1}: Received response ({len(response.response)} chars)")

    async def federated_learning_examples(self):
        """Demonstrate federated learning participation"""
        print("\n🤝 FEDERATED LEARNING EXAMPLES")
        print("=" * 50)

        # Example 1: Join training round as participant
        print("\n1. 🎓 Joining Training Round")
        try:
            training_config = await self.client.join_training_round(
                model_name="llama-7b",
                node_capabilities={
                    "gpu_memory": 24,
                    "compute_power": "high",
                    "availability_hours": 8
                },
                reward_expectation=0.05  # Expect 0.05 SOL per round
            )
            print(f"   ✅ Joined training round: {training_config['round_id']}")
            print(f"   📊 Expected reward: {training_config['reward_per_update']} SOL")
            print(f"   ⏱️ Training duration: {training_config['estimated_duration']} minutes")

        except Exception as e:
            print(f"   ⚠️ Training round not available: {e}")

        # Example 2: Monitor training progress
        print("\n2. 📈 Monitoring Training Progress")
        training_status = await self.client.get_training_status()
        print(f"   Active rounds: {training_status['active_rounds']}")
        print(f"   Your participation: {training_status['your_rounds']}")
        print(f"   Total rewards earned: {training_status['total_rewards']} SOL")

        # Example 3: Custom model training
        print("\n3. 🔧 Custom Model Training")
        custom_config = {
            "model_architecture": "gpt-2",
            "training_data": "domain_specific_dataset",
            "learning_rate": 0.0001,
            "epochs": 5,
            "privacy_level": "high"  # Private training
        }

        try:
            training_result = await self.client.start_custom_training(
                config=custom_config,
                wallet_address="demo-wallet"
            )
            print(f"   ✅ Custom training started: {training_result['training_id']}")
            print(f"   💰 Estimated cost: {training_result['estimated_cost']} SOL")

        except Exception as e:
            print(f"   ⚠️ Custom training unavailable: {e}")

    async def error_handling_examples(self):
        """Demonstrate robust error handling and resilience"""
        print("\n🛡️ ERROR HANDLING & RESILIENCE EXAMPLES")
        print("=" * 50)

        # Example 1: Retry with backoff on failures
        print("\n1. 🔄 Automatic Retry with Backoff")
        async def resilient_inference(prompt: str, max_retries: int = 3):
            for attempt in range(max_retries):
                try:
                    response = await self.client.inference(
                        model="gpt-4",
                        prompt=prompt,
                        wallet_address="demo-wallet",
                        timeout=30
                    )
                    return response
                except Exception as e:
                    wait_time = (2 ** attempt)  # Exponential backoff
                    print(f"   Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"   Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"   All {max_retries} attempts failed")
                        raise

        try:
            response = await resilient_inference("What is the meaning of life?")
            print(f"   ✅ Resilient inference succeeded: {response.response[:50]}...")
        except Exception as e:
            print(f"   ❌ All retries failed: {e}")

        # Example 2: Fallback to different models
        print("\n2. 🔀 Model Fallback Strategy")
        preferred_models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        prompt = "Explain blockchain technology"

        for model in preferred_models:
            try:
                response = await self.client.inference(
                    model=model,
                    prompt=prompt,
                    wallet_address="demo-wallet"
                )
                print(f"   ✅ Success with {model}: {response.response[:50]}...")
                break
            except Exception as e:
                print(f"   ⚠️ {model} failed: {e}")
                continue
        else:
            print("   ❌ All model fallbacks failed")

        # Example 3: Graceful degradation with privacy levels
        print("\n3. 📉 Privacy Level Degradation")
        privacy_levels = ["maximum", "high", "standard"]
        sensitive_prompt = "Confidential business strategy analysis"

        for level in privacy_levels:
            try:
                response = await self.client.private_inference(
                    model="gpt-4",
                    prompt=sensitive_prompt,
                    privacy_level=level,
                    wallet_address="demo-wallet",
                    timeout=20
                )
                print(f"   ✅ Success with {level} privacy: {response.processing_time:.2f}s")
                break
            except Exception as e:
                print(f"   ⚠️ {level} privacy failed: {e}")
                continue

    async def cost_optimization_examples(self):
        """Demonstrate cost optimization strategies"""
        print("\n💰 COST OPTIMIZATION EXAMPLES")
        print("=" * 50)

        # Example 1: Model selection based on cost
        print("\n1. 💸 Cost-Efficient Model Selection")
        prompt = "Write a short poem about artificial intelligence"

        models_by_cost = [
            ("gpt-3.5-turbo", "Low cost, good quality"),
            ("claude-3", "Medium cost, high quality"),
            ("gpt-4", "High cost, best quality")
        ]

        for model, description in models_by_cost:
            try:
                start_time = time.time()
                response = await self.client.inference(
                    model=model,
                    prompt=prompt,
                    wallet_address="demo-wallet",
                    max_tokens=100
                )
                end_time = time.time()

                print(f"   {model}: {response.cost_sol} SOL - {description}")
                print(f"     Quality: {len(response.response)} chars in {end_time-start_time:.2f}s")
            except Exception as e:
                print(f"   {model}: Unavailable - {e}")

        # Example 2: Bulk pricing for batch operations
        print("\n2. 📦 Bulk Pricing Benefits")
        individual_cost = 0
        batch_cost = 0

        # Individual requests
        prompts = ["Question 1", "Question 2", "Question 3"]
        for prompt in prompts:
            try:
                response = await self.client.inference(
                    model="gpt-3.5-turbo",
                    prompt=prompt,
                    wallet_address="demo-wallet"
                )
                individual_cost += response.cost_sol
            except:
                pass

        # Batch request
        try:
            batch_responses = await self.client.batch_inference(
                model="gpt-3.5-turbo",
                prompts=prompts,
                wallet_address="demo-wallet"
            )
            batch_cost = sum(r.cost_sol for r in batch_responses)
        except:
            pass

        if individual_cost > 0 and batch_cost > 0:
            savings = ((individual_cost - batch_cost) / individual_cost) * 100
            print(f"   Individual requests: {individual_cost:.6f} SOL")
            print(f"   Batch request: {batch_cost:.6f} SOL")
            print(f"   Savings: {savings:.1f}%")

    async def integration_examples(self):
        """Demonstrate integration with existing workflows"""
        print("\n🔗 INTEGRATION EXAMPLES")
        print("=" * 50)

        # Example 1: Drop-in OpenAI replacement
        print("\n1. 🔄 OpenAI API Compatibility")

        # Configure OpenAI client to use SolanaLM
        openai.api_key = "demo-wallet"
        openai.api_base = "http://localhost:8001/v1"

        try:
            # Standard OpenAI call
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Explain quantum computing"}
                ],
                max_tokens=150
            )
            print(f"   ✅ OpenAI compatibility: {response.choices[0].message.content[:50]}...")

            # With privacy headers
            private_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": "Sensitive business analysis"}
                ],
                headers={"X-Privacy-Level": "high"}
            )
            print(f"   🔒 Private OpenAI call: {private_response.choices[0].message.content[:50]}...")

        except Exception as e:
            print(f"   ⚠️ OpenAI compatibility issue: {e}")

        # Example 2: Webhook integration
        print("\n2. 🔔 Webhook Integration")
        webhook_config = {
            "url": "https://your-app.com/solanalm-webhook",
            "events": ["training_complete", "payment_received"],
            "secret": "webhook-secret-key"
        }

        try:
            webhook_result = await self.client.configure_webhook(webhook_config)
            print(f"   ✅ Webhook configured: {webhook_result['webhook_id']}")
            print(f"   📡 Events: {', '.join(webhook_config['events'])}")
        except Exception as e:
            print(f"   ⚠️ Webhook setup failed: {e}")

        # Example 3: Custom application integration
        print("\n3. 🏗️ Custom Application Integration")

        class AIAssistant:
            """Example AI assistant using SolanaLM"""

            def __init__(self, client):
                self.client = client
                self.conversation_history = []

            async def chat(self, message: str, privacy_level: str = "standard"):
                """Chat with privacy-preserving memory"""
                self.conversation_history.append({"role": "user", "content": message})

                # Prepare context (last 5 messages)
                context = self.conversation_history[-5:]
                prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])

                response = await self.client.private_inference(
                    model="gpt-3.5-turbo",
                    prompt=prompt,
                    privacy_level=privacy_level,
                    wallet_address="demo-wallet"
                )

                self.conversation_history.append({"role": "assistant", "content": response.response})
                return response.response

        # Test custom assistant
        assistant = AIAssistant(self.client)
        response1 = await assistant.chat("Hello, what can you help me with?")
        response2 = await assistant.chat("Tell me about machine learning", privacy_level="high")

        print(f"   🤖 Assistant response 1: {response1[:50]}...")
        print(f"   🔒 Private response 2: {response2[:50]}...")

    async def monitoring_examples(self):
        """Demonstrate monitoring and analytics capabilities"""
        print("\n📊 MONITORING & ANALYTICS EXAMPLES")
        print("=" * 50)

        # Example 1: Usage analytics
        print("\n1. 📈 Usage Analytics")
        try:
            analytics = await self.client.get_usage_analytics(
                wallet_address="demo-wallet",
                period="last_7_days"
            )

            print(f"   Total requests: {analytics['total_requests']}")
            print(f"   Total cost: {analytics['total_cost']} SOL")
            print(f"   Average latency: {analytics['avg_latency']:.2f}s")
            print(f"   Privacy requests: {analytics['privacy_requests']} ({analytics['privacy_percentage']:.1f}%)")
            print(f"   Most used model: {analytics['top_model']}")

        except Exception as e:
            print(f"   ⚠️ Analytics unavailable: {e}")

        # Example 2: Network health monitoring
        print("\n2. 🏥 Network Health Monitoring")
        try:
            health = await self.client.get_network_health()

            print(f"   Active nodes: {health['active_nodes']}")
            print(f"   Network latency: {health['avg_latency']:.2f}s")
            print(f"   Success rate: {health['success_rate']:.1f}%")
            print(f"   Privacy network: {health['privacy_nodes']} nodes")

        except Exception as e:
            print(f"   ⚠️ Health data unavailable: {e}")

        # Example 3: Performance benchmarking
        print("\n3. 🏃 Performance Benchmarking")
        benchmark_prompts = [
            "Explain artificial intelligence",
            "Write a Python function",
            "Summarize recent tech news"
        ]

        results = []
        for prompt in benchmark_prompts:
            start_time = time.time()
            try:
                response = await self.client.inference(
                    model="gpt-3.5-turbo",
                    prompt=prompt,
                    wallet_address="demo-wallet"
                )
                end_time = time.time()

                results.append({
                    "prompt": prompt[:30] + "...",
                    "latency": end_time - start_time,
                    "tokens": response.tokens_generated,
                    "cost": response.cost_sol
                })
            except Exception as e:
                results.append({
                    "prompt": prompt[:30] + "...",
                    "error": str(e)
                })

        for result in results:
            if "error" in result:
                print(f"   ❌ {result['prompt']}: {result['error']}")
            else:
                print(f"   ✅ {result['prompt']}: {result['latency']:.2f}s, {result['tokens']} tokens")


async def run_advanced_examples():
    """Run all advanced examples"""
    print("🚀 SOLANALM ADVANCED EXAMPLES")
    print("=" * 60)
    print("Demonstrating advanced features and integration patterns")

    async with AdvancedSolanaLMExamples() as examples:
        try:
            await examples.private_inference_examples()
            await examples.batch_processing_examples()
            await examples.federated_learning_examples()
            await examples.error_handling_examples()
            await examples.cost_optimization_examples()
            await examples.integration_examples()
            await examples.monitoring_examples()

            print("\n✨ ADVANCED EXAMPLES COMPLETE")
            print("=" * 60)
            print("🎯 Key Features Demonstrated:")
            print("• Tor-like privacy with multiple security levels")
            print("• Federated learning participation and rewards")
            print("• Robust error handling and fallback strategies")
            print("• Cost optimization and batch processing")
            print("• OpenAI API compatibility and integrations")
            print("• Comprehensive monitoring and analytics")
            print("\n🚀 Ready to build privacy-preserving AI applications!")

        except Exception as e:
            logger.error(f"Advanced examples failed: {e}")
            print(f"❌ Examples failed: {e}")


if __name__ == "__main__":
    asyncio.run(run_advanced_examples())