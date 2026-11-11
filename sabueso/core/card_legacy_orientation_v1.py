"""Original pre-orientation opening, retained for unmarked historical sessions.

The original opening comes from source1741b71; scientific predicates and frozen
SOURCE resources are unchanged. Explicit current readings remain separate.
"""

RULE = "legacy_card_orientation@1"


def opening(view, preview, field_text, attribution):
    data = view.explorer.access._focal.data
    names = data.get("sections", {}).get("names", {})
    name = names.get("canonical_name", {}) if isinstance(names, dict) else None
    if isinstance(name, dict):
        name = name.get("value")
    lines = [preview(name)] if name else []
    lines.append(f"{view.explorer.profile} · captured Card")
    if view.explorer.profile == "protein":
        from .card_protein_exploration import field_entries, node

        gaps = {row["field"]: row["state"] for row in field_entries(view.explorer)[1]}

        for path, label in (
            ("annotations.organism", "Organism"),
            ("identifiers.uniprot", "UniProt accession"),
            ("sequence.length", "Sequence length"),
            ("annotations.function", "Function description"),
            ("annotations.catalytic_activity", "Catalytic activity"),
        ):
            value = node(view.explorer, path)
            if isinstance(value, dict) and "value" in value:
                lines.append(
                    f"{label}: {field_text(path, value['value'])} · {attribution(view.explorer, path)}"
                )
            elif path in ("annotations.function", "annotations.catalytic_activity"):
                lines.append(
                    f"{label}: "
                    + (
                        "unrecognized retained field; inspect the original content."
                        if gaps.get(path) == "unrecognized_shape"
                        else "not retained; no function is inferred from the name."
                    )
                )
        lines.append(
            f"Captured schema {preview(data.get('meta', {}).get('schema_version'))}; current sources have not been queried."
        )
        lines.append(
            "Start: items()[i].open() or explorer.questions(). All stored content: explorer.inspect()."
        )
    if view.explorer.profile in ("small_molecule", "disease"):
        from .card_protein_exploration import node

        fields = (
            (
                ("identifiers.inchikey", "Standard InChIKey"),
                ("properties.physchem.formula", "Molecular formula"),
                ("identifiers.smiles", "SMILES"),
            )
            if view.explorer.profile == "small_molecule"
            else (
                ("identifiers.mondo", "MONDO identifier"),
                ("annotations.definition", "Ontology definition"),
                ("names.synonyms", "Scoped synonyms"),
                ("annotations.term_status", "Retained term status"),
            )
        )
        for path, label in fields:
            value = node(view.explorer, path)
            if isinstance(value, dict) and "value" in value:
                lines.append(
                    f"{label}: {field_text(path, value['value'])} · {attribution(view.explorer, path)}"
                )
            else:
                lines.append(
                    f"{label}: no supported retained field value; inspect original content."
                )
        if view.explorer.profile == "small_molecule":
            lines.append(
                "Explore source-stated chemical identity and retained properties. No chemical calculation or target-context acquisition is performed."
            )
        else:
            lines.append(
                "Ontology terminology, not a diagnosis. Parent relationships and equivalent identifiers are separate routes; destination Cards are not opened here."
            )
        lines.append(
            f"Captured schema {preview(data.get('meta', {}).get('schema_version'))}; current sources have not been queried."
        )
        lines.append(
            "Start: items()[i].open() or explorer.questions(). All stored content: explorer.inspect()."
        )
    lines.append(
        f"{len(data.get('source_assertion_store', []))} retained source statements · "
        f"{len(data.get('relationship_store', []))} retained relationships"
    )
    quality = data.get("quality", {})
    if isinstance(quality, dict) and quality.get("conflicts"):
        lines.append(
            "Stored conflicts are present. Inspect explorer.view('quality') or original coverage/quality records."
        )
    return lines
