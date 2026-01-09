# -*- coding: utf-8 -*-
"""认证相关fixtures"""
import pytest
from typing import Dict
from framework.config import get_test_config


@pytest.fixture(scope="function")
def test_user(db_session):
    """创建测试用户"""
    import sys
    from pathlib import Path
    from datetime import datetime
    import uuid
    import bcrypt
    
    # 添加backend目录到路径
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import User
    
    hashed_password = bcrypt.hashpw(
        "test_password".encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")
    
    user = User(
        id=str(uuid.uuid4()),
        username="test_user",
        email="test@example.com",
        password_hash=hashed_password,
        status=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    """创建管理员用户"""
    import sys
    from pathlib import Path
    from datetime import datetime
    import uuid
    import bcrypt
    
    # 添加backend目录到路径
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import User, Role
    
    # 创建管理员角色（如果不存在）
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(
            id=str(uuid.uuid4()),
            name="admin",
            display_name="管理员",
            description="管理员角色",
            is_system=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(admin_role)
        db_session.commit()
    
    config = get_test_config()
    hashed_password = bcrypt.hashpw(
        config.TEST_ADMIN_PASSWORD.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")
    
    user = User(
        id=str(uuid.uuid4()),
        username=config.TEST_ADMIN_USERNAME,
        email=config.TEST_ADMIN_EMAIL,
        password_hash=hashed_password,
        status=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user) -> Dict[str, str]:
    """生成认证headers（普通用户）"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from core.security import create_access_token
    from config import settings
    
    config = get_test_config()
    # 临时替换JWT密钥
    original_key = settings.JWT_SECRET_KEY
    settings.JWT_SECRET_KEY = config.TEST_JWT_SECRET_KEY
    try:
        access_token = create_access_token(data={"sub": str(test_user.id)})
    finally:
        settings.JWT_SECRET_KEY = original_key
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(admin_user) -> Dict[str, str]:
    """生成管理员认证headers"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from core.security import create_access_token
    from config import settings
    
    config = get_test_config()
    # 临时替换JWT密钥
    original_key = settings.JWT_SECRET_KEY
    settings.JWT_SECRET_KEY = config.TEST_JWT_SECRET_KEY
    try:
        access_token = create_access_token(data={"sub": str(admin_user.id)})
    finally:
        settings.JWT_SECRET_KEY = original_key
    
    return {"Authorization": f"Bearer {access_token}"}

