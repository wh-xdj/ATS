"""项目相关API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Project
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from schemas.common import APIResponse, ResponseStatus
from api.deps import get_current_user
from models import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    projects = [
        {
            "id": "project_1",
            "name": "项目A",
            "description": "这是项目A的描述",
            "ownerId": str(current_user.id) if current_user else "user_1",
            "status": "active",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00",
            "createdBy": str(current_user.id) if current_user else "user_1"
        },
        {
            "id": "project_2",
            "name": "项目B",
            "description": "这是项目B的描述",
            "ownerId": str(current_user.id) if current_user else "user_1",
            "status": "active",
            "createdAt": "2024-01-02T00:00:00",
            "updatedAt": "2024-01-02T00:00:00",
            "createdBy": str(current_user.id) if current_user else "user_1"
        }
    ]
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=projects
    )


@router.get("/{project_id}", response_model=APIResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情"""
    # TODO: 从数据库获取真实数据
    project = {
        "id": str(project_id),
        "name": "项目详情",
        "description": "这是项目的详细描述",
        "ownerId": str(current_user.id) if current_user else "user_1",
        "status": "active",
        "createdAt": "2024-01-01T00:00:00",
        "updatedAt": "2024-01-01T00:00:00",
        "createdBy": str(current_user.id) if current_user else "user_1"
    }
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=project
    )


@router.post("", response_model=APIResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目"""
    # 使用当前登录用户的 ID 作为 owner_id（如果未提供）
    owner_id = project_data.owner_id if project_data.owner_id else current_user.id
    
    # TODO: 实现真实的创建逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data={
            "id": "project_new",
            "name": project_data.name,
            "description": project_data.description,
            "ownerId": str(owner_id),
            "status": "active",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00",
            "createdBy": str(current_user.id) if current_user else "user_1"
        }
    )


@router.put("/{project_id}", response_model=APIResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目"""
    # TODO: 实现真实的更新逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data={
            "id": str(project_id),
            "name": project_data.name or "项目名称",
            "description": project_data.description,
            "status": project_data.status or "active"
        }
    )


@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目"""
    # TODO: 实现真实的删除逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )


@router.get("/{project_id}/modules", response_model=APIResponse)
async def get_project_modules(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目模块列表"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    modules = [
        {
            "id": "module_1",
            "projectId": str(project_id),
            "name": "模块A",
            "parentId": None,
            "level": 1,
            "sortOrder": 0,
            "description": "模块A的描述",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        },
        {
            "id": "module_2",
            "projectId": str(project_id),
            "name": "模块B",
            "parentId": None,
            "level": 1,
            "sortOrder": 1,
            "description": "模块B的描述",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        },
        {
            "id": "module_3",
            "projectId": str(project_id),
            "name": "子模块A-1",
            "parentId": "module_1",
            "level": 2,
            "sortOrder": 0,
            "description": "子模块A-1的描述",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        }
    ]
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=modules
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

