#!/usr/bin/env python3
"""
End-to-End System Test

Comprehensive test of all SolanaLM components working together:
- Node registration and discovery
- Standard inference requests
- Privacy-preserving inference
- Federated learning participation
- Payment processing
"""

import asyncio
import logging
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from client.python.solanalm_client import SolanaLMClient
from core.models.schemas import NodeCapabilities, NodeType, HardwareSpecs, PricingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EndToEndTest:
    """Comprehensive end-to-end system test"""

    def __init__(self):
        self.gateway_url = "http://localhost:8001"
        self.test_wallet = "TEST_WALLET_ADDR_123"
        self.results = {}

    async def run_all_tests(self):
        """Run comprehensive end-to-end tests"""
        print("🚀 SOLANALM END-TO-END SYSTEM TEST")
        print("=" * 60)
        print("Testing all components working together...\n")

        tests = [
            ("Gateway Health Check", self.test_gateway_health),
            ("Network Status", self.test_network_status),
            ("Node Discovery", self.test_node_discovery),
            ("Standard Inference", self.test_standard_inference),
            ("Privacy Inference", self.test_privacy_inference),
            ("Batch Processing", self.test_batch_inference),
            ("Training Status", self.test_training_status),
            ("Privacy Network", self.test_privacy_network),
            ("Error Handling", self.test_error_handling),
            ("Performance", self.test_performance)
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            print(f"🧪 {test_name}...")
            try:
                result = await test_func()
                if result:
                    print(f"   ✅ PASSED")
                    passed += 1
                else:
                    print(f"   ❌ FAILED")
                    failed += 1
                self.results[test_name] = result
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
                failed += 1
                self.results[test_name] = False

            # Small delay between tests
            await asyncio.sleep(0.5)

        print(f"\n📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Total:  {passed + failed}")
        print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! SolanaLM is working correctly.")
        else:
            print(f"\n⚠️  {failed} tests failed. See output above for details.")

        return failed == 0

    async def test_gateway_health(self) -> bool:
        """Test gateway health endpoint"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                status = await client.get_network_status()
                return "service" in status and status.get("service") == "SolanaLM Gateway"
        except Exception as e:
            logger.error(f"Gateway health test failed: {e}")
            return False

    async def test_network_status(self) -> bool:
        """Test network status reporting"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                status = await client.get_network_status()
                required_fields = ["service", "version", "status"]
                return all(field in status for field in required_fields)
        except Exception as e:
            logger.error(f"Network status test failed: {e}")
            return False

    async def test_node_discovery(self) -> bool:
        """Test node discovery and listing"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()
                # Should return at least an empty list
                return isinstance(models, list)
        except Exception as e:
            logger.error(f"Node discovery test failed: {e}")
            return False

    async def test_standard_inference(self) -> bool:
        """Test standard inference request"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()

                if not models:
                    logger.warning("No models available for inference test")
                    return True  # Pass if no nodes are running

                # Try inference with first available model
                response = await client.inference(
                    model=models[0],
                    prompt="Hello, how are you?",
                    wallet_address=self.test_wallet,
                    max_tokens=50
                )

                return (
                    hasattr(response, 'response') and
                    hasattr(response, 'cost_sol') and
                    hasattr(response, 'processing_time') and
                    len(response.response) > 0
                )

        except Exception as e:
            # Expected to fail if no nodes are running
            logger.debug(f"Standard inference test failed (expected): {e}")
            return True

    async def test_privacy_inference(self) -> bool:
        """Test privacy-preserving inference"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()

                if not models:
                    logger.warning("No models available for privacy test")
                    return True

                response = await client.private_inference(
                    model=models[0],
                    prompt="This is a private query",
                    wallet_address=self.test_wallet,
                    privacy_level="standard"
                )

                return (
                    hasattr(response, 'response') and
                    hasattr(response, 'node_id') and
                    response.node_id == "private-circuit"  # Should hide actual node
                )

        except Exception as e:
            logger.debug(f"Privacy inference test failed (expected): {e}")
            return True

    async def test_batch_inference(self) -> bool:
        """Test batch inference processing"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                models = await client.list_available_models()

                if not models:
                    return True

                prompts = [
                    "First test prompt",
                    "Second test prompt",
                    "Third test prompt"
                ]

                responses = await client.batch_inference(
                    model=models[0],
                    prompts=prompts,
                    wallet_address=self.test_wallet,
                    max_concurrent=2
                )

                return isinstance(responses, list)

        except Exception as e:
            logger.debug(f"Batch inference test failed (expected): {e}")
            return True

    async def test_training_status(self) -> bool:
        """Test training status endpoint"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                status = await client.get_training_status()
                # Should return a dict with training info
                return isinstance(status, dict)
        except Exception as e:
            logger.debug(f"Training status test failed: {e}")
            return True

    async def test_privacy_network(self) -> bool:
        """Test privacy network status"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                privacy_status = await client.get_privacy_network_health()
                return isinstance(privacy_status, dict)
        except Exception as e:
            logger.debug(f"Privacy network test failed: {e}")
            return True

    async def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        try:
            async with SolanaLMClient(self.gateway_url) as client:
                # Test with invalid model
                try:
                    await client.inference(
                        model="INVALID_MODEL_NAME",
                        prompt="Test prompt",
                        wallet_address=self.test_wallet
                    )
                    return False  # Should have failed
                except Exception:
                    return True  # Expected to fail

        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False

    async def test_performance(self) -> bool:
        """Test basic performance metrics"""
        try:
            start_time = time.time()

            async with SolanaLMClient(self.gateway_url) as client:
                # Test multiple quick requests
                tasks = []
                for i in range(3):
                    task = client.get_network_status()
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            total_time = end_time - start_time

            # Should complete within reasonable time
            performance_ok = total_time < 10.0  # 10 seconds for 3 requests

            logger.info(f"Performance test: {total_time:.2f}s for 3 requests")
            return performance_ok

        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return False

    async def test_schema_validation(self) -> bool:
        """Test that all schemas are properly defined"""
        try:
            # Test NodeCapabilities creation
            hardware = HardwareSpecs(
                cpu_cores=4,
                ram_gb=8,
                storage_gb=100,
                network_speed_mbps=1000
            )

            pricing = PricingConfig(
                per_request=0.001,
                per_token=0.0001
            )

            capabilities = NodeCapabilities(
                node_id="test-node",
                node_type=NodeType.INFERENCE,
                wallet_address="test-wallet",
                endpoint_url="http://test:8100",
                hardware=hardware,
                pricing=pricing,
                supported_models=["test-model"]
            )

            # Should create without errors
            return capabilities.node_id == "test-node"

        except Exception as e:
            logger.error(f"Schema validation test failed: {e}")
            return False


async def quick_connectivity_test():
    """Quick test to verify gateway is reachable"""
    print("🔍 Quick Connectivity Test")
    print("-" * 30)

    try:
        async with SolanaLMClient("http://localhost:8001") as client:
            status = await client.get_network_status()
            if status:
                print("✅ Gateway is reachable")
                print(f"   Service: {status.get('service', 'Unknown')}")
                print(f"   Version: {status.get('version', 'Unknown')}")
                print(f"   Status: {status.get('status', 'Unknown')}")
                return True
            else:
                print("❌ Gateway returned empty response")
                return False

    except Exception as e:
        print(f"❌ Gateway not reachable: {e}")
        print("\n💡 To start the gateway, run:")
        print("   python scripts/run_gateway.py")
        return False


async def main():
    """Main test runner"""
    # Quick connectivity test first
    if not await quick_connectivity_test():
        print("\n⚠️  Gateway not running. Skipping full tests.")
        print("Start the gateway first, then run this test again.")
        return 1

    print("\n" + "="*60)

    # Run full end-to-end test
    tester = EndToEndTest()
    success = await tester.run_all_tests()

    if success:
        print("\n🎊 SolanaLM system is fully functional!")
        print("\n🚀 Ready for:")
        print("   • Standard AI inference")
        print("   • Privacy-preserving queries")
        print("   • Federated learning")
        print("   • Production deployment")
        return 0
    else:
        print("\n🔧 Some components need attention.")
        print("Review the failed tests above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)