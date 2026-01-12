# -*- coding: utf-8 -*-
"""Hook模块入口 - 初始化所有hooks"""
from framework.hooks.registry import HookRegistry, get_hook_registry
from framework.hooks.impl import (
    PytestConfigureHook,
    MarkerRegistrationHook,
    AsyncioConfigHook,
    SessionStartHookImpl,
    SessionFinishHookImpl,
    TestEnvironmentSetupHook,
    CollectionModifyItemsHook,
    TestMarkerHook,
    TestSorterHook,
    TestCaseFilterHook,
    TestSetupLogHook,
    TestTeardownLogHook,
    TestReportHook,
    TestResultCollectorHook,
    AllureConfigHook,
    AllureTestSetupHook,
    AllureTestTeardownHook,
    AllureReportHook,
)


def setup_hooks() -> HookRegistry:
    """
    设置并注册所有hooks
    
    Returns:
        HookRegistry实例
    """
    registry = get_hook_registry()
    
    # 注册配置类hooks
    registry.register(PytestConfigureHook())
    registry.register(MarkerRegistrationHook())
    registry.register(AsyncioConfigHook())
    registry.register(AllureConfigHook())
    registry.register(AllureReportHook())
    
    # 注册session类hooks（需要保持引用以便传递）
    session_start_hook = SessionStartHookImpl()
    session_finish_hook = SessionFinishHookImpl(start_hook=session_start_hook)
    
    registry.register(session_start_hook)
    registry.register(TestEnvironmentSetupHook())
    registry.register(session_finish_hook)
    
    # 注册collection类hooks
    registry.register(CollectionModifyItemsHook())
    registry.register(TestMarkerHook())
    registry.register(TestSorterHook(sort_by="marker"))
    registry.register(TestCaseFilterHook())  # 用例筛选Hook，放在最后确保筛选在最后执行
    
    # 注册测试用例类hooks（需要保持引用以便传递）
    test_setup_hook = TestSetupLogHook()
    test_teardown_hook = TestTeardownLogHook(setup_hook=test_setup_hook)
    test_result_collector = TestResultCollectorHook()  # 结果收集Hook
    
    registry.register(test_setup_hook)
    registry.register(test_teardown_hook)
    registry.register(test_result_collector)  # 注册结果收集Hook
    registry.register(AllureTestSetupHook())
    registry.register(AllureTestTeardownHook())
    
    return registry


# 自动初始化hooks
_hook_registry = setup_hooks()

# 导出pytest hook函数（pytest会自动发现这些函数）
def pytest_configure(config):
    """Pytest配置hook"""
    _hook_registry.pytest_configure(config)


def pytest_sessionstart(session):
    """Pytest session开始hook"""
    _hook_registry.pytest_sessionstart(session)


def pytest_sessionfinish(session, exitstatus):
    """Pytest session结束hook"""
    _hook_registry.pytest_sessionfinish(session, exitstatus)


def pytest_collection_modifyitems(config, items):
    """Pytest collection修改hook"""
    _hook_registry.pytest_collection_modifyitems(config, items)


def pytest_runtest_setup(item):
    """Pytest测试用例开始hook"""
    _hook_registry.pytest_runtest_setup(item)


def pytest_runtest_teardown(item):
    """Pytest测试用例结束hook"""
    _hook_registry.pytest_runtest_teardown(item)


def pytest_runtest_logreport(report):
    """Pytest测试报告hook - 记录测试结果"""
    from framework.logger import get_logger
    
    logger = get_logger()
    
    # 只在测试结束时记录
    if report.when == "call" and report.outcome:
        test_name = report.nodeid
        status_map = {
            "passed": "PASSED",
            "failed": "FAILED",
            "skipped": "SKIPPED",
        }
        status = status_map.get(report.outcome, "UNKNOWN")
        duration = getattr(report, 'duration', 0.0)
        error = ""
        
        if report.outcome == "failed" and hasattr(report, 'longrepr'):
            error = str(report.longrepr)[:1000]  # 限制错误信息长度
        
        logger.log_test_end(test_name, status, duration, error)
        
        # 调用结果收集Hook（立即写入文件）
        for hook in _hook_registry.get_hooks("test"):
            if hasattr(hook, 'log_test_result'):
                hook.log_test_result(test_name, status, duration, error)


__all__ = [
    "HookRegistry",
    "get_hook_registry",
    "setup_hooks",
    "pytest_configure",
    "pytest_sessionstart",
    "pytest_sessionfinish",
    "pytest_collection_modifyitems",
    "pytest_runtest_setup",
    "pytest_runtest_teardown",
    "pytest_runtest_logreport",
]
