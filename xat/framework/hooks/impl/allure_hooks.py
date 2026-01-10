# -*- coding: utf-8 -*-
"""Allure相关Hook实现"""
import pytest
from typing import Optional
from framework.hooks.base import ConfigHook, TestSetupHook, TestTeardownHook
from framework.config import get_test_config
from framework.logger import get_logger


class AllureConfigHook(ConfigHook):
    """Allure配置Hook"""

    def __init__(self):
        super().__init__("AllureConfig")
        self.allure_enabled = True

    def execute(self, config: pytest.Config) -> None:
        """配置Allure"""
        if not self.enabled:
            return

        logger = get_logger()
        test_config = get_test_config()

        try:
            # 检查allure是否可用
            import allure

            # 设置allure选项 - 使用pytest config.option
            if not hasattr(config.option, 'allure_report_dir') or config.option.allure_report_dir is None:
                config.option.allure_report_dir = test_config.ALLURE_RESULTS_DIR

            # 确保allure-results目录存在
            from pathlib import Path
            allure_dir = Path(config.option.allure_report_dir)
            allure_dir.mkdir(exist_ok=True)

            logger.log_hook_execution(self.name, "Allure配置完成")
            logger.info(f"Allure报告目录: {allure_dir.absolute()}")

        except ImportError:
            logger.warning("Allure未安装，跳过Allure配置")
            self.allure_enabled = False


class AllureTestSetupHook(TestSetupHook):
    """Allure测试用例开始Hook"""

    def execute(self, item: pytest.Item) -> None:
        """记录测试用例开始到Allure"""
        if not self.enabled:
            return

        try:
            import allure
            from framework.logger import get_logger

            logger = get_logger()

            # 获取测试信息
            test_name = item.nodeid
            test_file = str(item.fspath) if hasattr(item, 'fspath') else ""

            # 添加测试步骤到Allure
            with allure.step(f"开始执行测试: {test_name}"):
                # 添加测试描述
                if hasattr(item, 'function') and item.function.__doc__:
                    allure.dynamic.description(item.function.__doc__)

                # 添加测试文件信息
                if test_file:
                    allure.dynamic.label("test_file", test_file)

                # 添加标记信息
                markers = [marker.name for marker in item.iter_markers()]
                if markers:
                    for marker in markers:
                        allure.dynamic.label("marker", marker)

            logger.debug(f"[Allure] 记录测试开始: {test_name}")

        except ImportError:
            pass
        except Exception as e:
            logger = get_logger()
            logger.warning(f"[Allure] 记录测试开始失败: {e}")


class AllureTestTeardownHook(TestTeardownHook):
    """Allure测试用例结束Hook"""

    def execute(self, item: pytest.Item) -> None:
        """记录测试用例结束到Allure"""
        if not self.enabled:
            return

        try:
            import allure
            from framework.logger import get_logger

            logger = get_logger()
            test_name = item.nodeid

            # 测试结束会在pytest_runtest_logreport中处理
            logger.debug(f"[Allure] 测试结束: {test_name}")

        except ImportError:
            pass
        except Exception as e:
            logger = get_logger()
            logger.warning(f"[Allure] 记录测试结束失败: {e}")


class AllureReportHook(ConfigHook):
    """Allure报告生成Hook"""

    def execute(self, config: pytest.Config) -> None:
        """配置Allure报告"""
        if not self.enabled:
            return

        try:
            import allure
            from framework.logger import get_logger
            from framework.config import get_test_config

            logger = get_logger()
            test_config = get_test_config()

            # 设置Allure环境变量
            import os
            os.environ.setdefault("ALLURE_RESULTS_DIR", "allure-results")

            # 添加环境信息到Allure
            allure.dynamic.label("framework", "XAT")
            allure.dynamic.label("environment", test_config.TEST_ENVIRONMENT)

            logger.log_hook_execution(self.name, "Allure报告配置完成")

        except ImportError:
            logger = get_logger()
            logger.warning("Allure未安装，跳过Allure报告配置")
        except Exception as e:
            logger = get_logger()
            logger.warning(f"[Allure] 配置报告失败: {e}")

