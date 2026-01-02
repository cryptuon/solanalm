# Terminal User Interface (TUI)

SolanaLM includes a terminal-based dashboard for monitoring nodes directly from the command line.

## Overview

The TUI provides real-time monitoring of your SolanaLM nodes with:

- Dashboard with node status and metrics
- Live log streaming
- Training round monitoring
- Earnings tracker

```
┌─────────────────────────────────────────────────────────────┐
│  SolanaLM Node Monitor                    Node: abc123...   │
├─────────────────────────────────────────────────────────────┤
│  [Dashboard]  [Logs]  [Training]  [Earnings]                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Node Status: ONLINE                                        │
│  Requests Processed: 1,234                                  │
│  Average Latency: 0.234s                                    │
│  GPU Memory: 8.2 / 16 GB                                    │
│                                                             │
│  Network Stats                                              │
│  ─────────────                                              │
│  Connected Peers: 12                                        │
│  Gateway Status: Connected                                  │
│  Total Earnings: 0.0234 SOL                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
│  1: Dashboard  2: Logs  3: Training  4: Earnings  q: Quit   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Start the TUI connected to your local node
python -m core.tui

# Connect to a specific node
python -m core.tui --node-url http://localhost:8100

# Use light theme
python -m core.tui --theme light

# Disable mouse (for SSH sessions)
python -m core.tui --no-mouse
```

## Installation

The TUI requires the `textual` library:

```bash
# Already included with SolanaLM
poetry install

# Or install manually
pip install textual
```

## Command Line Options

```bash
python -m core.tui --help
```

| Option | Default | Description |
|--------|---------|-------------|
| `--node-url` | `http://localhost:8100` | Node API URL to connect to |
| `--theme` | `dark` | Color theme (`dark` or `light`) |
| `--no-mouse` | `false` | Disable mouse support for SSH |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Switch to Dashboard tab |
| `2` | Switch to Logs tab |
| `3` | Switch to Training tab |
| `4` | Switch to Earnings tab |
| `r` | Refresh current view |
| `?` | Show help |
| `q` | Quit application |
| `Ctrl+C` | Force quit |

## Tabs

### Dashboard

The main overview showing:

- Node status (online/offline/busy)
- Current workload and queue depth
- Resource usage (CPU, Memory, GPU)
- Connection status to gateway
- Quick metrics summary

### Logs

Live streaming of node logs with:

- Severity filtering (info, warning, error)
- Search functionality
- Auto-scroll with pause option
- Log export capability

### Training

Federated learning monitoring:

- Current training round status
- Participation history
- Model update progress
- Privacy budget tracking
- Round completion metrics

### Earnings

Track your SOL earnings:

- Total earnings summary
- Earnings by period (daily, weekly, monthly)
- Payment history
- Pending payments
- Earnings charts

## Connecting to Remote Nodes

Connect to nodes running on remote servers:

```bash
# Local node
python -m core.tui --node-url http://localhost:8100

# Remote node
python -m core.tui --node-url http://192.168.1.100:8100

# Node with custom port
python -m core.tui --node-url http://my-node.example.com:8100
```

## SSH Usage

When using the TUI over SSH, disable mouse support for better compatibility:

```bash
ssh user@server "cd /path/to/solanalm && python -m core.tui --no-mouse"
```

Or use tmux/screen for persistent sessions:

```bash
# Start in tmux
tmux new -s solanalm
python -m core.tui

# Detach with Ctrl+B, D
# Reattach with: tmux attach -t solanalm
```

## Customization

### Themes

The TUI supports dark and light themes:

```bash
# Dark theme (default)
python -m core.tui --theme dark

# Light theme
python -m core.tui --theme light
```

### Configuration

Create a config file for persistent settings:

```python
# ~/.solanalm/tui_config.py
TUI_CONFIG = {
    "default_node_url": "http://localhost:8100",
    "theme": "dark",
    "refresh_interval": 5,  # seconds
    "log_buffer_size": 1000,
}
```

## Troubleshooting

### TUI won't start

Ensure you have the required dependencies:

```bash
poetry install
# or
pip install textual aiohttp
```

### Connection errors

Check that your node is running and accessible:

```bash
# Test node API
curl http://localhost:8100/health
```

### Display issues over SSH

Use the `--no-mouse` flag and ensure your terminal supports ANSI colors:

```bash
export TERM=xterm-256color
python -m core.tui --no-mouse
```

### Performance issues

Increase refresh interval for slower connections:

```python
# In your config
TUI_CONFIG = {
    "refresh_interval": 10,  # Slower refresh
}
```

## Next Steps

- [Running Nodes](running-nodes.md) - Start your first node
- [Federated Learning](federated-learning.md) - Training round details
- [Privacy Features](privacy.md) - Privacy monitoring
