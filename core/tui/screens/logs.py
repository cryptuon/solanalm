"""
Logs screen for viewing node logs
"""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static, Header, Footer, Input, Select, RichLog


class LogsScreen(Screen):
    """Screen for viewing and filtering logs"""

    DEFAULT_CSS = """
    LogsScreen {
        layout: vertical;
    }

    #log-controls {
        dock: top;
        height: 3;
        padding: 0 1;
        background: $surface;
    }

    #log-controls Input {
        width: 30;
    }

    #log-controls Select {
        width: 15;
    }

    #log-viewer {
        height: 1fr;
        padding: 1;
    }

    RichLog {
        height: 1fr;
        border: solid $primary;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("c", "clear", "Clear"),
        ("/", "focus_search", "Search"),
        ("escape", "clear_search", "Clear Search"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_level: Optional[str] = None
        self._search_query: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="log-controls"):
            yield Input(placeholder="Search logs...", id="search-input")
            yield Select(
                [
                    ("All Levels", None),
                    ("DEBUG", "DEBUG"),
                    ("INFO", "INFO"),
                    ("WARNING", "WARNING"),
                    ("ERROR", "ERROR"),
                ],
                prompt="Level",
                id="level-select",
                value=None,
            )
            yield Static("", id="log-count")

        with Container(id="log-viewer"):
            yield RichLog(id="log-output", highlight=True, markup=True)

        yield Footer()

    async def on_mount(self) -> None:
        """Load initial logs"""
        await self.refresh_logs()
        self.set_interval(5.0, self.refresh_logs)

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        if event.input.id == "search-input":
            self._search_query = event.value if event.value else None
            await self.refresh_logs()

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle level filter changes"""
        if event.select.id == "level-select":
            self._current_level = event.value
            await self.refresh_logs()

    async def refresh_logs(self) -> None:
        """Refresh logs from API"""
        try:
            client = self.app.api_client
            logs = await client.get_logs(
                limit=200,
                level=self._current_level,
                search=self._search_query,
            )

            log_output = self.query_one("#log-output", RichLog)
            log_output.clear()

            for log in reversed(logs):  # Show oldest first
                timestamp = log.get("timestamp", "")
                if "T" in timestamp:
                    timestamp = timestamp.split("T")[1][:12]

                level = log.get("level", "INFO")
                source = log.get("source", "node")
                message = log.get("message", "")

                # Color based on level
                level_color = {
                    "DEBUG": "dim",
                    "INFO": "cyan",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold red",
                }.get(level, "white")

                log_output.write(
                    f"[dim]{timestamp}[/] [{level_color}]{level:8}[/] "
                    f"[dim]{source:15}[/] {message}"
                )

            # Update count
            count_label = self.query_one("#log-count", Static)
            count_label.update(f"{len(logs)} logs")

        except Exception as e:
            log_output = self.query_one("#log-output", RichLog)
            log_output.write(f"[red]Error loading logs: {e}[/]")

    async def action_refresh(self) -> None:
        """Manual refresh"""
        await self.refresh_logs()

    async def action_clear(self) -> None:
        """Clear log display"""
        log_output = self.query_one("#log-output", RichLog)
        log_output.clear()

    def action_focus_search(self) -> None:
        """Focus the search input"""
        self.query_one("#search-input", Input).focus()

    def action_clear_search(self) -> None:
        """Clear search and filter"""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self._search_query = None
