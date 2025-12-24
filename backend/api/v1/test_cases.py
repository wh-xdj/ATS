"""测试用例相关 API（独立 URL 前缀）"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import APIResponse, ResponseStatus
from schemas.test_case import TestCaseCreate, TestCaseUpdate
from api.deps import get_current_user
from models import User
from services.test_case_service import TestCaseService
from utils.serializer import serialize_model, serialize_list


router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_test_cases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    module_id: Optional[str] = None,
    module_ids: Optional[str] = None,  # 逗号分隔的模块 ID 列表（包含子模块）
    status: Optional[str] = None,
    priority: Optional[str] = None,
    type: Optional[str] = None,
):
    """获取测试用例列表（按项目过滤，使用数据库持久化）"""
    result = TestCaseService.get_test_cases(
        db=db,
        project_id=project_id,
        page=page,
        size=size,
        search=search,
        module_id=module_id,
        module_ids=module_ids,  # 传递多个模块 ID
        status=status,
        priority=priority,
        type=type,
    )

    # 序列化items为camelCase
    serialized_items = serialize_list(result["items"], camel_case=True)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "items": serialized_items,
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "pages": result["pages"],
            "hasNext": result["hasNext"],
            "hasPrev": result["hasPrev"],
        },
    )


# 注意：/tree 必须在 /{case_id} 之前定义，否则会被错误匹配
@router.get("/tree", response_model=APIResponse)
async def get_case_tree(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用例树（包含模块和用例）"""
    tree_data = TestCaseService.get_case_tree(db=db, project_id=project_id)

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=tree_data,
    )


@router.get("/{case_id}", response_model=APIResponse)
async def get_test_case(
    case_id: str,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取测试用例详情"""
    test_case = TestCaseService.get_test_case(db=db, case_id=case_id)

    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    # 序列化为camelCase
    serialized_case = serialize_model(test_case, camel_case=True)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=serialized_case,
    )


@router.post("", response_model=APIResponse)
async def create_test_case(
    case_data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建测试用例（使用数据库持久化）"""
    try:
        # 确保steps不为None
        if case_data.steps is None:
            case_data.steps = []

        test_case = TestCaseService.create_test_case(
            db=db,
            case_data=case_data,
            current_user_id=str(current_user.id),
        )

        # 序列化为camelCase
        serialized_case = serialize_model(test_case, camel_case=True)
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="创建成功",
            data=serialized_case,
        )
    except Exception as e:
        import traceback
        print("创建测试用例失败:", traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")


@router.put("/{case_id}", response_model=APIResponse)
async def update_test_case(
    case_id: str,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新测试用例"""
    test_case = TestCaseService.update_test_case(
        db=db,
        case_id=case_id,
        case_data=case_data,
        current_user_id=str(current_user.id)
    )

    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    # 序列化为camelCase
    serialized_case = serialize_model(test_case, camel_case=True)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=serialized_case,
    )


@router.delete("/{case_id}", response_model=APIResponse)
async def delete_test_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除测试用例"""
    success = TestCaseService.delete_test_case(db=db, case_id=case_id)

    if not success:
        raise HTTPException(status_code=404, detail="测试用例不存在")

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功",
    )

