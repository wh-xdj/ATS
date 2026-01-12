"""测试套相关API"""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from api.deps import get_current_user
from services.test_suite_service import TestSuiteService
from schemas.test_suite import TestSuiteCreate, TestSuiteUpdate, TestSuiteResponse, TestSuiteExecutionResponse, TestSuiteCancelRequest
from schemas.common import APIResponse, ResponseStatus
from utils.serializer import serialize_model, serialize_list
from typing import Optional
from datetime import timedelta
from core.logger import logger

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
        # 先检查测试套是否存在
        from models.test_suite import TestSuite
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套不存在"
            )
        
        # 检查环境是否在线
        from services.environment_service import EnvironmentService
        from services.task_queue_service import TaskQueueService
        environment = EnvironmentService.get_environment(db, suite.environment_id)
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行环境不存在"
            )
        
        # 检查环境在线状态（兼容 isOnline 和 is_online）
        is_online = environment.get("isOnline") or environment.get("is_online", False)
        if not is_online:
            env_name = environment.get("name", "未知环境")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"执行环境\"{env_name}\"未在线，请先启动Agent"
            )
        
        # 生成执行ID（用于关联本次执行的所有日志）
        # 注意：允许多次执行，每次执行都会创建新的执行记录和任务队列项
        import uuid
        execution_id = str(uuid.uuid4())
        
        # 检查是否可以立即执行
        can_execute = TaskQueueService.can_execute_immediately(db, suite.environment_id)
        
        if can_execute:
            # 可以立即执行，添加到队列并标记为running
            TaskQueueService.add_to_queue(
                db=db,
                environment_id=suite.environment_id,
                suite_id=suite.id,
                execution_id=execution_id,
                executor_id=str(current_user.id)
            )
            TaskQueueService.start_task(db, execution_id)
            
            # 更新测试套状态：如果有正在运行的任务，状态为running
            from models.task_queue import TaskQueue
            running_count = db.query(TaskQueue).filter(
                TaskQueue.suite_id == suite_id,
                TaskQueue.status == "running"
            ).count()
            suite.status = "running" if running_count > 0 else "pending"
            suite.updated_by = str(current_user.id)
            from utils.datetime_utils import beijing_now
            suite.updated_at = beijing_now()
            db.commit()
            
            # 根据case_ids查询对应的case_code（用于用例筛选）
            from models.test_case import TestCase
            test_cases = db.query(TestCase).filter(TestCase.id.in_(suite.case_ids)).all()
            case_codes = [case.case_code for case in test_cases]
            
            # 构建执行任务消息
            # 只有当git_enabled为'true'时才使用git配置
            git_enabled = suite.git_enabled == 'true' if hasattr(suite, 'git_enabled') and suite.git_enabled else False
            
            task_message = {
                "type": "execute_test_suite",
                "suite_id": suite.id,
                "plan_id": suite.plan_id,
                "execution_id": execution_id,  # 添加执行ID
                "git_repo_url": (suite.git_repo_url or None) if git_enabled else None,
                "git_branch": (suite.git_branch or None) if git_enabled else None,
                "git_token": (suite.git_token or None) if git_enabled else None,
                "execution_command": suite.execution_command,
                "case_ids": suite.case_ids,  # 保留用于结果回填
                "case_codes": case_codes,  # 新增：用于用例筛选
                "executor_id": str(current_user.id)
            }
            
            # 发送到Agent
            from api.v1.websocket import manager
            success = await manager.send_message(suite.environment_id, task_message)
            if not success:
                # 如果发送失败，回滚状态和队列
                suite.status = "pending"
                TaskQueueService.complete_task(db, execution_id, "failed")
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
        else:
            # 需要排队，添加到队列并保持pending状态
            TaskQueueService.add_to_queue(
                db=db,
                environment_id=suite.environment_id,
                suite_id=suite.id,
                execution_id=execution_id,
                executor_id=str(current_user.id)
            )
            
            # 更新测试套状态：如果有正在运行的任务，状态为running，否则为pending
            from models.task_queue import TaskQueue
            running_count = db.query(TaskQueue).filter(
                TaskQueue.suite_id == suite_id,
                TaskQueue.status == "running"
            ).count()
            suite.status = "running" if running_count > 0 else "pending"
            suite.updated_by = str(current_user.id)
            from utils.datetime_utils import beijing_now
            suite.updated_at = beijing_now()
            db.commit()
            
            return APIResponse(
                status=ResponseStatus.SUCCESS,
                message="任务已加入队列，等待执行",
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
    request: TestSuiteCancelRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取消测试套执行（支持通过execution_id取消特定执行）"""
    try:
        from models.test_suite import TestSuite, TestSuiteLog
        from api.v1.websocket import manager
        from services.environment_service import EnvironmentService
        from services.task_queue_service import TaskQueueService
        from models.task_queue import TaskQueue
        
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套不存在"
            )
        
        environment = EnvironmentService.get_environment(db, suite.environment_id)
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行环境不存在"
            )
        
        # 检查环境在线状态（兼容 isOnline 和 is_online）
        is_online = environment.get("isOnline") or environment.get("is_online", False)
        if not is_online:
            env_name = environment.get("name", "未知环境")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"执行环境\"{env_name}\"未在线，请先启动Agent"
            )
        
        execution_id = request.executionId
        
        # 如果提供了execution_id，取消特定的执行记录
        if execution_id:
            # 查找任务队列中的任务
            task = db.query(TaskQueue).filter(
                TaskQueue.execution_id == execution_id,
                TaskQueue.suite_id == suite_id
            ).first()
            
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="执行记录不存在"
                )
            
            if task.status not in ["running", "pending"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该执行记录不在运行中或等待中，无法取消"
                )
            
            # 根据任务状态处理取消
            if task.status == "running":
                # 如果任务正在运行，需要发送取消消息到Agent
                cancel_message = {
                    "type": "cancel_test_suite",
                    "suite_id": suite_id,
                    "execution_id": execution_id
                }
                
                # 发送到Agent
                success = await manager.send_message(suite.environment_id, cancel_message)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="无法发送取消指令到Agent，请确保环境在线"
                    )
            elif task.status == "pending":
                # 如果任务还在等待中，直接标记为取消，不需要发送消息到Agent
                pass
            
            # 更新任务队列状态为cancelled
            TaskQueueService.complete_task(db, execution_id, "cancelled")
            
            # 取消任务后，尝试执行队列中的下一个任务（无论取消的是running还是pending）
            if task.status == "running" or task.status == "pending":
                next_task = TaskQueueService.get_next_pending_task(db, suite.environment_id)
                if next_task:
                    if TaskQueueService.can_execute_immediately(db, suite.environment_id):
                        TaskQueueService.start_task(db, next_task.execution_id)
                        next_suite = db.query(TestSuite).filter(TestSuite.id == next_task.suite_id).first()
                        if next_suite:
                            next_suite.status = "running"
                        
                        git_enabled = next_suite.git_enabled == 'true' if hasattr(next_suite, 'git_enabled') and next_suite.git_enabled else False
                        
                        # 根据case_ids查询对应的case_code
                        from models.test_case import TestCase
                        next_test_cases = db.query(TestCase).filter(TestCase.id.in_(next_suite.case_ids)).all()
                        next_case_codes = [case.case_code for case in next_test_cases]
                        
                        task_message = {
                            "type": "execute_test_suite",
                            "suite_id": next_suite.id,
                            "plan_id": next_suite.plan_id,
                            "execution_id": next_task.execution_id,
                            "git_repo_url": (next_suite.git_repo_url or None) if git_enabled else None,
                            "git_branch": (next_suite.git_branch or None) if git_enabled else None,
                            "git_token": (next_suite.git_token or None) if git_enabled else None,
                            "execution_command": next_suite.execution_command,
                            "case_ids": next_suite.case_ids,
                            "case_codes": next_case_codes,  # 新增：用于用例筛选
                            "executor_id": next_task.executor_id
                        }
                        await manager.send_message(suite.environment_id, task_message)
            
            # 检查是否还有其他正在运行或等待的任务
            running_tasks = db.query(TaskQueue).filter(
                TaskQueue.suite_id == suite_id,
                TaskQueue.status == "running"
            ).count()
            
            pending_tasks = db.query(TaskQueue).filter(
                TaskQueue.suite_id == suite_id,
                TaskQueue.status == "pending"
            ).count()
            
            # 更新测试套状态
            if running_tasks > 0:
                suite.status = "running"
            elif pending_tasks > 0:
                suite.status = "pending"
            else:
                suite.status = "completed"
            
            db.commit()
            
            return APIResponse(
                status=ResponseStatus.SUCCESS,
                message="取消指令已发送",
                data=serialize_model(suite, camel_case=True)
            )
        else:
            # 如果没有提供execution_id，取消所有正在运行的任务（兼容旧逻辑）
            running_tasks = db.query(TaskQueue).filter(
                TaskQueue.suite_id == suite_id,
                TaskQueue.status == "running"
            ).all()
            
            if not running_tasks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="没有正在执行的任务，无法取消"
                )
            
            # 取消所有正在运行的任务
            for task in running_tasks:
                cancel_message = {
                    "type": "cancel_test_suite",
                    "suite_id": suite_id,
                    "execution_id": task.execution_id
                }
                await manager.send_message(suite.environment_id, cancel_message)
                TaskQueueService.complete_task(db, task.execution_id, "cancelled")
            
            # 更新测试套状态
            pending_tasks = db.query(TaskQueue).filter(
                TaskQueue.suite_id == suite_id,
                TaskQueue.status == "pending"
            ).count()
            suite.status = "pending" if pending_tasks > 0 else "completed"
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
    """获取测试套执行记录（旧接口，保留兼容性）"""
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


@router.get("/suites/{suite_id}/logs", response_model=APIResponse)
async def get_suite_logs(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 1000,
    execution_id: Optional[str] = Query(None, alias="executionId"),
    log_id: Optional[str] = Query(None, alias="logId")
):
    """获取测试套日志"""
    from models.test_suite import TestSuiteLog
    from utils.serializer import serialize_model
    print(f"log_id: {log_id}, execution_id: {execution_id}")
    try:
        query = db.query(TestSuiteLog).filter(TestSuiteLog.suite_id == suite_id)
        
        if log_id:
            # 优先使用log_id查询
            query = query.filter(TestSuiteLog.id == log_id)
        elif execution_id:
            query = query.filter(TestSuiteLog.execution_id == execution_id)
        
        total = query.count()
        items = query.order_by(TestSuiteLog.timestamp.asc()).offset(skip).limit(limit).all()
        print(f"items: {items}")
        # logger.info(f"items: {items}")
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "items": [serialize_model(item, camel_case=True) for item in items],
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日志失败: {str(e)}"
        )


@router.get("/suites/{suite_id}/suite-executions", response_model=APIResponse)
async def get_suite_suite_executions(
    suite_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    result: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取测试套的执行历史（按execution_id分组）"""
    from models.test_suite import TestSuiteExecution, TestSuite, TestSuiteLog
    from models.user import User
    from sqlalchemy import func
    from datetime import datetime, timedelta
    from utils.serializer import serialize_model
    from core.logger import logger
    
    try:
        # 验证测试套存在
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套不存在"
            )
        
        # 从TaskQueue表获取所有execution_id（包括pending和running状态的）
        from models.task_queue import TaskQueue
        task_queue_execution_ids = db.query(TaskQueue.execution_id).filter(
            TaskQueue.suite_id == suite_id
        ).distinct().all()
        task_queue_execution_ids_set = {row[0] for row in task_queue_execution_ids}
        
        # 从TestSuiteLog表获取所有有execution_id的记录，按execution_id分组
        log_query = db.query(TestSuiteLog).filter(
            TestSuiteLog.suite_id == suite_id,
            TestSuiteLog.execution_id.isnot(None)
        )
        
        # 获取所有唯一的execution_id（从日志中）
        log_execution_ids = log_query.with_entities(
            TestSuiteLog.execution_id,
            func.min(TestSuiteLog.timestamp).label('first_timestamp')
        ).group_by(
            TestSuiteLog.execution_id
        ).order_by(
            func.min(TestSuiteLog.timestamp).desc()
        ).all()
        
        # 合并两个来源的execution_id
        # 创建一个字典，key是execution_id，value是first_timestamp
        execution_id_map = {}
        for execution_id_val, first_timestamp in log_execution_ids:
            execution_id_map[execution_id_val] = first_timestamp
        
        # 对于任务队列中但没有日志的execution_id，使用任务的创建时间
        for execution_id_val in task_queue_execution_ids_set:
            if execution_id_val not in execution_id_map:
                task = db.query(TaskQueue).filter(
                    TaskQueue.execution_id == execution_id_val,
                    TaskQueue.suite_id == suite_id
                ).order_by(TaskQueue.created_at.asc()).first()
                if task:
                    execution_id_map[execution_id_val] = task.created_at
        
        # 按时间戳排序
        unique_execution_ids = sorted(
            execution_id_map.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 获取每次执行的详细信息
        items = []
        for execution_id_val, first_timestamp in unique_execution_ids:
            # 获取这次执行的所有日志记录（每个execution_id只有一条记录）
            log_record = db.query(TestSuiteLog).filter(
                TestSuiteLog.execution_id == execution_id_val
            ).order_by(TestSuiteLog.timestamp.asc()).first()
            
            # 如果没有日志记录，从任务队列获取信息
            if not log_record:
                # 从任务队列获取任务信息
                task = db.query(TaskQueue).filter(
                    TaskQueue.execution_id == execution_id_val,
                    TaskQueue.suite_id == suite_id
                ).first()
                
                if not task:
                    continue
                
                # 使用任务的创建时间作为执行时间
                exec_time = task.created_at
                # 为排队中的任务生成一个log_id（使用execution_id作为标识）
                # 或者使用task.id，但为了保持一致性，我们使用execution_id
                log_id = execution_id_val  # 使用execution_id作为log_id
                duration = None
                
                # 计算序号：获取该测试套的所有执行记录（包括已完成和等待中的）
                # 按时间排序，计算当前执行记录的序号
                from sqlalchemy import func, or_
                # 获取所有有execution_id的记录（包括日志和任务队列）
                all_execution_ids = set()
                
                # 从日志中获取所有execution_id
                log_execution_ids = db.query(TestSuiteLog.execution_id).filter(
                    TestSuiteLog.suite_id == suite_id,
                    TestSuiteLog.execution_id.isnot(None)
                ).distinct().all()
                all_execution_ids.update([row[0] for row in log_execution_ids])
                
                # 从任务队列中获取所有execution_id
                task_execution_ids = db.query(TaskQueue.execution_id).filter(
                    TaskQueue.suite_id == suite_id
                ).distinct().all()
                all_execution_ids.update([row[0] for row in task_execution_ids])
                
                # 获取所有执行记录的时间戳（从日志或任务队列）
                execution_times = []
                for eid in all_execution_ids:
                    # 优先从日志获取时间
                    log_time = db.query(TestSuiteLog.timestamp).filter(
                        TestSuiteLog.suite_id == suite_id,
                        TestSuiteLog.execution_id == eid
                    ).order_by(TestSuiteLog.timestamp.asc()).first()
                    if log_time:
                        execution_times.append((eid, log_time[0]))
                    else:
                        # 如果没有日志，从任务队列获取
                        task_time = db.query(TaskQueue.created_at).filter(
                            TaskQueue.suite_id == suite_id,
                            TaskQueue.execution_id == eid
                        ).first()
                        if task_time:
                            execution_times.append((eid, task_time[0]))
                
                # 按时间排序
                execution_times.sort(key=lambda x: x[1])
                
                # 找到当前execution_id的序号
                sequence_number = None
                for idx, (eid, _) in enumerate(execution_times, start=1):
                    if eid == execution_id_val:
                        sequence_number = idx
                        break
                
                # 如果没找到，使用当前总数+1
                if sequence_number is None:
                    sequence_number = len(execution_times) + 1
                
                # 根据任务状态设置结果
                if task.status == "pending":
                    overall_result = "pending"
                elif task.status == "running":
                    overall_result = "running"
                elif task.status == "cancelled":
                    overall_result = "cancelled"
                elif task.status == "failed":
                    overall_result = "failed"
                else:
                    overall_result = "completed"
                
                # 获取执行人信息
                executor = db.query(User).filter(User.id == task.executor_id).first()
                executor_id_val = task.executor_id
                executor_name = executor.username if executor else "未知用户"
                exec_time_iso = exec_time.isoformat() if exec_time else None
                
                # 添加到结果列表
                items.append({
                    "logId": log_id,
                    "executionId": execution_id_val,
                    "suiteId": suite_id,
                    "suiteName": suite.name,
                    "result": overall_result,
                    "executorId": executor_id_val,
                    "executorName": executor_name,
                    "executedAt": exec_time_iso,
                    "duration": duration,
                    "sequenceNumber": sequence_number
                })
                continue
            
            log_id = log_record.id
            # 使用日志记录的timestamp作为执行时间
            exec_time = log_record.timestamp
            
            # 从日志记录的duration字段获取执行耗时（如果已计算）
            duration = log_record.duration if log_record.duration else None
            
            # 从TestSuiteExecution表获取执行记录（用于判断结果和执行人）
            time_window_start = exec_time - timedelta(minutes=5)
            time_window_end = exec_time + timedelta(minutes=5)
            exec_records = db.query(TestSuiteExecution).filter(
                TestSuiteExecution.suite_id == suite_id,
                TestSuiteExecution.executed_at >= time_window_start,
                TestSuiteExecution.executed_at <= time_window_end
            ).all()
            
            # 如果没有找到执行记录，尝试查找最近的
            if not exec_records:
                exec_records = db.query(TestSuiteExecution).filter(
                    TestSuiteExecution.suite_id == suite_id
                ).order_by(TestSuiteExecution.executed_at.desc()).limit(1).all()
            
            # 检查任务队列状态
            task = db.query(TaskQueue).filter(
                TaskQueue.execution_id == execution_id_val,
                TaskQueue.suite_id == suite_id
            ).first()
            
            # 检查是否正在执行中
            is_running = False
            is_pending = False
            if task:
                if task.status == "running":
                    is_running = True
                elif task.status == "pending":
                    is_pending = True
            else:
                # 如果没有任务队列记录，通过suite.status和日志判断
                is_running = suite.status == "running"
                if is_running:
                    # 检查这个execution_id是否是最新的（通过时间戳判断）
                    latest_log = db.query(TestSuiteLog).filter(
                        TestSuiteLog.suite_id == suite_id
                    ).order_by(TestSuiteLog.timestamp.desc()).first()
                    
                    # 如果这个execution_id是最新的，说明正在执行中
                    is_running = latest_log and latest_log.execution_id == execution_id_val
            
            if not exec_records:
                # 如果没有执行记录，检查任务队列状态和日志
                if is_pending:
                    overall_result = "pending"
                elif is_running:
                    overall_result = "running"
                else:
                    # 检查是否有取消相关的日志
                    cancel_log = db.query(TestSuiteLog).filter(
                        TestSuiteLog.suite_id == suite_id,
                        TestSuiteLog.execution_id == execution_id_val,
                        TestSuiteLog.message.like("%取消%")
                    ).first()
                    if cancel_log:
                        overall_result = "cancelled"
                    else:
                        overall_result = "unknown"
                
                # 从任务队列获取执行人信息
                if task:
                    executor = db.query(User).filter(User.id == task.executor_id).first()
                    executor_id_val = task.executor_id
                    executor_name = executor.username if executor else "未知用户"
                else:
                    executor_id_val = None
                    executor_name = "未知用户"
                exec_time_iso = exec_time.isoformat() if exec_time else None
            else:
                # 获取执行人信息
                executor = db.query(User).filter(User.id == exec_records[0].executor_id).first()
                executor_id_val = exec_records[0].executor_id
                executor_name = executor.username if executor else "未知用户"
                
                # 确定整体结果
                # 优先级：运行中 > 等待中 > 取消 > 失败/错误 > 跳过 > 通过
                if is_running:
                    overall_result = "running"
                elif is_pending:
                    overall_result = "pending"
                else:
                    # 先检查是否有取消相关的日志（即使有执行记录，也可能是被取消的）
                    cancel_log = db.query(TestSuiteLog).filter(
                        TestSuiteLog.suite_id == suite_id,
                        TestSuiteLog.execution_id == execution_id_val,
                        TestSuiteLog.message.like("%取消%")
                    ).first()
                    
                    if cancel_log:
                        # 如果有取消日志，优先标记为取消
                        overall_result = "cancelled"
                    else:
                        # 否则根据执行记录判断
                        overall_result = "passed"
                        for record in exec_records:
                            if record.result in ["failed", "error"]:
                                overall_result = "failed"
                                break
                            elif record.result == "cancelled":
                                overall_result = "cancelled"
                                break
                            elif record.result == "skipped" and overall_result == "passed":
                                overall_result = "skipped"
                
                # 使用日志记录的timestamp作为执行时间
                exec_time_iso = exec_time.isoformat() if exec_time else None
            
            # 结果过滤
            if result and overall_result != result:
                continue
            
            # 日期范围过滤
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    if exec_time and exec_time < start_dt:
                        continue
                except:
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    if exec_time and exec_time > end_dt:
                        continue
                except:
                    pass
            
            items.append({
                "id": log_id,  # 使用日志ID作为唯一标识
                "suiteId": suite_id,
                "suiteName": suite.name,
                "result": overall_result,
                "executorId": executor_id_val or "",
                "executorName": executor_name,
                "executedAt": exec_time_iso,  # 使用日志记录的timestamp
                "duration": duration,
                "executionId": execution_id_val,  # 用于获取日志
                "logId": log_id,  # 日志ID
                "sequenceNumber": log_record.sequence_number,  # 序号
                "caseCount": len(exec_records) if exec_records else 0,  # 用例数量
                "isRunning": is_running  # 是否正在运行
            })
        
        # 按执行时间排序
        items.sort(key=lambda x: x.get("executedAt") or "", reverse=True)
        
        # 应用分页（在过滤后）
        total = len(items)
        paginated_items = items[skip:skip + limit]
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "items": paginated_items,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取测试套执行历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行历史失败: {str(e)}"
        )


