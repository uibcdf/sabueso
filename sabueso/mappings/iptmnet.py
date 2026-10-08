"""Native iPTMnet report substrate rows, preserving groups and source support."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from html.parser import HTMLParser

from sabueso.core.errors import ConnectorError
from sabueso.core.source_assertion_store import make_source_assertion

URL_ROOT = "https://research.bioinformatics.udel.edu/iptmnet/entry/"
HEADERS = ("", "Site", "PTM Type", "PTM Enzyme", "Score", "Source", "PMID")
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
        r"[A-Z0-9]{6,10}", identifier
    ):
        raise ConnectorError(
            "iPTMnet report requires one exact uppercase base accession."
        )
    return {
        "accession": identifier,
        "representation": "HTML_report",
        "section": "asSubTabPanel",
    }


def _children(node, tag=None):
    return [
        x
        for x in node["children"]
        if isinstance(x, dict) and (tag is None or x["tag"] == tag)
    ]


def _descendants(node, tag):
    out = []
    for child in _children(node):
        if child["tag"] == tag:
            out.append(child)
        out.extend(_descendants(child, tag))
    return out


def _text(node):
    return "".join(x if isinstance(x, str) else _text(x) for x in node["children"])


class _ReportHTML(HTMLParser):
    """Parse only the identity and substrate panel; never execute report scripts."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.html = html
        self.starts = [0]
        for m in re.finditer("\n", html):
            self.starts.append(m.end())
        self.roots = {}
        self.stack = []

    def _offset(self):
        line, column = self.getpos()
        return self.starts[line - 1] + column

    def handle_starttag(self, tag, attrs):
        declaration = dict(attrs)
        root = tag == "div" and declaration.get("id") in {"request", "asSubTabPanel"}
        if not self.stack and not root:
            return
        if len(declaration) != len(attrs):
            raise ConnectorError(
                "Repeated iPTMnet HTML attributes in selected sections."
            )
        node = {
            "tag": tag,
            "attrs": declaration,
            "children": [],
            "start": self._offset(),
        }
        if root:
            if self.stack or declaration["id"] in self.roots:
                raise ConnectorError("Repeated or nested iPTMnet report section.")
            self.roots[declaration["id"]] = node
        else:
            self.stack[-1]["children"].append(node)
        if tag not in VOID:
            self.stack.append(node)
        else:
            node["end"] = node["start"] + len(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack:
            return
        if tag != self.stack[-1]["tag"]:
            raise ConnectorError("Malformed iPTMnet selected-section HTML nesting.")
        self.stack[-1]["end"] = self.html.index(">", self._offset()) + 1
        self.stack.pop()

    def handle_data(self, data):
        if self.stack:
            self.stack[-1]["children"].append(data)


def _one(items, message):
    if len(items) != 1:
        raise ConnectorError(message)
    return items[0]


def parse_substrate_report(html, identifier):
    """Validate all original substrate groups, including hidden sources/PMIDs."""
    response_query(identifier)
    if not isinstance(html, str) or not html:
        raise ConnectorError("iPTMnet requires a nonempty original HTML report.")
    parser = _ReportHTML(html)
    try:
        parser.feed(html)
        parser.close()
    except (ValueError, IndexError) as error:
        raise ConnectorError("Unreadable iPTMnet native HTML report.") from error
    if parser.stack or set(parser.roots) != {"request", "asSubTabPanel"}:
        raise ConnectorError(
            "iPTMnet identity/substrate panel is missing or incomplete."
        )
    identity = parser.roots["request"]
    table = _one(_descendants(identity, "table"), "Unsupported iPTMnet identity table.")
    identity_row = _one(
        [
            r
            for r in _descendants(table, "tr")
            if _children(r, "td")
            and _text(_children(r, "td")[0]).strip() == "UniProt AC / UniProt ID"
        ],
        "iPTMnet native accession declaration is missing or repeated.",
    )
    cells = _children(identity_row, "td")
    if len(cells) != 2:
        raise ConnectorError("Unsupported iPTMnet identity row.")
    accession_link = _one(
        _descendants(cells[1], "a"), "Unsupported iPTMnet native identity links."
    )
    if (
        _text(accession_link) != identifier
        or accession_link["attrs"].get("href")
        != "https://www.uniprot.org/uniprot/" + identifier
    ):
        raise ConnectorError("iPTMnet native report accession differs from query.")
    panel = parser.roots["asSubTabPanel"]
    tabs = [a for a in _descendants(panel, "a") if a["attrs"].get("role") == "tab"]
    groups = []
    for tab in tabs:
        group = _text(tab)
        if (
            not re.fullmatch(re.escape(identifier) + r"(?:-[0-9]+)?", group)
            or tab["attrs"].get("href") != "#asSub-" + group
            or tab["attrs"].get("aria-controls") != "asSub-" + group
            or group in groups
        ):
            raise ConnectorError(
                "Unsupported, foreign or repeated iPTMnet substrate group."
            )
        groups.append(group)
    tables = _descendants(panel, "table")
    if not groups or groups[0] != identifier or len(tables) != len(groups):
        raise ConnectorError("iPTMnet declared substrate groups and tables differ.")
    rows = []
    for group, table in zip(groups, tables):
        if table["attrs"].get("id") != "asSubTable-" + group:
            raise ConnectorError(
                "iPTMnet native substrate table identity differs from its tab."
            )
        thead = _one(
            _children(table, "thead"), "Missing/repeated iPTMnet native header."
        )
        headers = _children(
            _one(_children(thead, "tr"), "Unsupported iPTMnet header rows."), "th"
        )
        if tuple(_text(x).strip() for x in headers) != HEADERS:
            raise ConnectorError("Unsupported iPTMnet native substrate columns.")
        tbody = _one(_children(table, "tbody"), "Missing/repeated iPTMnet native body.")
        if any(x["tag"] not in {"tr", "script"} for x in _children(tbody)):
            raise ConnectorError("Unknown iPTMnet substrate-body structure.")
        for index, row in enumerate(_children(tbody, "tr")):
            cells = _children(row, "td")
            if len(cells) != len(HEADERS) or len(_children(row)) != len(cells):
                raise ConnectorError(
                    "Malformed iPTMnet substrate row, including late groups."
                )
            values = [_text(c).strip() for c in cells]
            if not values[2]:
                raise ConnectorError(
                    "iPTMnet substrate row lacks its modification declaration."
                )
            rows.append(
                {
                    "group": group,
                    "row_index": index,
                    "native_fields": dict(zip(HEADERS[1:], values[1:])),
                    "cells": [
                        {
                            "text": _text(c),
                            "links": [
                                {"text": _text(a), "attrs": deepcopy(a["attrs"])}
                                for a in _descendants(c, "a")
                            ],
                        }
                        for c in cells
                    ],
                    "raw_html": html[row["start"] : row["end"]],
                }
            )
    return {
        "groups": groups,
        "rows": rows,
        "identity_html": html[identity["start"] : identity["end"]],
        "identity_text": _text(identity_row),
    }


def map_substrate_report(envelope):
    """Record report-group row declarations, without canonical residue projection."""
    if (
        not isinstance(envelope, dict)
        or envelope.get("source") != "iPTMnet"
        or envelope.get("kind") != "substrate_report"
        or envelope.get("version") is not None
        or envelope.get("truncated") is not False
        or not isinstance(envelope.get("query"), dict)
    ):
        raise ConnectorError(
            "iPTMnet requires the qualified native substrate-report envelope."
        )
    identifier = envelope["query"].get("accession")
    if envelope["query"] != response_query(identifier):
        raise ConnectorError("Unsupported iPTMnet native report query scope.")
    parsed = parse_substrate_report(envelope.get("record"), identifier)
    response_hash = "sha256:" + hashlib.sha256(envelope["record"].encode()).hexdigest()
    assertions = []
    for row in parsed["rows"]:
        assertion = make_source_assertion(
            "annotations.ptm_report_rows",
            {"native_group": row["group"], **deepcopy(row["native_fields"])},
            "iPTMnet",
            f"{row['group']}:{response_hash}:row:{row['row_index']}",
            envelope.get("retrieved_at"),
            subject_ref=f"iptmnet:report_group:{row['group']}",
        )
        assertion["source"]["version"] = None
        assertion["source_metadata"] = {
            "native_row": deepcopy(row),
            "native_identity_html": parsed["identity_html"],
            "response_hash": response_hash,
            "query": deepcopy(envelope["query"]),
            "received_groups": parsed["groups"],
            "received_row_count": len(parsed["rows"]),
            "mapping_scope": {
                "identity": "native_report_accession_and_group_tab; no_isoform_base_or_protein_identity_merge",
                "position": "native_site_literal; missing_site_retained; sequence_revision_and_canonical_correspondence_unqualified",
                "support": "native_aggregate_row_and_all_hidden_source_PMID_links; no_enzyme_source_publication_pairing_reconstruction",
                "score": "native_hidden_score_label_and_original_stars; no_recalculation_probability_or_Sabueso_rule",
                "classification": "no_curated_inferred_status_or_experimental_confirmation_assigned",
                "revision": "dataset_record_sequence_and_scoring_rule_revisions_not_stated",
                "coverage": "all_received_substrate_panel_rows; other_report_sections_and_expanded_view_unqueried",
                "terms": "CC_BY_NC_SA_4_0; independent_contributing_source_rights_retained",
            },
        }
        if "snapshot_receipt" in envelope:
            assertion["source_metadata"]["snapshot_receipt"] = deepcopy(
                envelope["snapshot_receipt"]
            )
        assertions.append(assertion)
    return assertions
