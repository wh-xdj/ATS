"""Read actual persisted records, including historical suite records."""
from models import TestExecution, TestCase, User
from models.test_suite import TestSuiteExecution, TestSuite
from utils.serializer import serialize_model


def records(db, project_id):
    output = {}
    for row in db.query(TestExecution).join(TestCase).filter(TestCase.project_id == project_id).all():
        case = db.get(TestCase, row.case_id)
        data = serialize_model(row, camel_case=True)
        data.update(caseName=case.name, caseCode=case.case_code)
        output[row.id] = data
    for row in db.query(TestSuiteExecution).join(TestCase).filter(TestCase.project_id == project_id).all():
        if row.id in output:
            continue
        case = db.get(TestCase, row.case_id)
        suite = db.get(TestSuite, row.suite_id)
        try:
            duration = float((row.duration or '0').rstrip('s'))
        except ValueError:
            duration = None
        output[row.id] = dict(id=row.id, planId=suite.plan_id if suite else None, caseId=row.case_id, executorId=row.executor_id,
            environmentId=row.environment_id, result=row.result, duration=duration, notes=None,
            errorMessage=row.error_message, executionLog=row.log_output,
            executedAt=row.executed_at.isoformat(), createdAt=row.created_at.isoformat(),
            caseName=case.name, caseCode=case.case_code)
    for data in output.values():
        user = db.get(User, data['executorId'])
        data['executorName'] = user.username if user else ''
    return sorted(output.values(), key=lambda r: (r['executedAt'], r['id']), reverse=True)
