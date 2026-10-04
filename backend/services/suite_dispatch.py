"""Build the same ordered dispatch message for initial and queued executions."""
from models.test_case import TestCase


def build_suite_message(db, suite, execution_id, executor_id):
    cases = db.query(TestCase).filter(TestCase.id.in_(suite.case_ids)).all()
    by_id = {case.id: case for case in cases}
    if len(by_id) != len(suite.case_ids):
        raise ValueError("Some selected test cases no longer exist")
    git_enabled = suite.git_enabled == "true"
    return {
        "type": "execute_test_suite", "suite_id": suite.id, "plan_id": suite.plan_id,
        "execution_id": execution_id,
        "git_repo_url": suite.git_repo_url if git_enabled else None,
        "git_branch": suite.git_branch if git_enabled else None,
        "git_token": suite.git_token if git_enabled else None,
        "execution_command": suite.execution_command, "case_ids": suite.case_ids,
        "case_codes": [by_id[case_id].case_code for case_id in suite.case_ids],
        "executor_id": executor_id,
    }
