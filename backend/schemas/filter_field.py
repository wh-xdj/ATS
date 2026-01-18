"""筛选字段配置相关模式"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID


class FilterFieldBase(BaseModel):
    """筛选字段基础模式"""
    field_key: str
    field_label: str
    field_type: str  # text, select, number, date, tags, module
    operators: Optional[List[str]] = None
    options: Optional[List[Dict[str, Any]]] = None
    sort_order: int = 0
    is_enabled: bool = True
    is_default: bool = False


class FilterFieldCreate(FilterFieldBase):
    """创建筛选字段请求"""
    project_id: str


class FilterFieldUpdate(BaseModel):
    """更新筛选字段请求"""
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    operators: Optional[List[str]] = None
    options: Optional[List[Dict[str, Any]]] = None
    sort_order: Optional[int] = None
    is_enabled: Optional[bool] = None
    is_default: Optional[bool] = None


class FilterFieldResponse(FilterFieldBase):
    """筛选字段响应"""
    id: UUID
    project_id: UUID
    
    class Config:
        from_attributes = True
