# Native mapping scopes

Living standalone subject/field boundaries from the recovered sources (#112).
Shared naming and view rules belong to [API_CONVENTIONS.md](../API_CONVENTIONS.md).
These field scopes do not change frozen cards or authorize automatic card intake.

# Source-specific mapping notes

Development Interactome3D keeps independent native archived protein structure/
model occurrences outside frozen card schema 0.3.12. Exact accession selection
retains rank pairs, original PDB/chain case, blank/whitespace chains, sequence
endpoint strings, filename pointers and opaque GA431/MPQS/ZDOPE literals including
negative sentinels. Percent identity/coverage use PyUnitWizard quantity nodes.
A representative set can contain multiple models; a template PDB is not a model's
experimental method. Bounds do not establish exact full-chain correspondence,
current canonical placement, protein similarity identity or MOLI Evidence.

Development ProBiS keeps literal reference-chain catalog occurrences outside
frozen card schema 0.3.12. Columns 3/4 select PDB/chain; columns 1/2/5 remain opaque
strings, including padding. Gaps in column 1 and repeated selectors are not repaired
or merged. Source IDs use full-export hash and native line, not an undocumented
column. A listed chain establishes neither a query-to-representative relation nor
protein identity, score/weight, binding, function, MOLI Evidence or current coverage.

Development PDBTM retains each native chain occurrence independently, including
duplicate/generated chains and identical sequences. XML-decoded sequence text,
TMP/type/TM-count strings and sequence/PDB endpoints survive with complete original
XML/copyright support. XML character/attribute decoding is distinct from unchanged
document bytes. Nonuniform endpoints imply no constant offset or exact residue map;
site/history versions imply no sequence revision. Matrices/scores stay raw XML,
without guessed quantities or transform execution. Standalone topology assertions
add no frozen-card field, protein/function identity or automatic intake.

Development 3did retains whole DMI ID/PT/3D/end blocks before exact PDB selection.
Each instance keeps its parent domain/motif labels, opaque pattern/date and original
chain/range/sequence/count/topology literals. PDB spans are not sequence offsets;
repeated lowercase chain tokens are not decoded. Zero counts and duplicate/conflicting
occurrences survive. This standalone mapping does not infer methods, function,
protein identity, new motifs or MOLI Evidence, and changes no frozen card field.


Development HPO keeps all six native gene/disease phenotype columns unchanged.
Selection uses the exact NCBI Gene ID column, never a gene symbol/name. Frequencies
remain original fractions, percentages, HP terms, missing `-` or future literals
with disease annotation scope. Every occurrence keeps native line/hash/release;
no deduplication, ontology expansion, penetrance calculation, clinical or protein
projection occurs. Assertions are standalone, outside frozen card schema 0.3.12.


Development MEROPS access records standalone native family/taxonomy literals in
`annotations.peptidase_inhibitor_classifications` on `merops:accession:<literal>`.
This is outside the frozen card schema. Prefixes, spaces/blanks and every repeated
occurrence survive. `representation_issues` retains three unassigned four-column
rows and one quoted literal; `selection_complete=False` prevents incomplete
selection from passing as complete. Raw export `truncated=False` only states that
received lines are retained. No activity, cleavage, protein identity or card intake.


Development MetalPDB access reads one native site ID and maps each received
occurrence on `metalpdb:site:<ID>` under the standalone `sites.metal_sites` field.
Original ligand chains and PDB atom/residue literals remain unplaced. Qualified
donor distances carry `{value, unit}` angstrom nodes; native geometry/counts and
pointers do not infer protein identity, function, experimental method or enrichment.
This reader does not introduce a frozen-card field or negotiated card intake path.


Development ECOD access selects one explicit numeric UID. The standalone field
`annotations.structural_domains.ecod` records native classification on
`ecod:uid:<UID>`; it is not a frozen-card field. Source range text is opaque,
experimental structure is a provider origin label, and UniProt remains a native
pointer. No sequence placement, protein merge or automatic enrichment is added.


Development TCDB access selects an exact case-sensitive accession literal after
complete headerless-export validation. The standalone mapping field
`annotations.transporter_classifications` records native TC-system occurrences
about `tcdb:accession:<literal>`; it does not add a frozen-card field or assign
UniProt/RefSeq/protein identity, sequence axes or family function.

Development `sabueso.tools.db.channelsdb.get_annotations(identifier, client=None)`
and `sabueso.mappings.channelsdb.map_annotations(envelope)` expose native PDB
annotations and independent SourceAssertions. The mapping's
`structure.channelsdb_entry_annotations` and `structure.channelsdb_residue_annotations`
paths are standalone source scopes, not new frozen-card fields or residue views.
No geometry reader, canonical numbering, card enrichment or protein identity merge
is introduced.
