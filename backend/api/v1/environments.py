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
from utils.serializer import serialize_model, serialize_list, deserialize_dict
from core.logger import logger

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_environments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """获取环境列表（节点列表）"""
    environments = EnvironmentService.get_environments(db, skip=skip, limit=limit)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=environments
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

