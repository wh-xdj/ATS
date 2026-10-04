"""Software-only checks of the actual SAT and ECU SDK; no bus, SSH or DUT."""
from sat_framework.utils.data_type import CaseStatus, ReportInfo
from automotive_sdk.services.simulator import SimulatorService


def test_caseid_sat_import():
    report = ReportInfo(total=1, passed=1, failed=0)
    assert report.to_dict()["passed"] == 1
    assert CaseStatus.finished.value == 2


def test_caseid_ecu_positive():
    simulator = SimulatorService(None)
    simulator.set_mock_response("OFFLINE", 0x22, b"\xf1\x90ATS")
    assert simulator.get_response_for("OFFLINE", 0x22) == b"\x62\xf1\x90ATS"


def test_caseid_ecu_negative():
    simulator = SimulatorService(None)
    simulator.set_nrc("OFFLINE", 0x22, 0x31)
    assert simulator.get_response_for("OFFLINE", 0x22) == b"\x7f\x22\x31"
    simulator.set_mock_response("OFFLINE", 0x22, b"OK")
    assert simulator.get_response_for("OFFLINE", 0x22) == b"\x62OK"


def test_caseid_ecu_lifecycle():
    simulator = SimulatorService(None)
    simulator.start_simulation(ecus=["OFFLINE", "DUT"], exclude_dut=["DUT"])
    assert simulator.is_running
    assert simulator.get_simulated_ecus() == ["OFFLINE"]
    simulator.stop_simulation()
    assert not simulator.is_running
    assert simulator.get_response_for("OFFLINE", 0x22) is None
