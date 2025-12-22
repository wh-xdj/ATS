"""测试报告模型"""
from sqlalchemy import Column, String, Text, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base


class TestReport(Base, BaseModel):
    """测试报告表"""
    __tablename__ = "test_reports"
    
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    plan_id = Column(String(36), ForeignKey("test_plans.id"), nullable=True, index=True)
    report_type = Column(String(50), nullable=False, index=True)  # execution, plan, project, custom
    report_name = Column(String(255), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    report_data = Column(JSON)  # 报告数据
    summary = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # 关系
    project = relationship("Project", back_populates="test_reports")
    plan = relationship("TestPlan", back_populates="reports")
    
    def __repr__(self):
        return f"<TestReport(id={self.id}, report_name={self.report_name})>"

