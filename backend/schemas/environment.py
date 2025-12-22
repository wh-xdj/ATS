"""环境相关模式"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class EnvironmentBase(BaseModel):
    """环境基础模式"""
    name: str
    api_url: Optional[str] = None
    web_url: Optional[str] = None
    database_config: Optional[Dict[str, Any]] = None
    env_variables: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class EnvironmentCreate(EnvironmentBase):
    """创建环境请求"""
    pass


class EnvironmentUpdate(BaseModel):
    """更新环境请求"""
    name: Optional[str] = None
    api_url: Optional[str] = None
    web_url: Optional[str] = None
    database_config: Optional[Dict[str, Any]] = None
    env_variables: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    status: Optional[bool] = None


class EnvironmentResponse(EnvironmentBase):
    """环境响应"""
    id: UUID
    status: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

