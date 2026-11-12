"""Run the unchanged CI pytest selection with a small, monitored resource budget.

This is a development launcher, not a runtime dependency or resource reservation.
Limits are sampled safeguards; the hosting infrastructure owns hard enforcement.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

GIB = 1024**3
RSS_PER_WORKER = 2 * GIB
NATIVE_POOLS = (
    "OPENMM_CPU_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMBA_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
    "POLARS_MAX_THREADS",
    "RAYON_NUM_THREADS",
)


def host_reserve(total, reserve_gib):
    return max(GIB, math.ceil(total * 0.2), math.ceil(reserve_gib * GIB))


def worker_budget(requested, cpu_count, available, total, reserve_gib=0):
    """Keep one exposed CPU and at least 20% physical RAM available when possible."""
    reserve = host_reserve(total, reserve_gib)
    maximum = min(requested, max(1, cpu_count - 1))
    for workers in range(maximum, 0, -1):
        memory_limit = workers * RSS_PER_WORKER
        if available >= reserve + memory_limit:
            return workers, memory_limit, reserve
    raise ValueError("Insufficient available RAM for one worker plus the host reserve")


def preflight_budget(
    requested, cpu_count, reserve_gib, wait_seconds, stop_file, report
):
    """Observe capacity before refusal; wait briefly before the first launch only."""
    started = time.monotonic()
    samples = []
    report.update(
        preflight_wait_limit_s=wait_seconds,
        preflight_memory_samples=samples,
    )
    while True:
        elapsed = time.monotonic() - started
        report["preflight_wait_elapsed_s"] = round(elapsed, 3)
        if stop_file.exists():
            raise ValueError("An explicit owned stop request exists during preflight")
        memory = psutil.virtual_memory()
        reserve = host_reserve(memory.total, reserve_gib)
        minimum = reserve + RSS_PER_WORKER
        report.update(
            host_total_bytes=memory.total,
            host_available_before_bytes=memory.available,
            host_reserve_bytes=reserve,
            minimum_available_for_one_worker_bytes=minimum,
        )
        samples.append(
            {
                "elapsed_s": round(elapsed, 3),
                "available_bytes": memory.available,
                "total_bytes": memory.total,
            }
        )
        try:
            workers, memory_limit, reserve = worker_budget(
                requested, cpu_count, memory.available, memory.total, reserve_gib
            )
            return workers, memory_limit, reserve, memory
        except ValueError:
            # A physically impossible budget cannot improve by waiting.
            if memory.total < minimum or elapsed >= wait_seconds:
                raise
            time.sleep(min(5, wait_seconds - elapsed))


def child_environment(environment, scratch):
    """Do not leak parallel pytest flags into nested copied receiving processes."""
    env = dict(environment)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTHONPATH", None)
    env.update({name: "1" for name in NATIVE_POOLS})
    env.update(
        TMPDIR=str(scratch),
        TMP=str(scratch),
        TEMP=str(scratch),
        PYTHONIOENCODING="utf-8",
    )
    return env


def pytest_command(command, workers, scratch):
    if len(command) < 3 or command[1:3] != ["-m", "pytest"]:
        raise ValueError(
            "Expected -- python -m pytest followed by the original arguments"
        )
    options = command[3:]
    reserved = (
        "--numprocesses",
        "--dist",
        "--tx",
        "--basetemp",
        "--max-worker-restart",
    )
    if any(arg.startswith(reserved) or arg.startswith("-n") for arg in options):
        raise ValueError(
            "The launcher owns worker, scheduler and base-temporary options"
        )
    return [
        sys.executable,
        "-m",
        "pytest",
        *options,
        "-n",
        str(workers),
        "--dist=loadfile",
        "--max-worker-restart=0",
        f"--basetemp={scratch / 'pytest'}",
    ]


def scratch_bytes(directory):
    """Count only owned regular files, without following links to caller data."""
    total = 0
    for parent, _, files in os.walk(directory, followlinks=False):
        for name in files:
            try:
                entry = (Path(parent) / name).lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISREG(entry.st_mode):
                total += entry.st_size
    return total


def active_tracked(tracked):
    """Forget finished processes before their PID can refer to somebody else's work."""
    for key, process in list(tracked.items()):
        try:
            if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                yield process
                continue
        except psutil.NoSuchProcess:
            pass
        tracked.pop(key, None)


