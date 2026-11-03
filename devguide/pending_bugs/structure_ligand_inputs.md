# Malformed original ligand inputs (#180)

Owner: [#180](https://github.com/uibcdf/sabueso/issues/180), coordinated with #148/#112.

The public TcTIM journey audit reproduced an unhandled `TypeError` when a
synthetically modified retained `has_structure.qualifiers.ligands` contained
`False`. Other non-list containers, nonmapping entries and incorrectly typed
component identifiers could also reach iteration, attribute or ordering errors.
Nonboolean investigation flags could disagree between truthy identifier selection
and the exact-boolean state classifier. These controls are deliberately malformed
inputs, not observations of provider responses.

## Current input contract

Current `structures_view` and `structure_inventory` preflight every declaration
admitted by the unchanged `experimental_structure_admission@1` policy before
calling their scientific interpreter. The contract accepts a missing/null ligand
field, or a list of mappings. A stated `comp_id` must be text or null, and a stated
`subject_of_investigation` must be boolean or null. Missing optional keys, empty
lists, false flags and unknown values retain their original meanings. Nested
instance/contact fields are not inputs of this component/flag classification and
remain opaque; this guard does not claim to validate their mapping or geometry.
Foreign/unplaced declarations stay outside this interpretation and remain retained.

Malformed inputs cause a catalog `SchemaError` (`SABUESO-E-SCHEMA-001`) with
`extra.reason="malformed_structure_ligand_inputs"` and a stable `problem` enum.
Detailed diagnostics provide complete typed `location` and
`relationship_location` addresses into the exact original capture. The offending
value is never copied into the message. Restricted SMonitor capture omits those
addresses/identities while retaining safe schema/problem context and catalog URLs.
Human and agent callers can inspect the original through their same captured
literal access; no source query, automatic refresh, coercion or data edit occurs.

This is a **controlled whole-request refusal**, not successful partial science or
an unsupported-input state invented inside an existing scientific result. A Deck
request preflights all its Cards before entering the inventory engine. No completed
result is returned or cached on failure. Restoring the caller Card cannot silently
repair an older captured explorer; create a new capture after correcting the data
against its actual source basis.

## Scientific and historical boundary

Accepted inputs still reach the same original computations and named state,
inventory, explanation and packet rules. No new knowledge is derived, no
SourceAssertion is created and no stored Card/exploration schema changes. The
original classifier and explicitly historical declaration/projection helpers are
unchanged. Original saved @1–@6 readers never invoke the new current input guard;
they keep verifying their own original decisions and source support. A conscious
workload override does not waive scientific input validation.

The broader malformed **qualifier parent** problem is separately observable in
[#181](https://github.com/uibcdf/sabueso/issues/181): a nonempty string in an entire
relationship's `qualifiers` can fail during `Card.entities()` while preparing its
stored form, before native validation is reached. This guard covers ligand fields
inside actual qualifier mappings and does not claim to fix that earlier Card/schema
receiving defect or #173 physical assembly reconciliation.

## Qualification

Owning cases cover malformed containers/elements/identifiers/flags, exact original
locations and source inspection, Card/Deck/explanation/human/agent refusal before
computation, multi-Card preflight, valid absent/null/empty/partial states, foreign
declarations, restricted diagnostics, immutable failed captures and genuine @1/@6
reading with current validation forbidden. Source-bound selected integration,
static and hosted receipts belong to #180/#148/#112 and
`recovered_work/structure_ligand_inputs_180_20261103/`. Pending/older hosted runs
do not qualify this source. Full broad researcher acceptance and 0.15.0
consolidation remain separate.

The final selected local integration passes **457 cases /173.43 s** across fifteen
files, serial through pytest-receptor, including 38 owning cases. Sampled peak
owned RSS is about 473 MiB, minimum available host RAM 14.66 GiB, genuinely free
1.53 GiB, with zero owned swap. The new public guide block executes in valid,
malformed detailed and malformed restricted cases without queries or Card mutation.
Warning-fatal Sphinx and applicable Ruff, fixture, local governance and
Markdown/Python-3.11 checks pass. Five original classifier/projection helpers and
66 original policy/verifier/history files are byte-identical to the base source.
These are selected local receipts, not a full-local-original or completed hosted
qualification claim. Initial tests corrected fixture-version and catalog-metadata
expectations; the qualifier-parent counterexample was separately reported as #181.

Useful original hashes, scripts, complete gate logs and resource/source/environment
receipts are retained until the next checkpoint or pre-0.15.0 review. Remove only
completed owned disposable scratch; preserve earlier active CI captures.
