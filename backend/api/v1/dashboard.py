"""仪表盘相关API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.common import APIResponse, ResponseStatus
from typing import Optional
from datetime import datetime, timedelta
import math

router = APIRouter()


@router.get("/overview")
async def get_overview_stats(
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取概览统计数据"""
    # TODO: 从数据库获取真实数据
    # 目前返回模拟数据
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "totalProjects": 5,
            "activePlans": 12,
            "successRate": 85.5,
            "monthlyCases": 1250
        }
    )


@router.get("/trends")
async def get_trends(
    period: str = Query("week", description="时间周期: week, month, quarter"),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取趋势数据"""
    # TODO: 从数据库获取真实数据
    # 根据周期生成模拟数据
    days = 7 if period == "week" else (30 if period == "month" else 90)
    dates = []
    executions = []
    passed = []
    failed = []
    
    base_date = datetime.now()
    for i in range(days - 1, -1, -1):
        date = base_date - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
        exec_count = 20 + int(10 * math.sin(i / 3))
        pass_count = int(exec_count * 0.85)
        fail_count = exec_count - pass_count
        executions.append(exec_count)
        passed.append(pass_count)
        failed.append(fail_count)
    
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


@router.get("/status-distribution")
async def get_status_distribution(
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取状态分布数据"""
    # TODO: 从数据库获取真实数据
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=[
            {"name": "通过", "value": 850, "itemStyle": {"color": "#52c41a"}},
            {"name": "失败", "value": 120, "itemStyle": {"color": "#ff4d4f"}},
            {"name": "阻塞", "value": 30, "itemStyle": {"color": "#faad14"}},
            {"name": "跳过", "value": 50, "itemStyle": {"color": "#d9d9d9"}},
            {"name": "未执行", "value": 200, "itemStyle": {"color": "#bfbfbf"}}
        ]
    )


@router.get("/execution-analysis")
async def get_execution_analysis(
    period: str = Query("week", description="时间周期: week, month, quarter"),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取执行分析数据"""
    # TODO: 从数据库获取真实数据
    days = 7 if period == "week" else (30 if period == "month" else 90)
    dates = []
    for i in range(days - 1, -1, -1):
        date = datetime.now() - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "dates": dates,
            "data": [
                {
                    "name": "通过率",
                    "data": [85 + int(5 * math.sin(i / 3)) for i in range(days)]
                },
                {
                    "name": "失败率",
                    "data": [10 + int(3 * math.cos(i / 3)) for i in range(days)]
                },
                {
                    "name": "阻塞率",
                    "data": [5 + int(2 * math.sin(i / 5)) for i in range(days)]
                }
            ]
        }
    )


@router.get("/activities")
async def get_recent_activities(
    limit: int = Query(10, ge=1, le=100),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取最近活动"""
    # TODO: 从数据库获取真实数据
    activities = []
    activity_types = ["execution", "case", "plan", "report"]
    activity_titles = [
        "执行了测试用例",
        "创建了测试用例",
        "创建了测试计划",
        "生成了测试报告"
    ]
    
    for i in range(limit):
        activity_type = activity_types[i % len(activity_types)]
        activities.append({
            "id": f"activity_{i+1}",
            "type": activity_type,
            "title": activity_titles[i % len(activity_titles)],
            "description": f"这是第 {i+1} 个活动描述",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat()
        })
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data=activities
    )


@router.get("/project-stats")
async def get_project_stats(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    project_id: Optional[str] = Query(None, alias="projectId"),
    db: Session = Depends(get_db)
):
    """获取项目统计"""
    # TODO: 从数据库获取真实数据
    projects = []
    project_names = ["项目A", "项目B", "项目C", "项目D", "项目E"]
    
    for i in range(min(size, len(project_names))):
        projects.append({
            "id": f"project_{i+1}",
            "projectId": f"project_{i+1}",
            "projectName": project_names[i],
            "totalCases": 200 + i * 50,
            "executionCount": 150 + i * 30,
            "successRate": 85.0 + i * 2.5,
            "executionTrend": 5.0 + i * 1.5,
            "lastExecution": (datetime.now() - timedelta(hours=i*2)).isoformat()
        })
    
    return APIResponse(
        status=ResponseStatus.SUCCESS,
        message="获取成功",
        data={
            "items": projects,
            "total": len(project_names),
            "page": page,
            "size": size,
            "pages": math.ceil(len(project_names) / size),
            "hasNext": page * size < len(project_names),
            "hasPrev": page > 1
        }
    )

