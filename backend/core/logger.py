"""日志配置模块 - 使用 loguru"""
from loguru import logger
import sys
from pathlib import Path
from config import settings


def setup_logger():
    """配置 loguru logger"""
    # 移除默认的 handler
    logger.remove()
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 控制台输出（开发环境）
    if settings.ENVIRONMENT == "development":
        logger.add(
            sys.stdout,
            format=log_format,
            level=settings.LOG_LEVEL,
            colorize=True,
        )
    else:
        # 生产环境：只输出 INFO 及以上级别到控制台
        logger.add(
            sys.stdout,
            format=log_format,
            level="INFO",
            colorize=False,
        )
    
    # 文件输出 - 所有日志
    logger.add(
        log_dir / "ats.log",
        format=log_format,
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )
    
    # 文件输出 - 错误日志
    logger.add(
        log_dir / "error.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )
    
    return logger


# 初始化 logger
setup_logger()

# 导出 logger 供其他模块使用
__all__ = ["logger"]

