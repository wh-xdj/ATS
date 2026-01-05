# -*- coding: utf-8 -*-
"""项目相关API"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from database import get_db
from models import Project
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from schemas.test_case import TestCaseCreate, TestCaseUpdate, TestCaseResponse
from schemas.module import ModuleCreate, ModuleUpdate
from schemas.common import APIResponse, ResponseStatus
from api.deps import get_current_user
from models import User
from utils.serializer import serialize_model, serialize_list
from services.module_service import ModuleService
import uuid

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目列表（使用数据库持久化）"""
    # 查询所有项目，按创建时间倒序
    query = db.query(Project).order_by(Project.created_at.desc())
    items = query.all()

    # 获取所有相关的用户ID
    user_ids = set()
    for item in items:
        if item.created_by:
            user_ids.add(item.created_by)
        if item.owner_id:
            user_ids.add(item.owner_id)
    
    # 批量查询用户信息
    users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    user_map = {str(u.id): u.username or u.email or str(u.id) for u in users}
    
    # 构建项目列表，包含用户名
    project_list = []
    for item in items:
        project_data = serialize_model(item, camel_case=True)
        # 添加用户名字段
        project_data['createdByName'] = user_map.get(item.created_by, 'Unknown')
        project_data['updatedByName'] = user_map.get(item.owner_id, user_map.get(item.created_by, 'Unknown'))
        project_list.append(project_data)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=project_list,
    )


@router.get("/{project_id}", response_model=APIResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目详情（数据库）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    # 使用序列化器统一转换为camelCase
    data = serialize_model(project, camel_case=True)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=data,
    )


@router.post("", response_model=APIResponse)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建项目（写入数据库）"""
    owner_id = str(project_data.owner_id) if project_data.owner_id else str(current_user.id)

    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id,
        status="active",
        created_by=str(current_user.id),
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "ownerId": project.owner_id,
        "status": project.status,
        "createdAt": project.created_at.isoformat() if project.created_at else "",
        "updatedAt": project.updated_at.isoformat() if project.updated_at else "",
        "createdBy": project.created_by or project.owner_id,
    }

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data=data,
    )


@router.put("/{project_id}", response_model=APIResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新项目（数据库）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.status is not None:
        project.status = project_data.status

    db.commit()
    db.refresh(project)

    data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "ownerId": project.owner_id,
        "status": project.status,
        "createdAt": project.created_at.isoformat() if project.created_at else "",
        "updatedAt": project.updated_at.isoformat() if project.updated_at else "",
        "createdBy": project.created_by or project.owner_id,
    }

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=data,
    )


@router.delete("/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除项目（数据库，级联删除测试用例等）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    db.delete(project)
    db.commit()

    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功",
    )


@router.get("/{project_id}/modules", response_model=APIResponse)
async def get_project_modules(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目模块列表（数据库持久化，包含用例数量）"""
    module_list, total_case_count = ModuleService.get_modules_with_case_count(db, project_id)
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "modules": module_list,
            "totalCaseCount": total_case_count
        }
    )


@router.post("/{project_id}/modules", response_model=APIResponse)
async def create_module(
    project_id: str,
    module_data: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建模块（数据库持久化）"""
    try:
        module = ModuleService.create_module(
            db=db,
            project_id=project_id,
            module_data=module_data,
            current_user_id=str(current_user.id)
        )
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="创建成功",
            data=serialize_model(module, camel_case=True)
        )
    except Exception as e:
        from core.logger import logger
        logger.exception("创建模块失败")
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")


@router.put("/{project_id}/modules/{module_id}", response_model=APIResponse)
async def update_module(
    project_id: str,
    module_id: str,
    module_data: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新模块（数据库持久化）"""
    module = ModuleService.update_module(
        db=db,
        module_id=module_id,
        module_data=module_data,
        current_user_id=str(current_user.id)
    )
    
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data=serialize_model(module, camel_case=True)
    )


