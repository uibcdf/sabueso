"""Native PDBTM chain topology with unchanged XML and independent numbering axes."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from xml.etree import ElementTree as ET

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

BASE = "https://pdbtm.unitmp.org/api/v1/entry/"
NS = "{https://pdbtm.unitmp.org}"
PDB = re.compile(r"[1-9][a-z0-9]{3}\Z")
COPYRIGHT = (
    "All information, data and files are copyright. PDBTM database is "
    "produced in the Institute of Enzymology, Budapest, Hungary. There "
    "are no restrictions on its use by non-profit institutions as long "
    "as its content is in no way modified and this statement is not "
    "removed from entries. Usage by and for commercial entities requires "
    "a license agreement (send an email to pdbtm at enzim dot hu)."
)


def response_query(identifier):
    if not isinstance(identifier, str) or not PDB.fullmatch(identifier):
        raise ConnectorError(
            "PDBTM requires one exact lowercase four-character PDB ID."
        )
    return {"pdb_id": identifier, "representation": "pdbtm_xml"}


def xml_encoding(text):
    if not isinstance(text, str) or not text:
        raise ConnectorError("PDBTM requires nonempty original XML text.")
    declaration = re.match(r"\ufeff?\s*<\?xml\s+[^?]*\?>", text)
    match = (
        re.search(r"\bencoding\s*=\s*['\"]([^'\"]+)['\"]", declaration[0])
        if declaration
        else None
    )
    encoding = match[1].lower() if match else "utf-8"
    if encoding not in {"utf-8", "iso-8859-1"}:
        raise ConnectorError("Unsupported PDBTM native XML encoding.")
    return encoding


def decode_xml(raw):
    """Use the native declaration; never silently replace undecodable bytes."""
    try:
        head = raw[:256].decode("ascii", errors="ignore")
        text = raw.decode(xml_encoding(head))
        if text.encode(xml_encoding(text)) != raw:
            raise ConnectorError("PDBTM XML bytes cannot be reproduced unchanged.")
        return text
    except (UnicodeError, AttributeError) as error:
        raise ConnectorError(f"Unreadable PDBTM XML: {error}") from error


def native_hash(text):
    try:
        return hashlib.sha256(text.encode(xml_encoding(text))).hexdigest()
    except UnicodeError as error:
        raise ConnectorError(
            "PDBTM text contradicts its encoding declaration."
        ) from error


def parse_topology(text, identifier):
    """Validate all native chains before mapping; do not interpret transforms.

    The original copyright must remain present, under the reviewed conditional
    statement. DTD/entity declarations are unsupported; no external XML resource
    is resolved. Regions retain independent sequence and PDB endpoint literals.
    """
    response_query(identifier)
    xml_encoding(text)
    native_hash(text)
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, flags=re.IGNORECASE):
        raise ConnectorError("PDBTM DTD/entity declarations are unsupported.")
    try:
        root = ET.fromstring(text)
    except (ET.ParseError, ValueError) as error:
        raise ConnectorError(f"Malformed PDBTM XML: {error}") from error
    if root.tag != NS + "pdbtm" or root.get("ID") != identifier or not root.get("TMP"):
        raise ConnectorError(
            "PDBTM namespace, native entry ID or TMP declaration differ."
        )
    copyrights = root.findall(NS + "COPYRIGHT")
    if (
        len(copyrights) != 1
        or len(copyrights[0])
        or " ".join((copyrights[0].text or "").split()) != COPYRIGHT
    ):
        raise ConnectorError("PDBTM copyright/use statement is missing or changed.")
    known = {
        "COPYRIGHT",
        "CREATE_DATE",
        "MODIFICATION",
        "RAWRES",
        "BIOMATRIX",
        "MEMBRANE",
        "CHAIN",
    }
    if any(child.tag not in {NS + name for name in known} for child in root):
        raise ConnectorError("Unsupported PDBTM root representation.")
    chains = []
    for chain in root.findall(NS + "CHAIN"):
        attributes = dict(chain.attrib)
        sequences = chain.findall(NS + "SEQ")
        if (
            set(attributes) != {"CHAINID", "NUM_TM", "TYPE"}
            or not attributes["CHAINID"]
            or not attributes["TYPE"]
            or not re.fullmatch(r"[0-9]+", attributes["NUM_TM"])
            or len(sequences) != 1
            or len(sequences[0])
            or any(child.tag not in {NS + "SEQ", NS + "REGION"} for child in chain)
        ):
            raise ConnectorError("Unsupported PDBTM chain/sequence representation.")
        sequence_text = sequences[0].text
        if (
            not sequence_text
            or not re.fullmatch(r"[A-Z\t\r\n ]+", sequence_text)
            or not sequence_text.strip()
        ):
            raise ConnectorError("Invalid PDBTM source sequence literal.")
        length = len("".join(sequence_text.split()))
        regions = []
        for region in chain.findall(NS + "REGION"):
            values = dict(region.attrib)
            if (
                set(values) != {"seq_beg", "seq_end", "pdb_beg", "pdb_end", "type"}
                or len(region)
                or (region.text or "").strip()
                or not values["type"]
                or not re.fullmatch(r"[0-9]+", values["seq_beg"])
                or not re.fullmatch(r"[0-9]+", values["seq_end"])
                or not 1 <= int(values["seq_beg"]) <= int(values["seq_end"]) <= length
                or any(
                    not re.fullmatch(r"[+-]?[0-9]+[A-Za-z]?", values[name])
                    for name in ("pdb_beg", "pdb_end")
                )
            ):
                raise ConnectorError("Invalid PDBTM native region or sequence bounds.")
            regions.append(values)
        if not regions:
            raise ConnectorError("Unsupported PDBTM chain without native regions.")
        chains.append(
            {
                "chain_attributes": attributes,
                "sequence_text": sequence_text,
                "regions": regions,
            }
        )
    if not chains:
        raise ConnectorError("Unsupported PDBTM entry without native chain topology.")
    return root, chains


def map_topology(envelope):
    """Retain independent chain occurrences and their unchanged source support."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "PDBTM"
        or envelope.get("kind") != "transmembrane_topology"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("PDBTM requires a complete native topology envelope.")
    identifier = envelope["query"].get("pdb_id")
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("Unsupported PDBTM mapping query scope.")
    text = envelope.get("record")
    root, chains = parse_topology(text, identifier)
    checksum = native_hash(text)
    if envelope.get("native_document_sha256", checksum) != checksum:
        raise ConnectorError("PDBTM original document identity differs.")
    assertions = []
    for index, chain in enumerate(chains):
        assertion = make_source_assertion(
            "annotations.transmembrane_topology",
            {
                "pdb_id": identifier,
                "entry_tmp_literal": root.get("TMP"),
                **deepcopy(chain),
            },
            "PDBTM",
            f"{identifier}:sha256:{checksum}:chain-occurrence:{index}",
            envelope.get("retrieved_at"),
            subject_ref=f"pdbtm:structure:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "original_xml": text,
            "native_encoding": xml_encoding(text),
            "native_document_sha256": checksum,
            "copyright_text": root.find(NS + "COPYRIGHT").text,
            "entry_attributes": dict(root.attrib),
            "chain_occurrence": index,
            "received_chain_count": len(chains),
            "received_region_count": sum(len(c["regions"]) for c in chains),
            "query": deepcopy(envelope["query"]),
            "mapping_scope": {
                "identity": "native_PDB_and_chain_literals; independent_occurrences; no_generated_chain_or_protein_merge",
                "sequence": "XML_character_data; original_document_unchanged; no_canonical_or_cross_chain_sequence_identity",
                "regions": "independent_seq_and_PDB_endpoint_literals; no_constant_offset_or_per_residue_correspondence",
                "labels": "source_TMP_NUM_TM_TYPE_and_region_codes; no_orientation_function_or_MOLI_Evidence_inference",
                "transforms": "original_XML_only; units_axes_unqualified; no_structured_quantities_or_transform_execution",
                "revision": "source_history_and_site_release_are_not_current_PDB_or_sequence_revisions",
                "terms": "original_XML_and_copyright_unchanged; conditional_nonprofit_or_commercial_agreement; automatic_use_and_sharing_unknown",
                "coverage": "all_received_chains_validated; no_source_wide_or_sequence_completeness_claim",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
