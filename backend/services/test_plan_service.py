# -*- coding: utf-8 -*-
"""测试计划服务层"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.test_plan import TestPlan, PlanCaseRelation
from models.test_case import TestCase
from models.user import User
from core.logger import logger
from datetime import datetime, date
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
        logger.debug(f"TestPlanService.get_test_plans - project_id: {project_id}, type: {type(project_id)}")
        
        # 确保 project_id 是字符串格式
        project_id_str = str(project_id) if project_id else None
        if not project_id_str:
            logger.warning("错误: project_id 为空")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0,
                "hasNext": False,
                "hasPrev": False
            }
        
        # 查询所有计划（用于调试，仅在前几条记录时打印）
        all_plans_count = db.query(TestPlan).count()
        logger.debug(f"数据库中所有计划数量: {all_plans_count}")
        
        # 检查是否有匹配的项目ID
        sample_plans = db.query(TestPlan).limit(5).all()
        for p in sample_plans:
            logger.debug(f"  示例计划: id={p.id}, name={p.name}, project_id={p.project_id} (str={str(p.project_id)})")
        
        # 使用字符串比较进行过滤
        query = db.query(TestPlan).filter(TestPlan.project_id == project_id_str)
        
        # 检查过滤后的数量
        count_before_pagination = query.count()
        logger.debug(f"过滤后计划数量 (project_id={project_id_str}): {count_before_pagination}")

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

        # 检查并更新超时计划状态
        TestPlanService._check_and_update_overdue_plans(db, items)

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
        plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if plan:
            # 检查并更新超时状态
            TestPlanService._check_and_update_overdue_plans(db, [plan])
        return plan

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

        # 处理日期字段
        start_date = None
        if plan_data.get("startDate"):
            try:
                start_date_str = plan_data["startDate"]
                if isinstance(start_date_str, str):
                    # 处理ISO格式日期字符串
                    start_date_str = start_date_str.replace("Z", "+00:00")
                    start_date = datetime.fromisoformat(start_date_str)
                elif hasattr(start_date_str, 'date'):
                    # 如果是date对象，转换为datetime
                    start_date = datetime.combine(start_date_str, datetime.min.time())
            except (ValueError, AttributeError) as e:
                logger.warning(f"解析开始日期失败: {e}, 原始值: {plan_data.get('startDate')}")
                start_date = None

        end_date = None
        if plan_data.get("endDate"):
            try:
                end_date_str = plan_data["endDate"]
                if isinstance(end_date_str, str):
                    # 处理ISO格式日期字符串
                    end_date_str = end_date_str.replace("Z", "+00:00")
                    end_date = datetime.fromisoformat(end_date_str)
                elif hasattr(end_date_str, 'date'):
                    # 如果是date对象，转换为datetime
                    end_date = datetime.combine(end_date_str, datetime.min.time())
            except (ValueError, AttributeError) as e:
                logger.warning(f"解析结束日期失败: {e}, 原始值: {plan_data.get('endDate')}")
                end_date = None

        # 创建测试计划
        test_plan = TestPlan(
            id=str(uuid.uuid4()),
            project_id=project_id,
            plan_number=plan_number,
            name=plan_data.get("name", "新测试计划"),
            description=plan_data.get("description"),
            owner_id=current_user_id,
            plan_type=plan_data.get("planType", "manual"),
            start_date=start_date.date() if start_date else None,
            end_date=end_date.date() if end_date else None,
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
        
        # 处理开始日期
        if "startDate" in plan_data:
            if plan_data["startDate"]:
                try:
                    start_date_str = plan_data["startDate"]
                    if isinstance(start_date_str, str):
                        start_date_str = start_date_str.replace("Z", "+00:00")
                        start_date = datetime.fromisoformat(start_date_str)
                        test_plan.start_date = start_date.date()
                    elif hasattr(start_date_str, 'date'):
                        test_plan.start_date = start_date_str.date()
                except (ValueError, AttributeError) as e:
                    logger.warning(f"解析开始日期失败: {e}, 原始值: {plan_data.get('startDate')}")
            else:
                test_plan.start_date = None
        
        # 处理结束日期
        if "endDate" in plan_data:
            if plan_data["endDate"]:
                try:
                    end_date_str = plan_data["endDate"]
                    if isinstance(end_date_str, str):
                        end_date_str = end_date_str.replace("Z", "+00:00")
                        end_date = datetime.fromisoformat(end_date_str)
                        test_plan.end_date = end_date.date()
                    elif hasattr(end_date_str, 'date'):
                        test_plan.end_date = end_date_str.date()
                except (ValueError, AttributeError) as e:
                    logger.warning(f"解析结束日期失败: {e}, 原始值: {plan_data.get('endDate')}")
            else:
                test_plan.end_date = None
        
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
    def get_plan_cases(db: Session, plan_id: str) -> List[dict]:
        """获取计划关联的测试用例（包含执行状态）"""
        relations = db.query(PlanCaseRelation).filter(
            PlanCaseRelation.plan_id == plan_id
        ).order_by(PlanCaseRelation.execution_order).all()

        case_ids = [r.case_id for r in relations]
        if not case_ids:
            return []

        cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
        
        # 创建用例ID到关系的映射
        relation_map = {r.case_id: r for r in relations}
        
        # 获取所有相关的用户ID
        user_ids = set()
        for case in cases:
            if case.created_by:
                user_ids.add(case.created_by)
            if case.updated_by:
                user_ids.add(case.updated_by)
        
        # 批量查询用户信息
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        user_map = {str(u.id): u.username or u.email or str(u.id) for u in users}
        
        # 为每个用例添加执行状态信息
        result = []
        for case in cases:
            relation = relation_map.get(case.id)
            case_dict = {
                'id': case.id,
                'name': case.name,
                'caseCode': case.case_code,
                'priority': case.priority,
                'moduleId': case.module_id,
                'projectId': case.project_id,  # 添加项目ID，用于加载模块列表
                'precondition': getattr(case, 'precondition', None),  # TestCase 使用 precondition（单数）
                'steps': case.steps,
                'expectedResult': case.expected_result,
                'status': case.status,
                'tags': case.tags if hasattr(case, 'tags') and case.tags else [],
                'createdBy': case.created_by,
                'createdByName': user_map.get(case.created_by, '未知用户'),  # 添加用户名
                'updatedBy': case.updated_by or case.created_by,
                'updatedByName': user_map.get(case.updated_by or case.created_by, '未知用户'),  # 添加用户名
                'createdAt': case.created_at.isoformat() if case.created_at else None,
                'updatedAt': case.updated_at.isoformat() if case.updated_at else None,
                'executionStatus': relation.execution_status if relation else 'pending',
                'executionUpdatedAt': relation.execution_updated_at.isoformat() if relation and relation.execution_updated_at else None
            }
            result.append(case_dict)
        
        return result

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
    def update_case_execution_status(
        db: Session,
        plan_id: str,
        case_id: str,
        status: str
    ) -> bool:
        """更新用例执行状态，并自动检查计划进度"""
        relation = db.query(PlanCaseRelation).filter(
            and_(
                PlanCaseRelation.plan_id == plan_id,
                PlanCaseRelation.case_id == case_id
            )
        ).first()

        if not relation:
            return False

        relation.execution_status = status
        relation.execution_updated_at = datetime.utcnow()

        db.commit()
        
        # 检查并更新计划状态
        TestPlanService._check_and_update_plan_status(db, plan_id)
        
        return True

    @staticmethod
    def batch_update_case_execution_status(
        db: Session,
        plan_id: str,
        updates: List[dict]
    ) -> bool:
        """批量更新用例执行状态，并自动检查计划进度"""
        for update in updates:
            case_id = update.get("caseId")
            status = update.get("status")
            if not case_id or not status:
                continue

            relation = db.query(PlanCaseRelation).filter(
                and_(
                    PlanCaseRelation.plan_id == plan_id,
                    PlanCaseRelation.case_id == case_id
                )
            ).first()

            if relation:
                relation.execution_status = status
                relation.execution_updated_at = datetime.utcnow()

        db.commit()
        
        # 检查并更新计划状态
        TestPlanService._check_and_update_plan_status(db, plan_id)
        
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
    def _check_and_update_plan_status(db: Session, plan_id: str) -> None:
        """检查计划执行进度，如果所有用例都已完成，自动更新计划状态为已完成"""
        # 获取计划的所有用例关联
        relations = db.query(PlanCaseRelation).filter(
            PlanCaseRelation.plan_id == plan_id
        ).all()
        
        if not relations:
            return
        
        # 统计已执行的用例数（非pending状态）
        executed_count = sum(1 for r in relations if r.execution_status and r.execution_status != 'pending')
        total_count = len(relations)
        
        # 如果所有用例都已完成（进度100%），更新计划状态为已完成
        if total_count > 0 and executed_count == total_count:
            test_plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
            if test_plan and test_plan.status != 'completed':
                test_plan.status = 'completed'
                test_plan.updated_at = datetime.utcnow()
                db.commit()

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

    @staticmethod
    def _check_and_update_overdue_plans(db: Session, plans: List[TestPlan]):
        """
        检查并更新超时计划状态
        如果计划超过结束时间且还有用例未完成（execution_status为pending），则将状态改为overdue
        """
        today = date.today()
        
        for plan in plans:
            # 只检查有结束日期的计划
            if not plan.end_date:
                continue
            
            # 检查是否超过结束时间
            if plan.end_date < today:
                # 检查是否还有未完成的用例（execution_status为pending）
                pending_cases = db.query(PlanCaseRelation).filter(
                    and_(
                        PlanCaseRelation.plan_id == plan.id,
                        PlanCaseRelation.execution_status == "pending"
                    )
                ).count()
                
                # 如果有未完成的用例，且计划状态不是completed，则标记为overdue
                if pending_cases > 0 and plan.status not in ["completed", "overdue"]:
                    logger.info(f"计划 {plan.id} ({plan.name}) 已超过结束时间且还有 {pending_cases} 个用例未完成，状态更新为 overdue")
                    plan.status = "overdue"
                    db.commit()
                    db.refresh(plan)