@router.delete("/{project_id}/modules/{module_id}", response_model=APIResponse)
async def delete_module(
    project_id: str,
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除模块（数据库持久化）"""
    success = ModuleService.delete_module(db=db, module_id=module_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="模块不存在")
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )


@router.get("/{project_id}/case-tree", response_model=APIResponse)
async def get_case_tree(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用例树（包含模块和用例）"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    tree_data = [
        {
            "key": "module_1",
            "title": "模块A",
            "type": "module",
            "level": "P0",
            "children": [
                {
                    "key": "case_1",
                    "title": "测试用例001",
                    "type": "case",
                    "caseCode": "TC-001",
                    "level": "P0",
                    "tags": ["回归", "冒烟"]
                },
                {
                    "key": "case_2",
                    "title": "测试用例002",
                    "type": "case",
                    "caseCode": "TC-002",
                    "level": "P1",
                    "tags": ["功能"]
                }
            ]
        },
        {
            "key": "module_2",
            "title": "模块B",
            "type": "module",
            "level": "P1",
            "children": [
                {
                    "key": "case_3",
                    "title": "测试用例003",
                    "type": "case",
                    "caseCode": "TC-003",
                    "level": "P1",
                    "tags": ["接口"]
                }
            ]
        },
        {
            "key": "case_4",
            "title": "测试用例004（无模块）",
            "type": "case",
            "caseCode": "TC-004",
            "level": "P2",
            "tags": ["UI"]
        }
    ]
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=tree_data
    )


# 测试用例相关路由
@router.get("/{project_id}/cases", response_model=APIResponse)
async def get_test_cases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20,
    search: str = None,
    module_id: str = None,
    status: str = None,
    priority: str = None,
    type: str = None
):
    """获取测试用例列表"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    cases = [
        {
            "id": "case_1",
            "projectId": str(project_id),
            "moduleId": "module_1",
            "caseCode": "TC-001",
            "name": "测试用例001",
            "type": "functional",
            "priority": "P0",
            "status": "not_executed",
            "tags": ["回归", "冒烟"],
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        }
    ]
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "items": cases,
            "total": len(cases),
            "page": page,
            "size": size,
            "pages": 1,
            "hasNext": False,
            "hasPrev": False
        }
    )


