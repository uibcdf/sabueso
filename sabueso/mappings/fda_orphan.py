"""Native FDA OOPD page declarations, independent of molecule or protein identity."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from html.parser import HTMLParser

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

SOURCE = "FDA Orphan Drug Designations and Approvals"
URL_ROOT = "https://www.accessdata.fda.gov/scripts/opdlisting/oopd/detailedIndex.cfm?cfgridkey="
TITLE = "Search Orphan Drug Designations and Approvals"
SUMMARY = "Two-column table with up to 11 rows, representing one orphan drug. Row headers label the data fields within record."
VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def response_query(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(
        r"[1-9][0-9]{0,11}", identifier
    ):
        raise ConnectorError("FDA OOPD access requires an exact numeric page locator.")
    return {"page_locator": identifier, "representation": "OOPD_native_detailed_page"}


class _Tables(HTMLParser):
    """Read native table nesting, including its empty wrapper/spacer rows.

    FDA nests approval tables inside an outer row without a cell wrapper. Keep
    those tables independent rather than applying browser-style HTML repairs.
    """

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.offsets = [0]
        for match in re.finditer("\n", text):
            self.offsets.append(match.end())
        self.stack, self.tables, self.title = [], [], []
        self.in_title = False

    def position(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "h1":
            self.in_title = True
        if tag == "table":
            selected = "resultstable" in attributes.get("class", "").split()
            if selected:
                if len(attributes) != len(attrs):
                    raise ConnectorError("Repeated FDA native table attributes.")
                parent = next((t for t in reversed(self.stack) if t is not None), None)
                if parent and parent["parent"]:
                    raise ConnectorError("Unsupported FDA approval table nesting.")
                if parent and parent["row"] and parent["row"]["cells"]:
                    raise ConnectorError("Unsupported FDA nested table inside a field.")
                table = {
                    "attrs": attributes,
                    "parent": parent is not None,
                    "rows": [],
                    "row": None,
                    "cell": None,
                    "start": self.position(),
                    "end": None,
                    "child_just_closed": False,
                }
                self.tables.append(table)
            else:
                if any(t is not None for t in self.stack):
                    raise ConnectorError(
                        "Unsupported FDA table nested in native results."
                    )
                table = None
            self.stack.append(table)
            return
        table = self.stack[-1] if self.stack else None
        if table is None:
            return
        if tag == "tr":
            if table["row"] is not None:
                raise ConnectorError("Unclosed FDA native result row.")
            table["row"] = {"cells": [], "start": self.position(), "attrs": attributes}
        elif tag in {"td", "th"}:
            if table["row"] is None or table["cell"] is not None:
                raise ConnectorError("Malformed FDA native field cells.")
            if len(attributes) != len(attrs):
                raise ConnectorError("Repeated FDA native cell attributes.")
            cell = {
                "tag": tag,
                "attrs": attributes,
                "parts": [],
                "start": self.position(),
            }
            table["row"]["cells"].append(cell)
            table["cell"] = cell
        elif table["cell"] is not None:
            if tag in {"script", "style", "form", "input"}:
                raise ConnectorError("Unexpected active content in FDA native field.")
            if tag == "br":
                table["cell"]["parts"].append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        table = self.stack[-1] if self.stack else None
        if table and table["cell"] is not None:
            table["cell"]["parts"].append(data)
        elif table and data.strip():
            raise ConnectorError("Unbound text in FDA native result table.")

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_title = False
        end = self.text.find(">", self.position()) + 1
        if tag == "table":
            if not self.stack:
                raise ConnectorError("Unbalanced FDA table closure.")
            table = self.stack.pop()
            if table:
                if table["cell"] is not None or table["row"] is not None:
                    raise ConnectorError("Unclosed FDA native table row/cell.")
                table["end"] = end
                if table["parent"] and self.stack and self.stack[-1] is not None:
                    self.stack[-1]["child_just_closed"] = True
            return
        table = self.stack[-1] if self.stack else None
        if table is None:
            return
        if tag in {"td", "th"}:
            cell = table["cell"]
            if cell is None or cell["tag"] != tag:
                raise ConnectorError("Mismatched FDA native field closure.")
            cell["text"] = "".join(cell.pop("parts"))
            cell["raw_html"] = self.text[cell.pop("start") : end]
            table["cell"] = None
        elif tag == "tr":
            row = table["row"]
            if row is None and table["child_just_closed"] and not table["parent"]:
                table["child_just_closed"] = False
                return  # Native empty-approval page has a stray wrapper-row close.
            if row is None or table["cell"] is not None:
                raise ConnectorError("Mismatched FDA native result row closure.")
            row["raw_html"] = self.text[row.pop("start") : end]
            table["rows"].append(row)
            table["row"] = None


def _field_rows(table, text):
    fields, ordinal, marketing_header = [], None, False
    for row in table["rows"]:
        cells = row["cells"]
        if not cells:
            continue  # Native outer wrapper or empty spacer, retained in raw table.
        if (
            len(cells) == 1
            and cells[0]["tag"] == "th"
            and cells[0]["attrs"].get("colspan") == "2"
        ):
            if " ".join(cells[0]["text"].split()) != "Marketing approved:":
                raise ConnectorError("Unsupported FDA native section header.")
            marketing_header = True
            continue
        expected = ["td", "th", "td"] if table["parent"] else ["th", "td"]
        if [c["tag"] for c in cells] != expected:
            raise ConnectorError("Unsupported FDA native result columns.")
        if table["parent"]:
            declared = cells[0]["text"].strip()
            if declared:
                if (
                    ordinal is not None
                    or fields
                    or not re.fullmatch(r"[1-9][0-9]*", declared)
                ):
                    raise ConnectorError("Unsupported FDA native approval ordinal.")
                ordinal = declared
        label, value = cells[-2:]
        label_text = " ".join(label["text"].split())
        if not label_text.endswith(":"):
            raise ConnectorError("FDA native field label lacks its delimiter.")
        fields.append(
            {
                "label": label_text[:-1].strip(),
                "value": value["text"].strip(),
                "raw_html": row["raw_html"],
                "cells": deepcopy(cells),
            }
        )
    return {
        "kind": "marketing_approval" if table["parent"] else "designation",
        "fields": fields,
        "native_ordinal": ordinal,
        "marketing_header": marketing_header,
        "raw_html": text[table["start"] : table["end"]],
    }


def parse_page(text):
    if not isinstance(text, str) or not text.strip():
        raise ConnectorError("FDA OOPD requires an original nonempty HTML page.")
    parser = _Tables(text)
    try:
        parser.feed(text)
        parser.close()
    except (ValueError, IndexError) as error:
        raise ConnectorError("Unreadable FDA native HTML page.") from error
    if (
        any(t is not None for t in parser.stack)
        or " ".join("".join(parser.title).split()) != TITLE
    ):
        raise ConnectorError("Incomplete or unexpected FDA OOPD HTML page.")
    roots = [t for t in parser.tables if not t["parent"]]
    if len(roots) != 1 or roots[0]["attrs"].get("summary") != SUMMARY:
        raise ConnectorError(
            "FDA OOPD detailed page has no unique native designation table."
        )
    if len(parser.tables) < 2:
        raise ConnectorError("FDA OOPD detailed page lacks its native approval table.")
    parsed = [_field_rows(t, text) for t in parser.tables]
    designation = parsed[0]
    required = {
        "Generic Name",
        "Date Designated",
        "Orphan Designation",
        "Orphan Designation Status",
        "Sponsor",
    }
    if not required.issubset({f["label"] for f in designation["fields"]}):
        raise ConnectorError("FDA OOPD designation fields are incomplete.")
    approvals = []
    for table in parsed[1:]:
        if not table["fields"]:
            continue
        required = {
            "Generic Name",
            "Marketing Approval Date",
            "Approved Labeled Indication",
        }
        if table["native_ordinal"] is None or not required.issubset(
            {f["label"] for f in table["fields"]}
        ):
            raise ConnectorError("FDA OOPD approval fields/ordinal are incomplete.")
        approvals.append(table)
    if approvals and not designation["marketing_header"]:
        raise ConnectorError(
            "FDA approval tables lack their original section declaration."
        )
    return {
        "records": [designation, *approvals],
        "received_approval_tables": len(parsed) - 1,
        "empty_approval_tables": sum(not t["fields"] for t in parsed[1:]),
    }


def map_page(envelope):
    """Record each received declaration; the query locator identifies only a page."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != SOURCE
        or envelope.get("kind") != "page"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError("FDA OOPD requires its qualified native page envelope.")
    identifier = envelope["query"].get("page_locator")
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("Unsupported FDA OOPD page query scope.")
    parsed = parse_page(envelope.get("record"))
    response_hash = "sha256:" + hashlib.sha256(envelope["record"].encode()).hexdigest()
    assertions = []
    for index, row in enumerate(parsed["records"]):
        assertion = make_source_assertion(
            "annotations.orphan_product_records",
            {
                "kind": row["kind"],
                "native_ordinal": row["native_ordinal"],
                "fields": [
                    {"label": f["label"], "value": f["value"]} for f in row["fields"]
                ],
            },
            SOURCE,
            f"{identifier}:{response_hash}:table:{index}",
            envelope.get("retrieved_at"),
            subject_ref=f"fda:oopd_page:{identifier}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "query": deepcopy(envelope["query"]),
            "page_url": URL_ROOT + identifier,
            "response_hash": response_hash,
            "native_table": deepcopy(row),
            "received_approval_tables": parsed["received_approval_tables"],
            "empty_approval_tables": parsed["empty_approval_tables"],
            "mapping_scope": {
                "identity": "requested_page_URL; cfgridkey_is_not_a_designation_product_or_protein_ID; HTML_does_not_echo_locator",
                "dates": "native_literals; designation_marketing_approval_withdrawal_and_exclusivity_fields_kept_separate",
                "coverage": "all_received_page_tables; no_search_or_database_completeness_claim",
                "interpretation": "no_product_molecule_protein_merge_modality_target_or_clinical_conclusion",
                "revision": "dataset_and_record_revisions_unknown; publication_dates_are_not_revision_IDs",
                "terms": "FDA_website_policy_with_noted_and_third_party_exceptions; no_openFDA_CC0_substitution",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
