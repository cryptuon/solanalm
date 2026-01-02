"""
Hardware metrics gauges widget
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Static, ProgressBar, Label


class GaugeWidget(Container):
    """Single gauge for a hardware metric"""

    DEFAULT_CSS = """
    GaugeWidget {
        height: 3;
        padding: 0 1;
    }

    GaugeWidget .gauge-label {
        width: 10;
    }

    GaugeWidget ProgressBar {
        width: 1fr;
        padding: 0 1;
    }

    GaugeWidget .gauge-value {
        width: 8;
        text-align: right;
    }
    """

    value = reactive(0.0)

    def __init__(self, label: str, **kwargs):
        super().__init__(**kwargs)
        self._label = label

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(self._label, classes="gauge-label")
            yield ProgressBar(total=100, show_eta=False, show_percentage=False, id="bar")
            yield Static("0.0%", classes="gauge-value", id="value")

    def watch_value(self, value: float) -> None:
        try:
            bar = self.query_one("#bar", ProgressBar)
            bar.update(progress=min(value, 100))

            value_label = self.query_one("#value", Static)
            value_label.update(f"{value:.1f}%")
        except Exception:
            pass


class HardwareGauges(Container):
    """Panel showing hardware metrics as gauges"""

    DEFAULT_CSS = """
    HardwareGauges {
        height: auto;
        padding: 1;
        border: solid $primary;
    }

    HardwareGauges .section-title {
        text-style: bold;
        padding: 0 0 1 0;
        color: $text;
    }
    """

    # Reactive attributes
    cpu_percent = reactive(0.0)
    memory_percent = reactive(0.0)
    gpu_percent = reactive(0.0)
    storage_percent = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Static("Hardware Metrics", classes="section-title")
        yield GaugeWidget("CPU", id="gauge-cpu")
        yield GaugeWidget("Memory", id="gauge-memory")
        yield GaugeWidget("GPU", id="gauge-gpu")
        yield GaugeWidget("Storage", id="gauge-storage")

    def watch_cpu_percent(self, value: float) -> None:
        try:
            gauge = self.query_one("#gauge-cpu", GaugeWidget)
            gauge.value = value
        except Exception:
            pass

    def watch_memory_percent(self, value: float) -> None:
        try:
            gauge = self.query_one("#gauge-memory", GaugeWidget)
            gauge.value = value
        except Exception:
            pass

    def watch_gpu_percent(self, value: float) -> None:
        try:
            gauge = self.query_one("#gauge-gpu", GaugeWidget)
            gauge.value = value if value is not None else 0.0
        except Exception:
            pass

    def watch_storage_percent(self, value: float) -> None:
        try:
            gauge = self.query_one("#gauge-storage", GaugeWidget)
            gauge.value = value
        except Exception:
            pass

    def update_from_hardware(self, hardware) -> None:
        """Update from HardwareMetrics object"""
        self.cpu_percent = hardware.cpu_percent
        self.memory_percent = hardware.memory_percent
        self.gpu_percent = hardware.gpu_percent or 0.0
        self.storage_percent = hardware.storage_percent
