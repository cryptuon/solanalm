"""
Earnings screen for tracking revenue
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Static, Header, Footer, DataTable


class EarningsSummary(Container):
    """Earnings summary widget"""

    DEFAULT_CSS = """
    EarningsSummary {
        height: auto;
        padding: 1;
        border: solid $primary;
    }

    EarningsSummary .section-title {
        text-style: bold;
        padding: 0 0 1 0;
    }

    EarningsSummary .total {
        color: $success;
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Earnings Summary", classes="section-title")
        with Horizontal():
            with Container():
                yield Static("Total Earned:", id="total-label")
                yield Static("0.0000 SOL", id="total-earned", classes="total")
            with Container():
                yield Static("Pending:", id="pending-label")
                yield Static("0.0000 SOL", id="pending-earned")

        yield Static("", id="period-earnings")
        yield Static("", id="breakdown")

    def update_earnings(self, data: dict) -> None:
        """Update earnings display"""
        try:
            total = data.get("total_earned", 0)
            pending = data.get("pending", 0)
            today = data.get("today", 0)
            week = data.get("this_week", 0)
            month = data.get("this_month", 0)
            breakdown = data.get("breakdown", {})

            self.query_one("#total-earned", Static).update(f"{total:.4f} SOL")
            self.query_one("#pending-earned", Static).update(f"{pending:.4f} SOL")

            period_text = f"Today: {today:.4f}  Week: {week:.4f}  Month: {month:.4f}"
            self.query_one("#period-earnings", Static).update(period_text)

            inference = breakdown.get("inference", 0)
            training = breakdown.get("training", 0)
            breakdown_text = f"Inference: {inference:.4f} SOL  Training: {training:.4f} SOL"
            self.query_one("#breakdown", Static).update(breakdown_text)
        except Exception:
            pass


class EarningsScreen(Screen):
    """Screen for tracking earnings and transactions"""

    DEFAULT_CSS = """
    EarningsScreen {
        layout: vertical;
        padding: 1;
    }

    #earnings-top {
        height: auto;
    }

    #transactions {
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

        with Container(id="earnings-top"):
            yield EarningsSummary(id="earnings-summary")

        with Container(id="transactions"):
            yield Static("Recent Transactions", classes="section-title")
            yield DataTable(id="transactions-table")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the screen"""
        # Setup transactions table
        table = self.query_one("#transactions-table", DataTable)
        table.add_columns("Time", "Type", "Amount", "Status")

        await self.refresh_earnings()
        self.set_interval(10.0, self.refresh_earnings)

    async def refresh_earnings(self) -> None:
        """Refresh earnings data"""
        try:
            client = self.app.api_client
            summary = await client.get_earnings_summary()

            # Update summary
            earnings_summary = self.query_one("#earnings-summary", EarningsSummary)
            earnings_summary.update_earnings(summary)

            # Get transaction history
            stats = await client.get_stats()

            # Note: In a full implementation, we'd fetch transaction history
            # from the API. For now, we just show the summary.

        except Exception:
            pass

    async def action_refresh(self) -> None:
        """Manual refresh"""
        await self.refresh_earnings()
