"""
Statistics panel widget
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Static, Label


class StatCard(Static):
    """Individual statistic card"""

    DEFAULT_CSS = """
    StatCard {
        width: 1fr;
        height: 5;
        border: solid $primary;
        padding: 0 1;
    }

    StatCard .label {
        color: $text-muted;
    }

    StatCard .value {
        color: $text;
        text-style: bold;
    }

    StatCard .trend {
        color: $success;
    }

    StatCard .trend.negative {
        color: $error;
    }
    """

    def __init__(
        self,
        label: str,
        value: str = "0",
        trend: str = "",
        **kwargs
    ):
        super().__init__(**kwargs)
        self._label = label
        self._value = value
        self._trend = trend

    def compose(self) -> ComposeResult:
        yield Static(self._label, classes="label")
        yield Static(self._value, classes="value", id="value")
        if self._trend:
            yield Static(self._trend, classes="trend")

    def update_value(self, value: str, trend: str = "") -> None:
        """Update the displayed value"""
        value_widget = self.query_one("#value", Static)
        value_widget.update(value)


class StatsPanel(Container):
    """Panel showing node statistics"""

    DEFAULT_CSS = """
    StatsPanel {
        height: auto;
        padding: 1;
    }

    StatsPanel > Horizontal {
        height: auto;
    }

    StatsPanel .section-title {
        text-style: bold;
        padding: 0 0 1 0;
        color: $text;
    }
    """

    # Reactive attributes
    requests_served = reactive(0)
    tokens_generated = reactive(0)
    success_rate = reactive(1.0)
    avg_latency = reactive(0.0)
    uptime = reactive(0.0)
    errors = reactive(0)

    def compose(self) -> ComposeResult:
        yield Static("Node Statistics", classes="section-title")
        with Horizontal():
            yield StatCard("Requests", id="stat-requests")
            yield StatCard("Tokens", id="stat-tokens")
            yield StatCard("Success Rate", id="stat-success")
        with Horizontal():
            yield StatCard("Avg Latency", id="stat-latency")
            yield StatCard("Uptime", id="stat-uptime")
            yield StatCard("Errors", id="stat-errors")

    def watch_requests_served(self, value: int) -> None:
        try:
            card = self.query_one("#stat-requests", StatCard)
            card.update_value(f"{value:,}")
        except Exception:
            pass

    def watch_tokens_generated(self, value: int) -> None:
        try:
            card = self.query_one("#stat-tokens", StatCard)
            card.update_value(f"{value:,}")
        except Exception:
            pass

    def watch_success_rate(self, value: float) -> None:
        try:
            card = self.query_one("#stat-success", StatCard)
            card.update_value(f"{value * 100:.1f}%")
        except Exception:
            pass

    def watch_avg_latency(self, value: float) -> None:
        try:
            card = self.query_one("#stat-latency", StatCard)
            card.update_value(f"{value:.2f}s")
        except Exception:
            pass

    def watch_uptime(self, value: float) -> None:
        try:
            card = self.query_one("#stat-uptime", StatCard)
            # Format uptime
            hours = int(value // 3600)
            minutes = int((value % 3600) // 60)
            if hours > 24:
                days = hours // 24
                hours = hours % 24
                card.update_value(f"{days}d {hours}h")
            else:
                card.update_value(f"{hours}h {minutes}m")
        except Exception:
            pass

    def watch_errors(self, value: int) -> None:
        try:
            card = self.query_one("#stat-errors", StatCard)
            card.update_value(str(value))
        except Exception:
            pass

    def update_from_stats(self, stats) -> None:
        """Update from NodeStats object"""
        self.requests_served = stats.requests_served
        self.tokens_generated = stats.total_tokens_generated
        self.success_rate = stats.success_rate
        self.avg_latency = stats.average_response_time
        self.uptime = stats.uptime_seconds
        self.errors = stats.requests_failed
