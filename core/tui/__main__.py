"""
SolanaLM TUI Entry Point

Usage:
    python -m core.tui [OPTIONS]

Options:
    --node-url URL      Node API URL (default: http://localhost:8100)
    --theme THEME       Color theme (dark/light)
    --no-mouse          Disable mouse support for SSH
"""

import argparse
import sys

from .app import SolanaLMTUI


def main():
    parser = argparse.ArgumentParser(
        description="SolanaLM Node Monitor TUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m core.tui --node-url http://localhost:8100
    python -m core.tui --theme light
    python -m core.tui --no-mouse  # For SSH sessions
        """
    )
    parser.add_argument(
        "--node-url",
        default="http://localhost:8100",
        help="Node API URL (default: http://localhost:8100)"
    )
    parser.add_argument(
        "--theme",
        choices=["dark", "light"],
        default="dark",
        help="Color theme (default: dark)"
    )
    parser.add_argument(
        "--no-mouse",
        action="store_true",
        help="Disable mouse support (for SSH)"
    )

    args = parser.parse_args()

    app = SolanaLMTUI(
        node_url=args.node_url,
        theme=args.theme,
    )

    # Configure for SSH/keyboard-only mode
    if args.no_mouse:
        app.ENABLE_COMMAND_PALETTE = False

    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
