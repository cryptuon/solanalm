"""
Activity feed widget for recent events
"""

from datetime import datetime
from typing import List, Dict, Any

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static, Label


class ActivityItem(Static):
    """Single activity item"""

    DEFAULT_CSS = """
    ActivityItem {
        height: 1;
        padding: 0 1;
    }

    ActivityItem.info {
        color: $text;
    }

    ActivityItem.warning {
        color: $warning;
    }

    ActivityItem.error {
        color: $error;
    }

    ActivityItem .timestamp {
        color: $text-muted;
    }
    """

    def __init__(self, timestamp: str, message: str, severity: str = "info", **kwargs):
        super().__init__(**kwargs)
        self._timestamp = timestamp
        self._message = message
        self.add_class(severity)

    def compose(self) -> ComposeResult:
        yield Static(f"[{self._timestamp}] {self._message}")


class ActivityFeed(Container):
    """Feed showing recent node activity"""

    DEFAULT_CSS = """
    ActivityFeed {
        height: auto;
        max-height: 15;
        padding: 1;
        border: solid $primary;
    }

    ActivityFeed .section-title {
        text-style: bold;
        padding: 0 0 1 0;
        color: $text;
    }

    ActivityFeed VerticalScroll {
        height: auto;
        max-height: 10;
    }
    """

    activities: reactive[List[Dict[str, Any]]] = reactive([], always_update=True)

    def compose(self) -> ComposeResult:
        yield Static("Recent Activity", classes="section-title")
        yield VerticalScroll(id="activity-container")

    def watch_activities(self, activities: List[Dict[str, Any]]) -> None:
        """Update display when activities change"""
        try:
            container = self.query_one("#activity-container", VerticalScroll)
            container.remove_children()

            for activity in activities[-20:]:  # Show last 20
                timestamp = activity.get("timestamp", "")
                if isinstance(timestamp, str) and "T" in timestamp:
                    # Parse ISO format and format nicely
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        timestamp = dt.strftime("%H:%M:%S")
                    except Exception:
                        timestamp = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp

                title = activity.get("title", activity.get("message", "Event"))
                severity = activity.get("severity", "info")

                container.mount(ActivityItem(timestamp, title, severity))

        except Exception:
            pass

    def add_activity(self, activity: Dict[str, Any]) -> None:
        """Add a new activity"""
        current = list(self.activities)
        current.append(activity)
        self.activities = current[-50:]  # Keep last 50

    def update_from_events(self, events: List[Dict[str, Any]]) -> None:
        """Update from events list"""
        self.activities = events
