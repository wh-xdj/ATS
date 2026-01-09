# -*- coding: utf-8 -*-
"""测试辅助函数"""
from typing import Dict, Any, Optional
from httpx import Response


def assert_response_success(
    response: Response,
    expected_status: int = 200,
    expected_keys: Optional[list] = None
) -> Dict[str, Any]:
    """断言响应成功"""
    assert response.status_code == expected_status, \
        f"期望状态码 {expected_status}，实际 {response.status_code}，响应: {response.text}"
    
    data = response.json()
    
    if expected_keys:
        for key in expected_keys:
            assert key in data, f"响应中缺少键: {key}"
    
    return data


def assert_response_error(
    response: Response,
    expected_status: int = 400,
    expected_message: Optional[str] = None
) -> Dict[str, Any]:
    """断言响应错误"""
    assert response.status_code == expected_status, \
        f"期望错误状态码 {expected_status}，实际 {response.status_code}"
    
    data = response.json()
    
    if expected_message:
        assert expected_message in str(data), \
            f"期望错误消息包含 '{expected_message}'，实际: {data}"
    
    return data


def create_test_user(
    db_session,
    username: str = "test_user",
    email: str = "test@example.com",
    **kwargs
):
    """创建测试用户的辅助函数"""
    import sys
    from pathlib import Path
    from datetime import datetime
    import uuid
    import bcrypt
    
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        raise RuntimeError("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import User
    
    hashed_password = bcrypt.hashpw(
        kwargs.get("password", "test_password").encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")
    
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        password_hash=hashed_password,
        status=kwargs.get("status", True),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **{k: v for k, v in kwargs.items() if k not in ["password", "status"]}
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_project(
    db_session,
    owner_id: str,
    name: str = "测试项目",
    **kwargs
):
    """创建测试项目的辅助函数"""
    import sys
    from pathlib import Path
    from datetime import datetime
    import uuid
    
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        raise RuntimeError("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import Project
    
    project = Project(
        id=str(uuid.uuid4()),
        name=name,
        description=kwargs.get("description", "测试项目描述"),
        owner_id=owner_id,
        status=kwargs.get("status", "active"),
        created_by=kwargs.get("created_by", owner_id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **{k: v for k, v in kwargs.items() if k not in ["description", "status", "created_by"]}
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

