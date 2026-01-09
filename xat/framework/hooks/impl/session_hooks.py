# -*- coding: utf-8 -*-
"""Session类Hook实现"""
import pytest
import os
from framework.hooks.base import SessionStartHook, SessionFinishHook
from framework.config import get_test_config


class SessionStartHookImpl(SessionStartHook):
    """Session开始Hook实现"""
    
    def execute(self, session: pytest.Session) -> None:
        """执行session开始逻辑"""
        if not self.enabled:
            return
        
        config = get_test_config()
        
        # 设置测试环境变量
        os.environ["ENVIRONMENT"] = config.TEST_ENVIRONMENT
        
        print(f"\n{'='*60}")
        print(f"[Hook] {self.name}: 测试会话开始")
        print(f"环境: {config.TEST_ENVIRONMENT}")
        print(f"{'='*60}\n")


class TestEnvironmentSetupHook(SessionStartHook):
    """测试环境设置Hook"""
    
    def execute(self, session: pytest.Session) -> None:
        """设置测试环境"""
        if not self.enabled:
            return
        
        config = get_test_config()
        
        # 设置日志
        if config.TEST_LOG_TO_FILE:
            self._setup_test_logging(config)
        
        # 设置其他环境变量
        os.environ.setdefault("PYTEST_CURRENT_TEST", "1")
        
        print(f"[Hook] {self.name}: 测试环境设置完成")
    
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
    
    def execute(self, session: pytest.Session) -> None:
        """执行session结束逻辑"""
        if not self.enabled:
            return
        
        exitstatus = session.exitstatus
        
        print(f"\n{'='*60}")
        print(f"[Hook] {self.name}: 测试会话结束")
        print(f"退出状态: {exitstatus}")
        print(f"{'='*60}\n")
        
        # 清理测试环境
        self._cleanup_test_environment()
    
    def _cleanup_test_environment(self) -> None:
        """清理测试环境"""
        config = get_test_config()
        
        # 清理临时文件
        if config.USE_TEST_DATABASE and "sqlite" in config.TEST_DATABASE_URL:
            import os
            db_path = config.TEST_DATABASE_URL.replace("sqlite:///", "")
            # 注意：实际使用时可能需要更谨慎的清理策略
            pass

