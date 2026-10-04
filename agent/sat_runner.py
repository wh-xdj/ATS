"""SAT runner using existing suite protocol and an isolated directory per execution."""
import asyncio
import json
import os
import shlex
import signal
import sys
import time
import uuid
from pathlib import Path


def parse_command(command):
    import argparse
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise ValueError(message)
    parser = Parser(prog="ats-sat")
    parser.add_argument("--mode", choices=["offline", "sat"], default="offline")
    parser.add_argument("--tests", default="test_case")
    parser.add_argument("--bench-config")
    parser.add_argument("--case-config")
    parser.add_argument("--timeout", type=float)
    parts = shlex.split(command)
    if not parts or parts[0] != "ats-sat":
        raise ValueError("Expected ats-sat command")
    try:
        return parser.parse_args(parts[1:])
    except (SystemExit, argparse.ArgumentError) as exc:
        raise ValueError("Invalid ats-sat options") from exc


def build_invocation(config, options, directory, selection):
    ats_root = Path(__file__).resolve().parents[1]
    sat_root = Path(config.sat_root).expanduser().resolve()
    ecu_root = Path(config.ecu_root).expanduser().resolve()
    if not (sat_root / "sat_framework").is_dir():
        raise ValueError("SAT root must contain sat_framework")
    if not (ecu_root / "ecu_simulator").is_dir():
        raise ValueError("ECU root must contain legacy ecu_simulator")
    if options.mode == "sat" and not config.sat_allow_hardware:
        raise ValueError("SAT bench execution disabled; configure allow_hardware only on an approved bench")
    selection_path = directory / "selection.json"
    selection_path.write_text(json.dumps(selection), encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "ATS_CASE_SELECTION": str(selection_path),
        "ATS_RESULT_FILE": str(directory / "results.json"),
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": os.pathsep.join([str(ats_root), str(sat_root), str(ecu_root), str(ecu_root / "src")]),
    })
    command = [config.sat_python or sys.executable, "-m", "pytest", "-p", "integrations.sat_pytest",
               "-o", "addopts=", "-p", "no:cacheprovider", "--junitxml", str(directory / "junit.xml")]
    if options.mode == "offline":
        # Do not load SAT's hooks: they connect to bench/intranet services at startup.
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        command += ["--noconftest", "-c", str(ats_root / "integrations" / "pytest.ini"),
                    str(ats_root / "integrations" / "offline_cases.py")]
    else:
        def local_path(value):
            path = (sat_root / value).resolve()
            path.relative_to(sat_root)
            if not path.exists():
                raise ValueError(f"SAT path does not exist: {value}")
            return str(path)
        command += ["-c", str(sat_root / "pytest.ini"), local_path(options.tests)]
        if options.bench_config:
            command += ["--tbcfg", local_path(options.bench_config)]
        if options.case_config:
            command += ["--tccfg", local_path(options.case_config)]
        command += ["--alluredir", str(directory / "allure-results")]
    return command, env


async def terminate_process(process):
    """Terminate the runner and its children without blocking the event loop."""
    if process.returncode is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        await asyncio.wait_for(process.wait(), timeout=3)
    except asyncio.TimeoutError:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        await process.wait()
    except ProcessLookupError:
        pass


