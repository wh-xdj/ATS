# -*- coding: utf-8 -*-
"""Hook基类定义"""
from abc import ABC, abstractmethod
from typing import Any, Optional
import pytest


class BaseHook(ABC):
    """Hook基类 - 所有hook的抽象基类"""
    
    def __init__(self, name: Optional[str] = None):
        """
        初始化Hook
        
        Args:
            name: Hook名称，用于日志和调试
        """
        self.name = name or self.__class__.__name__
        self.enabled = True
    
    @property
    @abstractmethod
    def hook_name(self) -> str:
        """返回pytest hook函数名（如 pytest_configure）"""
        pass
    
    def enable(self) -> None:
        """启用hook"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用hook"""
        self.enabled = False
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, enabled={self.enabled})>"


class ConfigHook(BaseHook):
    """配置类Hook基类 - 对应pytest_configure"""
    
    @property
    def hook_name(self) -> str:
        return "pytest_configure"
    
    @abstractmethod
    def execute(self, config: pytest.Config) -> None:
        """
        执行配置hook
        
        Args:
            config: pytest配置对象
        """
        pass


class SessionHook(BaseHook):
    """Session类Hook基类"""
    
    @abstractmethod
    def execute(self, session: pytest.Session) -> None:
        """
        执行session hook
        
        Args:
            session: pytest session对象
        """
        pass


class SessionStartHook(SessionHook):
    """Session开始Hook"""
    
    @property
    def hook_name(self) -> str:
        return "pytest_sessionstart"


class SessionFinishHook(SessionHook):
    """Session结束Hook"""
    
    @property
    def hook_name(self) -> str:
        return "pytest_sessionfinish"


class CollectionHook(BaseHook):
    """Collection类Hook基类"""
    
    @property
    def hook_name(self) -> str:
        return "pytest_collection_modifyitems"
    
    @abstractmethod
    def execute(
        self,
        config: pytest.Config,
        items: list[pytest.Item]
    ) -> None:
        """
        执行collection hook
        
        Args:
            config: pytest配置对象
            items: 测试项列表
        """
        pass


class TestHook(BaseHook):
    """测试用例类Hook基类"""
    
    @abstractmethod
    def execute(self, item: pytest.Item) -> None:
        """
        执行测试hook
        
        Args:
            item: 测试项对象
        """
        pass


class TestSetupHook(TestHook):
    """测试用例开始Hook - pytest_runtest_setup"""
    
    @property
    def hook_name(self) -> str:
        return "pytest_runtest_setup"
    
    @abstractmethod
    def execute(self, item: pytest.Item) -> None:
        """执行测试开始hook"""
        pass


class TestTeardownHook(TestHook):
    """测试用例结束Hook - pytest_runtest_teardown"""
    
    @property
    def hook_name(self) -> str:
        return "pytest_runtest_teardown"
    
    @abstractmethod
    def execute(self, item: pytest.Item) -> None:
        """执行测试结束hook"""
        pass


class TestCallHook(TestHook):
    """测试用例调用Hook - pytest_runtest_call"""
    
    @property
    def hook_name(self) -> str:
        return "pytest_runtest_call"
    
    @abstractmethod
    def execute(self, item: pytest.Item) -> None:
        """执行测试调用hook"""
        pass
