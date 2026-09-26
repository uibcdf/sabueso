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
- `sabueso/_private/argdigest/function/`: function contracts (axis 1). A closed signature
  needs none. `sabueso.resolve` takes `**options`, and its contract admits the
  `card_options` domain (`sabueso/_private/argdigest/domain/card_options.py`). That
  domain is the union of the options of `resolve_protein_card` and
  `resolve_molecule_card`, read from their signatures so the two cannot drift. The tool
  `resolve` routes to refuses an option that belongs only to the other tool.

## Decorated functions

`tests/core/test_argument_contracts_offline.py` discovers them. It finds every `get_*`
of `sabueso.tools.db` and every decorated public method of `Card`, `Deck`,
`KnowledgeStore` and `CurationStore`, so that a new one cannot miss its digesters. As of
2026-09-26 they are:

- **Tools:** `resolve`, `resolve_protein_card`, `resolve_molecule_card`, `ligand_deck`,
  `ambiguity_deck`, `to_dataframe`, and every source-access function (`get_*`,
  `uniprot.search`).
- **Card views and operations:**
  - `bioactivities`, `structures`, `ligands`, `compare_ligands`, `compare_knowledge`;
  - `claims`, `table`, `extract`;
  - the curation methods (`add_literature_*`).
  `Card.compare` and `Deck.compare` reach their field paths through `Card.extract`.
- **Deck operations:** `summarize`, `structure_inventory`, `unique_names`,
  `group_by_rank`.
- **KnowledgeStore:** `save`, `load`, `history`, `source_assertion`, `relationship`,
  `relationships`, `save_deck`, `load_deck`, `deck_history`, `import_card_table`.
- **Resolver:** `EntityResolver(uniprot_client, policy, rcsb_client, ncbi_gene_client)`.
- **SQLite storage**, where the table name is interpolated into SQL:
  - `save_card_sqlite`, `load_card_sqlite`;
  - `save_deck_sqlite`, `read_deck_sqlite`, `load_deck_sqlite`.
  `Card.to_sqlite` and `Deck.to_sqlite` go through them.
- **Classmethods.** `Card.from_sqlite` and `Deck.from_sqlite` are classmethods, which
  ArgDigest does not wrap cleanly (uibcdf/argdigest#19). The storage readers they call
  digest `table` directly, with the same digester.

Not decorated, because their only constraints are ordinary types, or because a wrong
value fails loudly instead of answering plausibly:
- the JSON storage helpers, which take a path and a card or deck;
- `Card.get`, `set`, `quantity`, `quantity_columns`, `relationships`, `entity`;
- `Deck.add`, `extend`, `exclude`, `basis`, `sort`, `filter`, `map`, `in_lineage`,
  `group_by`, `intersect`, `difference`;
- `CurationStore`'s methods.

A method whose wrong value would answer plausibly (a typo that returns an empty result)
must be decorated. `claims(topic)` and `group_by_rank(rank)` were found missing on
2026-09-26 and are now decorated. `Card.expand` is not implemented and raises
`NotImplementedError`; it used to return an empty Deck, which read as "nothing related".

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