@router.get("/{project_id}/cases/export")
async def export_test_cases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    module_id: str = None,
    module_ids: str = None,  # 逗号分隔的模块 ID 列表（包含子模块）
    status: str = None,
    priority: str = None,
    type: str = None,
):
    """导出测试用例到Excel"""
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from utils.excel_handler import export_to_excel
    from services.test_case_service import TestCaseService
    from uuid import UUID
    from models.module import Module
    
    try:
        # 使用服务层获取测试用例
        # 获取所有符合条件的用例（不分页）
        result = TestCaseService.get_test_cases(
            db=db,
            project_id=project_id,
            page=1,
            size=99999,  # 获取所有用例
            search=None,
            module_id=module_id,
            module_ids=module_ids,
            status=status,
            priority=priority,
            type=type,
        )
        
        cases = result["items"]
        
        # 获取模块信息用于显示模块路径
        modules = db.query(Module).filter(Module.project_id == project_id).all()
        # 构建模块映射：id -> Module对象
        module_dict = {str(m.id): m for m in modules}
        
        # 构建模块路径的函数
        def get_module_path(module_id: str) -> str:
            """递归构建模块的完整路径，格式：父模块/子模块"""
            if not module_id or module_id not in module_dict:
                return ""
            
            module = module_dict[module_id]
            path_parts = [module.name]
            
            # 递归向上查找父模块
            current_module = module
            while current_module.parent_id:
                parent_id = str(current_module.parent_id)
                if parent_id in module_dict:
                    parent_module = module_dict[parent_id]
                    path_parts.insert(0, parent_module.name)
                    current_module = parent_module
                else:
                    break
            
            return "/".join(path_parts)
        
        # 获取用户信息用于显示创建人和更新人
        from models import User
        user_ids = set()
        for case in cases:
            if case.created_by:
                user_ids.add(case.created_by)
            if case.updated_by:
                user_ids.add(case.updated_by)
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        user_map = {str(u.id): u.username or u.email or str(u.id) for u in users}
        
        # 准备导出数据，按照前端显示的字段顺序
        export_data = []
        for case in cases:
            # 格式化测试步骤
            steps_text = ""
            if case.steps:
                steps_list = []
                for i, step in enumerate(case.steps):
                    if isinstance(step, dict):
                        step_num = step.get('step', i + 1)
                        action = step.get('action', '')
                        expected = step.get('expected', '')
                        if expected:
                            steps_list.append(f"{step_num}. {action}\n   期望: {expected}")
                        else:
                            steps_list.append(f"{step_num}. {action}")
                    else:
                        steps_list.append(f"{i + 1}. {str(step)}")
                steps_text = "\n".join(steps_list)
            
            # 格式化标签
            tags_text = ""
            if case.tags:
                if isinstance(case.tags, list):
                    tags_text = ",".join(str(tag) for tag in case.tags)
                else:
                    tags_text = str(case.tags)
            
            # 获取模块路径（完整路径，如：模块a/模块b）
            module_path = ""
            if case.module_id:
                module_path = get_module_path(str(case.module_id))
            
            # 获取创建人和更新人
            created_by_name = user_map.get(case.created_by, "") if case.created_by else ""
            updated_by_name = user_map.get(case.updated_by, "") if case.updated_by else ""
            
            # 格式化日期时间
            created_at_str = ""
            if case.created_at:
                created_at_str = case.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(case.created_at, 'strftime') else str(case.created_at)
            
            updated_at_str = ""
            if case.updated_at:
                updated_at_str = case.updated_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(case.updated_at, 'strftime') else str(case.updated_at)
            
            # 按照前端显示的字段顺序组织数据
            export_data.append({
                "ID": case.case_code or str(case.id)[:8] if hasattr(case, 'id') else "",
                "用例名称": case.name or "",
                "用例等级": case.priority or "",
                "评审结果": getattr(case, 'review_result', '未评审') or "未评审",
                "执行结果": case.status or "",
                "所属模块": module_path,
                "标签": tags_text,
                "是否自动化": "是" if getattr(case, 'is_automated', False) else "否",
                "创建人": created_by_name,
                "创建时间": created_at_str,
                "更新人": updated_by_name,
                "更新时间": updated_at_str,
                "用例类型": case.type or "",
                "前置条件": case.precondition or "",
                "测试步骤": steps_text,
                "期望结果": case.expected_result or "",
            })
        
        # 创建内存中的Excel文件
        from tempfile import NamedTemporaryFile
        import os
        
        # 创建临时文件
        with NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 导出到临时文件
            export_to_excel(export_data, tmp_path, "测试用例")
            
            # 读取文件内容到内存
            with open(tmp_path, 'rb') as f:
                file_content = f.read()
            
            # 删除临时文件
            os.unlink(tmp_path)
            
            # 创建文件流
            file_stream = BytesIO(file_content)
            
            # 生成文件名
            from datetime import datetime
            import urllib.parse
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"测试用例导出_{timestamp}.xlsx"
            
            # 使用 RFC 5987 编码文件名（支持中文）
            encoded_filename = urllib.parse.quote(filename, safe='')
            content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
            
            # 返回文件流
            return StreamingResponse(
                file_stream,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": content_disposition
                }
            )
        except Exception as e:
            # 确保临时文件被删除
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise e
            
    except Exception as e:
        from core.logger import logger
        logger.exception("导出测试用例失败")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/{project_id}/cases/template")
