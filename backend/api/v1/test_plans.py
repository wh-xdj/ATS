# -*- coding: utf-8 -*-
"""测试计划相关 API（独立 URL 前缀）- 使用数据库存储"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import APIResponse, ResponseStatus
from api.deps import get_current_user
from models import User
from services.test_plan_service import TestPlanService
from utils.serializer import serialize_model, serialize_list
from core.logger import logger


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
    type: Optional[str] = None,  # 前端使用的参数名
    plan_type: Optional[str] = None,  # 备用参数名
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    owner_id: Optional[str] = None,
):
    """获取测试计划列表（按项目过滤）"""
    try:
        # 保存内置 type 函数的引用，避免被覆盖
        import builtins
        type_func = builtins.type
        
        logger.debug(f"获取测试计划列表 - project_id: {project_id}, project_id_type: {type_func(project_id)}, page: {page}, size: {size}")
        
        # 使用 plan_type 或 type 参数（优先使用 plan_type，避免覆盖内置函数）
        # 注意：这里的 type 是函数参数名，不是内置函数
        actual_plan_type = plan_type if plan_type is not None else type
        
        if not project_id:
            logger.warning("错误: project_id 参数为空")
            return APIResponse(
                status=ResponseStatus.SUCCESS,
                message="获取成功",
                data={
                    "items": [],
                    "total": 0,
                    "page": page,
                    "size": size,
                    "pages": 0,
                    "hasNext": False,
                    "hasPrev": False,
                },
            )
        
        result = TestPlanService.get_test_plans(
            db=db,
            project_id=project_id,
            page=page,
            size=size,
            search=search,
            status=status,
            plan_type=actual_plan_type,  # 使用实际的值
            owner_id=owner_id
        )

        logger.debug(f"Service返回结果 - 总数: {result['total']}, 项目数: {len(result['items'])}")

        # 序列化返回数据
        items = serialize_list(result["items"], camel_case=True)
        logger.debug(f"序列化后项目数: {len(items)}")
        
        # 为每个计划添加统计信息
        for item in items:
            plan_id = item.get("id")
            try:
                cases = TestPlanService.get_plan_cases(db, plan_id)
                item["totalCases"] = len(cases)
                # 计算已执行的用例数（非pending状态）
                item["executedCases"] = sum(
                    1 for case in cases 
                    if case.get("executionStatus") and case.get("executionStatus") != "pending"
                )
                # 统计各状态的用例数量
                item["caseStatusCounts"] = {
                    "pending": sum(1 for case in cases if case.get("executionStatus") == "pending" or not case.get("executionStatus")),
                    "pass": sum(1 for case in cases if case.get("executionStatus") == "pass"),
                    "fail": sum(1 for case in cases if case.get("executionStatus") == "fail"),
                    "broken": sum(1 for case in cases if case.get("executionStatus") == "broken"),
                    "error": sum(1 for case in cases if case.get("executionStatus") == "error"),
                    "skip": sum(1 for case in cases if case.get("executionStatus") == "skip")
                }
            except Exception as e:
                logger.error(f"获取计划 {plan_id} 的用例失败: {e}")
                item["totalCases"] = 0
                item["executedCases"] = 0
                item["caseStatusCounts"] = {
                    "pending": 0,
                    "pass": 0,
                    "fail": 0,
                    "broken": 0,
                    "error": 0,
                    "skip": 0
                }

        response_data = {
            "items": items,
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "pages": result["pages"],
            "hasNext": result["hasNext"],
            "hasPrev": result["hasPrev"],
        }
        
        logger.debug(f"返回数据 - items数量: {len(response_data['items'])}, total: {response_data['total']}")

        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=response_data,
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"获取测试计划列表失败: {e}")
        logger.error(f"错误详情: {error_detail}")
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0,
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
    plan = TestPlanService.get_test_plan(db, plan_id)
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

    plan_data = serialize_model(plan, camel_case=True)
    
    # 添加关联的测试用例（已包含执行状态）
    cases = TestPlanService.get_plan_cases(db, plan_id)
    # cases已经是字典格式，直接使用
    plan_data["testCases"] = cases
    plan_data["totalCases"] = len(cases)
    # 计算已执行的用例数（非pending状态）
    plan_data["executedCases"] = sum(
        1 for case in cases 
        if case.get("executionStatus") and case.get("executionStatus") != "pending"
    )
    # 统计各状态的用例数量
    plan_data["caseStatusCounts"] = {
        "pending": sum(1 for case in cases if case.get("executionStatus") == "pending" or not case.get("executionStatus")),
        "pass": sum(1 for case in cases if case.get("executionStatus") == "pass"),
        "fail": sum(1 for case in cases if case.get("executionStatus") == "fail"),
        "broken": sum(1 for case in cases if case.get("executionStatus") == "broken"),
        "error": sum(1 for case in cases if case.get("executionStatus") == "error"),
        "skip": sum(1 for case in cases if case.get("executionStatus") == "skip")
    }
    # 确保 plan_data 包含 projectId（用于前端加载模块列表）
    if "projectId" not in plan_data and plan.project_id:
        plan_data["projectId"] = str(plan.project_id)

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=plan_data,
    )


@router.post("", response_model=APIResponse)
async def create_test_plan(
    plan_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建测试计划"""
    try:
        logger.debug(f"收到创建测试计划请求: {plan_data}")
        
        project_id = plan_data.get("project_id")
        if not project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id 不能为空")

        # 验证必填字段
        if not plan_data.get("name"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="计划名称不能为空")
        
        if not plan_data.get("startDate"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="开始日期不能为空")

        plan = TestPlanService.create_test_plan(
            db=db,
            project_id=project_id,
            plan_data=plan_data,
            current_user_id=str(current_user.id)
        )

        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="创建成功",
            data=serialize_model(plan, camel_case=True),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"创建测试计划失败: {e}")
        logger.error(f"错误详情: {error_detail}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"创建失败: {str(e)}")


@router.put("/{plan_id}", response_model=APIResponse)
async def update_test_plan(
    plan_id: str,
    plan_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新测试计划"""
    try:
        plan = TestPlanService.update_test_plan(
            db=db,
            plan_id=plan_id,
            plan_data=plan_data,
            current_user_id=str(current_user.id)
        )

        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

        # 序列化计划数据
        plan_data_response = serialize_model(plan, camel_case=True)
        
        # 添加关联的测试用例（与 get_test_plan 保持一致）
        cases = TestPlanService.get_plan_cases(db, plan_id)
        plan_data_response["testCases"] = cases
        plan_data_response["totalCases"] = len(cases)
        plan_data_response["executedCases"] = sum(
            1 for case in cases 
            if case.get("executionStatus") and case.get("executionStatus") != "pending"
        )
        plan_data_response["caseStatusCounts"] = {
            "pending": sum(1 for case in cases if case.get("executionStatus") == "pending" or not case.get("executionStatus")),
            "pass": sum(1 for case in cases if case.get("executionStatus") == "pass"),
            "fail": sum(1 for case in cases if case.get("executionStatus") == "fail"),
            "broken": sum(1 for case in cases if case.get("executionStatus") == "broken"),
            "error": sum(1 for case in cases if case.get("executionStatus") == "error"),
            "skip": sum(1 for case in cases if case.get("executionStatus") == "skip")
        }
        if "projectId" not in plan_data_response and plan.project_id:
            plan_data_response["projectId"] = str(plan.project_id)

        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="更新成功",
            data=plan_data_response,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新测试计划失败: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"更新失败: {str(e)}")


@router.delete("/{plan_id}", response_model=APIResponse)
async def delete_test_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除测试计划"""
    success = TestPlanService.delete_test_plan(db, plan_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

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
    cases = TestPlanService.get_plan_cases(db, plan_id)

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=serialize_list(cases, camel_case=True),
    )


@router.post("/{plan_id}/cases", response_model=APIResponse)
async def add_cases_to_plan(
    plan_id: str,
    case_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向计划添加用例"""
    case_ids = case_data.get("caseIds", [])
    
    if not case_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="caseIds 不能为空")

    TestPlanService.add_cases_to_plan(db, plan_id, case_ids)

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="添加成功",
    )


@router.delete("/{plan_id}/cases", response_model=APIResponse)
async def remove_cases_from_plan(
    plan_id: str,
    case_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从计划移除用例"""
    case_ids = case_data.get("caseIds", [])
    
    if not case_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="caseIds 不能为空")

    TestPlanService.remove_cases_from_plan(db, plan_id, case_ids)

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
    plan = TestPlanService.update_plan_status(db, plan_id, "paused")
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

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
    plan = TestPlanService.update_plan_status(db, plan_id, "running")
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

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
    plan = TestPlanService.update_plan_status(db, plan_id, "completed")
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

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
    plan = TestPlanService.update_plan_status(db, plan_id, "running")
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

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
    plan = TestPlanService.update_plan_status(db, plan_id, "paused")
    
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测试计划不存在")

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
    # TODO: 实现执行历史查询
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
    project_id = clone_data.get("project_id")
    if not project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="project_id 不能为空")

    new_plan = TestPlanService.clone_plan(
        db=db,
        plan_id=plan_id,
        project_id=project_id,
        current_user_id=str(current_user.id)
    )

    if not new_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="源测试计划不存在")

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="克隆成功",
        data=serialize_model(new_plan, camel_case=True),
    )


@router.put("/{plan_id}/cases/{case_id}/status", response_model=APIResponse)
async def update_case_execution_status(
    plan_id: str,
    case_id: str,
    status_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用例执行状态"""
    status = status_data.get("status")
    if not status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status 不能为空")

    success = TestPlanService.update_case_execution_status(
        db=db,
        plan_id=plan_id,
        case_id=case_id,
        status=status
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例关联不存在")

    # 返回更新后的计划信息（包含最新的执行进度）
    plan = TestPlanService.get_test_plan(db, plan_id)
    plan_data = serialize_model(plan, camel_case=True) if plan else None
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=plan_data
    )


@router.put("/{plan_id}/cases/status", response_model=APIResponse)
async def batch_update_case_execution_status(
    plan_id: str,
    updates_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量更新用例执行状态"""
    updates = updates_data.get("updates", [])
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="updates 不能为空")

    TestPlanService.batch_update_case_execution_status(
        db=db,
        plan_id=plan_id,
        updates=updates
    )
    
    # 返回更新后的计划信息（包含最新的执行进度）
    plan = TestPlanService.get_test_plan(db, plan_id)
    plan_data = serialize_model(plan, camel_case=True) if plan else None

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="批量更新成功",
        data=plan_data
    )
