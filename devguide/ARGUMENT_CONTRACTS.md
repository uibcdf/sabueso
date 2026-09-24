# Sabueso — Argument contracts (ArgDigest)

Sabueso digests the arguments of its public tools with ArgDigest, as MOLI's
support-library policy requires (uibcdf/sabueso#31) and as the sibling components do
(MolSysMT, MolSysViewer).

## Layout

- `sabueso/_argdigest.py`: the configuration, the same as the siblings'.
  - `DIGESTION_STYLE = "package"`, `STRICTNESS = "warn"`, `SKIP_PARAM = "skip_digestion"`.
  - `UNKNOWN_ARGUMENT = "error"`: a mistyped keyword is refused, as plain Python would.
- `sabueso/_private/argdigest/digest.py`: `arg_digest()`, the decorator bound to that
  configuration.
- `sabueso/_private/argdigest/argument/<name>.py`: one digester per argument name,
  `digest_<name>(value, caller=None)`. Shared helpers live in `_shared.py`, outside the
  digester package.
- `sabueso/_private/argdigest/function/`: function contracts (axis 1). It is empty, because
  every decorated function has a closed signature. A public function that takes
  `**kwargs` must declare its domain there.

## Decorated functions

- Tools: `resolve_protein_card`, `resolve_molecule_card`, `ligand_deck`, `ambiguity_deck`.
- Card views and operations: `Card.bioactivities`, `Card.structures`, `Card.ligands`,
  `Card.compare_ligands`, `Card.extract`. `Card.compare` and `Deck.compare` reach
  their field paths through `Card.extract`.
- Deck operations: `Deck.summarize`.
- Resolver: `EntityResolver(uniprot_client, policy, rcsb_client)`.
- SQLite storage, where the table name is interpolated into SQL: `save_card_sqlite`,
  `load_card_sqlite`, `save_deck_sqlite`, `read_deck_sqlite`, `load_deck_sqlite`.
  `Card.to_sqlite` and `Deck.to_sqlite` go through them.
- `Card.from_sqlite` and `Deck.from_sqlite` are classmethods. ArgDigest does not wrap
  those cleanly (uibcdf/argdigest#19), so the storage readers they call digest `table`
  directly with the same digester.

Not decorated, because the only constraints are ordinary types: the JSON storage helpers
(a path and a card or deck), `Card.get`/`set`/`quantity` (one field path), `Deck.sort`,
`filter` and `map`. `Card.expand` is not implemented and raises `NotImplementedError`.
It used to return an empty Deck, which read as "nothing related".

Rules for all of them:

- `@arg_digest()` goes under `@signal`.
- Each function takes `skip_digestion=False`. Use it only for internal calls with values
  Sabueso just built, never at a public boundary.

## What the digesters decide, and what they do not

- **Refused with `ArgumentError`** (`SABUESO-E-ARG-001`, also a `ValueError`): values that
  would otherwise run and give a plausible wrong result. Examples:
  - `structures="1SUX"` used to iterate its characters; it is now one structure;
  - unknown source options (`chembl={"limt": 10}`) and out-of-range ones;
  - non-boolean switches;
  - strings where a client object is expected;
  - table names that are not plain SQL identifiers, or that Sabueso reserves (`deck_meta`).
- **Normalized**: a single value where a list is expected is one item, not its characters.
  `structures="1SUX"` is one structure, and `card.extract("identifiers.uniprot")` is one
  field.
- **Not refused**: whether an identifier names a supported record. That is the resolver's
  answer, recorded in the resolution (`status="unsupported"`), not an argument error.
- **Source clients are duck-typed**: any object, or `None` for the online default. Their
  protocol is exercised by the call, and failures are source outcomes.

## Guards

`tests/core/test_argument_contracts_offline.py`:

- every listed public tool is wrapped by ArgDigest, and every parameter has a digester;
- the refusals listed above;
- unknown keywords are refused;
- no `DigestNotDigestedWarning` on ordinary calls.

## Known limitations

- ArgDigest's wrapper adds frames. Diagnostics raised inside decorated functions therefore
  compute their stack level (`sabueso/_private/smonitor/outcomes.py`, see
  `DIAGNOSTICS.md`). Reported upstream.
- A truthy non-boolean `skip_digestion` (for example `"yes"`) switches digestion off
  before the flag itself is digested, so only a falsy non-boolean reaches its digester.
  Reported upstream.
- Refusals name the caller as `<module>.<function>`, so a method's class is missing, for
  example `sabueso.resolver.entity_resolver.__init__`. Reported upstream
  (uibcdf/argdigest#18).
- A decorated classmethod warns that `cls` has no digester (uibcdf/argdigest#19). Until
  that is fixed, classmethods are not decorated; see above.
