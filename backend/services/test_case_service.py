"""测试用例服务层"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.test_case import TestCase
from models.module import Module
from schemas.test_case import TestCaseCreate, TestCaseUpdate
import uuid
from datetime import datetime


class TestCaseService:
    """测试用例服务类"""

    @staticmethod
    def get_test_cases(
        db: Session,
        project_id: str,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        module_id: Optional[str] = None,
        module_ids: Optional[str] = None,  # 逗号分隔的模块 ID 列表
        status: Optional[str] = None,
        priority: Optional[str] = None,
        type: Optional[str] = None,
    ):
        """获取测试用例列表"""
        query = db.query(TestCase).filter(TestCase.project_id == project_id)

        # 搜索条件
        if search:
            query = query.filter(
                or_(
                    TestCase.name.contains(search),
                    TestCase.case_code.contains(search)
                )
            )

        # 模块过滤（支持多个模块 ID）
        if module_ids:
            # 多个模块 ID（逗号分隔），用于查询模块及其子模块的用例
            id_list = [mid.strip() for mid in module_ids.split(',') if mid.strip()]
            if id_list:
                query = query.filter(TestCase.module_id.in_(id_list))
        elif module_id:
            if module_id == 'null':
                # 未规划用例：module_id 为空
                query = query.filter(TestCase.module_id.is_(None))
            else:
                query = query.filter(TestCase.module_id == module_id)

        # 状态过滤
        if status:
            query = query.filter(TestCase.status == status)

        # 优先级过滤
        if priority:
            query = query.filter(TestCase.priority == priority)

        # 类型过滤
        if type:
            query = query.filter(TestCase.type == type)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * size
        items = query.order_by(TestCase.created_at.desc()).offset(offset).limit(size).all()

        # 计算总页数
        pages = (total + size - 1) // size if total > 0 else 0

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages,
            "hasNext": page < pages,
            "hasPrev": page > 1
        }

    @staticmethod
    def get_test_case(db: Session, case_id: str) -> Optional[TestCase]:
        """获取单个测试用例"""
        return db.query(TestCase).filter(TestCase.id == case_id).first()

    @staticmethod
    def create_test_case(
        db: Session,
        case_data: TestCaseCreate,
        current_user_id: str
    ) -> TestCase:
        """创建测试用例"""
        # 生成case_code（如果未提供）
        case_code = case_data.case_code
        if not case_code:
            timestamp = int(datetime.now().timestamp() * 1000) % 1000000
            case_code = f"TC-{timestamp:06d}"

            # 确保case_code唯一
            while db.query(TestCase).filter(TestCase.case_code == case_code).first():
                timestamp = (timestamp + 1) % 1000000
                case_code = f"TC-{timestamp:06d}"

        # 创建测试用例对象（当前暂不强制关联模块，避免与尚未落库的模块产生外键冲突）
        test_case = TestCase(
            id=str(uuid.uuid4()),
            project_id=str(case_data.project_id),
            # TODO: 当模块管理切换为数据库实现后，再恢复对 module_id 的真实写入
            module_id=str(case_data.module_id) if getattr(case_data, "module_id", None) else None,
            case_code=case_code,
            name=case_data.name,
            type=case_data.type,
            priority=case_data.priority,
            precondition=case_data.precondition,
            steps=case_data.steps or [],
            expected_result=case_data.expected_result,
            requirement_ref=case_data.requirement_ref,
            module_path=case_data.module_path,
            level=case_data.level or case_data.priority,  # level默认使用priority
            executor_id=str(case_data.executor_id) if case_data.executor_id else None,
            tags=case_data.tags or [],
            status="not_executed",
            created_by=current_user_id,
            updated_by=current_user_id
        )

        db.add(test_case)
        db.commit()
        db.refresh(test_case)

        return test_case

    @staticmethod
    def update_test_case(
        db: Session,
        case_id: str,
        case_data: TestCaseUpdate,
        current_user_id: str
    ) -> Optional[TestCase]:
        """更新测试用例"""
        test_case = db.query(TestCase).filter(TestCase.id == case_id).first()

        if not test_case:
            return None

        # 更新字段
        update_data = case_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test_case, field, value)

        test_case.updated_by = current_user_id
        test_case.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(test_case)

        return test_case

    @staticmethod
    def delete_test_case(db: Session, case_id: str) -> bool:
        """删除测试用例"""
        test_case = db.query(TestCase).filter(TestCase.id == case_id).first()

        if not test_case:
            return False

        db.delete(test_case)
        db.commit()

        return True

    @staticmethod
    def get_case_tree(db: Session, project_id: str) -> List[dict]:
        """获取测试用例树（包含模块和用例）"""
        # 获取所有模块
        modules = db.query(Module).filter(Module.project_id == project_id).all()

        # 获取所有测试用例
        cases = db.query(TestCase).filter(TestCase.project_id == project_id).all()

        # 构建树结构
        module_map = {}
        tree_data = []

        # 首先构建模块树
        for module in modules:
            module_node = {
                "key": module.id,
                "title": module.name,
                "type": "module",
                "level": getattr(module, 'priority', 'P2'),
                "children": []
            }
            module_map[module.id] = module_node

        # 建立父子关系
        for module in modules:
            node = module_map[module.id]
            if module.parent_id and module.parent_id in module_map:
                module_map[module.parent_id]["children"].append(node)
            else:
                tree_data.append(node)

        # 将用例添加到对应模块
        for case in cases:
            case_node = {
                "key": case.id,
                "title": case.name,
                "type": "case",
                "caseCode": case.case_code,
                "level": case.priority,
                "tags": case.tags or []
            }

            if case.module_id and case.module_id in module_map:
                module_map[case.module_id]["children"].append(case_node)
            else:
                # 无模块的用例直接添加到根级别
                tree_data.append(case_node)

        return tree_data
