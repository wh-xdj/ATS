"""用户管理API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from database import get_db
from api.deps import get_current_active_user
from models import User
from schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from schemas.common import APIResponse, ResponseStatus, PaginationResponse
from services.user_service import create_user, get_user, get_users, update_user, delete_user
import math

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_user_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户列表"""
    skip = (page - 1) * size
    users, total = await get_users(db, skip=skip, limit=size, search=search, status_filter=status)
    
    pages = math.ceil(total / size) if total > 0 else 0
    
    user_responses = [UserResponse.model_validate(user) for user in users]
    
    pagination_data = PaginationResponse(
        items=user_responses,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=pagination_data.model_dump()
    )


@router.post("", response_model=APIResponse)
async def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建用户"""
    user = await create_user(db, user_data)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data=UserResponse.model_validate(user).model_dump()
    )


@router.get("/{user_id}", response_model=APIResponse)
async def get_user_detail(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户详情"""
    user = await get_user(db, user_id)
    
    if not user:
        return APIResponse(
            status=ResponseStatus.ERROR,
            message="用户不存在",
            code=404
        )
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=UserResponse.model_validate(user).model_dump()
    )


@router.put("/{user_id}", response_model=APIResponse)
async def update_user_endpoint(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新用户信息"""
    user = await update_user(db, user_id, user_data)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=UserResponse.model_validate(user).model_dump()
    )


@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除用户"""
    await delete_user(db, user_id)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )

