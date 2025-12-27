"""工作空间API - 通过WebSocket与Agent通信"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from api.deps import get_current_user
from api.v1.websocket import manager
from services.environment_service import EnvironmentService
from schemas.common import APIResponse, ResponseStatus
import uuid
import asyncio
from typing import Dict, Any, Optional

router = APIRouter()

# 存储待响应的请求: {request_id: (event, response_data)}
pending_requests: Dict[str, tuple] = {}


async def send_workspace_request(
    environment_id: str,
    message_type: str,
    data: Dict[str, Any],
    timeout: float = 10.0
) -> Dict[str, Any]:
    """
    向Agent发送工作空间请求并等待响应
    
    Args:
        environment_id: 环境ID
        message_type: 消息类型（workspace_list, workspace_read等）
        data: 请求数据
        timeout: 超时时间（秒）
        
    Returns:
        响应数据
    """
    # 生成请求ID
    request_id = str(uuid.uuid4())
    
    # 创建事件用于等待响应
    event = asyncio.Event()
    response_data: Optional[Dict[str, Any]] = None
    
    # 存储请求
    pending_requests[request_id] = (event, response_data)
    
    # 构建消息
    message = {
        "type": message_type,
        "request_id": request_id,
        **data
    }
    
    # 发送消息
    print(f"[Workspace] 发送请求到环境 {environment_id}: {message_type}, request_id: {request_id}")
    success = await manager.send_message(environment_id, message)
    if not success:
        del pending_requests[request_id]
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent未连接或无法发送消息"
        )
    
    print(f"[Workspace] 消息已发送，等待响应...")
    # 等待响应（带超时）
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        print(f"[Workspace] 收到响应，request_id: {request_id}")
    except asyncio.TimeoutError:
        print(f"[Workspace] 等待响应超时，request_id: {request_id}")
        del pending_requests[request_id]
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="等待Agent响应超时"
        )
    
    # 获取响应数据
    _, response_data = pending_requests.pop(request_id, (None, None))
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="未收到响应数据"
        )
    
    if not response_data.get("success"):
        error = response_data.get("error", "未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent处理失败: {error}"
        )
    
    return response_data.get("data", {})


def handle_workspace_response(message: Dict[str, Any]) -> None:
    """
    处理来自Agent的工作空间响应
    
    Args:
        message: 响应消息
    """
    request_id = message.get("request_id")
    msg_type = message.get("type", "unknown")
    print(f"[Workspace] 收到响应: {msg_type}, request_id: {request_id}")
    
    if not request_id:
        print(f"[Workspace] 警告: 响应消息缺少request_id")
        return
    
    if request_id not in pending_requests:
        print(f"[Workspace] 警告: 未找到对应的请求，request_id: {request_id}, 当前pending: {list(pending_requests.keys())}")
        return
    
    event, _ = pending_requests[request_id]
    pending_requests[request_id] = (event, message)
    print(f"[Workspace] 设置事件，request_id: {request_id}")
    event.set()


@router.get("/{environment_id}/workspace/list", response_model=APIResponse)
async def list_workspace_files(
    environment_id: str,
    path: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出工作空间文件"""
    # 检查环境是否存在
    environment = EnvironmentService.get_environment(db, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    # 检查环境是否在线
    if not environment.get("isOnline"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="环境离线，无法访问工作空间"
        )
    
    try:
        data = await send_workspace_request(
            environment_id,
            "workspace_list",
            {"path": path}
        )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取文件列表成功",
            data=data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件列表失败: {str(e)}"
        )


@router.get("/{environment_id}/workspace/read", response_model=APIResponse)
async def read_workspace_file(
    environment_id: str,
    path: str,
    encoding: str = "utf-8",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """读取工作空间文件"""
    environment = EnvironmentService.get_environment(db, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    if not environment.get("isOnline"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="环境离线，无法访问工作空间"
        )
    
    try:
        data = await send_workspace_request(
            environment_id,
            "workspace_read",
            {"path": path, "encoding": encoding}
        )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="读取文件成功",
            data=data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取文件失败: {str(e)}"
        )


@router.post("/{environment_id}/workspace/delete", response_model=APIResponse)
async def delete_workspace_file(
    environment_id: str,
    path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除工作空间文件或文件夹"""
    environment = EnvironmentService.get_environment(db, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    if not environment.get("isOnline"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="环境离线，无法访问工作空间"
        )
    
    try:
        data = await send_workspace_request(
            environment_id,
            "workspace_delete",
            {"path": path}
        )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="删除成功",
            data=data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.post("/{environment_id}/workspace/mkdir", response_model=APIResponse)
async def create_workspace_directory(
    environment_id: str,
    path: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建工作空间文件夹"""
    environment = EnvironmentService.get_environment(db, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="环境不存在"
        )
    
    if not environment.get("isOnline"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="环境离线，无法访问工作空间"
        )
    
    try:
        data = await send_workspace_request(
            environment_id,
            "workspace_mkdir",
            {"path": path}
        )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="创建文件夹成功",
            data=data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建文件夹失败: {str(e)}"
        )

