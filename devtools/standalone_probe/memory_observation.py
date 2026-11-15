"""Opt-in owned-process memory observations for the bounded desktop receiver."""

import time
from pathlib import Path

import psutil


def process_role(arguments):
    """Label reported argv roles; forked workers can inherit zygote arguments."""
    if "sabueso.explorer._service" in arguments:
        return "knowledge_and_molecular_service"
    if "sabueso.explorer" in arguments:
        return "qt_application"
    if arguments and Path(arguments[0]).name == "QtWebEngineProcess":
        kind = next(
            (arg.split("=", 1)[1] for arg in arguments if arg.startswith("--type=")),
            "unknown",
        )
        return {
            "renderer": "webengine_renderer",
            "gpu-process": "webengine_gpu",
            "utility": "webengine_utility",
            "zygote": "webengine_reported_zygote",
        }.get(kind, "webengine_other")
    if arguments and Path(arguments[0]).name == "Xvfb":
        return "display"
    if any(Path(arg).name == "molecular_explorer_journey.mjs" for arg in arguments):
        return "receiver"
    return "other_owned"


def observe_process_memory(tracked):
    """Sample known PID/generation pairs, retaining unavailable fields explicitly.

    The process tree is owned by the caller. PSS/USS are OS observations, not
    provider heap attribution, GPU allocations or atomic whole-tree accounting.
    """
    rows = []
    started = time.time()
    for (pid, generation), process in list(tracked.items()):
        row = {
            "pid": pid,
            "created_at_s": generation,
            "role": "unavailable",
            "rss_bytes": None,
            "uss_bytes": None,
            "pss_bytes": None,
            "unavailable": [],
        }
        try:
            if (
                process.create_time() != generation
                or not process.is_running()
                or process.status() == psutil.STATUS_ZOMBIE
            ):
                continue
            try:
                row["role"] = process_role(process.cmdline())
            except psutil.AccessDenied:
                row["unavailable"].append("role:access_denied")
            row["rss_bytes"] = process.memory_info().rss
            try:
                memory = process.memory_full_info()
                for name in ("rss", "uss", "pss"):
                    row[name + "_bytes"] = getattr(memory, name, None)
                    if row[name + "_bytes"] is None:
                        row["unavailable"].append(name + ":not_provided")
            except (psutil.AccessDenied, NotImplementedError) as error:
                row["unavailable"].append("full_memory:" + type(error).__name__)
        except (psutil.NoSuchProcess, ProcessLookupError, FileNotFoundError):
            continue
        except psutil.AccessDenied:
            row["unavailable"].append("memory:access_denied")
        rows.append(row)
    totals = {
        field: sum(row[field] for row in rows)
        if rows and all(row[field] is not None for row in rows)
        else None
        for field in ("rss_bytes", "uss_bytes", "pss_bytes")
    }
    return {
        "format": "sabueso.owned_process_memory@1",
        "start_wall_s": started,
        "end_wall_s": time.time(),
        "processes": rows,
        "totals": totals,
        "scope": "Non-atomic OS samples; roles use reported argv (forked workers can inherit zygote arguments), combine Knowledge/Viewer service and all renderer frames; no provider heap or GPU attribution",
    }
