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
    
    # 注册session类hooks
    registry.register(SessionStartHookImpl())
    registry.register(TestEnvironmentSetupHook())
    registry.register(SessionFinishHookImpl())
    
    # 注册collection类hooks
    registry.register(CollectionModifyItemsHook())
    registry.register(TestMarkerHook())
    registry.register(TestSorterHook(sort_by="marker"))
    
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


__all__ = [
    "HookRegistry",
    "get_hook_registry",
    "setup_hooks",
    "pytest_configure",
    "pytest_sessionstart",
    "pytest_sessionfinish",
    "pytest_collection_modifyitems",
]

