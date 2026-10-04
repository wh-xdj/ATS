"""Persisted HTML snapshots of actual execution records; private downloads."""
from collections import Counter
from datetime import date
from html import escape
from typing import Literal
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, TestReport, TestCase
from models.project import Project
from api.deps import get_current_user
from schemas.common import APIResponse
from services.access import require_project
from services.execution_records import records
from services.inbox import notify

router = APIRouter()


class ReportRequest(BaseModel):
    type: Literal['summary','detailed','trend','coverage'] = 'summary'
    format: Literal['html'] = 'html'
    name: str = '测试结果报告'
    projectId: str | None = None
    startDate: date
    endDate: date
    includeContent: list[str] = []


def render(report):
    snapshot=report.report_data; counts=snapshot['counts']
    headings=['用例编号','用例名称','实际结果','执行时间','日志/错误']
    rows=''.join('<tr>'+''.join('<td>'+escape(str(value or ''))+'</td>' for value in
        [r['caseCode'],r['caseName'],r['result'],r['executedAt'],(r.get('errorMessage') or '')+'\n'+(r.get('executionLog') or '')])+'</tr>' for r in snapshot['rows'])
    metrics=escape(str(counts)); coverage=snapshot['coverage']
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+escape(report.report_name)+
        '</title><style>body{font:16px sans-serif;margin:32px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:8px;white-space:pre-wrap;word-break:break-word}</style><h1>'+escape(report.report_name)+
        '</h1><p>数据来源：ATS 已持久化执行结果。无记录不等于通过。</p><p>实际结果记录数：'+str(len(snapshot['rows']))+
        '；结果计数：'+metrics+'</p><p>期间已执行用例：'+str(coverage['executedCases'])+' / 项目用例：'+str(coverage['totalCases'])+
        '</p><p>每日实际记录：'+escape(str(snapshot['trend']))+'</p><table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headings)+
        '</tr></thead><tbody>'+rows+'</tbody></table></html>')


def metadata(report, db):
    user=db.get(User,report.created_by); snapshot=report.report_data
    return dict(id=report.id,name=report.report_name,reportNumber='RPT-'+report.id[:8],type=report.report_type,
        status='completed',format='html',fileSize=len(render(report).encode()),createdAt=report.created_at.isoformat(),
        creatorId=report.created_by,creatorName=user.username if user else '',projectId=report.project_id,
        startDate=report.start_date.isoformat(),endDate=report.end_date.isoformat(),summary=report.summary,
        totalCases=snapshot['coverage']['totalCases'],executedCases=snapshot['coverage']['executedCases'],
        passedCases=snapshot['counts'].get('passed',0),failedCases=snapshot['counts'].get('failed',0)+snapshot['counts'].get('error',0))


def owned_report(db, user, identifier):
    report=db.query(TestReport).filter(TestReport.id==identifier,TestReport.created_by==str(user.id)).first()
    if not report: raise HTTPException(404,'报告不存在或没有访问权限')
    return report


@router.post('/reports')
async def create_report(body: ReportRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if body.startDate>body.endDate: raise HTTPException(422,'开始日期不能晚于结束日期')
    if not body.name.strip() or len(body.name)>100: raise HTTPException(422,'报告名称长度应为1-100')
    if body.projectId:
        projects=[require_project(db,current_user,body.projectId,'report','create')]
    else:
        projects=db.query(Project).filter(Project.owner_id==str(current_user.id)).all()
    rows=[]; total_cases=0
    for project in projects:
        rows.extend(r for r in records(db,project.id) if body.startDate.isoformat()<=r['executedAt'][:10]<=body.endDate.isoformat())
        total_cases+=db.query(TestCase).filter(TestCase.project_id==project.id).count()
    counts=dict(Counter(r['result'] for r in rows)); trend=dict(Counter(r['executedAt'][:10] for r in rows))
    snapshot=dict(rows=rows,counts=counts,trend=trend,coverage=dict(totalCases=total_cases,executedCases=len({r['caseId'] for r in rows})))
    report=TestReport(id=str(uuid.uuid4()),project_id=body.projectId,report_type=body.type,report_name=body.name.strip(),
        start_date=body.startDate,end_date=body.endDate,report_data=snapshot,summary=f'实际执行记录 {len(rows)} 条',created_by=str(current_user.id))
    db.add(report)
    notify(db,current_user.id,report.id,'report_generated','真实测试报告已生成',report.report_name,report.id)
    db.commit();db.refresh(report)
    return APIResponse(status='success',message='报告已生成',data=metadata(report,db))


@router.get('/reports')
async def get_reports(projectId: str | None = None, search: str = '', type: str | None = None,
    page: int = Query(1,ge=1),size: int = Query(20,ge=1,le=1000),db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    query=db.query(TestReport).filter(TestReport.created_by==str(current_user.id))
    if projectId: query=query.filter(TestReport.project_id==projectId)
    if search: query=query.filter(TestReport.report_name.contains(search))
    if type: query=query.filter(TestReport.report_type==type)
    total=query.count();rows=query.order_by(TestReport.created_at.desc()).offset((page-1)*size).limit(size).all()
    return APIResponse(status='success',message='获取成功',data=dict(items=[metadata(r,db) for r in rows],total=total,page=page,size=size))


@router.get('/reports/{identifier}')
async def get_report(identifier: str,db: Session=Depends(get_db),current_user: User=Depends(get_current_user)):
    return APIResponse(status='success',message='获取成功',data=metadata(owned_report(db,current_user,identifier),db))


@router.get('/reports/{identifier}/download')
async def download_report(identifier: str,db: Session=Depends(get_db),current_user: User=Depends(get_current_user)):
    report=owned_report(db,current_user,identifier)
    return Response(render(report),media_type='text/html',headers={
        'Content-Disposition':f'attachment; filename="report-{report.id}.html"',
        'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; sandbox",'X-Content-Type-Options':'nosniff'})


@router.delete('/reports/{identifier}')
async def delete_report(identifier: str,db: Session=Depends(get_db),current_user: User=Depends(get_current_user)):
    report=owned_report(db,current_user,identifier);db.delete(report);db.commit()
    return APIResponse(status='success',message='报告已删除')
