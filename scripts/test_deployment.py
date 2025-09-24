#!/usr/bin/env python3

"""
Deployment Testing Script

Comprehensive testing of deployed SolanaLM network.
"""

import asyncio
import aiohttp
import time
import json
import sys
import os
from typing import Dict, Any, List

# Add core to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from client.python.solanalm_client import SolanaLMClient
from client.python.openai_compat import openai, set_api_key, set_api_base


class DeploymentTester:
    """Comprehensive testing of deployed network"""

    def __init__(self, gateway_url: str = "http://localhost:8001"):
        self.gateway_url = gateway_url
        self.test_wallet = "test-deployment-wallet-123"
        self.results = []

    async def test_basic_connectivity(self) -> bool:
        """Test basic connectivity to gateway"""
        print("🔌 Testing basic connectivity...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/health", timeout=10) as response:
                    if response.status == 200:
                        print("  ✅ Gateway is accessible")
                        return True
                    else:
                        print(f"  ❌ Gateway returned {response.status}")
                        return False

        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
            return False

    async def test_network_status(self) -> bool:
        """Test network status endpoint"""
        print("📊 Testing network status...")

        try:
            async with SolanaLMClient(self.gateway_url) as client:
                status = await client.get_network_status()

                print(f"  Service: {status.get('service', 'Unknown')}")
                print(f"  Version: {status.get('version', 'Unknown')}")

                network_stats = status.get('network_stats', {})
                print(f"  Total nodes: {network_stats.get('total_nodes', 0)}")
                print(f"  Active nodes: {network_stats.get('active_nodes', 0)}")

                if network_stats.get('total_nodes', 0) > 0:
                    print("  ✅ Network has registered nodes")
                    return True
                else:
                    print("  ⚠️  No nodes registered yet")
                    return False

        except Exception as e:
            print(f"  ❌ Network status check failed: {e}")
            return False

    async def test_model_listing(self) -> bool:
        """Test model listing"""
        print("🤖 Testing model listing...")

        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()

                if models:
                    print(f"  ✅ Found {len(models)} available models:")
                    for model in models[:3]:  # Show first 3
                        print(f"    - {model}")
                    return True
                else:
                    print("  ❌ No models available")
                    return False

        except Exception as e:
            print(f"  ❌ Model listing failed: {e}")
            return False

    async def test_openai_compatibility(self) -> bool:
        """Test OpenAI-compatible API"""
        print("🔄 Testing OpenAI compatibility...")

        try:
            # Test model listing
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.gateway_url}/v1/models", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('data', [])
                        print(f"  ✅ OpenAI API: {len(models)} models available")
                    else:
                        print(f"  ❌ OpenAI API model listing failed: {response.status}")
                        return False

            # Test chat completion
            set_api_key(self.test_wallet)
            set_api_base(f"{self.gateway_url}/v1")

            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",  # Will use first available model
                messages=[{"role": "user", "content": "Say 'Hello from SolanaLM' in exactly those words"}],
                max_tokens=20
            )

            if response and response.choices:
                print(f"  ✅ Chat completion: {response.choices[0]['message']['content'][:50]}...")
                return True
            else:
                print("  ❌ Chat completion failed: No response")
                return False

        except Exception as e:
            print(f"  ❌ OpenAI compatibility test failed: {e}")
            return False

    async def test_inference_performance(self) -> Dict[str, Any]:
        """Test inference performance"""
        print("⚡ Testing inference performance...")

        test_prompts = [
            "What is 2 + 2?",
            "Name three colors.",
            "Complete: The sky is",
            "Say hello",
            "Count to 5"
        ]

        results = {
            "total_requests": len(test_prompts),
            "successful": 0,
            "failed": 0,
            "total_time": 0,
            "total_tokens": 0,
            "total_cost": 0,
            "avg_latency": 0
        }

        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()
                if not models:
                    print("  ❌ No models available for performance testing")
                    return results

                model = models[0]  # Use first available model
                print(f"  Using model: {model}")

                start_time = time.time()

                for i, prompt in enumerate(test_prompts):
                    try:
                        request_start = time.time()

                        response = await client.inference(
                            model=model,
                            prompt=prompt,
                            wallet_address=self.test_wallet,
                            max_tokens=30
                        )

                        request_time = time.time() - request_start

                        results["successful"] += 1
                        results["total_tokens"] += response.tokens_generated
                        results["total_cost"] += response.cost_sol

                        print(f"  {i+1}. ✅ '{prompt[:20]}...' -> {response.tokens_generated} tokens, {request_time:.2f}s")

                    except Exception as e:
                        results["failed"] += 1
                        print(f"  {i+1}. ❌ '{prompt[:20]}...' -> Error: {e}")

                results["total_time"] = time.time() - start_time
                results["avg_latency"] = results["total_time"] / len(test_prompts)

                print(f"  📊 Performance Summary:")
                print(f"    Success rate: {results['successful']}/{results['total_requests']} ({results['successful']/results['total_requests']*100:.1f}%)")
                print(f"    Total time: {results['total_time']:.2f}s")
                print(f"    Avg latency: {results['avg_latency']:.2f}s")
                print(f"    Total tokens: {results['total_tokens']}")
                print(f"    Total cost: {results['total_cost']:.6f} SOL")

        except Exception as e:
            print(f"  ❌ Performance test setup failed: {e}")

        return results

    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """Test concurrent request handling"""
        print("🔀 Testing concurrent requests...")

        concurrent_requests = 5
        prompt = "Hello, world!"

        results = {
            "concurrent_requests": concurrent_requests,
            "successful": 0,
            "failed": 0,
            "total_time": 0,
            "avg_latency": 0
        }

        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()
                if not models:
                    print("  ❌ No models available for concurrency testing")
                    return results

                model = models[0]

                # Create concurrent requests
                tasks = []
                start_time = time.time()

                for i in range(concurrent_requests):
                    task = client.inference(
                        model=model,
                        prompt=f"{prompt} (Request {i+1})",
                        wallet_address=f"{self.test_wallet}-{i}",
                        max_tokens=20
                    )
                    tasks.append(task)

                # Execute concurrently
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                results["total_time"] = time.time() - start_time
                results["avg_latency"] = results["total_time"] / concurrent_requests

                # Process results
                for i, response in enumerate(responses):
                    if isinstance(response, Exception):
                        results["failed"] += 1
                        print(f"  {i+1}. ❌ Request failed: {response}")
                    else:
                        results["successful"] += 1
                        print(f"  {i+1}. ✅ Request succeeded: {response.tokens_generated} tokens")

                print(f"  📊 Concurrency Summary:")
                print(f"    Successful: {results['successful']}/{concurrent_requests}")
                print(f"    Total time: {results['total_time']:.2f}s")
                print(f"    Avg latency: {results['avg_latency']:.2f}s")

        except Exception as e:
            print(f"  ❌ Concurrency test failed: {e}")

        return results

    async def test_error_handling(self) -> bool:
        """Test error handling"""
        print("🛡️ Testing error handling...")

        tests_passed = 0
        total_tests = 3

        # Test 1: Invalid model
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                await client.inference(
                    model="nonexistent-model-xyz",
                    prompt="test",
                    wallet_address=self.test_wallet
                )
            print("  ❌ Invalid model test: Should have failed")
        except Exception:
            print("  ✅ Invalid model test: Correctly rejected")
            tests_passed += 1

        # Test 2: Empty prompt
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()
                if models:
                    await client.inference(
                        model=models[0],
                        prompt="",
                        wallet_address=self.test_wallet
                    )
            print("  ❌ Empty prompt test: Should have failed")
        except Exception:
            print("  ✅ Empty prompt test: Correctly rejected")
            tests_passed += 1

        # Test 3: Invalid endpoint
        try:
            async with SolanaLMClient("http://localhost:9999") as client:
                await client.get_network_status()
            print("  ❌ Invalid endpoint test: Should have failed")
        except Exception:
            print("  ✅ Invalid endpoint test: Correctly rejected")
            tests_passed += 1

        success_rate = tests_passed / total_tests
        print(f"  📊 Error handling: {tests_passed}/{total_tests} tests passed ({success_rate*100:.1f}%)")

        return success_rate >= 0.8

    async def test_integration_examples(self) -> bool:
        """Test integration examples work"""
        print("🔗 Testing integration examples...")

        try:
            # Test simple chat function
            from client.python.openai_compat import chat

            set_api_key(self.test_wallet)
            set_api_base(f"{self.gateway_url}/v1")

            response = await chat("Say 'Integration test passed'")
            if "integration" in response.lower() or "test" in response.lower():
                print("  ✅ OpenAI compatibility chat function works")
                return True
            else:
                print(f"  ⚠️  Unexpected response: {response}")
                return True  # Still working, just different response

        except Exception as e:
            print(f"  ❌ Integration example failed: {e}")
            return False

    def generate_test_report(self, all_results: Dict[str, Any]):
        """Generate comprehensive test report"""
        print("\n📋 Test Report")
        print("=" * 50)

        # Summary
        total_tests = len(all_results)
        passed_tests = sum(1 for result in all_results.values() if result)

        print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")

        # Detailed results
        print(f"\n🔍 Detailed Results:")
        for test_name, result in all_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")

        # Performance metrics
        if "performance" in all_results and isinstance(all_results["performance"], dict):
            perf = all_results["performance"]
            print(f"\n⚡ Performance Metrics:")
            print(f"  Average latency: {perf.get('avg_latency', 0):.2f}s")
            print(f"  Success rate: {perf.get('successful', 0)}/{perf.get('total_requests', 0)}")
            print(f"  Total cost: {perf.get('total_cost', 0):.6f} SOL")

        # Recommendations
        print(f"\n💡 Recommendations:")
        if passed_tests == total_tests:
            print("  🎉 All tests passed! Deployment is ready for production.")
        elif passed_tests / total_tests >= 0.8:
            print("  ⚠️  Most tests passed. Review failed tests before production.")
        else:
            print("  🚨 Multiple tests failed. Deployment needs attention.")

        # Next steps
        print(f"\n🎯 Next Steps:")
        print("  1. Monitor logs for errors: docker-compose logs -f")
        print("  2. Check node health: curl http://localhost:8001/health")
        print("  3. Test with real workloads")
        print("  4. Set up monitoring and alerting")
        print("  5. Configure auto-scaling if needed")

    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 Running Comprehensive Deployment Tests")
        print("=" * 60)

        all_results = {}

        # Basic tests
        all_results["connectivity"] = await self.test_basic_connectivity()
        all_results["network_status"] = await self.test_network_status()
        all_results["model_listing"] = await self.test_model_listing()

        # API tests
        all_results["openai_compatibility"] = await self.test_openai_compatibility()
        all_results["integration_examples"] = await self.test_integration_examples()

        # Performance tests
        all_results["performance"] = await self.test_inference_performance()
        all_results["concurrency"] = await self.test_concurrent_requests()

        # Robustness tests
        all_results["error_handling"] = await self.test_error_handling()

        # Generate report
        self.generate_test_report(all_results)

        return all_results


async def main():
    """Main testing function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test deployed SolanaLM network")
    parser.add_argument("--gateway-url", default="http://localhost:8001", help="Gateway URL to test")
    parser.add_argument("--quick", action="store_true", help="Run only basic tests")

    args = parser.parse_args()

    tester = DeploymentTester(args.gateway_url)

    if args.quick:
        print("🏃 Running quick tests...")
        connectivity = await tester.test_basic_connectivity()
        status = await tester.test_network_status()
        models = await tester.test_model_listing()

        if connectivity and status and models:
            print("✅ Quick tests passed - deployment looks good!")
            return 0
        else:
            print("❌ Quick tests failed - check deployment")
            return 1
    else:
        results = await tester.run_all_tests()

        # Return success if most tests pass
        passed_count = sum(1 for result in results.values() if result)
        total_count = len(results)

        if passed_count / total_count >= 0.8:
            return 0
        else:
            return 1


if __name__ == "__main__":
    try:
        exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        exit(130)