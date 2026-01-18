"""环境相关API（节点管理）"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from models import Environment
from schemas.environment import EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse
from schemas.common import APIResponse, ResponseStatus
from api.deps import get_current_user
from models import User
from services.environment_service import EnvironmentService
from services.task_queue_service import TaskQueueService
from utils.serializer import serialize_model, serialize_list, deserialize_dict
from core.logger import logger
from typing import Optional

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_environments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    status: Optional[bool] = None,
):
    """获取环境列表（节点列表，支持分页）"""
    # 计算 skip 和 limit
    skip = (page - 1) * size
    limit = size
    
    # 获取环境列表
    environments = EnvironmentService.get_environments(db, skip=skip, limit=limit, search=search, status=status)
    
    # 获取总数
    total = EnvironmentService.get_environments_count(db, search=search, status=status)
    
    # 计算总页数
    pages = (total + size - 1) // size if total > 0 else 0
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "items": environments,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "hasNext": page < pages,
            "hasPrev": page > 1,
        }
    )


@router.get("/{environment_id}", response_model=APIResponse)
async def get_environment(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取环境详情（节点详情）"""
    environment = EnvironmentService.get_environment(db, str(environment_id))
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=environment
    )


@router.post("", response_model=APIResponse)
async def create_environment(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建环境（节点）"""
    # 获取原始请求数据
    request_data = await request.json()
    
    # 调试日志：打印原始数据
    import json
    logger.debug(f"[DEBUG] 创建环境 - 原始数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    # 手动处理字段名转换（前端发送的是camelCase，后端需要snake_case）
    request_data = deserialize_dict(request_data, snake_case=True)
    
    logger.debug(f"[DEBUG] 创建环境 - 转换后数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    # 创建 Pydantic 模型
    environment_data = EnvironmentCreate(**request_data)
    
    logger.debug(f"[DEBUG] remote_work_dir值: {environment_data.remote_work_dir}")
    
    environment = EnvironmentService.create_environment(
        db=db,
        environment_data=environment_data,
        current_user_id=str(current_user.id)
    )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data=environment
    )


@router.put("/{environment_id}", response_model=APIResponse)
async def update_environment(
    environment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新环境（节点配置）"""
    # 获取原始请求数据
    request_data = await request.json()
    
    # 调试日志：打印原始数据
    import json
    logger.debug(f"[DEBUG] 更新环境 - 原始数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    # 手动处理字段名转换（前端发送的是camelCase，后端需要snake_case）
    request_data = deserialize_dict(request_data, snake_case=True)
    
    logger.debug(f"[DEBUG] 更新环境 - 转换后数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    # 创建 Pydantic 模型
    environment_data = EnvironmentUpdate(**request_data)
    
    logger.debug(f"[DEBUG] remote_work_dir值: {environment_data.remote_work_dir}")
    
    environment = EnvironmentService.update_environment(
        db=db,
        environment_id=str(environment_id),
        environment_data=environment_data,
        current_user_id=str(current_user.id)
    )
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=environment
    )


@router.delete("/{environment_id}", response_model=APIResponse)
async def delete_environment(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除环境（节点）"""
    success = EnvironmentService.delete_environment(db, str(environment_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )


@router.post("/{environment_id}/test", response_model=APIResponse)
async def test_environment_connection(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试环境连接（检查节点状态）"""
    status_info = EnvironmentService.check_node_status(db, str(environment_id))
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message=status_info.get("message", "状态检查完成"),
        data={
            "success": status_info.get("is_online", False),
            "message": status_info.get("message", "节点离线")
        }
    )


@router.post("/{environment_id}/heartbeat", response_model=APIResponse)
async def node_heartbeat(
    environment_id: str,
    node_info: dict,
    db: Session = Depends(get_db)
):
    """
    节点心跳接口（由agent调用）
    
    请求体示例：
    {
        "node_ip": "192.168.1.100",
        "os_type": "Linux",
        "os_version": "Ubuntu 20.04",
        "disk_info": {"total": "500GB", "used": "200GB", "free": "300GB"},
        "memory_info": {"total": "16GB", "used": "8GB", "free": "8GB"},
        "cpu_info": {"model": "Intel Core i7", "cores": 8, "frequency": "3.2GHz"}
    }
    """
    environment = EnvironmentService.update_node_info(
        db=db,
        environment_id=str(environment_id),
        node_info=node_info
    )
    
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="节点不存在"
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="心跳更新成功",
        data=environment
    )


@router.get("/{environment_id}/start-command", response_model=APIResponse)
async def get_start_command(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取环境启动命令"""
    environment = EnvironmentService.get_environment(db, str(environment_id))
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    if not environment.get("token"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="环境Token未生成，请先重新生成Token"
        )
    
    # 构建WebSocket URL
    from config import settings
    ws_host = settings.WEBSOCKET_HOST
    ws_port = settings.WEBSOCKET_PORT
    ws_path = settings.WEBSOCKET_PATH
    
    # 判断协议（开发环境通常用ws，生产环境用wss）
    protocol = "ws" if settings.ENVIRONMENT == "development" else "wss"
    ws_url = f"{protocol}://{ws_host}:{ws_port}{ws_path}"
    
    # 构建启动命令
    token = environment.get("token")
    work_dir = environment.get("remoteWorkDir") or environment.get("remote_work_dir") or ""
    
    start_command = f"python agent.py --url='{ws_url}' --token='{token}' --work_dir='{work_dir}'"
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "startCommand": start_command,
            "websocketUrl": ws_url,
            "token": token,
            "workDir": work_dir
        }
    )


@router.post("/{environment_id}/regenerate-token", response_model=APIResponse)
async def regenerate_token(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重新生成环境Token"""
    # 在生成新token之前，先断开使用旧token的连接
    from api.v1.websocket import manager
    environment_id_str = str(environment_id)
    
    # 检查是否有活跃连接
    if environment_id_str in manager.active_connections:
        logger.info(f"[WebSocket] 检测到环境 {environment_id_str} 有活跃连接，正在断开...")
        # 断开连接并通知agent
        await manager.disconnect_and_notify(
            environment_id_str,
            reason="Token已重新生成，请使用新Token重新连接"
        )
    
    # 生成新token
    environment = EnvironmentService.regenerate_token(
        db=db,
        environment_id=environment_id_str,
        current_user_id=str(current_user.id)
    )
    
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="Token重新生成成功，旧连接已断开",
        data=environment
    )


@router.post("/{environment_id}/enable", response_model=APIResponse)
async def enable_environment(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启用环境"""
    environment = EnvironmentService.update_environment(
        db=db,
        environment_id=str(environment_id),
        environment_data=EnvironmentUpdate(status=True),
        current_user_id=str(current_user.id)
    )
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="环境已启用",
        data=environment
    )


@router.post("/{environment_id}/disable", response_model=APIResponse)
async def disable_environment(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """禁用环境"""
    environment = EnvironmentService.update_environment(
        db=db,
        environment_id=str(environment_id),
        environment_data=EnvironmentUpdate(status=False),
        current_user_id=str(current_user.id)
    )
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="环境已禁用",
        data=environment
    )


@router.get("/{environment_id}/suite-executions", response_model=APIResponse)
async def get_environment_suite_executions(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    result: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取环境的测试套执行历史"""
    from models.test_suite import TestSuiteExecution, TestSuite, TestSuiteLog
    from models.user import User
    from sqlalchemy import func, or_
    from datetime import datetime, timedelta
    
    try:
        # 从TestSuiteLog表获取所有有execution_id的记录，按execution_id分组
        # 这样可以准确获取每次执行的记录
        log_query = db.query(TestSuiteLog).filter(
            TestSuiteLog.execution_id.isnot(None)
        )
        
        # 通过suite_id关联TestSuite，再关联Environment来过滤环境
        if search:
            log_query = log_query.join(TestSuite, TestSuiteLog.suite_id == TestSuite.id).filter(
                TestSuite.environment_id == environment_id,
                TestSuite.name.like(f"%{search}%")
            )
        else:
            log_query = log_query.join(TestSuite, TestSuiteLog.suite_id == TestSuite.id).filter(
                TestSuite.environment_id == environment_id
            )
        
        # 获取所有唯一的execution_id
        unique_execution_ids = log_query.with_entities(
            TestSuiteLog.execution_id,
            func.min(TestSuiteLog.timestamp).label('first_timestamp')
        ).group_by(
            TestSuiteLog.execution_id
        ).order_by(
            func.min(TestSuiteLog.timestamp).desc()
        ).all()
        
        # 获取总数（先不过滤，后面再过滤）
        total_before_filter = len(unique_execution_ids)
        
        # 获取每次执行的详细信息
        items = []
        for execution_id_val, first_timestamp in unique_execution_ids:
            # 获取这次执行的所有日志记录（每个execution_id只有一条记录）
            log_record = db.query(TestSuiteLog).filter(
                TestSuiteLog.execution_id == execution_id_val
            ).order_by(TestSuiteLog.timestamp.asc()).first()
            
            if not log_record:
                continue
            
            suite_id_val = log_record.suite_id
            log_id = log_record.id
            # 使用日志记录的timestamp作为执行时间
            exec_time = log_record.timestamp
            
            # 获取测试套信息
            suite = db.query(TestSuite).filter(TestSuite.id == suite_id_val).first()
            if not suite or suite.environment_id != environment_id:
                continue
            
            # 如果测试套正在执行中，检查这个execution_id是否是最新的执行
            # 如果是，则跳过不显示（因为还在执行中）
            # 如果不是，则显示（因为这是历史记录）
            if suite.status == "running":
                # 检查这个execution_id是否是最新的（通过时间戳判断）
                # 获取该测试套最新的execution_id
                latest_log = db.query(TestSuiteLog).filter(
                    TestSuiteLog.suite_id == suite_id_val
                ).order_by(TestSuiteLog.timestamp.desc()).first()
                
                # 如果这个execution_id是最新的，说明正在执行中，跳过
                if latest_log and latest_log.execution_id == execution_id_val:
                    continue
            
            suite_name = suite.name if suite else "未知测试套"
            
            # 从日志记录的duration字段获取执行耗时（如果已计算）
            duration = log_record.duration if log_record.duration else None
            
            # 从TestSuiteExecution表获取执行记录（用于判断结果和执行人）
            time_window_start = exec_time - timedelta(minutes=5)
            time_window_end = exec_time + timedelta(minutes=5)
            exec_records = db.query(TestSuiteExecution).filter(
                TestSuiteExecution.suite_id == suite_id_val,
                TestSuiteExecution.executed_at >= time_window_start,
                TestSuiteExecution.executed_at <= time_window_end
            ).all()
            
            # 如果没有找到执行记录，尝试查找最近的
            if not exec_records:
                exec_records = db.query(TestSuiteExecution).filter(
                    TestSuiteExecution.suite_id == suite_id_val
                ).order_by(TestSuiteExecution.executed_at.desc()).limit(1).all()
            
            if not exec_records:
                # 如果没有执行记录，检查是否有取消相关的日志
                from models.test_suite import TestSuiteLog
                cancel_log = db.query(TestSuiteLog).filter(
                    TestSuiteLog.suite_id == suite_id_val,
                    TestSuiteLog.execution_id == execution_id_val,
                    TestSuiteLog.message.like("%取消%")
                ).first()
                if cancel_log:
                    overall_result = "cancelled"
                else:
                    overall_result = "unknown"
                
                executor_id_val = None
                executor_name = "未知用户"
                exec_time_iso = exec_time.isoformat() if exec_time else None
            else:
                # 获取执行人信息
                executor = db.query(User).filter(User.id == exec_records[0].executor_id).first()
                executor_id_val = exec_records[0].executor_id
                executor_name = executor.username if executor else "未知用户"
                
                # 确定整体结果
                # 优先级：取消 > 失败/错误 > 跳过 > 通过
                # 先检查是否有取消相关的日志（即使有执行记录，也可能是被取消的）
                from models.test_suite import TestSuiteLog
                cancel_log = db.query(TestSuiteLog).filter(
                    TestSuiteLog.suite_id == suite_id_val,
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
                
                # 使用日志记录的timestamp作为执行时间，而不是TestSuiteExecution的executed_at
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
                "suiteId": suite_id_val,
                "suiteName": suite_name,
                "result": overall_result,
                "executorId": executor_id_val or "",
                "executorName": executor_name,
                "executedAt": exec_time_iso,  # 使用日志记录的timestamp
                "duration": duration,
                "executionId": execution_id_val,  # 用于获取日志
                "logId": log_id,  # 日志ID
                "caseCount": len(exec_records) if exec_records else 0  # 用例数量
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
        logger.exception("获取环境测试套执行历史失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行历史失败: {str(e)}"
        )


@router.get("/{environment_id}/queue-status", response_model=APIResponse)
async def get_queue_status(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取环境任务队列状态"""
    try:
        queue_status = TaskQueueService.get_queue_status(db, environment_id)
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=queue_status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取队列状态失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取队列状态失败: {str(e)}"
        )


@router.get("/{environment_id}/queue-tasks", response_model=APIResponse)
async def get_queue_tasks(
    environment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """获取环境任务队列中的任务列表"""
    try:
        tasks = TaskQueueService.get_queue_tasks(
            db=db,
            environment_id=environment_id,
            status=status,
            skip=skip,
            limit=limit
        )
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=tasks
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("获取队列任务失败")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取队列任务失败: {str(e)}"
        )

