"""Real loopback HTTP + WebSocket + Agent + subprocess + SQLite persistence."""
import asyncio
import json
import socket
import uuid

import httpx
import pytest
import pytest_asyncio
import uvicorn

from agent.agent import Agent
from agent.websocket_client import WebSocketClient


async def until(predicate, timeout=15):
    async def poll():
        while not predicate():
            await asyncio.sleep(0.02)
    await asyncio.wait_for(poll(), timeout)


@pytest_asyncio.fixture
async def lab(sat_config):
    from main import app
    from database import SessionLocal
    from models import User
    from core.security import get_password_hash
    from api.v1.websocket import manager
    with SessionLocal() as db:
        user = User(id=str(uuid.uuid4()), username="software_test", email="software_test@example.com", password_hash=get_password_hash("ats-local-test"))
        db.add(user)
        db.commit()
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="off"))
    server_task = asyncio.create_task(server.serve(sockets=[sock]))
    await until(lambda: server.started)
    client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}")
    response = await client.post("/api/v1/auth/login", json={"username": "software_test", "password": "ats-local-test"})
    assert response.status_code == 200, response.text
    login = response.json()["data"]
    client.headers["Authorization"] = "Bearer " + (login.get("accessToken") or login["access_token"])
    async def post(path, data):
        response = await client.post("/api/v1" + path, json=data)
        assert response.status_code == 200, response.text
        return response.json()["data"]
    project = await post("/projects", {"name": "SAT software regression"})
    cases = []
    for code in ["sat_import", "ecu_positive", "ecu_negative", "ecu_lifecycle"]:
        case = await post("/test-cases", {"project_id": project["id"], "case_code": code, "name": code, "type": "functional", "is_automated": True})
        assert case["isAutomated"] is True
        cases.append(case)
    # Reverse the stored IDs to detect accidental DB query order mapping.
    ids = [case["id"] for case in reversed(cases)]
    plan = await post("/test-plans", {"project_id": project["id"], "name": "Offline", "startDate": "2026-10-04", "testCaseIds": ids})
    environment = await post("/environments", {"name": "Offline node", "remoteWorkDir": str(sat_config.work_dir), "reconnectDelay": "1", "maxConcurrentTasks": 1})
    agent = Agent(sat_config)
    agent.work_dir = sat_config.work_dir
    agent.ws_client = WebSocketClient(f"ws://127.0.0.1:{port}/ws/agent", environment["token"], on_message=agent.on_message, on_connect=agent.on_connect, on_disconnect=agent.on_disconnect)
    assert await agent.ws_client.connect()
    receiving = asyncio.create_task(agent.ws_client.receive_messages())
    await until(lambda: agent.environment_id == environment["id"])
    suite = await post(f'/test-plans/{plan["id"]}/suites', {"plan_id": plan["id"], "name": "SAT offline", "environment_id": environment["id"], "execution_command": "ats-sat --mode offline", "case_ids": ids})
    value = {"client": client, "post": post, "agent": agent, "suite": suite, "plan": plan, "cases": cases, "environment": environment, "manager": manager}
    try:
        yield value
    finally:
        await agent.stop()
        receiving.cancel()
        await asyncio.gather(receiving, return_exceptions=True)
        await client.aclose()
        server.should_exit = True
        await asyncio.wait_for(server_task, 5)
        manager.active_connections.clear()


def queue_states(suite_id):
    from database import SessionLocal
    from models.task_queue import TaskQueue
    with SessionLocal() as db:
        return {task.execution_id: task.status for task in db.query(TaskQueue).filter(TaskQueue.suite_id == suite_id).all()}


