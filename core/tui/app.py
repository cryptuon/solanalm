"""
SolanaLM TUI Application

Main Textual application for monitoring SolanaLM nodes.
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane

from .api import NodeAPIClient
from .screens import DashboardScreen, LogsScreen, TrainingScreen, EarningsScreen


class SolanaLMTUI(App):
    """Main TUI application for SolanaLM node monitoring"""

    TITLE = "SolanaLM Node Monitor"
    SUB_TITLE = "Terminal Dashboard"

    CSS = """
    Screen {
        background: $surface;
    }

    TabbedContent {
        height: 1fr;
    }

    TabPane {
        padding: 1;
    }

    .section-title {
        text-style: bold;
        padding: 0 0 1 0;
        color: $text;
    }

    Header {
        dock: top;
    }

    Footer {
        dock: bottom;
    }

    /* Status colors */
    .status-online {
        color: $success;
    }

    .status-offline {
        color: $error;
    }

    .status-busy {
        color: $warning;
    }

    /* Severity colors */
    .info {
        color: $text;
    }

    .warning {
        color: $warning;
    }

    .error {
        color: $error;
    }

    /* Connected/Disconnected */
    .connected {
        color: $success;
    }

    .disconnected {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("1", "switch_tab('dashboard')", "Dashboard", show=True),
        Binding("2", "switch_tab('logs')", "Logs", show=True),
        Binding("3", "switch_tab('training')", "Training", show=True),
        Binding("4", "switch_tab('earnings')", "Earnings", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "show_help", "Help", show=True),
        Binding("r", "refresh", "Refresh", show=False),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(
        self,
        node_url: str = "http://localhost:8100",
        theme: str = "dark",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.node_url = node_url
        self._theme = theme
        self.api_client = NodeAPIClient(node_url)

    def compose(self) -> ComposeResult:
        """Compose the application layout"""
        yield Header()

        with TabbedContent(id="tabs"):
            with TabPane("Dashboard", id="dashboard"):
                yield DashboardScreen()
            with TabPane("Logs", id="logs"):
                yield LogsScreen()
            with TabPane("Training", id="training"):
                yield TrainingScreen()
            with TabPane("Earnings", id="earnings"):
                yield EarningsScreen()

        yield Footer()

    async def on_mount(self) -> None:
        """Called when the app is mounted"""
        # Connect to node API
        await self.api_client.connect()

        # Set theme
        self.dark = self._theme == "dark"

        # Update title with node info
        try:
            info = await self.api_client.get_info()
            self.sub_title = f"Node: {info.node_id[:12]}..."
        except Exception:
            self.sub_title = f"Connecting to {self.node_url}..."

    async def on_unmount(self) -> None:
        """Called when the app is unmounted"""
        await self.api_client.disconnect()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab"""
        tabs = self.query_one("#tabs", TabbedContent)
        tabs.active = tab_id

    async def action_refresh(self) -> None:
        """Refresh the current view"""
        # Get the active tab and refresh it
        tabs = self.query_one("#tabs", TabbedContent)
        active_pane = tabs.active_pane

        if active_pane:
            # Find the screen in the pane and refresh it
            for child in active_pane.children:
                if hasattr(child, 'refresh_all'):
                    await child.refresh_all()
                elif hasattr(child, 'refresh_logs'):
                    await child.refresh_logs()
                elif hasattr(child, 'refresh_training'):
                    await child.refresh_training()
                elif hasattr(child, 'refresh_earnings'):
                    await child.refresh_earnings()

    def action_show_help(self) -> None:
        """Show help information"""
        self.notify(
            "Keyboard Shortcuts:\n"
            "1-4: Switch tabs\n"
            "r: Refresh\n"
            "q: Quit\n"
            "?: Help",
            title="Help",
            timeout=5,
        )

    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()
