# -*- coding: utf-8 -*-
"""FastAPI客户端相关fixtures"""
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from framework.config import get_test_config


@pytest.fixture(scope="function")
def test_client(db_session) -> TestClient:
    """同步测试客户端（用于同步测试）"""
    import sys
    from pathlib import Path
    
    # 添加backend目录到路径
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from main import app
    from database import get_db
    
    # 覆盖数据库依赖
    def override_get_db():
        """覆盖数据库依赖"""
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # 清理覆盖
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端（用于异步测试）"""
    import sys
    from pathlib import Path
    
    # 添加backend目录到路径
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from main import app
    from database import get_db
    
    # 覆盖数据库依赖
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    config = get_test_config()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=config.TEST_CLIENT_BASE_URL
    ) as client:
        yield client
    
    # 清理覆盖
    app.dependency_overrides.clear()