@pytest.mark.asyncio
async def test_http_queue_actual_sat_ecu_results(lab):
    from database import SessionLocal
    from models.test_suite import TestSuiteExecution
    from models.test_plan import PlanCaseRelation
    suite_id = lab["suite"]["id"]
    path = f"/api/v1/test-plans/suites/{suite_id}/execute"
    first = await lab["client"].post(path)
    second = await lab["client"].post(path)
    assert first.status_code == second.status_code == 200
    assert "队列" in second.json()["message"]
    await until(lambda: len(queue_states(suite_id)) == 2 and all(s == "completed" for s in queue_states(suite_id).values()))
    with SessionLocal() as db:
        rows = db.query(TestSuiteExecution).filter(TestSuiteExecution.suite_id == suite_id).all()
        assert len(rows) == 8
        assert all(row.result == "passed" for row in rows)
        assert {row.case_id for row in rows} == {case["id"] for case in lab["cases"]}
        assert all(row.execution_status == "pass" for row in db.query(PlanCaseRelation).all())
    await until(lambda: not list(lab["agent"].sat_runner.outbox.glob("*.json")))
    response = await lab["client"].get(f"/api/v1/test-plans/suites/{suite_id}/executions")
    assert response.status_code == 200, response.text
    history = await lab["client"].get(f"/api/v1/test-plans/suites/{suite_id}/suite-executions")
    assert history.status_code == 200, history.text
    assert len(history.json()["data"]["items"]) == 2
    assert all(row["caseCount"] == 4 for row in history.json()["data"]["items"])
    print("E2E: two HTTP executions; second queued; actual SAT/ECU produced eight persisted passed rows; all ACKed")


@pytest.mark.asyncio
async def test_normal_close_reconnect_replay_is_idempotent(lab):
    from database import SessionLocal
    from models.test_suite import TestSuiteExecution
    from services.suite_results import result_id
    suite_id = lab["suite"]["id"]
    await lab["client"].post(f"/api/v1/test-plans/suites/{suite_id}/execute")
    await until(lambda: lab["agent"].sat_runner.has_suite(suite_id))
    during_run = lab["agent"].ws_client.websocket
    await during_run.close(code=1000)
    await until(lambda: bool(list(lab["agent"].sat_runner.outbox.glob("*.json"))))
    await until(lambda: bool(queue_states(suite_id)) and all(s == "completed" for s in queue_states(suite_id).values()))
    await until(lambda: not list(lab["agent"].sat_runner.outbox.glob("*.json")))
    execution_id = next(iter(queue_states(suite_id)))
    case_id = lab["cases"][0]["id"]
    with SessionLocal() as db:
        row = db.get(TestSuiteExecution, result_id(execution_id, case_id))
        assert row is not None
    connection = lab["agent"].ws_client.websocket
    await connection.close(code=1000)
    await until(lambda: not lab["agent"].ws_client.connected)
    await lab["agent"].sat_runner.deliver({"type": "test_suite_result", "suite_id": suite_id, "execution_id": execution_id, "case_id": case_id, "result": "passed", "duration": "0.001s"})
    assert list(lab["agent"].sat_runner.outbox.glob("*.json"))
    await until(lambda: lab["agent"].ws_client.connected and lab["agent"].ws_client.websocket is not connection)
    await until(lambda: not list(lab["agent"].sat_runner.outbox.glob("*.json")))
    with SessionLocal() as db:
        assert db.query(TestSuiteExecution).count() == 4
        from models import TestExecution, Notification
        assert db.query(TestExecution).count() == 4
        assert db.query(Notification).count() == 1
    print("E2E: normal WebSocket close recovered; disk outbox replay ACKed without duplicate result rows")


@pytest.mark.asyncio
async def test_timeout_cancel_and_queue_resume(lab):
    client, suite_id = lab["client"], lab["suite"]["id"]
    base = f"/api/v1/test-plans/suites/{suite_id}"
    response = await client.put(base, json={"execution_command": "ats-sat --mode offline --timeout 0.001"})
    assert response.status_code == 200
    await client.post(base + "/execute")
    await until(lambda: bool(queue_states(suite_id)) and all(s == "failed" for s in queue_states(suite_id).values()))
    run_files = list(lab["agent"].work_dir.glob("suites/*/executions/*/run.json"))
    assert json.loads(run_files[0].read_text())["outcome"] == "timeout"
    await client.put(base, json={"execution_command": "ats-sat --mode offline"})
    await client.post(base + "/execute")
    await until(lambda: lab["agent"].sat_runner.has_suite(suite_id))
    states = queue_states(suite_id)
    execution_id = next(key for key, value in states.items() if value == "running")
    await client.post(base + "/execute")
    response = await client.post(base + "/cancel", json={"executionId": execution_id})
    assert response.status_code == 200, response.text
    await until(lambda: "running" not in queue_states(suite_id).values() and "pending" not in queue_states(suite_id).values())
    assert sorted(queue_states(suite_id).values()) == ["cancelled", "completed", "failed"]
    print("E2E: real silent subprocess timeout; running cancellation; queued successor completed")


