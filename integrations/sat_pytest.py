"""Select ATS cases and atomically emit one result after setup/call/teardown."""
import json
import os
from pathlib import Path

import pytest


class ATSResults:
    def __init__(self, selection, result_path):
        self.selection = selection
        self.result_path = result_path
        self.rows = {}
        self.reports = {}
        self.mapping = {}

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, config, items):
        selected, deselected, assigned = [], [], set()
        for item in items:
            marker = item.get_closest_marker("ats_case")
            if marker:
                candidates = [str(code) for code in marker.args]
            elif item.nodeid in self.selection:
                candidates = [item.nodeid]
            elif "[" in item.name:
                # SAT's case_info_helper treats the parametrized ID as the case ID.
                candidates = [item.name.split("[", 1)[1].rsplit("]", 1)[0]]
            elif "_caseid_" in item.name:
                suffix = item.name.rsplit("_caseid_", 1)[1]
                # Preserve named offline codes; SAT also maps a method to several numeric IDs.
                candidates = [suffix] if suffix in self.selection else suffix.split("_")
            else:
                candidates = [item.nodeid]
            codes = [code for code in candidates if code in self.selection]
            if codes:
                if assigned.intersection(codes):
                    raise pytest.UsageError("Selected ATS case maps to multiple tests; use unique node IDs")
                assigned.update(codes)
                self.mapping[item.nodeid] = codes
                selected.append(item)
            else:
                deselected.append(item)
        items[:] = selected
        config.hook.pytest_deselected(items=deselected)

    def pytest_runtest_logreport(self, report):
        codes = self.mapping.get(report.nodeid)
        if codes is None:
            return
        phases = self.reports.setdefault(report.nodeid, {})
        phases[report.when] = report
        if report.when != "teardown":
            return
        failed = [p for p in phases.values() if p.failed]
        skipped = [p for p in phases.values() if p.skipped]
        status = "error" if any(p.when != "call" for p in failed) else (
            "failed" if failed else "skipped" if skipped else "passed")
        for code in codes:
            self.rows[code] = {
                "test_name": report.nodeid, "case_code": code, "case_id": self.selection[code],
                "status": status, "duration": sum(p.duration for p in phases.values()),
                "error": "\n".join(str(p.longrepr) for p in failed + skipped) or None,
                "log": "\n".join(
                    [f"{p.when}: {p.outcome} ({p.duration:.3f}s)" for p in phases.values()]
                    + list(dict.fromkeys(text for p in phases.values() for _, text in p.sections))
                ),
            }
        self.flush()

    def pytest_sessionfinish(self, session, exitstatus):
        for code, case_id in self.selection.items():
            if code not in self.rows:
                self.rows[code] = {
                    "test_name": code, "case_code": code, "case_id": case_id,
                    "status": "error", "duration": 0,
                    "error": f"Selected case did not complete (pytest exit {int(exitstatus)})",
                }
        self.flush()

    def flush(self):
        temporary = self.result_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(list(self.rows.values()), ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, self.result_path)


def pytest_configure(config):
    config.addinivalue_line("markers", "ats_case(code): stable ATS case code")
    selection_path = os.environ.get("ATS_CASE_SELECTION")
    if selection_path:
        selection = json.loads(Path(selection_path).read_text(encoding="utf-8"))
        config.pluginmanager.register(ATSResults(selection, Path(os.environ["ATS_RESULT_FILE"])))
