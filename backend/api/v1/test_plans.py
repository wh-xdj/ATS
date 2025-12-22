"""测试计划相关 API（独立 URL 前缀）"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import APIResponse, ResponseStatus
from api.deps import get_current_user
from models import User


router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_test_plans(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    owner_id: Optional[str] = None,
):
    """获取测试计划列表（按项目过滤）"""
    # TODO: 使用 SQLAlchemy 从数据库查询真实数据
    items = [
        {
            "id": "plan_1",
            "projectId": project_id,
            "planNumber": "TP-001",
            "name": "示例测试计划 001",
            "description": "这是一个示例测试计划",
            "ownerId": str(current_user.id) if current_user else "user_1",
            "planType": "manual",
            "startDate": "2024-01-01",
            "endDate": "2024-01-31",
            "status": "not_started",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00",
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


@router.get("/{plan_id}", response_model=APIResponse)
async def get_test_plan(
    plan_id: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取测试计划详情"""
    # TODO: 使用 SQLAlchemy 从数据库查询真实数据
    plan = {
        "id": plan_id,
        "projectId": project_id or "project_1",
        "planNumber": "TP-001",
        "name": "示例测试计划 001",
        "description": "这是一个示例测试计划",
        "ownerId": str(current_user.id) if current_user else "user_1",
        "planType": "manual",
        "startDate": "2024-01-01",
        "endDate": "2024-01-31",
        "status": "not_started",
        "createdAt": "2024-01-01T00:00:00",
        "updatedAt": "2024-01-01T00:00:00",
    }

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=plan,
    )


@router.post("", response_model=APIResponse)
async def create_test_plan(
    plan_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建测试计划"""
    import uuid

    plan_id = str(uuid.uuid4())

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data={
            "id": plan_id,
            "projectId": plan_data.get("project_id") or "project_1",
            "planNumber": plan_data.get("planNumber") or f"TP-{plan_id[:8]}",
            "name": plan_data.get("name") or "新测试计划",
            "description": plan_data.get("description"),
            "ownerId": str(current_user.id) if current_user else "user_1",
            "planType": plan_data.get("planType") or "manual",
            "startDate": plan_data.get("startDate"),
            "endDate": plan_data.get("endDate"),
            "status": "not_started",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00",
        },
    )


@router.put("/{plan_id}", response_model=APIResponse)
async def update_test_plan(
    plan_id: str,
    plan_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新测试计划"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data={
            "id": plan_id,
            "name": plan_data.get("name") or "测试计划",
            "description": plan_data.get("description"),
            "status": plan_data.get("status") or "not_started",
        },
    )


@router.delete("/{plan_id}", response_model=APIResponse)
async def delete_test_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除测试计划"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功",
    )


@router.get("/{plan_id}/cases", response_model=APIResponse)
async def get_plan_cases(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取计划关联的用例列表"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=[],
    )


@router.post("/{plan_id}/cases", response_model=APIResponse)
async def add_cases_to_plan(
    plan_id: str,
    case_ids: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向计划添加用例"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="添加成功",
    )


@router.delete("/{plan_id}/cases", response_model=APIResponse)
async def remove_cases_from_plan(
    plan_id: str,
    case_ids: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从计划移除用例"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="移除成功",
    )


@router.post("/{plan_id}/pause", response_model=APIResponse)
async def pause_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """暂停计划"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="暂停成功",
    )


@router.post("/{plan_id}/resume", response_model=APIResponse)
async def resume_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """恢复计划"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="恢复成功",
    )


@router.post("/{plan_id}/complete", response_model=APIResponse)
async def complete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """完成计划"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="完成成功",
    )


@router.post("/{plan_id}/execute", response_model=APIResponse)
async def execute_plan(
    plan_id: str,
    execution_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """执行计划"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="执行已启动",
    )


@router.post("/{plan_id}/stop", response_model=APIResponse)
async def stop_plan_execution(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """停止计划执行"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="停止成功",
    )


@router.get("/{plan_id}/executions", response_model=APIResponse)
async def get_plan_executions(
    plan_id: str,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取计划的执行历史"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "items": [],
            "total": 0,
            "page": page,
            "size": size,
        },
    )


@router.post("/{plan_id}/clone", response_model=APIResponse)
async def clone_plan(
    plan_id: str,
    clone_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """克隆计划"""
    import uuid

    new_plan_id = str(uuid.uuid4())
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="克隆成功",
        data={"id": new_plan_id},
    )

