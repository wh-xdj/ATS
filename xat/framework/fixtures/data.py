# -*- coding: utf-8 -*-
"""测试数据fixtures"""
import pytest
from typing import Dict, Any
from datetime import datetime
import uuid


@pytest.fixture(scope="function")
def sample_project(db_session, test_user):
    """创建示例项目数据"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import Project
    
    project = Project(
        id=str(uuid.uuid4()),
        name="测试项目",
        description="这是一个测试项目",
        owner_id=test_user.id,
        status="active",
        created_by=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "owner_id": project.owner_id,
    }


@pytest.fixture(scope="function")
def sample_module(db_session, sample_project):
    """创建示例模块数据"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import Module
    
    module = Module(
        id=str(uuid.uuid4()),
        name="测试模块",
        description="这是一个测试模块",
        project_id=sample_project["id"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)
    
    return {
        "id": module.id,
        "name": module.name,
        "description": module.description,
        "project_id": module.project_id,
    }


@pytest.fixture(scope="function")
def sample_test_case(db_session, sample_project, test_user):
    """创建示例测试用例数据"""
    import sys
    from pathlib import Path
    
    backend_path = Path(__file__).parent.parent.parent.parent / "backend"
    if not backend_path.exists():
        pytest.skip("Backend directory not found")
    
    sys.path.insert(0, str(backend_path))
    from models import TestCase
    
    test_case = TestCase(
        id=str(uuid.uuid4()),
        case_code="TC001",
        name="测试用例标题",
        type="functional",
        priority="P1",
        project_id=sample_project["id"],
        steps=[],
        created_by=test_user.id,
        status="not_executed",
        is_automated=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(test_case)
    db_session.commit()
    db_session.refresh(test_case)
    
    return {
        "id": test_case.id,
        "case_code": test_case.case_code,
        "name": test_case.name,
        "type": test_case.type,
        "priority": test_case.priority,
        "project_id": test_case.project_id,
    }

