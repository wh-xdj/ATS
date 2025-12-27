# -*- coding: utf-8 -*-
"""日志管理模块 - 使用loguru"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(
    log_dir: Path,
    log_level: str = "INFO",
    log_file: str = "agent.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logger:
    """
    设置日志系统（使用loguru）
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_file: 日志文件名
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 保留的历史日志文件数量
    
    Returns:
        配置好的Logger实例
    """
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 移除默认的handler
    logger.remove()
    
    # 日志格式：包含时间、级别、进程ID、线程ID、文件名、行号、函数名、消息
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>PID-{process.id}</cyan> | "
        "<cyan>Thread-{thread.id}</cyan> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 控制台输出（带颜色）
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # 文件输出（不带颜色，更详细的格式）
    log_file_path = log_dir / log_file
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "PID-{process.id} | "
        "Thread-{thread.id} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    logger.add(
        str(log_file_path),
        format=file_format,
        level="DEBUG",  # 文件记录所有级别的日志
        rotation=max_bytes,  # 文件大小达到max_bytes时轮转
        retention=backup_count,  # 保留backup_count个历史文件
        compression="zip",  # 压缩旧日志文件
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
        enqueue=True,  # 异步写入，提高性能
    )
    
    return logger


def get_logger(name: Optional[str] = None):
    """
    获取日志器
    
    Args:
        name: 日志器名称，如果为None则返回默认的agent logger
    
    Returns:
        Logger实例
    """
    if name:
        return logger.bind(name=f"agent.{name}")
    return logger.bind(name="agent")
