# -*- coding: utf-8 -*-
"""测试用例相关Hook实现"""
import pytest
import json
import time
import threading
from typing import Optional
from pathlib import Path
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


class TestResultCollectorHook(TestReportHook):
    """测试结果收集Hook - 增量收集测试结果并写入JSON Lines文件"""
    
    def __init__(self):
        super().__init__()
        self._case_ids_map: dict = {}  # case_code -> case_id
        self._result_file: Optional[Path] = None
        self._file_lock = threading.Lock()  # 文件写入锁
        self._load_case_ids_map()
        self._init_result_file()
    
    def _load_case_ids_map(self):
        """从test_cases.json文件加载case_code到case_id的映射"""
        possible_paths = [
            Path("test_cases.json"),
            Path(__file__).parent.parent.parent / "test_cases.json",
        ]
        
        for json_file in possible_paths:
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        case_codes = data.get("case_codes", [])
                        case_ids = data.get("case_ids", [])
                        
                        if len(case_codes) == len(case_ids):
                            self._case_ids_map = {
                                str(code): str(cid) for code, cid in zip(case_codes, case_ids)
                            }
                            logger = get_logger()
                            logger.debug(f"[Hook] {self.name}: 加载了 {len(self._case_ids_map)} 个用例映射")
                except Exception as e:
                    logger = get_logger()
                    logger.warning(f"[Hook] {self.name}: 读取用例映射失败: {e}")
    
    def _init_result_file(self):
        """初始化结果文件（清空或创建）"""
        possible_paths = [
            Path("test_results.jsonl"),
            Path(__file__).parent.parent.parent / "test_results.jsonl",
        ]
        
        for result_file in possible_paths:
            try:
                # 清空文件（如果存在）或创建新文件
                with open(result_file, 'w', encoding='utf-8') as f:
                    pass  # 创建空文件
                self._result_file = result_file
                logger = get_logger()
                logger.debug(f"[Hook] {self.name}: 初始化结果文件: {result_file}")
                break
            except Exception as e:
                logger = get_logger()
                logger.warning(f"[Hook] {self.name}: 初始化结果文件失败: {e}")
    
    def _extract_case_code_from_test_name(self, test_name: str) -> Optional[str]:
        """
        从测试用例名称中提取case_code
        
        用例命名格式: test_caseid_6位唯一数字
        例如: test_caseid_000001 -> 000001
        """
        import re
        # 匹配 test_caseid_ 后面的6位数字
        pattern = r'test_caseid_(\d{6})'
        match = re.search(pattern, test_name)
        if match:
            return match.group(1)
        return None
    
    def log_test_result(self, test_name: str, status: str, duration: float = 0.0, error: str = ""):
        """记录测试结果并立即写入文件（增量）"""
        # 调用父类方法记录日志
        super().log_test_result(test_name, status, duration, error)
        
        # 提取case_code
        case_code = self._extract_case_code_from_test_name(test_name)
        
        # 映射pytest状态到backend状态
        status_map = {
            "PASSED": "passed",
            "FAILED": "failed",
            "SKIPPED": "skipped",
            "ERROR": "error",
        }
        backend_status = status_map.get(status, "error")
        
        # 获取case_id
        case_id = self._case_ids_map.get(case_code) if case_code else None
        
        # 构建结果对象
        result_data = {
            "test_name": test_name,
            "case_code": case_code,
            "case_id": case_id,
            "status": backend_status,
            "duration": duration,
            "error": error[:1000] if error else None,  # 限制错误信息长度
            "timestamp": time.time()  # 添加时间戳
        }
        
        # 立即写入文件（增量追加）
        self._append_result_to_file(result_data)
    
    def _append_result_to_file(self, result_data: dict):
        """将结果追加到JSON Lines文件"""
        if not self._result_file:
            return
        
        try:
            with self._file_lock:
                with open(self._result_file, 'a', encoding='utf-8') as f:
                    # 写入JSON Lines格式（每行一个JSON对象）
                    json_line = json.dumps(result_data, ensure_ascii=False)
                    f.write(json_line + '\n')
                    f.flush()  # 立即刷新到磁盘
            
            logger = get_logger()
            logger.debug(f"[Hook] {self.name}: 已追加测试结果: {result_data.get('test_name')}")
        except Exception as e:
            logger = get_logger()
            logger.error(f"[Hook] {self.name}: 写入测试结果失败: {e}")

