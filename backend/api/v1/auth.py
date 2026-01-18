"""认证相关API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.auth import LoginRequest, LoginResponse, RefreshTokenRequest
from schemas.common import APIResponse, ResponseStatus
from services.auth_service import authenticate_user, create_tokens
from core.security import verify_token
from models import User
from api.deps import get_current_user
from core.logger import logger

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        user = await authenticate_user(db, login_data.username, login_data.password)
        token_data = await create_tokens(user)
        
        return LoginResponse(
            status=ResponseStatus.SUCCESS,
            message="登录成功",
            data=token_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"用户登录失败: username={login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录失败"
        )


@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        user_id = verify_token(refresh_data.refresh_token, "refresh")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        token_data = await create_tokens(user)
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="令牌刷新成功",
            data=token_data.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("刷新令牌失败")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效"
        )


@router.post("/logout")
async def logout():
    """用户登出"""
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="登出成功"
    )


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    try:
        from schemas.user import UserResponse
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=UserResponse.model_validate(current_user).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取用户信息失败: user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

