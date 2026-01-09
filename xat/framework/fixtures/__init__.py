# -*- coding: utf-8 -*-
"""Pytest fixtures模块 - 统一导出所有fixtures"""
from .database import (
    test_db,
    db_session,
    db_engine,
    test_database,
)
from .client import (
    test_client,
    async_client,
)
from .auth import (
    test_user,
    admin_user,
    auth_headers,
    admin_auth_headers,
)
from .data import (
    sample_project,
    sample_test_case,
    sample_module,
)

__all__ = [
    # Database fixtures
    "test_db",
    "db_session",
    "db_engine",
    "test_database",
    # Client fixtures
    "test_client",
    "async_client",
    # Auth fixtures
    "test_user",
    "admin_user",
    "auth_headers",
    "admin_auth_headers",
    # Data fixtures
    "sample_project",
    "sample_test_case",
    "sample_module",
]

