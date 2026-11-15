"""Memory observations retain process identity and missing-data meaning."""

from types import SimpleNamespace

import psutil

from devtools.standalone_probe.memory_observation import (
    observe_process_memory,
    process_role,
)


class Process:
    def __init__(self, *, generation=1, denied=False, partial=False):
        self.generation = generation
        self.denied = denied
        self.partial = partial

    def create_time(self):
        return self.generation

    def is_running(self):
        return True

    def status(self):
        return psutil.STATUS_RUNNING

    def cmdline(self):
        return ["python", "-m", "sabueso.explorer._service", "--bootstrap", "private"]

    def memory_info(self):
        return SimpleNamespace(rss=100)

    def memory_full_info(self):
        if self.denied:
            raise psutil.AccessDenied(7)
        return SimpleNamespace(rss=110, uss=70, pss=None if self.partial else 80)


def test_unavailable_memory_does_not_become_zero_or_partial_total():
    observation = observe_process_memory(
        {(7, 1): Process(), (8, 1): Process(denied=True)}
    )
    assert observation["totals"] == {
        "rss_bytes": 210,
        "uss_bytes": None,
        "pss_bytes": None,
    }
    assert observation["processes"][1]["unavailable"] == ["full_memory:AccessDenied"]


def test_recycled_pid_is_excluded_by_generation():
    assert observe_process_memory({(7, 1): Process(generation=2)})["processes"] == []


def test_missing_os_field_is_explicit_and_not_a_complete_total():
    observation = observe_process_memory({(7, 1): Process(partial=True)})
    assert observation["totals"]["uss_bytes"] == 70
    assert observation["totals"]["pss_bytes"] is None
    assert observation["processes"][0]["unavailable"] == ["pss:not_provided"]


def test_roles_are_execution_groups_and_do_not_record_sensitive_arguments():
    observation = observe_process_memory({(7, 1): Process()})
    assert observation["processes"][0]["role"] == "knowledge_and_molecular_service"
    assert "private" not in str(observation)
    assert process_role(["/qt/QtWebEngineProcess", "--type=renderer"]) == (
        "webengine_renderer"
    )
    assert process_role(["python", "-m", "sabueso.explorer"]) == "qt_application"
    assert process_role(["/qt/QtWebEngineProcess", "--type=zygote"]) == (
        "webengine_reported_zygote"
    )


def test_actual_owned_current_process_has_positive_os_memory():
    process = psutil.Process()
    observation = observe_process_memory(
        {(process.pid, process.create_time()): process}
    )
    assert observation["totals"]["rss_bytes"] > 0
    row = observation["processes"][0]
    for field in ("uss_bytes", "pss_bytes"):
        assert row[field] is None or 0 < row[field] <= row["rss_bytes"]
