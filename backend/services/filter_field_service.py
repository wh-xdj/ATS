"""筛选字段配置服务层"""
from typing import List
from sqlalchemy.orm import Session
from models.filter_field import FilterField
import uuid


class FilterFieldService:
    """筛选字段配置服务类"""

    @staticmethod
    def get_default_fields(project_id: str, db: Session) -> List[FilterField]:
        """获取默认筛选字段配置"""
        default_fields = [
            {
                "field_key": "id",
                "field_label": "ID",
                "field_type": "text",
                "operators": ["contains", "equals", "not_equals"],
                "sort_order": 1,
                "is_default": True
            },
            {
                "field_key": "name",
                "field_label": "用例名称",
                "field_type": "text",
                "sort_order": 2,
                "is_default": True
            },
            {
                "field_key": "moduleId",
                "field_label": "所属模块",
                "field_type": "module",
                "sort_order": 3,
                "is_default": True
            },
            {
                "field_key": "priority",
                "field_label": "用例等级",
                "field_type": "select",
                "options": [
                    {"label": "P0", "value": "P0"},
                    {"label": "P1", "value": "P1"},
                    {"label": "P2", "value": "P2"},
                    {"label": "P3", "value": "P3"}
                ],
                "sort_order": 4,
                "is_default": True
            },
            {
                "field_key": "type",
                "field_label": "用例类型",
                "field_type": "select",
                "options": [
                    {"label": "功能测试", "value": "functional"},
                    {"label": "接口测试", "value": "interface"},
                    {"label": "UI测试", "value": "ui"},
                    {"label": "性能测试", "value": "performance"},
                    {"label": "安全测试", "value": "security"}
                ],
                "sort_order": 5,
                "is_default": True
            },
            {
                "field_key": "status",
                "field_label": "执行结果",
                "field_type": "select",
                "options": [
                    {"label": "未执行", "value": "not_executed"},
                    {"label": "通过", "value": "passed"},
                    {"label": "失败", "value": "failed"},
                    {"label": "阻塞", "value": "blocked"},
                    {"label": "跳过", "value": "skipped"}
                ],
                "sort_order": 6,
                "is_default": True
            },
            {
                "field_key": "isAutomated",
                "field_label": "是否自动化",
                "field_type": "select",
                "options": [
                    {"label": "是", "value": True},
                    {"label": "否", "value": False}
                ],
                "sort_order": 7,
                "is_default": True
            },
            {
                "field_key": "tags",
                "field_label": "标签",
                "field_type": "tags",
                "sort_order": 8,
                "is_default": True
            },
            {
                "field_key": "requirementRef",
                "field_label": "需求关联",
                "field_type": "text",
                "sort_order": 9,
                "is_default": True
            },
            {
                "field_key": "precondition",
                "field_label": "前置条件",
                "field_type": "text",
                "sort_order": 10,
                "is_default": True
            }
        ]
        
        # 创建默认字段对象（不保存到数据库，仅返回）
        fields = []
        for field_data in default_fields:
            field = FilterField(
                id=uuid.uuid4(),
                project_id=project_id,
                **field_data
            )
            fields.append(field)
        
        return fields
