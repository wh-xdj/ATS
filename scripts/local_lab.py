#!/usr/bin/env python3
"""Launch an isolated ATS software lab on loopback; never reuse the user's DB."""
import argparse
import asyncio
import os
import socket
import sys
import tempfile
import uuid
from datetime import date
from pathlib import Path


async def main(args):
    root = Path(__file__).resolve().parents[1]
    directory = Path(tempfile.mkdtemp(prefix="ats-local-lab-"))
    os.environ["DATABASE_URL"] = "sqlite:///" + str(directory / "ats.sqlite")
    os.environ["ENVIRONMENT"] = "test"
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "backend"))
    import httpx
    import uvicorn
    from main import app
    from database import Base, engine, SessionLocal
    from models import User
    from core.security import get_password_hash
    from agent.agent import Agent
    from agent.config import Config
    from agent.websocket_client import WebSocketClient

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(User(id=str(uuid.uuid4()), username="local_demo", email="local_demo@example.com", password_hash=get_password_hash("ats-local-demo")))
        db.commit()
    sock = socket.socket()
    sock.bind(("127.0.0.1", args.port))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
    serving = asyncio.create_task(server.serve(sockets=[sock]))
    while not server.started:
        await asyncio.sleep(0.05)
    client = httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}/api/v1")
    login = (await client.post("/auth/login", json={"username": "local_demo", "password": "ats-local-demo"})).json()["data"]
    client.headers["Authorization"] = "Bearer " + login["access_token"]
    async def post(path, data):
        response = await client.post(path, json=data)
        response.raise_for_status()
        return response.json()["data"]
    project = await post("/projects", {"name": "SAT / ECU 离线软件验收"})
    cases = []
    for code in ["sat_import", "ecu_positive", "ecu_negative", "ecu_lifecycle"]:
        cases.append(await post("/test-cases", {"project_id": project["id"], "case_code": code, "name": code, "type": "functional", "is_automated": True}))
    ids = [case["id"] for case in cases]
    plan = await post("/test-plans", {"project_id": project["id"], "name": "离线计划", "startDate": date.today().isoformat(), "testCaseIds": ids})
    environment = await post("/environments", {"name": "本机软件节点", "remoteWorkDir": str(directory / "agent"), "reconnectDelay": "1"})
    config = Config()
    config.work_dir = directory / "agent"
    config.work_dir.mkdir()
    config.sat_root, config.ecu_root = args.sat_root, args.ecu_root
    config.monitor_interval = 2
    agent = Agent(config)
    agent.work_dir, agent.running = config.work_dir, True
    agent.ws_client = WebSocketClient(f"ws://127.0.0.1:{port}/ws/agent", environment["token"], on_message=agent.on_message, on_connect=agent.on_connect)
    assert await agent.ws_client.connect()
    receiving = asyncio.create_task(agent.ws_client.receive_messages())
    monitoring = asyncio.create_task(agent._monitor_loop())
    while not agent.environment_id:
        await asyncio.sleep(0.02)
    await post(f'/test-plans/{plan["id"]}/suites', {"plan_id": plan["id"], "name": "SAT / ECU 离线验收", "environment_id": environment["id"], "execution_command": "ats-sat --mode offline", "case_ids": ids})
    frontend = await asyncio.create_subprocess_exec(
        "npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(args.frontend_port), "--strictPort",
        cwd=str(root / "frontend"), env=dict(os.environ, ATS_BACKEND_URL=f"http://127.0.0.1:{port}"),
    )
    print(f"LAB http://127.0.0.1:{args.frontend_port} ; local_demo / ats-local-demo ; state {directory}", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await agent.stop()
        receiving.cancel()
        monitoring.cancel()
        await asyncio.gather(receiving, monitoring, return_exceptions=True)
        frontend.terminate()
        await frontend.wait()
        server.should_exit = True
        await serving
        await client.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = Path(__file__).resolve().parents[2]
    parser.add_argument("--sat-root", default=str(base / "sat"))
    parser.add_argument("--ecu-root", default=str(base / "ecu-simulator"))
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--frontend-port", type=int, default=3300)
    try:
        asyncio.run(main(parser.parse_args()))
    except KeyboardInterrupt:
        pass