@router.delete("/suites/{suite_id}/suite-executions/{execution_id}", response_model=APIResponse)
async def delete_suite_execution(
    suite_id: str,
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除测试套执行历史"""
    from models.test_suite import TestSuite, TestSuiteLog, TestSuiteExecution
    
    try:
        # 验证测试套存在
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套不存在"
            )
        
        # 查找要删除的执行记录（通过execution_id查找日志记录和任务队列记录）
        log_records = db.query(TestSuiteLog).filter(
            TestSuiteLog.suite_id == suite_id,
            TestSuiteLog.execution_id == execution_id
        ).all()
        
        # 查找任务队列中的记录
        from models.task_queue import TaskQueue
        task_records = db.query(TaskQueue).filter(
            TaskQueue.suite_id == suite_id,
            TaskQueue.execution_id == execution_id
        ).all()
        
        if not log_records and not task_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        # 检查是否正在执行中或等待中
        running_tasks = [t for t in task_records if t.status == "running"]
        pending_tasks = [t for t in task_records if t.status == "pending"]
        
        if running_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法删除正在执行中的记录"
            )
        
        if pending_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法删除等待中的记录，请先取消任务"
            )
        
        # 删除日志记录
        for log_record in log_records:
            db.delete(log_record)
        
        # 删除任务队列记录（已完成或已取消的任务）
        for task_record in task_records:
            db.delete(task_record)
        
        # 删除关联的执行记录（TestSuiteExecution）
        exec_records = db.query(TestSuiteExecution).filter(
            TestSuiteExecution.suite_id == suite_id
        ).all()
        
        # 通过时间窗口匹配执行记录（在日志时间前后5分钟内）
        for log_record in log_records:
            if log_record.timestamp:
                time_window_start = log_record.timestamp - timedelta(minutes=5)
                time_window_end = log_record.timestamp + timedelta(minutes=5)
                matching_execs = db.query(TestSuiteExecution).filter(
                    TestSuiteExecution.suite_id == suite_id,
                    TestSuiteExecution.executed_at >= time_window_start,
                    TestSuiteExecution.executed_at <= time_window_end
                ).all()
                for exec_record in matching_execs:
                    db.delete(exec_record)
        
        db.commit()
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"删除测试套执行历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )

