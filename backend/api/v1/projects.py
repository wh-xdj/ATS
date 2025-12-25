# -*- coding: utf-8 -*-
"""项目相关API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Project
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from schemas.module import ModuleCreate, ModuleUpdate
from schemas.common import APIResponse, ResponseStatus
from api.deps import get_current_user
from models import User
from utils.serializer import serialize_model, serialize_list
from services.module_service import ModuleService

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表（使用数据库持久化）"""
    # 查询所有项目，按创建时间倒序
    query = db.query(Project).order_by(Project.created_at.desc())
    items = query.all()

    # 获取所有相关的用户ID
    user_ids = set()
    for item in items:
        if item.created_by:
            user_ids.add(item.created_by)
        if item.owner_id:
            user_ids.add(item.owner_id)
    
    # 批量查询用户信息
    users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    user_map = {str(u.id): u.username or u.email or str(u.id) for u in users}
    
    # 构建项目列表，包含用户名
    project_list = []
    for item in items:
        project_data = serialize_model(item, camel_case=True)
        # 添加用户名字段
        project_data['createdByName'] = user_map.get(item.created_by, 'Unknown')
        project_data['updatedByName'] = user_map.get(item.owner_id, user_map.get(item.created_by, 'Unknown'))
        project_list.append(project_data)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=project_list,
    )


@router.get("/{project_id}", response_model=APIResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情（数据库）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    # 使用序列化器统一转换为camelCase
    data = serialize_model(project, camel_case=True)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=data,
    )


@router.post("", response_model=APIResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目（写入数据库）"""
    owner_id = str(project_data.owner_id) if project_data.owner_id else str(current_user.id)

    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id,
        status="active",
        created_by=str(current_user.id),
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "ownerId": project.owner_id,
        "status": project.status,
        "createdAt": project.created_at.isoformat() if project.created_at else "",
        "updatedAt": project.updated_at.isoformat() if project.updated_at else "",
        "createdBy": project.created_by or project.owner_id,
    }

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data=data,
    )


@router.put("/{project_id}", response_model=APIResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目（数据库）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.status is not None:
        project.status = project_data.status

    db.commit()
    db.refresh(project)

    data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "ownerId": project.owner_id,
        "status": project.status,
        "createdAt": project.created_at.isoformat() if project.created_at else "",
        "updatedAt": project.updated_at.isoformat() if project.updated_at else "",
        "createdBy": project.created_by or project.owner_id,
    }

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=data,
    )


@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目（数据库，级联删除测试用例等）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    db.delete(project)
    db.commit()

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功",
    )


@router.get("/{project_id}/modules", response_model=APIResponse)
async def get_project_modules(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目模块列表（数据库持久化，包含用例数量）"""
    module_list, total_case_count = ModuleService.get_modules_with_case_count(db, project_id)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "modules": module_list,
            "totalCaseCount": total_case_count
        }
    )


@router.post("/{project_id}/modules", response_model=APIResponse)
async def create_module(
    project_id: str,
    module_data: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建模块（数据库持久化）"""
    try:
        module = ModuleService.create_module(
            db=db,
            project_id=project_id,
            module_data=module_data,
            current_user_id=str(current_user.id)
        )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="创建成功",
            data=serialize_model(module, camel_case=True)
        )
    except Exception as e:
        import traceback
        print("创建模块失败:", traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")


@router.put("/{project_id}/modules/{module_id}", response_model=APIResponse)
async def update_module(
    project_id: str,
    module_id: str,
    module_data: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模块（数据库持久化）"""
    module = ModuleService.update_module(
        db=db,
        module_id=module_id,
        module_data=module_data,
        current_user_id=str(current_user.id)
    )
    
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=serialize_model(module, camel_case=True)
    )


@router.delete("/{project_id}/modules/{module_id}", response_model=APIResponse)
async def delete_module(
    project_id: str,
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模块（数据库持久化）"""
    success = ModuleService.delete_module(db=db, module_id=module_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )


@router.get("/{project_id}/case-tree", response_model=APIResponse)
async def get_case_tree(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用例树（包含模块和用例）"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    tree_data = [
        {
            "key": "module_1",
            "title": "模块A",
            "type": "module",
            "level": "P0",
            "children": [
                {
                    "key": "case_1",
                    "title": "测试用例001",
                    "type": "case",
                    "caseCode": "TC-001",
                    "level": "P0",
                    "tags": ["回归", "冒烟"]
                },
                {
                    "key": "case_2",
                    "title": "测试用例002",
                    "type": "case",
                    "caseCode": "TC-002",
                    "level": "P1",
                    "tags": ["功能"]
                }
            ]
        },
        {
            "key": "module_2",
            "title": "模块B",
            "type": "module",
            "level": "P1",
            "children": [
                {
                    "key": "case_3",
                    "title": "测试用例003",
                    "type": "case",
                    "caseCode": "TC-003",
                    "level": "P1",
                    "tags": ["接口"]
                }
            ]
        },
        {
            "key": "case_4",
            "title": "测试用例004（无模块）",
            "type": "case",
            "caseCode": "TC-004",
            "level": "P2",
            "tags": ["UI"]
        }
    ]
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=tree_data
    )


# 测试用例相关路由
@router.get("/{project_id}/cases", response_model=APIResponse)
async def get_test_cases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    search: str = None,
    module_id: str = None,
    status: str = None,
    priority: str = None,
    type: str = None
):
    """获取测试用例列表"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    cases = [
        {
            "id": "case_1",
            "projectId": str(project_id),
            "moduleId": "module_1",
            "caseCode": "TC-001",
            "name": "测试用例001",
            "type": "functional",
            "priority": "P0",
            "status": "not_executed",
            "tags": ["回归", "冒烟"],
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        }
    ]
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "items": cases,
            "total": len(cases),
            "page": page,
            "size": size,
            "pages": 1,
            "hasNext": False,
            "hasPrev": False
        }
    )


@router.get("/{project_id}/cases/{case_id}", response_model=APIResponse)
async def get_test_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取测试用例详情"""
    # TODO: 从数据库获取真实数据
    case = {
        "id": str(case_id),
        "projectId": str(project_id),
        "moduleId": "module_1",
        "caseCode": "TC-001",
        "name": "测试用例001",
        "type": "functional",
        "priority": "P0",
        "precondition": "前置条件说明",
        "steps": [
            {"step": 1, "action": "打开登录页面", "expected": "页面正常显示"},
            {"step": 2, "action": "输入用户名和密码", "expected": "输入成功"}
        ],
        "expectedResult": "登录成功",
        "requirementRef": "REQ-001",
        "status": "not_executed",
        "tags": ["回归", "冒烟"],
        "createdAt": "2024-01-01T00:00:00",
        "updatedAt": "2024-01-01T00:00:00"
    }
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=case
    )


@router.post("/{project_id}/cases", response_model=APIResponse)
async def create_test_case(
    project_id: str,
    case_data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建测试用例"""
    # TODO: 实现真实的创建逻辑
    import uuid
    case_id = str(uuid.uuid4())
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data={
            "id": case_id,
            "projectId": str(project_id),
            "moduleId": str(case_data.module_id) if case_data.module_id else None,
            "caseCode": case_data.case_code,
            "name": case_data.name,
            "type": case_data.type,
            "priority": case_data.priority,
            "precondition": case_data.precondition,
            "steps": case_data.steps,
            "expectedResult": case_data.expected_result,
            "requirementRef": case_data.requirement_ref,
            "tags": case_data.tags or [],
            "status": "not_executed",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        }
    )


@router.put("/{project_id}/cases/{case_id}", response_model=APIResponse)
async def update_test_case(
    project_id: str,
    case_id: str,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新测试用例"""
    # TODO: 实现真实的更新逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data={
            "id": str(case_id),
            "projectId": str(project_id),
            "name": case_data.name or "测试用例",
            "type": case_data.type or "functional",
            "priority": case_data.priority or "P2",
            "status": case_data.status or "not_executed",
            "tags": case_data.tags or []
        }
    )


@router.delete("/{project_id}/cases/{case_id}", response_model=APIResponse)
async def delete_test_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除测试用例"""
    # TODO: 实现真实的删除逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )

