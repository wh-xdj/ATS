# -*- coding: utf-8 -*-
"""模块服务层"""
from typing import Optional, List
from sqlalchemy.orm import Session
from models.module import Module
from schemas.module import ModuleCreate, ModuleUpdate
import uuid
from datetime import datetime


class ModuleService:
    """模块服务类"""

    @staticmethod
    def get_modules(db: Session, project_id: str) -> List[Module]:
        """获取项目的所有模块"""
        return db.query(Module).filter(
            Module.project_id == project_id
        ).order_by(Module.sort_order, Module.created_at).all()

    @staticmethod
    def get_module(db: Session, module_id: str) -> Optional[Module]:
        """获取单个模块"""
        return db.query(Module).filter(Module.id == module_id).first()

    @staticmethod
    def create_module(
        db: Session,
        project_id: str,
        module_data: ModuleCreate,
        current_user_id: str
    ) -> Module:
        """创建模块"""
        # 计算层级
        level = 1
        if module_data.parent_id:
            parent = db.query(Module).filter(Module.id == module_data.parent_id).first()
            if parent:
                level = parent.level + 1

        module = Module(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=module_data.name,
            parent_id=module_data.parent_id,
            level=level,
            sort_order=module_data.sort_order,
            description=module_data.description
        )

        db.add(module)
        db.commit()
        db.refresh(module)

        return module

    @staticmethod
    def update_module(
        db: Session,
        module_id: str,
        module_data: ModuleUpdate,
        current_user_id: str
    ) -> Optional[Module]:
        """更新模块"""
        module = db.query(Module).filter(Module.id == module_id).first()

        if not module:
            return None

        # 更新字段
        if module_data.name is not None:
            module.name = module_data.name
        
        if module_data.parent_id is not None:
            module.parent_id = module_data.parent_id if module_data.parent_id else None
            # 重新计算层级
            if module.parent_id:
                parent = db.query(Module).filter(Module.id == module.parent_id).first()
                if parent:
                    module.level = parent.level + 1
            else:
                module.level = 1
        
        if module_data.sort_order is not None:
            module.sort_order = module_data.sort_order
        
        if module_data.description is not None:
            module.description = module_data.description

        module.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(module)

        return module

    @staticmethod
    def delete_module(db: Session, module_id: str) -> bool:
        """删除模块"""
        module = db.query(Module).filter(Module.id == module_id).first()

        if not module:
            return False

        # 先将子模块的 parent_id 设置为当前模块的 parent_id（提升子模块）
        db.query(Module).filter(Module.parent_id == module_id).update(
            {"parent_id": module.parent_id}
        )

        # 将关联的测试用例的 module_id 设置为 None
        from models.test_case import TestCase
        db.query(TestCase).filter(TestCase.module_id == module_id).update(
            {"module_id": None}
        )

        db.delete(module)
        db.commit()

        return True

    @staticmethod
    def get_module_tree(db: Session, project_id: str) -> List[dict]:
        """获取模块树结构"""
        modules = ModuleService.get_modules(db, project_id)

        # 构建模块映射
        module_map = {}
        for module in modules:
            module_map[module.id] = {
                "key": module.id,
                "title": module.name,
                "type": "module",
                "level": f"P{min(module.level, 3)}",
                "children": []
            }

        # 构建树结构
        tree = []
        for module in modules:
            node = module_map[module.id]
            if module.parent_id and module.parent_id in module_map:
                module_map[module.parent_id]["children"].append(node)
            else:
                tree.append(node)

        return tree

