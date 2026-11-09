"""Frozen SDK227 exact-location disease association link metadata, without source resolution."""

from copy import deepcopy
from dataclasses import replace

from ..card_access import _Entry
from ..errors import StorageError

RULE = "retained_context_links@2"


def _resolve(explorer, target):
    raise StorageError(
        "Original disease association links require an exact retained location."
    )


def _link(explorer, role, target, support, *, location=None):
    label = f"{role.capitalize()} · {target}"
    if role == "source" and location:
        original, _ = explorer.access._resolve(location)
        fields = {
            "sequence.checksums": "reference sequence checksums",
            "sequence.primary": "reference primary sequence",
            "identifiers.uniprot": "reference UniProt identity",
            "sequence.length": "reference sequence length",
            "annotations.isoforms": "UniProt isoform declaration",
            "relationships.has_predicted_structure": "predicted model metadata",
        }
        if isinstance(original, dict) and original.get("field_path") in fields:
            label = f"Source · {fields[original['field_path']]} · {target}"
    resolution = (
        {
            "candidates": [
                {
                    "location": location,
                    "capture": explorer.access._focal_key,
                    "basis": "exact_retained_node",
                }
            ],
            "paths": [],
            "blocked_paths": [],
            "availability": "available",
        }
        if location
        else _resolve(explorer, target)
    )
    return {
        "role": role,
        "label": label,
        "target_ref": target,
        "support": deepcopy(support),
        "rule": RULE,
        **resolution,
    }


def _link_view(
    explorer,
    links,
    origin,
    title,
    *,
    source_location=None,
    status=None,
    rule=RULE,
    reason=None,
    support_location=None,
):
    view = explorer._metadata(
        {
            "rule": rule,
            "inputs": explorer.context["captures"],
            "focal": explorer.access._focal_key,
            "source_location": source_location,
            "links": links,
            **(
                {"support_location": support_location}
                if support_location is not None
                else {}
            ),
        },
        title,
        origin,
    )
    root = view._selection._target["location"]
    _, root = explorer.access._resolve(root)
    entries = tuple(
        _Entry(
            {
                **root,
                "segments": [
                    {"type": "Key", "value": "links"},
                    {"type": "Index", "value": i},
                ],
            },
            str(i),
            link,
        )
        for i, link in enumerate(links)
    )
    if rule in (
        "assembly_generation_links@1",
        "assembly_generation_links@2",
        "assembly_generation_links@3",
        "assembly_component_list_links@1",
        "assembly_component_detail_links@1",
        "molecule_activity_context_links@1",
        "ligand_site_context_links@1",
        "quaternary_context_links@1",
        "ligand_instance_context_links@1",
        "structure_declaration_context_links@1",
        "structure_declaration_context_links@2",
        "structure_declaration_context_links@3",
        "retained_context_links@7",
    ):
        explorer._session["views"].pop(id(view), None)
    return replace(
        view,
        _selection=replace(view._selection, _entries=entries),
        _selected=entries,
        _link_panel=True,
        _status=status or ("ok" if links else "empty"),
        _request=origin.request,
        _reason=reason
        or (
            "Retained sources and an explicit local structural question; no source queries or identity merge."
            if rule == "retained_context_links@3"
            else "Retained sources and explicit destinations only; no source queries or identity merge."
        ),
    )
