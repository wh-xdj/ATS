"""测试用例相关 API（独立 URL 前缀）"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import APIResponse, ResponseStatus
from schemas.test_case import TestCaseCreate, TestCaseUpdate
from api.deps import get_current_user
from models import User


router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_test_cases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    module_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    type: Optional[str] = None,
):
    """获取测试用例列表（按项目过滤）

    注意：当前实现仍返回模拟数据，后续可接入真实数据库查询。
    """
    # TODO: 使用 SQLAlchemy 从数据库查询真实数据
    items = [
        {
            "id": "case_1",
            "projectId": project_id,
            "moduleId": "module_1",
            "caseCode": "TC-001",
            "name": "示例测试用例 001",
            "type": "functional",
            "priority": "P0",
            "precondition": "前置条件示例",
            "steps": [
                {"step": 1, "action": "打开页面", "expected": "页面正常展示"},
                {"step": 2, "action": "输入用户名密码", "expected": "可以正常输入"},
            ],
            "expectedResult": "登录成功",
            "requirementRef": "REQ-001",
            "modulePath": "未规划用例",
            "tags": ["回归", "冒烟"],
            "status": "not_executed",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00",
            "createdBy": "Administrator",
            "updatedBy": "Administrator",
        }
    ]

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "items": items,
            "total": len(items),
            "page": page,
            "size": size,
            "pages": 1,
            "hasNext": False,
            "hasPrev": False,
        },
    )


@router.get("/{case_id}", response_model=APIResponse)
async def get_test_case(
    case_id: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取测试用例详情"""
    # TODO: 使用 SQLAlchemy 从数据库查询真实数据
    case = {
        "id": case_id,
        "projectId": project_id or "project_1",
        "moduleId": "module_1",
        "caseCode": "TC-001",
        "name": "示例测试用例 001",
        "type": "functional",
        "priority": "P0",
        "precondition": "前置条件示例",
        "steps": [
            {"step": 1, "action": "打开页面", "expected": "页面正常展示"},
            {"step": 2, "action": "输入用户名密码", "expected": "可以正常输入"},
        ],
        "expectedResult": "登录成功",
        "requirementRef": "REQ-001",
        "modulePath": "未规划用例",
        "tags": ["回归", "冒烟"],
        "status": "not_executed",
        "createdAt": "2024-01-01T00:00:00",
        "updatedAt": "2024-01-01T00:00:00",
        "createdBy": "Administrator",
        "updatedBy": "Administrator",
    }

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=case,
    )


@router.post("", response_model=APIResponse)
async def create_test_case(
    case_data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建测试用例

    当前为模拟实现，只回显提交的数据并补充字段。
    """
    import uuid

    case_id = str(uuid.uuid4())

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data={
            "id": case_id,
            "projectId": str(case_data.project_id) if case_data.project_id else "project_1",
            "moduleId": str(case_data.module_id) if case_data.module_id else None,
            "caseCode": case_data.case_code,
            "name": case_data.name,
            "type": case_data.type,
            "priority": case_data.priority,
            "precondition": case_data.precondition,
            "steps": case_data.steps,
            "expectedResult": case_data.expected_result,
            "requirementRef": case_data.requirement_ref,
            "modulePath": case_data.module_path,
            "tags": case_data.tags or [],
            "status": "not_executed",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00",
            "createdBy": str(current_user.id) if current_user else "user_1",
            "updatedBy": str(current_user.id) if current_user else "user_1",
        },
    )


@router.put("/{case_id}", response_model=APIResponse)
async def update_test_case(
    case_id: str,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新测试用例（模拟实现）"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data={
            "id": case_id,
            "name": case_data.name or "测试用例",
            "type": case_data.type or "functional",
            "priority": case_data.priority or "P2",
            "precondition": case_data.precondition,
            "steps": case_data.steps or [],
            "expectedResult": case_data.expected_result,
            "status": case_data.status or "not_executed",
            "tags": case_data.tags or [],
        },
    )


@router.delete("/{case_id}", response_model=APIResponse)
async def delete_test_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除测试用例（模拟实现）"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功",
    )


@router.get("/case-tree", response_model=APIResponse)
async def get_case_tree(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用例树（包含模块和用例）

    当前为模拟数据，结构与前端期望保持一致。
    """
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
                    "tags": ["回归", "冒烟"],
                },
                {
                    "key": "case_2",
                    "title": "测试用例002",
                    "type": "case",
                    "caseCode": "TC-002",
                    "level": "P1",
                    "tags": ["功能"],
                },
            ],
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
                    "tags": ["接口"],
                }
            ],
        },
        {
            "key": "case_4",
            "title": "测试用例004（无模块）",
            "type": "case",
            "caseCode": "TC-004",
            "level": "P2",
            "tags": ["UI"],
        },
    ]

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=tree_data,
    )


