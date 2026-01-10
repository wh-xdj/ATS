# -*- coding: utf-8 -*-
"""测试框架日志模块"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from framework.config import get_test_config


class TestLogger:
    """测试框架日志管理器"""
    
    _instance: Optional['TestLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化日志器"""
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self) -> None:
        """设置日志器"""
        config = get_test_config()
        
        # 创建logger
        self._logger = logging.getLogger("xat.framework")
        self._logger.setLevel(getattr(logging, config.TEST_LOG_LEVEL))
        
        # 避免重复添加handler
        if self._logger.handlers:
            return
        
        # 日志格式
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.TEST_LOG_LEVEL))
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # 文件输出（如果启用）
        if config.TEST_LOG_TO_FILE:
            log_dir = Path(config.TEST_LOG_FILE_DIR)
            log_dir.mkdir(exist_ok=True)
            
            # 测试运行日志（带时间戳）
            log_file = log_dir / f"{config.TEST_LOG_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            file_handler = logging.FileHandler(
                log_file,
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            
            # 同时创建一个latest.log文件，方便查看最新日志
            latest_log = log_dir / f"{config.TEST_LOG_FILE_PREFIX}_latest.log"
            latest_handler = logging.FileHandler(
                latest_log,
                encoding="utf-8",
                mode='w'  # 每次覆盖
            )
            latest_handler.setLevel(logging.DEBUG)
            latest_handler.setFormatter(formatter)
            self._logger.addHandler(latest_handler)
    
    @property
    def logger(self) -> logging.Logger:
        """获取logger实例"""
        if self._logger is None:
            self._setup_logger()
        return self._logger
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """记录DEBUG级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """记录INFO级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """记录WARNING级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """记录ERROR级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """记录CRITICAL级别日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def log_test_start(self, test_name: str, test_file: str = "", markers: list = None) -> None:
        """记录测试用例开始"""
        marker_str = f" [标记: {', '.join(markers)}]" if markers else ""
        self.info(f"开始执行测试: {test_name}{marker_str}")
        if test_file:
            self.debug(f"测试文件: {test_file}")
    
    def log_test_end(
        self,
        test_name: str,
        status: str = "PASSED",
        duration: float = 0.0,
        error: str = ""
    ) -> None:
        """记录测试用例结束"""
        duration_str = f" (耗时: {duration:.3f}s)" if duration > 0 else ""
        if status == "PASSED":
            self.info(f"测试通过: {test_name}{duration_str}")
        elif status == "FAILED":
            self.error(f"测试失败: {test_name}{duration_str}")
            if error:
                self.error(f"错误信息: {error}")
        elif status == "SKIPPED":
            self.warning(f"测试跳过: {test_name}{duration_str}")
        elif status == "ERROR":
            self.error(f"测试错误: {test_name}{duration_str}")
            if error:
                self.error(f"错误信息: {error}")
    
    def log_framework_start(self, version: str = "1.0.0") -> None:
        """记录框架启动"""
        self.info("=" * 80)
        self.info(f"XAT测试框架启动 - 版本: {version}")
        self.info("=" * 80)
    
    def log_framework_end(self, total_tests: int = 0, passed: int = 0, failed: int = 0, 
                         skipped: int = 0, duration: float = 0.0) -> None:
        """记录框架结束"""
        self.info("=" * 80)
        self.info("XAT测试框架执行完成")
        self.info(f"总测试数: {total_tests}")
        self.info(f"通过: {passed} | 失败: {failed} | 跳过: {skipped}")
        if duration > 0:
            self.info(f"总耗时: {duration:.2f}s")
        self.info("=" * 80)
    
    def log_hook_execution(self, hook_name: str, status: str = "执行") -> None:
        """记录Hook执行"""
        self.debug(f"[Hook] {hook_name}: {status}")
    
    def log_fixture_setup(self, fixture_name: str, scope: str = "function") -> None:
        """记录Fixture设置"""
        self.debug(f"[Fixture] 设置 {fixture_name} (scope: {scope})")
    
    def log_fixture_teardown(self, fixture_name: str) -> None:
        """记录Fixture清理"""
        self.debug(f"[Fixture] 清理 {fixture_name}")


# 全局日志器实例
_test_logger: Optional[TestLogger] = None


def get_logger() -> TestLogger:
    """获取全局日志器实例"""
    global _test_logger
    if _test_logger is None:
        _test_logger = TestLogger()
    return _test_logger


# 便捷函数
def log_debug(message: str, *args, **kwargs) -> None:
    """记录DEBUG级别日志"""
    get_logger().debug(message, *args, **kwargs)


def log_info(message: str, *args, **kwargs) -> None:
    """记录INFO级别日志"""
    get_logger().info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs) -> None:
    """记录WARNING级别日志"""
    get_logger().warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs) -> None:
    """记录ERROR级别日志"""
    get_logger().error(message, *args, **kwargs)


def log_critical(message: str, *args, **kwargs) -> None:
    """记录CRITICAL级别日志"""
    get_logger().critical(message, *args, **kwargs)