class SATRunner:
    def __init__(self, agent):
        self.agent = agent
        self.runs = {}
        self.suites = {}
        self.executed = set()
        self.delivery_lock = asyncio.Lock()

    @property
    def outbox(self):
        return self.agent.work_dir / "sat-outbox"

    async def deliver(self, payload):
        self.outbox.mkdir(parents=True, exist_ok=True)
        key = str(uuid.uuid5(uuid.NAMESPACE_URL, payload["execution_id"] + ":" + (payload.get("case_id") or "completed")))
        payload["event_id"] = key
        path = self.outbox / (key + ".json")
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(temporary, path)
        await self.flush()

    async def flush(self):
        if not self.agent.work_dir or not self.agent.ws_client:
            return
        async with self.delivery_lock:
            if not self.outbox.exists():
                return
            # Results must reach the backend before completion releases the queue.
            pending = [(path, json.loads(path.read_text(encoding="utf-8"))) for path in self.outbox.glob("*.json")]
            pending.sort(key=lambda entry: (entry[1]["type"] == "test_suite_completed", entry[0].name))
            for path, payload in pending:
                if not await self.agent.ws_client.send_message(payload):
                    break


    def acknowledge(self, event_id):
        try:
            uuid.UUID(event_id)
        except (ValueError, TypeError, AttributeError):
            return
        (self.outbox / (event_id + ".json")).unlink(missing_ok=True)

    def has_suite(self, suite_id):
        return suite_id in self.suites.values()

    def start(self, message):
        execution_id = message["execution_id"]
        if execution_id in self.runs or execution_id in self.executed:
            return
        self.executed.add(execution_id)
        self.suites[execution_id] = message["suite_id"]
        self.runs[execution_id] = asyncio.create_task(self.execute(message))

    async def cancel(self, suite_id, execution_id=None):
        tasks = [task for key, task in self.runs.items()
                 if self.suites[key] == suite_id and (execution_id is None or key == execution_id)]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def log(self, message, text):
        await self.agent.ws_client.send_message({
            "type": "test_suite_log", "suite_id": message["suite_id"],
            "execution_id": message["execution_id"], "level": "info", "message": text,
        })

    async def execute(self, message):
        suite_id, execution_id = message["suite_id"], message["execution_id"]
        process, rows, error, status = None, [], None, "failed"
        started = time.monotonic()
        directory = self.agent.work_dir / "suites" / suite_id / "executions" / execution_id
        directory.mkdir(parents=True, exist_ok=True)
        try:
            options = parse_command(message["execution_command"])
            ids, codes = message["case_ids"], message.get("case_codes", [])
            if len(ids) != len(codes) or len(set(codes)) != len(codes) or not all(codes):
                raise ValueError("SAT requires one unique case code per selected ATS case")
            timeout = options.timeout if options.timeout is not None else self.agent.config.default_timeout
            if timeout <= 0:
                raise ValueError("SAT timeout must be positive")
            command, env = build_invocation(self.agent.config, options, directory, dict(zip(codes, ids)))
            await self.log(message, "SAT execution: " + options.mode)
            process = await asyncio.create_subprocess_exec(
                *command, cwd=str(directory), env=env, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT, start_new_session=(os.name == "posix"),
            )
            async def read_output():
                with (directory / "output.log").open("w", encoding="utf-8") as log:
                    while True:
                        chunk = await process.stdout.read(4096)
                        if not chunk:
                            break
                        text = chunk.decode("utf-8", errors="replace")
                        log.write(text)
                        log.flush()
                        await self.log(message, text)
                return await process.wait()
            exit_code = await asyncio.wait_for(read_output(), timeout=timeout)
            result_file = directory / "results.json"
            if result_file.exists():
                rows = json.loads(result_file.read_text(encoding="utf-8"))
            status = "completed" if exit_code == 0 and len(rows) == len(ids) and all(
                row["status"] in ["passed", "skipped"] for row in rows) else "failed"
            if exit_code:
                error = f"pytest exited with code {exit_code}; see output.log"
        except asyncio.CancelledError:
            status, error = "cancelled", "Execution cancelled"
        except asyncio.TimeoutError:
            error = "SAT execution timed out"
        except Exception as exc:
            error = str(exc)
        finally:
            if process:
                await terminate_process(process)
            try:
                if status != "cancelled":
                    row_by_id = {row["case_id"]: row for row in rows}
                    for case_id in message["case_ids"]:
                        row = row_by_id.get(case_id, {"status": "error", "duration": 0, "error": error or "No result emitted"})
                        await self.deliver({
                            "type": "test_suite_result", "suite_id": suite_id, "execution_id": execution_id,
                            "case_id": case_id, "result": row["status"], "duration": f'{row["duration"]:.3f}s',
                            "error_message": row.get("error"), "log_output": row.get("log") or row.get("error"),
                            "executor_id": message.get("executor_id", "system"),
                        })
                (directory / "run.json").write_text(json.dumps({
                    "execution_id": execution_id, "status": status, "error": error,
                    "exit_code": process.returncode if process else None,
                    "outcome": "cancelled" if status == "cancelled" else "timeout" if error == "SAT execution timed out" else status,
                }), encoding="utf-8")
                self.runs.pop(execution_id, None)
                self.suites.pop(execution_id, None)
                await self.deliver({
                    "type": "test_suite_completed", "suite_id": suite_id, "execution_id": execution_id,
                    "status": status, "message": error or "SAT execution finished",
                    "duration": f"{time.monotonic() - started:.3f}s", "total_case_count": len(message["case_ids"]),
                    "reported_case_count": len(rows), "exit_code": process.returncode if process else None,
                    "outcome": "cancelled" if status == "cancelled" else "timeout" if error == "SAT execution timed out" else status,
                })
            finally:
                if self.runs.get(execution_id) is asyncio.current_task():
                    self.runs.pop(execution_id, None)
                    self.suites.pop(execution_id, None)