@pytest.mark.asyncio
async def test_concurrent_same_suite_keeps_execution_results_separate(lab):
    client, suite_id = lab["client"], lab["suite"]["id"]
    response = await client.put(f'/api/v1/environments/{lab["environment"]["id"]}', json={"maxConcurrentTasks": 2})
    assert response.status_code == 200, response.text
    await asyncio.gather(*(client.post(f"/api/v1/test-plans/suites/{suite_id}/execute") for _ in range(3)))
    await until(lambda: len(queue_states(suite_id)) == 3 and all(s == "completed" for s in queue_states(suite_id).values()))
    from database import SessionLocal
    from models.test_suite import TestSuiteExecution
    with SessionLocal() as db:
        assert db.query(TestSuiteExecution).count() == 12
    assert not lab["agent"].sat_runner.runs
    print("E2E: three same-suite executions at node concurrency=2 retained twelve distinct results")


@pytest.mark.asyncio
async def test_missing_selected_case_is_error_not_success(lab):
    client, suite_id = lab["client"], lab["suite"]["id"]
    case = lab["cases"][0]
    missing = await lab["post"]("/test-cases", {"project_id": case["projectId"], "case_code": "not_present", "name": "Missing pytest case", "type": "functional", "is_automated": True})
    case = missing
    response = await client.put(f"/api/v1/test-plans/suites/{suite_id}", json={"case_ids": [case["id"]]})
    assert response.status_code == 200, response.text
    await client.post(f"/api/v1/test-plans/suites/{suite_id}/execute")
    await until(lambda: bool(queue_states(suite_id)) and all(s == "failed" for s in queue_states(suite_id).values()))
    from database import SessionLocal
    from models.test_suite import TestSuiteExecution
    with SessionLocal() as db:
        row = db.query(TestSuiteExecution).filter(TestSuiteExecution.case_id == case["id"]).one()
        assert row.result == "error"
    print("E2E: missing selected pytest case persisted error and failed the execution")


@pytest.mark.asyncio
async def test_existing_case_plan_and_environment_apis(lab):
    client, case = lab["client"], lab["cases"][0]
    response = await client.put(f'/api/v1/test-cases/{case["id"]}', json={"name": "Edited offline case", "priority": "P0", "requirement_ref": "SAT-REQ-1", "steps": [{"step": 1, "action": "Read DID", "expected": "Positive UDS response"}], "level": "system", "is_automated": True})
    assert response.status_code == 200
    detail = await client.get(f'/api/v1/test-cases/{case["id"]}')
    assert detail.json()["data"]["name"] == "Edited offline case"
    assert detail.json()["data"]["priority"] == "P0"
    assert detail.json()["data"]["requirementRef"] == "SAT-REQ-1"
    assert detail.json()["data"]["steps"][0]["expected"] == "Positive UDS response"
    assert detail.json()["data"]["level"] == "system"
    plans = await client.get("/api/v1/test-plans", params={"project_id": case["projectId"]})
    assert plans.status_code == 200 and plans.json()["data"]["total"] == 1
    cases = await client.get("/api/v1/test-cases", params={"project_id": case["projectId"], "is_automated": True})
    assert cases.status_code == 200 and cases.json()["data"]["total"] == 4
    env = await client.get(f'/api/v1/environments/{lab["environment"]["id"]}')
    assert env.status_code == 200 and env.json()["data"]["reconnectDelay"] == "1"
    plan = plans.json()["data"]["items"][0]
    settings = {"notificationMethods": ["email"], "notificationRecipients": ["software_test@example.com"], "retryOnFailure": True}
    edited_plan = await client.put(f'/api/v1/test-plans/{plan["id"]}', json={"environmentId": lab["environment"]["id"], "environmentConfig": settings})
    assert edited_plan.status_code == 200
    plan_detail = (await client.get(f'/api/v1/test-plans/{plan["id"]}')).json()["data"]
    assert plan_detail["environmentId"] == lab["environment"]["id"]
    assert plan_detail["environmentConfig"] == settings
    assert len(plan_detail["testCases"]) == 4
    print("Regression: login, project/case/plan/environment APIs, automated filter, editable case fields and plan config persisted")
