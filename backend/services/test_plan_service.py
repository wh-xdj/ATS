# -*- coding: utf-8 -*-
"""测试计划服务层"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.test_plan import TestPlan, PlanCaseRelation
from models.test_case import TestCase
from datetime import datetime
import uuid


class TestPlanService:
    """测试计划服务类"""

    @staticmethod
    def get_test_plans(
        db: Session,
        project_id: str,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        plan_type: Optional[str] = None,
        owner_id: Optional[str] = None,
    ):
        """获取测试计划列表"""
        query = db.query(TestPlan).filter(TestPlan.project_id == project_id)

        # 搜索条件
        if search:
            query = query.filter(
                or_(
                    TestPlan.name.contains(search),
                    TestPlan.plan_number.contains(search)
                )
            )

        # 状态过滤
        if status:
            query = query.filter(TestPlan.status == status)

        # 类型过滤
        if plan_type:
            query = query.filter(TestPlan.plan_type == plan_type)

        # 负责人过滤
        if owner_id:
            query = query.filter(TestPlan.owner_id == owner_id)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * size
        items = query.order_by(TestPlan.created_at.desc()).offset(offset).limit(size).all()

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
    def get_test_plan(db: Session, plan_id: str) -> Optional[TestPlan]:
        """获取单个测试计划"""
        return db.query(TestPlan).filter(TestPlan.id == plan_id).first()

    @staticmethod
    def create_test_plan(
        db: Session,
        project_id: str,
        plan_data: dict,
        current_user_id: str
    ) -> TestPlan:
        """创建测试计划"""
        # 生成计划编号
        timestamp = int(datetime.now().timestamp() * 1000) % 1000000
        plan_number = f"TP-{timestamp:06d}"

        # 确保 plan_number 唯一
        while db.query(TestPlan).filter(TestPlan.plan_number == plan_number).first():
            timestamp = (timestamp + 1) % 1000000
            plan_number = f"TP-{timestamp:06d}"

        # 创建测试计划
        test_plan = TestPlan(
            id=str(uuid.uuid4()),
            project_id=project_id,
            plan_number=plan_number,
            name=plan_data.get("name", "新测试计划"),
            description=plan_data.get("description"),
            owner_id=current_user_id,
            plan_type=plan_data.get("planType", "manual"),
            start_date=datetime.fromisoformat(plan_data["startDate"].replace("Z", "+00:00")) if plan_data.get("startDate") else None,
            end_date=datetime.fromisoformat(plan_data["endDate"].replace("Z", "+00:00")) if plan_data.get("endDate") else None,
            environment_config=plan_data.get("environmentConfig"),
            status="not_started"
        )

        db.add(test_plan)
        db.commit()
        db.refresh(test_plan)

        # 添加关联的测试用例
        test_case_ids = plan_data.get("testCaseIds", [])
        if test_case_ids:
            for idx, case_id in enumerate(test_case_ids):
                relation = PlanCaseRelation(
                    id=str(uuid.uuid4()),
                    plan_id=test_plan.id,
                    case_id=case_id,
                    execution_order=idx
                )
                db.add(relation)
            db.commit()

        return test_plan

    @staticmethod
    def update_test_plan(
        db: Session,
        plan_id: str,
        plan_data: dict,
        current_user_id: str
    ) -> Optional[TestPlan]:
        """更新测试计划"""
        test_plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()

        if not test_plan:
            return None

        # 更新字段
        if "name" in plan_data:
            test_plan.name = plan_data["name"]
        if "description" in plan_data:
            test_plan.description = plan_data["description"]
        if "planType" in plan_data:
            test_plan.plan_type = plan_data["planType"]
        if "startDate" in plan_data and plan_data["startDate"]:
            test_plan.start_date = datetime.fromisoformat(plan_data["startDate"].replace("Z", "+00:00"))
        if "endDate" in plan_data and plan_data["endDate"]:
            test_plan.end_date = datetime.fromisoformat(plan_data["endDate"].replace("Z", "+00:00"))
        if "status" in plan_data:
            test_plan.status = plan_data["status"]
        if "environmentConfig" in plan_data:
            test_plan.environment_config = plan_data["environmentConfig"]

        test_plan.updated_at = datetime.utcnow()

        # 更新关联的测试用例
        if "testCaseIds" in plan_data:
            test_case_ids = plan_data.get("testCaseIds", [])
            
            # 删除旧的关联
            db.query(PlanCaseRelation).filter(
                PlanCaseRelation.plan_id == plan_id
            ).delete(synchronize_session=False)
            
            # 添加新的关联
            for idx, case_id in enumerate(test_case_ids):
                relation = PlanCaseRelation(
                    id=str(uuid.uuid4()),
                    plan_id=plan_id,
                    case_id=case_id,
                    execution_order=idx
                )
                db.add(relation)

        db.commit()
        db.refresh(test_plan)

        return test_plan

    @staticmethod
    def delete_test_plan(db: Session, plan_id: str) -> bool:
        """删除测试计划"""
        test_plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()

        if not test_plan:
            return False

        db.delete(test_plan)
        db.commit()

        return True

    @staticmethod
    def get_plan_cases(db: Session, plan_id: str) -> List[TestCase]:
        """获取计划关联的测试用例"""
        relations = db.query(PlanCaseRelation).filter(
            PlanCaseRelation.plan_id == plan_id
        ).order_by(PlanCaseRelation.execution_order).all()

        case_ids = [r.case_id for r in relations]
        if not case_ids:
            return []

        cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
        return cases

    @staticmethod
    def add_cases_to_plan(db: Session, plan_id: str, case_ids: List[str]) -> bool:
        """向计划添加用例"""
        # 获取当前最大的执行顺序
        max_order = db.query(PlanCaseRelation.execution_order).filter(
            PlanCaseRelation.plan_id == plan_id
        ).order_by(PlanCaseRelation.execution_order.desc()).first()
        
        start_order = (max_order[0] + 1) if max_order else 0

        for idx, case_id in enumerate(case_ids):
            # 检查是否已存在
            existing = db.query(PlanCaseRelation).filter(
                and_(
                    PlanCaseRelation.plan_id == plan_id,
                    PlanCaseRelation.case_id == case_id
                )
            ).first()
            
            if not existing:
                relation = PlanCaseRelation(
                    id=str(uuid.uuid4()),
                    plan_id=plan_id,
                    case_id=case_id,
                    execution_order=start_order + idx
                )
                db.add(relation)

        db.commit()
        return True

    @staticmethod
    def remove_cases_from_plan(db: Session, plan_id: str, case_ids: List[str]) -> bool:
        """从计划移除用例"""
        db.query(PlanCaseRelation).filter(
            and_(
                PlanCaseRelation.plan_id == plan_id,
                PlanCaseRelation.case_id.in_(case_ids)
            )
        ).delete(synchronize_session=False)
        
        db.commit()
        return True

    @staticmethod
    def update_plan_status(db: Session, plan_id: str, status: str) -> Optional[TestPlan]:
        """更新计划状态"""
        test_plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()

        if not test_plan:
            return None

        test_plan.status = status
        test_plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(test_plan)

        return test_plan

    @staticmethod
    def clone_plan(db: Session, plan_id: str, project_id: str, current_user_id: str) -> Optional[TestPlan]:
        """克隆计划"""
        source_plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()

        if not source_plan:
            return None

        # 生成新计划编号
        timestamp = int(datetime.now().timestamp() * 1000) % 1000000
        plan_number = f"TP-{timestamp:06d}"

        while db.query(TestPlan).filter(TestPlan.plan_number == plan_number).first():
            timestamp = (timestamp + 1) % 1000000
            plan_number = f"TP-{timestamp:06d}"

        # 创建新计划
        new_plan = TestPlan(
            id=str(uuid.uuid4()),
            project_id=project_id,
            plan_number=plan_number,
            name=f"{source_plan.name} (副本)",
            description=source_plan.description,
            owner_id=current_user_id,
            plan_type=source_plan.plan_type,
            start_date=source_plan.start_date,
            end_date=source_plan.end_date,
            environment_config=source_plan.environment_config,
            status="not_started"
        )

        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        # 复制用例关联
        relations = db.query(PlanCaseRelation).filter(
            PlanCaseRelation.plan_id == plan_id
        ).all()

        for relation in relations:
            new_relation = PlanCaseRelation(
                id=str(uuid.uuid4()),
                plan_id=new_plan.id,
                case_id=relation.case_id,
                execution_order=relation.execution_order
            )
            db.add(new_relation)

        db.commit()

        return new_plan

