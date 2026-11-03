# Opaque relationship qualifier parents (#181)

Owner: [#181](https://github.com/uibcdf/sabueso/issues/181), coordinated with #180/#148/#112.

The public-only synthetic counterexample replaces a P52270/1SUX relationship's
whole `qualifiers` value with a nonempty string. Preparing `Card.to_dict()` rebuilds
the entity glossary and previously failed on `.get()` before literal capture or
native input validation could run. Similar failures occurred for other nonmapping
parents. This is malformed test input, not a reported provider response.

## Storage, glossary and scientific boundaries

`build_entities()` now reads qualifier-derived context only from mappings. Other
parent values remain unchanged in the original RelationshipStore, along with every
SourceAssertion, derivation and quantity. Serialization, pinning, Card JSON and
KnowledgeStore roundtrips and captured literal exploration therefore remain
available. A missing qualifier, null, false, empty list and nonempty unsupported
value are not rewritten into each other in storage.

The private empty mapping used for glossary lookup supplies no names or additional
identifiers. Direct relationship endpoints and source-stated `same_as` predicates
retain their existing meaning; independent registered identities are preserved.
No metadata string is parsed as a mapping, and no extra alias is inferred from an
unreadable parent. The glossary is not a source-completeness or absence report.
Original unsupported context is inspectable through typed literal locations and
existing source/structure-context links. Their `unrecognized_parent_shape` state
continues to describe it. Other supported knowledge remains accessible.

Current structural interpretation separately requires an admitted declaration's
qualifier parent to be a mapping. Missing/empty mappings retain their previous
unknown states. A retained nonmapping parent causes the existing catalog
`SchemaError`, with `reason="malformed_structure_qualifier_inputs"`,
`problem="qualifiers_not_mapping"` and `field="has_structure.qualifiers"`.
Detailed capture carries exact original field/relationship locations; restricted
capture omits input identities. This is atomic request refusal, never a successful
empty/partial inventory or a claim of absent ligands. Foreign unplaced declarations
remain unplaced without entering focal interpretation. #180's existing ligand-field
diagnostics retain their original reason and field.

No Card schema, quantity seal, exploration format, classifier or saved verifier
changes. Typed supported glossary inputs keep the same existing processing.
Literal saved reading remains independent of live Card construction, entity
rebuilding and source acquisition.

## Separate nested-field interpretation issue

The audit also reproduced a numeric component identifier `17` becoming the apparent
record `pdb.ligand:17`. A stricter unpublished prototype rejects nontext component
and alias values and other unsupported inner context. An explicitly synthetic
legacy projection using original source `1052e5a` then demonstrated that rebuilding
its stored glossary under that prototype changes the Card's recomputed pin.
No actual published artifact was changed or presented as this control.

[#182](https://github.com/uibcdf/sabueso/issues/182) owns typed glossary inputs and
named/versioned original-glossary interpretation/pin acceptance. The broader
prototype was retained as owner-local proof and removed from this implementation.
Only the parent mapping read boundary and current structural parent refusal are
part of #181; accepted historical glossary algorithms are not rewritten here.

## Qualification and resource ownership

Owning cases cover all JSON parent shapes, exact original data/support and stable
new-state pins, public Card/KnowledgeStore persistence, human/agent literal access,
source inspection, predicate-specific explicit records, separate and independent
identity bases, missing/empty versus unsupported native parents, foreign scope,
restricted diagnostics and an independent inert original reader.
Selected integration, source/static/docs and hosted receipts belong to #181/#148/#112
and `recovered_work/entity_qualifier_parents_181_20261103/`. Pending or cancelled
runs are not passing qualification. Researcher acceptance and 0.15.0 consolidation
remain separate. #173 remains the broader scientific continuation.

The final selected local integration passes **444 cases across 17 files** in three
serial receptor invocations (196 + 115 + 133; 199.14 pytest seconds). Peak owned RSS
is 488,919,040 bytes, minimum host available RAM 14,485,196,800 bytes, minimum true
free RAM 287,297,536 bytes and owned swap zero. The unchanged guard stopped an
earlier broader invocation at its true-free-RAM floor; that stopped attempt is
retained as an observation, not passing qualification.

All fourteen tracked public frozen Cards produce identical complete stored forms
and recomputed pins under this implementation and original source `1052e5a`;
their input hashes are unchanged. The glossary union/entry algorithms, Card stored
form method and 66 original policy/verifier/history files remain byte-identical.
The public diagnostic example passes five valid/malformed/detailed/restricted
controls without acquisition or Card mutation. Warning-fatal Sphinx and applicable
Ruff, fixture-delivery, governance and Markdown/Python checks pass. Hosted final
source qualification remains separate until complete receptor evidence is reviewed.

Remove completed owned test/build/generated-notebook scratch after its last use.
Retain useful exact-source proof and active final CI captures with this owner and
review trigger at the next code checkpoint or pre-0.15.0. The minimal #182 prototype
and observation are retained under `recovered_work/glossary_input_audit_20261103/`
for that issue's interpretation review; they are not production runtime.
