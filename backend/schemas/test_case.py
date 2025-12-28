"""测试用例相关模式"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from datetime import datetime


class TestStep(BaseModel):
    """测试步骤"""
    step: int
    action: str
    expected: str


class TestCaseBase(BaseModel):
    """测试用例基础模式"""
    case_code: Optional[str] = None
    name: str
    type: str  # functional, interface, ui, performance, security
    priority: str = "P2"  # P0, P1, P2, P3
    precondition: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None  # JSONB格式，默认为None，在服务层处理
    expected_result: Optional[str] = None
    requirement_ref: Optional[str] = None
    module_path: Optional[str] = None
    level: Optional[str] = None
    tags: Optional[List[str]] = None
    is_automated: bool = False  # 是否自动化，默认否
    
    @field_validator('steps', mode='before')
    @classmethod
    def validate_steps(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []


class TestCaseCreate(TestCaseBase):
    """创建测试用例请求"""
    project_id: Union[UUID, str]  # 支持UUID或字符串
    module_id: Optional[Union[UUID, str]] = None
    executor_id: Optional[Union[UUID, str]] = None

    @field_validator('project_id', mode='before')
    @classmethod
    def validate_project_id(cls, v):
        if v is None:
            raise ValueError('project_id 不能为空')
        if isinstance(v, str):
            v = v.strip()
            if v == '':
                raise ValueError('project_id 不能为空')
            # 尝试将字符串转换为UUID，如果失败则保持为字符串
            try:
                from uuid import UUID
                return UUID(v)
            except (ValueError, AttributeError):
                # 如果不是有效的UUID格式，保持为字符串
                return v
        return v

    @field_validator('module_id', mode='before')
    @classmethod
    def validate_module_id(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == '':
                return None
            # 尝试转换为 UUID，如果失败保持为字符串
            try:
                from uuid import UUID
                return UUID(v)
            except (ValueError, AttributeError):
                # 如果不是有效的 UUID 格式，保持为字符串
                return v
        return v

    @field_validator('executor_id', mode='before')
    @classmethod
    def validate_executor_id(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == '':
                return None
            # 尝试转换为 UUID，如果失败保持为字符串
            try:
                from uuid import UUID
                return UUID(v)
            except (ValueError, AttributeError):
                # 如果不是有效的 UUID 格式，保持为字符串
                return v
        return v


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
    module_id: Optional[str] = None  # 支持移动用例到不同模块
    is_automated: Optional[bool] = None  # 是否自动化


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

