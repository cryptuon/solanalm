"""
LangChain Integration Example

Shows how to use SolanaLM with LangChain for advanced AI applications.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
import sys
sys.path.append('..')

# Mock LangChain imports (replace with actual imports when LangChain is installed)
try:
    from langchain.llms.base import LLM
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.schema import LLMResult, Generation
    LANGCHAIN_AVAILABLE = True
except ImportError:
    print("LangChain not installed. Install with: pip install langchain")
    LANGCHAIN_AVAILABLE = False

    # Mock base classes for demonstration
    class LLM:
        def _call(self, *args, **kwargs): pass
        def _llm_type(self): return "mock"

    class CallbackManagerForLLMRun: pass
    class LLMResult: pass
    class Generation: pass

from client.python.solanalm_client import SolanaLMClient


class SolanaLMLangChain(LLM):
    """
    Custom LangChain LLM that uses SolanaLM network.

    Usage:
        llm = SolanaLMLangChain(
            gateway_url="http://localhost:8001",
            wallet_address="your-wallet-address",
            model="gpt-3.5-turbo"
        )

        response = llm("What is the capital of France?")
    """

    gateway_url: str = "http://localhost:8001"
    wallet_address: str = "anonymous_wallet"
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 100
    temperature: float = 0.7

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def _llm_type(self) -> str:
        return "solanalm"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the SolanaLM API synchronously"""
        return asyncio.run(self._acall(prompt, stop, run_manager, **kwargs))

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the SolanaLM API asynchronously"""
        async with SolanaLMClient(self.gateway_url) as client:
            response = await client.inference(
                model=self.model,
                prompt=prompt,
                wallet_address=self.wallet_address,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature)
            )
            return response.response


async def langchain_example():
    """Example of using SolanaLM with LangChain"""
    print("🦜 LangChain + SolanaLM Integration Example")
    print("=" * 50)

    if not LANGCHAIN_AVAILABLE:
        print("⚠️  LangChain not available, showing mock example")

    # Initialize SolanaLM LangChain wrapper
    llm = SolanaLMLangChain(
        gateway_url="http://localhost:8001",
        wallet_address="demo-langchain-wallet",
        model="gpt-3.5-turbo",
        max_tokens=150,
        temperature=0.7
    )

    print(f"🤖 Using model: {llm.model}")
    print(f"💰 Wallet: {llm.wallet_address}")

    # Example queries
    queries = [
        "What are the benefits of decentralized AI?",
        "Explain blockchain in simple terms.",
        "How does federated learning work?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        try:
            # This would work if gateway is running
            response = llm(query)
            print(f"   Response: {response[:100]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print("   (Expected if gateway is not running)")

    print("\n✨ Benefits of SolanaLM + LangChain:")
    print("- Same familiar LangChain interface")
    print("- Decentralized model serving")
    print("- Cost-effective SOL payments")
    print("- Access to multiple model types")
    print("- Support for both local and proxy models")


# Advanced LangChain integration examples
class SolanaLMChain:
    """
    Custom chain that combines multiple SolanaLM calls
    """

    def __init__(self, gateway_url: str, wallet_address: str):
        self.gateway_url = gateway_url
        self.wallet_address = wallet_address

    async def multi_model_query(self, query: str) -> Dict[str, str]:
        """Query multiple models and compare responses"""
        async with SolanaLMClient(self.gateway_url) as client:
            # Get available models
            models = await client.list_available_models()

            results = {}
            for model in models[:3]:  # Limit to first 3 models
                try:
                    response = await client.inference(
                        model=model,
                        prompt=query,
                        wallet_address=self.wallet_address,
                        max_tokens=100
                    )
                    results[model] = response.response
                except Exception as e:
                    results[model] = f"Error: {e}"

            return results

    async def consensus_query(self, query: str, threshold: int = 2) -> str:
        """Get consensus response from multiple models"""
        responses = await self.multi_model_query(query)

        # Simple consensus: return most common response
        # In practice, you'd use more sophisticated consensus logic
        response_counts = {}
        for response in responses.values():
            if response.startswith("Error:"):
                continue
            response_counts[response] = response_counts.get(response, 0) + 1

        if response_counts:
            consensus_response = max(response_counts, key=response_counts.get)
            if response_counts[consensus_response] >= threshold:
                return consensus_response

        # Fallback to first successful response
        for response in responses.values():
            if not response.startswith("Error:"):
                return response

        return "No consensus reached"


async def advanced_langchain_example():
    """Advanced LangChain integration examples"""
    print("\n🚀 Advanced LangChain Integration")
    print("=" * 40)

    chain = SolanaLMChain(
        gateway_url="http://localhost:8001",
        wallet_address="demo-advanced-wallet"
    )

    query = "What is the future of AI?"

    try:
        # Multi-model comparison
        print(f"🔍 Multi-model query: {query}")
        results = await chain.multi_model_query(query)

        for model, response in results.items():
            print(f"  {model}: {response[:50]}...")

        # Consensus query
        print(f"\n🤝 Consensus query: {query}")
        consensus = await chain.consensus_query(query)
        print(f"  Consensus: {consensus[:100]}...")

    except Exception as e:
        print(f"❌ Advanced example failed: {e}")
        print("(Expected if gateway is not running)")


def migration_guide():
    """Show how to migrate existing LangChain code to SolanaLM"""
    print("\n📚 Migration Guide: OpenAI → SolanaLM")
    print("=" * 45)

    print("BEFORE (OpenAI):")
    print("""
from langchain.llms import OpenAI

llm = OpenAI(
    openai_api_key="sk-your-key",
    model_name="gpt-3.5-turbo",
    temperature=0.7
)

response = llm("Hello, world!")
""")

    print("AFTER (SolanaLM):")
    print("""
from examples.langchain_integration import SolanaLMLangChain

llm = SolanaLMLangChain(
    gateway_url="http://localhost:8001",
    wallet_address="your-solana-wallet",
    model="gpt-3.5-turbo",
    temperature=0.7
)

response = llm("Hello, world!")  # Same interface!
""")

    print("\n✅ Benefits:")
    print("- Same LangChain interface")
    print("- Decentralized model serving")
    print("- Transparent pricing in SOL")
    print("- Support for local + proxy models")
    print("- Federated learning participation")


async def main():
    """Run all examples"""
    await langchain_example()
    await advanced_langchain_example()
    migration_guide()

    print("\n🎯 Next Steps:")
    print("1. Start SolanaLM gateway: python scripts/run_gateway.py")
    print("2. Start some nodes: python scripts/run_node.py --type inference")
    print("3. Install LangChain: pip install langchain")
    print("4. Run this example with a live gateway")


if __name__ == "__main__":
    asyncio.run(main())