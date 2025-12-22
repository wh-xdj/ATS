"""权限控制相关功能"""
from functools import wraps
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, Permission, Role, UserRole, RolePermission, ProjectPermission


# 系统权限定义
SYSTEM_PERMISSIONS = {
    # 用户管理
    "user:create": "创建用户",
    "user:read": "查看用户",
    "user:update": "更新用户",
    "user:delete": "删除用户",
    
    # 项目管理
    "project:create": "创建项目",
    "project:read": "查看项目",
    "project:update": "更新项目",
    "project:delete": "删除项目",
    "project:manage_members": "管理项目成员",
    
    # 用例管理
    "test_case:create": "创建用例",
    "test_case:read": "查看用例",
    "test_case:update": "更新用例",
    "test_case:delete": "删除用例",
    "test_case:import": "导入用例",
    "test_case:export": "导出用例",
    
    # 计划管理
    "test_plan:create": "创建计划",
    "test_plan:read": "查看计划",
    "test_plan:update": "更新计划",
    "test_plan:delete": "删除计划",
    "test_plan:execute": "执行计划",
    
    # 执行管理
    "test_execution:read": "查看执行记录",
    "test_execution:update": "更新执行结果",
    
    # 报告管理
    "report:create": "生成报告",
    "report:read": "查看报告",
    "report:delete": "删除报告",
    
    # 系统管理
    "system:manage": "系统管理"
}


def has_global_permission(db: Session, user_id: UUID, resource: str, action: str) -> bool:
    """检查全局权限"""
    permission_code = f"{resource}:{action}"
    
    # 查询用户是否有该权限
    query = db.query(Permission).join(
        RolePermission, Permission.id == RolePermission.permission_id
    ).join(
        Role, RolePermission.role_id == Role.id
    ).join(
        UserRole, Role.id == UserRole.role_id
    ).filter(
        UserRole.user_id == user_id,
        Permission.code == permission_code
    )
    
    return query.first() is not None


def has_project_permission(
    db: Session, 
    user_id: UUID, 
    project_id: UUID, 
    resource: str, 
    action: str
) -> bool:
    """检查项目权限"""
    permission_code = f"{resource}:{action}"
    
    # 查询用户在该项目是否有该权限
    query = db.query(ProjectPermission).join(
        Permission, ProjectPermission.permission_id == Permission.id
    ).filter(
        ProjectPermission.user_id == user_id,
        ProjectPermission.project_id == project_id,
        Permission.code == permission_code
    )
    
    return query.first() is not None


def check_permission(resource: str, action: str):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user和db
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证"
                )
            
            # 检查全局权限
            if has_global_permission(db, current_user.id, resource, action):
                return await func(*args, **kwargs)
            
            # 检查项目权限
            project_id = kwargs.get("project_id")
            if project_id and has_project_permission(db, current_user.id, project_id, resource, action):
                return await func(*args, **kwargs)
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return wrapper
    return decorator

