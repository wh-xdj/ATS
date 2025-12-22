"""测试环境模型"""
from sqlalchemy import Column, String, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base


class Environment(Base, BaseModel):
    """测试环境表"""
    __tablename__ = "environments"
    
    name = Column(String(100), nullable=False)
    api_url = Column(String(500))
    web_url = Column(String(500))
    database_config = Column(JSON)
    env_variables = Column(JSON)
    description = Column(Text)
    status = Column(Boolean, default=True, nullable=False, index=True)
    
    # 关系
    test_plans = relationship("TestPlan", back_populates="environment")
    executions = relationship("TestExecution", back_populates="environment")
    
    def __repr__(self):
        return f"<Environment(id={self.id}, name={self.name})>"

