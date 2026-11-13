"""Task-owned resource observer; this is not a reusable execution platform."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

parser = argparse.ArgumentParser()
parser.add_argument("--output-root", type=Path, required=True)
parser.add_argument("--cpus", type=int, choices=(1, 2, 4, 8), default=2)
parser.add_argument("--rss-gib", type=int, choices=(4, 10), default=4)
parser.add_argument("name")
parser.add_argument("--cwd", default=str(Path.cwd()))
parser.add_argument("--seconds", type=int, default=600)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
BASE = args.output_root.resolve()
BASE.mkdir(parents=True, exist_ok=True)
if os.environ.get("SLURM_JOB_ID"):
    raise SystemExit("This local observer does not interpret Slurm allocations")
command = args.command[1:] if args.command[:1] == ["--"] else args.command
if not command:
    parser.error("A command is required")
log_path, report_path = BASE / f"{args.name}.log", BASE / f"{args.name}-resources.json"
if log_path.exists() or report_path.exists():
    raise SystemExit("Refusing to overwrite prior observations")
limit, reserve = args.rss_gib * 1024**3, 16 * 1024**3
if psutil.virtual_memory().available < limit + reserve:
    raise SystemExit("Deferred: insufficient shared-memory headroom")
if psutil.disk_usage("/tmp").free < 4 * 1024**3:
    raise SystemExit("Deferred: insufficient temporary disk headroom")
env = os.environ.copy()
for name in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "RAYON_NUM_THREADS",
    "OPENMM_CPU_THREADS",
    "NUMBA_NUM_THREADS",
    "LP_NUM_THREADS",
):
    env[name] = "1"
env["PYTHONDONTWRITEBYTECODE"] = "1"
env["MPLCONFIGDIR"] = str(BASE / "matplotlib")
scratch = BASE / f"{args.name}-scratch"
scratch.mkdir(exist_ok=False)
env["TMPDIR"] = str(scratch)
env["ELECTRON_CACHE"] = str(BASE / "electron-cache")
env["npm_config_cache"] = str(BASE / "npm-cache")
cpus = sorted(os.sched_getaffinity(0))[: args.cpus]
if len(cpus) != args.cpus:
    raise SystemExit("The requested small CPU affinity is unavailable")
command = ["nice", "-n", "10", "taskset", "-c", ",".join(map(str, cpus)), *command]
tracked = {}
cpu_observed = {}
samples = []
peak, minimum, stop_reason = 0, psutil.virtual_memory().available, None
started = last_print = time.monotonic()
stop_requested = None


def request_stop(signum, unused_frame):
    global stop_requested
    stop_requested = f"observer received signal {signum}"


signal.signal(signal.SIGTERM, request_stop)
signal.signal(signal.SIGINT, request_stop)
with log_path.open("x", encoding="utf-8") as log:
    process = subprocess.Popen(
        command, cwd=args.cwd, env=env, stdout=log, stderr=subprocess.STDOUT
    )
    while process.poll() is None:
        try:
            parent = psutil.Process(process.pid)
            for child in [parent, *parent.children(recursive=True)]:
                tracked[(child.pid, child.create_time())] = child
        except psutil.NoSuchProcess:
            pass
        rss, swap = 0, 0
        for key, child in list(tracked.items()):
            try:
                if child.create_time() != key[1] or not child.is_running():
                    continue
                rss += child.memory_info().rss
                cpu = child.cpu_times()
                cpu_observed[key] = cpu.user + cpu.system
                status = Path(f"/proc/{child.pid}/status").read_text()
                swap += next(
                    (
                        int(line.split()[1]) * 1024
                        for line in status.splitlines()
                        if line.startswith("VmSwap:")
                    ),
                    0,
                )
            except (psutil.NoSuchProcess, ProcessLookupError, FileNotFoundError):
                pass
        available = psutil.virtual_memory().available
        peak, minimum = max(peak, rss), min(minimum, available)
        samples.append(
            {
                "wall_s": time.time(),
                "rss_bytes": rss,
                "owned_cpu_s": sum(cpu_observed.values()),
            }
        )
        if stop_requested:
            stop_reason = stop_requested
        elif rss > limit:
            stop_reason = "owned RSS ceiling"
        elif available < reserve:
            stop_reason = "host available RAM floor"
        elif swap:
            stop_reason = "owned swap observed"
        elif time.monotonic() - started > args.seconds:
            stop_reason = "elapsed ceiling"
        elif psutil.disk_usage("/tmp").free < 2 * 1024**3:
            stop_reason = "temporary filesystem free floor"
        if stop_reason:
            break
        if time.monotonic() - last_print >= 25:
            print(
                f"{args.name}: {time.monotonic() - started:.0f}s; owned RSS {rss / 1024**2:.0f} MiB",
                flush=True,
            )
            last_print = time.monotonic()
        time.sleep(0.25)
    if stop_reason:
        for key, child in reversed(list(tracked.items())):
            try:
                if child.create_time() == key[1]:
                    child.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(list(tracked.values()), timeout=5)
        for child in alive:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(alive, timeout=5)
    returncode = process.wait()
survivors = []
remaining = []
for key, child in tracked.items():
    try:
        if (
            child.create_time() == key[1]
            and child.is_running()
            and child.status() != psutil.STATUS_ZOMBIE
        ):
            survivors.append(child.pid)
            child.terminate()
            remaining.append(child)
    except psutil.NoSuchProcess:
        pass
_, alive = psutil.wait_procs(remaining, timeout=5)
for child in alive:
    try:
        child.kill()
    except psutil.NoSuchProcess:
        pass
psutil.wait_procs(alive, timeout=5)
report = {
    "owner": "uibcdf/sabueso#154",
    "command": command,
    "cwd": args.cwd,
    "returncode": returncode,
    "elapsed_s": round(time.monotonic() - started, 3),
    "stop_reason": stop_reason,
    "peak_owned_rss_bytes": peak,
    "minimum_host_available_bytes": minimum,
    "survivors_after_command": survivors,
    "limits": {
        "owned_rss_bytes": limit,
        "host_available_bytes": reserve,
        "cpu_affinity": cpus,
        "native_threads": 1,
    },
    "scope": "Sampled observer, no reservation; exploratory software/native scopes remain distinct",
    "samples": samples,
}
report_path.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "samples"}), flush=True)
if returncode or stop_reason or survivors:
    print(log_path.read_text(encoding="utf-8")[-6000:], flush=True)
sys.exit(returncode if returncode else int(bool(stop_reason or survivors)))
