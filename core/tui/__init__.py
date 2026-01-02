"""
SolanaLM Terminal User Interface (TUI)

A Textual-based terminal dashboard for monitoring and controlling
SolanaLM nodes.

Usage:
    python -m core.tui --node-url http://localhost:8100
"""

from .app import SolanaLMTUI

__all__ = ["SolanaLMTUI"]
