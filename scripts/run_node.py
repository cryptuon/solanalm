#!/usr/bin/env python3

"""
Script to run SolanaLM nodes (inference, training, proxy, hybrid)
"""

import asyncio
import logging
import sys
import os
import argparse

# Add core to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config.settings import get_node_config, get_settings
from core.nodes.inference.node import InferenceNode
from core.nodes.proxy.node import ProxyNode


def setup_logging():
    """Setup logging configuration"""
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=settings.log_format
    )


async def run_inference_node(config):
    """Run an inference node"""
    node = InferenceNode(
        node_id=config.node_id,
        wallet_address=config.wallet_address,
        gateway_url=config.gateway_url,
        model_name=config.model_name,
        host=config.node_host,
        port=config.node_port
    )

    await node.initialize()
    await node.run()


async def run_proxy_node(config):
    """Run a proxy node"""
    node = ProxyNode(
        node_id=config.node_id,
        wallet_address=config.wallet_address,
        gateway_url=config.gateway_url,
        host=config.node_host,
        port=config.node_port
    )

    await node.initialize()
    await node.run()


async def run_hybrid_node(config):
    """Run a hybrid node (inference + training)"""
    # TODO: Implement hybrid node that can switch between modes
    logging.warning("Hybrid nodes not yet implemented, falling back to inference mode")
    await run_inference_node(config)


async def run_training_node(config):
    """Run a training-only node"""
    # TODO: Implement dedicated training node
    logging.warning("Training-only nodes not yet implemented")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run SolanaLM Node")
    parser.add_argument(
        "--type",
        choices=["inference", "proxy", "training", "hybrid"],
        default="inference",
        help="Type of node to run"
    )
    parser.add_argument("--node-id", help="Node ID (overrides env var)")
    parser.add_argument("--wallet", help="Wallet address (overrides env var)")
    parser.add_argument("--port", type=int, help="Port to run on (overrides env var)")

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Load configuration
        config = get_node_config()

        # Override with command line arguments
        if args.node_id:
            config.node_id = args.node_id
        if args.wallet:
            config.wallet_address = args.wallet
        if args.port:
            config.node_port = args.port

        logger.info(f"Starting {args.type} node {config.node_id}")
        logger.info(f"Wallet: {config.wallet_address}")
        logger.info(f"Gateway: {config.gateway_url}")
        logger.info(f"Port: {config.node_port}")

        # Run the appropriate node type
        if args.type == "inference":
            await run_inference_node(config)
        elif args.type == "proxy":
            await run_proxy_node(config)
        elif args.type == "training":
            await run_training_node(config)
        elif args.type == "hybrid":
            await run_hybrid_node(config)

    except KeyboardInterrupt:
        logger.info("Node shutdown requested")
    except Exception as e:
        logger.error(f"Node failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())