def sample_tree(tracked):
    """Include the launcher, workers, nested readers and observed surviving children."""
    for child in psutil.Process().children(recursive=True):
        try:
            tracked[(child.pid, child.create_time())] = child
        except psutil.NoSuchProcess:
            continue
    rss = 0
    swap = 0 if sys.platform.startswith("linux") else None
    for process in active_tracked(tracked):
        try:
            rss += process.memory_info().rss
            if swap is not None:
                status = Path(f"/proc/{process.pid}/status").read_text()
                swap += next(
                    (
                        int(line.split()[1]) * 1024
                        for line in status.splitlines()
                        if line.startswith("VmSwap:")
                    ),
                    0,
                )
        except (psutil.NoSuchProcess, FileNotFoundError, ProcessLookupError):
            continue
    return rss, swap


def stop_owned(process, tracked):
    """Terminate only this launcher's observed descendants, retaining PID identity."""
    children = [
        p for p in active_tracked(tracked) if p.pid not in (os.getpid(), process.pid)
    ]
    for child in children:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            pass
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    _, alive = psutil.wait_procs(children, timeout=2)
    for child in alive:
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass


def run(args, report):
    if os.getenv("SLURM_JOB_ID"):
        raise ValueError("This hosted-CI profile does not interpret Slurm allocations")
    stop_file = Path(str(args.report) + ".stop")
    report["stop_request_path"] = str(stop_file)
    if stop_file.exists():
        raise ValueError("An explicit owned stop request exists before launch")
    current = psutil.Process()
    cpus = (
        current.cpu_affinity()
        if hasattr(current, "cpu_affinity")
        else list(range(os.cpu_count() or 1))
    )
    report.update(
        cpu_slots_observed=len(cpus),
        physical_cores_observed=psutil.cpu_count(logical=False),
        requested_workers=args.workers,
    )
    report["host_cpu_percent_before"] = psutil.cpu_percent(interval=0.1)
    report["host_swap_before"] = psutil.swap_memory()._asdict()
    requested = 1 if report["host_cpu_percent_before"] >= 85 else args.workers
    workers, memory_limit, reserve, memory = preflight_budget(
        requested,
        len(cpus),
        args.reserve_gib,
        args.preflight_wait_seconds,
        stop_file,
        report,
    )
    parent = Path(
        args.scratch_parent or os.getenv("RUNNER_TEMP", tempfile.gettempdir())
    )
    scratch_limit = math.ceil(args.scratch_gib * GIB)
    disk_floor = 2 * GIB
    disk_free = shutil.disk_usage(parent).free
    report.update(
        workers=workers,
        memory_limit_bytes=memory_limit,
        host_reserve_bytes=reserve,
        scratch_limit_bytes=scratch_limit,
        disk_free_floor_bytes=disk_floor,
        scratch_filesystem=str(parent.resolve()),
        disk_free_before_bytes=disk_free,
    )
    if disk_free < disk_floor + scratch_limit:
        raise ValueError(
            "Insufficient scratch filesystem space plus the 2 GiB host margin"
        )
    if args.preflight_only:
        report.update(
            state="PREFLIGHT_READY",
            scope="Capacity observed only; no pytest, resource reservation or test qualification",
        )
        return 0
    scratch = Path(tempfile.mkdtemp(prefix="sabueso-ci-pytest-", dir=parent)).resolve()
    report.update(
        scratch=str(scratch),
        scratch_retained=True,
        scratch_scope="Owned pytest/TMP tree; free-space checks also cover the working filesystem",
    )
    command = pytest_command(args.command, workers, scratch)
    report["command"] = command
    report["native_pools"] = {name: "1" for name in NATIVE_POOLS}
    report["affinity"] = "worker/native-pool limits; affinity unavailable"
    if hasattr(current, "cpu_affinity"):
        current.cpu_affinity(cpus[:workers])
        report["affinity"] = cpus[:workers]
    if os.name == "posix":
        os.nice(10)
    elif sys.platform == "win32":
        current.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    report["state"] = "RUNNING"
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("SABUESO_CI_RESOURCE_START " + json.dumps(report), flush=True)
    tracked = {(current.pid, current.create_time()): current}
    process = subprocess.Popen(command, env=child_environment(os.environ, scratch))
    reason = None
    started = last_log = last_scratch = time.monotonic()
    exited_at = None
    peak_rss = peak_scratch = 0
    peak_swap = 0 if sys.platform.startswith("linux") else None
    minimum_available = memory.available
    try:
        while True:
            rss, swap = sample_tree(tracked)
            available = psutil.virtual_memory().available
            peak_rss = max(peak_rss, rss)
            minimum_available = min(minimum_available, available)
            if swap is not None:
                peak_swap = max(peak_swap, swap)
            now = time.monotonic()
            if now - last_scratch >= 2 or process.poll() is not None:
                peak_scratch = max(peak_scratch, scratch_bytes(scratch))
                last_scratch = now
            if stop_file.exists():
                reason = "owned_stop_request"
            elif rss > memory_limit:
                reason = "owned_memory_limit"
            elif available < reserve:
                reason = "host_memory_reserve"
            elif swap:
                reason = "owned_swap_detected"
            elif peak_scratch > scratch_limit:
                reason = "owned_scratch_limit"
            elif (
                min(shutil.disk_usage(scratch).free, shutil.disk_usage(Path.cwd()).free)
                < disk_floor
            ):
                reason = "host_disk_reserve"
            elif now - started > args.seconds:
                reason = "elapsed_limit"
            if not reason and process.poll() is not None:
                surviving = [
                    child
                    for child in active_tracked(tracked)
                    if child.pid not in (os.getpid(), process.pid)
                ]
                if not surviving:
                    break
                exited_at = now if exited_at is None else exited_at
                if now - exited_at >= 2:
                    reason = "owned_children_survived"
            if reason:
                break
            if now - last_log >= 30:
                print(
                    f"CI_RESOURCE elapsed={now - started:.0f}s workers={workers} "
                    f"rss_mib={rss / 1024**2:.1f} available_gib={available / GIB:.1f} "
                    f"scratch_mib={peak_scratch / 1024**2:.1f}",
                    flush=True,
                )
                last_log = now
            time.sleep(0.25)
    except KeyboardInterrupt:
        reason = "interrupted"
    except (OSError, psutil.Error) as error:
        reason = "monitor_error: " + str(error)
    finally:
        if process.poll() is None or reason:
            stop_owned(process, tracked)
    code = process.wait()
    report.update(
        state="STOPPED" if reason else "PASS" if code == 0 else "FAILED",
        stop_reason=reason,
        pytest_exit_code=code,
        elapsed_s=round(time.monotonic() - started, 3),
        peak_owned_rss_bytes=peak_rss,
        peak_owned_swap_bytes=peak_swap,
        peak_owned_scratch_bytes=peak_scratch,
        minimum_host_available_bytes=minimum_available,
        sample_interval_s=0.25,
        scratch_retained=True,
        host_swap_after=psutil.swap_memory()._asdict(),
    )
    if not reason and code == 0:
        shutil.rmtree(scratch)
        report["scratch_retained"] = False
    return 70 if reason else code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=3)
    parser.add_argument("--reserve-gib", type=float, default=0)
    parser.add_argument("--preflight-wait-seconds", type=float, default=30)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Observe the same CPU/RAM/disk budget without creating scratch or starting pytest",
    )
    parser.add_argument("--scratch-gib", type=float, default=6)
    parser.add_argument("--scratch-parent")
    parser.add_argument("--seconds", type=float, default=19800)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    args.command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if args.preflight_only and args.command:
        parser.error("Preflight-only mode cannot accept a command")
    if not all(math.isfinite(v) and v > 0 for v in (args.scratch_gib, args.seconds)):
        parser.error("Scratch and elapsed limits must be finite and positive")
    if not math.isfinite(args.reserve_gib) or args.reserve_gib < 0:
        parser.error("The optional host reserve must be finite and nonnegative")
    if (
        not math.isfinite(args.preflight_wait_seconds)
        or not 0 <= args.preflight_wait_seconds <= 60
    ):
        parser.error(
            "The preflight wait must be finite and between zero and 60 seconds"
        )
    # Refuse caller output before starting any process or creating owned scratch.
    with args.report.open("x", encoding="utf-8"):
        pass
    report = {
        "format": "sabueso.ci_resource_report@1",
        "state": "PREFLIGHT",
        "preflight_only": args.preflight_only,
        "source_sha": os.getenv("GITHUB_SHA"),
        "python": sys.version,
        "platform": sys.platform,
        "cwd": str(Path.cwd()),
        "owner": "uibcdf/sabueso#112/#148",
        "review_trigger": "CI recovery or before candidate qualification",
        "tools": {
            name: importlib.metadata.version(name)
            for name in ("pytest", "pytest-xdist", "pytest-receptor", "psutil")
        },
        "limits": "Sampled safeguards, not infrastructure-enforced limits or resource reservations",
    }

    def interrupted(*_):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, interrupted)
    try:
        code = run(args, report)
    except KeyboardInterrupt:
        if report["state"] != "PREFLIGHT":
            raise
        report.update(
            state="REFUSED", reason="Preflight interrupted before pytest launch"
        )
        code = 130
    except (ValueError, OSError, psutil.Error) as error:
        report.update(state="REFUSED", reason=str(error))
        code = 71
    finally:
        signal.signal(signal.SIGTERM, previous)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print("SABUESO_CI_RESOURCE_JSON " + json.dumps(report), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
