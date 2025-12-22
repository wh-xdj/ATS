"""测试执行模型"""
from sqlalchemy import Column, String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
import uuid


class TestExecution(Base):
    """测试执行表"""
    __tablename__ = "test_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    plan_id = Column(String(36), ForeignKey("test_plans.id"), nullable=True, index=True)
    case_id = Column(String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    executor_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    environment_id = Column(String(36), ForeignKey("environments.id"), nullable=True)
    result = Column(String(50), nullable=False, index=True)  # passed, failed, blocked, skipped
    duration = Column(Float)  # 执行耗时（秒）
    notes = Column(Text)
    error_message = Column(Text)
    execution_log = Column(Text)
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    plan = relationship("TestPlan", back_populates="executions")
    case = relationship("TestCase", back_populates="executions")
    executor = relationship("User", back_populates="executed_cases")
    environment = relationship("Environment", back_populates="executions")
    attachments = relationship("ExecutionAttachment", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TestExecution(id={self.id}, case_id={self.case_id}, result={self.result})>"


class ExecutionAttachment(Base):
    """执行附件表"""
    __tablename__ = "execution_attachments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(36), ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Float)
    file_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    execution = relationship("TestExecution", back_populates="attachments")
    
    def __repr__(self):
        return f"<ExecutionAttachment(id={self.id}, file_name={self.file_name})>"

