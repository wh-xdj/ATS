"""任务队列模型"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from database import Base
import uuid


class TaskQueue(Base):
    """任务队列表"""
    __tablename__ = "task_queue"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    environment_id = Column(String(36), ForeignKey("environments.id", ondelete="CASCADE"), nullable=False, index=True, comment="环境ID")
    suite_id = Column(String(36), ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False, index=True, comment="测试套ID")
    execution_id = Column(String(36), nullable=False, index=True, comment="执行ID")
    executor_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="执行人ID")
    status = Column(String(50), default="pending", nullable=False, index=True, comment="状态: pending, running, completed, failed, cancelled")
    priority = Column(Integer, default=0, nullable=False, comment="优先级，数字越大优先级越高")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True, comment="创建时间")
    started_at = Column(DateTime(timezone=True), nullable=True, comment="开始执行时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    
    # 关系
    environment = relationship("Environment")
    suite = relationship("TestSuite")
    executor = relationship("User")
    
    def __repr__(self):
        return f"<TaskQueue(id={self.id}, environment_id={self.environment_id}, suite_id={self.suite_id}, status={self.status})>"

