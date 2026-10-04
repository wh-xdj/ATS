"""Execution history reads actual persisted results; unknown IDs never pass."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from api.deps import get_current_user
from models import User, TestCase, TestExecution
from models.test_suite import TestSuiteExecution
from services.access import require_project
from services.execution_records import records
from schemas.common import APIResponse

router = APIRouter()


def reply(data):
    return APIResponse(status='success', message='获取成功', data=data)


@router.get('')
async def get_executions(project_id: str, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=1000),
    search: str = '', case_id: str | None = Query(None, alias='caseId'), plan_id: str | None = Query(None, alias='planId'),
    environment_id: str | None = Query(None, alias='environmentId'), executor_id: str | None = Query(None, alias='executorId'), result: str | None = None,
    start_date: str | None = Query(None, alias='startDate'), end_date: str | None = Query(None, alias='endDate'),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_project(db, current_user, project_id)
    rows = records(db, project_id)
    rows = [r for r in rows if (not search or search.lower() in (r['caseName'] + r['caseCode']).lower())
        and (not case_id or r['caseId'] == case_id) and (not plan_id or r['planId'] == plan_id)
        and (not executor_id or r['executorId'] == executor_id) and (not environment_id or r['environmentId'] == environment_id) and (not result or r['result'] == result)
        and (not start_date or r['executedAt'][:10] >= start_date[:10])
        and (not end_date or r['executedAt'][:10] <= end_date[:10])]
    total = len(rows)
    return reply(dict(items=rows[(page-1)*size:page*size], total=total, page=page, size=size,
        pages=(total+size-1)//size, hasNext=page*size<total, hasPrev=page>1))


def find_record(db, user, identifier):
    row = db.get(TestExecution, identifier) or db.get(TestSuiteExecution, identifier)
    if not row:
        raise HTTPException(404, '执行记录不存在')
    case = db.get(TestCase, row.case_id)
    require_project(db, user, case.project_id)
    return next(r for r in records(db, case.project_id) if r['id'] == identifier)


@router.get('/{execution_id}')
async def get_execution(execution_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return reply(find_record(db, current_user, execution_id))


@router.get('/{execution_id}/logs')
async def get_execution_logs(execution_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return reply(find_record(db, current_user, execution_id).get('executionLog') or '')


@router.put('/{execution_id}')
@router.post('/{execution_id}/attachments')
@router.get('/{execution_id}/attachments')
async def unsupported(execution_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    find_record(db, current_user, execution_id)
    raise HTTPException(501, '执行结果不可手动改为通过；执行附件尚未支持，可使用工作空间上传')
