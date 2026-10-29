"""Live request receiving budgets, separate from frozen scientific predicates."""

from contextvars import ContextVar
from copy import deepcopy
from dataclasses import replace
from functools import wraps
from inspect import signature

from .errors import ArgumentError, _diagnostic_details_allowed

# Operating default, not a biological sequence-length constraint. Both raw terms
# and total distinct positions across requested Cards are bounded.
DEFAULT_REGION_BUDGET = 100_000


class _InheritedBudget:
    def __repr__(self):
        return "INHERIT"


INHERIT = _InheritedBudget()
_budget = ContextVar("sabueso_region_budget", default=DEFAULT_REGION_BUDGET)


def current_budget():
    return _budget.get()


def receiving(function):
    """Establish only the receiving budget, including before argument digestion."""
    call_signature = signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        limit = budget(kwargs.get("region_budget", current_budget()))
        token = _budget.set(limit)
        try:
            result = function(*args, **kwargs)
            bound = call_signature.bind(*args, **kwargs).arguments
            request = bound.get("region", bound.get("regions"))
            options = bound.get("options")
            if isinstance(options, dict):
                request = options.get("region", request)
            receipt = {
                "policy": "region_request_budget@1",
                "region_budget": limit,
                "request": deepcopy(request),
            }
            if isinstance(result, dict):
                return ReceivedResult(result, receipt)
            if hasattr(result, "_access"):
                # Scientific selections intentionally retain object identity in
                # their cache. A receiving invocation is a separate observation.
                result._access._last_workload = receipt
                return result
            if hasattr(result, "_workload"):
                delivered = replace(result, _workload=receipt)
                # A live human producer creates this intermediate view for this
                # call. Its receiving wrapper replaces it, not scientific history.
                if hasattr(result, "_explorer") and result._explorer.mode == "live":
                    result._explorer._session["views"].pop(id(result), None)
                return delivered
            return result
        finally:
            _budget.reset(token)

    return wrapped


def budget(value):
    if value is not None and (type(value) is not int or value < 1):
        raise ArgumentError(
            "region_budget requires a positive integer or None.",
            argument="region_budget",
        )
    return value


def _check(positions, terms, limit):
    if limit is not None and max(positions or 0, terms) > limit:
        detailed = _diagnostic_details_allowed()
        size = (
            (
                f"needs {positions} distinct positions and {terms} input terms"
                if positions is not None
                else f"has at least {terms} input terms; distinct positions were not counted"
            )
            if detailed
            else "exceeds the receiving workload ceiling"
        )
        setting = f"region_budget={limit}" if detailed else "region_budget"
        error = ArgumentError(
            f"Region request {size}; {setting}. No positions were expanded. Raise "
            "region_budget or pass region_budget=None deliberately to disable "
            "this workload ceiling; scientific validation still applies.",
            argument="region_budget",
        )
        if detailed:
            error.extra["region_workload"] = {
                "positions": positions,
                "terms": terms,
                "terms_basis": "exact" if positions is not None else "at_least",
                "region_budget": limit,
                "expanded": False,
            }
        error.extra["reason"] = "region_budget_exceeded"
        raise error


def intervals(region, limit=None):
    """Validate compact syntax and compute the exact union without expansion."""
    limit = budget(limit)
    if region is None:
        return [], 0
    if not isinstance(region, (list, tuple, set)) or not region:
        raise ArgumentError("region requires positive positions or inclusive ranges.")
    _check(None, len(region), limit)
    spans = []
    for item in region:
        if type(item) is int and item > 0:
            spans.append((item, item))
        elif (
            isinstance(item, (list, tuple))
            and len(item) == 2
            and all(type(v) is int for v in item)
            and 0 < item[0] <= item[1]
        ):
            spans.append(tuple(item))
        else:
            raise ArgumentError(
                "region requires positive positions or inclusive ranges."
            )
    merged = []
    for begin, end in sorted(spans):
        if merged and begin <= merged[-1][1] + 1:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([begin, end])
    return merged, len(region)


def compact(region, limit=None):
    """Argument digestion retains ranges; scientific context precedes expansion."""
    if region is None:
        budget(limit)
        return None
    spans, terms = intervals(region, limit)
    _check(sum(end - begin + 1 for begin, end in spans), terms, limit)
    # Keep raw terms, including duplicates, for the receiving budget and receipt.
    return [list(item) if isinstance(item, (list, tuple)) else item for item in region]


def _expand(spans):
    return [position for begin, end in spans for position in range(begin, end + 1)]


