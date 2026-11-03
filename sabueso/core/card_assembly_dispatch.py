"""Select explicit assembly interpretations without changing original receivers."""

from importlib import import_module

from .errors import ArgumentError

OLD_RULE = "rcsb_assembly_generation@4"
NEW_RULE = "rcsb_assembly_generation@5"
NEW_ADAPTER = "assembly_generation_exploration@2"


def descriptor(access):
    module = (
        "card_assembly_history_v1" if access.mode == "saved" else "card_assembly_access"
    )
    result = import_module("." + module, __package__).descriptor()
    retained = {
        item.wire.get("context", {}).get("native_rule")
        for item in access._scientific_cache.values()
        if hasattr(item, "wire")
        and item.wire.get("context", {}).get("adapter")
        in ("assembly_generation_exploration@1", NEW_ADAPTER)
    }
    if access.mode != "saved" or NEW_RULE in retained:
        result["generation_rule_selection"] = {
            "option": "generation_rule",
            "default": OLD_RULE,
            "supported": [OLD_RULE, NEW_RULE],
            "retained_results": sorted(retained) if access.mode == "saved" else None,
            "saved_request_scope": "Only exact retained requests can be reopened.",
        }
    return result


def options_for_assembly(options, *, saved=False):
    options = {} if options is None else options
    if not isinstance(options, dict):
        raise ArgumentError("assembly_generation options require a mapping.")
    rule = options.get("generation_rule", OLD_RULE)
    if not saved:
        from sabueso._private.argdigest.argument.generation_rule import (
            digest_generation_rule,
        )

        rule = digest_generation_rule(rule)
    if not isinstance(rule, str) or rule not in (OLD_RULE, NEW_RULE):
        raise ArgumentError(
            "Assembly exploration supports rcsb_assembly_generation@4 or @5.",
            argument="generation_rule",
        )
    if rule == NEW_RULE:
        module = "card_assembly_history_v2" if saved else "card_assembly_exploration_v2"
        return import_module("." + module, __package__).options_for_assembly(options)
    module = "card_assembly_history_v1" if saved else "card_assembly_exploration"
    rest = {k: v for k, v in options.items() if k != "generation_rule"}
    return import_module("." + module, __package__).options_for_assembly(rest)


def materialize(access, options):
    module = (
        "card_assembly_access_v2"
        if options.get("generation_rule") == NEW_RULE
        else "card_assembly_access"
    )
    return import_module("." + module, __package__).materialize(access, options)


def view(explorer, origin, options):
    module = (
        "card_assembly_exploration_v2"
        if options.get("generation_rule") == NEW_RULE
        else "card_assembly_exploration"
    )
    return import_module("." + module, __package__).view(explorer, origin, options)


def presentation(view):
    result = view._selection._scientific
    version = (
        2
        if result is not None
        and result.wire.get("context", {}).get("adapter") == NEW_ADAPTER
        else 1
    )
    module = (
        f"card_assembly_history_v{version}"
        if view._explorer.mode == "saved"
        else "card_assembly_exploration" + ("_v2" if version == 2 else "")
    )
    return import_module("." + module, __package__)


def defer_frame(access, frame):
    version = 2 if frame.get("adapter") == NEW_ADAPTER else 1
    module = (
        f"card_assembly_history_v{version}"
        if access.mode == "saved"
        else "card_assembly_access" + ("_v2" if version == 2 else "")
    )
    return import_module("." + module, __package__).defer_frame(frame)


def saved_selection(access, fields, options, where, item_refs, order_by):
    options = options_for_assembly(options, saved=True)
    module = (
        "card_exploration_assembly_v2"
        if options.get("generation_rule") == NEW_RULE
        else "card_exploration_assembly"
    )
    return import_module("." + module, __package__).saved_selection(
        access, fields, options, where, item_refs, order_by
    )


def saved_human(explorer, options, origin, *, question):
    options = options_for_assembly(options, saved=True)
    module = (
        "card_exploration_assembly_v2"
        if options.get("generation_rule") == NEW_RULE
        else "card_exploration_assembly"
    )
    return import_module("." + module, __package__).saved_human(
        explorer, options, origin, question=question
    )
