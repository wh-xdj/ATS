"""环境相关API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from models import Environment
from schemas.environment import EnvironmentCreate, EnvironmentUpdate, EnvironmentResponse
from schemas.common import APIResponse, ResponseStatus
from api.deps import get_current_user
from models import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_environments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取环境列表"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    environments = [
        {
            "id": "env_1",
            "name": "测试环境",
            "apiUrl": "https://test-api.example.com",
            "webUrl": "https://test.example.com",
            "databaseConfig": {
                "host": "test-db.example.com",
                "port": 3306,
                "database": "test_db"
            },
            "envVariables": {
                "API_KEY": "test_key",
                "ENV": "test"
            },
            "description": "测试环境描述",
            "status": True,
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        },
        {
            "id": "env_2",
            "name": "预发布环境",
            "apiUrl": "https://staging-api.example.com",
            "webUrl": "https://staging.example.com",
            "databaseConfig": {
                "host": "staging-db.example.com",
                "port": 3306,
                "database": "staging_db"
            },
            "envVariables": {
                "API_KEY": "staging_key",
                "ENV": "staging"
            },
            "description": "预发布环境描述",
            "status": True,
            "createdAt": "2024-01-02T00:00:00",
            "updatedAt": "2024-01-02T00:00:00"
        }
    ]
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=environments
    )


@router.get("/{environment_id}", response_model=APIResponse)
async def get_environment(
    environment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取环境详情"""
    # TODO: 从数据库获取真实数据
    environment = {
        "id": str(environment_id),
        "name": "测试环境",
        "apiUrl": "https://test-api.example.com",
        "webUrl": "https://test.example.com",
        "databaseConfig": {
            "host": "test-db.example.com",
            "port": 3306,
            "database": "test_db"
        },
        "envVariables": {
            "API_KEY": "test_key",
            "ENV": "test"
        },
        "description": "测试环境描述",
        "status": True,
        "createdAt": "2024-01-01T00:00:00",
        "updatedAt": "2024-01-01T00:00:00"
    }
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=environment
    )


@router.post("", response_model=APIResponse)
async def create_environment(
    environment_data: EnvironmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建环境"""
    # TODO: 实现真实的创建逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data={
            "id": "env_new",
            "name": environment_data.name,
            "apiUrl": environment_data.api_url,
            "webUrl": environment_data.web_url,
            "databaseConfig": environment_data.database_config,
            "envVariables": environment_data.env_variables,
            "description": environment_data.description,
            "status": True,
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        }
    )


@router.put("/{environment_id}", response_model=APIResponse)
async def update_environment(
    environment_id: UUID,
    environment_data: EnvironmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新环境"""
    # TODO: 实现真实的更新逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data={
            "id": str(environment_id),
            "name": environment_data.name or "环境名称",
            "apiUrl": environment_data.api_url,
            "webUrl": environment_data.web_url,
            "status": environment_data.status if environment_data.status is not None else True
        }
    )


@router.delete("/{environment_id}", response_model=APIResponse)
async def delete_environment(
    environment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除环境"""
    # TODO: 实现真实的删除逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )


@router.post("/{environment_id}/test", response_model=APIResponse)
async def test_environment_connection(
    environment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """测试环境连接"""
    # TODO: 实现真实的连接测试逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="连接测试成功",
        data={
            "success": True,
            "message": "环境连接正常"
        }
    )


@router.post("/{environment_id}/enable", response_model=APIResponse)
async def enable_environment(
    environment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """启用环境"""
    # TODO: 实现真实的启用逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="环境已启用"
    )


@router.post("/{environment_id}/disable", response_model=APIResponse)
async def disable_environment(
    environment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """禁用环境"""
    # TODO: 实现真实的禁用逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="环境已禁用"
    )

