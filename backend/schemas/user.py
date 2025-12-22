"""用户相关模式"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模式"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None


class UserCreate(UserBase):
    """创建用户请求"""
    password: str


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    status: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应"""
    id: UUID
    status: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    items: list[UserResponse]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

