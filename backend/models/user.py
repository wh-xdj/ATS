"""用户模型"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base


class User(Base, BaseModel):
    """用户表"""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    phone = Column(String(20))
    department = Column(String(100))
    status = Column(Boolean, default=True, nullable=False)
    
    # 关系
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    created_projects = relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    project_permissions = relationship("ProjectPermission", back_populates="user", foreign_keys="ProjectPermission.user_id", cascade="all, delete-orphan")
    granted_project_permissions = relationship("ProjectPermission", foreign_keys="ProjectPermission.granted_by")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    created_cases = relationship("TestCase", back_populates="creator", foreign_keys="TestCase.created_by")
    updated_cases = relationship("TestCase", back_populates="updater", foreign_keys="TestCase.updated_by")
    executed_cases = relationship("TestExecution", back_populates="executor")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