def normalize(
    regions,
    cards=(),
    *,
    region_budget=DEFAULT_REGION_BUDGET,
    allow_mapping=False,
    record=False,
):
    """Preflight all recipients, then expand without changing scientific meaning.

    With no Cards (saved lookup), only resource receiving is checked. Frozen
    readers remain responsible for the exact retained scientific request.
    """
    limit = budget(region_budget)
    cards = tuple(cards)
    per_card = isinstance(regions, dict)
    if per_card and not allow_mapping:
        raise ArgumentError("region requires positive positions or inclusive ranges.")
    if per_card and cards and set(regions) - {card.id for card in cards}:
        raise ArgumentError("regions must name protein Cards present in the deck.")
    raw = regions if per_card else {None: regions}
    _check(None, len(raw) if per_card else 0, limit)
    # Count raw terms across all recipients before retaining parsed intervals.
    raw_terms = sum(
        len(value) for value in raw.values() if isinstance(value, (list, tuple, set))
    )
    _check(None, raw_terms, limit)
    parsed, terms, count = {}, 0, 0
    for key, region in raw.items():
        if per_card and (not isinstance(key, str) or region is None):
            raise ArgumentError("regions requires {Card id: nonempty region}.")
        spans, nterms = intervals(region, limit)
        parsed[key] = spans
        terms += nterms
        multiplicity = 1 if per_card else max(1, len(cards))
        count += multiplicity * sum(end - begin + 1 for begin, end in spans)
    if cards:
        from ._card_ligand_site_scope_v1 import reference

        for card in cards:
            spans = parsed.get(card.id if per_card else None, [])
            if not spans:
                continue
            canonical = reference(card)
            if (
                canonical["status"] == "comparable"
                and spans[-1][1] > canonical["length"]
            ):
                raise ArgumentError(
                    "region extends outside the original source-backed canonical reference."
                )
    _check(count, terms, limit)
    normalized = {
        key: None if raw[key] is None else _expand(spans)
        for key, spans in parsed.items()
    }

    def original(value):
        return (
            None
            if value is None
            else [list(x) if isinstance(x, (tuple, list)) else x for x in value]
        )

    receipt = (
        {
            "policy": "region_request_budget@1",
            "region_budget": limit,
            "positions": count,
            "terms": terms,
            "request": {key: original(value) for key, value in raw.items()}
            if per_card
            else original(regions),
        }
        if record
        else None
    )
    return normalized if per_card else normalized[None], receipt


def capabilities():
    return {
        "policy": "region_request_budget@1",
        "default": DEFAULT_REGION_BUDGET,
        "counts": ["distinct positions across requested Cards", "raw input terms"],
        "override": "region_budget=<positive integer>; region_budget=None disables the ceiling",
        "silent_truncation": False,
    }


def prepare_options(access, topic, options):
    """Live receiving before frozen saved lookup or current materialization."""
    if topic not in ("structures", "region_coverage"):
        return options
    if options is None or not isinstance(options, dict) or "region" not in options:
        return options
    # The existing captured Card facade supplies exact original reference support.
    card = _ReferenceInput(access._focal.data) if access.mode == "live" else None
    accession = card.get("identifiers.uniprot") if card is not None else None
    accession = accession.get("value") if isinstance(accession, dict) else None
    cards = (
        [card]
        if card is not None
        and (
            topic == "structures"
            or options.get("sequence_ref") == f"uniprot:{accession}"
        )
        else ()
    )
    region, _ = normalize(options["region"], cards, region_budget=current_budget())
    return {**options, "region": region}


class _ReferenceInput:
    """Only original canonical fields/support, without reconstructing a Card."""

    def __init__(self, data):
        self.meta = data["meta"]
        self.id = self.meta.get("card_id")
        self.quality = data["quality"]
        self._sections = data["sections"]
        refs = set()
        for path in ("identifiers.uniprot", "sequence.primary", "sequence.length"):
            node = self.get(path)
            if isinstance(node, dict) and isinstance(
                node.get("source_assertion_ids"), list
            ):
                refs.update(
                    key for key in node["source_assertion_ids"] if isinstance(key, str)
                )
        self.source_assertion_store = {
            row["id"]: row
            for row in data["source_assertion_store"]
            if row["id"] in refs
        }

    def get(self, path):
        value = self._sections
        for key in path.split("."):
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value


class ReceivedResult(dict):
    """Native scientific mapping with a separate live receiving receipt.

    JSON serialization retains the unchanged scientific mapping. The workload
    receipt describes this invocation, not a source assertion or saved science.
    """

    def __init__(self, result, workload):
        super().__init__(result)
        self._workload = deepcopy(workload)

    @property
    def workload(self):
        return deepcopy(self._workload)
