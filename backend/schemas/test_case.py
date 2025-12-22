"""测试用例相关模式"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class TestStep(BaseModel):
    """测试步骤"""
    step: int
    action: str
    expected: str


class TestCaseBase(BaseModel):
    """测试用例基础模式"""
    case_code: str
    name: str
    type: str  # functional, interface, ui, performance, security
    priority: str = "medium"  # P0, P1, P2, P3
    precondition: Optional[str] = None
    steps: List[Dict[str, Any]]  # JSONB格式
    expected_result: Optional[str] = None
    requirement_ref: Optional[str] = None
    module_path: Optional[str] = None
    level: Optional[str] = None
    tags: Optional[List[str]] = None


class TestCaseCreate(TestCaseBase):
    """创建测试用例请求"""
    module_id: Optional[UUID] = None
    executor_id: Optional[UUID] = None


class TestCaseUpdate(BaseModel):
    """更新测试用例请求"""
    name: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    precondition: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class TestCaseResponse(TestCaseBase):
    """测试用例响应"""
    id: UUID
    project_id: UUID
    module_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    """测试用例列表响应"""
    items: list[TestCaseResponse]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

