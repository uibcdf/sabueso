"""Exercise bounded CI execution, nested receiving and actual owned-process stops."""

import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "devtools/run_ci_pytest.py"
SPEC = importlib.util.spec_from_file_location("ci_pytest_resources", LAUNCHER)
RESOURCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESOURCE)
GIB = 1024**3


@pytest.mark.parametrize(
    "requested,cpus,available,total,reserve,expected",
    [
        (2, 20, 50 * GIB, 60 * GIB, 16, (2, 4 * GIB, 16 * GIB)),
        (2, 4, 6 * GIB, 8 * GIB, 0, (2, 4 * GIB, 1717986919)),
        (2, 2, 6 * GIB, 8 * GIB, 0, (1, 2 * GIB, 1717986919)),
        (2, 4, 4 * GIB, 8 * GIB, 0, (1, 2 * GIB, 1717986919)),
        (1, 20, 50 * GIB, 60 * GIB, 16, (1, 2 * GIB, 16 * GIB)),
        (3, 4, 12 * GIB, 16 * GIB, 0, (3, 6 * GIB, 3435973837)),
        (3, 4, 8 * GIB, 16 * GIB, 0, (2, 4 * GIB, 3435973837)),
    ],
)
def test_budgets_preserve_host_margin(
    requested, cpus, available, total, reserve, expected
):
    assert (
        RESOURCE.worker_budget(requested, cpus, available, total, reserve) == expected
    )


def test_insufficient_memory_refuses_even_one_worker():
    with pytest.raises(ValueError, match="Insufficient available RAM"):
        RESOURCE.worker_budget(2, 20, 3 * GIB, 60 * GIB, 16)


@pytest.mark.parametrize(
    "option",
    [
        "-n",
        "-nauto",
        "--numprocesses=8",
        "--dist=loadgroup",
        "--basetemp=x",
        "--tx=2*popen",
        "--max-worker-restart=3",
    ],
)
def test_unsafe_or_competing_parallel_options_refused(option, tmp_path):
    with pytest.raises(ValueError, match="launcher owns"):
        RESOURCE.pytest_command(["python", "-m", "pytest", option], 2, tmp_path)


def test_original_scientific_selection_and_receptor_are_preserved(tmp_path):
    original = [
        "test_original.py::test_read",
        "-m",
        "not online",
        "--receptor=ci",
        "--cov=sabueso",
        "-W",
        "error::ResourceWarning",
    ]
    command = RESOURCE.pytest_command(
        ["python", "-m", "pytest", *original], 2, tmp_path
    )
    assert command[3 : 3 + len(original)] == original
    assert "--dist=loadfile" in command and command[command.index("-n") + 1] == "2"
    assert "--max-worker-restart=0" in command


