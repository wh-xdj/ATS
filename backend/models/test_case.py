"""测试用例模型"""
from sqlalchemy import Column, String, Text, ForeignKey, Float, DateTime, JSON, func
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base
import uuid


class TestCase(Base, BaseModel):
    """测试用例表"""
    __tablename__ = "test_cases"
    
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    # TODO: 当模块管理落库后，恢复外键约束 ForeignKey("modules.id")
    module_id = Column(String(36), nullable=True, index=True)
    case_code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    type = Column(String(50), nullable=False, index=True)  # functional, interface, ui, performance, security
    priority = Column(String(20), default="P2", nullable=False, index=True)  # P0, P1, P2, P3
    precondition = Column(Text)
    steps = Column(JSON, nullable=False)  # 结构化步骤存储
    expected_result = Column(Text)
    requirement_ref = Column(String(255))
    module_path = Column(String(500))
    level = Column(String(20))  # P0/P1/P2/P3
    executor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    tags = Column(JSON)  # ["回归", "冒烟"]
    status = Column(String(50), default="not_executed", nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # 关系
    project = relationship("Project", back_populates="test_cases")
    # 显式指定 primaryjoin，因为暂时移除了外键约束
    module = relationship(
        "Module",
        primaryjoin="TestCase.module_id == Module.id",
        foreign_keys=[module_id],
        back_populates="test_cases"
    )
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_cases")
    updater = relationship("User", foreign_keys=[updated_by], back_populates="updated_cases")
    attachments = relationship("CaseAttachment", back_populates="case", cascade="all, delete-orphan")
    plan_relations = relationship("PlanCaseRelation", back_populates="case", cascade="all, delete-orphan")
    executions = relationship("TestExecution", back_populates="case", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TestCase(id={self.id}, case_code={self.case_code}, name={self.name})>"


class CaseAttachment(Base):
    """用例附件表"""
    __tablename__ = "case_attachments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Float)
    file_type = Column(String(50))
    upload_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # 关系
    case = relationship("TestCase", back_populates="attachments")
    
    def __repr__(self):
        return f"<CaseAttachment(id={self.id}, file_name={self.file_name})>"

