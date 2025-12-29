# -*- coding: utf-8 -*-
"""测试套服务层"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models.test_suite import TestSuite, TestSuiteExecution
from models.test_case import TestCase
from models.test_plan import TestPlan
from models.environment import Environment
from models.user import User
from core.logger import logger
from datetime import datetime
import uuid


class TestSuiteService:
    """测试套服务类"""

    @staticmethod
    def get_test_suites(
        db: Session,
        plan_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """获取测试套列表"""
        query = db.query(TestSuite).filter(TestSuite.plan_id == plan_id)
        total = query.count()
        items = query.order_by(TestSuite.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    def get_test_suite(db: Session, suite_id: str) -> Optional[TestSuite]:
        """获取单个测试套"""
        return db.query(TestSuite).filter(TestSuite.id == suite_id).first()

    @staticmethod
    def create_test_suite(
        db: Session,
        plan_id: str,
        suite_data: dict,
        current_user_id: str
    ) -> TestSuite:
        """创建测试套"""
        # 验证计划是否存在
        plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not plan:
            raise ValueError("测试计划不存在")
        
        # 验证环境是否存在且在线
        environment = db.query(Environment).filter(Environment.id == suite_data.get("environment_id")).first()
        if not environment:
            raise ValueError("执行环境不存在")
        if not environment.is_online:
            raise ValueError("执行环境未在线")
        
        # 验证用例是否存在且都是自动化用例
        case_ids = suite_data.get("case_ids", [])
        if not case_ids:
            raise ValueError("至少需要选择一个测试用例")
        
        cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
        if len(cases) != len(case_ids):
            raise ValueError("部分测试用例不存在")
        
        for case in cases:
            if not case.is_automated:
                raise ValueError(f"用例 {case.name} 不是自动化用例")
        
        # 创建测试套
        suite = TestSuite(
            id=str(uuid.uuid4()),
            plan_id=plan_id,
            name=suite_data.get("name"),
            description=suite_data.get("description"),
            git_repo_url=suite_data.get("git_repo_url"),
            git_branch=suite_data.get("git_branch", "main"),
            git_token=suite_data.get("git_token"),
            environment_id=suite_data.get("environment_id"),
            execution_command=suite_data.get("execution_command"),
            case_ids=case_ids,
            status="pending",
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        db.add(suite)
        db.commit()
        db.refresh(suite)
        
        logger.info(f"创建测试套成功: {suite.id} ({suite.name})")
        return suite

    @staticmethod
    def update_test_suite(
        db: Session,
        suite_id: str,
        suite_data: dict,
        current_user_id: str
    ) -> Optional[TestSuite]:
        """更新测试套"""
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            return None
        
        # 如果更新环境，验证环境是否在线
        if "environment_id" in suite_data:
            environment = db.query(Environment).filter(Environment.id == suite_data["environment_id"]).first()
            if not environment:
                raise ValueError("执行环境不存在")
            if not environment.is_online:
                raise ValueError("执行环境未在线")
        
        # 如果更新用例，验证用例是否都是自动化用例
        if "case_ids" in suite_data:
            case_ids = suite_data["case_ids"]
            if case_ids:
                cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
                if len(cases) != len(case_ids):
                    raise ValueError("部分测试用例不存在")
                
                for case in cases:
                    if not case.is_automated:
                        raise ValueError(f"用例 {case.name} 不是自动化用例")
        
        # 更新字段
        # 注意：允许显式设置None值来清除字段（如Git配置）
        optional_fields = ['git_repo_url', 'git_branch', 'git_token', 'description', 'git_enabled']
        for key, value in suite_data.items():
            if hasattr(suite, key):
                # 对于可选字段（git配置、description等），允许设置为None来清除
                # 对于必填字段，None值会被忽略（不更新）
                if value is not None:
                    # 非None值，直接设置
                    setattr(suite, key, value)
                elif key in optional_fields:
                    # None值，但字段是可选的，允许设置为None来清除
                    # 注意：git_enabled字段如果是None，使用默认值'false'
                    if key == 'git_enabled' and value is None:
                        setattr(suite, key, 'false')
                    else:
                        setattr(suite, key, None)
                # 其他字段如果是None，则跳过（不更新该字段）
        
        suite.updated_by = current_user_id
        suite.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(suite)
        
        logger.info(f"更新测试套成功: {suite.id}")
        return suite

    @staticmethod
    def delete_test_suite(db: Session, suite_id: str) -> bool:
        """删除测试套"""
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            return False
        
        db.delete(suite)
        db.commit()
        
        logger.info(f"删除测试套成功: {suite_id}")
        return True

    @staticmethod
    def execute_test_suite(
        db: Session,
        suite_id: str,
        current_user_id: str
    ) -> Optional[TestSuite]:
        """执行测试套"""
        suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            return None
        
        # 检查环境是否在线
        environment = db.query(Environment).filter(Environment.id == suite.environment_id).first()
        if not environment or not environment.is_online:
            raise ValueError("执行环境未在线")
        
        # 更新状态为运行中
        suite.status = "running"
        suite.updated_by = current_user_id
        suite.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"测试套执行启动: {suite.id} ({suite.name})")
        return suite

    @staticmethod
    def get_suite_executions(
        db: Session,
        suite_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """获取测试套执行记录"""
        query = db.query(TestSuiteExecution).filter(TestSuiteExecution.suite_id == suite_id)
        total = query.count()
        items = query.order_by(TestSuiteExecution.executed_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    def create_suite_execution(
        db: Session,
        suite_id: str,
        case_id: str,
        environment_id: str,
        executor_id: str,
        result: str,
        duration: Optional[str] = None,
        log_output: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> TestSuiteExecution:
        """创建测试套执行记录"""
        execution = TestSuiteExecution(
            id=str(uuid.uuid4()),
            suite_id=suite_id,
            case_id=case_id,
            environment_id=environment_id,
            executor_id=executor_id,
            result=result,
            duration=duration,
            log_output=log_output,
            error_message=error_message
        )
        
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        logger.info(f"创建测试套执行记录: {execution.id}, case_id={case_id}, result={result}")
        return execution

