"""角色和权限模型"""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Table, DateTime, func
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base
import uuid


class Role(Base, BaseModel):
    """角色表"""
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_system = Column(Boolean, default=False, nullable=False)  # 系统内置角色不可删除
    
    # 关系
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base, BaseModel):
    """权限表"""
    __tablename__ = "permissions"
    
    code = Column(String(100), unique=True, nullable=False, index=True)  # 权限代码
    name = Column(String(100), nullable=False)
    resource = Column(String(50), nullable=False, index=True)  # test_case, test_plan, project, user等
    action = Column(String(50), nullable=False)  # create, read, update, delete, execute等
    description = Column(Text)
    
    # 关系
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    project_permissions = relationship("ProjectPermission", back_populates="permission", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, code={self.code})>"


class UserRole(Base):
    """用户角色关联表"""
    __tablename__ = "user_roles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(Base):
    """角色权限关联表"""
    __tablename__ = "role_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class ProjectPermission(Base):
    """项目权限表"""
    __tablename__ = "project_permissions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    granted_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    project = relationship("Project", back_populates="project_permissions")
    user = relationship("User", back_populates="project_permissions", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    permission = relationship("Permission", back_populates="project_permissions")
    
    def __repr__(self):
        return f"<ProjectPermission(project_id={self.project_id}, user_id={self.user_id}, permission_id={self.permission_id})>"

