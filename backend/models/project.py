"""项目模型"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base
import uuid


class Project(Base, BaseModel):
    """项目表"""
    __tablename__ = "projects"
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), default="active", nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # 关系
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")
    test_plans = relationship("TestPlan", back_populates="project", cascade="all, delete-orphan")
    test_reports = relationship("TestReport", back_populates="project")
    project_permissions = relationship("ProjectPermission", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"


class ProjectMember(Base):
    """项目成员表"""
    __tablename__ = "project_members"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="member", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")
    
    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id})>"

