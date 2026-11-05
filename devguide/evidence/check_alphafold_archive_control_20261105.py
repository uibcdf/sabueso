"""Receive the original public ModelCIF fragment and canonical reference offline.

This developer control uses existing Biopython and Gemmi independently. They are
not new Sabueso runtime dependencies. No coordinate calculation, API record,
Card enrichment or production archive importer is introduced.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import io
import json
import socket
import tarfile
from pathlib import Path

RULE = "alphafold_archive_fragment_control@1"
ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / "temp_data/alphafold_archive"
MODEL = "AF-Q8WZ42-F2-model_v6.cif.gz"
MODEL_SHA256 = "74da31b7a0153ef2c90dc8f60fe07edaa83ba50049bf06e6f4eb113ece1963ef"
DECODED_SHA256 = "206ffc9821eaa76a33f7f3afe1b42f5ffd1eeae5b411c299cf8ae910f9964036"
REFERENCE_SHA256 = "28cb420c5f120679947abde3186939a33e07ea232ae4dbc1300268d871c14dec"


def forbidden(*args, **kwargs):
    raise AssertionError("No network or unrequested molecular calculation")


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def receive(inputs=INPUTS):
    """A finite scientific control, not a general ModelCIF ingestion contract."""
    from Bio.PDB.MMCIF2Dict import MMCIF2Dict
    from Bio.SeqUtils.CheckSum import crc64
    from gemmi import cif

    raw = (inputs / MODEL).read_bytes()
    assert len(raw) == 269404 and checksum(raw) == MODEL_SHA256
    decoded = gzip.decompress(raw)
    assert len(decoded) == 1298513 and checksum(decoded) == DECODED_SHA256
    reference_raw = (inputs / "uniprot/Q8WZ42.json").read_bytes()
    assert checksum(reference_raw) == REFERENCE_SHA256
    reference = json.loads(reference_raw)
    projection = json.loads((inputs / "modelcif_metadata.json").read_text("utf-8"))
    capture = json.loads((inputs / "capture.json").read_text("utf-8"))
    assert projection["format"] == "sabueso.modelcif_literal_metadata@1"
    assert projection["input_sha256"] == DECODED_SHA256
    first = MMCIF2Dict(io.StringIO(decoded.decode("utf-8")))
    block = cif.read_string(decoded.decode("utf-8")).sole_block()

    def original_value(value):
        # as_string alone maps CIF unknown/inapplicable markers to an empty
        # string. Keep the literal markers, which have different meanings.
        return value if value in ("?", ".") else cif.as_string(value)

    for key, original in projection["native_tags"].items():
        assert first[key] == original, key
        assert [original_value(v) for v in block.find_values(key)] == original, key

    def one(key):
        values = first[key]
        assert len(values) == 1, f"No selection among alternative rows: {key}"
        return values[0]

    assert one("_database_2.database_id") == "AlphaFoldDB"
    assert one("_database_2.database_code") == "AF-Q8WZ42-F2"
    assert one("_ma_target_ref_db_details.db_name") == "UNP"
    assert (
        one("_ma_target_ref_db_details.db_accession")
        == reference["primaryAccession"]
        == "Q8WZ42"
    )
    assert (
        one("_ma_target_ref_db_details.target_entity_id")
        == one("_entity_poly.entity_id")
        == "1"
    )
    begin = int(one("_ma_target_ref_db_details.seq_db_align_begin"))
    end = int(one("_ma_target_ref_db_details.seq_db_align_end"))
    assert (begin, end) == (201, 1600)
    assert [
        one("_struct_ref_seq.db_align_beg"),
        one("_struct_ref_seq.db_align_end"),
    ] == ["201", "1600"]
    assert [
        one("_struct_ref_seq.seq_align_beg"),
        one("_struct_ref_seq.seq_align_end"),
    ] == ["1", "1400"]
    assert one("_ma_target_ref_db_details.seq_db_isoform") == "?"
    fragment = "".join(one("_entity_poly.pdbx_seq_one_letter_code_can").split())
    assert fragment == "".join(one("_entity_poly.pdbx_seq_one_letter_code").split())
    assert fragment == "".join(one("_struct_ref.pdbx_seq_one_letter_code").split())
    sequence = reference["sequence"]["value"]
    assert len(sequence) == reference["sequence"]["length"] == 34350
    assert len(fragment) == end - begin + 1 == 1400
    assert fragment == sequence[begin - 1 : end]
    stated_crc64 = one("_ma_target_ref_db_details.seq_db_sequence_checksum")
    assert (
        stated_crc64
        == reference["sequence"]["crc64"]
        == crc64(sequence).removeprefix("CRC-")
    )
    assert (
        one("_ma_target_ref_db_details.seq_db_sequence_version_date")
        == reference["entryAudit"]["lastSequenceUpdateDate"]
        == "2012-04-18"
    )
    assert (
        hashlib.md5(sequence.encode(), usedforsecurity=False).hexdigest()
        == reference["sequence"]["md5"].lower()
    )
    header = (inputs / "AF-Q8WZ42-F2-model_v6.tar-header.bin").read_bytes()
    member = tarfile.TarInfo.frombuf(header, encoding="utf-8", errors="strict")
    assert member.isfile() and member.name == MODEL and member.size == len(raw)
    assert checksum(header) == capture["member_header"]["header_sha256"]
    assert capture["member_header"]["offset"] == 3628310528
    return {
        "rule": RULE,
        "owner": "#148/#173/#112",
        "review_trigger": "archive-native admission / scientific and researcher receiving",
        "parsers": {
            name: importlib.metadata.version(name) for name in ("biopython", "gemmi")
        },
        "model": "AF-Q8WZ42-F2",
        "identity_basis": "Original ModelCIF explicitly declares UNP/Q8WZ42; exact source accession, full-reference CRC64 and sequence-version date agree with the retained UniProt record. Sequence equality corroborates an interval, never merges identities.",
        "reference_interval": [begin, end],
        "model_sequence_interval": [1, len(fragment)],
        "reference_length": len(sequence),
        "fragment_length": len(fragment),
        "exact_interval_sequence_match": True,
        "source_reference_crc64": stated_crc64,
        "derived_fragment_crc64": crc64(fragment).removeprefix("CRC-"),
        "derived_fragment_md5": hashlib.md5(
            fragment.encode(), usedforsecurity=False
        ).hexdigest(),
        "derived_checksums_are_source_assertions": False,
        "isoform_membership": "not_established; source literal ? retained",
        "api_record_or_source_md5_generated": False,
        "coordinate_correspondence": "not_qualified; no coordinate calculation",
        "new_provider_requests": 0,
        "card_archive_intake": "pending a separate named native-input contract; this control does not qualify API context @1/@2 or a Card fragment journey",
        "independent_scientist_researcher_acceptance": "pending",
        "b2_review": "maintainer-owned and deferred",
        "release_consolidation": "paused",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    socket.socket.connect = forbidden
    socket.create_connection = forbidden
    report = receive()
    (args.output / "receiving.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(
        "PASS original archive/header integrity, independent metadata readers, CRC64 and exact reference interval; production intake remains pending."
    )


if __name__ == "__main__":
    main()
