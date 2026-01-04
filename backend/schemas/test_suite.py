"""测试套相关模式"""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class TestSuiteBase(BaseModel):
    """测试套基础模式"""
    name: str
    description: Optional[str] = None
    git_enabled: Optional[str] = "false"  # Git配置是否启用: true/false
    git_repo_url: Optional[str] = None  # 可选
    git_branch: Optional[str] = "main"  # 可选
    git_token: Optional[str] = None  # 可选
    environment_id: str
    execution_command: str
    case_ids: List[str]


class TestSuiteCreate(TestSuiteBase):
    """创建测试套请求"""
    plan_id: str


class TestSuiteUpdate(BaseModel):
    """更新测试套请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    git_enabled: Optional[str] = None  # Git配置是否启用: true/false
    git_repo_url: Optional[str] = None
    git_branch: Optional[str] = None
    git_token: Optional[str] = None
    environment_id: Optional[str] = None
    execution_command: Optional[str] = None
    case_ids: Optional[List[str]] = None
    status: Optional[str] = None
    plan_id: Optional[str] = None  # 允许修改关联的测试计划


class TestSuiteResponse(TestSuiteBase):
    """测试套响应"""
    id: str
    plan_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class TestSuiteExecutionResponse(BaseModel):
    """测试套执行记录响应"""
    id: str
    suite_id: str
    case_id: str
    case_name: Optional[str] = None
    environment_id: str
    environment_name: Optional[str] = None
    executor_id: str
    result: str
    duration: Optional[str] = None
    log_output: Optional[str] = None
    error_message: Optional[str] = None
    executed_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestSuiteCancelRequest(BaseModel):
    """取消测试套执行请求"""
    executionId: Optional[str] = None
    
    class Config:
        populate_by_name = True

