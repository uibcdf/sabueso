"""Observe an owned probe's NVIDIA contexts; not a GPU reservation or energy meter.

Run inside run_bounded.py. Only this command's descendants may be stopped.
Whole-device temperature/power includes other activity and remains unattributed.
"""

import argparse
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--framebuffer-stop-mb", type=int, choices=(1, 2048), default=2048)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command[:1] == ["--"] else args.command
if not command or args.output.exists():
    raise SystemExit("A command and fresh observation path are required")
samples, errors = [], []
tracked = {}
stop_reason = None


def signal_stop(signum, unused_frame):
    global stop_reason
    stop_reason = f"observer received signal {signum}"


signal.signal(signal.SIGTERM, signal_stop)
signal.signal(signal.SIGINT, signal_stop)


def number(value):
    return None if value in {"N/A", "[N/A]", "[Not Supported]"} else float(value)


process = subprocess.Popen(command)
try:
    while process.poll() is None:
        try:
            root = psutil.Process(process.pid)
            for child in [root, *root.children(recursive=True)]:
                tracked[child.pid] = child.create_time()
        except psutil.NoSuchProcess:
            pass
        sample = {
            "wall_s": time.time(),
            "devices": [],
            "owned_graphics": [],
            "unattributed_context_gpu_indices": [],
        }
        try:
            state = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=True,
            )
            for line in state.stdout.splitlines():
                fields = [x.strip() for x in line.split(",")]
                sample["devices"].append(
                    dict(
                        zip(
                            (
                                "index",
                                "total_memory_mib",
                                "used_memory_mib",
                                "utilization_percent",
                                "temperature_celsius",
                                "power_watt",
                            ),
                            [int(fields[0]), *map(number, fields[1:])],
                            strict=True,
                        )
                    )
                )
            contexts = subprocess.run(
                ["nvidia-smi", "pmon", "-c", "1", "-s", "um"],
                capture_output=True,
                text=True,
                timeout=3,
                check=True,
            )
            # Include actors created during the two device queries. A context
            # outside this refreshed tree remains unattributed, not proved foreign.
            try:
                root = psutil.Process(process.pid)
                for child in [root, *root.children(recursive=True)]:
                    tracked[child.pid] = child.create_time()
            except psutil.NoSuchProcess:
                pass
            for line in contexts.stdout.splitlines():
                fields = line.split()
                if (
                    len(fields) < 11
                    or fields[0].startswith("#")
                    or not fields[1].isdigit()
                ):
                    continue
                gpu, pid = int(fields[0]), int(fields[1])
                is_owned = False
                try:
                    is_owned = (
                        pid in tracked
                        and psutil.Process(pid).create_time() == tracked[pid]
                    )
                except psutil.NoSuchProcess:
                    pass
                if is_owned:
                    sample["owned_graphics"].append(
                        {
                            "gpu_index": gpu,
                            "pid": pid,
                            "type": fields[2],
                            "framebuffer_mb": None
                            if fields[9] == "-"
                            else int(fields[9]),
                        }
                    )
                else:
                    sample["unattributed_context_gpu_indices"].append(gpu)
            owned_per_gpu = {}
            for row in sample["owned_graphics"]:
                if row["framebuffer_mb"] is None:
                    raise ValueError("Owned GPU framebuffer observation is unavailable")
                owned_per_gpu[row["gpu_index"]] = owned_per_gpu.get(
                    row["gpu_index"], 0
                ) + (row["framebuffer_mb"] or 0)
            if any(
                value > args.framebuffer_stop_mb for value in owned_per_gpu.values()
            ):
                stop_reason = f"owned summed GPU framebuffer exceeded {args.framebuffer_stop_mb} MB (pmon-reported) on one device"
            for row in sample["owned_graphics"]:
                device = next(
                    x for x in sample["devices"] if x["index"] == row["gpu_index"]
                )
                if any(
                    device[key] is None
                    for key in (
                        "used_memory_mib",
                        "total_memory_mib",
                        "temperature_celsius",
                    )
                ):
                    raise ValueError("Selected GPU safety observation is unavailable")
                if device["used_memory_mib"] > 0.8 * device["total_memory_mib"]:
                    stop_reason = "selected GPU available-memory floor"
                if (
                    device["temperature_celsius"] is not None
                    and device["temperature_celsius"] > 80
                ):
                    stop_reason = "selected GPU temperature above 80 Celsius"
        except (subprocess.SubprocessError, ValueError, KeyError, OSError) as error:
            errors.append(str(error))
            stop_reason = "GPU observation unavailable"
        samples.append(sample)
        if stop_reason:
            break
        time.sleep(0.5)
finally:
    if process.poll() is None:
        for pid, created in reversed(list(tracked.items())):
            try:
                child = psutil.Process(pid)
                if child.create_time() == created:
                    child.terminate()
            except psutil.NoSuchProcess:
                pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    returncode = process.wait()
    observation = {
        "owner": "uibcdf/sabueso#154",
        "format": "sabueso.owned_gpu_observation@2",
        "scope": "Read-only device samples; pmon framebuffer uses reported MB without byte conversion; context ownership does not identify the WebGL device",
        "limits": {
            "owned_framebuffer_mb_per_gpu": args.framebuffer_stop_mb,
            "selected_gpu_available_fraction": 0.2,
            "selected_gpu_celsius": 80,
        },
        "stop_reason": stop_reason,
        "returncode": returncode,
        "errors": errors,
        "samples": samples,
    }
    args.output.write_text(json.dumps(observation, indent=2) + "\n")
sys.exit(returncode if returncode else int(bool(stop_reason)))
