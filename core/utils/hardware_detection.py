#!/usr/bin/env python3
"""
Hardware Detection Utilities

Auto-detect system hardware specifications for nodes.
"""

import os
import platform
import psutil
import subprocess
import logging
from typing import Dict, Any, Optional
import torch

logger = logging.getLogger(__name__)


class HardwareDetector:
    """Detects and reports system hardware specifications"""

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information"""
        try:
            cpu_info = {
                "cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "architecture": platform.machine(),
                "model": platform.processor() or "Unknown"
            }

            # Try to get more detailed CPU info on Linux
            if platform.system() == "Linux":
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        cpuinfo = f.read()
                        for line in cpuinfo.split("\n"):
                            if "model name" in line:
                                cpu_info["model"] = line.split(":")[1].strip()
                                break
                except:
                    pass

            return cpu_info

        except Exception as e:
            logger.warning(f"Failed to detect CPU info: {e}")
            return {
                "cores": 4,
                "logical_cores": 8,
                "frequency_mhz": 2400,
                "architecture": platform.machine(),
                "model": "Unknown"
            }

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get memory information"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "total_gb": round(memory.total / (1024**3), 1),
                "available_gb": round(memory.available / (1024**3), 1),
                "used_gb": round(memory.used / (1024**3), 1),
                "percent_used": memory.percent,
                "swap_total_gb": round(swap.total / (1024**3), 1),
                "swap_used_gb": round(swap.used / (1024**3), 1)
            }

        except Exception as e:
            logger.warning(f"Failed to detect memory info: {e}")
            return {
                "total_gb": 8.0,
                "available_gb": 6.0,
                "used_gb": 2.0,
                "percent_used": 25.0,
                "swap_total_gb": 2.0,
                "swap_used_gb": 0.0
            }

    @staticmethod
    def get_storage_info() -> Dict[str, Any]:
        """Get storage information"""
        try:
            disk_usage = psutil.disk_usage('/')

            storage_info = {
                "total_gb": round(disk_usage.total / (1024**3), 1),
                "used_gb": round(disk_usage.used / (1024**3), 1),
                "free_gb": round(disk_usage.free / (1024**3), 1),
                "percent_used": round((disk_usage.used / disk_usage.total) * 100, 1)
            }

            # Get disk I/O statistics
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    storage_info.update({
                        "read_mb": round(disk_io.read_bytes / (1024**2), 1),
                        "write_mb": round(disk_io.write_bytes / (1024**2), 1),
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count
                    })
            except:
                pass

            return storage_info

        except Exception as e:
            logger.warning(f"Failed to detect storage info: {e}")
            return {
                "total_gb": 100.0,
                "used_gb": 20.0,
                "free_gb": 80.0,
                "percent_used": 20.0
            }

    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        """Get GPU information"""
        gpu_info = {
            "gpu_available": False,
            "gpu_count": 0,
            "gpus": []
        }

        try:
            if torch.cuda.is_available():
                gpu_info["gpu_available"] = True
                gpu_info["gpu_count"] = torch.cuda.device_count()

                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    gpu_info["gpus"].append({
                        "index": i,
                        "name": props.name,
                        "memory_gb": round(props.total_memory / (1024**3), 1),
                        "compute_capability": f"{props.major}.{props.minor}",
                        "multiprocessor_count": props.multi_processor_count
                    })

                # Get current GPU usage
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                         "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=5
                    )

                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for i, line in enumerate(lines):
                            if i < len(gpu_info["gpus"]):
                                parts = line.split(', ')
                                if len(parts) == 3:
                                    gpu_info["gpus"][i].update({
                                        "utilization_percent": int(parts[0]),
                                        "memory_used_mb": int(parts[1]),
                                        "memory_total_mb": int(parts[2])
                                    })
                except Exception:
                    # nvidia-smi not available or failed
                    pass

        except Exception as e:
            logger.debug(f"GPU detection failed: {e}")

        return gpu_info

    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get network information"""
        try:
            network_info = {
                "interfaces": [],
                "total_bytes_sent": 0,
                "total_bytes_recv": 0
            }

            # Get network interface information
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            for interface_name, addresses in net_if_addrs.items():
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    interface_info = {
                        "name": interface_name,
                        "is_up": stats.isup,
                        "speed_mbps": stats.speed if stats.speed > 0 else None,
                        "addresses": []
                    }

                    for addr in addresses:
                        interface_info["addresses"].append({
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        })

                    network_info["interfaces"].append(interface_info)

            # Get network I/O statistics
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    network_info.update({
                        "total_bytes_sent": net_io.bytes_sent,
                        "total_bytes_recv": net_io.bytes_recv,
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv
                    })
            except:
                pass

            # Estimate network speed
            active_interfaces = [iface for iface in network_info["interfaces"]
                               if iface["is_up"] and iface["speed_mbps"]]
            if active_interfaces:
                max_speed = max(iface["speed_mbps"] for iface in active_interfaces
                              if iface["speed_mbps"])
                network_info["estimated_speed_mbps"] = max_speed
            else:
                network_info["estimated_speed_mbps"] = 100  # Default assumption

            return network_info

        except Exception as e:
            logger.warning(f"Failed to detect network info: {e}")
            return {
                "interfaces": [],
                "estimated_speed_mbps": 100,
                "total_bytes_sent": 0,
                "total_bytes_recv": 0
            }

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get general system information"""
        try:
            boot_time = psutil.boot_time()
            return {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "boot_time": boot_time,
                "uptime_seconds": psutil.time.time() - boot_time
            }

        except Exception as e:
            logger.warning(f"Failed to detect system info: {e}")
            return {
                "platform": platform.system(),
                "platform_release": "Unknown",
                "platform_version": "Unknown",
                "architecture": platform.machine(),
                "hostname": "Unknown",
                "python_version": platform.python_version(),
                "boot_time": 0,
                "uptime_seconds": 0
            }

    @classmethod
    def get_complete_hardware_info(cls) -> Dict[str, Any]:
        """Get complete hardware information"""
        logger.info("Detecting system hardware...")

        hardware_info = {
            "cpu": cls.get_cpu_info(),
            "memory": cls.get_memory_info(),
            "storage": cls.get_storage_info(),
            "gpu": cls.get_gpu_info(),
            "network": cls.get_network_info(),
            "system": cls.get_system_info()
        }

        logger.info(f"Hardware detection complete:")
        logger.info(f"  CPU: {hardware_info['cpu']['cores']} cores")
        logger.info(f"  Memory: {hardware_info['memory']['total_gb']} GB")
        logger.info(f"  Storage: {hardware_info['storage']['total_gb']} GB")
        logger.info(f"  GPU: {hardware_info['gpu']['gpu_count']} devices")

        return hardware_info

    @classmethod
    def get_hardware_specs_for_node(cls) -> Dict[str, Any]:
        """Get hardware specs in the format expected by NodeCapabilities"""
        try:
            full_info = cls.get_complete_hardware_info()

            # Extract relevant information for node capabilities
            specs = {
                "cpu_cores": full_info["cpu"]["cores"],
                "ram_gb": int(full_info["memory"]["total_gb"]),
                "storage_gb": int(full_info["storage"]["total_gb"]),
                "network_speed_mbps": full_info["network"]["estimated_speed_mbps"]
            }

            # Add GPU information if available
            if full_info["gpu"]["gpu_available"] and full_info["gpu"]["gpus"]:
                primary_gpu = full_info["gpu"]["gpus"][0]
                specs.update({
                    "gpu_model": primary_gpu["name"],
                    "gpu_memory_gb": int(primary_gpu["memory_gb"])
                })
            else:
                specs.update({
                    "gpu_model": None,
                    "gpu_memory_gb": 0
                })

            return specs

        except Exception as e:
            logger.error(f"Failed to get hardware specs: {e}")
            # Return sensible defaults
            return {
                "cpu_cores": 4,
                "ram_gb": 8,
                "storage_gb": 100,
                "network_speed_mbps": 100,
                "gpu_model": None,
                "gpu_memory_gb": 0
            }


def benchmark_system_performance() -> Dict[str, Any]:
    """Run basic performance benchmarks"""
    logger.info("Running system performance benchmarks...")

    results = {}

    try:
        import time
        import numpy as np

        # CPU benchmark - simple matrix multiplication
        start_time = time.time()
        a = np.random.rand(1000, 1000)
        b = np.random.rand(1000, 1000)
        c = np.dot(a, b)
        cpu_time = time.time() - start_time
        results["cpu_benchmark_seconds"] = round(cpu_time, 3)

        # Memory benchmark - large array operations
        start_time = time.time()
        large_array = np.random.rand(10000, 1000)
        result_array = np.sum(large_array, axis=1)
        memory_time = time.time() - start_time
        results["memory_benchmark_seconds"] = round(memory_time, 3)

        # GPU benchmark if available
        if torch.cuda.is_available():
            start_time = time.time()
            gpu_tensor = torch.randn(1000, 1000).cuda()
            gpu_result = torch.mm(gpu_tensor, gpu_tensor)
            torch.cuda.synchronize()
            gpu_time = time.time() - start_time
            results["gpu_benchmark_seconds"] = round(gpu_time, 3)

    except Exception as e:
        logger.warning(f"Benchmark failed: {e}")
        results["benchmark_error"] = str(e)

    return results


if __name__ == "__main__":
    # Test hardware detection
    print("🔍 Hardware Detection Test")
    print("=" * 50)

    detector = HardwareDetector()

    # Get complete hardware info
    hardware_info = detector.get_complete_hardware_info()

    print("\n💻 System Information:")
    system = hardware_info["system"]
    print(f"  Platform: {system['platform']} {system['platform_release']}")
    print(f"  Hostname: {system['hostname']}")
    print(f"  Architecture: {system['architecture']}")
    print(f"  Python: {system['python_version']}")

    print("\n🔧 CPU Information:")
    cpu = hardware_info["cpu"]
    print(f"  Model: {cpu['model']}")
    print(f"  Cores: {cpu['cores']} physical, {cpu['logical_cores']} logical")
    print(f"  Frequency: {cpu['frequency_mhz']} MHz")

    print("\n💾 Memory Information:")
    memory = hardware_info["memory"]
    print(f"  Total: {memory['total_gb']} GB")
    print(f"  Available: {memory['available_gb']} GB")
    print(f"  Used: {memory['percent_used']}%")

    print("\n💿 Storage Information:")
    storage = hardware_info["storage"]
    print(f"  Total: {storage['total_gb']} GB")
    print(f"  Free: {storage['free_gb']} GB")
    print(f"  Used: {storage['percent_used']}%")

    print("\n🎮 GPU Information:")
    gpu = hardware_info["gpu"]
    if gpu["gpu_available"]:
        print(f"  GPU Count: {gpu['gpu_count']}")
        for i, gpu_device in enumerate(gpu["gpus"]):
            print(f"  GPU {i}: {gpu_device['name']}")
            print(f"    Memory: {gpu_device['memory_gb']} GB")
            print(f"    Compute: {gpu_device['compute_capability']}")
    else:
        print("  No GPU available")

    print("\n🌐 Network Information:")
    network = hardware_info["network"]
    print(f"  Estimated Speed: {network['estimated_speed_mbps']} Mbps")
    print(f"  Active Interfaces: {len([i for i in network['interfaces'] if i['is_up']])}")

    print("\n📊 Node Hardware Specs:")
    specs = detector.get_hardware_specs_for_node()
    for key, value in specs.items():
        print(f"  {key}: {value}")

    print("\n⚡ Performance Benchmarks:")
    benchmarks = benchmark_system_performance()
    for key, value in benchmarks.items():
        print(f"  {key}: {value}")

    print("\n✅ Hardware detection complete!")