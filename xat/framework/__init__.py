# -*- coding: utf-8 -*-
"""Pytest测试框架主入口"""
from framework.config import TestConfig, get_test_config
from framework.logger import (
    get_logger,
    log_debug,
    log_info,
    log_warning,
    log_error,
    log_critical,
)
from framework.hooks import (
    pytest_configure,
    pytest_sessionstart,
    pytest_sessionfinish,
    pytest_collection_modifyitems,
    pytest_runtest_setup,
    pytest_runtest_teardown,
    pytest_runtest_logreport,
    get_hook_registry,
)

# 注意：fixtures模块已被删除，如果需要可以重新创建
# from framework.fixtures import (
#     # Database
#     test_db,
#     db_session,
#     db_engine,
#     test_database,
#     # Client
#     test_client,
#     async_client,
#     # Auth
#     test_user,
#     admin_user,
#     auth_headers,
#     admin_auth_headers,
#     # Data
#     sample_project,
#     sample_test_case,
#     sample_module,
# )

from framework.utils import (
    assert_response_success,
    assert_response_error,
    create_test_user,
    create_test_project,
    attach_screenshot,
    attach_text,
    attach_json,
    attach_html,
    step,
    label,
    description,
    severity,
)

__all__ = [
    # Config
    "TestConfig",
    "get_test_config",
    # Logger
    "get_logger",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_critical",
    # Hooks
    "pytest_configure",
    "pytest_sessionstart",
    "pytest_sessionfinish",
    "pytest_collection_modifyitems",
    "pytest_runtest_setup",
    "pytest_runtest_teardown",
    "pytest_runtest_logreport",
    "get_hook_registry",
    # Utils
    "assert_response_success",
    "assert_response_error",
    "create_test_user",
    "create_test_project",
    # Allure Utils
    "attach_screenshot",
    "attach_text",
    "attach_json",
    "attach_html",
    "step",
    "label",
    "description",
    "severity",
]
