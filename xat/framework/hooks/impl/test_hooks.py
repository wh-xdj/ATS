# -*- coding: utf-8 -*-
"""测试用例相关Hook实现"""
import pytest
import time
from framework.hooks.base import TestSetupHook, TestTeardownHook
from framework.logger import get_logger


class TestSetupLogHook(TestSetupHook):
    """测试用例开始日志Hook"""
    
    def __init__(self):
        super().__init__("TestSetupLog")
        self._test_start_times: dict = {}
    
    def execute(self, item: pytest.Item) -> None:
        """记录测试用例开始"""
        if not self.enabled:
            return
        
        logger = get_logger()
        
        # 获取测试信息
        test_name = item.nodeid
        test_file = str(item.fspath) if hasattr(item, 'fspath') else ""
        
        # 获取标记
        markers = [marker.name for marker in item.iter_markers()]
        
        # 记录开始时间
        self._test_start_times[test_name] = time.time()
        
        # 记录日志
        logger.log_test_start(test_name, test_file, markers)
    
    def get_test_duration(self, test_name: str) -> float:
        """获取测试执行时长"""
        if test_name in self._test_start_times:
            return time.time() - self._test_start_times[test_name]
        return 0.0


class TestTeardownLogHook(TestTeardownHook):
    """测试用例结束日志Hook"""
    
    def __init__(self, setup_hook: TestSetupLogHook = None):
        super().__init__("TestTeardownLog")
        self._setup_hook = setup_hook
    
    def execute(self, item: pytest.Item) -> None:
        """记录测试用例结束"""
        if not self.enabled:
            return
        
        logger = get_logger()
        
        # 获取测试信息
        test_name = item.nodeid
        
        # 获取执行时长
        duration = 0.0
        if self._setup_hook:
            duration = self._setup_hook.get_test_duration(test_name)
        
        # 获取测试状态（从pytest的report中获取）
        # 注意：在teardown阶段，我们无法直接获取状态，需要在call阶段记录
        # 这里先记录基本信息，状态会在report hook中补充
        logger.log_test_end(test_name, status="COMPLETED", duration=duration)


class TestReportHook(TestTeardownHook):
    """测试报告Hook - 记录测试结果"""
    
    def __init__(self, setup_hook: TestSetupLogHook = None):
        super().__init__("TestReportLog")
        self._setup_hook = setup_hook
        self._test_results: dict = {}
    
    def execute(self, item: pytest.Item) -> None:
        """记录测试结果"""
        if not self.enabled:
            return
        
        # 这个方法会在pytest_runtest_logreport中调用
        # 但为了保持一致性，我们在这里也记录基本信息
        pass
    
    def log_test_result(self, test_name: str, status: str, duration: float = 0.0, error: str = ""):
        """记录测试结果"""
        logger = get_logger()
        logger.log_test_end(test_name, status, duration, error)

