"""
Drop-in Replacement Examples

Shows how SolanaLM can replace existing LLM services with minimal code changes.
"""

import asyncio
import sys
sys.path.append('..')

print("🔄 Drop-in Replacement Examples")
print("=" * 50)


def openai_replacement_example():
    """Show how to replace OpenAI API calls"""
    print("\n1. OpenAI API Replacement")
    print("-" * 30)

    print("BEFORE (OpenAI):")
    print("""
import openai

openai.api_key = "sk-your-openai-key"

# Chat completion
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response.choices[0].message.content)
""")

    print("AFTER (SolanaLM):")
    print("""
from client.python.openai_compat import openai

openai.api_key = "your-solana-wallet-address"
openai.api_base = "http://localhost:8001/v1"

# Same exact code!
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ],
    max_tokens=100,
    temperature=0.7
)

print(response.choices[0].message.content)
""")

    print("✅ Changes needed: 2 lines (import + api_base)")


def langchain_replacement_example():
    """Show LangChain integration"""
    print("\n2. LangChain Integration")
    print("-" * 30)

    print("BEFORE (OpenAI with LangChain):")
    print("""
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

llm = OpenAI(
    openai_api_key="sk-your-key",
    model_name="text-davinci-003"
)

chain = LLMChain(llm=llm, prompt=PromptTemplate(...))
result = chain.run("input text")
""")

    print("AFTER (SolanaLM with LangChain):")
    print("""
from examples.langchain_integration import SolanaLMLangChain
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

llm = SolanaLMLangChain(
    gateway_url="http://localhost:8001",
    wallet_address="your-wallet",
    model="gpt-3.5-turbo"
)

chain = LLMChain(llm=llm, prompt=PromptTemplate(...))
result = chain.run("input text")  # Same interface!
""")

    print("✅ Changes needed: Import and constructor only")


def fastapi_integration_example():
    """Show FastAPI backend integration"""
    print("\n3. FastAPI Backend Integration")
    print("-" * 40)

    print("BEFORE (Direct OpenAI calls):")
    print("""
from fastapi import FastAPI
import openai

app = FastAPI()
openai.api_key = "sk-your-key"

@app.post("/chat")
async def chat(message: str):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message}]
    )
    return {"response": response.choices[0].message.content}
""")

    print("AFTER (SolanaLM backend):")
    print("""
from fastapi import FastAPI
from client.python.solanalm_client import SolanaLMClient

app = FastAPI()

@app.post("/chat")
async def chat(message: str):
    async with SolanaLMClient("http://localhost:8001") as client:
        response = await client.inference(
            model="gpt-3.5-turbo",
            prompt=message,
            wallet_address="your-wallet"
        )
        return {"response": response.response}
""")

    print("✅ Benefits: Decentralized, cheaper, transparent pricing")


def jupyter_notebook_example():
    """Show Jupyter notebook usage"""
    print("\n4. Jupyter Notebook Usage")
    print("-" * 30)

    print("Standard OpenAI in Jupyter:")
    print("""
# Cell 1
import openai
openai.api_key = "sk-your-key"

# Cell 2
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.choices[0].message.content)
""")

    print("SolanaLM in Jupyter:")
    print("""
# Cell 1
from client.python.openai_compat import openai
openai.api_key = "your-solana-wallet"
openai.api_base = "http://localhost:8001/v1"

# Cell 2 - Same exact code!
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)
print(response.choices[0].message.content)
print(f"Cost: {response.usage.total_tokens * 0.0001} SOL")
""")

    print("✅ Extra benefit: See actual costs in SOL")


async def live_comparison_example():
    """Show live comparison if gateway is running"""
    print("\n5. Live Comparison (if gateway is running)")
    print("-" * 50)

    try:
        from client.python.openai_compat import openai

        openai.api_key = "demo-wallet-123"
        openai.api_base = "http://localhost:8001/v1"

        print("Testing SolanaLM connection...")

        # Test model listing
        models = await openai.Model.alist()
        print(f"✅ Available models: {len(models['data'])}")

        # Test simple completion
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello in 5 words"}],
            max_tokens=20
        )

        print(f"✅ Response: {response.choices[0]['message']['content']}")
        print(f"✅ Tokens: {response.usage['total_tokens']}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("(Expected if gateway is not running)")
        print("\nTo test live:")
        print("1. python scripts/run_gateway.py")
        print("2. python scripts/run_node.py --type inference --node-id test1 --wallet TestWallet123")
        print("3. python examples/drop_in_replacement.py")


def migration_checklist():
    """Provide migration checklist"""
    print("\n📋 Migration Checklist")
    print("-" * 25)

    checklist_items = [
        "Install SolanaLM client: pip install solanalm (when published)",
        "Get a Solana wallet address for payments",
        "Update imports to use SolanaLM client",
        "Change API base URL to your SolanaLM gateway",
        "Test with small requests first",
        "Monitor costs in SOL vs USD",
        "Update error handling if needed",
        "Consider privacy implications for your data",
        "Set up your own nodes for better control (optional)",
        "Contribute to federated learning (optional)"
    ]

    for i, item in enumerate(checklist_items, 1):
        print(f"{i:2d}. [ ] {item}")

    print(f"\n✨ Total effort: ~30 minutes for most applications")


def cost_comparison():
    """Compare costs between providers"""
    print("\n💰 Cost Comparison")
    print("-" * 20)

    print("OpenAI GPT-3.5 Turbo:")
    print("  Input:  $0.0015 / 1K tokens")
    print("  Output: $0.002  / 1K tokens")
    print("  ~$2.00 / 1M tokens average")

    print("\nSolanaLM Network:")
    print("  Inference: ~0.001 SOL / request")
    print("  Per token: ~0.0001 SOL / token")
    print("  ~$1.00 / 1M tokens average (at $50/SOL)")

    print("\nPotential Savings: ~50% cheaper")
    print("Plus benefits:")
    print("  ✅ No vendor lock-in")
    print("  ✅ Transparent pricing")
    print("  ✅ Support decentralized AI")
    print("  ✅ Contribute to model improvement")


async def main():
    """Run all examples"""
    openai_replacement_example()
    langchain_replacement_example()
    fastapi_integration_example()
    jupyter_notebook_example()
    await live_comparison_example()
    migration_checklist()
    cost_comparison()

    print("\n🎯 Key Takeaways")
    print("=" * 20)
    print("1. Drop-in replacement for OpenAI API")
    print("2. Works with existing frameworks (LangChain, etc.)")
    print("3. Minimal code changes required")
    print("4. Significant cost savings potential")
    print("5. Supports decentralized AI ecosystem")

    print("\n🚀 Get Started:")
    print("1. Start gateway: python scripts/run_gateway.py")
    print("2. Start node: python scripts/run_node.py --type inference")
    print("3. Update your code with examples above")
    print("4. Save money and support decentralized AI! 🌟")


if __name__ == "__main__":
    asyncio.run(main())