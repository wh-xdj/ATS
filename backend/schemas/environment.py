"""环境相关模式"""
from pydantic import BaseModel, model_validator
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class EnvironmentBase(BaseModel):
    """环境基础模式"""
    name: str
    tags: Optional[str] = None
    remote_work_dir: Optional[str] = None
    # 兼容前端camelCase字段名（仅用于接收，不存储）
    remoteWorkDir: Optional[str] = None
    reconnect_delay: Optional[str] = "30"  # Agent重连延迟时间（秒）
    reconnectDelay: Optional[str] = None  # 兼容前端camelCase
    # 兼容旧字段
    api_url: Optional[str] = None
    web_url: Optional[str] = None
    database_config: Optional[Dict[str, Any]] = None
    env_variables: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def handle_field_aliases(cls, data: Any) -> Any:
        """处理字段名兼容：将remoteWorkDir转换为remote_work_dir"""
        if isinstance(data, dict):
            # 如果收到remoteWorkDir但没有remote_work_dir，则转换
            if 'remoteWorkDir' in data and 'remote_work_dir' not in data:
                data['remote_work_dir'] = data.pop('remoteWorkDir')
            # 如果两个字段都存在，优先使用remote_work_dir
            elif 'remoteWorkDir' in data and 'remote_work_dir' in data:
                if not data.get('remote_work_dir'):
                    data['remote_work_dir'] = data.pop('remoteWorkDir')
                else:
                    data.pop('remoteWorkDir', None)
        return data


class EnvironmentCreate(EnvironmentBase):
    """创建环境请求（节点配置）"""
    pass


class EnvironmentUpdate(BaseModel):
    """更新环境请求"""
    name: Optional[str] = None
    tags: Optional[str] = None
    remote_work_dir: Optional[str] = None
    # 兼容前端camelCase字段名（仅用于接收，不存储）
    remoteWorkDir: Optional[str] = None
    reconnect_delay: Optional[str] = None  # Agent重连延迟时间（秒）
    reconnectDelay: Optional[str] = None  # 兼容前端camelCase
    # 兼容旧字段
    api_url: Optional[str] = None
    web_url: Optional[str] = None
    database_config: Optional[Dict[str, Any]] = None
    env_variables: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    status: Optional[bool] = None
    
    @model_validator(mode='before')
    @classmethod
    def handle_field_aliases(cls, data: Any) -> Any:
        """处理字段名兼容：将remoteWorkDir转换为remote_work_dir"""
        if isinstance(data, dict):
            # 如果收到remoteWorkDir但没有remote_work_dir，则转换
            if 'remoteWorkDir' in data and 'remote_work_dir' not in data:
                data['remote_work_dir'] = data.pop('remoteWorkDir')
            # 如果两个字段都存在，优先使用remote_work_dir
            elif 'remoteWorkDir' in data and 'remote_work_dir' in data:
                if not data.get('remote_work_dir'):
                    data['remote_work_dir'] = data.pop('remoteWorkDir')
                else:
                    data.pop('remoteWorkDir', None)
        return data


class EnvironmentResponse(EnvironmentBase):
    """环境响应（包含节点信息）"""
    id: UUID
    # 节点信息（从agent获取）
    node_ip: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    disk_info: Optional[Dict[str, Any]] = None
    memory_info: Optional[Dict[str, Any]] = None
    cpu_info: Optional[Dict[str, Any]] = None
    # 节点状态
    is_online: bool = False
    last_heartbeat: Optional[datetime] = None
    # 其他字段
    reconnect_delay: str = "30"  # Agent重连延迟时间（秒）
    status: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

