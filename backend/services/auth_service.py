"""认证服务"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import timedelta
from models import User
from core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from fastapi import HTTPException, status
from config import settings
from schemas.auth import TokenResponse
from schemas.user import UserResponse


async def authenticate_user(db: Session, username: str, password: str) -> User:
    """用户认证"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户账号已被禁用"
        )
    
    return user


async def create_tokens(user: User) -> TokenResponse:
    """创建访问令牌和刷新令牌"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    user_response = UserResponse.model_validate(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response
    )