async def download_case_template(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载测试用例导入模板"""
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from utils.excel_handler import export_to_excel
    from tempfile import NamedTemporaryFile
    import os
    import urllib.parse
    
    try:
        # 创建空的模板数据，只包含表头
        # 字段顺序与导出保持一致
        template_data = [{
            "ID": "",  # 用例编号，留空表示新增，填写表示更新
            "用例名称": "",
            "用例等级": "",
            "评审结果": "",
            "执行结果": "",
            "所属模块": "",  # 模块路径，如：模块a/模块b
            "标签": "",
            "是否自动化": "",
            "创建人": "",
            "创建时间": "",
            "更新人": "",
            "更新时间": "",
            "用例类型": "",
            "前置条件": "",
            "测试步骤": "",  # 格式：1. 步骤1\n   期望: 期望1\n2. 步骤2\n   期望: 期望2
            "期望结果": "",
        }]
        
        # 创建临时文件
        with NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 导出到临时文件
            export_to_excel(template_data, tmp_path, "测试用例")
            
            # 读取文件内容到内存
            with open(tmp_path, 'rb') as f:
                file_content = f.read()
            
            # 删除临时文件
            os.unlink(tmp_path)
            
            # 创建文件流
            file_stream = BytesIO(file_content)
            
            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"测试用例导入模板_{timestamp}.xlsx"
            
            # 使用 RFC 5987 编码文件名（支持中文）
            encoded_filename = urllib.parse.quote(filename, safe='')
            content_disposition = f"attachment; filename*=UTF-8''{encoded_filename}"
            
            # 返回文件流
            return StreamingResponse(
                file_stream,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": content_disposition
                }
            )
        except Exception as e:
            # 确保临时文件被删除
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise e
            
    except Exception as e:
        from core.logger import logger
        logger.exception("下载模板失败")
        raise HTTPException(status_code=500, detail=f"下载模板失败: {str(e)}")


@router.post("/{project_id}/cases/import", response_model=APIResponse)
async def import_test_cases(
    project_id: str,
    file: UploadFile = File(...),
    validate_only: bool = False,  # 是否只校验不导入
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导入测试用例（支持只校验模式）"""
    from tempfile import NamedTemporaryFile
    import os
    import pandas as pd
    from utils.excel_handler import read_excel_file
    from models.test_case import TestCase
    from models.module import Module
    from services.test_case_service import TestCaseService
    from schemas.test_case import TestCaseCreate, TestCaseUpdate
    import json
    import re
    
    # 保存上传的文件
    with NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        tmp_path = tmp_file.name
        content = await file.read()
        tmp_file.write(content)
    
    try:
        # 读取Excel文件
        df = read_excel_file(tmp_path)
        
        # 验证必需的列
        required_columns = ["用例名称"]  # 至少需要用例名称
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"缺少必需的列: {', '.join(missing_columns)}"
            )
        
        # 获取项目下的所有模块，用于模块路径解析
        modules = db.query(Module).filter(Module.project_id == project_id).all()
        module_dict = {str(m.id): m for m in modules}
        
        # 构建模块路径映射：路径 -> 模块ID
        def get_module_id_by_path(module_path: str) -> Optional[str]:
            """根据模块路径查找模块ID"""
            if not module_path or pd.isna(module_path):
                return None
            
            path_parts = str(module_path).split('/')
            if not path_parts:
                return None
            
            # 从根模块开始查找
            current_modules = [m for m in modules if m.parent_id is None]
            
            for part in path_parts:
                part = part.strip()
                found = None
                for m in current_modules:
                    if m.name == part:
                        found = m
                        break
                if not found:
                    return None
                current_modules = [m for m in modules if str(m.parent_id) == str(found.id)]
            
            return str(found.id) if found else None
        
        # 获取项目下的所有用例，用于ID校验
        existing_cases = db.query(TestCase).filter(TestCase.project_id == project_id).all()
        case_code_map = {case.case_code: case for case in existing_cases if case.case_code}
        case_id_map = {str(case.id): case for case in existing_cases}
        
        # 按模块分组现有用例
        cases_by_module = {}
        for case in existing_cases:
            module_id = str(case.module_id) if case.module_id else 'null'
            if module_id not in cases_by_module:
                cases_by_module[module_id] = []
            cases_by_module[module_id].append(case)
        
        # 解析测试步骤的函数
        def parse_steps(steps_text: str) -> List[Dict]:
            """解析测试步骤文本为结构化数据"""
            if not steps_text or pd.isna(steps_text):
                return []
            
            steps = []
            lines = str(steps_text).split('\n')
            current_step = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 匹配步骤格式：1. 步骤内容 或 1. 步骤内容\n   期望: 期望内容
                step_match = re.match(r'^(\d+)\.\s*(.+)$', line)
                if step_match:
                    if current_step:
                        steps.append(current_step)
                    step_num = int(step_match.group(1))
                    action = step_match.group(2).strip()
                    current_step = {
                        'step': step_num,
                        'action': action,
                        'expected': ''
                    }
                elif current_step and line.startswith('期望:'):
                    current_step['expected'] = line.replace('期望:', '').strip()
            
            if current_step:
                steps.append(current_step)
            
            return steps if steps else []
        
        # 校验和解析每一行数据
        validation_errors = []
        import_data = []  # 存储解析后的数据
        
        for index, row in df.iterrows():
            row_num = index + 2  # Excel行号（第1行是表头）
            row_errors = []
            
            # 获取ID（用例编号）
            case_id = None
            if 'ID' in df.columns and not pd.isna(row.get('ID')):
                case_id = str(row['ID']).strip()
                if case_id:
                    # 检查ID是否存在
                    if case_id not in case_code_map:
                        row_errors.append(f"ID '{case_id}' 在数据库中不存在")
            
            # 校验用例名称（必填）
            name = None
            if '用例名称' in df.columns and not pd.isna(row.get('用例名称')):
                name = str(row['用例名称']).strip()
                if not name:
                    row_errors.append("用例名称不能为空")
            else:
                row_errors.append("用例名称不能为空")
            
            # 解析其他字段
            priority = 'P2'
            if '用例等级' in df.columns and not pd.isna(row.get('用例等级')):
                priority_val = str(row['用例等级']).strip()
                if priority_val in ['P0', 'P1', 'P2', 'P3']:
                    priority = priority_val
                else:
                    row_errors.append(f"用例等级 '{priority_val}' 无效，应为 P0/P1/P2/P3")
            
            case_type = 'functional'
            if '用例类型' in df.columns and not pd.isna(row.get('用例类型')):
                type_val = str(row['用例类型']).strip()
                valid_types = ['functional', 'interface', 'ui', 'performance', 'security']
                if type_val in valid_types:
                    case_type = type_val
                else:
                    row_errors.append(f"用例类型 '{type_val}' 无效")
            
            status = 'not_executed'
            if '执行结果' in df.columns and not pd.isna(row.get('执行结果')):
                status_val = str(row['执行结果']).strip()
                valid_statuses = ['not_executed', 'passed', 'failed', 'blocked', 'skipped']
                if status_val in valid_statuses:
                    status = status_val
                else:
                    row_errors.append(f"执行结果 '{status_val}' 无效")
            
            # 解析模块路径
            module_id = None
            if '所属模块' in df.columns and not pd.isna(row.get('所属模块')):
                module_path = str(row['所属模块']).strip()
                if module_path:
                    module_id = get_module_id_by_path(module_path)
                    if not module_id:
                        row_errors.append(f"模块路径 '{module_path}' 不存在")
            
            # 解析标签
            tags = []
            if '标签' in df.columns and not pd.isna(row.get('标签')):
                tags_text = str(row['标签']).strip()
                if tags_text:
                    tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
            
            # 解析测试步骤
            steps = []
            if '测试步骤' in df.columns and not pd.isna(row.get('测试步骤')):
                steps_text = str(row['测试步骤'])
                steps = parse_steps(steps_text)
            
            # 其他字段
            precondition = None
            if '前置条件' in df.columns and not pd.isna(row.get('前置条件')):
                precondition = str(row['前置条件']).strip() or None
            
            expected_result = None
            if '期望结果' in df.columns and not pd.isna(row.get('期望结果')):
                expected_result = str(row['期望结果']).strip() or None
            
            is_automated = False
            if '是否自动化' in df.columns and not pd.isna(row.get('是否自动化')):
                automated_val = str(row['是否自动化']).strip()
                is_automated = automated_val in ['是', 'true', 'True', '1', 'yes']
            
            # 收集该行的所有错误
            if row_errors:
                validation_errors.append({
                    'row': row_num,
                    'id': case_id or '(新增)',
                    'name': name or '(未填写)',
                    'errors': row_errors
                })
            else:
                # 确定操作类型
                operation = 'create'
                existing_case = None
                
                if case_id:
                    if case_id in case_code_map:
                        existing_case = case_code_map[case_id]
                        # 检查内容是否有变化
                        has_changes = (
                            existing_case.name != name or
                            existing_case.priority != priority or
                            existing_case.type != case_type or
                            existing_case.status != status or
                            str(existing_case.module_id) != str(module_id) if module_id else existing_case.module_id is not None
                        )
                        if has_changes:
                            operation = 'update'
                        else:
                            operation = 'no_change'
                    else:
                        # ID存在但数据库中不存在，已在上面报错
                        continue
                else:
                    operation = 'create'
                
                import_data.append({
                    'row': row_num,
                    'operation': operation,
                    'case_id': case_id,
                    'existing_case': existing_case,
                    'data': {
                        'name': name,
                        'type': case_type,
                        'priority': priority,
                        'status': status,
                        'module_id': module_id,
                        'precondition': precondition,
                        'steps': steps,
                        'expected_result': expected_result,
                        'tags': tags,
                        'is_automated': is_automated,
                    }
                })
        
        # 检测删除的用例（按模块分组：如果一个模块下的ID缺失表示用例删除）
        # 按模块分组导入的用例ID
        imported_cases_by_module: Dict[str, set] = {}
        for item in import_data:
            module_id = item['data']['module_id'] or 'null'
            if module_id not in imported_cases_by_module:
                imported_cases_by_module[module_id] = set()
            if item['case_id']:
                imported_cases_by_module[module_id].add(item['case_id'])
        
        deleted_cases = []
        # 对于每个模块，检查该模块下现有的用例ID是否都在导入文件中
        for module_id, cases in cases_by_module.items():
            imported_ids = imported_cases_by_module.get(module_id, set())
            for case in cases:
                if case.case_code not in imported_ids:
                    deleted_cases.append({
                        'case_id': case.case_code,
                        'case_name': case.name,
                        'module_id': module_id
                    })
        
        # 如果有校验错误，返回错误信息
        if validation_errors:
            error_messages = []
            for error in validation_errors:
                error_msg = f"第{error['row']}行 (ID: {error['id']}, 用例名称: {error['name']}): " + "; ".join(error['errors'])
                error_messages.append(error_msg)
            
            return APIResponse(
                status=ResponseStatus.ERROR,
                message="导入校验失败",
                data={
                    'total': len(df),
                    'validated': len(import_data),
                    'errors': len(validation_errors),
                    'error_details': error_messages,
                    'validation_errors': validation_errors
                }
            )
        
        # 如果只是校验模式，返回校验结果
        if validate_only:
            return APIResponse(
                status=ResponseStatus.SUCCESS,
                message="校验通过",
                data={
                    'total': len(df),
                    'validated': len(import_data),
                    'errors': 0,
                    'error_details': [],
                    'validation_errors': [],
                    'preview': {
                        'to_create': len([item for item in import_data if item['operation'] == 'create']),
                        'to_update': len([item for item in import_data if item['operation'] == 'update']),
                        'to_delete': len(deleted_cases),
                        'no_change': len([item for item in import_data if item['operation'] == 'no_change'])
                    }
                }
            )
        
        # 所有校验通过，执行导入操作
        created_count = 0
        updated_count = 0
        deleted_count = 0
        
        try:
            # 执行新增和更新
            for item in import_data:
                if item['operation'] == 'create':
                    # 生成case_code
                    import time
                    timestamp = int(time.time() * 1000) % 1000000
                    case_code = f"{timestamp:06d}"
                    while db.query(TestCase).filter(TestCase.case_code == case_code).first():
                        timestamp = (timestamp + 1) % 1000000
                        case_code = f"{timestamp:06d}"
                    
                    new_case = TestCase(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        module_id=item['data']['module_id'],
                        case_code=case_code,
                        name=item['data']['name'],
                        type=item['data']['type'],
                        priority=item['data']['priority'],
                        precondition=item['data']['precondition'],
                        steps=item['data']['steps'] or [],
                        expected_result=item['data']['expected_result'],
                        tags=item['data']['tags'],
                        status=item['data']['status'],
                        is_automated=item['data']['is_automated'],
                        created_by=str(current_user.id),
                        updated_by=str(current_user.id)
                    )
                    db.add(new_case)
                    created_count += 1
                    
                elif item['operation'] == 'update':
                    existing_case = item['existing_case']
                    existing_case.name = item['data']['name']
                    existing_case.type = item['data']['type']
                    existing_case.priority = item['data']['priority']
                    existing_case.status = item['data']['status']
                    existing_case.module_id = item['data']['module_id']
                    existing_case.precondition = item['data']['precondition']
                    existing_case.steps = item['data']['steps'] or []
                    existing_case.expected_result = item['data']['expected_result']
                    existing_case.tags = item['data']['tags']
                    existing_case.is_automated = item['data']['is_automated']
                    existing_case.updated_by = str(current_user.id)
                    updated_count += 1
            
            # 执行删除
            for deleted_case in deleted_cases:
                case = case_code_map.get(deleted_case['case_id'])
                if case:
                    db.delete(case)
                    deleted_count += 1
            
            db.commit()
            
            return APIResponse(
                status=ResponseStatus.SUCCESS,
                message="导入成功",
                data={
                    'total': len(df),
                    'created': created_count,
                    'updated': updated_count,
                    'deleted': deleted_count,
                    'no_change': len([item for item in import_data if item['operation'] == 'no_change'])
                }
            )
            
        except Exception as e:
            db.rollback()
            from core.logger import logger
            logger.exception("导入用例失败")
            raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/{project_id}/cases/{case_id}", response_model=APIResponse)
