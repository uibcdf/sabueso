"""Synthetic scale controls using public providers, never new molecular knowledge."""

import asyncio
import time


class BufferObservation:
    """Count the probe channel's public outbound buffers without changing them.

    This is an API-boundary observation, not socket/GPU byte accounting. The
    provider remains responsible for validation, routing and transfer lifetime.
    """

    def __init__(self, channel):
        self.channel = channel
        self.original_send = channel.send
        self.records = []
        channel.send = self.send

    def send(self, message, buffers=None, **kwargs):
        result = self.original_send(message, buffers, **kwargs)
        if buffers:
            arrays = []
            for descriptor in message.get("structural_arrays", []):
                byte_count = memoryview(buffers[descriptor["buffer_index"]]).nbytes
                if byte_count != descriptor["byte_length"]:
                    raise ValueError(
                        "Observed buffer length differs from its provider descriptor"
                    )
                arrays.append(
                    {
                        "kind": descriptor["kind"],
                        "dtype": descriptor["dtype"],
                        "shape": list(descriptor["shape"]),
                        "unit": descriptor["units"],
                        "layout": descriptor["layout"],
                        "buffer_bytes": byte_count,
                    }
                )
            self.records.append(
                {
                    "operation": message.get("op"),
                    "arrays": arrays,
                    "buffer_bytes": sum(
                        memoryview(buffer).nbytes for buffer in buffers
                    ),
                }
            )
        return result

    def snapshot(self, first_record):
        records = self.records[first_record:]
        return {
            "format": "sabueso.outbound_buffer_observation@2",
            "scope": "Public send API; bytes can be resent and are not GPU allocations",
            "buffer_bytes": sum(row["buffer_bytes"] for row in records),
            "coordinate_buffer_bytes": sum(
                array["buffer_bytes"]
                for row in records
                for array in row["arrays"]
                if array["kind"] == "coordinates"
            ),
            "records": records,
        }

    def close(self):
        self.channel.send = self.original_send


def _prepare(path, copies, structures):
    import molsysmt as msm

    original = msm.convert(str(path), to_form="molsysmt.MolSys")
    system = (
        original
        if copies == 1
        else msm.merge([original] * copies, to_form="molsysmt.MolSys")
    )
    count = 1
    while count < structures:
        system = msm.append_structures(system, system, in_place=False)
        count *= 2
    return system


async def run_scale_case(probe, copies, structures):
    import molsysmt as msm

    if type(copies) is not int or copies not in {1, 4, 16}:
        raise ValueError("Synthetic atom copies must be 1, 4 or 16")
    if type(structures) is not int or structures not in {1, 8, 32}:
        raise ValueError("Synthetic structures must be 1, 8 or 32")
    start = time.perf_counter()
    system = await asyncio.to_thread(
        _prepare, probe.inputs / "1tcd.bcif.gz", copies, structures
    )
    preparation = time.perf_counter() - start
    atoms = int(msm.get(system, n_atoms=True))
    n_structures = int(msm.get(system, n_structures=True))
    if (
        atoms != len(probe.correspondence["atoms"]) * copies
        or n_structures != structures
    ):
        raise ValueError(
            "Synthetic cohort dimensions differ from the declared input repetition"
        )
    first_record = len(probe.buffers.records)
    start = time.perf_counter()
    probe.view.load(
        system,
        mode="replace",
        label=f"Synthetic {copies} independent copies; {structures} identical structures",
    )
    load = time.perf_counter() - start
    start = time.perf_counter()
    await probe.view.movie.capture_baseline_async(1000.0, timeout=30.0)
    capture = time.perf_counter() - start
    if structures > 1:
        probe.view.movie.add_track(
            {
                "tag": "synthetic-structure-indices",
                "target": {"domain": "structure"},
                "property": "index",
                "keys": [
                    {"time_ms": 500, "value": structures - 1},
                    {"time_ms": 1000, "value": 0},
                ],
            }
        )
    draws = []
    for moment, expected in ((0.0, 0), (500.0, structures - 1), (1000.0, 0)):
        start = time.perf_counter()
        sample = await probe.view.movie.seek_async(moment, timeout=30.0)
        elapsed = time.perf_counter() - start
        if sample["structure_index"] != expected or probe.view.player.index != expected:
            raise ValueError("Acknowledged sample has a different structure index")
        draws.append(
            {
                "sample_time": {"value": moment, "unit": "millisecond"},
                "structure_index": expected,
                "elapsed": {"value": elapsed, "unit": "second"},
                "basis": "movie.seek_async primary-canvas completed draw",
            }
        )
    if probe.knowledge.card.to_dict() != probe.knowledge.before:
        raise ValueError("Scale control changed original Card knowledge")
    return {
        "kind": "synthetic_repetition_control",
        "atom_copies": copies,
        "n_atoms": atoms,
        "n_structures": structures,
        "meaning": "Overlapping independent copies and identical conformations; no physical assembly or dynamics claim",
        "card_mapping_admitted": probe.binding_valid(),
        "preparation": {"value": preparation, "unit": "second"},
        "load_call": {"value": load, "unit": "second"},
        "live_baseline_capture": {"value": capture, "unit": "second"},
        "draws": draws,
        "outbound_buffers": probe.buffers.snapshot(first_record),
    }
