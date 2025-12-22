"""认证相关模式"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from schemas.user import UserResponse


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class LoginResponse(BaseModel):
    """登录响应"""
    status: str = "success"
    message: str = "登录成功"
    data: TokenResponse

