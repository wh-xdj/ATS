"""测试套相关API"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from api.deps import get_current_user
from services.test_suite_service import TestSuiteService
from schemas.test_suite import TestSuiteCreate, TestSuiteUpdate, TestSuiteResponse, TestSuiteExecutionResponse
from schemas.common import APIResponse, ResponseStatus
from utils.serializer import serialize_model, serialize_list
from typing import Optional

router = APIRouter()


@router.get("/{plan_id}/suites", response_model=APIResponse)
async def get_test_suites(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """获取测试套列表"""
    try:
        result = TestSuiteService.get_test_suites(db, plan_id, skip=skip, limit=limit)
        items = serialize_list(result["items"], camel_case=True)
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "items": items,
                "total": result["total"],
                "skip": result["skip"],
                "limit": result["limit"]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取测试套列表失败: {str(e)}"
        )


@router.get("/suites/{suite_id}", response_model=APIResponse)
async def get_test_suite(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取测试套详情"""
    suite = TestSuiteService.get_test_suite(db, suite_id)
    if not suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套不存在"
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=serialize_model(suite, camel_case=True)
    )


@router.post("/{plan_id}/suites", response_model=APIResponse)
async def create_test_suite(
    plan_id: str,
    suite_data: TestSuiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建测试套"""
    try:
        suite = TestSuiteService.create_test_suite(
            db=db,
            plan_id=plan_id,
            suite_data=suite_data.model_dump(),
            current_user_id=str(current_user.id)
        )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="创建成功",
            data=serialize_model(suite, camel_case=True)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建测试套失败: {str(e)}"
        )


@router.put("/suites/{suite_id}", response_model=APIResponse)
async def update_test_suite(
    suite_id: str,
    suite_data: TestSuiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新测试套"""
    try:
        # 获取所有字段，包括None值（用于清除Git配置）
        # 使用model_dump(exclude_unset=True)来区分"未设置"和"设置为None"
        update_data = suite_data.model_dump(exclude_unset=True)
        
        suite = TestSuiteService.update_test_suite(
            db=db,
            suite_id=suite_id,
            suite_data=update_data,
            current_user_id=str(current_user.id)
        )
        
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套不存在"
            )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="更新成功",
            data=serialize_model(suite, camel_case=True)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新测试套失败: {str(e)}"
        )


@router.delete("/suites/{suite_id}", response_model=APIResponse)
async def delete_test_suite(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除测试套"""
    success = TestSuiteService.delete_test_suite(db, suite_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套不存在"
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )


@router.post("/suites/{suite_id}/execute", response_model=APIResponse)
async def execute_test_suite(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行测试套"""
    try:
        suite = TestSuiteService.execute_test_suite(
            db=db,
            suite_id=suite_id,
            current_user_id=str(current_user.id)
        )
        
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套不存在"
            )
        
        # 通过WebSocket发送执行任务到Agent
        from api.v1.websocket import manager
        from services.environment_service import EnvironmentService
        
        environment = EnvironmentService.get_environment(db, suite.environment_id)
        if not environment or not environment.get("isOnline"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="执行环境未在线"
            )
        
        # 构建执行任务消息
        # 只有当git_enabled为'true'时才使用git配置
        git_enabled = suite.git_enabled == 'true' if hasattr(suite, 'git_enabled') and suite.git_enabled else False
        
        task_message = {
            "type": "execute_test_suite",
            "suite_id": suite.id,
            "plan_id": suite.plan_id,
            "git_repo_url": (suite.git_repo_url or None) if git_enabled else None,
            "git_branch": (suite.git_branch or None) if git_enabled else None,
            "git_token": (suite.git_token or None) if git_enabled else None,
            "execution_command": suite.execution_command,
            "case_ids": suite.case_ids,
            "executor_id": str(current_user.id)
        }
        
        # 发送到Agent
        success = await manager.send_message(suite.environment_id, task_message)
        if not success:
            # 如果发送失败，回滚状态
            suite.status = "pending"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="无法发送任务到Agent，请确保环境在线"
            )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="测试套执行已启动",
            data=serialize_model(suite, camel_case=True)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行测试套失败: {str(e)}"
        )


@router.post("/suites/{suite_id}/cancel", response_model=APIResponse)
async def cancel_test_suite(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消测试套执行"""
    try:
        from models.test_suite import TestSuite
        from api.v1.websocket import manager
        from services.environment_service import EnvironmentService
        
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套不存在"
            )
        
        if suite.status != "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试套未在执行中，无法取消"
            )
        
        environment = EnvironmentService.get_environment(db, suite.environment_id)
        if not environment or not environment.get("isOnline"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="执行环境未在线"
            )
        
        # 构建取消消息
        cancel_message = {
            "type": "cancel_test_suite",
            "suite_id": suite_id
        }
        
        # 发送到Agent
        success = await manager.send_message(suite.environment_id, cancel_message)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="无法发送取消指令到Agent，请确保环境在线"
            )
        
        # 更新状态为pending（等待Agent确认取消）
        suite.status = "pending"
        db.commit()
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="取消指令已发送",
            data=serialize_model(suite, camel_case=True)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消测试套失败: {str(e)}"
        )


@router.get("/suites/{suite_id}/executions", response_model=APIResponse)
async def get_suite_executions(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """获取测试套执行记录"""
    try:
        result = TestSuiteService.get_suite_executions(db, suite_id, skip=skip, limit=limit)
        
        # 序列化执行记录，并添加用例名称和环境名称
        items = []
        for execution in result["items"]:
            item = serialize_model(execution, camel_case=True)
            # 获取用例名称
            from models.test_case import TestCase
            case = db.query(TestCase).filter(TestCase.id == execution.case_id).first()
            if case:
                item["caseName"] = case.name
            
            # 获取环境名称
            from models.environment import Environment
            env = db.query(Environment).filter(Environment.id == execution.environment_id).first()
            if env:
                item["environmentName"] = env.name
            
            items.append(item)
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "items": items,
                "total": result["total"],
                "skip": result["skip"],
                "limit": result["limit"]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行记录失败: {str(e)}"
        )

