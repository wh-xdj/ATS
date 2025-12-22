"""用户服务"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from models import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash
from fastapi import HTTPException, status


async def create_user(db: Session, user_data: UserCreate) -> User:
    """创建用户"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        department=user_data.department,
        status=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


async def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """获取用户"""
    return db.query(User).filter(User.id == user_id).first()


async def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[bool] = None
) -> tuple[List[User], int]:
    """获取用户列表"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if status_filter is not None:
        query = query.filter(User.status == status_filter)
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return users, total


async def update_user(db: Session, user_id: UUID, user_data: UserUpdate) -> User:
    """更新用户"""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新字段
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


async def delete_user(db: Session, user_id: UUID) -> bool:
    """删除用户"""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    db.delete(user)
    db.commit()
    
    return True

