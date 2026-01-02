"""
Training screen for federated learning nodes
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static, Header, Footer, ProgressBar, DataTable


class TrainingProgress(Container):
    """Current training round progress"""

    DEFAULT_CSS = """
    TrainingProgress {
        height: auto;
        padding: 1;
        border: solid $primary;
    }

    TrainingProgress .section-title {
        text-style: bold;
        padding: 0 0 1 0;
    }

    TrainingProgress ProgressBar {
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Current Training Round", classes="section-title")
        yield Static("Status: No active round", id="training-status")
        yield Static("Round: -", id="round-id")
        yield Static("Model: -", id="training-model")
        yield ProgressBar(total=100, show_eta=False, id="training-progress")
        yield Static("Progress: 0%", id="progress-text")
        yield Static("Loss: -", id="training-loss")
        yield Static("Expected Reward: 0.0 SOL", id="expected-reward")

    def update_training(self, data: dict) -> None:
        """Update training display"""
        try:
            active = data.get("active", False)

            if not active:
                self.query_one("#training-status", Static).update("Status: No active round")
                self.query_one("#round-id", Static).update("Round: -")
                self.query_one("#training-model", Static).update("Model: -")
                self.query_one("#training-progress", ProgressBar).update(progress=0)
                self.query_one("#progress-text", Static).update("Progress: 0%")
                self.query_one("#training-loss", Static).update("Loss: -")
                self.query_one("#expected-reward", Static).update("Expected Reward: 0.0 SOL")
                return

            round_data = data.get("round", {})
            status = round_data.get("status", "unknown")
            round_id = round_data.get("round_id", "-")
            model = round_data.get("model", "-")
            progress = round_data.get("progress", 0) * 100
            loss = round_data.get("current_loss")
            reward = round_data.get("expected_reward", 0)

            self.query_one("#training-status", Static).update(f"Status: {status.upper()}")
            self.query_one("#round-id", Static).update(f"Round: {round_id[:12] if round_id else '-'}...")
            self.query_one("#training-model", Static).update(f"Model: {model}")
            self.query_one("#training-progress", ProgressBar).update(progress=progress)
            self.query_one("#progress-text", Static).update(f"Progress: {progress:.1f}%")
            self.query_one("#training-loss", Static).update(f"Loss: {loss:.4f}" if loss else "Loss: -")
            self.query_one("#expected-reward", Static).update(f"Expected Reward: {reward:.4f} SOL")
        except Exception:
            pass


class TrainingScreen(Screen):
    """Screen for monitoring federated learning"""

    DEFAULT_CSS = """
    TrainingScreen {
        layout: vertical;
        padding: 1;
    }

    #training-top {
        height: auto;
    }

    #training-history {
        height: 1fr;
        padding: 1;
        border: solid $primary;
    }

    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="training-top"):
            yield TrainingProgress(id="training-progress")

        with Container(id="training-history"):
            yield Static("Training History", classes="section-title")
            yield DataTable(id="history-table")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the screen"""
        # Setup history table
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Round", "Status", "Loss", "Reward", "Duration")

        await self.refresh_training()
        self.set_interval(5.0, self.refresh_training)

    async def refresh_training(self) -> None:
        """Refresh training data"""
        try:
            client = self.app.api_client
            training_data = await client.get_training_current()

            # Update progress
            progress = self.query_one("#training-progress", TrainingProgress)
            progress.update_training(training_data)

        except Exception:
            # Not a training node or error
            progress = self.query_one("#training-progress", TrainingProgress)
            progress.update_training({"active": False})

    async def action_refresh(self) -> None:
        """Manual refresh"""
        await self.refresh_training()
