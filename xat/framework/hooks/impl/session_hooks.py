# -*- coding: utf-8 -*-
"""Session类Hook实现"""
import pytest
import os
import time
from framework.hooks.base import SessionStartHook, SessionFinishHook
from framework.config import get_test_config
from framework.logger import get_logger


class SessionStartHookImpl(SessionStartHook):
    """Session开始Hook实现"""
    
    def __init__(self):
        super().__init__("SessionStart")
        self._start_time = None
    
    def execute(self, session: pytest.Session) -> None:
        """执行session开始逻辑"""
        if not self.enabled:
            return
        
        self._start_time = time.time()
        logger = get_logger()
        config = get_test_config()
        
        # 记录框架启动
        logger.log_framework_start(version="1.0.0")
        
        # 设置测试环境变量
        os.environ["ENVIRONMENT"] = config.TEST_ENVIRONMENT
        
        logger.info(f"测试环境: {config.TEST_ENVIRONMENT}")
        logger.info(f"日志级别: {config.TEST_LOG_LEVEL}")
        logger.info(f"测试数据库: {config.TEST_DATABASE_URL}")
    
    def get_start_time(self) -> float:
        """获取session开始时间"""
        return self._start_time or time.time()


class TestEnvironmentSetupHook(SessionStartHook):
    """测试环境设置Hook"""
    
    def execute(self, session: pytest.Session) -> None:
        """设置测试环境"""
        if not self.enabled:
            return
        
        logger = get_logger()
        config = get_test_config()
        
        # 设置日志
        if config.TEST_LOG_TO_FILE:
            self._setup_test_logging(config)
            logger.info("已启用文件日志")
        
        # 设置其他环境变量
        os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
        
        logger.debug("测试环境设置完成")
    
    def _setup_test_logging(self, config) -> None:
        """设置测试日志"""
        import logging
        from pathlib import Path
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, config.TEST_LOG_LEVEL),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "test.log"),
                logging.StreamHandler()
            ]
        )


class SessionFinishHookImpl(SessionFinishHook):
    """Session结束Hook实现"""
    
    def __init__(self, start_hook: SessionStartHookImpl = None):
        super().__init__("SessionFinish")
        self._start_hook = start_hook
        self._test_stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0,
        }
    
    def execute(self, session: pytest.Session) -> None:
        """执行session结束逻辑"""
        if not self.enabled:
            return
        
        logger = get_logger()
        exitstatus = session.exitstatus
        
        # 计算总耗时
        duration = 0.0
        if self._start_hook:
            duration = time.time() - self._start_hook.get_start_time()
        
        # 收集测试统计信息
        self._collect_test_stats(session)
        
        # 记录框架结束
        logger.log_framework_end(
            total_tests=self._test_stats["total"],
            passed=self._test_stats["passed"],
            failed=self._test_stats["failed"],
            skipped=self._test_stats["skipped"],
            duration=duration
        )
        
        # 清理测试环境
        self._cleanup_test_environment()
    
    def _collect_test_stats(self, session: pytest.Session) -> None:
        """收集测试统计信息"""
        # 从session中获取测试结果
        # 注意：这需要在pytest_runtest_logreport中收集
        # 这里先设置默认值
        pass
    
    def update_test_stats(self, **kwargs) -> None:
        """更新测试统计信息"""
        self._test_stats.update(kwargs)
    
    def _cleanup_test_environment(self) -> None:
        """清理测试环境"""
        logger = get_logger()
        config = get_test_config()
        
        # 清理临时文件
        if config.USE_TEST_DATABASE and "sqlite" in config.TEST_DATABASE_URL:
            import os
            db_path = config.TEST_DATABASE_URL.replace("sqlite:///", "")
            # 注意：实际使用时可能需要更谨慎的清理策略
            logger.debug(f"清理测试数据库: {db_path}")