async def get_test_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取测试用例详情"""
    # TODO: 从数据库获取真实数据
    case = {
        "id": str(case_id),
        "projectId": str(project_id),
        "moduleId": "module_1",
        "caseCode": "TC-001",
        "name": "测试用例001",
        "type": "functional",
        "priority": "P0",
        "precondition": "前置条件说明",
        "steps": [
            {"step": 1, "action": "打开登录页面", "expected": "页面正常显示"},
            {"step": 2, "action": "输入用户名和密码", "expected": "输入成功"}
        ],
        "expectedResult": "登录成功",
        "requirementRef": "REQ-001",
        "status": "not_executed",
        "tags": ["回归", "冒烟"],
        "createdAt": "2024-01-01T00:00:00",
        "updatedAt": "2024-01-01T00:00:00"
    }
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=case
    )


@router.post("/{project_id}/cases", response_model=APIResponse)
async def create_test_case(
    project_id: str,
    case_data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建测试用例"""
    # TODO: 实现真实的创建逻辑
    import uuid
    case_id = str(uuid.uuid4())
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="创建成功",
        data={
            "id": case_id,
            "projectId": str(project_id),
            "moduleId": str(case_data.module_id) if case_data.module_id else None,
            "caseCode": case_data.case_code,
            "name": case_data.name,
            "type": case_data.type,
            "priority": case_data.priority,
            "precondition": case_data.precondition,
            "steps": case_data.steps,
            "expectedResult": case_data.expected_result,
            "requirementRef": case_data.requirement_ref,
            "tags": case_data.tags or [],
            "status": "not_executed",
            "createdAt": "2024-01-01T00:00:00",
            "updatedAt": "2024-01-01T00:00:00"
        }
    )


@router.put("/{project_id}/cases/{case_id}", response_model=APIResponse)
async def update_test_case(
    project_id: str,
    case_id: str,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新测试用例"""
    # TODO: 实现真实的更新逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="更新成功",
        data={
            "id": str(case_id),
            "projectId": str(project_id),
            "name": case_data.name or "测试用例",
            "type": case_data.type or "functional",
            "priority": case_data.priority or "P2",
            "status": case_data.status or "not_executed",
            "tags": case_data.tags or []
        }
    )


@router.delete("/{project_id}/cases/{case_id}", response_model=APIResponse)
async def delete_test_case(
    project_id: str,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除测试用例"""
    # TODO: 实现真实的删除逻辑
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="删除成功"
    )

