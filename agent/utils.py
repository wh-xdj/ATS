"""工具函数模块"""
import os
import platform
import socket
from pathlib import Path
from typing import Dict, Any


def get_hostname() -> str:
    """获取主机名"""
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def get_local_ip() -> str:
    """获取本机IP地址"""
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个远程地址（不会实际发送数据）
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # 备用方法
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return "127.0.0.1"


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    
    Returns:
        目录路径
    
    Raises:
        OSError: 如果无法创建目录或没有写权限
    """
    path = Path(path)
    if path.exists():
        if not path.is_dir():
            raise OSError(f"路径已存在但不是目录: {path}")
        # 检查写权限
        if not os.access(path, os.W_OK):
            raise OSError(f"目录没有写权限: {path}")
    else:
        path.mkdir(parents=True, exist_ok=True)
        # 创建后再次检查权限
        if not os.access(path, os.W_OK):
            raise OSError(f"目录创建成功但没有写权限: {path}")
    
    return path


def get_platform_info() -> Dict[str, str]:
    """
    获取平台信息
    
    Returns:
        包含平台信息的字典
    """
    return {
        "platform": platform.system().lower(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


def format_bytes(bytes_value: int) -> str:
    """
    格式化字节数为人类可读的格式
    
    Args:
        bytes_value: 字节数
    
    Returns:
        格式化后的字符串，如 "1.5 GB"
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def parse_work_dir(work_dir: str) -> Path:
    """
    解析工作目录路径
    
    Args:
        work_dir: 工作目录字符串
    
    Returns:
        Path对象
    """
    return Path(work_dir).expanduser().resolve()