def test_scratch_count_does_not_follow_caller_links(tmp_path):
    owned = tmp_path / "owned"
    owned.mkdir()
    (owned / "small").write_bytes(b"abc")
    outside = tmp_path / "caller"
    outside.mkdir()
    (outside / "large").write_bytes(b"x" * 1000)
    try:
        (owned / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Creating a directory symlink requires platform permission")
    assert RESOURCE.scratch_bytes(owned) == 3


def invoke(directory, *, seconds=45, extra=()):
    report = directory / "resources.json"
    environment = dict(os.environ)
    # These inherited flags must never reach the outer or nested pytest clients.
    environment["PYTEST_ADDOPTS"] = "-n auto --dist=loadgroup"
    environment["PYTHONPATH"] = str(directory / "caller-shadow")
    environment["OMP_NUM_THREADS"] = "16"
    result = subprocess.run(
        [
            sys.executable,
            str(LAUNCHER),
            "--workers",
            "2",
            "--scratch-parent",
            str(directory),
            "--scratch-gib",
            "0.1",
            "--seconds",
            str(seconds),
            "--report",
            str(report),
            "--",
            "python",
            "-m",
            "pytest",
            "test_client.py",
            "--receptor=llm",
            *extra,
        ],
        cwd=directory,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    return result, json.loads(report.read_text(encoding="utf-8"))


def test_real_workers_and_nested_child_keep_explicit_scope(tmp_path):
    (tmp_path / "test_client.py").write_text(
        """
import json,os,subprocess,sys
from pathlib import Path
def test_copied_child():
    assert "PYTEST_ADDOPTS" not in os.environ
    assert "PYTHONPATH" not in os.environ
    assert all(os.environ[n] == "1" for n in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS"))
    code = "import os,json; print(json.dumps(dict(addopts=os.getenv('PYTEST_ADDOPTS'),native=os.getenv('OMP_NUM_THREADS'))))"
    child = subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,check=True)
    assert json.loads(child.stdout) == dict(addopts=None,native="1")
def test_complete_original_value():
    assert Path("original.json").read_bytes() == b'{"source":"public synthetic control"}'
""",
        encoding="utf-8",
    )
    (tmp_path / "original.json").write_bytes(b'{"source":"public synthetic control"}')
    result, report = invoke(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2 passed" in result.stdout and "PASS exit=0" in result.stdout
    assert report["state"] == "PASS" and report["pytest_exit_code"] == 0
    assert report["workers"] in (1, 2)
    assert report["peak_owned_rss_bytes"] > 0
    assert report["minimum_host_available_bytes"] >= report["host_reserve_bytes"]
    assert report["peak_owned_swap_bytes"] in (0, None)
    assert not report["scratch_retained"] and not Path(report["scratch"]).exists()


def test_actual_test_failure_is_not_hidden_and_keeps_owned_scratch(tmp_path):
    (tmp_path / "test_client.py").write_text(
        "def test_incomplete():\n    assert False, 'original failed'\n",
        encoding="utf-8",
    )
    result, report = invoke(tmp_path)
    assert result.returncode == 1
    assert report["state"] == "FAILED" and report["pytest_exit_code"] == 1
    assert "original failed" in result.stdout
    assert report["scratch_retained"] and Path(report["scratch"]).exists()


@pytest.mark.parametrize("stop_reason", ["elapsed_limit", "owned_stop_request"])
def test_stop_closes_nested_owned_child_and_preserves_other_process(
    tmp_path, stop_reason
):
    pid_file = tmp_path / "owned-child.json"
    (tmp_path / "test_client.py").write_text(
        """
import json,subprocess,sys,time
from pathlib import Path
def test_nested_reader():
    code = "import json,os,time; from pathlib import Path; payload=bytearray(64*1024**2); Path('owned-child.json').write_text(json.dumps(dict(pid=os.getpid()))); time.sleep(60)"
    subprocess.Popen([sys.executable,"-c",code])
    time.sleep(60)
""",
        encoding="utf-8",
    )
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])

    def request_stop():
        deadline = time.monotonic() + 10
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        (tmp_path / "resources.json.stop").write_text(
            "Owned operator stop control", encoding="utf-8"
        )

    operator = None
    if stop_reason == "owned_stop_request":
        operator = threading.Thread(target=request_stop)
        operator.start()
    try:
        result, report = invoke(
            tmp_path, seconds=8 if stop_reason == "elapsed_limit" else 20
        )
        assert unrelated.poll() is None
        assert result.returncode == 70
        assert report["state"] == "STOPPED" and report["stop_reason"] == stop_reason
        assert report["scratch_retained"]
        assert pid_file.exists(), result.stdout + result.stderr
        pid = json.loads(pid_file.read_text())["pid"]
        for _ in range(20):
            if (
                not psutil.pid_exists(pid)
                or psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
            ):
                break
            time.sleep(0.05)
        else:
            pytest.fail("The stopped gate left its observed nested reader running")
        assert report["peak_owned_rss_bytes"] > 64 * 1024**2
    finally:
        if operator:
            operator.join(timeout=12)
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_retired_pid_is_never_used_to_measure_another_process(monkeypatch):
    class Retired:
        def is_running(self):
            return False

        def memory_info(self):
            pytest.fail("The old PID must not be used to measure its new owner")

    class Root:
        def children(self, recursive):
            return []

    monkeypatch.setattr(RESOURCE.psutil, "Process", Root)
    tracked = {(999999, 1): Retired()}
    assert RESOURCE.sample_tree(tracked) == (
        0,
        0 if sys.platform.startswith("linux") else None,
    )
    assert not tracked


def test_successful_pytest_cannot_leave_an_owned_reader_running(tmp_path):
    (tmp_path / "test_client.py").write_text(
        """
import subprocess,sys,time
def test_unfinished_reader():
    subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"])
    time.sleep(0.75)
""",
        encoding="utf-8",
    )
    result, report = invoke(tmp_path)
    assert "PASS exit=0" in result.stdout
    assert result.returncode == 70 and report["pytest_exit_code"] == 0
    assert (
        report["state"] == "STOPPED"
        and report["stop_reason"] == "owned_children_survived"
    )


def test_existing_report_is_never_overwritten(tmp_path):
    report = tmp_path / "resources.json"
    report.write_text("caller-owned", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(LAUNCHER),
            "--report",
            str(report),
            "--",
            "python",
            "-m",
            "pytest",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert result.returncode != 0 and report.read_text() == "caller-owned"
    assert not list(tmp_path.glob("sabueso-ci-pytest-*"))


def test_insufficient_host_headroom_refuses_before_creating_scratch(tmp_path):
    report = tmp_path / "resources.json"
    result = subprocess.run(
        [
            sys.executable,
            str(LAUNCHER),
            "--reserve-gib",
            "999999",
            "--scratch-parent",
            str(tmp_path),
            "--report",
            str(report),
            "--",
            "python",
            "-m",
            "pytest",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    data = json.loads(report.read_text())
    assert result.returncode == 71 and data["state"] == "REFUSED"
    assert "Insufficient available RAM" in data["reason"]
    assert data["host_total_bytes"] > 0
    assert 0 < data["host_available_before_bytes"] <= data["host_total_bytes"]
    assert data["cpu_slots_observed"] >= 1
    assert data["minimum_available_for_one_worker_bytes"] > data["host_total_bytes"]
    assert len(data["preflight_memory_samples"]) == 1
    assert "command" not in data and not list(tmp_path.glob("sabueso-ci-pytest-*"))


def controlled_preflight(monkeypatch, snapshots, on_sleep=None):
    clock = {"now": 0}
    pauses = []
    remaining = iter(snapshots)
    current = snapshots[-1]

    def memory():
        nonlocal current
        current = next(remaining, current)
        return SimpleNamespace(total=current[0], available=current[1])

    def sleep(seconds):
        pauses.append(seconds)
        clock["now"] += seconds
        if on_sleep:
            on_sleep()

    monkeypatch.setattr(RESOURCE, "psutil", SimpleNamespace(virtual_memory=memory))
    monkeypatch.setattr(
        RESOURCE,
        "time",
        SimpleNamespace(
            monotonic=lambda: clock["now"],
            sleep=sleep,
        ),
    )
    return pauses


def test_transient_headroom_settles_before_first_launch(monkeypatch, tmp_path):
    pauses = controlled_preflight(monkeypatch, [(8 * GIB, 2 * GIB), (8 * GIB, 4 * GIB)])
    report = {}
    workers, limit, reserve, memory = RESOURCE.preflight_budget(
        3, 4, 0, 12, tmp_path / "owned.stop", report
    )
    assert (workers, limit, reserve) == (1, 2 * GIB, 1717986919)
    assert memory.available == 4 * GIB
    assert pauses == [5] and report["preflight_wait_elapsed_s"] == 5
    assert [s["available_bytes"] for s in report["preflight_memory_samples"]] == [
        2 * GIB,
        4 * GIB,
    ]


def test_persistent_headroom_refuses_at_bounded_deadline(monkeypatch, tmp_path):
    pauses = controlled_preflight(monkeypatch, [(8 * GIB, 2 * GIB)])
    report = {}
    with pytest.raises(ValueError, match="Insufficient available RAM"):
        RESOURCE.preflight_budget(3, 4, 0, 12, tmp_path / "owned.stop", report)
    assert pauses == [5, 5, 2] and report["preflight_wait_elapsed_s"] == 12
    assert report["host_total_bytes"] == 8 * GIB
    assert report["host_available_before_bytes"] == 2 * GIB
    assert report["host_reserve_bytes"] == 1717986919
    assert report["minimum_available_for_one_worker_bytes"] == 1717986919 + 2 * GIB
    assert len(report["preflight_memory_samples"]) == 4
    assert not list(tmp_path.iterdir())


def test_physically_impossible_budget_never_waits(monkeypatch, tmp_path):
    pauses = controlled_preflight(monkeypatch, [(2 * GIB, 2 * GIB)])
    report = {}
    with pytest.raises(ValueError, match="Insufficient available RAM"):
        RESOURCE.preflight_budget(3, 4, 0, 30, tmp_path / "owned.stop", report)
    assert pauses == [] and report["preflight_wait_elapsed_s"] == 0
    assert report["minimum_available_for_one_worker_bytes"] == 3 * GIB
    assert len(report["preflight_memory_samples"]) == 1


def test_zero_grace_preserves_immediate_refusal(monkeypatch, tmp_path):
    pauses = controlled_preflight(monkeypatch, [(8 * GIB, 2 * GIB)])
    report = {}
    with pytest.raises(ValueError, match="Insufficient available RAM"):
        RESOURCE.preflight_budget(3, 4, 0, 0, tmp_path / "owned.stop", report)
    assert pauses == [] and report["preflight_wait_elapsed_s"] == 0


def test_owned_stop_request_interrupts_preflight_wait(monkeypatch, tmp_path):
    stop = tmp_path / "owned.stop"
    pauses = controlled_preflight(
        monkeypatch,
        [(8 * GIB, 2 * GIB)],
        on_sleep=lambda: stop.write_text("Operator stop", encoding="utf-8"),
    )
    report = {}
    with pytest.raises(ValueError, match="stop request.*preflight"):
        RESOURCE.preflight_budget(3, 4, 0, 30, stop, report)
    assert pauses == [5] and report["preflight_wait_elapsed_s"] == 5
    assert len(report["preflight_memory_samples"]) == 1


def test_preflight_interrupt_is_reported_without_launching_pytest(
    monkeypatch, tmp_path
):
    def interrupted(*args):
        raise KeyboardInterrupt

    def forbidden(*args, **kwargs):
        pytest.fail("An interrupted preflight must not start pytest")

    monkeypatch.setattr(RESOURCE, "preflight_budget", interrupted)
    monkeypatch.setattr(RESOURCE.subprocess, "Popen", forbidden)
    report = tmp_path / "resources.json"
    code = RESOURCE.main(["--report", str(report), "--", "python", "-m", "pytest"])
    data = json.loads(report.read_text())
    assert code == 130 and data["state"] == "REFUSED"
    assert data["reason"] == "Preflight interrupted before pytest launch"
    assert "scratch" not in data and "command" not in data


@pytest.mark.parametrize("limit", ["-1", "nan", "inf", "61"])
def test_invalid_preflight_wait_never_creates_output(tmp_path, limit):
    report = tmp_path / "resources.json"
    result = subprocess.run(
        [
            sys.executable,
            str(LAUNCHER),
            "--preflight-wait-seconds",
            limit,
            "--report",
            str(report),
            "--",
            "python",
            "-m",
            "pytest",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    assert result.returncode == 2 and "preflight wait" in result.stderr
    assert not report.exists() and not list(tmp_path.iterdir())


def test_hosted_profile_does_not_guess_slurm_allocations(tmp_path, monkeypatch):
    monkeypatch.setenv("SLURM_JOB_ID", "public-synthetic-control")
    report = tmp_path / "resources.json"
    code = RESOURCE.main(["--report", str(report), "--", "python", "-m", "pytest"])
    data = json.loads(report.read_text())
    assert code == 71 and data["state"] == "REFUSED"
    assert "Slurm allocations" in data["reason"]
    assert "scratch" not in data and "command" not in data
