"""通用模式"""
from typing import Optional, Any, List
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from utils.datetime_utils import beijing_now_iso


class ResponseStatus(str, Enum):
    """响应状态"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class APIResponse(BaseModel):
    """统一API响应格式"""
    status: ResponseStatus
    message: str
    data: Optional[Any] = None
    code: int = 200
    timestamp: str = beijing_now_iso()
    request_id: Optional[str] = None


class PaginationResponse(BaseModel):
    """分页响应格式"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

