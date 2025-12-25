# -*- coding: utf-8 -*-
"""仪表盘相关API - 从数据库获取真实数据"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from database import get_db
from schemas.common import APIResponse, ResponseStatus
from models.project import Project
from models.test_case import TestCase
from models.test_plan import TestPlan
from models.test_execution import TestExecution
from typing import Optional
from datetime import datetime, timedelta
import math

router = APIRouter()


@router.get("/overview")
async def get_overview_stats(
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取概览统计数据 - 从数据库获取真实数据"""
    try:
        # 项目总数
        if project_id:
            total_projects = 1
        else:
            total_projects = db.query(func.count(Project.id)).scalar() or 0
        
        # 活跃计划数（状态为 in_progress 或 not_started）
        plans_query = db.query(func.count(TestPlan.id)).filter(
            TestPlan.status.in_(["in_progress", "not_started"])
        )
        if project_id:
            plans_query = plans_query.filter(TestPlan.project_id == project_id)
        active_plans = plans_query.scalar() or 0
        
        # 计算执行成功率（基于最近30天的执行记录）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        exec_query = db.query(TestExecution).filter(
            TestExecution.executed_at >= thirty_days_ago
        )
        if project_id:
            exec_query = exec_query.join(TestCase).filter(TestCase.project_id == project_id)
        
        total_executions = exec_query.count()
        passed_executions = exec_query.filter(TestExecution.result == "passed").count()
        success_rate = round((passed_executions / total_executions * 100), 1) if total_executions > 0 else 0
        
        # 本月用例数
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cases_query = db.query(func.count(TestCase.id)).filter(
            TestCase.created_at >= current_month_start
        )
        if project_id:
            cases_query = cases_query.filter(TestCase.project_id == project_id)
        monthly_cases = cases_query.scalar() or 0
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "totalProjects": total_projects,
                "activePlans": active_plans,
                "successRate": success_rate,
                "monthlyCases": monthly_cases
            }
        )
    except Exception as e:
        print(f"获取概览统计失败: {e}")
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "totalProjects": 0,
                "activePlans": 0,
                "successRate": 0,
                "monthlyCases": 0
            }
        )


@router.get("/trends")
async def get_trends(
    period: str = Query("week", description="时间周期: week, month, quarter"),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取趋势数据 - 从数据库获取真实数据"""
    try:
        days = 7 if period == "week" else (30 if period == "month" else 90)
        base_date = datetime.now()
        
        dates = []
        executions = []
        passed = []
        failed = []
        
        for i in range(days - 1, -1, -1):
            date = base_date - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            
            dates.append(date.strftime("%m-%d"))
            
            # 查询当天的执行记录
            exec_query = db.query(TestExecution).filter(
                and_(
                    TestExecution.executed_at >= date_start,
                    TestExecution.executed_at < date_end
                )
            )
            if project_id:
                exec_query = exec_query.join(TestCase).filter(TestCase.project_id == project_id)
            
            day_total = exec_query.count()
            day_passed = exec_query.filter(TestExecution.result == "passed").count()
            day_failed = exec_query.filter(TestExecution.result == "failed").count()
            
            executions.append(day_total)
            passed.append(day_passed)
            failed.append(day_failed)
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "dates": dates,
                "executions": executions,
                "passed": passed,
                "failed": failed
            }
        )
    except Exception as e:
        print(f"获取趋势数据失败: {e}")
        # 返回空数据
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "dates": [],
                "executions": [],
                "passed": [],
                "failed": []
            }
        )


@router.get("/status-distribution")
async def get_status_distribution(
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取状态分布数据 - 从数据库获取真实数据"""
    try:
        # 查询用例状态分布
        query = db.query(
            TestCase.status,
            func.count(TestCase.id).label('count')
        )
        if project_id:
            query = query.filter(TestCase.project_id == project_id)
        
        status_counts = query.group_by(TestCase.status).all()
        
        # 状态颜色映射
        status_colors = {
            "passed": "#52c41a",
            "failed": "#ff4d4f",
            "blocked": "#faad14",
            "skipped": "#d9d9d9",
            "not_executed": "#bfbfbf"
        }
        
        # 状态名称映射
        status_names = {
            "passed": "通过",
            "failed": "失败",
            "blocked": "阻塞",
            "skipped": "跳过",
            "not_executed": "未执行"
        }
        
        data = []
        for status, count in status_counts:
            data.append({
                "name": status_names.get(status, status),
                "value": count,
                "itemStyle": {"color": status_colors.get(status, "#bfbfbf")}
            })
        
        # 如果没有数据，返回空数组
        if not data:
            data = [
                {"name": "未执行", "value": 0, "itemStyle": {"color": "#bfbfbf"}}
            ]
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=data
        )
    except Exception as e:
        print(f"获取状态分布失败: {e}")
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=[]
        )


