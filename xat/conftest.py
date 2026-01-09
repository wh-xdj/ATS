# -*- coding: utf-8 -*-
"""Pytest配置文件 - 从framework导入所有hooks和fixtures"""
# 导入所有hooks（pytest会自动发现）
from framework.hooks import (
    pytest_configure,
    pytest_sessionstart,
    pytest_sessionfinish,
    pytest_collection_modifyitems,
)

# 导入所有fixtures（pytest会自动发现）
from framework.fixtures import (
    # Database fixtures
    test_db,
    db_session,
    db_engine,
    test_database,
    # Client fixtures
    test_client,
    async_client,
    # Auth fixtures
    test_user,
    admin_user,
    auth_headers,
    admin_auth_headers,
    # Data fixtures
    sample_project,
    sample_test_case,
    sample_module,
)

# 这样pytest就能自动发现并使用这些hooks和fixtures

