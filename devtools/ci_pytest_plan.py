"""Keep the exact CI selection while receiving large original modules serially."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def serial_module(nodeid):
    name = nodeid.split("::", 1)[0].replace("\\", "/").rsplit("/", 1)[-1]
    return (
        name.startswith("test_card_saved_")
        or (name.startswith("test_card_") and "history" in name)
        or (name.startswith("test_card_") and "original" in name)
        or name
        in {
            "test_card_cell_support_offline.py",
            "test_card_regional_reading_offline.py",
            "test_exploration_shared_values_offline.py",
            "test_installed_receiving_scope_offline.py",
            "test_pytest_scratch_retention_offline.py",
        }
    )


def identity(nodeids):
    return hashlib.sha256(
        json.dumps(sorted(nodeids), ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()


def pytest_addoption(parser):
    parser.addoption("--ci-scope-report", type=Path)
    parser.addoption("--ci-expected-scope", type=Path)


def pytest_configure(config):
    if config.getoption("--ci-scope-report") is not None:
        config.pluginmanager.register(ScopeReport(config), "sabueso-ci-scope")


class ScopeReport:
    def __init__(self, config):
        self.config = config
        self.selected = []
        self.finished = []
        expected = config.getoption("--ci-expected-scope")
        self.expected = (
            json.loads(expected.read_text(encoding="utf-8")) if expected else None
        )

    def pytest_collection_finish(self, session):
        if session.items:
            self.selected = [item.nodeid for item in session.items]
        if self.expected is not None and (
            hasattr(self.config, "workerinput")
            or not getattr(self.config.option, "numprocesses", 0)
        ):
            if sorted(self.selected) != sorted(self.expected):
                raise pytest.UsageError(
                    "CI phase collection differs from its original plan"
                )

    def pytest_xdist_node_collection_finished(self, node, ids):
        if not self.selected:
            self.selected = list(ids)

    def pytest_runtest_logreport(self, report):
        if report.when == "teardown":
            self.finished.append(report.nodeid)

    def pytest_sessionfinish(self, session, exitstatus):
        if hasattr(self.config, "workerinput"):
            return
        path = self.config.getoption("--ci-scope-report")
        path.write_text(
            json.dumps(
                {
                    "selected": self.selected,
                    "finished": self.finished,
                    "exitstatus": int(exitstatus),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def execute(args):
    report = {
        "format": "sabueso.ci_selection_plan@1",
        "state": "RUNNING",
        "selected": [],
        "phases": [],
        "scope": "One original selection; ordinary workers followed by one serial worker. No retries or additional cases.",
    }
    with args.report.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    try:
        return run_plan(args, report)
    except Exception as error:
        report.update(state="INCOMPLETE", reason=f"{type(error).__name__}: {error}")
        raise
    finally:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(
            "SABUESO_CI_PLAN_JSON "
            + json.dumps(
                {key: value for key, value in report.items() if key != "selected"},
                sort_keys=True,
            ),
            flush=True,
        )


def run_plan(args, report):
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if len(command) < 3 or command[1:3] != ["-m", "pytest"]:
        raise ValueError("Expected the original python -m pytest command")
    options = command[3:]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parent)
    environment["COVERAGE_FILE"] = str(args.scratch / ".coverage")
    coverage = any(option.startswith("--cov") for option in options)

    def invoke(label, extra, workers, expected=None):
        scope = args.scratch / (label + "-scope.json")
        actual = [
            sys.executable,
            "-m",
            "pytest",
            *options,
            "-p",
            "ci_pytest_plan",
            "--ci-scope-report=" + str(scope),
            *extra,
        ]
        if workers:
            actual += [
                "-n",
                str(workers),
                "--dist=loadfile",
                "--max-worker-restart=0",
            ]
        if expected is not None:
            expected_path = args.scratch / (label + "-expected.json")
            expected_path.write_text(json.dumps(expected), encoding="utf-8")
            actual += ["--ci-expected-scope=" + str(expected_path)]
        actual += ["--basetemp=" + str(args.scratch / label)]
        result = subprocess.run(actual, env=environment)
        data = json.loads(scope.read_text(encoding="utf-8")) if scope.exists() else None
        return result.returncode, data

    code, discovery = invoke(
        "discovery", ["--collect-only", *(["--no-cov"] if coverage else [])], 0
    )
    if code or discovery is None:
        report.update(state="INCOMPLETE", reason="Original collection failed")
        return code or 1
    selected = discovery["selected"]
    if len(selected) != len(set(selected)):
        report.update(
            state="INCOMPLETE", reason="Original node identifiers are not unique"
        )
        return 1
    report.update(
        selected=selected,
        selected_count=len(selected),
        selected_sha256=identity(selected),
    )
    groups = (
        (
            "ordinary",
            [node for node in selected if not serial_module(node)],
            args.workers,
        ),
        ("serial", [node for node in selected if serial_module(node)], 1),
    )
    executed = []
    failure = 0
    for label, nodes, workers in groups:
        if not nodes:
            continue
        excluded = set(selected) - set(nodes)
        response = args.scratch / (label + "-deselected.args")
        response.write_text(
            "\n".join("--deselect=" + node for node in sorted(excluded)) + "\n",
            encoding="utf-8",
        )
        extra = ["@" + str(response)] if excluded else []
        if coverage and report["phases"]:
            extra.append("--cov-append")
        code, actual = invoke(label, extra, workers, expected=nodes)
        complete = (
            actual is not None
            and set(actual["selected"]) == set(nodes)
            and len(actual["selected"]) == len(nodes)
            and set(actual["finished"]) == set(nodes)
            and len(actual["finished"]) == len(nodes)
        )
        report["phases"].append(
            {
                "name": label,
                "workers": workers,
                "planned_count": len(nodes),
                "planned_sha256": identity(nodes),
                "finished_count": len(actual["finished"]) if actual else 0,
                "exit_code": code,
                "complete_exact_selection": complete,
            }
        )
        if not complete or code not in (0, 1):
            report.update(
                state="INCOMPLETE", reason="Phase selection or completion differs"
            )
            return code or 1
        executed.extend(actual["finished"])
        failure = max(failure, code)
    if len(executed) != len(selected) or set(executed) != set(selected):
        report.update(
            state="INCOMPLETE", reason="Phases do not cover the original selection once"
        )
        return 1
    report.update(state="FAILED" if failure else "PASS", executed_count=len(executed))
    return failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return execute(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
