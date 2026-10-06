# Source coverage for scientific journeys

Choose sources according to the question. This table covers the protein/comparator,
molecule/activity and disease/related-entity workflows; the full resource list is
in {doc}`data_sources`. A connector, a cross-reference and direct source access
have different meanings.

| Source | Knowledge used in these journeys | Scope to inspect |
| --- | --- | --- |
| UniProt | Protein identity, sequence, function, features, references and stated cross-references | Isoform/construct scope, entry/sequence versions, identity alternatives; a cross-reference does not mean the linked resource was queried. |
| RCSB PDB | Experimental entries, constructs, chains, assemblies, ligands and primary citations | Requested entries, native revisions, numbering, fragments and failures; selecting entries does not fetch every known structure or coordinate file. |
| ChEMBL | Target activities, molecule identity/properties, phases and indications | Target assignment, assay/type/relation/units, duplicate measurements, caps, source-reported release and partial results. |
| BindingDB | Target affinity measurements and publication pointers | Experimental context, source identity joins, query cutoffs, copies and source/REST version gaps. |
| PDB CCD / UniChem | Chemical components and explicit cross-source molecular identity | Standard InChIKey, unanchored records, linked-provider scope; linked resources are not additional direct access. |
| MONDO | Disease identity, stated equivalents and hierarchy | Related ids are not necessarily equivalents; unresolved EFO terms remain unresolved. |
| Open Targets / Orphanet | Disease-associated targets/genes | Source-specific scores, association types and gene/product identity; associations are not proof of mechanism or efficacy. |
| ClinicalTrials.gov | Registered studies explicitly cited by ChEMBL indications | NCT ids, registry status and limits; intervention names are not molecular identity, and registry entries are not clinical outcome proof. |

## Knowledge and execution coverage

`Card.knowledge_state()` describes scientific knowledge/coverage on a protein
card. Acquisition traces describe observed requests and their outcomes. Inspect
both, together with enrichment reports and deck membership/exclusions. `not_stated`,
`not_queried`, `unavailable`, `partial` and conflicting knowledge need different
interpretations; none automatically establishes a biological negative.

Sabueso 0.13.0 observes declared built-in UniProt, RCSB, Europe PMC, ChEMBL,
PubChem/BioAssay, BindingDB, CCD, UniChem, PDBe-KB, AlphaFold DB and InterPro
operations. MONDO, Open Targets, Orphanet, ClinicalTrials.gov, custom clients and
additional result/operation types have remaining observation gaps. Disease-deck
metadata records source outcomes but does not by itself establish complete runtime
traceability. See {doc}`attribution` for the exact coverage and original sidecars.

The disease journey in {doc}`journeys` uses development rules `@2` to retain native
target/drug membership assertions and exact MONDO/member identity pins. Earlier
rules `@1` have metadata-only membership with explicit missing support. Its exported
runtime bibliography covers observed sources only. Development MONDO term/equivalence
queries retain index/release origins and citations. Development Open Targets/Orphanet
queries retain page/file versions, original times and reuse, scoped empty/failure
outcomes and resource citations; disease builders retain original input/support and
final deck/member pins. Development DISEASES, ClinVar and MedGen queries now
retain their own original file/page/version/identity receipts. Access is never
reconstructed or credited from nearby card statements. Native source versions in scientific
support do not prove that access was observed. Target selection limits can count
attempted candidates rather than successfully built cards; inspect both.

Development ChEMBL indication references now enter portable workflow attribution
with exact native row/page occurrence scope. Trial-registry, label and classification
pointers retain grouped identifiers and missing metadata. Their role is
`source_cited_reference`; linked targets are not consulted by that operation.
Development ClinicalTrials.gov study/reference queries now retain native NCT,
page/version/reuse/empty/failure scope. Explicit reference lookup preserves registry
PMID and link declarations; a separate Europe PMC lookup can add source-stated article
metadata to the workflow. Complete bibliography across other source families remains
pending. The scientific clinical enrichment route in the table is a separate scope.

Always inspect requested limits, source totals, truncation, unavailable records and
the query's actual scope before interpreting a count or empty collection. The
offline comparison uses frozen public subsets; it does not establish current
online availability. Fixture absence is not absence from an external database.

## Reuse and citations

Use {doc}`terms` to inspect allowed use and obligations. Original literature
citations and resource-description citations remain distinct; bibliography does
not license downloaded content. Unknown versions or incomplete citations should
remain explicit. Exact stored references identify what you used, and original
runtime records identify the observed execution; preserve both for another reader.
