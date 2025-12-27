"""系统监控模块"""
import platform
import psutil
from typing import Dict, Any, Optional
from pathlib import Path


class SystemMonitor:
    """系统监控类"""
    
    def __init__(self):
        self._last_cpu_percent: Optional[float] = None
        self._last_memory_info: Optional[Dict[str, Any]] = None
        self._last_disk_info: Optional[Dict[str, Any]] = None
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """
        获取CPU信息
        
        Returns:
            CPU信息字典
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            
            # 获取CPU型号（平台相关）
            cpu_model = "Unknown"
            try:
                if platform.system() == "Linux":
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if "model name" in line:
                                cpu_model = line.split(":")[1].strip()
                                break
                elif platform.system() == "Darwin":  # macOS
                    import subprocess
                    result = subprocess.run(
                        ["sysctl", "-n", "machdep.cpu.brand_string"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        cpu_model = result.stdout.strip()
                elif platform.system() == "Windows":
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "cpu", "get", "name"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split("\n")
                        if len(lines) > 1:
                            cpu_model = lines[1].strip()
            except Exception:
                pass
            
            return {
                "usage_percent": round(cpu_percent, 2),
                "cores": cpu_count,
                "model": cpu_model,
                "frequency": f"{cpu_freq.current:.2f}MHz" if cpu_freq else "Unknown"
            }
        except Exception as e:
            # 如果采集失败，使用上一次的值
            if self._last_cpu_percent is not None:
                return {
                    "usage_percent": self._last_cpu_percent,
                    "cores": psutil.cpu_count(logical=True) or 0,
                    "model": "Unknown",
                    "frequency": "Unknown"
                }
            return {
                "usage_percent": 0.0,
                "cores": 0,
                "model": "Unknown",
                "frequency": "Unknown"
            }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        获取内存信息
        
        Returns:
            内存信息字典（单位：MB）
        """
        try:
            mem = psutil.virtual_memory()
            total_mb = mem.total // (1024 * 1024)
            used_mb = mem.used // (1024 * 1024)
            free_mb = mem.available // (1024 * 1024)
            usage_percent = mem.percent
            
            info = {
                "total": total_mb,
                "used": used_mb,
                "free": free_mb,
                "usage_percent": round(usage_percent, 2),
                "unit": "MB"
            }
            self._last_memory_info = info
            return info
        except Exception as e:
            # 使用上一次的值
            if self._last_memory_info:
                return self._last_memory_info
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "usage_percent": 0.0,
                "unit": "MB"
            }
    
    def get_disk_info(self, work_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        获取磁盘信息
        
        Args:
            work_dir: 工作目录路径，用于获取该目录所在磁盘的信息
        
        Returns:
            磁盘信息字典（单位：MB）
        """
        try:
            if work_dir:
                # 获取工作目录所在磁盘的信息
                disk = psutil.disk_usage(str(work_dir))
            else:
                # 获取根目录所在磁盘的信息
                disk = psutil.disk_usage("/")
            
            total_mb = disk.total // (1024 * 1024)
            used_mb = disk.used // (1024 * 1024)
            free_mb = disk.free // (1024 * 1024)
            usage_percent = (disk.used / disk.total) * 100
            
            info = {
                "total": total_mb,
                "used": used_mb,
                "free": free_mb,
                "usage_percent": round(usage_percent, 2),
                "unit": "MB"
            }
            self._last_disk_info = info
            return info
        except Exception as e:
            # 使用上一次的值
            if self._last_disk_info:
                return self._last_disk_info
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "usage_percent": 0.0,
                "unit": "MB"
            }
    
    def get_network_info(self) -> Dict[str, str]:
        """
        获取网络信息
        
        Returns:
            网络信息字典
        """
        try:
            from .utils import get_local_ip, get_hostname
        except ImportError:
            from utils import get_local_ip, get_hostname
        
        try:
            return {
                "ip": get_local_ip(),
                "hostname": get_hostname()
            }
        except Exception:
            return {
                "ip": "127.0.0.1",
                "hostname": "unknown"
            }
    
    def get_os_info(self) -> Dict[str, str]:
        """
        获取操作系统信息
        
        Returns:
            操作系统信息字典
        """
        try:
            os_type = platform.system()
            os_version = platform.version()
            
            # 获取更详细的版本信息
            if os_type == "Linux":
                try:
                    import distro
                    os_version = f"{distro.name()} {distro.version()}"
                except ImportError:
                    # 尝试从/etc/os-release读取
                    try:
                        with open("/etc/os-release", "r") as f:
                            for line in f:
                                if line.startswith("PRETTY_NAME="):
                                    os_version = line.split("=", 1)[1].strip().strip('"')
                                    break
                    except Exception:
                        pass
            elif os_type == "Darwin":  # macOS
                import subprocess
                try:
                    result = subprocess.run(
                        ["sw_vers", "-productVersion"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        os_version = f"macOS {result.stdout.strip()}"
                except Exception:
                    pass
            
            kernel = platform.release()
            
            return {
                "type": os_type,
                "version": os_version,
                "kernel": kernel
            }
        except Exception:
            return {
                "type": platform.system(),
                "version": "Unknown",
                "kernel": platform.release()
            }
    
    def get_all_info(self, work_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        获取所有系统信息
        
        Args:
            work_dir: 工作目录路径
        
        Returns:
            包含所有系统信息的字典
        """
        return {
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(work_dir),
            "network": self.get_network_info(),
            "os": self.get_os_info()
        }

