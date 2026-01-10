# -*- coding: utf-8 -*-
"""Hook注册管理器"""
from typing import Dict, List
import pytest
from framework.hooks.base import (
    BaseHook,
    ConfigHook,
    SessionStartHook,
    SessionFinishHook,
    CollectionHook,
    TestSetupHook,
    TestTeardownHook,
    TestCallHook,
)


class HookRegistry:
    """Hook注册管理器 - 统一管理所有hooks"""
    
    def __init__(self):
        """初始化Hook注册器"""
        self._config_hooks: List[ConfigHook] = []
        self._session_start_hooks: List[SessionStartHook] = []
        self._session_finish_hooks: List[SessionFinishHook] = []
        self._collection_hooks: List[CollectionHook] = []
        self._test_setup_hooks: List[TestSetupHook] = []
        self._test_teardown_hooks: List[TestTeardownHook] = []
        self._test_call_hooks: List[TestCallHook] = []
        self._all_hooks: Dict[str, List[BaseHook]] = {
            "config": self._config_hooks,
            "session_start": self._session_start_hooks,
            "session_finish": self._session_finish_hooks,
            "collection": self._collection_hooks,
            "test_setup": self._test_setup_hooks,
            "test_teardown": self._test_teardown_hooks,
            "test_call": self._test_call_hooks,
        }
    
    def register(self, hook: BaseHook) -> None:
        """
        注册一个hook
        
        Args:
            hook: Hook实例
        """
        if isinstance(hook, ConfigHook):
            self._config_hooks.append(hook)
        elif isinstance(hook, SessionStartHook):
            self._session_start_hooks.append(hook)
        elif isinstance(hook, SessionFinishHook):
            self._session_finish_hooks.append(hook)
        elif isinstance(hook, CollectionHook):
            self._collection_hooks.append(hook)
        elif isinstance(hook, TestSetupHook):
            self._test_setup_hooks.append(hook)
        elif isinstance(hook, TestTeardownHook):
            self._test_teardown_hooks.append(hook)
        elif isinstance(hook, TestCallHook):
            self._test_call_hooks.append(hook)
        else:
            raise ValueError(f"不支持的Hook类型: {type(hook)}")
    
    def register_many(self, hooks: List[BaseHook]) -> None:
        """
        批量注册hooks
        
        Args:
            hooks: Hook实例列表
        """
        for hook in hooks:
            self.register(hook)
    
    def unregister(self, hook_name: str) -> None:
        """
        取消注册hook
        
        Args:
            hook_name: Hook名称
        """
        for hook_list in self._all_hooks.values():
            hooks_to_remove = [h for h in hook_list if h.name == hook_name]
            for hook in hooks_to_remove:
                hook_list.remove(hook)
    
    def get_hooks(self, hook_type: str) -> List[BaseHook]:
        """
        获取指定类型的hooks
        
        Args:
            hook_type: Hook类型
        
        Returns:
            Hook列表
        """
        return self._all_hooks.get(hook_type, [])
    
    def enable_all(self) -> None:
        """启用所有hooks"""
        for hook_list in self._all_hooks.values():
            for hook in hook_list:
                hook.enable()
    
    def disable_all(self) -> None:
        """禁用所有hooks"""
        for hook_list in self._all_hooks.values():
            for hook in hook_list:
                hook.disable()
    
    # Pytest Hook函数 - 这些会被pytest自动调用
    def pytest_configure(self, config: pytest.Config) -> None:
        """pytest_configure hook入口"""
        for hook in self._config_hooks:
            if hook.enabled:
                try:
                    hook.execute(config)
                except Exception as e:
                    from framework.logger import get_logger
                    get_logger().error(f"[Hook Error] {hook.name} 执行失败: {e}", exc_info=True)
    
    def pytest_sessionstart(self, session: pytest.Session) -> None:
        """pytest_sessionstart hook入口"""
        for hook in self._session_start_hooks:
            if hook.enabled:
                try:
                    hook.execute(session)
                except Exception as e:
                    from framework.logger import get_logger
                    get_logger().error(f"[Hook Error] {hook.name} 执行失败: {e}", exc_info=True)
    
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        """pytest_sessionfinish hook入口"""
        for hook in self._session_finish_hooks:
            if hook.enabled:
                try:
                    hook.execute(session)
                except Exception as e:
                    from framework.logger import get_logger
                    get_logger().error(f"[Hook Error] {hook.name} 执行失败: {e}", exc_info=True)
    
    def pytest_collection_modifyitems(
        self,
        config: pytest.Config,
        items: List[pytest.Item]
    ) -> None:
        """pytest_collection_modifyitems hook入口"""
        for hook in self._collection_hooks:
            if hook.enabled:
                try:
                    hook.execute(config, items)
                except Exception as e:
                    from framework.logger import get_logger
                    get_logger().error(f"[Hook Error] {hook.name} 执行失败: {e}", exc_info=True)
    
    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        """pytest_runtest_setup hook入口"""
        for hook in self._test_setup_hooks:
            if hook.enabled:
                try:
                    hook.execute(item)
                except Exception as e:
                    from framework.logger import get_logger
                    get_logger().error(f"[Hook Error] {hook.name} 执行失败: {e}", exc_info=True)
    
    def pytest_runtest_teardown(self, item: pytest.Item) -> None:
        """pytest_runtest_teardown hook入口"""
        for hook in self._test_teardown_hooks:
            if hook.enabled:
                try:
                    hook.execute(item)
                except Exception as e:
                    from framework.logger import get_logger
                    get_logger().error(f"[Hook Error] {hook.name} 执行失败: {e}", exc_info=True)
    
    def pytest_runtest_call(self, item: pytest.Item) -> None:
        """pytest_runtest_call hook入口"""
        for hook in self._test_call_hooks:
            if hook.enabled:
                try:
                    hook.execute(item)
                except Exception as e:
                    from framework.logger import get_logger
                    get_logger().error(f"[Hook Error] {hook.name} 执行失败: {e}", exc_info=True)


# 全局Hook注册器实例
_hook_registry: HookRegistry = None


def get_hook_registry() -> HookRegistry:
    """获取全局Hook注册器实例（单例模式）"""
    global _hook_registry
    if _hook_registry is None:
        _hook_registry = HookRegistry()
    return _hook_registry
