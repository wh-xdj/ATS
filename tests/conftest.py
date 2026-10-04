"""All regression state lives in a fresh SQLite database and temporary workspace."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
TEST_DIRECTORY = Path(tempfile.mkdtemp(prefix="ats-software-regression-"))
os.environ["DATABASE_URL"] = "sqlite:///" + str(TEST_DIRECTORY / "test.sqlite")
os.environ["ENVIRONMENT"] = "test"
os.environ["LOG_FILE"] = str(TEST_DIRECTORY / "backend.log")


@pytest.fixture(autouse=True)
def isolated_database():
    from database import engine, Base
    import models
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def sat_config(tmp_path):
    from agent.config import Config
    config = Config()
    config.work_dir = tmp_path / "agent"
    config.work_dir.mkdir()
    config.sat_root = os.environ.get("ATS_SAT_ROOT", "/Users/xiongdejian/project/python_project/sat")
    config.ecu_root = os.environ.get("ATS_ECU_ROOT", "/Users/xiongdejian/project/python_project/ecu-simulator")
    config.default_timeout = 20
    return config
