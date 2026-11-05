"""Reproduce the full public titin save under an owned Linux resource guard.

This developer diagnostic needs existing psutil, never changes SDK defaults and
never kills unrelated processes. Exit2 records a resource stop; it is not a
passing save. The complete public source is preserved in temp_data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[2]
WORKER = r"""
import functools,hashlib,json,socket,sys,time
from pathlib import Path
import psutil
def forbidden(*a,**k):raise AssertionError('No source request')
socket.socket.connect=forbidden;socket.create_connection=forbidden
import sabueso
from sabueso.core.aggregator import build_card_from_mapping
from sabueso.mappings.uniprot import map_protein
import sabueso.core.card_exploration_storage as storage
root=Path(sys.argv[1]);output=Path(sys.argv[2]);start=time.monotonic()
def stage(name,**extra):
 print(json.dumps({'step':name,'elapsed_s':round(time.monotonic()-start,4),'rss_bytes':psutil.Process().memory_info().rss,**extra}),flush=True)
raw=(root/'temp_data/alphafold_archive/uniprot/Q8WZ42.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='28cb420c5f120679947abde3186939a33e07ea232ae4dbc1300268d871c14dec'
entry=json.loads(raw);stage('map full native reference',sdk=sabueso.__version__,features=len(entry['features']))
mapping=map_protein(entry,retrieved_at='2026-11-05')
stage('build full Card',fields=len(mapping['fields']),assertions=len(mapping['source_assertions']),relationships=len(mapping['relationships']))
card=build_card_from_mapping(mapping,meta={'entity_type':'protein'},card_id='sabueso:protein:uniprot:Q8WZ42',entity_subjects={'uniprot:Q8WZ42'})
before=card.to_dict();stage('capture full Card')
explorer=card.explore();sequence=explorer.view('sequence')
length=next(item for item in sequence.items() if item.label=='Sequence length')
frame=explorer.access.read(length.payload_location).page(limit=8,max_bytes=4096)
assert next(row for row in frame['items'] if row['key']=='value')['value']==34350
stage('interactive sequence ready',items=len(sequence.items()),frame_bytes=len(json.dumps(frame).encode()))
for name in ('_prepare','_seal','_restore'):
 original=getattr(storage,name)
 def wrapper(*a,_original=original,_name=name,**k):
  stage('enter '+_name);result=_original(*a,**k);stage('leave '+_name);return result
 setattr(storage,name,wrapper)
sequence.save(output/'full-sequence.json.gz',compression='gzip')
assert card.to_dict()==before
stage('full save completed')
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--rss-limit-mib", type=int, default=512)
    parser.add_argument("--seconds", type=int, default=60)
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error("This owned process-group and /proc guard is Linux-only.")
    if args.rss_limit_mib <= 0 or args.seconds <= 0:
        parser.error("Resource ceilings must be positive.")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    limits = {
        "owned_rss_bytes": args.rss_limit_mib * 1024**2,
        "host_available_bytes": 4 * 1024**3,
        "owned_swap_bytes": 0,
        "elapsed_s": args.seconds,
        "owned_scratch_bytes": 128 * 1024**2,
    }
    if psutil.virtual_memory().available < limits["host_available_bytes"]:
        parser.error(
            "Host available RAM is below the declared4GiB floor; no worker started."
        )
    report = {
        "rule": "public_sequence_save_workload@1",
        "owner": "#167/#148/#112",
        "review_trigger": "save preparation correction / before0.15.0 workload acceptance",
        "source_head": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "sdk": metadata.version("sabueso"),
        "runtime_storage_sha256": hashlib.sha256(
            (ROOT / "sabueso/core/card_exploration_storage.py").read_bytes()
        ).hexdigest(),
        "input_sha256": "28cb420c5f120679947abde3186939a33e07ea232ae4dbc1300268d871c14dec",
        "scope": "Full original public UniProt Card, sequence pane and compact length page, followed by same-session gzip save. File-byte defaults unchanged; no acquisition or tracer.",
        "limits": limits,
    }
    start = time.monotonic()
    peak = swap_peak = scratch_peak = 0
    available_min = psutil.virtual_memory().available
    reason = None
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    with (output / "worker.log").open("w") as log:
        child = subprocess.Popen(
            [sys.executable, "-c", WORKER, str(ROOT), str(output)],
            cwd=ROOT,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            while child.poll() is None:
                try:
                    parent = psutil.Process(child.pid)
                    processes = [parent, *parent.children(recursive=True)]
                except psutil.NoSuchProcess:
                    processes = []
                rss = swap = 0
                for process in processes:
                    try:
                        rss += process.memory_info().rss
                        status = Path(f"/proc/{process.pid}/status").read_text()
                        swap += next(
                            (
                                int(line.split()[1]) * 1024
                                for line in status.splitlines()
                                if line.startswith("VmSwap:")
                            ),
                            0,
                        )
                    except (
                        psutil.NoSuchProcess,
                        FileNotFoundError,
                        ProcessLookupError,
                    ):
                        pass
                peak, swap_peak = max(peak, rss), max(swap_peak, swap)
                available = psutil.virtual_memory().available
                available_min = min(available_min, available)
                size = sum(
                    p.stat().st_size
                    for p in output.rglob("*")
                    if p.is_file() and not p.is_symlink()
                )
                scratch_peak = max(scratch_peak, size)
                reason = (
                    "owned RSS ceiling"
                    if rss > limits["owned_rss_bytes"]
                    else "owned swap ceiling"
                    if swap
                    else "host available RAM floor"
                    if available < limits["host_available_bytes"]
                    else "owned scratch ceiling"
                    if size > limits["owned_scratch_bytes"]
                    else "elapsed ceiling"
                    if time.monotonic() - start > limits["elapsed_s"]
                    else None
                )
                if reason:
                    break
                time.sleep(0.05)
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
            code = child.wait()
    report.update(
        exit_code=code,
        stop_reason=reason,
        elapsed_s=round(time.monotonic() - start, 3),
        peak_owned_rss_bytes=peak,
        peak_owned_swap_bytes=swap_peak,
        minimum_host_available_bytes=available_min,
        peak_owned_scratch_bytes=scratch_peak,
        outcome="resource_stop"
        if reason
        else "completed"
        if code == 0
        else "worker_error",
    )
    (output / "receiving.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 2 if reason else code


if __name__ == "__main__":
    raise SystemExit(main())
