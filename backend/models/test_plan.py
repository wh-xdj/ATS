"""测试计划模型"""
from sqlalchemy import Column, String, Text, Date, ForeignKey, DateTime, Integer, JSON, func
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base
import uuid


class TestPlan(Base, BaseModel):
    """测试计划表"""
    __tablename__ = "test_plans"
    
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    plan_type = Column(String(50), default="functional", nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    cron_expression = Column(String(100))
    environment_config = Column(JSON)
    status = Column(String(50), default="not_started", nullable=False, index=True)
    environment_id = Column(String(36), ForeignKey("environments.id"), nullable=True)
    
    # 关系
    project = relationship("Project", back_populates="test_plans")
    owner = relationship("User", foreign_keys=[owner_id])
    environment = relationship("Environment", back_populates="test_plans")
    case_relations = relationship("PlanCaseRelation", back_populates="plan", cascade="all, delete-orphan")
    executions = relationship("TestExecution", back_populates="plan")
    reports = relationship("TestReport", back_populates="plan")
    
    def __repr__(self):
        return f"<TestPlan(id={self.id}, plan_number={self.plan_number}, name={self.name})>"


class PlanCaseRelation(Base):
    """计划用例关联表"""
    __tablename__ = "plan_case_relations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("test_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    execution_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    plan = relationship("TestPlan", back_populates="case_relations")
    case = relationship("TestCase", back_populates="plan_relations")
    
    def __repr__(self):
        return f"<PlanCaseRelation(plan_id={self.plan_id}, case_id={self.case_id})>"