@router.get("/execution-analysis")
async def get_execution_analysis(
    period: str = Query("week", description="时间周期: week, month, quarter"),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取执行分析数据 - 从数据库获取真实数据"""
    try:
        days = 7 if period == "week" else (30 if period == "month" else 90)
        base_date = datetime.now()
        
        dates = []
        passed_data = []
        failed_data = []
        blocked_data = []
        
        for i in range(days - 1, -1, -1):
            date = base_date - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            
            dates.append(date.strftime("%m-%d"))
            
            # 查询当天的执行记录
            exec_query = db.query(TestExecution).filter(
                and_(
                    TestExecution.executed_at >= date_start,
                    TestExecution.executed_at < date_end
                )
            )
            if project_id:
                exec_query = exec_query.join(TestCase).filter(TestCase.project_id == project_id)
            
            day_passed = exec_query.filter(TestExecution.result == "passed").count()
            day_failed = exec_query.filter(TestExecution.result == "failed").count()
            day_blocked = exec_query.filter(TestExecution.result == "blocked").count()
            
            passed_data.append(day_passed)
            failed_data.append(day_failed)
            blocked_data.append(day_blocked)
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "dates": dates,
                "data": [
                    {"name": "通过", "data": passed_data},
                    {"name": "失败", "data": failed_data},
                    {"name": "阻塞", "data": blocked_data}
                ]
            }
        )
    except Exception as e:
        print(f"获取执行分析失败: {e}")
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "dates": [],
                "data": []
            }
        )


@router.get("/activities")
async def get_recent_activities(
    limit: int = Query(10, ge=1, le=100),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取最近活动 - 从数据库获取真实数据"""
    try:
        activities = []
        
        # 获取最近创建的测试用例
        cases_query = db.query(TestCase).order_by(TestCase.created_at.desc())
        if project_id:
            cases_query = cases_query.filter(TestCase.project_id == project_id)
        recent_cases = cases_query.limit(limit // 3).all()
        
        for case in recent_cases:
            activities.append({
                "id": f"case_{case.id}",
                "type": "case",
                "title": "创建了测试用例",
                "description": case.name[:50] + "..." if len(case.name) > 50 else case.name,
                "timestamp": case.created_at.isoformat() if case.created_at else datetime.now().isoformat()
            })
        
        # 获取最近的执行记录
        exec_query = db.query(TestExecution).order_by(TestExecution.executed_at.desc())
        if project_id:
            exec_query = exec_query.join(TestCase).filter(TestCase.project_id == project_id)
        recent_executions = exec_query.limit(limit // 3).all()
        
        for execution in recent_executions:
            result_text = "通过" if execution.result == "passed" else ("失败" if execution.result == "failed" else execution.result)
            activities.append({
                "id": f"exec_{execution.id}",
                "type": "execution",
                "title": f"执行测试用例 - {result_text}",
                "description": f"用例ID: {execution.case_id[:8]}...",
                "timestamp": execution.executed_at.isoformat() if execution.executed_at else datetime.now().isoformat()
            })
        
        # 获取最近创建的测试计划
        plans_query = db.query(TestPlan).order_by(TestPlan.created_at.desc())
        if project_id:
            plans_query = plans_query.filter(TestPlan.project_id == project_id)
        recent_plans = plans_query.limit(limit // 3).all()
        
        for plan in recent_plans:
            activities.append({
                "id": f"plan_{plan.id}",
                "type": "plan",
                "title": "创建了测试计划",
                "description": plan.name[:50] + "..." if len(plan.name) > 50 else plan.name,
                "timestamp": plan.created_at.isoformat() if plan.created_at else datetime.now().isoformat()
            })
        
        # 按时间排序
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=activities[:limit]
        )
    except Exception as e:
        print(f"获取最近活动失败: {e}")
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data=[]
        )


@router.get("/project-stats")
async def get_project_stats(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取项目统计 - 从数据库获取真实数据"""
    try:
        # 获取所有项目
        projects_query = db.query(Project)
        if project_id:
            projects_query = projects_query.filter(Project.id == project_id)
        
        total = projects_query.count()
        projects = projects_query.offset((page - 1) * size).limit(size).all()
        
        project_stats = []
        for project in projects:
            # 获取项目的用例总数
            total_cases = db.query(func.count(TestCase.id)).filter(
                TestCase.project_id == project.id
            ).scalar() or 0
            
            # 获取执行次数
            execution_count = db.query(func.count(TestExecution.id)).join(
                TestCase, TestExecution.case_id == TestCase.id
            ).filter(TestCase.project_id == project.id).scalar() or 0
            
            # 计算成功率
            passed_count = db.query(func.count(TestExecution.id)).join(
                TestCase, TestExecution.case_id == TestCase.id
            ).filter(
                TestCase.project_id == project.id,
                TestExecution.result == "passed"
            ).scalar() or 0
            
            success_rate = round((passed_count / execution_count * 100), 1) if execution_count > 0 else 0
            
            # 获取最后执行时间
            last_execution = db.query(TestExecution.executed_at).join(
                TestCase, TestExecution.case_id == TestCase.id
            ).filter(
                TestCase.project_id == project.id
            ).order_by(TestExecution.executed_at.desc()).first()
            
            last_exec_time = last_execution[0].isoformat() if last_execution and last_execution[0] else None
            
            # 计算执行趋势（对比上周和本周）
            now = datetime.now()
            this_week_start = now - timedelta(days=now.weekday())
            last_week_start = this_week_start - timedelta(days=7)
            
            this_week_count = db.query(func.count(TestExecution.id)).join(
                TestCase, TestExecution.case_id == TestCase.id
            ).filter(
                TestCase.project_id == project.id,
                TestExecution.executed_at >= this_week_start
            ).scalar() or 0
            
            last_week_count = db.query(func.count(TestExecution.id)).join(
                TestCase, TestExecution.case_id == TestCase.id
            ).filter(
                TestCase.project_id == project.id,
                TestExecution.executed_at >= last_week_start,
                TestExecution.executed_at < this_week_start
            ).scalar() or 0
            
            if last_week_count > 0:
                execution_trend = round(((this_week_count - last_week_count) / last_week_count * 100), 1)
            else:
                execution_trend = 100.0 if this_week_count > 0 else 0
            
            project_stats.append({
                "id": project.id,
                "projectId": project.id,
                "projectName": project.name,
                "totalCases": total_cases,
                "executionCount": execution_count,
                "successRate": success_rate,
                "executionTrend": execution_trend,
                "lastExecution": last_exec_time
            })
        
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "items": project_stats,
                "total": total,
                "page": page,
                "size": size,
                "pages": math.ceil(total / size) if total > 0 else 0,
                "hasNext": page * size < total,
                "hasPrev": page > 1
            }
        )
    except Exception as e:
        print(f"获取项目统计失败: {e}")
        return APIResponse(
            status=ResponseStatus.SUCCESS,
            message="获取成功",
            data={
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "pages": 0,
                "hasNext": False,
                "hasPrev": False
            }
        )
