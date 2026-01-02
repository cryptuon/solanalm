"""
Main dashboard screen
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, Header, Footer

from ..widgets import StatsPanel, HardwareGauges, ActivityFeed


class NodeStatusBar(Static):
    """Node status indicator bar"""

    DEFAULT_CSS = """
    NodeStatusBar {
        dock: top;
        height: 3;
        padding: 1;
        background: $surface;
        border-bottom: solid $primary;
    }

    NodeStatusBar .status-online {
        color: $success;
    }

    NodeStatusBar .status-offline {
        color: $error;
    }

    NodeStatusBar .node-id {
        text-style: bold;
    }
    """

    def __init__(self, node_id: str = "unknown", status: str = "connecting", **kwargs):
        super().__init__(**kwargs)
        self.node_id = node_id
        self.status = status

    def compose(self) -> ComposeResult:
        status_class = "status-online" if self.status == "healthy" else "status-offline"
        yield Static(
            f"Node: [{self.node_id}]  Status: [{status_class}]{self.status.upper()}[/]  "
            f"Type: Inference  Model: Loading..."
        )

    def update_status(self, node_id: str, status: str, node_type: str, model: str) -> None:
        """Update the status bar"""
        self.node_id = node_id
        self.status = status
        status_class = "status-online" if status == "healthy" else "status-offline"
        self.update(
            f"Node: {node_id[:12]}  Status: [{status_class}]{status.upper()}[/]  "
            f"Type: {node_type}  Model: {model}"
        )


class GatewayStatus(Static):
    """Gateway connection status widget"""

    DEFAULT_CSS = """
    GatewayStatus {
        height: auto;
        padding: 1;
        border: solid $primary;
    }

    GatewayStatus .section-title {
        text-style: bold;
        padding: 0 0 1 0;
    }

    GatewayStatus .connected {
        color: $success;
    }

    GatewayStatus .disconnected {
        color: $error;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._connected = False
        self._gateway_url = ""
        self._last_ping = ""

    def compose(self) -> ComposeResult:
        yield Static("Gateway Connection", classes="section-title")
        yield Static("Status: Connecting...", id="gateway-status")
        yield Static("URL: -", id="gateway-url")

    def update_gateway(self, connected: bool, gateway_url: str = "") -> None:
        """Update gateway status"""
        self._connected = connected
        self._gateway_url = gateway_url

        try:
            status = self.query_one("#gateway-status", Static)
            url = self.query_one("#gateway-url", Static)

            if connected:
                status.update("[connected]Connected[/]")
            else:
                status.update("[disconnected]Disconnected[/]")

            url.update(f"URL: {gateway_url or '-'}")
        except Exception:
            pass


class ModelInfo(Static):
    """Model information widget"""

    DEFAULT_CSS = """
    ModelInfo {
        height: auto;
        padding: 1;
        border: solid $primary;
    }

    ModelInfo .section-title {
        text-style: bold;
        padding: 0 0 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Model Information", classes="section-title")
        yield Static("Model: Loading...", id="model-name")
        yield Static("Device: -", id="model-device")
        yield Static("Status: -", id="model-status")

    def update_model(self, model: str, device: str, ready: bool) -> None:
        """Update model info"""
        try:
            self.query_one("#model-name", Static).update(f"Model: {model}")
            self.query_one("#model-device", Static).update(f"Device: {device}")
            status = "Ready" if ready else "Loading"
            self.query_one("#model-status", Static).update(f"Status: {status}")
        except Exception:
            pass


class DashboardScreen(Screen):
    """Main dashboard screen with node overview"""

    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }

    DashboardScreen > Container {
        height: auto;
    }

    #left-column {
        column-span: 1;
    }

    #right-column {
        column-span: 1;
    }

    #activity-section {
        column-span: 2;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("p", "toggle_pause", "Pause/Resume"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield NodeStatusBar(id="status-bar")

        with Container(id="left-column"):
            yield StatsPanel(id="stats-panel")
            yield GatewayStatus(id="gateway-status")

        with Container(id="right-column"):
            yield HardwareGauges(id="hardware-gauges")
            yield ModelInfo(id="model-info")

        with Container(id="activity-section"):
            yield ActivityFeed(id="activity-feed")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize data fetching when screen mounts"""
        # Start periodic updates
        self.set_interval(2.0, self.refresh_hardware)
        self.set_interval(5.0, self.refresh_stats)
        self.set_interval(10.0, self.refresh_events)

        # Initial load
        await self.refresh_all()

    async def refresh_all(self) -> None:
        """Refresh all data"""
        await self.refresh_info()
        await self.refresh_stats()
        await self.refresh_hardware()
        await self.refresh_events()

    async def refresh_info(self) -> None:
        """Refresh node info"""
        try:
            client = self.app.api_client
            info = await client.get_info()
            health = await client.get_health()

            # Update status bar
            status_bar = self.query_one("#status-bar", NodeStatusBar)
            status_bar.update_status(
                node_id=info.node_id,
                status=health.status,
                node_type=info.node_type,
                model=health.model,
            )

            # Update model info
            model_info = self.query_one("#model-info", ModelInfo)
            model_info.update_model(
                model=health.model,
                device=health.device,
                ready=health.is_ready,
            )

            # Update gateway status
            gateway_status = self.query_one("#gateway-status", GatewayStatus)
            gateway_status.update_gateway(
                connected=health.gateway_connected,
                gateway_url=info.gateway_url or "",
            )
        except Exception:
            pass

    async def refresh_stats(self) -> None:
        """Refresh statistics"""
        try:
            client = self.app.api_client
            stats = await client.get_stats()

            stats_panel = self.query_one("#stats-panel", StatsPanel)
            stats_panel.update_from_stats(stats)
        except Exception:
            pass

    async def refresh_hardware(self) -> None:
        """Refresh hardware metrics"""
        try:
            client = self.app.api_client
            hardware = await client.get_hardware()

            gauges = self.query_one("#hardware-gauges", HardwareGauges)
            gauges.update_from_hardware(hardware)
        except Exception:
            pass

    async def refresh_events(self) -> None:
        """Refresh activity feed"""
        try:
            client = self.app.api_client
            events = await client.get_events(limit=20)

            feed = self.query_one("#activity-feed", ActivityFeed)
            feed.update_from_events(events)
        except Exception:
            pass

    async def action_refresh(self) -> None:
        """Manual refresh"""
        await self.refresh_all()

    async def action_toggle_pause(self) -> None:
        """Toggle node pause state"""
        try:
            client = self.app.api_client
            health = await client.get_health()

            if health.is_paused:
                await client.resume_node()
            else:
                await client.pause_node()

            await self.refresh_info()
        except Exception:
            pass
