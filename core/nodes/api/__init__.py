"""
Node API Layer for SolanaLM

Provides unified REST and WebSocket APIs for node dashboards.
Both TUI and web frontends consume this API.
"""

from .router import NodeAPIRouter

__all__ = ["NodeAPIRouter"]
