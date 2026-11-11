"""Readable navigation over the literal Card capture (#148).

Literal inspection and the first shared structural adapter use one captured state.
Destination navigation uses supplied captures only. Literal/field sessions support saved reading.
"""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass, field, replace
from types import MappingProxyType

from sabueso._private.argdigest import arg_digest

from .card_access import CardAccess, _Entry, _handle, _type
from .errors import ArgumentError
from .region_requests import DEFAULT_REGION_BUDGET, receiving

_LABELS = {
    "meta": "Card details",
    "sections": "Knowledge",
    "source_assertion_store": "Source statements",
    "relationship_store": "Relationships",
    "selection_rules": "Selection rules",
    "quality": "Coverage and quality records",
    "quantities": "Quantity integrity",
    "entities": "Entity records",
}
_TOPICS = {
    "comparative_context": (
        "Related proteins and explicit comparisons",
        "Source relationships and explicitly supplied protein comparisons; no identity merge.",
    ),
    "sequence_changes": (
        "Natural variants and mutagenesis",
        "Original protein substitutions and source annotations, separate from population genomic variants.",
    ),
    "variants": (
        "Variants, isoforms and tissue context",
        "Original population-variant and isoform tissue scope, exact input support and per-tissue unknowns.",
    ),
    "associations": (
        "Retained molecular and clinical associations",
        "Original association directions, indication and variant-condition occurrences in explicitly supplied input scope.",
    ),
    "clinical": (
        "Indications and clinical studies",
        "Source indications, individual cited trials and retained registry records, with separate phases, support and original request scope.",
    ),
    "activity_context": (
        "Targets, measurements and assay context",
        "Exact molecule identity joins into explicitly supplied target captures, preserving original measurements and source/query scope.",
    ),
    "literature": (
        "Publications and stored source links",
        "Original citations, ECO support, curated statements, mentions and source activity records, with complete publication context.",
    ),
    "bioactivities": (
        "Measured molecules and assay context",
        "Retained molecule, measurement-group and activity records with units, original assay/citation context and source support.",
    ),
    "assembly_generation": (
        "Assembly components and operations",
        "Original assembly declarations, key binding and declared combination counts; physical copies and contacts remain uncomputed.",
    ),
    "quaternary_interpretation": (
        "Interface classifications and family-site comparisons",
        "Source-bound interface findings and all family-site pairs, with original inputs and explicit uncomputed context.",
    ),
    "quaternary_structure": (
        "Subunits, assemblies and interfaces",
        "Original source declarations with structure-local assembly context, interface numbering and complete support.",
    ),
    "ligand_site_comparisons": (
        "Ligand contacts and annotated-site comparisons",
        "Source-bound comparisons, partial findings and uncomputed coordinate context with original inputs.",
    ),
    "annotated_regions": (
        "Annotated regions and structural context",
        "Individual source annotations with their axes, original support and explicit structural questions.",
    ),
    "ligand_instances": (
        "Ligand instances in structures",
        "Original structure-local ligand instances, recorded chains and contact coordinates/distances.",
    ),
    "sequence": (
        "Sequence and annotations",
        "Original sequence, units, checksums and source positional annotations.",
    ),
    "predicted_structures": (
        "Predicted models",
        "Source model versions, metrics, ranges and sequence context; separate from experiments.",
    ),
    "sites": (
        "Sites and contact statements",
        "Original functional-site fields and ligand/interface contacts with their numbering.",
    ),
    "chemistry": (
        "Chemical identity",
        "Retained chemical representations and source-stated identity links.",
    ),
    "properties": (
        "Physicochemical properties",
        "Stored values, units, source methods and alternatives.",
    ),
    "definition": (
        "Disease definition",
        "Ontology definition, scoped synonyms and retained term metadata.",
    ),
    "classification": (
        "Disease classification",
        "Retained parent relationships; identity terminology is separate.",
    ),
    "identity": (
        "Identity terminology",
        "Equivalent identifiers and related xrefs, explicitly separated.",
    ),
    "quality": (
        "Stored quality records",
        "Complete original quality, enrichment and selection records.",
    ),
    "function": (
        "Protein function",
        "Retained function, catalytic annotations and identity; no inferred function.",
    ),
    "structures": (
        "Experimental structures",
        "Existing inventory, original state rules and pinned support.",
    ),
    "content": ("Explore all content", "Complete retained Card content."),
    "sources": ("Source statements", "Original statements retained from sources."),
    "coverage": (
        "Knowledge coverage",
        "Original source/area knowledge states and their classification inputs.",
    ),
}


def _key(value):
    return {"type": "Key", "value": value}


@dataclass(frozen=True)
class Cell:
    """One retained value; public mutable values and support are defensive copies."""

    _value: object = field(repr=False)
    state: str = "present"
    reason: str | None = None
    _support: tuple = field(default=(), repr=False)

    @property
    def value(self):
        return deepcopy(self._value)

    @property
    def support(self):
        return deepcopy(list(self._support))

    def to_dict(self):
        return {
            "value": self.value,
            "state": self.state,
            "reason": self.reason,
            "support": self.support,
        }


