import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

from agent.task_executor import TaskExecutor
from agent.sat_runner import build_invocation, parse_command


@pytest.mark.asyncio
async def test_generic_executor_timeout_and_cancel(tmp_path):
    executor = TaskExecutor(tmp_path)
    result = await executor.execute_task({"task_id": "timeout", "command": [sys.executable, "-c", "import time; time.sleep(20)"], "timeout": 0.05})
    assert result["status"] == "timeout"
    assert result["duration"] < 4
    task = asyncio.create_task(executor.execute_task({"task_id": "cancel", "command": [sys.executable, "-c", "import time; time.sleep(20)"]}))
    while "cancel" not in executor.tasks:
        await asyncio.sleep(0.005)
    assert await executor.cancel_task("cancel")
    assert (await task)["status"] == "cancelled"
    assert not executor.tasks


def test_bench_is_disabled_and_paths_checked(sat_config, tmp_path):
    with pytest.raises(ValueError, match="disabled"):
        build_invocation(sat_config, parse_command("ats-sat --mode sat"), tmp_path, {"case": "id"})
    sat_config.sat_allow_hardware = True
    with pytest.raises(ValueError):
        build_invocation(sat_config, parse_command("ats-sat --mode sat --tests ../../outside"), tmp_path, {"case": "id"})
    with pytest.raises(ValueError):
        parse_command("ats-sat --bogus")


@pytest.mark.asyncio
async def test_pytest_results_cover_setup_teardown_skip_and_missing(tmp_path):
    # Exercise real pytest phases; setup/teardown errors must not report passed.
    source = tmp_path / "test_phases.py"
    source.write_text('''import pytest
@pytest.fixture
def bad_setup():
    raise RuntimeError("setup failed")
@pytest.fixture
def bad_teardown():
    yield
    raise RuntimeError("teardown failed")
def test_caseid_good(): assert True
def test_caseid_bad(): assert False
def test_caseid_setup(bad_setup): pass
def test_caseid_teardown(bad_teardown): pass
@pytest.mark.skip(reason="offline skip")
def test_caseid_skip(): pass
def test_caseid_unselected(): assert False
''')
    codes = ["good", "bad", "setup", "teardown", "skip", "missing"]
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({code: code + "-id" for code in codes}))
    env = dict(os.environ, ATS_CASE_SELECTION=str(selection), ATS_RESULT_FILE=str(tmp_path / "results.json"), PYTHONPATH=str(Path(__file__).resolve().parents[1]), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    process = await asyncio.create_subprocess_exec(sys.executable, "-m", "pytest", "--noconftest", "-p", "integrations.sat_pytest", str(source), cwd=str(tmp_path), env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    output, _ = await process.communicate()
    assert process.returncode == 1, output.decode()
    results = {row["case_code"]: row["status"] for row in json.loads((tmp_path / "results.json").read_text())}
    assert results == {"good": "passed", "bad": "failed", "setup": "error", "teardown": "error", "skip": "skipped", "missing": "error"}


@pytest.mark.asyncio
async def test_sat_multi_id_and_parametrized_case_selection(tmp_path):
    source = tmp_path / "test_sat_names.py"
    source.write_text('import pytest\ndef test_safety_caseid_101_102(): assert True\n@pytest.mark.parametrize("value", [1, 2], ids=["201", "202"])\ndef test_caseid_parameter(value): assert value == 1\n')
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({code: code + "-id" for code in ["101", "102", "201"]}))
    env = dict(os.environ, ATS_CASE_SELECTION=str(selection), ATS_RESULT_FILE=str(tmp_path / "results.json"), PYTHONPATH=str(Path(__file__).resolve().parents[1]), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    process = await asyncio.create_subprocess_exec(sys.executable, "-m", "pytest", "--noconftest", "-p", "integrations.sat_pytest", str(source), cwd=str(tmp_path), env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    output, _ = await process.communicate()
    assert process.returncode == 0, output.decode()
    rows = json.loads((tmp_path / "results.json").read_text())
    assert {row["case_code"] for row in rows} == {"101", "102", "201"}
    assert all(row["status"] == "passed" for row in rows)
