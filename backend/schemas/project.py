"""项目相关模式"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ProjectBase(BaseModel):
    """项目基础模式"""
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """创建项目请求"""
    owner_id: Optional[UUID] = None  # 可选，如果不提供则使用当前登录用户


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    """项目响应"""
    id: UUID
    owner_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    items: list[ProjectResponse]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

