"""
Hardware metrics collector for real-time system monitoring
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

# Try to import psutil, provide fallback if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, hardware metrics will be limited")


@dataclass
class HardwareMetrics:
    """Snapshot of hardware metrics"""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # CPU
    cpu_percent: float = 0.0
    cpu_cores_used: int = 0
    cpu_frequency_mhz: float = 0.0

    # Memory
    memory_total_gb: float = 0.0
    memory_used_gb: float = 0.0
    memory_percent: float = 0.0

    # GPU
    gpu_available: bool = False
    gpu_percent: Optional[float] = None
    gpu_memory_used_gb: Optional[float] = None
    gpu_memory_total_gb: Optional[float] = None
    gpu_temperature_c: Optional[float] = None

    # Storage
    storage_total_gb: float = 0.0
    storage_used_gb: float = 0.0
    storage_percent: float = 0.0

    # Network
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0


class HardwareCollector:
    """Collects real-time hardware metrics"""

    def __init__(self, history_size: int = 3600):
        """
        Args:
            history_size: Number of metrics snapshots to retain (default 1 hour at 1/sec)
        """
        self.history: deque[HardwareMetrics] = deque(maxlen=history_size)
        self._last_network_bytes_sent = 0
        self._last_network_bytes_recv = 0
        self._gpu_info_cache: Optional[Dict] = None
        self._gpu_cache_time: Optional[datetime] = None

    def get_current_metrics(self) -> HardwareMetrics:
        """Get current hardware utilization snapshot"""
        metrics = HardwareMetrics()

        if PSUTIL_AVAILABLE:
            metrics = self._collect_with_psutil()
        else:
            metrics = self._collect_fallback()

        # Add GPU metrics
        gpu_metrics = self._collect_gpu_metrics()
        if gpu_metrics:
            metrics.gpu_available = True
            metrics.gpu_percent = gpu_metrics.get("utilization")
            metrics.gpu_memory_used_gb = gpu_metrics.get("memory_used_gb")
            metrics.gpu_memory_total_gb = gpu_metrics.get("memory_total_gb")
            metrics.gpu_temperature_c = gpu_metrics.get("temperature")

        # Store in history
        self.history.append(metrics)

        return metrics

    def _collect_with_psutil(self) -> HardwareMetrics:
        """Collect metrics using psutil"""
        metrics = HardwareMetrics()

        # CPU
        metrics.cpu_percent = psutil.cpu_percent(interval=None)
        metrics.cpu_cores_used = psutil.cpu_count(logical=True) or 1
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            metrics.cpu_frequency_mhz = cpu_freq.current

        # Memory
        memory = psutil.virtual_memory()
        metrics.memory_total_gb = memory.total / (1024 ** 3)
        metrics.memory_used_gb = memory.used / (1024 ** 3)
        metrics.memory_percent = memory.percent

        # Storage
        try:
            disk = psutil.disk_usage('/')
            metrics.storage_total_gb = disk.total / (1024 ** 3)
            metrics.storage_used_gb = disk.used / (1024 ** 3)
            metrics.storage_percent = disk.percent
        except Exception:
            pass

        # Network
        try:
            net_io = psutil.net_io_counters()
            metrics.network_bytes_sent = net_io.bytes_sent
            metrics.network_bytes_recv = net_io.bytes_recv
        except Exception:
            pass

        return metrics

    def _collect_fallback(self) -> HardwareMetrics:
        """Fallback collection when psutil is not available"""
        metrics = HardwareMetrics()

        # Try to read from /proc on Linux
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if line.startswith('MemTotal:'):
                        metrics.memory_total_gb = int(line.split()[1]) / (1024 ** 2)
                    elif line.startswith('MemAvailable:'):
                        available = int(line.split()[1]) / (1024 ** 2)
                        metrics.memory_used_gb = metrics.memory_total_gb - available
                        metrics.memory_percent = (metrics.memory_used_gb / metrics.memory_total_gb) * 100
        except Exception:
            pass

        # Try to get CPU load average
        try:
            with open('/proc/loadavg', 'r') as f:
                load = float(f.read().split()[0])
                metrics.cpu_percent = min(load * 100, 100)
        except Exception:
            pass

        return metrics

    def _collect_gpu_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect GPU metrics using multiple methods"""
        # Try PyTorch first
        try:
            import torch
            if torch.cuda.is_available():
                device = torch.cuda.current_device()
                total_mem = torch.cuda.get_device_properties(device).total_memory
                allocated = torch.cuda.memory_allocated(device)

                return {
                    "utilization": None,  # PyTorch doesn't provide this directly
                    "memory_used_gb": allocated / (1024 ** 3),
                    "memory_total_gb": total_mem / (1024 ** 3),
                    "temperature": None,
                }
        except Exception:
            pass

        # Try nvidia-smi
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                values = result.stdout.strip().split(',')
                if len(values) >= 4:
                    return {
                        "utilization": float(values[0].strip()),
                        "memory_used_gb": float(values[1].strip()) / 1024,
                        "memory_total_gb": float(values[2].strip()) / 1024,
                        "temperature": float(values[3].strip()),
                    }
        except Exception:
            pass

        return None

    def get_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get historical metrics for the specified time period"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes) if minutes > 0 else None

        from datetime import timedelta

        result = []
        for m in self.history:
            if cutoff is None or m.timestamp > cutoff:
                result.append({
                    "timestamp": m.timestamp.isoformat(),
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "memory_used_gb": m.memory_used_gb,
                    "gpu_percent": m.gpu_percent,
                    "gpu_memory_used_gb": m.gpu_memory_used_gb,
                    "storage_percent": m.storage_percent,
                })

        return result

    def to_dict(self, metrics: Optional[HardwareMetrics] = None) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        if metrics is None:
            metrics = self.get_current_metrics()

        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu": {
                "percent": metrics.cpu_percent,
                "cores": metrics.cpu_cores_used,
                "frequency_mhz": metrics.cpu_frequency_mhz,
            },
            "memory": {
                "total_gb": round(metrics.memory_total_gb, 2),
                "used_gb": round(metrics.memory_used_gb, 2),
                "percent": round(metrics.memory_percent, 1),
            },
            "gpu": {
                "available": metrics.gpu_available,
                "percent": metrics.gpu_percent,
                "memory_used_gb": round(metrics.gpu_memory_used_gb, 2) if metrics.gpu_memory_used_gb else None,
                "memory_total_gb": round(metrics.gpu_memory_total_gb, 2) if metrics.gpu_memory_total_gb else None,
                "temperature_c": metrics.gpu_temperature_c,
            },
            "storage": {
                "total_gb": round(metrics.storage_total_gb, 1),
                "used_gb": round(metrics.storage_used_gb, 1),
                "percent": round(metrics.storage_percent, 1),
            },
            "network": {
                "bytes_sent": metrics.network_bytes_sent,
                "bytes_recv": metrics.network_bytes_recv,
            },
        }
