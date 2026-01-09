# -*- coding: utf-8 -*-
"""Collection类Hook实现"""
import pytest
from typing import List
from framework.hooks.base import CollectionHook


class CollectionModifyItemsHook(CollectionHook):
    """Collection修改Hook - 基础实现"""
    
    def execute(
        self,
        config: pytest.Config,
        items: List[pytest.Item]
    ) -> None:
        """执行collection修改"""
        if not self.enabled:
            return
        
        print(f"[Hook] {self.name}: 收集到 {len(items)} 个测试项")


class TestMarkerHook(CollectionHook):
    """自动添加测试标记Hook"""
    
    def execute(
        self,
        config: pytest.Config,
        items: List[pytest.Item]
    ) -> None:
        """自动为测试添加标记"""
        if not self.enabled:
            return
        
        marked_count = 0
        
        for item in items:
            # 如果测试没有标记，根据路径添加默认标记
            if not any(item.iter_markers()):
                # 根据路径判断测试类型
                path_str = str(item.fspath)
                
                if "integration" in path_str or "integration" in path_str.lower():
                    item.add_marker(pytest.mark.integration)
                    marked_count += 1
                elif "unit" in path_str or "unit" in path_str.lower():
                    item.add_marker(pytest.mark.unit)
                    marked_count += 1
                
                # 默认添加asyncio标记（如果是async测试）
                if hasattr(item, 'function') and hasattr(item.function, '__code__'):
                    if 'async' in str(item.function.__code__.co_flags):
                        item.add_marker(pytest.mark.asyncio)
        
        if marked_count > 0:
            print(f"[Hook] {self.name}: 为 {marked_count} 个测试添加了标记")


class TestSorterHook(CollectionHook):
    """测试排序Hook"""
    
    def __init__(self, sort_by: str = "path"):
        """
        初始化排序Hook
        
        Args:
            sort_by: 排序方式 ("path", "name", "marker")
        """
        super().__init__("TestSorter")
        self.sort_by = sort_by
    
    def execute(
        self,
        config: pytest.Config,
        items: List[pytest.Item]
    ) -> None:
        """对测试进行排序"""
        if not self.enabled:
            return
        
        if self.sort_by == "path":
            items.sort(key=lambda x: str(x.fspath))
        elif self.sort_by == "name":
            items.sort(key=lambda x: x.name)
        elif self.sort_by == "marker":
            # 有slow标记的测试排在后面
            items.sort(key=lambda x: (
                "slow" in [m.name for m in x.iter_markers()],
                str(x.fspath)
            ))
        
        print(f"[Hook] {self.name}: 按 {self.sort_by} 排序了 {len(items)} 个测试")