@dataclass(frozen=True, repr=False)
class CardItem:
    """A labeled item bound to its originating selected view."""

    _view: object = field(repr=False)
    _entry: _Entry = field(repr=False)

    @property
    def item_ref(self):
        return _handle(
            "XI_",
            {"result_ref": self._view.result_ref, "location": self._entry.location},
        )

    @property
    def kind(self):
        if self._view._record_panel in (
            "clinical",
            "associations",
            "variants",
            "sequence_changes",
            "protein_context",
        ):
            return self._entry.value["kind"]
        if self._view._record_panel == "literature":
            return self._entry.value["kind"]
        if self._view._record_panel in ("bioactivities", "activity_context"):
            return self._entry.value["kind"]
        if self._view._record_panel == "chemical_classification":
            return self._entry.value["kind"]
        if self._view._record_panel == "assembly_generation":
            return self._entry.value["kind"]
        if self._view._record_panel == "quaternary_interpretation":
            return self._entry.value["kind"]
        if self._view._field_panel == "quaternary_structure":
            from .card_quaternary_source_v1 import context

            return context(self._view.explorer, self._entry)[0]
        if self._view._field_panel == "annotated_regions":
            return "annotation"
        if self._view._link_panel:
            return "link"
        if self._view._record_panel:
            return (
                "ligand_contact_comparison"
                if self._view._record_panel == "ligand_site_comparisons"
                else "knowledge_state"
                if self._view._record_panel == "coverage"
                else "relationship"
            )
        if self._view._field_panel:
            from .card_exploration_profiles import is_field

            return (
                "field"
                if is_field(self._entry)
                else "ligand_instance"
                if self._view._field_panel == "ligand_instances"
                else "predicted_model"
                if self._view._field_panel == "predicted_structures"
                else "contact_relationship"
                if self._view._field_panel == "sites"
                else "identity_statement"
            )
        if self._view._selection._scientific is not None:
            return "structure"
        return "route" if self._view._route_catalog else "literal"

    @property
    def label(self):
        if self._view._record_panel in ("sequence_changes", "protein_context"):
            return self._entry.value["label"]
        if self._view._link_panel:
            return self._entry.value["label"]
        if self._view._record_panel:
            if (
                self._view._record_panel == "coverage"
                and self._view._explorer.mode == "saved"
            ):
                return f"{self._entry.value['area']} · {self._entry.value['source']}"
            if self._view._record_panel == "classification":
                from .card_exploration_labels import relationship_basis

                return (
                    f"{relationship_basis(self)[0]} · {self._entry.value['object_ref']}"
                )
            from .card_exploration_profiles import record_label

            return record_label(self._view._record_panel, self._entry.value)
        if self._view._field_panel:
            from .card_exploration_profiles import field_label

            return field_label(
                self._view._field_panel, self._entry, self._view._explorer
            )
        if self._view._selection._scientific is not None:
            return self._entry.value["structure_ref"]
        if self._view._route_catalog:
            if self._view._question_catalog:
                return self._view._explorer._questions[self._entry.key]["label"]
            return self._view._explorer._topic_label(self._entry.key)
        from .card_protein_source_v1 import node_label

        friendly = node_label(self)
        if friendly is not None:
            return friendly
        segments = self._entry.location["segments"]
        if len(segments) == 1 and segments[0]["type"] == "Key":
            return _LABELS.get(self._entry.key, str(self._entry.key))
        node = self._entry.value
        if segments and segments[-1]["type"] == "Record" and isinstance(node, dict):
            if segments[0]["value"] == "source_assertion_store":
                source = node.get("source", {})
                name = source.get("name") if isinstance(source, dict) else source
                from .card_exploration_labels import source_role

                label = " · ".join(
                    str(v)
                    for v in (
                        name,
                        source.get("record_id") if isinstance(source, dict) else None,
                        node.get("field_path"),
                    )
                    if v is not None
                ) or str(self._entry.key)
                role = source_role(self)
                return f"{role} · {label}" if role else label
            return f"{node.get('predicate', 'Relationship')} → {node.get('object_ref', '')}"
        return str(self._entry.key) if self._entry.key is not None else "Value"

    @property
    def payload_location(self):
        if self._view._record_panel in ("sequence_changes", "protein_context"):
            return deepcopy(self._entry.value["original_location"])
        return deepcopy(self._entry.location)

    @property
    def is_selected(self):
        return self._entry in self._view._selected

    @property
    def support(self):
        if self._view._record_panel == "activity_context":
            from .card_molecule_activity_exploration import support

            return support(self)
        if self._view._record_panel == "literature":
            from .card_literature_exploration import support

            return support(self)
        if self._view._record_panel == "bioactivities":
            from .card_bioactivity_exploration import support

            return support(self)
        if self._view._record_panel == "chemical_classification":
            from .card_chemical_exploration import support

            return support(self)
        if self._view._record_panel == "assembly_generation":
            from .card_assembly_dispatch import presentation

            return presentation(self._view).support(self)
        if self._view._record_panel == "quaternary_interpretation":
            if self._view._explorer.mode == "saved":
                from .card_quaternary_history_v1 import support
            else:
                from .card_quaternary_exploration import support

            return support(self)
        if self._view._record_panel == "ligand_site_comparisons":
            if self._view._explorer.mode == "saved":
                from .card_ligand_site_history_v1 import support
            else:
                from .card_ligand_site_exploration import support

            return support(self)
        if self._view._field_panel == "annotated_regions":
            from .card_annotation_regions_v1 import support

            return support(self._view._explorer, self._entry.location)
        if self._view._link_panel:
            return deepcopy(self._entry.value["support"])
        if self._view._record_panel == "coverage":
            return [
                {
                    "basis": "derived_knowledge_state",
                    "rule": deepcopy(
                        self._view._explorer._coverage_result.native["rule"]
                    ),
                    "location": self.payload_location,
                    "explanation_available": True,
                }
            ]
        if self._view._selection._scientific is not None:
            return [
                deepcopy(
                    self._view._selection._scientific.wire["support"][self._entry.key]
                )
            ]
        return self._view._explorer._support(self._entry.location)

    @property
    def cells(self):
        if self._view._record_panel in (
            "clinical",
            "associations",
            "variants",
            "sequence_changes",
            "protein_context",
        ):
            if self._view._record_panel == "protein_context":
                from .card_protein_context_dispatch import selection

                COLUMNS = selection(self._view).COLUMNS
            elif self._view._record_panel == "sequence_changes":
                from .card_sequence_change_dispatch import selection

                COLUMNS = selection(self._view).COLUMNS
            elif self._view._record_panel == "variants":
                if self._view._explorer.mode == "saved":
                    from ._variant_history_v1.selection import COLUMNS
                else:
                    from .card_variant_selection_v1 import COLUMNS
            elif self._view._record_panel == "associations":
                if self._view._explorer.mode == "saved":
                    from ._disease_association_history_v1.selection import COLUMNS
                else:
                    from .card_disease_association_selection_v1 import COLUMNS
            elif self._view._explorer.mode == "saved":
                from ._clinical_history_v1.selection import COLUMNS
            else:
                from .card_clinical_selection_v1 import COLUMNS

            result = self._view._selection._scientific
            support = tuple(self.support)
            return MappingProxyType(
                {
                    column: Cell(
                        deepcopy(result.value(self._entry.key, column)),
                        state=result.cell_state(self._entry.key, column),
                        reason=result.cell_reason(self._entry.key, column),
                        _support=support,
                    )
                    for column in COLUMNS
                }
            )
        if self._view._record_panel == "literature":
            from .card_literature_selection_v1 import COLUMNS

            result = self._view._selection._scientific
            support = tuple(self.support)
            return MappingProxyType(
                {
                    column: Cell(
                        deepcopy(result.value(self._entry.key, column)),
                        state=result.cell_state(self._entry.key, column),
                        reason=result.cell_reason(self._entry.key, column),
                        _support=support,
                    )
                    for column in COLUMNS
                }
            )
        if self._view._record_panel in ("bioactivities", "activity_context"):
            if self._view._record_panel == "activity_context":
                from .card_molecule_activity_selection_v1 import COLUMNS
            else:
                from .card_bioactivity_selection_v1 import COLUMNS
            from .quantities import to_quantity

            result = self._view._selection._scientific
            values = {
                column: result.value(self._entry.key, column) for column in COLUMNS
            }
            support = tuple(self.support)
            return MappingProxyType(
                {
                    column: Cell(
                        to_quantity(value)
                        if column == "measurement" and value is not None
                        else deepcopy(value),
                        state=result.cell_state(self._entry.key, column),
                        reason=result.cell_reason(self._entry.key, column),
                        _support=support,
                    )
                    for column, value in values.items()
                }
            )
        if self._view._record_panel == "assembly_generation":
            from .card_assembly_selection_v1 import COLUMNS

            result = self._view._selection._scientific
            return MappingProxyType(
                {
                    column: Cell(
                        self._entry.value[column],
                        state=result.cell_state(self._entry.key, column),
                        reason=result.cell_reason(self._entry.key, column),
                        _support=tuple(self.support),
                    )
                    for column in COLUMNS
                }
            )
        if self._view._field_panel == "quaternary_structure":
            from .card_quaternary_source_v1 import values

            fields = {
                "label": self.label,
                **values(self._view.explorer, self._entry),
                "type": "object",
            }
            fields["type"] = _type(fields["value"])
            return MappingProxyType(
                {
                    key: Cell(
                        value,
                        state="unknown" if value is None else "present",
                        _support=tuple(self.support),
                    )
                    for key, value in fields.items()
                }
            )
        if self._view._field_panel == "annotated_regions":
            from .card_annotation_regions_v1 import annotation_path, context

            key, _ = annotation_path(self._entry.location)
            value = self._entry.value
            location = value.get("location")
            axis = location.get("sequence") if isinstance(location, dict) else None
            axis = axis if isinstance(axis, dict) else {}
            binding = context(self._view._explorer, self._entry.location)
            values = {
                "label": self.label,
                "kind": self.kind,
                "feature_type": key,
                "sequence_ref": axis.get("sequence_id"),
                "start": axis.get("start"),
                "end": axis.get("end"),
                "context_state": binding["state"],
                "value": value,
                "type": "object",
            }
            basis = tuple(self.support)
            return MappingProxyType(
                {
                    key: Cell(
                        value,
                        state="unknown" if value is None else "present",
                        _support=basis,
                    )
                    for key, value in values.items()
                }
            )
        if self._view._field_panel == "ligand_instances":
            from .card_ligand_instances_v1 import context

            row, ligand = context(self._view._explorer, self._entry)
            values = {
                "label": self.label,
                "kind": self.kind,
                "structure_ref": row["object_ref"],
                "component_id": ligand.get("comp_id"),
                "instance_id": self._entry.value.get("asym_id"),
                "value": self._entry.value,
                "type": "object",
            }
            return MappingProxyType(
                {
                    key: Cell(
                        value,
                        state="unknown" if value is None else "present",
                        _support=tuple(self.support),
                    )
                    for key, value in values.items()
                }
            )
        if self._view._link_panel:
            return MappingProxyType(
                {
                    key: Cell(
                        self.label
                        if key == "label"
                        else self.kind
                        if key == "kind"
                        else self._entry.value[key],
                        _support=tuple(self.support),
                    )
                    for key in ("label", "kind", "role", "target_ref", "availability")
                }
            )
        if self._view._record_panel:
            from .card_exploration_profiles import RECORD_COLUMNS

            if (
                self._view._record_panel == "coverage"
                and self._view._explorer.mode == "saved"
            ):
                from .card_exploration_adapter_v1 import COVERAGE_COLUMNS

                columns = COVERAGE_COLUMNS
            else:
                columns = RECORD_COLUMNS[self._view._record_panel]
            return MappingProxyType(
                {
                    column: Cell(
                        value,
                        state="unknown" if value is None else "present",
                        _support=tuple(self.support),
                    )
                    for column in (
                        "label",
                        "kind",
                        *columns,
                    )
                    for value in (
                        self.label
                        if column == "label"
                        else self.kind
                        if column == "kind"
                        else self._entry.value.get(column),
                    )
                }
            )
        result = self._view._selection._scientific
        if result is not None:
            if self._view._explorer.mode == "saved":
                from .card_exploration_adapter_v1 import COLUMNS
            else:
                from .card_scientific_access import COLUMNS

            return MappingProxyType(
                {
                    column: Cell(
                        record["value"],
                        record["state"],
                        record["reason"],
                        tuple(record["support"]),
                    )
                    for column in ("label", "kind", *COLUMNS)
                    for record in (result.cell(self._entry.key, column),)
                }
            )
        from .card_exploration_profiles import is_field

        value = self._entry.value
        field_item = bool(self._view._field_panel) and is_field(self._entry)
        # Only declared Card quantities are converted; extension lookalikes stay raw.
        access = self._view._explorer.access
        quantity = None
        if isinstance(value, dict) and "value" in value and "unit" in value:
            quantity = access._quantity_context(
                {
                    **self._entry.location,
                    "segments": [*self._entry.location["segments"], _key("value")],
                }
            )
        if quantity is not None:
            from pyunitwizard import QuantityRecord

            value = QuantityRecord.from_dict(quantity["record"]).to_quantity(
                field=quantity["field"], unit=value["unit"]
            )
        elif field_item:
            value = value["value"]
        return MappingProxyType(
            {
                "label": Cell(self.label),
                "kind": Cell(self.kind),
                "value": Cell(
                    value,
                    state="conflicting"
                    if self._conflicts
                    else "unknown"
                    if field_item and value is None
                    else "present",
                    reason="Stored conflict; inspect explain() and the quality records."
                    if self._conflicts
                    else "No retained value for this field."
                    if field_item and value is None
                    else None,
                    _support=tuple(self.support),
                ),
                "type": Cell(
                    "quantity"
                    if field_item and quantity is not None
                    else _type(value)
                    if field_item
                    else _type(self._entry.value)
                ),
            }
        )

    @property
    def _conflicts(self):
        location = self._entry.location
        segments = location["segments"]
        if (
            location["kind"] != "card"
            or not segments
            or segments[0] != _key("sections")
        ):
            return []
        keys = [s["value"] for s in segments[1:] if s["type"] == "Key"]
        path = ".".join(keys)
        quality = self._view._explorer.access._focal.data.get("quality", {})
        conflicts = quality.get("conflicts", []) if isinstance(quality, dict) else []
        if not isinstance(conflicts, list):
            return []
        return [
            conflict
            for conflict in conflicts
            if isinstance(conflict, dict)
            and conflict.get("field") in (path, path.removesuffix(".value"))
        ]

    def open(self):
        """Open all retained detail, or follow a labeled catalog route."""
        if (
            self._view._explorer.mode == "saved"
            and self._view._explorer._session.get("format")
            == "sabueso.card_exploration@35"
        ):
            from .card_exploration_knowledge_comparison import (
                is_context,
                is_view,
                item_operation,
                open_retained_child,
            )

            if is_view(self._view):
                return item_operation(self, "open")
            if is_context(self._view):
                return (
                    item_operation(self, "open")
                    if self._view._link_panel
                    else open_retained_child(self)
                )
        if self._view._explorer.mode == "saved" and self._view._explorer._session.get(
            "format"
        ) in ("sabueso.card_exploration@33", "sabueso.card_exploration@35"):
            from .card_exploration_protein_context import (
                is_context,
                is_view,
                item_operation,
                open_retained_child,
            )

            if is_view(self._view):
                return item_operation(self, "open")
            if is_context(self._view):
                return (
                    item_operation(self, "open")
                    if self._view._link_panel
                    else open_retained_child(self)
                )
        if self._view._record_panel == "protein_context":
            from .card_protein_context_dispatch import presentation

            return presentation(self._view).open_item(self)
        if self._view._record_panel == "sequence_changes":
            if self._view._explorer.mode == "saved":
                from .card_exploration_sequence_change import item_operation

                return item_operation(self, "open")
            from .card_sequence_change_dispatch import presentation

            open_item = presentation(self._view).open_item

            return open_item(self)
        if self._view._explorer.mode == "saved" and self._view._explorer._session.get(
            "format"
        ) in (
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from .card_exploration_sequence_change import (
                is_context,
                item_operation,
                open_retained_child,
            )

            if is_context(self._view):
                return (
                    item_operation(self, "open")
                    if self._view._link_panel
                    else open_retained_child(self)
                )
        if self._view._record_panel == "variants":
            if self._view._explorer.mode == "saved":
                from .card_exploration_variant import item_operation

                return item_operation(self, "open")
            from .card_variant_exploration import open_item

            return open_item(self)
        if self._view._record_panel == "associations":
            if self._view._explorer.mode == "saved":
                from .card_exploration_disease_association import item_operation

                return item_operation(self, "open")
            from .card_disease_association_exploration import open_item

            return open_item(self)
        if self._view._record_panel == "clinical":
            if self._view._explorer.mode == "saved":
                from .card_exploration_clinical import item_operation

                return item_operation(self, "open")
            from .card_clinical_exploration import open_item

            return open_item(self)
        if self._view._link_panel:
            from .card_context_navigation import follow

            return follow(self)
        if self._view._route_catalog:
            if self._view._question_catalog:
                return self._view._explorer._answer(self._entry.key, {}, self._view)
            return self._view._explorer._topic(self._entry.key, self._view)
        if self._view._record_panel == "activity_context":
            if self._view._explorer.mode == "saved":
                from .card_molecule_activity_operations_v1 import saved_item

                return saved_item(self, "open")
            from .card_molecule_activity_exploration import open_item

            return open_item(self)
        if self._view._record_panel == "literature":
            if self._view._explorer.mode == "saved":
                from .card_exploration_literature import open_item
            else:
                from .card_literature_exploration import open_item

            return open_item(self)
        if self._view._record_panel == "bioactivities":
            if self._view._explorer.mode == "saved":
                from .card_bioactivity_dispatch import binding

                open_item = binding(self._view._explorer.access).open_item
            else:
                from .card_bioactivity_exploration import open_item

            return open_item(self)
        if self._view._record_panel in (
            "chemical_classification",
            "ligand_site_comparisons",
            "quaternary_interpretation",
            "assembly_generation",
        ):
            return replace(
                self._view,
                _selected=(self._entry,),
                _origin=self._view,
                _display_request=None,
                _native_override=deepcopy(self._entry.value["item"]),
                title=f"Assembly declaration · {self.label}"
                if self._view._record_panel == "assembly_generation"
                else f"Quaternary finding · {self.label}"
                if self._view._record_panel == "quaternary_interpretation"
                else f"Chemical class or role · {self.label}"
                if self._view._record_panel == "chemical_classification"
                else f"Ligand contact comparison · {self.label}",
                presentation="detail",
            )
        if self._view._selection._scientific is not None:
            return replace(
                self._view,
                _selected=(self._entry,),
                _origin=self._view,
                _focus=self._entry.key,
                _display_request=None,
                title=f"Structure {self.label}",
                presentation="detail",
            )
        context = self._view._context_override
        if (
            self._view._explorer.mode == "saved"
            and isinstance(context, dict)
            and context.get("adapter") == "variant_context_links@1"
        ):
            from .card_exploration_variant import open_retained_child

            return open_retained_child(self)
        if (
            isinstance(context, dict)
            and context.get("adapter") == "disease_association_context_links@1"
            and not self._view._link_panel
        ):
            from .card_exploration_disease_association import open_retained_child

            return open_retained_child(self)
        if (
            isinstance(context, dict)
            and context.get("adapter") == "molecule_activity_context_links@1"
            and self._entry.location["kind"] == "card"
            and self._entry.location["card_ref"]
            != self._view._explorer.access._focal.pin
        ):
            from .card_exploration_molecule_activity import open_retained_child

            return open_retained_child(self)
        return replace(
            self._view._explorer._inspect(
                self._entry.location, self._view, title=self.label
            ),
            _request=self._view._request,
            _display_request=None,
            _context_only=self._view._context_only,
            _context_override=self._view._context_override,
        )

    def related(self):
        """Explore retained sources, relationship endpoints and supplied Cards."""
        from .card_context_navigation import related

        if self._view._explorer.mode == "saved":
            from .card_exploration_storage import saved_item_operation

            return saved_item_operation(self, "links")
        result = related(self)
        from .card_exploration_storage import operation_key

        self._view._explorer._session["links"][operation_key(self)] = result
        return result

    def explain(self):
        """Inspect original support without interpreting a source's silence."""
        if self._view._explorer.mode == "saved":
            from .card_exploration_storage import saved_item_operation

            return saved_item_operation(self, "explanations")
        result = self._live_explain()
        from .card_exploration_storage import operation_key

        self._view._explorer._session["explanations"][operation_key(self)] = result
        return result

    def _live_explain(self):
        if self._view._record_panel == "protein_context":
            from .card_protein_context_dispatch import presentation

            return presentation(self._view).explain(self)
        if self._view._record_panel == "sequence_changes":
            from .card_sequence_change_dispatch import presentation

            explain = presentation(self._view).explain

            return explain(self)
        if self._view._record_panel == "variants":
            from .card_variant_exploration import explain

            return explain(self)
        if self._view._record_panel == "associations":
            from .card_disease_association_exploration import explain

            return explain(self)
        if self._view._record_panel == "clinical":
            from .card_clinical_exploration import explain

            return explain(self)
        if self._view._record_panel == "activity_context":
            from .card_molecule_activity_exploration import explain

            return explain(self)
        if self._view._record_panel == "literature":
            from .card_literature_exploration import explain

            return explain(self)
        if self._view._record_panel == "bioactivities":
            from .card_bioactivity_exploration import explain

            return explain(self)
        if self._view._record_panel == "chemical_classification":
            from .card_chemical_exploration import explain

            return explain(self)
        if self._view._record_panel == "assembly_generation":
            from .card_assembly_dispatch import presentation

            return presentation(self._view).explain(self)
        if self._view._record_panel == "quaternary_interpretation":
            from .card_quaternary_exploration import explain

            return explain(self)
        if self._view._record_panel == "ligand_site_comparisons":
            from .card_ligand_site_exploration import explain

            return explain(self)
        if self._view._link_panel:
            return self._view._explorer._metadata(
                {"rule": self._entry.value["rule"], "link": self._entry.value},
                f"Link support for {self.label}",
                self._view,
            )
        if self._view._record_panel == "coverage":
            from .card_coverage_exploration import explain

            return explain(self._view._explorer, self._entry.value, self._view)
        result = self._view._selection._scientific
        if result is not None:
            selection = self._view._explorer.access.explain(self.item_ref)
            view = self._view._explorer._inspect(
                selection._target["location"],
                self._view,
                title=f"Scientific support for {self.label}",
            )
            entries = []
            seen = set()
            for statement in result.wire["support"][self._entry.key][
                "source_assertions"
            ]:
                if statement["state"] == "present" and statement["id"] not in seen:
                    value, location = self._view._explorer.access._resolve(
                        statement["location"]
                    )
                    entries.append(_Entry(location, statement["id"], value))
                    seen.add(statement["id"])
            return replace(
                view,
                _selected=tuple(entries),
                _selection=replace(view._selection, _entries=tuple(entries)),
                _native_override=result.explanations[self._entry.key],
                _request=self._view._request,
                _reason="Original source records for this structure relationship; complete scientific explanation remains in native_payload.",
            )
        from .card_exploration_profiles import alternatives

        alternative_context = (
            alternatives(self._view._explorer, self._entry)
            if self._view._field_panel
            else {}
        )
        view = self._view._explorer._metadata(
            {
                "basis": "stored_literal",
                "support": self.support,
                "stored_conflicts": self._conflicts,
                **alternative_context,
                "selection_rules": self._view._explorer.access._focal.data.get(
                    "selection_rules", {}
                ),
                "quality_location": self._view._explorer._location("quality"),
                "reason": "Original support only; no new scientific explanation is derived.",
            },
            f"Support for {self.label}",
            self._view,
        )
        view = replace(view, _request=self._view._request)
        if self._view._field_panel or self._view._record_panel == "classification":
            # Direct source-record rows spare the researcher a traversal through
            # support bookkeeping. Missing records stay explicit in native_payload.
            entries = []
            seen = set()
            for support in self.support:
                for statement in support.get("statements", []):
                    if statement["state"] == "present" and statement["id"] not in seen:
                        value, location = self._view._explorer.access._resolve(
                            statement["location"]
                        )
                        entries.append(_Entry(location, statement["id"], value))
                        seen.add(statement["id"])
            for statement in [
                *alternative_context.get("alternative_source_assertions", []),
                *alternative_context.get("unclassified_field_source_assertions", []),
            ]:
                if statement["state"] == "present" and statement["id"] not in seen:
                    value, location = self._view._explorer.access._resolve(
                        statement["location"]
                    )
                    entries.append(_Entry(location, statement["id"], value))
                    seen.add(statement["id"])
            return replace(
                view,
                _selected=tuple(entries),
                _selection=replace(view._selection, _entries=tuple(entries)),
                _reason="Original source records; unretained support and alternatives remain in native_payload.",
            )
        return view

    def back(self):
        return self._view

    def __repr__(self):
        from .card_exploration_render import preview

        return f"CardItem({preview(self.label)}; open(), explain(), related(), back())"


@dataclass(frozen=True, repr=False)
class CardItems(Sequence):
    """All selected items; rendering previews never truncate this sequence."""

    _view: object = field(repr=False)

    def __len__(self):
        return len(self._view._selected)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self._view._item(e) for e in self._view._selected[index])
        return self._view._item(self._view._selected[index])

    def __repr__(self):
        return (
            f"CardItems({len(self)} items; index, slice or iterate for complete access)"
        )


