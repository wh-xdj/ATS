"""模块模型"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base


class Module(Base, BaseModel):
    """模块表"""
    __tablename__ = "modules"
    
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(String(36), ForeignKey("modules.id"), nullable=True, index=True)
    level = Column(Integer, default=1, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    description = Column(Text)
    
    # 关系
    project = relationship("Project", back_populates="modules")
    parent = relationship("Module", remote_side="Module.id", backref="children")
    # 显式指定 primaryjoin，因为 test_cases.module_id 暂无外键约束
    test_cases = relationship(
        "TestCase",
        primaryjoin="Module.id == foreign(TestCase.module_id)",
        back_populates="module"
    )
    
    def __repr__(self):
        return f"<Module(id={self.id}, name={self.name}, project_id={self.project_id})>"

