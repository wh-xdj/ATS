"""筛选字段配置模型"""
from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel
from database import Base


class FilterField(Base, BaseModel):
    """筛选字段配置表"""
    __tablename__ = "filter_fields"
    
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    field_key = Column(String(100), nullable=False, comment="字段键名，如：id, name, priority")
    field_label = Column(String(100), nullable=False, comment="字段显示名称")
    field_type = Column(String(50), nullable=False, comment="字段类型：text, select, number, date, tags, module")
    operators = Column(JSON, comment="允许的操作符列表，为空则使用默认")
    options = Column(JSON, comment="选项列表（用于select类型）")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认字段")
    
    # 关系
    project = relationship("Project", backref="filter_fields")
    
    def __repr__(self):
        return f"<FilterField(id={self.id}, field_key={self.field_key}, field_label={self.field_label})>"