@dataclass(frozen=True, repr=False)
class CardView:
    """One captured result with independent presentation and navigation state."""

    _explorer: object = field(repr=False)
    _selection: object = field(repr=False)
    _selected: tuple = field(repr=False)
    title: str
    _origin: object = field(default=None, repr=False)
    _route_catalog: bool = False
    _question_catalog: bool = False
    _field_panel: str | None = field(default=None, repr=False)
    _record_panel: str | None = field(default=None, repr=False)
    _link_panel: bool = field(default=False, repr=False)
    _context_override: object = field(default=None, repr=False)
    _context_only: bool = field(default=False, repr=False)
    _request: object = field(default=None, repr=False)
    _status: str = "ok"
    _reason: str | None = None
    presentation: str = "summary"
    _focus: str | None = field(default=None, repr=False)
    _native_override: object = field(default=None, repr=False)
    _saved_state: object = field(default=None, repr=False)
    _display_request: object = field(default=None, repr=False)
    _machine_ref: str | None = field(default=None, repr=False)
    _component_navigation: dict | None = field(default=None, repr=False)
    _workload: object = field(default=None, repr=False)

    def __post_init__(self):
        self._explorer._session["views"][id(self)] = self

    def _item(self, entry):
        if self._saved_state is not None:
            from .card_exploration_storage import _SavedItem

            return _SavedItem(self, entry)
        return CardItem(self, entry)

    @property
    def workload(self):
        """Receiving policy/request for this invocation; None if not retained."""
        return deepcopy(self._workload)

    @property
    def orientation(self):
        """Detached presentation of curated original overview fields and sources.

        Exact typed locations retain field values, declared support references,
        source versions and stored quality scope. None outside a supported
        overview; no new knowledge, acquisition or scientific evaluation.
        """
        from .card_orientation_v1 import reading

        return reading(self)

    @property
    def regional_reading(self):
        """Current presentation of this focused original regional result.

        Contains per-chain counts and exact original input/output locations, not
        a new coordinate calculation. None outside a focused structural region.
        Historical results retain their own coordinate basis and unknowns.
        """
        return self._regional_reading()

    def _regional_reading(self, *, chain_limit=None):
        """Prepare only the requested presentation prefix, without omitting silently."""
        result = self._selection._scientific
        if (
            result is None
            or self._focus is None
            or result.wire["context"]["adapter"] != "structure_exploration@1"
        ):
            return None
        from .card_structure_reading_v1 import reading

        return reading(
            self._explorer.access, result, self._focus, chain_limit=chain_limit
        )

    @property
    def ligand_reading(self):
        """Current presentation of an exact original structure ligand node.

        Component/instance fields retain their original states, counts and typed
        locations. None elsewhere. No region, contact or assembly join is made;
        historical source values and scientific results remain unchanged.
        """
        return self._ligand_reading()

    def _ligand_reading(self, *, entry_limit=None):
        from .card_ligand_reading_v1 import reading

        return reading(self, entry_limit=entry_limit)

    @property
    def explorer(self):
        return None if self._context_only else self._explorer

    @property
    def result_ref(self):
        return self._selection.result_ref

    @property
    def view_ref(self):
        return _handle(
            "XV_",
            {
                "format": "literal_human_view@1",
                "result_ref": self.result_ref,
                "selection": [item.item_ref for item in self.items()],
                "presentation": self.presentation,
                "title": self.title,
                "route_catalog": self._route_catalog,
                **({"link_panel": True} if self._link_panel else {}),
                **(
                    {"context": self._context_override}
                    if self._context_override
                    else {}
                ),
                **({"focus": self._focus} if self._focus is not None else {}),
                **(
                    {"question_request": self._request}
                    if self._request is not None
                    else {}
                ),
                **({"question_catalog": True} if self._question_catalog else {}),
                **({"field_panel": self._field_panel} if self._field_panel else {}),
                **({"record_panel": self._record_panel} if self._record_panel else {}),
                **(
                    {"component_navigation": self._component_navigation}
                    if self._component_navigation is not None
                    else {}
                ),
            },
        )

    @property
    def at_root(self):
        return self._origin is None

    @property
    def context(self):
        if self._saved_state is not None:
            return {**deepcopy(self._saved_state["context"]), "mode": "saved"}
        if self._context_override is not None:
            return deepcopy(self._context_override)
        if self._link_panel:
            return {**self._explorer.context, "adapter": self.native_payload["rule"]}
        if self._selection._scientific is not None:
            return deepcopy(self._selection._scientific.wire["context"])
        if self._record_panel or self._field_panel:
            adapter = (
                "knowledge_coverage_exploration@1"
                if self._record_panel == "coverage"
                else "disease_classification_fields@1"
                if self._record_panel
                else "protein_function_fields@1"
                if self._field_panel == "function"
                else f"{self._field_panel}_fields@1"
            )
            return {
                **self._explorer.context,
                "adapter": adapter,
                "used_captures": [self._explorer.access._focal_key],
            }
        return {**self._explorer.context, "adapter": "literal_human@1"}

    @property
    def outcome(self):
        return {"status": self._status, "reason": self._reason}

    @property
    def validation(self):
        """Reported saved integrity/binding scope, or None for a live interpretation."""
        return (
            deepcopy(self._explorer._session.get("validation"))
            if self._explorer.mode == "saved"
            else None
        )

    @property
    def request(self):
        """Explicit question binding, or None for ordinary topic/literal views."""
        return deepcopy(self._request)

    @property
    def coverage(self):
        if self._saved_state is not None:
            return deepcopy(self._saved_state["coverage"])
        if self._record_panel == "coverage" and self._explorer._coverage_result.native:
            return {
                "basis": "original_knowledge_state",
                **deepcopy(self._explorer._coverage_result.native),
                "reason": "Source/area/request scope only; no global completeness denominator is known.",
            }
        if self._selection._scientific is not None:
            if (
                self._selection._scientific.wire.get("context", {}).get("adapter")
                == "protein_knowledge_comparison_exploration@1"
            ):
                from .card_knowledge_comparison_history_v1 import coverage

                return coverage(self._selection._scientific)
            return deepcopy(self._selection._scientific.wire["coverage"])
        return {
            "classification": "not_evaluated",
            "basis": "stored_literal",
            "quality_location": None
            if self._context_only
            else self._explorer._location("quality"),
            "reason": "Inspect the stored quality records; no source coverage is inferred.",
        }

    @property
    def capabilities(self):
        capabilities = {
            "items": True,
            "rows": True,
            "inspect": not self._context_only,
            "explain": True,
            "filter": ["label", "kind"],
            "sort": ["label", "kind"],
            "related": not self._context_only,
            "save": self._can_save(),
            "scientific_adapter": False,
        }
        if self._link_panel:
            capabilities.update(
                filter=self.schema["columns"], sort=self.schema["columns"], follow=True
            )
        if self._field_panel:
            capabilities.update(
                filter=self.schema.get("selection_columns", ["label", "kind"]),
                sort=self.schema.get("selection_columns", ["label", "kind"]),
            )
        if self._record_panel:
            capabilities.update(
                filter=self.schema["columns"], sort=self.schema["columns"]
            )
            capabilities["scientific_adapter"] = self._record_panel in (
                "activity_context",
                "literature",
                "bioactivities",
                "chemical_classification",
                "coverage",
                "ligand_site_comparisons",
                "quaternary_interpretation",
                "assembly_generation",
            )
        if self._selection._scientific is not None:
            capabilities.update(
                scientific_adapter=True,
                filter=self.schema["columns"],
                sort=[
                    c for c in self.schema["columns"] if c not in ("chains", "state")
                ],
            )
        if self._machine_ref is not None:
            capabilities["root_machine_selection_ref"] = self._machine_ref
        if self._record_panel == "sequence_changes":
            from .card_sequence_change_dispatch import selection

            SORT_COLUMNS = selection(self).SORT_COLUMNS

            capabilities["sort"] = list(SORT_COLUMNS)
        if self._record_panel == "protein_context":
            capabilities["sort"] = list(self.schema["columns"])
        if self._record_panel == "literature":
            capabilities["sort"] = list(self.schema["columns"])
        if self._record_panel == "clinical":
            if self._explorer.mode == "saved":
                from ._clinical_history_v1.selection import SORT_COLUMNS
            else:
                from .card_clinical_selection_v1 import SORT_COLUMNS

            capabilities["sort"] = list(SORT_COLUMNS)
        if self._explorer.mode == "saved":
            from .card_exploration_storage import operation_key

            keys = [operation_key(CardItem(self, entry)) for entry in self._selected]
            capabilities["explain"] = bool(keys) and all(
                key in self._explorer._session["explanations"] for key in keys
            )
            capabilities["related"] = bool(keys) and all(
                key in self._explorer._session["links"] for key in keys
            )
            from .card_exploration_molecule_activity import is_view

            if self._explorer._session.get("format") in (
                "sabueso.card_exploration@21",
                "sabueso.card_exploration@23",
                "sabueso.card_exploration@25",
                "sabueso.card_exploration@27",
                "sabueso.card_exploration@29",
                "sabueso.card_exploration@31",
                "sabueso.card_exploration@33",
                "sabueso.card_exploration@35",
            ) and is_view(self):
                from .card_molecule_activity_operations_v1 import has_operation

                capabilities["explain"] = has_operation(self, "explanations")
                capabilities["related"] = has_operation(self, "links")
        return capabilities

    @property
    def schema(self):
        if self._saved_state is not None:
            return deepcopy(self._saved_state["schema"])
        if self._record_panel == "protein_context":
            from .card_protein_context_dispatch import selection

            COLUMNS = selection(self).COLUMNS

            return {
                "kind": "protein_context_exploration",
                "grain": "retained relationship or explicit captured comparison",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "sequence_changes":
            from .card_sequence_change_dispatch import selection

            COLUMNS = selection(self).COLUMNS

            return {
                "kind": "sequence_change_exploration",
                "grain": "one original natural-variant or mutagenesis occurrence",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "variants":
            if self._explorer.mode == "saved":
                from ._variant_history_v1.selection import COLUMNS
            else:
                from .card_variant_selection_v1 import COLUMNS

            return {
                "kind": "variant_tissue_context_exploration",
                "grain": "native population-variant or isoform occurrence",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "associations":
            if self._explorer.mode == "saved":
                from ._disease_association_history_v1.selection import COLUMNS
            else:
                from .card_disease_association_selection_v1 import COLUMNS

            return {
                "kind": "disease_association_exploration",
                "grain": "one original association/indication/condition occurrence or input context",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "clinical":
            if self._explorer.mode == "saved":
                from ._clinical_history_v1.selection import COLUMNS
            else:
                from .card_clinical_selection_v1 import COLUMNS

            return {
                "kind": "clinical_exploration",
                "grain": "separate molecule phase, indication, cited-trial occurrence and registry record",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "activity_context":
            from .card_molecule_activity_selection_v1 import COLUMNS

            return {
                "kind": "molecule_activity_context",
                "grain": "one exact supplied target context, native group or source activity record under explicit molecule identity",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "literature":
            from .card_literature_selection_v1 import COLUMNS

            return {
                "kind": "literature_exploration",
                "grain": "one exact native publication identity on the focal captured Card",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "bioactivities":
            from .card_bioactivity_selection_v1 import COLUMNS

            return {
                "kind": "bioactivity_exploration",
                "grain": "one original molecule, native measurement group or source activity record for the exact focused request",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "chemical_classification":
            from .card_chemical_selection_v1 import COLUMNS

            return {
                "kind": "chemical_classification",
                "grain": "one retained original field-member position, including duplicates",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "assembly_generation":
            from .card_assembly_selection_v1 import COLUMNS

            return {
                "kind": "assembly_generation_finding",
                "grain": "one original generator, unavailable source/parent scope, acquisition gap or unplaced declaration",
                "columns": list(COLUMNS),
                "presentations": ["summary", "table", "detail"],
            }
        if self._record_panel == "quaternary_interpretation":
            from .card_quaternary_exploration import COLUMNS

            return {
                "kind": "quaternary_interpretation",
                "grain": "one retained interface classification or one interface/family-annotation pair",
                "columns": ["label", "kind", *COLUMNS],
                "presentations": ["summary", "table", "detail"],
            }
        if self._field_panel == "quaternary_structure":
            from .card_quaternary_source_v1 import COLUMNS, SELECT

            return {
                "kind": "quaternary_source_statement",
                "grain": "one original subunit field, structure-local assembly record or interface relationship",
                "columns": list(COLUMNS),
                "selection_columns": list(SELECT),
                "presentations": ["summary", "table"],
            }
        if (
            self._explorer.mode == "saved"
            and self._record_panel == "ligand_site_comparisons"
        ):
            from .card_exploration_sites import HUMAN_SCHEMA

            return deepcopy(HUMAN_SCHEMA)
        if self._explorer.mode == "saved":
            from .card_exploration_adapter_v1 import (
                COVERAGE_HUMAN_SCHEMA,
                STRUCTURE_HUMAN_SCHEMA,
            )

            if self._selection._scientific is not None:
                return deepcopy(STRUCTURE_HUMAN_SCHEMA)
            if self._record_panel == "coverage":
                return deepcopy(COVERAGE_HUMAN_SCHEMA)
        if self._field_panel == "annotated_regions":
            return {
                "kind": "annotation",
                "grain": "one original positional annotation",
                "columns": [
                    "label",
                    "kind",
                    "feature_type",
                    "sequence_ref",
                    "start",
                    "end",
                    "context_state",
                    "value",
                    "type",
                ],
                "selection_columns": [
                    "label",
                    "kind",
                    "feature_type",
                    "sequence_ref",
                    "start",
                    "end",
                    "context_state",
                ],
                "presentations": ["summary", "table"],
            }
        if self._link_panel:
            return {
                "kind": "link",
                "grain": "one retained destination role",
                "columns": ["label", "kind", "role", "target_ref", "availability"],
                "presentations": ["summary", "table"],
            }
        if self._record_panel:
            from .card_exploration_profiles import RECORD_COLUMNS

            return {
                "kind": "ligand_contact_comparison"
                if self._record_panel == "ligand_site_comparisons"
                else "knowledge_state"
                if self._record_panel == "coverage"
                else "relationship",
                "grain": "one retained protein–ligand contact declaration, not a physical ligand occurrence"
                if self._record_panel == "ligand_site_comparisons"
                else "one original source/area classification row"
                if self._record_panel == "coverage"
                else "one retained parent relationship",
                "columns": ["label", "kind", *RECORD_COLUMNS[self._record_panel]],
                "presentations": ["summary", "table"],
            }
        if self._selection._scientific is not None:
            from .card_scientific_access import COLUMNS

            return {
                "kind": "structure",
                "grain": "one retained structural inventory entry",
                "columns": ["label", "kind", *COLUMNS],
                "presentations": ["summary", "table", "detail"],
                "quantity_expectations": {
                    "resolution": {
                        "field": "relationships.has_structure.resolution",
                        "unit": "angstrom",
                    }
                },
            }
        from .quantities import FIELD_UNITS

        return {
            "kind": "field"
            if self._field_panel
            else "route"
            if self._route_catalog
            else "literal",
            "grain": "one original model relationship"
            if self._field_panel == "predicted_structures"
            else "one original instance within a structure ligand declaration"
            if self._field_panel == "ligand_instances"
            else "one original functional-site field or contact relationship"
            if self._field_panel == "sites"
            else "one original sequence or positional-annotation field"
            if self._field_panel == "sequence"
            else "one retained field or source-stated identity statement"
            if self._field_panel == "chemistry"
            else f"one retained {self._explorer.profile} field"
            if self._field_panel
            else "retained literal nodes, or navigation catalog entries",
            "columns": [
                "label",
                "kind",
                "structure_ref",
                "component_id",
                "instance_id",
                "value",
                "type",
            ]
            if self._field_panel == "ligand_instances"
            else ["label", "kind", "value", "type"],
            "presentations": ["summary", "table"],
            "selection_columns": [
                "label",
                "kind",
                "structure_ref",
                "component_id",
                "instance_id",
            ]
            if self._field_panel == "ligand_instances"
            else ["label", "kind"],
            **(
                {
                    "quantity_expectations": {
                        path: {"field": path, "unit": unit}
                        for path, unit in FIELD_UNITS.items()
                        if path.startswith(
                            "properties.physchem."
                            if self._field_panel == "properties"
                            else "sequence."
                        )
                    }
                }
                if self._field_panel in ("properties", "sequence")
                else {}
            ),
        }

    @property
    def exclusions(self):
        """Original excluded/unplaced declarations, separate from display filtering."""
        if self._record_panel == "chemical_classification":
            # Every retained chemical member is kept, including unsupported ones.
            return []
        return (
            deepcopy(self._selection._scientific.wire["exclusions"])
            if self._selection._scientific is not None
            else []
        )

    @property
    def native_payload(self):
        if self._native_override is not None:
            return deepcopy(self._native_override)
        if self._selection._scientific is not None:
            result = self._selection._scientific
            return deepcopy(
                result.native_item(self._focus)
                if self._focus is not None
                else result.native
            )
        return deepcopy(
            self._explorer.access._resolve(self._selection._target["location"])[0]
        )

    def items(self):
        return CardItems(self)

    def rows(self):
        """Explicit complete selected rows, including unabridged typed values."""
        return [
            {
                "item_ref": item.item_ref,
                "kind": item.kind,
                "label": item.label,
                "cells": {key: cell.to_dict() for key, cell in item.cells.items()},
                "support": item.support,
                "payload_location": item.payload_location,
            }
            for item in self.items()
        ]

    @arg_digest()
    def item(self, item_ref, skip_digestion=False):
        """Find an exact original item, including one hidden by a display filter."""
        for entry in self._selection._entries:
            item = self._item(entry)
            if item.item_ref == item_ref:
                return item
        raise ArgumentError("This item reference does not belong to this result.")

    @arg_digest()
    def follow(self, item_ref, skip_digestion=False):
        """Open an exact link in this result, including display-filtered links."""
        if not self._link_panel:
            raise ArgumentError("follow requires a link view.")
        return self.item(item_ref).open()

    @arg_digest()
    def filter(self, column, *, equals, skip_digestion=False):
        """Select exact declared cells without changing the scientific result."""
        self._check_column(column)
        if self._record_panel == "protein_context":
            from .card_protein_context_dispatch import presentation

            display_filter = presentation(self).display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "sequence_changes":
            from .card_sequence_change_dispatch import presentation

            display_filter = presentation(self).display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "variants":
            if self._explorer.mode == "saved":
                from .card_exploration_variant import display_filter

                return display_filter(self, column, equals)
            from .card_variant_exploration import display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "associations":
            if self._explorer.mode == "saved":
                from .card_exploration_disease_association import display_filter

                return display_filter(self, column, equals)
            from .card_disease_association_exploration import display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "clinical":
            if self._explorer.mode == "saved":
                from .card_exploration_clinical import display_filter
            else:
                from .card_clinical_exploration import display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "activity_context":
            if self._explorer.mode == "saved":
                from .card_exploration_molecule_activity import display_filter
            else:
                from .card_molecule_activity_exploration import display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "literature":
            if self._explorer.mode == "saved":
                from .card_exploration_literature import display_filter
            else:
                from .card_literature_exploration import display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "bioactivities":
            if self._explorer.mode == "saved":
                from .card_bioactivity_dispatch import binding

                display_filter = binding(self._explorer.access).display_filter
            else:
                from .card_bioactivity_exploration import display_filter

            return display_filter(self, column, equals)
        if self._record_panel == "chemical_classification":
            from .card_chemical_presentation_v1 import display_filter

            return display_filter(self, column, equals)
        from .card_display_filter_v2 import RULE, legacy_verification

        legacy = legacy_verification()
        if self._record_panel == "assembly_generation":
            from .card_assembly_dispatch import presentation

            if not legacy and self._status not in ("ok", "empty"):
                raise ArgumentError(
                    f"Display filtering is unavailable for this assembly view with status={self._status}; inspect its retained items and original scope."
                )
            return presentation(self).display_filter(self, column, equals)
        scientific = (
            self._selection._scientific is not None
            and self._record_panel
            not in ("ligand_site_comparisons", "quaternary_interpretation")
        )
        if scientific:
            if self._explorer.mode == "saved":
                from .card_exploration_adapter_v1 import (
                    _validate_equality as validate_equality,
                )
            else:
                from .card_scientific_access import validate_equality

            validate_equality(column, equals)
        elif self._record_panel == "coverage" and column == "count":
            import math

            if type(equals) not in (int, float) or not math.isfinite(equals):
                raise ArgumentError(
                    "count equality requires a finite number, not a boolean."
                )
        elif not isinstance(equals, str):
            raise ArgumentError("This column requires string equality.")
        unavailable = self._status not in ("ok", "empty") and not (
            self._link_panel and self._status == "ambiguous"
        )
        retained_filter = unavailable and not legacy
        if unavailable:
            if legacy:
                return replace(self, _origin=self)
            if not self._selection._entries:
                raise ArgumentError(
                    f"Cannot filter a view with status={self._status} and no retained rows; inspect its outcome and original scope."
                )
        if (
            self._record_panel
            in ("ligand_site_comparisons", "quaternary_interpretation")
            or self._field_panel == "quaternary_structure"
        ):

            def equal_values(column, first, second):
                return (
                    isinstance(first, str)
                    and isinstance(second, str)
                    and first == second
                )
        elif self._explorer.mode == "saved":
            from .card_exploration_adapter_v1 import _equal_values as equal_values
        else:
            from .card_scientific_access import equal_values

        entries = tuple(
            item._entry
            for item in self.items()
            if item.cells[column].state in ("present", "conflicting")
            and equal_values(column, item.cells[column]._value, equals)
        )
        return replace(
            self,
            _selected=entries,
            _origin=self,
            _status=self._status
            if retained_filter
            else ("ambiguous" if self._status == "ambiguous" else "ok")
            if entries
            else "empty",
            _reason=self._reason
            if retained_filter
            else None
            if entries
            else "No items match this display selection.",
            _display_request={
                "operation": "filter",
                "column": column,
                "equals": deepcopy(equals),
                **({"filter_policy": RULE} if retained_filter else {}),
            },
        )

    @arg_digest()
    def sort(self, column, descending=False, skip_digestion=False, *, unit=None):
        """Sort declared scalar cells with missing values last and explicit units."""
        self._check_column(column)
        if type(descending) is not bool:
            raise ArgumentError("descending must be True or False.")
        if unit is not None and (not isinstance(unit, str) or not unit.strip()):
            raise ArgumentError("unit requires a nonempty unit name or None.")
        if self._record_panel == "protein_context":
            from .card_protein_context_dispatch import presentation

            display_sort = presentation(self).display_sort

            return display_sort(self, column, descending, unit)
        if self._record_panel == "sequence_changes":
            from .card_sequence_change_dispatch import presentation

            display_sort = presentation(self).display_sort

            return display_sort(self, column, descending, unit)
        if self._record_panel == "variants":
            if self._explorer.mode == "saved":
                from .card_exploration_variant import display_sort

                return display_sort(self, column, descending, unit)
            from .card_variant_exploration import display_sort

            return display_sort(self, column, descending, unit)
        if self._record_panel == "associations":
            if self._explorer.mode == "saved":
                from .card_exploration_disease_association import display_sort

                return display_sort(self, column, descending, unit)
            from .card_disease_association_exploration import display_sort

            return display_sort(self, column, descending, unit)
        if self._record_panel == "clinical":
            if self._explorer.mode == "saved":
                from .card_exploration_clinical import display_sort
            else:
                from .card_clinical_exploration import display_sort

            return display_sort(self, column, descending, unit)
        if self._record_panel == "activity_context":
            if self._explorer.mode == "saved":
                from .card_exploration_molecule_activity import display_sort
            else:
                from .card_molecule_activity_exploration import display_sort

            return display_sort(self, column, descending, unit)
        if self._record_panel == "literature":
            if self._explorer.mode == "saved":
                from .card_exploration_literature import display_sort
            else:
                from .card_literature_exploration import display_sort

            return display_sort(self, column, descending, unit)
        if self._record_panel == "bioactivities":
            if self._explorer.mode == "saved":
                from .card_bioactivity_dispatch import binding

                display_sort = binding(self._explorer.access).display_sort
            else:
                from .card_bioactivity_exploration import display_sort

            return display_sort(self, column, descending, unit)
        if self._selection._scientific is not None and self._explorer.mode == "saved":
            from .card_exploration_adapter_v1 import _sorted_entries as sorted_entries
        else:
            from .card_scientific_access import sorted_entries

        if self._record_panel or self._link_panel:
            if unit is not None:
                raise ArgumentError("These record columns do not take a quantity unit.")
            present, missing = [], []
            for item in self.items():
                value = item.cells[column]._value
                (missing if value is None else present).append((value, item._entry))
            present.sort(key=lambda pair: pair[0], reverse=descending)
            entries = tuple(entry for _, entry in [*present, *missing])
        else:
            entries = sorted_entries(self, column, descending, unit)
        return replace(
            self,
            _selected=entries,
            _origin=self,
            _display_request={
                "operation": "sort",
                "column": column,
                "descending": descending,
                "unit": unit,
            },
        )

    def _check_column(self, column):
        if (
            not isinstance(column, str)
            or column not in self.schema["columns"]
            or (
                self._selection._scientific is None
                and not self._record_panel
                and not self._link_panel
                and column
                not in self.schema.get("selection_columns", ("label", "kind"))
            )
        ):
            raise ArgumentError(
                f"Available selection columns: {self.capabilities['filter']}."
            )

    def _can_save(self):
        from .card_exploration_storage import can_save

        return can_save(self)

    @arg_digest()
    def save(
        self,
        path,
        *,
        overwrite=False,
        compression="none",
        max_encoded_bytes=67108864,
        max_decoded_bytes=67108864,
        max_logical_bytes=268435456,
        skip_digestion=False,
    ):
        """Save supported retained views and their original captured context atomically."""
        from .card_exploration_storage import save_exploration

        return save_exploration(
            self,
            path,
            overwrite=overwrite,
            compression=compression,
            max_encoded_bytes=max_encoded_bytes,
            max_decoded_bytes=max_decoded_bytes,
            max_logical_bytes=max_logical_bytes,
        )

    def summary(self):
        return replace(
            self,
            presentation="summary",
            _origin=self,
            _display_request={"operation": "presentation"},
        )

    def table(self):
        return replace(
            self,
            presentation="table",
            _origin=self,
            _display_request={"operation": "presentation"},
        )

    def back(self):
        return self if self.at_root else self._origin

    def __repr__(self):
        from .card_exploration_render import render_text

        return render_text(self)

    def _repr_html_(self):
        from .card_exploration_render import render_html

        return render_html(self)


class CardExplorer:
    """Readable focal Card inspection with the exact same capture as ``access``.

    Start with ``overview()`` or ``topics()``. This generic first slice supports
    every valid Card nature; proteins also have function fields, structural views
    and explicit scientific questions. Navigation opens only captured destinations.
    """

    __slots__ = (
        "_access",
        "_coverage_result",
        "_origin",
        "_navigation_cache",
        "_session",
    )

    @arg_digest()
    def __init__(self, card, related_cards=(), skip_digestion=False):
        self._access = CardAccess(card, related_cards)
        self._coverage_result = None
        self._origin = None
        self._navigation_cache = {}
        from .card_navigation_preview_v1 import metadata

        self._session = {
            "views": {},
            "explanations": {},
            "links": {},
            "presentation_metadata": metadata(),
        }
        self._access._exploration_session = self._session

    @property
    def access(self):
        return self._access

    @property
    def profile(self):
        return self.access.profile

    @property
    def mode(self):
        return self.access.mode

    @property
    def context(self):
        return self.access.context

    @property
    def capabilities(self):
        capabilities = {
            "region_workload": self.access.capabilities["region_workload"],
            "topics": list(self._topics),
            "inspect": True,
            "search": "literal_casefold",
            "scientific_questions": bool(self._questions),
            "question_keys": list(self._questions),
            "scientific_topics": [*self._nature_topics, "coverage"]
            if self._nature_topics
            else [],
            "cross_card_navigation": True,
            "save": True,
        }
        capabilities["scientific_topics"].append("literature")

        if self.mode == "saved":
            views = [
                view
                for view in self._session["views"].values()
                if view._saved_state is not None
                and view._explorer.access._focal_key == self.access._focal_key
            ]
            topics = {
                view._field_panel
                for view in views
                if view._field_panel in self._nature_topics
                and view._field_panel is not None
            }
            topics.update(
                view._record_panel
                for view in views
                if view._record_panel
                in (
                    "activity_context",
                    "clinical",
                    "associations",
                    "variants",
                    "bioactivities",
                    "literature",
                    "chemical_classification",
                    "classification",
                    "coverage",
                    "ligand_site_comparisons",
                    "quaternary_interpretation",
                )
            )
            if "chemical_classification" in topics:
                topics.remove("chemical_classification")
                topics.add("classification")
            from .card_structure_selection_v1 import original

            if any(
                original(view._selection)
                and view._selection._scientific.wire["context"]["adapter"]
                == "structure_exploration@1"
                for view in views
            ):
                topics.add("structures")
            questions = {
                view.request["question"] for view in views if view.request is not None
            }
            capabilities.update(
                scientific_topics=sorted(topics),
                question_keys=sorted(questions),
                scientific_questions=bool(questions),
                not_saved_topics=sorted(
                    set(capabilities["scientific_topics"]) - topics
                ),
            )
        return capabilities

    def start_new(self):
        """Start a new local interpretation from the captures, without source access."""
        from .card_exploration_storage import start_new

        return start_new(self)

    @property
    def _nature_topics(self):
        if (
            self.mode == "saved"
            and self._session.get("format") == "sabueso.card_exploration@35"
        ):
            from ._knowledge_comparison_history_v1.catalogs import NATURE_TOPICS

            return NATURE_TOPICS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._protein_context_history_v1.catalogs import NATURE_TOPICS

            return NATURE_TOPICS.get(self.profile, ())
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._sequence_change_history_v1.catalogs import NATURE_TOPICS

            return NATURE_TOPICS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@29",
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._variant_history_v1.catalogs import NATURE_TOPICS

            return NATURE_TOPICS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@27",
            "sabueso.card_exploration@29",
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._disease_association_history_v1.catalogs import NATURE_TOPICS

            return NATURE_TOPICS.get(self.profile, ())
        if (
            self.mode == "saved"
            and self._session.get("format") == "sabueso.card_exploration@25"
        ):
            from ._clinical_history_v1.catalogs import NATURE_TOPICS

            return NATURE_TOPICS.get(self.profile, ())
        from .card_exploration_profiles import NATURE_TOPICS

        topics = NATURE_TOPICS.get(self.profile, ())
        return (
            (
                *topics,
                "variants",
                "sequence_changes",
                "comparative_context",
                "associations",
            )
            if self.mode == "live" and self.profile == "protein"
            else topics
        )

    @property
    def _topics(self):
        if (
            self.mode == "saved"
            and self._session.get("format") == "sabueso.card_exploration@35"
        ):
            from ._knowledge_comparison_history_v1.catalogs import TOPICS

            return TOPICS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._protein_context_history_v1.catalogs import TOPICS

            return TOPICS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._sequence_change_history_v1.catalogs import TOPICS

            return TOPICS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@29",
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._variant_history_v1.catalogs import TOPICS

            return TOPICS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@27",
            "sabueso.card_exploration@29",
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._disease_association_history_v1.catalogs import TOPICS

            return TOPICS[self.profile]
        if (
            self.mode == "saved"
            and self._session.get("format") == "sabueso.card_exploration@25"
        ):
            from ._clinical_history_v1.catalogs import TOPICS

            if self.profile in TOPICS:
                return TOPICS[self.profile]
        keys = (
            (
                *self._nature_topics,
                "literature",
                "sources",
                "coverage",
                "quality",
                "content",
            )
            if self._nature_topics
            else ("literature", "sources", "coverage", "content")
        )
        return {
            key: (
                "Coverage and quality records",
                "Original stored quality records; source knowledge coverage is not evaluated.",
            )
            if key == "coverage" and not self._nature_topics
            else (
                "Chemical classes and source-stated roles",
                "Retained classes, direct/inherited roles and original source support; no therapeutic inference.",
            )
            if key == "classification" and self.profile == "small_molecule"
            else (
                "Protein biological associations",
                "Original disease, pathway and interaction records; source channels and recorded direction stay distinct.",
            )
            if key == "associations"
            and self.profile == "protein"
            and self.mode == "live"
            else _TOPICS[key]
            for key in keys
        }

    def _topic_label(self, topic):
        if (
            self.mode == "saved"
            and self._session.get("format") == "sabueso.card_exploration@35"
            and self.profile == "protein"
        ):
            from ._knowledge_comparison_history_v1.catalogs import PROTEIN_LABELS

            return PROTEIN_LABELS[topic]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@27",
            "sabueso.card_exploration@29",
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            return self._topics[topic][0]
        if topic == "classification" and self.profile == "small_molecule":
            return self._topics[topic][0]
        return (
            "Coverage and quality records"
            if topic == "coverage" and not self._nature_topics
            else _TOPICS[topic][0]
        )

    @property
    def _questions(self):
        if (
            self.mode == "saved"
            and self._session.get("format") == "sabueso.card_exploration@35"
        ):
            from ._knowledge_comparison_history_v1.catalogs import QUESTIONS

            return QUESTIONS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._protein_context_history_v1.catalogs import QUESTIONS

            return QUESTIONS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._sequence_change_history_v1.catalogs import QUESTIONS

            return QUESTIONS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@29",
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._variant_history_v1.catalogs import QUESTIONS

            return QUESTIONS[self.profile]
        if self.mode == "saved" and self._session.get("format") in (
            "sabueso.card_exploration@27",
            "sabueso.card_exploration@29",
            "sabueso.card_exploration@31",
            "sabueso.card_exploration@33",
            "sabueso.card_exploration@35",
        ):
            from ._disease_association_history_v1.catalogs import QUESTIONS

            return QUESTIONS[self.profile]
        if (
            self.mode == "saved"
            and self._session.get("format") == "sabueso.card_exploration@25"
        ):
            from ._clinical_history_v1.catalogs import QUESTIONS

            if self.profile in QUESTIONS:
                return QUESTIONS[self.profile]
        from .card_exploration_profiles import COMMON_QUESTIONS, QUESTIONS

        result = {**QUESTIONS.get(self.profile, {}), **COMMON_QUESTIONS}
        if self.mode == "live" and self.profile == "protein":
            for question, label in (
                (
                    "variant_tissue_context",
                    "What tissue context is retained for population variants?",
                ),
                (
                    "isoform_tissue_context",
                    "What tissue context is retained for individual isoforms?",
                ),
            ):
                result[question] = {
                    "label": label,
                    "topic": "variants",
                    "required_options": [],
                    "scope": "Original scoped native rules, genomic/transcript/CDS context and per-tissue unknowns; no clinical inference or acquisition.",
                }
        if self.mode == "live" and self.profile == "protein":
            result["sequence_changes"] = {
                "label": "Which natural variants and experimental sequence changes are retained?",
                "topic": "sequence_changes",
                "required_options": [],
                "scope": "Original annotation occurrences, substitutions and source support; no genomic correspondence or clinical inference.",
            }
        if self.mode == "live" and self.profile == "protein":
            for key, topic, label, required in (
                (
                    "related_proteins",
                    "comparative_context",
                    "Which comparative relationships and supplied proteins are retained?",
                    [],
                ),
                (
                    "protein_associations",
                    "associations",
                    "Which disease, pathway and interaction relationships are retained?",
                    [],
                ),
                (
                    "sequence_differences",
                    "comparative_context",
                    "How do these explicitly supplied captured sequences differ at equal positions?",
                    ["other_ref"],
                ),
            ):
                result[key] = {
                    "label": label,
                    "topic": topic,
                    "required_options": required,
                    "scope": "Captured records and explicit inputs; no identity, coordinate correspondence or causality inference.",
                }
        return result

    def _location(self, *keys):
        return self.access._card_location(segments=[_key(key) for key in keys])

    def _inspect(self, location, origin=None, *, title="All retained content"):
        node, full = self.access._resolve(location)
        origin = self._origin if origin is None else origin
        if full["kind"] == "card" and (
            full["card_ref"] != self.context["card_ref"]
            or full["snapshot_id"] != self.context["snapshot_id"]
        ):
            raise ArgumentError(
                "Inspection is limited to the focal capture; open a related link to switch context explicitly."
            )
        selection = self.access.read(full)
        request = None
        if self.mode == "live":
            from .card_sequence_change_exploration import inherited_request

            request = inherited_request(origin)
            if request is None:
                from .card_protein_context_exploration import (
                    inherited_request as protein_request,
                )

                request = protein_request(origin)
        return CardView(
            self,
            selection,
            selection._entries,
            title,
            origin,
            _request=request,
            _status="ok" if selection.count else "empty",
            _reason=None if selection.count else "This retained container is empty.",
        )

    def _metadata(self, value, title, origin=None):
        return self._inspect(self.access._object_location(value), origin, title=title)

    def overview(self):
        """Readable opening with recorded identity and explicit navigation routes."""
        if self._nature_topics:
            return replace(self.topics(), title="Card overview")
        return self._inspect(self.access.root_location, title="Card overview")

    def topics(self):
        """Only delivered routes; no unavailable scientific panels are advertised."""
        descriptors = {
            key: {"description": value[1]} for key, value in self._topics.items()
        }
        if self.mode == "saved":
            missing = set(self.capabilities["not_saved_topics"])
            for key, descriptor in descriptors.items():
                descriptor["availability"] = (
                    "not_saved" if key in missing else "retained"
                )
        result = self._metadata(descriptors, "Where would you like to explore?")
        order = tuple(self._topics)
        return replace(
            result,
            _route_catalog=True,
            _selected=tuple(
                sorted(result._selected, key=lambda entry: order.index(entry.key))
            ),
        )

    def questions(self):
        """Delivered question routes, their scope and required explicit inputs."""
        if self.mode == "live" and "knowledge_differences" in self._questions:
            self._session["pending_knowledge_catalog"] = True
        if self._questions:
            result = self._metadata(self._questions, "Scientific questions")
            order = tuple(self._questions)
            return replace(
                result,
                _selected=tuple(
                    sorted(result._selected, key=lambda entry: order.index(entry.key))
                ),
                _route_catalog=True,
                _question_catalog=True,
            )
        return replace(
            self._metadata({}, "Scientific questions"),
            _status="unsupported",
            _reason="Scientific question adapters are not implemented. Use topics() or inspect().",
        )

    def _topic(self, topic, origin=None, options=None):
        if self.mode == "saved" and topic == "assembly_generation":
            from .card_assembly_dispatch import saved_human

            return saved_human(self, options, origin, question=False)
        if self.mode == "saved":
            from .card_exploration_storage import saved_topic

            return saved_topic(self, topic, origin, options)
        result = self._live_topic(topic, origin, options)
        parent = self._origin if origin is None else origin
        if parent is not None and parent._link_panel:
            from .card_exploration_disease_association import scientific_transition

            return scientific_transition(self, result, topic, origin)
        return result

    def _live_topic(self, topic, origin=None, options=None):
        origin = self._origin if origin is None else origin
        if not isinstance(topic, str):
            raise ArgumentError("topic requires a declared topic key.")
        if options is not None and not isinstance(options, dict):
            raise ArgumentError("Scientific options require a mapping or None.")
        from .card_exploration_profiles import PANELS

        if (
            topic == "comparative_context"
            or topic == "associations"
            and self.profile == "protein"
        ):
            from .card_protein_context_exploration import view

            return view(self, topic, origin, options)
        if topic == "sequence_changes":
            from .card_sequence_change_exploration import view

            return view(self, origin, options)
        if topic == "variants":
            from .card_variant_exploration import view

            return view(self, origin, options)
        if topic == "associations":
            from .card_disease_association_exploration import view

            return view(self, origin, options)
        if topic == "clinical":
            from .card_clinical_exploration import view

            return view(self, origin, options)
        if topic == "activity_context":
            from .card_molecule_activity_exploration import view

            return view(self, origin, options)
        if topic == "literature":
            from .card_literature_exploration import view

            return view(self, origin, options)
        if topic == "bioactivities":
            from .card_bioactivity_exploration import view

            return view(self, origin, options)
        if topic == "assembly_generation":
            from .card_assembly_dispatch import options_for_assembly, view

            return view(self, origin, options_for_assembly(options))
        if topic == "quaternary_interpretation":
            from .card_quaternary_access import options_for_quaternary
            from .card_quaternary_exploration import view

            options_for_quaternary(options)
            return view(self, origin)
        if topic == "ligand_site_comparisons":
            if options not in (None, {}):
                raise ArgumentError(
                    "ligand_site_comparisons has no scientific options."
                )
            from .card_ligand_site_exploration import view

            return view(self, origin)
        if topic in PANELS:
            if options not in (None, {}):
                raise ArgumentError(f"{topic} has no scientific options.")
            return self._field_view(topic, origin)
        if topic == "classification":
            if options not in (None, {}):
                raise ArgumentError("classification has no scientific options.")
            if self.profile == "small_molecule":
                from .card_chemical_exploration import view

                return view(self, origin)
            return self._classification(origin)
        if topic == "coverage" and self._nature_topics:
            if options not in (None, {}):
                raise ArgumentError("coverage has no scientific options.")
            from .card_coverage_exploration import view

            return view(self, origin)
        if topic == "structures":
            selection = self.access.select(topic, options=options)
            result = selection._scientific
            return CardView(
                self,
                selection,
                selection._entries,
                "Experimental structures",
                origin,
                _status=result.wire["outcome"]["status"],
                _reason=result.wire["outcome"]["reason"],
            )
        if options not in (None, {}):
            raise ArgumentError("Scientific options are valid only for structures.")
        if not isinstance(topic, str) or topic not in self._topics:
            raise ArgumentError(f"Available topics: {', '.join(_TOPICS)}.")
        location = {
            "content": self.access.root_location,
            "sources": self._location("source_assertion_store"),
            "coverage": self._location("quality"),
            "quality": self._location("quality"),
        }[topic]
        return self._inspect(location, origin, title=self._topic_label(topic))

    def _field_view(self, topic, origin):
        from .card_exploration_profiles import PANELS, field_entries

        nature = PANELS[topic][0]
        from .card_annotation_regions_v1 import SCOPE as ANNOTATION_SCOPE
        from .card_ligand_instances_v1 import SCOPE as INSTANCE_SCOPE
        from .card_protein_source_v1 import SCOPES
        from .card_quaternary_source_v1 import SCOPE as QUATERNARY_SCOPE

        applicable = self.profile == nature
        entries, gaps = field_entries(self, topic) if applicable else ((), [])
        result = self._metadata(
            {
                "adapter": "protein_function_fields@1"
                if topic == "function"
                else f"{topic}_fields@1",
                "context": self.context,
                "fields": {entry.key: entry.value for entry in entries},
                "field_gaps": gaps,
                "scope": ANNOTATION_SCOPE
                if topic == "annotated_regions"
                else INSTANCE_SCOPE
                if topic == "ligand_instances"
                else QUATERNARY_SCOPE
                if topic == "quaternary_structure"
                else SCOPES[topic]
                if topic in SCOPES
                else "Retained fields only; no function is inferred from a name. Source coverage is not evaluated."
                if topic == "function"
                else "Retained source statements only; no chemical calculation, diagnosis or identity inference. Source coverage is not evaluated.",
            },
            _TOPICS[topic][0],
            origin,
        )
        return replace(
            result,
            _selection=replace(result._selection, _entries=entries),
            _selected=entries,
            _field_panel=topic,
            _status="not_applicable"
            if not applicable
            else "missing_prerequisite"
            if topic
            in ("predicted_structures", "ligand_instances", "quaternary_structure")
            and any(row["state"] == "missing_prerequisite" for row in gaps)
            else "ok"
            if entries
            else "empty",
            _reason=f"The {topic} route requires a {nature} Card."
            if not applicable
            else "A consistent captured protein identity is required to select structure/model relationships; inspect original identity and quality records."
            if topic
            in ("predicted_structures", "ligand_instances", "quaternary_structure")
            and any(row["state"] == "missing_prerequisite" for row in gaps)
            else "Function description has no supported retained field value; inspect field_gaps and the original content."
            if topic == "function"
            and any(row["field"] == "annotations.function" for row in gaps)
            else "Some source declarations are missing, empty or unrecognized; original records and source coverage remain available."
            if topic == "quaternary_structure" and gaps
            else "Only retained values are shown; inspect field_gaps for missing or unsupported fields."
            if gaps
            else None,
        )

    def _classification(self, origin):
        nature = self.profile == "disease"
        card_id = self.access._focal.data.get("meta", {}).get("card_id")
        focal = (
            card_id.removeprefix("sabueso:disease:")
            if isinstance(card_id, str) and card_id.startswith("sabueso:disease:")
            else None
        )
        parent = self._location("relationship_store")
        entries = tuple(
            entry
            for entry in self.access._children(
                self.access._focal.data["relationship_store"], parent
            )
            if nature
            and focal
            and entry.value["predicate"] == "subclass_of"
            and entry.value["subject_ref"] == focal
        )
        result = self._metadata(
            {
                "adapter": "disease_classification_fields@1",
                "context": self.context,
                "focal_ref": focal,
                "relationships": [entry.value for entry in entries],
                "identity_route": "identity",
                "scope": "Exact focal-subject stored parent relationships only; no parent Card is opened or fetched.",
            },
            "Disease classification",
            origin,
        )
        return replace(
            result,
            _selection=replace(result._selection, _entries=entries),
            _selected=entries,
            _record_panel="classification",
            _status="not_applicable"
            if not nature
            else "missing_prerequisite"
            if not focal
            else "ok"
            if entries
            else "empty",
            _reason="This route requires a disease Card."
            if not nature
            else "A focal disease identity is required."
            if not focal
            else "Parent term Cards were not opened. Identity terminology: explorer.view('identity'); equivalence and related xrefs are separate from parent edges.",
        )

    @receiving
    @arg_digest()
    def view(
        self,
        topic,
        skip_digestion=False,
        *,
        options=None,
        region_budget=DEFAULT_REGION_BUDGET,
    ):
        """Open a delivered topic by its catalog key.

        ``region_budget`` bounds raw region terms and distinct positions (default
        100,000); a positive integer changes it, and None removes this workload
        ceiling. Scientific/reference checks remain. The view's ``workload``
        receipt records this invocation separately from scientific result identity.
        """
        from .region_requests import prepare_options

        options = prepare_options(self.access, topic, options)
        return self._topic(topic, options=options)

    def _answer(self, question, options, origin=None):
        if self.mode == "saved" and question == "assembly_generation":
            from .card_assembly_dispatch import saved_human

            return saved_human(self, options, origin, question=True)
        if self.mode == "saved":
            from .card_exploration_storage import saved_answer

            return saved_answer(self, question, options, origin)
        return self._live_answer(question, options, origin)

    def _live_answer(self, question, options, origin=None):
        if not isinstance(question, str) or question not in self._questions:
            raise ArgumentError(
                f"Available question keys: {', '.join(self._questions) or '(none for this Card nature)'}."
            )
        if not isinstance(options, dict):
            raise ArgumentError("Question options require a mapping.")
        if (
            question == "related_proteins"
            and options.get("mode", "relationships") != "relationships"
        ):
            raise ArgumentError(
                "related_proteins requires relationship context; ask sequence_differences explicitly for sequence comparison."
            )
        if question == "knowledge_differences":
            if "mode" in options and options["mode"] != "knowledge":
                raise ArgumentError("knowledge_differences requires mode knowledge.")
            options = {**options, "mode": "knowledge"}
        if question == "sequence_differences":
            if "mode" in options and options["mode"] != "sequence":
                raise ArgumentError("sequence_differences requires mode sequence.")
            options = {**options, "mode": "sequence"}
        if question in ("variant_tissue_context", "isoform_tissue_context"):
            mode = "variants" if question == "variant_tissue_context" else "isoforms"
            if "mode" in options and options["mode"] != mode:
                raise ArgumentError(
                    "The requested tissue-context question requires its matching mode."
                )
            options = {**options, "mode": mode}
        if question != "region_coverage":
            view = self._topic(self._questions[question]["topic"], origin, options)
            effective = (
                deepcopy(view.context["options"])
                if question
                in (
                    "assembly_generation",
                    "measured_molecules",
                    "measured_targets",
                    "publications",
                    "variant_tissue_context",
                    "isoform_tissue_context",
                    "sequence_changes",
                    "related_proteins",
                    "protein_associations",
                    "sequence_differences",
                    "knowledge_differences",
                )
                else {}
            )
        else:
            from .card_protein_exploration import region_request

            effective, status, reason = region_request(self, options)
            if status == "ok":
                view = self._topic(
                    "structures",
                    origin,
                    {
                        key: value
                        for key, value in effective.items()
                        if key != "sequence_ref"
                    },
                )
            else:
                view = replace(
                    self._metadata(
                        {
                            "question": question,
                            "options": effective,
                            "outcome": {"status": status, "reason": reason},
                        },
                        "Structural region coverage",
                        origin,
                    ),
                    _status=status,
                    _reason=reason,
                )
                view = replace(
                    view, _selection=replace(view._selection, _entries=()), _selected=()
                )
        return replace(
            view,
            _request={
                "question": question,
                "options": deepcopy(effective),
                "topic": self._questions[question]["topic"],
            },
        )

    @receiving
    @arg_digest()
    def answer(
        self,
        question,
        skip_digestion=False,
        *,
        options=None,
        region_budget=DEFAULT_REGION_BUDGET,
    ):
        """Follow a registered scientific question over the same captured results.

        ``region_coverage`` requires an explicit canonical UniProt sequence_ref
        and region in ``options``. Missing scope never starts a source query.
        ``region_budget`` is the same explicit workload control as for ``view``;
        None removes its ceiling without bypassing scientific validation.
        """
        from .region_requests import prepare_options

        options = prepare_options(self.access, question, options)
        return self._answer(question, {} if options is None else options)

    @arg_digest()
    def inspect(self, field_path=None, *, locator=None, skip_digestion=False):
        """Inspect everything, a dotted section field, or an exact typed location.

        Literal keys containing dots are reached through items or ``locator``;
        dotted paths are convenient section-field paths, never a key-guessing rule.
        """
        if field_path is not None and locator is not None:
            raise ArgumentError("Use field_path or locator, not both.")
        if field_path is not None:
            if not isinstance(field_path, str) or any(
                not part.strip() for part in field_path.split(".")
            ):
                raise ArgumentError("field_path requires nonempty dotted segments.")
            locator = self._location("sections", *field_path.split("."))
        return self._inspect(self.access.root_location if locator is None else locator)

    @arg_digest()
    def search(self, text, skip_digestion=False):
        """Find every literal key/scalar match locally, using Unicode casefold."""
        if not isinstance(text, str) or not text.strip():
            raise ArgumentError("text must be a nonempty string.")
        needle, matches = text.casefold(), []
        stack = [_Entry(self.access._card_location(), None, self.access._focal.data)]
        while stack:
            entry = stack.pop()
            value = entry.value
            if (entry.key is not None and needle in str(entry.key).casefold()) or (
                not isinstance(value, (list, dict)) and needle in str(value).casefold()
            ):
                matches.append(entry)
            if isinstance(value, (list, dict)):
                stack.extend(reversed(self.access._children(value, entry.location)))
        base = self._metadata({"query": text}, "Literal search")
        # The complete captured inputs and query bind a deterministic search result;
        # hit locations always point to original content, never copied search rows.
        selection = replace(
            base._selection,
            _result_ref=_handle(
                "XR_",
                {
                    "format": "literal_human_search@1",
                    "inputs": self.context["captures"],
                    "focal": self.context["snapshot_id"],
                    "text": text,
                },
            ),
            _entries=tuple(matches),
            _target={"location": self.access.root_location},
        )
        return replace(
            base,
            _selection=selection,
            _selected=tuple(matches),
            _status="ok" if matches else "empty",
            _reason="Literal matches only; no scientific meaning or completeness is inferred.",
        )

    def _support(self, location):
        """Nearest original field/record support; metadata is never source evidence."""
        if location["kind"] != "card":
            return [{"basis": "navigation_metadata", "location": deepcopy(location)}]
        segments = location["segments"]
        # Start at the outside: objects nested inside a field's original value
        # cannot redeclare lineage merely by resembling a field node.
        for stop in range(1, len(segments) + 1):
            owner = {**location, "segments": segments[:stop]}
            node, _ = self.access._resolve(owner)
            store = segments[0]["value"]
            if stop == 2 and store == "source_assertion_store":
                return [{"basis": "original_assertion", "location": owner}]
            relationship = stop == 2 and store == "relationship_store"
            field_support = (
                store == "sections"
                and isinstance(node, dict)
                and "value" in node
                and isinstance(node.get("source_assertion_ids"), list)
                and all(isinstance(ref, str) for ref in node["source_assertion_ids"])
            )
            if relationship or field_support:
                refs = node.get("source_assertion_ids", [])
                support = {
                    "basis": "relationship_level"
                    if relationship
                    else "original_field_support",
                    "location": owner,
                    "source_assertion_ids": deepcopy(refs),
                    "statements": [self._statement(ref) for ref in refs]
                    if isinstance(refs, list)
                    and all(isinstance(ref, str) for ref in refs)
                    else [],
                }
                if relationship:
                    for key in (
                        "derivation",
                        "derivation_applications",
                        "qualifier_conflicts",
                    ):
                        if key in node:
                            support[key] = deepcopy(node[key])
                    if (
                        node.get("predicate") == "has_predicted_structure"
                        and isinstance(node.get("qualifiers"), dict)
                        and (
                            isinstance(
                                (node.get("qualifiers") or {}).get("sequence_context"),
                                dict,
                            )
                            or (
                                isinstance(
                                    node["qualifiers"].get("native_reference_context"),
                                    dict,
                                )
                                and node["qualifiers"]["native_reference_context"].get(
                                    "rule"
                                )
                                == "alphafold_modelcif_reference_context@1"
                            )
                        )
                    ):
                        applications = node.get("derivation_applications")
                        inputs = set()
                        for app in (
                            applications if isinstance(applications, list) else []
                        ):
                            derivation = (
                                app.get("derivation") if isinstance(app, dict) else None
                            )
                            if not isinstance(derivation, dict) or derivation.get(
                                "rule"
                            ) not in (
                                "alphafold_sequence_context@1",
                                "alphafold_sequence_context@2",
                                "alphafold_modelcif_reference_context@1",
                            ):
                                continue
                            declared = derivation.get("inputs")
                            if isinstance(declared, list):
                                inputs.update(
                                    ref
                                    for ref in declared
                                    if isinstance(ref, str) and ref.startswith("SA_")
                                )
                        support["derivation_input_statements"] = [
                            self._statement(ref)
                            for ref in sorted(inputs)
                            if ref not in (refs if isinstance(refs, list) else [])
                        ]
                return [support]
        return [{"basis": "stored_literal", "location": deepcopy(location)}]

    def _statement(self, ref):
        location = {
            **self._location("source_assertion_store"),
            "segments": [
                _key("source_assertion_store"),
                {"type": "Record", "value": ref},
            ],
        }
        try:
            self.access._resolve(location)
        except ArgumentError:
            return {"id": ref, "state": "not_retained", "location": None}
        return {"id": ref, "state": "present", "location": location}

    def __repr__(self):
        if not hasattr(self, "_access"):
            return "CardExplorer(initializing)"
        return repr(self.overview())

    def _repr_html_(self):
        return self.overview()._repr_html_()
