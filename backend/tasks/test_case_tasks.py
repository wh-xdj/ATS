"""测试用例相关任务"""
from typing import Dict, Any
from uuid import UUID
import pandas as pd
from core.celery_app import celery_app
from database import SessionLocal
from models import TestCase, Project
from utils.excel_handler import read_excel_file, validate_excel_format


@celery_app.task(name="tasks.import_test_cases")
def import_test_cases_task(project_id: str, file_path: str, user_id: str) -> Dict[str, Any]:
    """异步导入用例任务"""
    db = SessionLocal()
    try:
        # 读取Excel文件
        df = read_excel_file(file_path)
        
        # 验证格式
        required_columns = ["case_code", "name", "type", "priority"]
        validate_excel_format(df, required_columns)
        
        results = {
            "total": len(df),
            "created": 0,
            "updated": 0,
            "failed": 0,
            "errors": []
        }
        
        project = db.query(Project).filter(Project.id == UUID(project_id)).first()
        if not project:
            results["errors"].append("项目不存在")
            return results
        
        for index, row in df.iterrows():
            try:
                # 验证必要字段
                if pd.isna(row.get('name')) or pd.isna(row.get('case_code')):
                    results["failed"] += 1
                    results["errors"].append(f"第{index+2}行: 用例名称和编号不能为空")
                    continue
                
                # 检查用例是否存在
                existing_case = db.query(TestCase).filter(
                    TestCase.case_code == str(row['case_code'])
                ).first()
                
                if existing_case:
                    # 更新用例
                    for key, value in row.items():
                        if hasattr(existing_case, key) and not pd.isna(value):
                            setattr(existing_case, key, value)
                    results["updated"] += 1
                else:
                    # 创建新用例
                    case_data = {
                        "project_id": UUID(project_id),
                        "case_code": str(row['case_code']),
                        "name": str(row['name']),
                        "type": str(row.get('type', 'functional')),
                        "priority": str(row.get('priority', 'medium')),
                        "precondition": str(row.get('precondition', '')) if not pd.isna(row.get('precondition')) else None,
                        "steps": row.get('steps', []),
                        "created_by": UUID(user_id),
                        "status": "not_executed"
                    }
                    new_case = TestCase(**case_data)
                    db.add(new_case)
                    results["created"] += 1
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"第{index+2}行: {str(e)}")
        
        db.commit()
        
        # 清理临时文件
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return results
        
    except Exception as e:
        return {"error": f"导入失败: {str(e)}"}
    finally:
        db.close()


@celery_app.task(name="tasks.export_test_cases")
def export_test_cases_task(project_id: str, filters: Dict[str, Any]) -> str:
    """异步导出用例任务"""
    db = SessionLocal()
    try:
        from utils.excel_handler import export_to_excel
        
        # 构建查询
        query = db.query(TestCase).filter(TestCase.project_id == UUID(project_id))
        
        # 应用过滤条件
        if filters.get('module_id'):
            query = query.filter(TestCase.module_id == UUID(filters['module_id']))
        if filters.get('type'):
            query = query.filter(TestCase.type == filters['type'])
        if filters.get('priority'):
            query = query.filter(TestCase.priority == filters['priority'])
        
        cases = query.all()
        
        # 准备导出数据
        export_data = []
        for case in cases:
            steps_text = "\n".join([
                f"{step.get('step', i+1)}. {step.get('action', '')}" 
                for i, step in enumerate(case.steps if case.steps else [])
            ])
            tags_text = ",".join(case.tags) if case.tags else ""
            
            export_data.append({
                "用例编号": case.case_code,
                "用例名称": case.name,
                "用例类型": case.type,
                "优先级": case.priority,
                "前置条件": case.precondition or "",
                "测试步骤": steps_text,
                "模块路径": case.module_path or "",
                "标签": tags_text,
                "状态": case.status
            })
        
        # 保存文件
        import time
        file_path = f"/tmp/export_{project_id}_{int(time.time())}.xlsx"
        export_to_excel(export_data, file_path, "测试用例")
        
        return file_path
        
    except Exception as e:
        return f"导出失败: {str(e)}"
    finally:
        db.close()

