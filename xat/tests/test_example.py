# -*- coding: utf-8 -*-
"""测试示例 - 展示如何使用框架"""
import pytest
from framework.utils import assert_response_success, assert_response_error


@pytest.mark.asyncio
@pytest.mark.api
async def test_example_with_async_client(async_client, admin_auth_headers):
    """使用异步客户端测试API"""
    response = await async_client.get(
        "/api/v1/projects",
        headers=admin_auth_headers
    )
    data = assert_response_success(response, expected_status=200)
    assert "items" in data or "data" in data


@pytest.mark.api
def test_example_with_sync_client(test_client, auth_headers):
    """使用同步客户端测试API"""
    response = test_client.get(
        "/api/v1/projects",
        headers=auth_headers
    )
    data = assert_response_success(response, expected_status=200)
    assert "items" in data or "data" in data


@pytest.mark.database
def test_example_with_database(db_session, sample_project):
    """使用数据库测试"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import Project
    
    project = db_session.query(Project).filter(
        Project.id == sample_project["id"]
    ).first()
    
    assert project is not None
    assert project.name == "测试项目"
    assert project.status == "active"


@pytest.mark.database
def test_example_with_test_data(db_session, sample_project, sample_test_case):
    """使用测试数据fixtures"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import TestCase
    
    test_case = db_session.query(TestCase).filter(
        TestCase.id == sample_test_case["id"]
    ).first()
    
    assert test_case is not None
    assert test_case.case_code == "TC001"
    assert test_case.project_id == sample_project["id"]


@pytest.mark.auth
def test_example_with_auth(test_client, test_user, auth_headers):
    """测试认证功能"""
    # 使用认证headers访问需要认证的端点
    response = test_client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    
    # 验证响应
    if response.status_code == 200:
        data = assert_response_success(response)
        assert data.get("id") == str(test_user.id)
    elif response.status_code == 404:
        # 如果端点不存在，跳过测试
        pytest.skip("Endpoint /api/v1/users/me not found")


@pytest.mark.unit
def test_example_unit_test():
    """单元测试示例 - 不依赖外部资源"""
    from framework.utils import assert_response_success
    
    # 模拟响应对象
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json_data = json_data
        
        def json(self):
            return self._json_data
    
    response = MockResponse(200, {"status": "success", "data": {"id": "123"}})
    data = assert_response_success(response, expected_keys=["status", "data"])
    assert data["data"]["id"] == "123"

