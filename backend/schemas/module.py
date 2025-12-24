# -*- coding: utf-8 -*-
"""模块相关 Schema"""
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class ModuleBase(BaseModel):
    """模块基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="模块名称")
    parent_id: Optional[str] = Field(None, alias="parentId", description="父模块ID")
    sort_order: int = Field(default=0, alias="sortOrder", description="排序顺序")
    description: Optional[str] = Field(None, description="模块描述")

    class Config:
        populate_by_name = True


class ModuleCreate(ModuleBase):
    """创建模块 Schema"""
    pass


class ModuleUpdate(BaseModel):
    """更新模块 Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模块名称")
    parent_id: Optional[str] = Field(None, alias="parentId", description="父模块ID")
    sort_order: Optional[int] = Field(None, alias="sortOrder", description="排序顺序")
    description: Optional[str] = Field(None, description="模块描述")

    class Config:
        populate_by_name = True


class ModuleResponse(BaseModel):
    """模块响应 Schema"""
    id: str
    project_id: str = Field(..., alias="projectId")
    name: str
    parent_id: Optional[str] = Field(None, alias="parentId")
    level: int
    sort_order: int = Field(..., alias="sortOrder")
    description: Optional[str] = None
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ModuleTreeNode(BaseModel):
    """模块树节点 Schema"""
    key: str
    title: str
    type: str = "module"
    level: Optional[str] = None
    children: List["ModuleTreeNode"] = []

    class Config:
        from_attributes = True


# 为了支持递归引用
ModuleTreeNode.model_rebuild()

