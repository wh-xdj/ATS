"""测试套模型"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base
import uuid


class TestSuite(Base, BaseModel):
    """测试套表"""
    __tablename__ = "test_suites"
    
    plan_id = Column(String(36), ForeignKey("test_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, comment="测试套名称")
    description = Column(Text, comment="测试套描述")
    git_enabled = Column(String(10), default="false", nullable=False, comment="Git配置是否启用: true/false")
    git_repo_url = Column(String(500), nullable=True, comment="Git代码仓库地址（可选）")
    git_branch = Column(String(100), default="main", nullable=True, comment="Git分支（可选）")
    git_token = Column(Text, nullable=True, comment="Git登录Token（可选）")
    environment_id = Column(String(36), ForeignKey("environments.id"), nullable=False, index=True, comment="执行环境ID")
    execution_command = Column(Text, nullable=False, comment="执行命令")
    case_ids = Column(JSON, nullable=False, comment="测试用例ID列表")
    status = Column(String(50), default="pending", nullable=False, index=True, comment="状态: pending, running, completed, failed")
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # 关系
    plan = relationship("TestPlan", back_populates="test_suites")
    environment = relationship("Environment", back_populates="test_suites")
    executions = relationship("TestSuiteExecution", back_populates="suite", cascade="all, delete-orphan")
    logs = relationship("TestSuiteLog", back_populates="suite", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TestSuite(id={self.id}, name={self.name}, plan_id={self.plan_id})>"


class TestSuiteExecution(Base):
    """测试套执行记录表"""
    __tablename__ = "test_suite_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    suite_id = Column(String(36), ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    environment_id = Column(String(36), ForeignKey("environments.id"), nullable=False, index=True)
    executor_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    result = Column(String(50), nullable=False, index=True, comment="执行结果: passed, failed, error, skipped")
    duration = Column(String(20), comment="执行耗时")
    log_output = Column(Text, comment="执行日志输出")
    error_message = Column(Text, comment="错误信息")
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    suite = relationship("TestSuite", back_populates="executions")
    case = relationship("TestCase")
    environment = relationship("Environment")
    executor = relationship("User")
    
    def __repr__(self):
        return f"<TestSuiteExecution(id={self.id}, suite_id={self.suite_id}, case_id={self.case_id}, result={self.result})>"


class TestSuiteLog(Base):
    """测试套实时日志表"""
    __tablename__ = "test_suite_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    suite_id = Column(String(36), ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False, index=True)
    execution_id = Column(String(36), nullable=True, index=True, comment="执行ID，用于关联同一次执行的所有日志")
    message = Column(Text, nullable=False, comment="日志消息（多行，用换行符分隔）")
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关系
    suite = relationship("TestSuite", back_populates="logs")
    
    def __repr__(self):
        return f"<TestSuiteLog(id={self.id}, suite_id={self.suite_id})>"

