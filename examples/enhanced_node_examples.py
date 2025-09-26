#!/usr/bin/env python3
"""
Enhanced Node Examples
Shows how to run different types of inference nodes with various backends
"""

import asyncio
import os

# Example usage scripts for different node types

EXAMPLES = {
    "transformers_node": {
        "description": "Run local Transformers model (DialoGPT)",
        "command": "poetry run python scripts/run_enhanced_node.py --backend transformers --node-id my-transformers-node --wallet MyWallet123 --model microsoft/DialoGPT-small --port 8100"
    },

    "llama_cpp_node": {
        "description": "Run llama.cpp quantized model (requires GGUF file)",
        "command": "poetry run python scripts/run_enhanced_node.py --backend llama_cpp --node-id my-llama-node --wallet MyWallet123 --model-path ./models/llama-7b.gguf --port 8101",
        "note": "Requires downloading a GGUF model file first"
    },

    "openai_proxy": {
        "description": "Proxy to OpenAI API (requires API key)",
        "command": "poetry run python scripts/run_enhanced_node.py --backend openai --node-id my-openai-proxy --wallet MyWallet123 --api-key YOUR_OPENAI_KEY --model gpt-3.5-turbo --port 8102",
        "env": "export OPENAI_API_KEY=your-key-here"
    },

    "anthropic_proxy": {
        "description": "Proxy to Anthropic Claude API (requires API key)",
        "command": "poetry run python scripts/run_enhanced_node.py --backend anthropic --node-id my-claude-proxy --wallet MyWallet123 --api-key YOUR_ANTHROPIC_KEY --model claude-3-sonnet --port 8103",
        "env": "export ANTHROPIC_API_KEY=your-key-here"
    },

    "ollama_proxy": {
        "description": "Proxy to local Ollama server (requires Ollama running)",
        "command": "poetry run python scripts/run_enhanced_node.py --backend ollama --node-id my-ollama-node --wallet MyWallet123 --model llama2 --api-url http://localhost:11434 --port 8104",
        "requirements": ["Install Ollama", "Run: ollama pull llama2"]
    },

    "custom_api": {
        "description": "Proxy to any custom API endpoint",
        "command": "poetry run python scripts/run_enhanced_node.py --backend custom --node-id my-custom-node --wallet MyWallet123 --api-url http://your-api.com/generate --api-key optional-key --port 8105"
    }
}

def show_examples():
    """Display all available node examples"""
    print("🚀 SolanaLM Enhanced Node Examples")
    print("=" * 50)

    for name, config in EXAMPLES.items():
        print(f"\n🔧 {name.upper().replace('_', ' ')}")
        print(f"   📝 {config['description']}")

        if 'env' in config:
            print(f"   🔑 Environment: {config['env']}")

        if 'requirements' in config:
            print("   📋 Requirements:")
            for req in config['requirements']:
                print(f"      - {req}")

        if 'note' in config:
            print(f"   💡 Note: {config['note']}")

        print(f"   ▶️  Command:")
        print(f"      {config['command']}")

def show_federated_learning_example():
    """Show federated learning example"""
    print("\n🤖 FEDERATED LEARNING EXAMPLE")
    print("=" * 50)

    print("1. Quick Demo:")
    print("   poetry run python core/training/federated_learning.py")

    print("\n2. Comprehensive Demo:")
    print("   poetry run python examples/comprehensive_demo.py")

    print("\n3. Training Node (participates in FL rounds):")
    print("   poetry run python scripts/run_node.py --type training --node-id fl-node-1 --wallet TrainingWallet123 --port 8200")

def show_quick_start():
    """Show quick start commands"""
    print("\n⚡ QUICK START")
    print("=" * 50)

    print("1. Install dependencies:")
    print("   poetry install && poetry shell")

    print("\n2. Start gateway:")
    print("   poetry run python scripts/run_gateway.py")

    print("\n3. Start a simple inference node:")
    print("   poetry run python scripts/run_enhanced_node.py --backend transformers --node-id node1 --wallet Wallet123")

    print("\n4. Test with client:")
    print("   poetry run python examples/basic_usage.py --mode client")

    print("\n5. Run comprehensive demo:")
    print("   poetry run python examples/comprehensive_demo.py")

if __name__ == "__main__":
    print("📚 SOLANALM ENHANCED NODES & FEDERATED LEARNING GUIDE")
    print("=" * 70)

    show_quick_start()
    show_examples()
    show_federated_learning_example()

    print("\n💡 KEY FEATURES")
    print("=" * 50)
    print("✅ Multiple inference backends (Transformers, llama.cpp, OpenAI, Ollama)")
    print("✅ Working federated learning with PyTorch")
    print("✅ API proxy support for external services")
    print("✅ Hybrid nodes (inference + training)")
    print("✅ Solana blockchain integration")
    print("✅ Privacy features (onion routing)")
    print("✅ OpenAI-compatible API layer")

    print("\n🔗 COMPATIBILITY")
    print("=" * 50)
    print("✅ Minimal code changes to existing architecture")
    print("✅ Drop-in replacement for OpenAI SDK")
    print("✅ Works with existing Solana wallet infrastructure")
    print("✅ Compatible with Poetry dependency management")
    print("✅ Supports both local and remote model inference")