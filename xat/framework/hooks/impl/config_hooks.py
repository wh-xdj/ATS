# -*- coding: utf-8 -*-
"""配置类Hook实现"""
import pytest
from typing import Optional
from framework.hooks.base import ConfigHook
from framework.config import get_test_config


class PytestConfigureHook(ConfigHook):
    """Pytest配置Hook - 基础配置"""
    
    def execute(self, config: pytest.Config) -> None:
        """执行pytest配置"""
        if not self.enabled:
            return
        
        test_config = get_test_config()
        
        # 设置pytest选项
        if not hasattr(config.option, 'asyncio_mode'):
            config.option.asyncio_mode = "auto"
        
        print(f"[Hook] {self.name}: Pytest配置完成")


class MarkerRegistrationHook(ConfigHook):
    """注册自定义标记Hook"""
    
    def __init__(self, markers: Optional[dict[str, str]] = None):
        """
        初始化标记注册Hook
        
        Args:
            markers: 自定义标记字典 {marker_name: description}
        """
        super().__init__("MarkerRegistration")
        self.markers = markers or self._default_markers()
    
    def _default_markers(self) -> dict[str, str]:
        """默认标记列表"""
        return {
            "slow": "标记为慢速测试（使用 -m 'not slow' 跳过）",
            "integration": "标记为集成测试",
            "unit": "标记为单元测试",
            "database": "标记为需要数据库的测试",
            "auth": "标记为需要认证的测试",
            "api": "标记为API测试",
            "websocket": "标记为WebSocket测试",
        }
    
    def execute(self, config: pytest.Config) -> None:
        """注册所有自定义标记"""
        if not self.enabled:
            return
        
        for marker_name, description in self.markers.items():
            config.addinivalue_line("markers", f"{marker_name}: {description}")
        
        print(f"[Hook] {self.name}: 注册了 {len(self.markers)} 个自定义标记")


class AsyncioConfigHook(ConfigHook):
    """Asyncio配置Hook"""
    
    def execute(self, config: pytest.Config) -> None:
        """配置pytest-asyncio"""
        if not self.enabled:
            return
        
        # 设置asyncio模式
        config.option.asyncio_mode = "auto"
        
        print(f"[Hook] {self.name}: Asyncio配置完成")

