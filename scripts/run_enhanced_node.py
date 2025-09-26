#!/usr/bin/env python3
"""
Run Enhanced SolanaLM Nodes with Multiple Backend Support
Supports: Transformers, llama.cpp, OpenAI, Ollama, Custom APIs
"""

import asyncio
import argparse
import logging
import sys
import os

# Add core to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.nodes.inference.enhanced_node import (
    EnhancedInferenceNode,
    ModelBackend,
    create_transformers_node,
    create_llama_cpp_node,
    create_openai_proxy_node,
    create_ollama_proxy_node
)

logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Run Enhanced SolanaLM Node")

    parser.add_argument("--backend",
                       choices=["transformers", "llama_cpp", "openai", "ollama", "custom"],
                       default="transformers",
                       help="Model backend to use")

    parser.add_argument("--node-id", required=True, help="Unique node identifier")
    parser.add_argument("--wallet", required=True, help="Solana wallet address")
    parser.add_argument("--gateway", default="http://localhost:8001", help="Gateway URL")
    parser.add_argument("--port", type=int, default=8100, help="Node port")

    # Backend-specific arguments
    parser.add_argument("--model", help="Model name or path")
    parser.add_argument("--model-path", help="Path to model file (for llama.cpp)")
    parser.add_argument("--api-key", help="API key (for OpenAI/Anthropic)")
    parser.add_argument("--api-url", help="API URL (for custom APIs)")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Create node based on backend
        if args.backend == "transformers":
            model = args.model or "microsoft/DialoGPT-small"
            logger.info(f"Starting Transformers node with model: {model}")

            node = await create_transformers_node(
                node_id=args.node_id,
                wallet=args.wallet,
                gateway=args.gateway,
                model=model,
                port=args.port
            )

        elif args.backend == "llama_cpp":
            if not args.model_path:
                raise ValueError("--model-path required for llama.cpp backend")

            logger.info(f"Starting llama.cpp node with model: {args.model_path}")

            node = await create_llama_cpp_node(
                node_id=args.node_id,
                wallet=args.wallet,
                gateway=args.gateway,
                model_path=args.model_path,
                port=args.port
            )

        elif args.backend == "openai":
            if not args.api_key:
                raise ValueError("--api-key required for OpenAI backend")

            model = args.model or "gpt-3.5-turbo"
            logger.info(f"Starting OpenAI proxy node with model: {model}")

            node = await create_openai_proxy_node(
                node_id=args.node_id,
                wallet=args.wallet,
                gateway=args.gateway,
                api_key=args.api_key,
                model=model,
                port=args.port
            )

        elif args.backend == "ollama":
            model = args.model or "llama2"
            api_url = args.api_url or "http://localhost:11434"
            logger.info(f"Starting Ollama proxy node: {model} at {api_url}")

            node = await create_ollama_proxy_node(
                node_id=args.node_id,
                wallet=args.wallet,
                gateway=args.gateway,
                model=model,
                ollama_url=api_url,
                port=args.port
            )

        elif args.backend == "custom":
            if not args.api_url:
                raise ValueError("--api-url required for custom backend")

            logger.info(f"Starting custom API proxy node: {args.api_url}")

            node = EnhancedInferenceNode(
                node_id=args.node_id,
                wallet_address=args.wallet,
                gateway_url=args.gateway,
                backend=ModelBackend.CUSTOM_API,
                model_name=args.model or "custom-model",
                api_url=args.api_url,
                api_key=args.api_key,
                port=args.port
            )
            await node.initialize()

        # Run the node
        logger.info(f"Node {args.node_id} ready on port {args.port}")
        await node.run()

    except KeyboardInterrupt:
        logger.info("Node shutdown requested")
    except Exception as e:
        logger.error(f"Node failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())