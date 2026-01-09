# -*- coding: utf-8 -*-
"""Pytest测试框架主入口"""
from framework.config import TestConfig, get_test_config
from framework.hooks import (
    pytest_configure,
    pytest_sessionstart,
    pytest_sessionfinish,
    pytest_collection_modifyitems,
    get_hook_registry,
)
from framework.fixtures import (
    # Database
    test_db,
    db_session,
    db_engine,
    test_database,
    # Client
    test_client,
    async_client,
    # Auth
    test_user,
    admin_user,
    auth_headers,
    admin_auth_headers,
    # Data
    sample_project,
    sample_test_case,
    sample_module,
)
from framework.utils import (
    assert_response_success,
    assert_response_error,
    create_test_user,
    create_test_project,
)

__all__ = [
    # Config
    "TestConfig",
    "get_test_config",
    # Hooks
    "pytest_configure",
    "pytest_sessionstart",
    "pytest_sessionfinish",
    "pytest_collection_modifyitems",
    "get_hook_registry",
    # Fixtures
    "test_db",
    "db_session",
    "db_engine",
    "test_database",
    "test_client",
    "async_client",
    "test_user",
    "admin_user",
    "auth_headers",
    "admin_auth_headers",
    "sample_project",
    "sample_test_case",
    "sample_module",
    # Utils
    "assert_response_success",
    "assert_response_error",
    "create_test_user",
    "create_test_project",
]

