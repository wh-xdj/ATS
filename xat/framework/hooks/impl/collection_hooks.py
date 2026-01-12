# -*- coding: utf-8 -*-
"""Collection类Hook实现"""
import pytest
import json
from typing import List, Optional
from pathlib import Path
from framework.hooks.base import CollectionHook
from framework.logger import get_logger


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
        
        logger = get_logger()
        logger.debug(f"[Hook] {self.name}: 收集到 {len(items)} 个测试项")


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
            logger = get_logger()
            logger.debug(f"[Hook] {self.name}: 为 {marked_count} 个测试添加了标记")


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
        
        logger = get_logger()
        logger.debug(f"[Hook] {self.name}: 按 {self.sort_by} 排序了 {len(items)} 个测试")


class TestCaseFilterHook(CollectionHook):
    """用例筛选Hook - 根据test_cases.json文件筛选需要执行的用例"""
    
    def __init__(self):
        super().__init__("TestCaseFilter")
        self.case_codes = self._load_case_codes_from_file()
    
    def _load_case_codes_from_file(self) -> set:
        """从test_cases.json文件加载需要执行的case_codes"""
        possible_paths = [
            Path("test_cases.json"),  # 当前工作目录
            Path(__file__).parent.parent.parent / "test_cases.json",  # xat根目录
        ]
        
        for json_file in possible_paths:
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        case_codes = data.get("case_codes", [])
                        if isinstance(case_codes, list):
                            # 转换为set以便快速查找
                            return {str(code) for code in case_codes}
                except (json.JSONDecodeError, IOError, KeyError) as e:
                    logger = get_logger()
                    logger.warning(f"[Hook] {self.name}: 读取用例文件失败 {json_file}: {e}")
        
        return set()
    
    def _extract_case_code_from_test_name(self, test_name: str) -> Optional[str]:
        """
        从测试用例名称中提取case_code
        
        用例命名格式: test_caseid_6位唯一数字
        例如: test_caseid_000001 -> 000001
        
        Args:
            test_name: 测试用例名称
            
        Returns:
            提取的用例编号（6位数字），如果无法提取则返回None
        """
        import re
        
        # 匹配 test_caseid_ 后面的6位数字
        pattern = r'test_caseid_(\d{6})'
        match = re.search(pattern, test_name)
        if match:
            return match.group(1)
        return None
    
    def execute(
        self,
        config: pytest.Config,
        items: List[pytest.Item]
    ) -> None:
        """执行用例筛选"""
        if not self.enabled:
            return
        
        logger = get_logger()
        
        # 如果没有指定case_codes，不进行筛选
        if not self.case_codes:
            logger.debug(f"[Hook] {self.name}: 未找到test_cases.json文件或case_codes为空，不进行筛选")
            return
        
        logger.info(f"[Hook] {self.name}: 开始筛选用例，目标case_codes: {self.case_codes}")
        
        # 筛选用例
        filtered_items = []
        skipped_count = 0
        matched_codes = set()
        
        for item in items:
            # 从测试用例名称中提取case_code
            test_name = item.name
            case_code = self._extract_case_code_from_test_name(test_name)
            
            if case_code and case_code in self.case_codes:
                # 匹配，保留该用例
                filtered_items.append(item)
                matched_codes.add(case_code)
                logger.debug(f"[Hook] {self.name}: 保留用例: {test_name} (case_code={case_code})")
            elif not case_code:
                # 无法提取case_code，保留该用例（兼容没有case_code的用例）
                filtered_items.append(item)
                logger.debug(f"[Hook] {self.name}: 无法提取case_code，保留用例: {test_name}")
            else:
                # 不匹配，跳过该用例
                skipped_count += 1
                logger.debug(f"[Hook] {self.name}: 跳过用例: {test_name} (case_code={case_code})")
        
        # 更新items列表（只保留筛选后的用例）
        items[:] = filtered_items
        
        # 检查是否有未匹配的case_codes
        unmatched_codes = self.case_codes - matched_codes
        if unmatched_codes:
            logger.warning(f"[Hook] {self.name}: 以下case_codes未找到对应的测试用例: {unmatched_codes}")
        
        logger.info(f"[Hook] {self.name}: 筛选完成，保留 {len(filtered_items)} 个用例，跳过 {skipped_count} 个用例，匹配 {len(matched_codes)} 个case_code")

