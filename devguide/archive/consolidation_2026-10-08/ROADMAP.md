> Historical snapshot preserved on 2026-10-08 during consolidation (#112).
> Current guidance: [devguide/ROADMAP.md](../../ROADMAP.md). Statements below retain their original receipt dates and qualification scopes.

# Sabueso — Roadmap

Sabueso's work follows two routes, and this roadmap integrates both. Neither replaces the
other.

1. **The foundational plan** (2026-01 → 2026-09-23). The original design:
   - the vision, architecture and use cases;
   - a roadmap in phases (`archive/ROADMAP_original_2026-01.md`) and a source plan
     (`archive/SOURCES_original_plan.md`);
   - the long-term directions written on 2026-09-23 (`SCIENTIFIC_POTENTIAL.md`,
     `archive/future_direction_2026-09-23.md`).
2. **The pilot-driven route** (since 2026-09-23). Real discovery programs, the MOLI
   vertical pilots, pull platform development: a pilot needs something, Sabueso builds
   the smallest useful slice, and real use shows what is missing. Pilots are private.
   Their needs enter this public repository phrased generically, with public test
   systems (TcTIM, HsTIM and HK2, public data only).

The pilot route decided the *order* of the work since 2026-09-23, not its *scope*. The
objectives of the foundational plan stay objectives. This document tracks each one's
status, so that none is lost because a pilot has not asked for it yet.

## How the two routes are integrated

- **A pilot blocker comes first.** When a pilot cannot advance without Sabueso, that
  work goes first, in its smallest useful form.
- **Foundations are not postponed until they are expensive.** Some objectives get
  costlier the longer they wait: identity, references, schema, stores, query
  interfaces. They are scheduled before a pilot forces them, when the design they
  constrain is being built.
- **Every slice is built toward the foundational design.** A pilot-driven slice uses the
  general model (relationships, SourceAssertions, named derivation rules, pinned
  references), never a pilot-shaped shortcut. The pilot is its acceptance test, not its
  boundary.
- **Each release is reviewed against both routes.** Its notes and `CHECKPOINT.md` say
  what it advanced in each. When this table is out of date, updating it is part of the
  release.
- **Maintainers may schedule a foundational objective on its own.** The pilots do not
  own the plan.

## Latest release: 0.13.0 (#121)

Unreleased local recovery on 2026-10-06 adds offline notebook reports, canonical
residue annotation readers, explicit AAindex1 reference access, supplied snapshot
intake, source-scoped DisProt disorder assertions and richer detached residue
knowledge views with explicitly supplied sequence/track support, plus explicit
raw/FASTA UniParc candidates with current canonical sequence verification.
Precomputed AlphaMissense substitution access now retains original predictions,
source coordinate scope and separate host/artifact acquisition. Native MobiDB v1
exports now supply independent disorder and modification assertions on explicit
source sequences; SIFTS retains structural correspondences and original numbering.
PDBe validation retains native entry-wide raw metrics and separate archive/comparable
percentile ranks on structure subjects, without quality classes or structure selection.
EPPIC interfaces/assemblies and PDB-REDO refinement/input-revision context now retain
source calculations, original component times, area units and distinct model stages.
GlyGen glycosylation/phosphorylation context now retains source sequence, native
categories/support and isoform comments; unlocated/range annotations stay unplaced.
iPTMnet native HTML substrate reports are recovered independently of earlier
REST HTTP 503 failures.
AlphaFill now supplies native filled-model/transplant assertions with original donor
numbering and angstrom RMSD/clash quantities; LIGYSIS retains an explicitly selected
segment's full native site table, provider scores/clusters and percent RSA. Unknown
sequence/revisions stay explicit; no canonical placement, coordinates or jobs.
`Card.residue_composition` now summarizes an explicit sequence position set with
unique-position counting, original sequence support/revisions and ambiguous types
in the full denominator. Membership is caller-declared; cavity geometry and structural
mapping remain separate. The named derived view changes no persisted card field.
Explicit EPPIC residue detail now preserves native side/serial rows, ASA/BSA,
region/entropy literals and NaN fractions on one selected public interface. These
rows include zero buried area and do not all declare contact membership. No numbering
projection, coordinate fetch or calculation job is added. Direct IntAct preserves
native MITAB 2.7 observations, participant references, negation/complex expansion
and bounded page/count scope without inferred direct binding. Consumer projection
requirements are reviewed under current MOLI owners;
no exchange implementation or receiving acceptance is claimed.
AmyPro now reads one full native JSON export for an explicit entry ID, preserving
investigated-sequence regions, parent bounds/mutation/category literals and independent
entry-level publication pointers. No parent/current UniProt projection or experimental
class is inferred; data reuse and revisions remain unstated. ConSurfDB and FireProtDB
are deferred with concrete reuse and native-contract qualification triggers.
SWISS-MODEL Repository now retains every native PDB/homology-model occurrence,
source target sequence and paired chain alignments from one unfiltered metadata
GET. Native score dictionaries and mutable download pointers survive; target MD5
is not a model identity. API/query/creation/release dates stay separate from unknown
record/model/sequence revisions. No model choice, current UniProt projection or
coordinate/job access is added. Provider-generated data retain CC BY-SA 4.0 terms.
Explicit UniProt isoform access now supplies full parent declarations and only the
selected native FASTA to independent sequence assertions. Native names/IDs, parent/
canonical/release context and unknown isoform revision stay separate. The existing
residue reader can use that sequence with exact support; automatic resolution,
variant reconstruction and canonical/structural remapping remain unimplemented.
CATH now reads one explicit native structural domain on a required fixed release
route, retaining classification, independent ATOM/COMBS sequences and literal
residue/segment correspondences. Query-bound supplied JSON/gzip files reuse strict
snapshot intake and optional original-byte SHA-256. The release is a request label;
response/scientific revisions stay unknown. Native GO/EC context stays attached to
a source-domain subject, without UniProt identity or canonical placement.
Complex Portal now reads one exact primary CPX declaration and maps the full complex
context plus every participant occurrence. Native prediction/ECO/stars, stoichiometry,
types/roles and feature/range/reference alternatives stay original, with query-bound
supplied-file and archive access. No binary expansion, experimental class, identity
merge, sequence placement or linked acquisition is inferred. Release dates are
separate from unknown complex/participant sequence revisions; data retain CC0 1.0.
APPRIS now retains every native human gene annotation occurrence, including
repeated/conflicting transcript names, genomic ranges and principal labels.
Provider defaults and unstated dataset/assembly/sequence revisions remain explicit;
no principal choice or protein-residue projection is inferred. Supplied snapshots
bind exact source/query; original-time replay and CC BY-NC-SA 4.0 are retained.
SIGNOR now retains original headerless causal tables for one explicit UniProt/
organism request, including the first row previously lost. Every occurrence keeps
native roles/effects/mechanisms, DIRECT, scores and publication/residue context.
Requested taxonomy is separate from observed species/in-vitro/unknown context;
no complex expansion, generic binding class or current sequence projection occurs.
Native TSV/gzip snapshots bind exact metadata and optional byte SHA, with CC BY 4.0.
An offline metadata catalog and category profiles derive from maintained registry
decisions without activating queries or claiming readiness. These slices restore
useful July work on current contracts without altering frozen card schema or
existing clinical priorities. Historical source/feature requirements remain in
`archive/local_work_2026-07/`. The first batch reviews HPA, GtoPdb, WikiPathways,
Monarch and MEROPS together; HPA now supplies native gene JSON and literal
RNA/protein categorical summaries with full raw context and unknown revisions.
WikiPathways, Monarch and MEROPS are recovered in the integration follow-ups;
GtoPdb retains concrete qualification requirements.
The second batch reviews COSMIC, HPO, ClinGen, OmniPath and ELM; ClinGen now
retains the full native gene-validity CSV and independent classifications with
original inheritance/SOP/panel/report/date context and unknown scientific revisions.
The third batch reviews BioCyc, OMIM, Interactome3D, PDBTM and TCDB, preserving
native requirements and concrete access/terms/identity boundaries without claiming
new connectors. The fourth batch reviews MetalPDB, ECOD, 3did, DrugCentral and
GWAS Catalog. DrugCentral now retains all native target observations, original
composite groups, raw activity/MOA/support, bound TSV/gzip and CC BY-SA 4.0.
The fifth batch reviews ChannelsDB, PRIDE, CIViC, CASTp and ProBiS; CIViC now
retains native monthly accepted items on complete molecular-profile subjects with
original support, flags, exact release and CC0. The final two-source batch reviews
FDA/EMA Orphan and recovers native EMA designation pages with independent page
identity, date/status/product context, declared coverage, original bytes/time and
EMA attribution. The first five-source integration follow-up recovers exact native
WikiPathways xrefs and advances HPO frequency scope, GWAS paging, accessible ECOD
version/format pointers and separate ChannelsDB preferred assembly. The second
five-source follow-up recovers native human OmniPath interaction occurrences with
opposing effects and original aggregate support; it qualifies MEROPS' actual native
accession columns/displaced rows and retains TCDB/PDBTM/ELM boundaries. The third
five-source follow-up recovers native Monarch direct-subject pages and PRIDE Archive
project metadata, with original input/depositor terms and independent entity/dataset
scope. MetalPDB, Interactome3D and 3did retain explicit pending conditions. The fourth
five-source follow-up recovers native GWAS standard mapped-gene HAL pages with
checked query/links/counts and original statistics, without causal/protein projection
or automatic paging. GtoPdb, COSMIC, BioCyc and OMIM retain authorized-access and
native scope/terms requirements. The fifth follow-up recovers native ChannelsDB PDB
annotation occurrences, literal source groups/references and unplaced residue IDs,
with bound JSON/gzip/hash/time and one-GET replay. Geometry and its units/axes remain
separate; ECOD, CASTp, ProBiS and FDA native access/terms remain pending. The sixth
follow-up recovers native TCDB accession assignments with full headerless bytes,
literal case/version selection, duplicate/multiple occurrences and unbound blank
IDs. No namespace, family function or protein identity is assigned; bound TSV/gzip,
hashes/time and one-GET replay survive. HPO, MEROPS, PDBTM and ELM retain scope/
access/terms gaps. The seventh follow-up recovers ECOD native experimental-domain
classifications on explicit UID subjects, with opaque range and original flags,
bound JSON/gzip/hash/time and one-GET replay. Predicted domains, residue placement,
full exports and protein identity remain separately unqualified. MetalPDB,
Interactome3D, 3did and GtoPdb retain native access/units/scope/terms gaps.
The eighth follow-up recovers MetalPDB native site/metal/ligand/donor context and
angstrom distances qualified against the public Coordination Sphere. Original
occurrences, geometry/counts, PDB numbers and false flags survive, with bound
JSON/gzip/hash/time and one-GET replay. Protein/canonical placement, physiological
or functional interpretation and automatic card intake remain unqualified.
MEROPS, HPO, PDBTM and ELM retain native representation/scope/access/terms gaps.
The ninth follow-up qualifies CASTpFold tutorial area/volume units and official
existing-result examples, the ProBiS representative route, Interactome3D's exact
metadata export and 3did/FDA acquisition scope. Native result acquisition remains
unavailable, so no reader is added. Require a changed access condition or a qualified
supplied native artifact before repeating those failed routes; preserve FDA's
existing block without retry/bypass. See
[follow-up 09](../local_work_2026-07/followup_09_source_integration.md).
The tenth follow-up recovers MEROPS native accession classifications with all
received lines, original prefix/family/taxonomy and four explicit representation
issues. Unassigned/quoted literals are not repaired and incomplete selection is
reported. Bound TSV/gzip/hash/time and one-GET replay are qualified. GNU Library
GPL remains version-unspecified with local unshared use and unknown automated use/
sharing verdicts. Original cleavage/sequence capabilities, card enrichment and
public data distribution remain unqualified. PDBTM, HPO, ELM and GtoPdb retain
concrete conditions. See [follow-up 10](../local_work_2026-07/followup_10_source_integration.md).
The eleventh follow-up recovers the dated HPO native gene/disease phenotype
export after locating actual data terms in the official website source and checking
them in the deployed site. Exact NCBI Gene selection retains independent original
frequency/disease occurrences, complete unchanged file and native release/hash/line
support with one-GET replay. No ontology expansion, penetrance or protein identity
is inferred; custom/source-input terms and unknown automatic use/sharing remain
explicit. COSMIC, BioCyc, OMIM and PDBTM retain concrete conditions. See
[follow-up 11](../local_work_2026-07/followup_11_source_integration.md).
The twelfth follow-up recovers 3did DMI structural occurrences after documented
public access recovers. All native pair/instance blocks validate before PDB
selection, with complete original pattern, chain/range/sequence/count/topology
and parent/hash support. No regex search, chain decoding, PDB span projection,
protein/function transfer or card intake. Original gzip stays local unreleased;
export-data grant is NOT-STATED, with input rights separate. DDI residue contacts
and HMM profile interfaces remain separate. GtoPdb, ELM, CASTpFold and ProBiS
retain concrete conditions. See
[follow-up 12](../local_work_2026-07/followup_12_source_integration.md).
The thirteenth follow-up recovers PDBTM native chain topology with all three
1c3w chains/45 regions and complete unchanged original XML/copyright support.
XML-decoded attributes/sequence text retain independent sequence/PDB endpoints;
no constant-offset projection, generated-chain merge, guessed quantities, transform
execution or card intake. Conditional nonprofit/commercial-agreement terms and
unknown automated use/sharing remain explicit. Interactome3D, BioCyc, OMIM and FDA
Orphan retain native access/terms conditions. See
[follow-up 13](../local_work_2026-07/followup_13_source_integration.md).
The fourteenth follow-up recovers ProBiS native reference-chain catalog lookup,
with all 42270 headerless rows, three independent `5a2q.h` occurrences and exact
chain case. Opaque columns/padding and row/hash support survive without similarity/
identity or representative relation. Dated filename is only an artifact label;
NOT-STATED data grant and local unreleased qualification stay explicit. GtoPdb,
COSMIC, ELM and CASTpFold retain native access/terms conditions. See
[follow-up 14](../local_work_2026-07/followup_14_source_integration.md).
The fifteenth follow-up recovers Interactome3D archived representative protein
metadata after actual native access succeeds, with all 18000 rows, independent
occurrences, whitespace chains and original ranks/template/endpoints/scores.
Identity/coverage use percent quantities; reported bounds are not exact full-chain
mapping. Archive route label is separate from unknown scientific revisions;
NOT-STATED grant and local unreleased qualification stay explicit. BioCyc, OMIM,
ELM and FDA Orphan retain conditions. See
[follow-up 15](../local_work_2026-07/followup_15_source_integration.md).
The sixteenth follow-up reviews CASTp/CASTpFold, GtoPdb, COSMIC, ELM and OMIM
without qualifying a new native reader. A distinct previous CASTp portal cannot
connect; preserved Fold builders expose no changed result condition. Current
registered/licensed access and native-instance requirements stay explicit. Further
attempts require a changed native-data/access condition or a qualified supplied
artifact. See [review 16](../local_work_2026-07/followup_16_source_review.md).
The seventeenth follow-up expands the recovery queue to the seven original
pending candidates plus iPTMnet, Pharos/TCRD, ASD, BRENDA, DepMap and TTD.
Native exact-target Pharos metadata and fixed public DepMap 24Q4 model context
are now recovered. Two of this 13-resource queue have scoped readers; eleven
remain pending. The original 27-list remains 20 scoped readers / 7 pending.
BRENDA's officially linked SPARQL prototype supplies an EC label without account,
but a bounded inhibitor probe returns HTTP 500 and kinetics remain unqualified.
SOAP's account requirement is not a blanket blocker. Other access/terms conditions
are preserved rather than replaced by synthetic data. See
[follow-up 17](../local_work_2026-07/followup_17_expanded_source_integration.md).

The eighteenth follow-up recovers BRENDA's native EC-class descriptions, keeping
historical kinetics unqualified. ASD's actual download script qualifies licence
application and no-redistribution conditions; TTD's actual redirect/download script
yields an original public cross-reference export with native entry-name/placeholder
keys and a 2024 revision. Data terms and its reader remain pending. Expanded queue:
3 resources with scoped readers / 10 pending / 0 unreviewed; original 27-list remains
20 scoped readers / 7 pending. See
[follow-up 18](../local_work_2026-07/followup_18_pending_source_integration.md).

The nineteenth follow-up recovers TTD native exact-ID target listings and iPTMnet
original HTML substrate reports. Native key/group/release and hidden source/PMID
support survive without accession inference, sequence projection, curation guesses
or clinical conclusions. TTD keeps NOT-STATED use/sharing; iPTMnet database
CC BY-NC-SA conditions are independently qualified. Expanded queue: 5 scoped
resources / 8 pending / 0 unreviewed; original 27-list remains 20 / 7. Remaining
sources need actual authorized native inputs or a changed access condition. See
[follow-up 19](../local_work_2026-07/followup_19_native_target_and_ptm_context.md).

The twentieth follow-up recovers native FDA OOPD detailed-page artifact reading,
preserving independent designation and marketing-approval tables on requested page
subjects. FDA website public-domain terms are separately qualified; no openFDA
grant or product/protein identity is inferred. Shared live transport receives
HTTP 404; supplied-artifact reading/imported-original replay remain separate.
ELM native acquisition still times out; GtoPdb explicitly requires an API key.
Expanded queue: 6 scoped resources / 7 pending / 0 unreviewed; original 27-list:
21 scoped readers / 6 pending / 0 unreviewed. The seven need new authorized access
or original scientific input; no repeated restricted/failed scientific routes.
See [follow-up 20](../local_work_2026-07/followup_20_pending_resource_recovery.md).


The twenty-first follow-up adapts preserved supplied-file intake for literal UTF-8
HTML/TXT and consolidates FDA/iPTMnet loading without widening native contracts.
Original hash/time declarations and all source validation remain required; broken
gzip and invalid UTF-8 are failures. This is utility recovery, with unchanged
source queues. Direct GO, small-molecule context, consumer projections and native
cavity membership retain the explicit requirements in
[follow-up 21](../local_work_2026-07/followup_21_supplied_native_files.md).


The twenty-second follow-up recovers LIGYSIS initial displayed residue-panel
annotations from the existing HsTIM result page. Native row/column occurrences,
UPResNum/MSACol, AA/SS, DS/MES/p and percent RSA retain original support. Selected
site identity and versioned source sequence/alignment remain unknown; no other-site
or current-canonical coverage is claimed. This adds a scientific slice within an
already adopted resource, with unchanged source queues. See
[follow-up 22](../local_work_2026-07/followup_22_ligysis_residue_panel.md).


The twenty-third follow-up recovers native LIGYSIS directed residue-correspondence
dictionaries from the same preserved result page: four independent tables and
491 entries per direction, with literal numbering and original support. Page query
does not identify each chain's protein. Identity/numbering/insertion/revision gaps
remain explicit; no inverse reconstruction, canonical placement or coordinate
acquisition is added. Provider counts stay unchanged. See
[follow-up 23](../local_work_2026-07/followup_23_ligysis_correspondences.md).


The twenty-fourth follow-up recovers **LIGYSIS native structure mapping** through
one documented read-only POST for HsTIM context and PDB 7t0q. The unchanged 9185-byte
response supplies four directed residue tables, two explicit chain-to-accession
declarations and eight native chain remappings. Online/fixture reading and 14
standalone assertions preserve original support and separate table identities.
The structure is echoed; protein/segment remain caller/transport context. Scientific
revisions and residue/chain namespaces remain unknown; no old-page join or current
canonical projection occurs. Expanded queue stays **6 scoped / 7 pending**, original
27-list **21 / 6**. Stash and 87 originals remain intact, index empty, recovery local.
See [follow-up 24](../local_work_2026-07/followup_24_ligysis_structure_mapping.md) for qualification and remaining boundaries.



The twenty-fifth follow-up recovers **ChannelsDB native tunnel membership and
channel annotations**. One public existing-result GET retains the unchanged
751462-byte 1tqn response: 26 channel occurrences, 910 layers and seven independent
channel comments/references. Native residue-flow, HetResidues and layer membership/
index arrays remain literal and separate across all twelve categories, including
MOLE/CAVER representation differences. No inferred identity, annotation join,
geometry conversion, canonical placement, job or schema/card enrichment is added.
Expanded queue stays **6 scoped / 7 pending**, original 27-list **21 / 6**. Stash
and 87 originals remain intact; the index is empty and recovery stays local.
See [follow-up 25](../local_work_2026-07/followup_25_channelsdb_membership.md) for qualification and remaining boundaries.



The twenty-sixth follow-up recovers **five bound original-file pathways** for
AlphaFill metadata, GlyGen protein detail, SIFTS mappings, LIGYSIS result HTML and
LIGYSIS structure-mapping JSON. Four explicit snapshot clients reuse qualified
native readers, preserve original byte hashes and declared retrieval context, and
reject foreign source/kind/query/revision declarations before file access. Native
validation and standalone assertion support remain mandatory. Plain/gzip originals
work without source requests. This utility adds no provider adoption: expanded
queue stays **6 scoped / 7 pending**, original 27-list **21 / 6**. Stash and 87
originals remain intact, index empty, recovery local/uncommitted/unpushed.
See [follow-up 26](../local_work_2026-07/followup_26_bound_native_snapshots.md) for qualification and remaining intake boundaries.



The thirty-fifth follow-up closes the **11 remaining original-file reviews** and
**nine scientific artifacts** (two cards, one ligand list, six notebooks).
Generic review labels fall **11 to 0**. Useful ready behavior is covered by current
qualified routes; future native-source and access conditions remain tracked.

Human **HK2/P52789** now complements TcTIM/HsTIM as a public test system.
The reproducible current card/report uses the unchanged public UniProt response:
**239 SourceAssertions**, schema **0.3.13**, original acquisition **2026-09-23**.
Five integrated regression cases preserve identity/support, separate ATP groups,
unqueried scope and exact store/report rebuilding. Multi-source HK2 expansion
requires additional qualified original responses; historical cards are not fixtures.
The old PTGS2-named card actually contains HK2; 188 old ligand references remain
unverified query hints with 313 preserved parent observation/support links.

All 87 exact originals are verified in a temporary local compressed backup.
The historical audit is complete. The maintainer authorized deletion of the
reviewed stash, and it was dropped on **2026-10-08** after verifying the backup.
The stash list is empty; all recovered working files, HEAD and index were preserved.
Accumulated changes remain local/uncommitted/unpushed.
See [follow-up 35](../local_work_2026-07/followup_35_final_review_and_hk2.md) and [the HK2 recipe](../../HK2_TEST_SYSTEM.md).

Full code checkpoint: **5554 passed in 173.00 seconds**, 10 expected fixture
warnings, pytest-receptor with **12 workers** and existing editable Python **3.14.7**.
Focused HK2 gate: **5 passed**; selected schema/snapshot/report/integrity scope:
**260 passed**. The current schema and published frozen cards remain unchanged.


At the thirty-fourth checkpoint, the follow-up closed **five grouped knowledge/structural/translational
mapper and enrichment-test reviews**: **30 map functions / 10 historical test functions**.
Current qualified native routes replace their useful ready behavior; no additional
runtime restoration is needed from this block. Peptide/PTM/HPP, broader drug/clinical
candidate, gene dependency/quantitative expression, structural-contact/geometry and
direct reaction/provider-prediction requirements are preserved independently under
#112/#83/#95. Provider deferrals and source identity/units remain explicit. Generic
individual-review labels fall **16 to 11 original files**, not eleven ready providers.

Selected gates: **221 passed in 8.71 seconds** and **1394 passed in 18.87 seconds**,
each with pytest-receptor, **12 workers** and existing editable Python **3.14.7**.
Outside-checkout replay preserves 598 card assertions, 493 independent bioactivities,
a 256-card ligand deck, explicitly selected residue composition and 216 standalone
assertions across six native scopes, with exact scientific documents/pins and zero
source requests. Registry, strict docs, original integrity, maintained links and diff
pass. This review changes metadata only; the full code checkpoint remains follow-up
32's **5549 passed in 176.40 seconds**. See [follow-up 34](../local_work_2026-07/followup_34_grouped_knowledge_mapper_review.md).
Stash and all 87 exact exports remain intact. Eleven file reviews and the historical
scientific artifacts still need reconciliation before recommending deletion.

At the thirty-third checkpoint, the follow-up closed a **five-file protein-query and retired-constructor
review**. Current native identity resolution, exact-sequence candidates and explicit
isoform access cover the ready behavior; no additional runtime restoration is needed
from this block. Native taxonomy aliases, gene/entry-name lookup, PDB chain selection
and any SCOPe reopening have self-contained future acceptance under #112/#83.
Automatic ranking and sequence-derived identity are not restored. Generic
individual-review labels fall **21 to 16 original files**, not sixteen ready features.

Selected gates: **171 passed in 3.99 seconds**, pytest-receptor with **12 workers**,
existing editable Python **3.14.7**. Native offline replay preserves seven resolution
records/traces, 18 preference alternatives, 19 unpreferred candidates, four complex
protein declarations, three distinct exact-sequence candidates and three explicit
isoforms, with exact scientific JSON/digests and zero source requests. Registry,
strict docs, original integrity and diff gates pass. This is a metadata-only review;
the last full code checkpoint remains follow-up 32's **5549 passed in 176.40 seconds**.
See [follow-up 33](../local_work_2026-07/followup_33_protein_query_review.md) for all conditions and receipts.
Stash and all 87 exact exports remain intact. Remaining file reviews and scientific
artifacts still need reconciliation before recommending deletion.

At the thirty-second checkpoint, the follow-up recovered **57 native UniProt SourceAssertions** from
five unchanged public fixtures: **11 text occurrences / 46 positional features**.
Five comment kinds and eight feature kinds retain native support, boundaries,
modifiers, molecule scope and source revisions. Source cautions and similarity
remain source statements; uncertain/foreign-scope or known revision-mismatched
features stay unplaced. Development schema **0.3.13** is unpublished; published
0.3.12 schemas, shapes and frozen cards remain unchanged. Migration reports 13
explicit optional refresh gaps without creating source knowledge.

The **five grouped specialist mappers (43 map functions)** are individually reviewed.
Useful remaining gene-expression, kinetic, gene-description and richer annotation
requirements are preserved independently of the stash under #83/#112. The generic
file-review queue falls from **26 to 21 original files**; this is an audit count,
not 21 ready capabilities or providers. Full checkpoint: **5549 passed in 176.40
seconds**, pytest-receptor with **12 workers**, 10 expected fixture warnings,
existing editable Python **3.14.7**. Selected gate: **148 passed**. Ruff, registry,
strict docs, shape/schema and integrity pass. Outside-checkout replay preserves
898 assertions and exact card/deck/storage snapshots with zero source requests.
Full qualification and remaining requirements: [follow-up 32](../local_work_2026-07/followup_32_uniprot_and_specialist_review.md).
Stash and all 87 exact exports remain intact. The remaining file reviews and
historical scientific artifacts need reconciliation before recommending deletion.

At the thirty-first checkpoint, the follow-up closed **five native source mapper reviews** (UniProt,
InterPro, PDB, PubChem, TED) and recovers PubChem's native summary-page title as an
independently supported molecule name. Existing structure-key admission remains;
equal titles cannot merge structures. A public unchanged three-CID response supports
the new reader; current source comments/features, matched-domain boundaries and
RCSB entry-title acceptance are retained under #83/#112 without the old package tree.
Current RCSB accession dates and primary citation already have structure context;
TED remains retired. Native offline replay preserves 42 assertions, three exact
card/deck/storage snapshots and titles with zero source requests. Five original
mapper reviews are closed; **26 original file entries** still carry generic
individual-review labels, an audit count rather than 26 ready features/providers.
Final full offline checkpoint: **5495 passed in 168.82 seconds**, pytest-receptor
with **12 workers**, 10 expected fixture warnings, existing editable Python 3.14.7.
Focused PubChem gate: 64 passed; licensing/new-reader gate: 22 passed. Ruff,
registry, strict docs, shape/schema and integrity pass.
Full qualification and remaining boundaries: [follow-up 31](../local_work_2026-07/followup_31_native_mapper_review.md).
Stash and all 87 exports remain intact; source-sequence/residue, older core/schema,
specialist support parsers and historical scientific artifacts still need assessment.
Stash deletion is not yet recommended.

At the thirtieth checkpoint, the follow-up closed **two five-file reviews** of source configuration,
transport, decks, assertions, selection and storage. Current implementations and
earlier qualified file readers cover their useful implemented behavior; no further
runtime code needs restoration from these ten originals. A future unified source
configuration needs the native-validation/identity/terms/trace contract retained in
[#112](https://github.com/uibcdf/sabueso/issues/112), with supplied input under #131.
Selected gates: **209 passed in 4.89 seconds** and **64 passed in 9.28 seconds**,
pytest-receptor with **12 workers**, existing editable Python 3.14.7. Outside-checkout
native fixture replay preserves 203 assertions from UniProt/RCSB/InterPro, exact
card/deck snapshots, repeated members, metadata and two ambiguous candidates with
zero source requests. This slice changes review metadata only; the last full code
checkpoint remains follow-up 29's **5477 passed in 172.18 seconds**.
Stash and 87 exports remain intact. Source-sequence/residue, remaining native metadata,
older core/schema and scientific artifact assessments still need completion before
a recommendation to delete the stash. See [follow-up 30](../local_work_2026-07/followup_30_configuration_and_persistence_review.md).

At the twenty-ninth checkpoint, the follow-up closed a **five-file notebook/reporting review** and
recovers the optional generated-cell offline regeneration workflow. It verifies
the exact saved card, preserves title/mode/language and regenerates beside the
saved pair after moving both files. The source notebook/card pair stays untouched;
rendering remains inert. Current reports replace obsolete Evidence/protein paths;
future deck/bundle/presentation acceptance is preserved independently of the stash
under [#112](https://github.com/uibcdf/sabueso/issues/112#issuecomment-6057570230).
Full checkpoint: **5477 passed in 172.18 seconds**, pytest-receptor with **12 workers**,
10 expected warnings, existing editable Python 3.14.7. Ruff, registry, strict docs,
shape/schema and integrity pass; external editable replay preserves 199 source
assertions with zero source requests. Stash and 87 originals remain intact.
Other admission/metadata/persistence/consumer areas still need residual assessment;
this is not yet a recommendation to delete the stash.
See [follow-up 29](../local_work_2026-07/followup_29_notebook_regeneration.md).

At the twenty-eighth checkpoint, the follow-up reviewed **five small-molecule implementation originals**
and recovers ChEBI's native name and formula into independent SourceAssertions.
Current identity, resolver conflict, molecule/ligand deck and clinical workflows
replace the old implemented paths. Direct ChEBI admission, additional qualified
chemical metadata and patent/clinical acceptance requirements are preserved with
concrete conditions in the report, independently of the stash. This adds no source
adoption or schema change. Full offline checkpoint: **5472 passed in 155.74 seconds**,
pytest-receptor with **12 workers**, 10 expected warnings, existing editable Python
3.14.7. The stash and 87 originals remain intact. Other implementation areas still
need residual-gap assessment; stash deletion is not yet ready for a recommendation.
See [follow-up 28](../local_work_2026-07/followup_28_small_molecule_recovery.md).

At the twenty-seventh checkpoint, the follow-up **finished the pending-provider actionability review**.
None of ASD, GtoPdb, COSMIC, ELM, BioCyc, OMIM or CASTp has a qualified original
input/access/rights condition available in this recovery. All seven are now
`deferred`, with individual `revisit_when` triggers tracked in [#83](https://github.com/uibcdf/sabueso/issues/83)
and access follow-up in [#95](https://github.com/uibcdf/sabueso/issues/95).
This is disposition, not adoption: the expanded 13-resource queue is **6 scoped /
0 active pending / 7 conditional deferrals**; the original 27-list is **21 scoped /
0 active pending / 6 conditional deferrals**. Historical 87-source catalog is
**65 in use / 0 evaluating / 18 deferred / 3 retired / 1 out of scope**. Other
registry evaluations are outside this recovered candidate set. Source grants and
existing reader behavior do not change. The stash and 87 originals remain intact.
Continue with other preserved implementation requirements; reopen a provider when
its named condition changes. See [follow-up 27](../local_work_2026-07/followup_27_provider_disposition.md).

No unreviewed or presently actionable pending providers remain from this recovery
list. Provider deferral does not close the implementation backlog or retire the
sources; their reactivation conditions live in the registry and issue-backed review.
Isoform sequence reconstruction, extra source integrations and supplied
legacy scientific data still require identity/support, units and terms contracts.

Published 2026-10-05 from qualified `7e78d07`, with unchanged `py_0` promotion,
clean public installation and an identical-tag Zenodo archive. All 12 installed
OS/minor lanes pass 613 receiving cases and the public workflow; receipt:
`devtools/conda-build/receipts/sabueso_0.13.0_public_2026-10-05.json`.

The release adds eight source families to required acquisition observation, original
literal extraction/article bibliography, pinned derived explanations, versioned
integrity corrections and an independent persisted application exercise. It advances
foundational identity/support/schema/reference integrity and receiving-pipeline
traceability. Schema 0.3.12 is frozen. Broader #108/#91/#92 and consumer-owned
Nextia Evidence / MOLI ProjectRecord / Recorda acceptance remain open.

## Previous release: 0.12.0 (#110)

Published 2026-10-04 from qualified `7739317`, with unchanged `py_1` promotion,
clean public installation and an identical-tag Zenodo archive. The 12 installed
OS/minor lanes each pass 56 integration cases and the public three-packet workflow;
receipt: `devtools/conda-build/receipts/sabueso_0.12.0_public_2026-10-04.json`.
The superseded preliminary `py_0` archive/receipt remain immutable.

This release combines located literature and supported structural mention context,
literature explanations, pinned packet terms, required Ackredit attribution and
UniProt/Europe PMC/RCSB acquisition traces. RCSB retains native entry revisions,
primary citations, reuse, empty answers and per-entry failures with every fallback.
It advances foundational support/terms/reference integrity and the pilot-driven
need to retain original source access and per-result/workflow references.
Schema 0.3.11 is frozen; original runtime JSON stays beside scientific payloads.

Other sources/custom clients, further result types, incomplete bibliography and
MOLI ProjectRecord/Recorda integration remain open in #108/#36. Traceability remains
mandatory. The next slices follow observed use and the foundational objectives below.

## Delivered so far (0.1.0 → 0.13.0)

- **Foundations.**
  - Card, Deck, `SourceAssertionStore` and `RelationshipStore`.
  - The FieldResolver with selection rules, and the EntityResolver.
  - Mappings, conflict and knowledge-state reporting.
  - Physical quantities (PyUnitWizard) and argument contracts (ArgDigest).
  - Diagnostics (SMonitor).
- **Storage and references.**
  - Content-addressed card and deck snapshots, and pinned references.
  - The `KnowledgeStore` and the `CurationStore`.
  - Honest migration and refresh of stored cards.
- **Release route.** Staged conda releases:
  - a dependency-contract preflight;
  - inspection of the exact artifact;
  - immutable coordinates, and a recorded public poststate (#76–#78).
- **Sources in use.**
  - UniProt, RCSB PDB, PDB CCD, PDBe-KB, InterPro, AlphaFold DB.
  - ChEMBL, BindingDB, PubChem and PubChem BioAssay, UniChem.
  - STRING, IntAct (through UniProt), NCBI Taxonomy, NCBI Gene.
  - Since 0.6.0: PHI-base, DISEASES, Open Targets, Orphanet, Reactome, ClinVar, gnomAD,
    ChEMBL indications and ClinicalTrials.gov (#81–#83).
  - Since 0.7.0: SKEMPI 2.0 (#83), MONDO and MedGen (#90), Europe PMC (#92).
  - Since 0.8.0: ChEBI, KLIFS, GPCRdb, SAbDab, OMA, OPM and PDBTM segments through RCSB
    (#83), and gnomAD's pext (#102).
  - Since 0.9.0: UniRef clusters, through UniProt (#103).
  - Since 0.10.0: GTEx's tissue terms (#102).
  - The registry, `sources/registry.yaml`, is the index.
- **Knowledge views, each with a named rule:**
  - structures and the structural inventory; predicted models;
  - oligomer and interfaces; ligand sites;
  - bioactivities, with one measurement across sources; ligands;
  - literature and claims; knowledge states;
  - card comparison; identity audit; unique names.
- **Curation.** Literature assertions, bioactivities, engagements, relationships and
  typed claims, compared with the sources, never given priority. Since 0.6.0, the
  biological context of a target (#60).
- **Since 0.6.0.**
  - Variants placed only through stated transcripts and isoform maps (#83, #85).
  - Knowledge packets, a prototype (#71).
  - Declared enrichers with shared network, release-cache and key services (#86).
- **Since 0.7.0.**
  - Diseases as entities, anchored at MONDO; a protein's diseases grouped; a
    disease's targets and drugs (#90).
  - What may be done with the knowledge, and terms profiles (#29, #94).
  - Scientific operations: expand, explain, as of (#91).
  - Molecules given as SMILES or InChI, through PubChem's stated match (#93).
  - How each statement entered, and text-mined literature mentions (#92).
- **Since 0.8.0.**
  - Variants checked against gnomAD's consequence on the canonical transcript; the
    tissues of each variant and isoform (#85, #102).
  - Kinase pockets, GPCR numbering, antibody complexes and orthologs (#83).
  - What was downloaded (a retrieval archive), local mirrors, offline work (#100).
  - Knowledge store format 2, `knowledge_packet@2` and `packet_aspects@3` (#88, #99).
- **Since 0.9.0.**
  - A reference entry and its genome-strain entry related through their UniRef
    clusters, never merged; the positions where two equal-length sequences differ
    (#103, verified in the pilot that asked for it).
  - Unreadable answers and server errors asked again, and every retry recorded on the
    card (`quality.retries`, #97).
  - Validation runs from scratch, with what the sources answered recorded, never
    reused (#100).
- **Since 0.10.0.**
  - Tissues as GTEx's UBERON and EFO terms; isoforms whose exons are unknown say why
    (`isoform_exon_usage@2`, #102).
  - A knowledge packet as an index by reference, with the guarantees agreed in
    uibcdf/moli#22 (`packet_index@1`, #88); `packet_aspects@5`.
- **Since 0.11.0.**
  - Pinned explanations of structural inventory items and all group members
    (`structure_inventory_explanation@1`, #91), without fetching or selecting.
  - Located accession annotations for explicit articles at source access (#92),
    and a public hypothetical review rehearsal that preserves historical support.
  - Curation export preserves extraction acquisition (#105); existing source
    identifiers with spaces are readable by their pins (#104).

## Status of the foundational plan

Status: **done**, **partial** (part delivered, the rest named), **pending**, or
**changed** (replaced by a decision, which is cited).

### Original roadmap (phases 0–5)

| Item | Status | Where / next |
|---|---|---|
| Phase 0 — conceptual schema, repository structure, devguide | done | `schemas/`, this devguide |
| Phase 1 — UniProt, RCSB, ChEMBL, PubChem connectors | done | `sabueso.tools.db.*`, `SOURCE_ACCESS.md` |
| Phase 2 — aggregator, SourceAssertionStore, conflict detection | done | `DATA_FLOW.md` |
| Phase 3 — selection engine with per-field rules | done | `RESOLVER.md`, `SELECTION_RULES_EXAMPLES.md` |
| Phase 4 — eMolecules, ChemSpider, DrugBank | pending | registry: eMolecules and ChemSpider queued; DrugBank deferred (licence) |
| Phase 4 — physchem and bioactivity fields | done | PubChem, ChEMBL physchem; three bioactivity sources (#66, #68) |
| Phase 4 — clinical layer | partial | ChEMBL max phase and indications, ClinicalTrials.gov trials by cited NCT id (#81); DrugBank deferred; ADMET and pharmacovigilance pending |
| Phase 5 — SDK entry points | done | `sabueso.resolve`, views, `PUBLIC_API.md` |
| Phase 5 — CLI | pending | no need has been stated |
| Phase 5 — Sphinx documentation | done | `docs/` |
| Phase 5 — pytest coverage, contract tests, snapshots | done | `TESTS.md`: offline suite, online tests, frozen cards, recorded card shape |

### Original vision and architecture

| Item | Status | Where / next |
|---|---|---|
| Protein cards | done | `resolve_protein_card` |
| Small-molecule cards | done | InChIKey anchor (#25) |
| Peptide cards | pending | `entity_type: peptide` exists in the schema; no peptide source or view (CPPsite queued) |
| Inputs: identifiers, names | done | UniProt, `pdb:`, `pubchem:`, `chembl:`, `pdb.ligand:`, `inchikey:`, name + organism |
| Inputs: SMILES, InChI | done | matched by PubChem, never a computed key (`pubchem_structure_lookup`, #93) |
| Inputs: sequence (FASTA), structure files | partial development | explicit `exact_sequence_candidates@1` accepts raw/FASTA, verifies full archive/current canonical sequences and retains ambiguity, caps, failures and unqueried isoforms. Automatic sequence/structure-file resolution remains pending and needs its own identity rules. |
| Disease associations of a protein | done | `annotations.disease` (#39) |
| Ligands with a role (inhibitor…) | changed | a role is a derived class, never asserted (#25): `bioactivity_class@3`, `ligand_deck` |
| Deck of inhibitors of a protein | done | `ligand_deck(card)` with derived classes |
| Local cache / store | done | `KnowledgeStore` (cards); retrieval archive and local mirrors, opt-in (#100, `CACHE_POLICY.md`) |

### Use cases (`USE_CASES.md`)

| Use case | Status |
|---|---|
| 1. Interactions, ligands, pathways of a protein | done (pathway structure from Reactome, #83) |
| 2. Clinical usage of ligands | partial (max phase and ChEMBL indications, #81; DrugBank clinical content deferred, licence) |
| 3. TopoMT: catalytic residues, mutations as structural features | partial (positional features, ligand and family sites, interface mutations from SKEMPI, #83; no TopoMT contract yet) |
| 4. PharmacophoreMT: deck of ligands | partial (ligand decks; no exchange format agreed) |
| 5. Commercial availability of peptides | pending |
| 6. Tissue-specific isoforms | partial (tissue specificity; UniProt isoforms and alternative sequences, #80; AlphaFold isoform models; the tissues of each variant and isoform from gnomAD's pext, with GTEx's UBERON terms, #102; isoform sequences not fetched) |
| 7. Visualization (MolSysViewer) | partial (interfaces, mutations, sites, secondary structure from UniProt and per chain from RCSB, #80; no contract) |
| 8. Clinical trials of ligands | done for the trials ChEMBL's indications cite (#81); a trial is never matched to a molecule by name |
| 9. Disease associations; targets of a disease | done: protein → diseases from UniProt, DISEASES, Open Targets, Orphanet and ClinVar, grouped through MONDO (#82, #90); disease → targets and → drugs as decks (#90) |
| 10. Knowledge baseline for a target and a comparator (pilot route) | done |
| 11. Curating what the literature states (pilot route) | done (human curation) |
| 12. Citing knowledge from a project (pilot route) | done, provisional reference form (#53, moli#3) |
| 13. Choosing structures to model (pilot route) | done |
| 14. A cohort of related proteins (pilot route) | done |

### Strategic directions (`SCIENTIFIC_POTENTIAL.md`, 2026-09-23)

| Direction | Status | Where / next |
|---|---|---|
| A strong SourceAssertionStore | done | MOLI-aligned fields, curated assertions, provenance |
| Cards that relate (relationships as knowledge) | done | `RelationshipStore`, typed predicates |
| More powerful decks | done | membership, derivation, pinned revisions, lineage, audits, inventory |
| Entity resolution as a central piece | done | EntityResolver, identity audit, curated names; a reference entry related to its genome-strain entry, never merged (#103) |
| Temporal knowledge | partial | snapshots, revisions, source releases; the store's `as_of` and `changed_since` (#91); no source asked as of a past release |
| Knowledge from Nextia not imported automatically | done (as a boundary) | promotion of derived knowledge open in uibcdf/moli#17 |
| Literature as a knowledge source | partial | human curation and literature views; literal rule extraction/intake and explicit article metadata since 0.13.0 (#92); broader extraction/validation pending |
| KnowledgeQuery (semantic queries over sources) | partial | prototype released in 0.6.0 (#71): a protein subject, a fixed aspect mapping (`packet_aspects@5` since 0.10.0; published @6 adds literature mentions and their index/unknowns); contract in uibcdf/moli#22 |
| Knowledge packets (entities, facts, conflicts, unknowns) | partial | prototype released in 0.6.0 (#71): pinned, stored, with a content-equivalence id; since 0.10.0, an index level by reference for size (#88), accepted in uibcdf/moli#22, which closes with a consumer test |
| Unknowns as first-class output | done | `knowledge_state()` (#56) |
| Two levels of access (semantic and raw) | done | `resolve` and views; `tools.db.*.get_*` |
| Patents | deferred | SureChEMBL evaluated 2026-09-30: mentions cannot be restricted to claims |
| Proprietary / internal knowledge | pending | needs its boundary with Nextia (moli#17) and usage terms (#29) |

## Pilot-driven work

Delivered for the first pilot's knowledge baseline and structural inventory:

- organism relations and identity hygiene (#54, #55, #67, #69);
- knowledge states (#56);
- versioned decks and card comparison (#58, #59);
- predicted structures (#57) and curated engagement (#61);
- measurements across sources (#66, #68);
- migration (#51) and claims (#43);
- names, the structural inventory and its grouping (#70);
- what the first live run of the baseline found: the authors' oligomer (#72), author
  numbering (#73), partial source answers (#74), the measurement review (#75);
- the integrity of pinned item reads (#79), a case of the reference contract
  (uibcdf/moli#3);
- the comparative context: orthologs (OMA, #83), the tissues of variants and isoforms
  (#102), and a reference entry related to the genome-strain entry proteome-based
  sources use (#103);
- steadier live runs: unreadable answers and server errors retried and recorded (#97);
  runs from scratch, with what the sources answered recorded (#100).

Open, pilot-related:
- #53, the reference form (waits on uibcdf/moli#3);
- #60, biological context: step 1 (curated fields) released in 0.6.0; step 2
  (VEuPathDB) blocked on access and terms (#84);
- #30, ligand proximity to sites (deferred);
- correspondence of regions across proteins. This one belongs to MolSysMT; Sabueso takes
  its residue maps (`residue_map`, `residue_maps`).

## Design review after 0.12.0

The maintainer-requested [implementation review](../../pending_proposals/design_implementation_review.md)
(#112, 2026-10-04) compares original phases, conceptual schema, architecture, scientific
potential and use cases against code/tests. The foundations are implemented; complete
runtime coverage, broader literature extraction, derived explanations, consumer acceptance,
peptides/suppliers and much of the clinical layer remain partial or pending. Illustrative
graph/query APIs are directions, not implied delivery obligations. The review retains
the earlier slice sequence; the approved next roadmap below sets the current order
across both routes. #101 remains postponed.

## Next roadmap after 0.13.0

Approved by the maintainer on 2026-10-05 after reviewing the original architecture,
MOLI's Knowledge role and Sabueso's promise to independent scientific users (#112).
This is the next development order. The capability status below remains the record
of what exists and what is incomplete; illustrative long-term APIs remain design
directions until a bounded use and acceptance criteria are agreed.

### Immediate resumption sequence

Current state: [CHECKPOINT.md, Resume here](../../CHECKPOINT.md#resume-here).
Detailed acceptance and local receipts: [journey audit](../../pending_proposals/independent_user_journeys.md)
and [clinical checkpoint](../../pending_proposals/clinical_registry_checkpoint.md).
This sequence narrows the approved roadmap; it does not replace either route.

1. **Code checkpoint completed (2026-10-06).** The accumulated implementation
   and public examples/fixtures/guards are pushed to `origin/main` in `413cdf6`,
   with the UTF-8 test correction in `74c8c3d`. [Exact-head CI](https://github.com/uibcdf/sabueso/actions/runs/37438528677)
   passes 15/15 jobs and MOLI governance passes. `CHECKPOINT.md` records
   the final receipt; no repeat is needed without a new change. #122–#128 remain
   open for public-package delivery. Candidate staging and a release remain
   separate work; no release number is decided here. Resume at step 2.
2. **Integrate the bounded clinical bibliography into a saved public journey
   (#108/#112).** Source-level registry/reference observation and explicit Europe PMC
   metadata are implemented. Next, declare which cited NCT ids and native PMID are
   in the journey's requested scope, save original per-result/workflow sidecars,
   and verify independent saved readers and reacquisition. Keep genuine disease
   `@1`–`@5` reports unchanged; version a changed example/manifest. Declare all
   unqueried links and remaining bibliography gaps. Refresh the broader live
   showcase separately; fixtures are not live-source acceptance.
3. **Discuss the next bounded contract, then implement it.** Choose one explicit
   non-protein question/result for #71/#91, or finer filtering by terms of use for
   #29. Filtering needs a separate derived view/deck with declared kept/excluded
   support and its original references/citations; conservative admission already
   exists. Decide shared versus member scope and partial/missing-support behavior
   before implementation. No silent deletion from original saved knowledge.
4. **Continue the foundational expansion and parallel consumer work.** Scope peptide
   identity and one scientific use (#112/#83/#95), as described below. Keep Nextia
   persistent Evidence acceptance and MOLI/Recorda recording with their owners;
   independent SDK work can proceed while those consumers develop.

The shared development environment's current external dependency conflicts are a
separate maintenance task. Diagnose their ownership and compatibility before
changing shared package versions; use clean installed qualification environments
for artifact claims. Do not treat those conflicts as a Sabueso source defect.

Both routes continue. An observed pilot blocker takes priority in its smallest
useful form. Foundational work also proceeds on its own: a scientist must be able
to use Sabueso without a MOLI project, while MOLI consumes the same authoritative
knowledge through agreed contracts. Consumer readiness does not block independent
SDK, documentation or scientific improvements. Public acceptance uses public data
and generic questions only.

### 1. Complete three independent-user journeys

Define and demonstrate these end-to-end journeys through the existing public SDK
first. Record missing behavior before adding a connector or changing an API.

| Journey | Scientific question and expected output | Acceptance |
| --- | --- | --- |
| Protein and comparator | What is known about each protein, where do sources disagree, and which structures, ligands and measurements can be compared? | Resolve and audit identities; inspect supported values, alternatives, conflicts and unknowns; compare within stated identity/numbering scope; save both states and read their exact support later. |
| Molecule and activities | What do sources state about a molecule, its measured activities and reported clinical context? | Resolve the molecule; retain measurement types, units, assay context, source-supported identity and clinical coverage limits; inspect original statements and citations; save and reopen the result. |
| Disease and related entities | Which targets and drugs do sources associate with a disease, and on what basis? | Resolve a MONDO-anchored disease; build target/drug decks; retain relationship support, grouping rules, ungrouped identity paths and conflicts; save and inspect exact historical items. |

Each journey needs a runnable public example and user-guide instructions that do
not require knowledge of provider endpoints or MOLI internals. Explain source
coverage, limits, terms and partial/unavailable outcomes. Preserve original runtime
JSON beside saved scientific objects, with per-result/workflow citations and explicit
observation gaps. An independent saved reader must recover the cited state without
source access; reacquisition must leave those historical references meaningful.

Refresh the showcase and add a dedicated small-molecule page, user-facing source
coverage tables and examples for comparative/source-specific views where used.
Track the journey audit in #112 and [DOCS_GAPS.md](../../DOCS_GAPS.md); use #71, #91,
#108 and the relevant source issues for implementation gaps. The SDK is the current
entry point; evaluate a CLI only when a journey demonstrates a need.

Development progress (2026-10-05, #112): the protein/comparator journey is implemented
in `examples/user_journeys/protein_comparison.py`, with separate producer, reader
and reacquisition processes, exact support for both proteins, original reports,
unit-preserving serialization and original runtime/bibliography records. Its scope
is explicit public fixture subsets, without positional alignment or a claim of
current online availability. The user guide now covers this journey, small-molecule
cards and source coverage for the three workflows. The molecule/declared-target
journey now preserves BTS/benznidazole identity, assay measurements and ChEMBL
clinical indications, with a selected molecular deck, target-context packet,
original reports/attribution, separate saved readers and fixture reacquisition.
Other targets and cited clinical studies are explicitly unqueried. Its source-state
counting defect is corrected locally in #122 under `knowledge_state@5` and
`knowledge_state_explanation@2`, with unknown/native counts, missing subsets and
separate clinical areas. Published delivery remains pending; broader molecular
queries and integration of observed clinical bibliography remain #71/#108. The disease journey now has a
bounded producer, independent saved reader and reacquisition example preserving
MONDO/card support, original target/drug membership metadata, disease-group
explanations and partial runtime attribution. Development disease rules `@2` now
preserve exact native membership, original MONDO input and member identity pins,
including excluded/unbuilt candidates, with portable support and atomic saves (#91).
MONDO term/equivalence observation is implemented locally with original index/file
origins, versions, reuse and bibliography. Complete acceptance remains open:
Open Targets/Orphanet and disease-deck build observation are also implemented locally
(#108/#124), including page/file receipts and exact input/result pins.
DISEASES/ClinVar/MedGen observation is also implemented locally (#108/#125).
Conservative `disease_deck_admission@1` is also implemented locally (#29): exact
embedded context must allow the use; all raw member statements are checked, and
excluded member identity pins become explicit historical references. Unknown or
restricted shared context refuses the operation; finer filtering by terms of use
remains pending. Native ChEMBL indication pointers now contribute to workflow
attribution, retaining exact row/page/query occurrences and explicit unfetched-target
and metadata gaps (#108). Development ClinicalTrials.gov observation and explicit
registry-reference/Europe PMC bibliography are implemented (#127/#128); broader
underlying study bibliography remains pending.
Non-protein packets remain
#71 work; see
[the journey audit](../../pending_proposals/independent_user_journeys.md) for concrete
query/observation gaps. The broader live showcase refresh remains open.

### 2. Extend queries, explanations and required traceability

Use the journey gaps to define a small catalog of precise scientific queries.
Examples to scope include ligands with specified measurements, structures that
represent a requested region, and drugs associated with a disease. Agree identity,
context, constraints, selection, completeness and result support before choosing
public method names.

- **Queries (#71).** Extend beyond the current protein/comparator and fixed aspects
  toward molecule, disease and collection questions in bounded slices. Source
  routing and normalized output belong to Sabueso. Every slice declares its
  supported constraints and reports unsupported requests explicitly; full/index
  results retain exact authoritative references, conflicts, unknowns and terms.
- **Explanations (#91).** Extend the named-rule/pinned-support readers to the derived
  results those journeys expose. Show inputs, parameters, exclusions, alternatives
  and partial support. Historical reads must not acquire data or silently change
  rules. General joins, ranking and graph navigation need separate scientific scopes.
- **Traceability (#108).** Extend observed source/client/operation coverage along
  these exercised paths, including reuse, versions with their actual basis, retries,
  empty answers, caps, partial returns and failures. Keep bibliography and missing
  citations explicit. Scientific support, observed execution and terms retain
  distinct meanings; coverage cannot be inferred from a returned card alone.
- **History and scale (#100/#98/#88).** Measure large journeys and make limits and
  truncation inspectable. Scope coherent replay, historical source access and export
  guarantees separately from local store history. Preserve pins and original
  receipts; local `as_of` is a stored-state date, not a historical database query.

Acceptance for each slice includes a public scientific example, meaningful
regressions, saved historical support after refresh/reacquisition, explicit coverage
and user documentation. New packet mappings/rules are versioned; published cards,
schemas and historical packets retain their meaning.

### 3. Scope peptides as the next scientific expansion

Prioritize the original peptide-card promise after the journey and contract work
above. Begin with identity and a bounded scientific use, before adding a source.
Define sequence, modifications, termini/cyclization and source-stated cross-references;
distinguish a peptide from a protein fragment, construct or isoform. Establish how
supplier products and availability relate to the scientific entity without merging
them by name or sequence similarity.

Then select a source whose access and terms fit that use, implement its client,
mapping/enricher and peptide views, and demonstrate a public save/read/cite journey.
Commercial availability must state the provider, product/context and observation
date; missing availability is not proof that a peptide cannot be obtained. Scope
CPPsite/eMolecules/ChemSpider against the actual question rather than adopting all
three automatically. #112/#83/#95 coordinate the initial scope; open a focused
owner issue before peptide implementation starts.

The clinical layer, isoform sequences/additional transcript coverage and broader
literature extraction remain objectives in the capability backlog below. Select
their next slices from a stated need. DrugBank still needs a terms/access decision;
local-mirror work #101 remains postponed until the maintainer reschedules it.

### 4. Close consumer contracts in parallel

- **Nextia and Context Assembly (#53/#71, MOLI #3/#22).** Receive actual consumer
  acceptance: persist an index, read an exact historical item, create consumer-owned
  Evidence with an explicit interpretation, and retain its original citation after
  new acquisition. `examples/persisted_pipeline/` already exercises Sabueso's public
  application side; it does not replace a persistent Nextia consumer test.
- **Platform recording (#108, MOLI #36/#18).** Agree correlation, persistence,
  availability and failure policy with the owners of ProjectRecord/Recorda. Sabueso
  supplies knowledge support and observed use; MOLI owns their platform composition.
- **Modeling exchanges.** Agree adapters with MolSysMT, TopoMT, PharmacophoreMT and
  MolSysViewer for entity references, source-supported residue/construct mappings,
  features and ligand decks. Preserve units, numbering, versions and support across
  exchanges. MOLI owns the Sabueso-to-MolSysSuite boundary; MolSysSuite governs its
  internal member contracts. Modeling and calculation remain with their owners.
  [Reviewed legacy projection requirements](../local_work_2026-07/consumer_projection_requirements.md)
  retain concrete receiving cases for owner review, without an accepted exchange
  schema or new exporter claim.

These are coordination tasks, not consumer implementations to add inside Sabueso.
Keep consumer acceptance separate from standalone journey acceptance.

### Decisions to close before broadening the API

| Decision | Questions to settle | Tracking / owner |
| --- | --- | --- |
| Scientific query catalog | Which questions and entity/collection types are supported? What context, constraints and coverage make a response meaningful? | Sabueso #71/#112; shared packet meaning in MOLI #22 |
| Entity and representation scope | Identity for modified peptides, isoforms, constructs, FASTA/structure-file inputs; whether structure-level cards are needed; EFO identity without a MONDO anchor | Sabueso #112/#20/#96; modeling exchanges with their owners |
| Reproducibility and export | Distinguish stored state, source release, downloaded response and execution; decide reference-only versus self-contained exports, retention and missing-target outcomes | Sabueso #100/#53; shared references/retention in MOLI #3 and retrieval boundary in MOLI #33 |
| Literature validation | Rights of supplied fragments; extraction/validation, correction and retraction; trace a statement to its actual source location and retain extraction method/version | Sabueso #92/#29; project-to-knowledge promotion in MOLI #17 |
| Public contract stability | Guarantees for queries, explanations, terms, references and export; version/deprecation policy and historical readers for each new slice | Sabueso #112 and feature issues; shared commitments in MOLI |

Model-generated interpretations do not automatically become SourceAssertions.
Extracted statements need support in the external source; project conclusions need
an explicit curation/promotion boundary. See
[RISKS_AND_OPEN_QUESTIONS.md](../../RISKS_AND_OPEN_QUESTIONS.md) for the outstanding decisions
and [DECISIONS.md](../../DECISIONS.md) for adoption of this order.

This roadmap schedules work, not a release date or a frozen new API. Revisit the
order against both routes at each release and when real use exposes a blocker.

## Capability backlog and dependencies

The following entries retain the progress and remaining work from the foundational
review begun on 2026-09-29. Their numbering groups capabilities; the next development
order is the approved roadmap above.

1. **The disease as an entity (#90).** Released in 0.7.0: disease cards anchored at
   MONDO, a protein's diseases grouped through stated identity and MONDO's hierarchy,
   and a disease's targets and drugs. Open: EFO terms MONDO does not map (#96).
2. **What may be done with the knowledge (#29).** Released in 0.7.0: `Card.terms`,
   `Deck.terms`, `Deck.admissible`, depositor terms per PubChem assay, and terms
   profiles (#94). Released in 0.12.0: read-time
   `KnowledgePacket.terms(use, store)` for `packet_aspects@6`, with pinned support,
   separate bibliography/fragment terms and full/index parity. Next: historical
   scope adapters as use asks, and the shared vocabulary with MOLI.
3. **Scientific operations (#91).** Released in 0.7.0: `expand` (relationships into decks),
   `explain` (a deck member and a card's SourceAssertions), and the store's `as_of` and
   `changed_since`. Released in 0.11.0: an inventory item through
   `Deck.explain(card_id, structure_ref=..., ...)`, with the pinned relationship and
   SourceAssertion support of every group member (`structure_inventory_explanation@1`).
   Released in 0.12.0: `Card.explain_literature(publication_ref)`
   traces stored publication links and both legs of structural mention context,
   preserving alternatives and recorded unlinked requests (`literature_explanation@1`).
   Released in 0.13.0 `Card.explain_disease(disease_ref)` now explains MONDO disease
   groups with pinned association/selected-annotation support, identity/hierarchy
   steps, stored alternatives and whole-card ungrouped context. Versioned
   `disease_grouping@2`/`disease_group_explanation@2` (#115) retain all identity
   paths and leave conflicting or unfinished branches ungrouped. Explicit `@1`
   selection preserves historical behavior without replacing stored cards.
   Released in 0.13.0 `Card.explain_knowledge_state` now traces exact classification
   inputs, selected/alternative scientific support, coverage and request reports
   at original pins (`knowledge_state_explanation@1`). Missing support is partial;
   absence and missing queries never become negative assertions. #116 retains
   multiple original UniProt versions without changing the working state rule.
   Released in 0.13.0 measurement-group and molecule bioactivity-class explanations now
   retain actual joins, precision, copy/voter decisions, original quantities and
   exact pinned source support. Whole-card candidate/glossary context remains
   explicit. Released in 0.13.0 `Card.explain_ligand_site` and `Card.explain_ligand` now
   trace actual annotated overlap and protein/molecule crossing support at distinct
   card pins, with native deck snapshot/membership context. Duplicate members,
   absence/numbering/instance limits and original source conflicts remain explicit.
   Released in 0.13.0 `Card.explain_oligomer()` now retains actual partner/agreement rules,
   source assembly alternatives, exact family members, original support and
   historical pins under `oligomer_explanation@2`. The #120 correction defaults to
   agreement `@2`, computing only confirmed UniProt/1-based comparisons; unknown,
   incompatible or conflicted inputs keep explicit reasons and uncomputed sets.
   Explicit agreement `@1` reproduces the legacy view/explanation at historical
   pins. Readers remain inert; stored cards and packet source scope stay fixed.
   Other derived explanations remain open. The #118 correction counts distinct
   included groups across matched molecule items (`ligand_measurement_count@2`),
   retaining explicit source-record counts, selected rules and exact counted ids
   under `ligand_deck_explanation@2`. Explicit `@1` preserves the published numeric
   counter; scientific grouping/classes, stored cards and historical pins stay fixed.
   Missing activity-only copy diagnostics are corrected in #117.
4. **Literature beyond manual curation (#92).**
   - Released in 0.7.0: how each statement entered (`acquisition`: database, curation, rule
     extraction, model extraction, validation).
   - Released in 0.7.0: Europe PMC's text-mined accession mentions (`mentioned_in`). Its gene
     and protein annotations were reviewed and set aside: they ground names without
     the organism.
   - Released in 0.11.0: source access to located accession annotations for
     explicit articles (`get_annotations`), with provider, section and quote
     fragments. A public P60174 mention in a figure verifies the route. These
     fragments are not complete sentences. Released in 0.12.0:
     explicit UniProt accession intake into cards, with native article ids,
     per-occurrence locations and SourceAssertions, terms and refresh through the
     recorded article requests (schema 0.3.11). Supported PDB mentions are now
     derived `structure_mentioned_in` context through source-stated `has_structure`
     links, retaining both statements and separating them from direct UniProt
     mentions. Public 2JK2/Methods verifies it; unsupported 7QON remains unlinked.
     Released in 0.13.0: Sabueso runs `literal_uniprot_mention@1` on identified supplied
     fragments, returning detached per-occurrence SourceAssertions, supported
     relationships and original Ackredit attribution. It requires an explicit
     namespace/official URL; no names, bare accessions or biological findings.
     Explicit intake/replay is implemented for this literal rule through
     `Card.add_literature_extraction` and `ExtractionStore`: original support and
     supplied receipts survive reuse, storage and refresh without human relabeling.
     Payload-only refresh reports the missing original runtime sidecar. New scientific
     intake metadata uses published schema 0.3.12; 0.3.11 stays fixed.
     Explicit article metadata/declared terms are now implemented through
     `europepmc.get_article` and `article_metadata_binding@1`: source-stated identity,
     native authors/bibliography/licence, alternatives, original access/support and
     citations survive stored replay, refresh and pinned packet reads. Service
     version is not article revision; no abstract or full text is projected.
     Next: supplied-fragment rights, broader statement rules and validation; unknown
     fragment terms cannot bypass a source-admissibility profile.
     Literature packet coverage is published in `packet_aspects@6`
     (#71): both mention areas are indexed and their unknowns reported; automatic
     acquisition asks bibliography only, without guessing article ids.
   - Included in 0.11.0: a public review draft and hypothetical curation rehearsal
     (`examples/literature_curation/`), preserving outcomes and historical support on
     rebuild. The draft awaits human review; #105 prevents extraction provenance from
     being replaced with human curation during export/replay.
5. **Continuing, in parallel when a need or a slot appears:**
   - sources of wave 2 (#83), complete, orthology through OMA instead of Ensembl:
     ChEBI, KLIFS, GPCRdb, SAbDab, OMA and membrane segments through RCSB
     in use; the Chemical Probes Portal, SureChEMBL, OPM's own API, ESM Atlas and
     Ensembl deferred with their reasons; #85 closed through gnomAD's canonical transcript
     (follow-up #102). iPPI-DB, VEuPathDB and TDR Targets wait on #84;
   - isoforms and variants by tissue (#102): done in 0.10.0 (gnomAD's pext,
     `pext_at_variant@1`, `isoform_exon_usage@2`, tissues as GTEx's UBERON and EFO
     terms). Isoforms without a stated transcript stay without exons (Sabueso does not
     align); exons from Ensembl for the few transcripts gnomAD lacks, when a use needs
     them;
   - local mirrors in real work (#101): ChEMBL as a mirror, and builds from cached
     sources; postponed by the maintainers on 2026-10-01;
   - knowledge packets: real use decides their aspects (#71); an index level by
     reference since 0.10.0 (`packet_index@1`, #88), accepted in uibcdf/moli#22;
   - the clinical layer: adverse events (openFDA), after a terms review; isoform
     sequences (#80);
   - peptide cards: scope them before any source (use case 5, CPPsite).
6. **Contracts with other MOLI components**, raised in uibcdf/moli when those
   components are ready:
   - the reference form (uibcdf/moli#3, #53) and knowledge packets (uibcdf/moli#22);
   - exchange with TopoMT (positions, interface mutations), MolSysViewer (features to
     show) and PharmacophoreMT (ligand decks). Use cases 3, 4 and 7 are partial for
     want of these.
   - required Ackredit attribution for knowledge pipelines (#108, moli#36): the
     automatic packet-composition adapter and public offline workflow are
     implemented against the accepted portable contract assigned to Ackredit's
     published 0.9.0 provider (ackredit#75). Traceability is mandatory: the first
     source-acquisition slice records built-in UniProt/Europe PMC/RCSB access, including
     fixture/reuse/replay, empty answers, failure and original response identities,
     automatically on cards, resolutions and one-call packets. The public pilot
     saves those detached traces and credits completed access in the workflow.
     Released in 0.13.0 adds ChEMBL bioactivities, assay activities, molecules
     and indication operations: pagination/chunks, source totals/caps, original
     document citations, retries and received-page subsets remain observable even
     when the original exception escapes. Client-reported cached releases are
     explicitly not per-page release proof.
     Released in 0.13.0 also covers PubChem compound properties, structure
     matches and BioAssay target queries, including native per-assay revisions,
     caps/batches, PubMed pointers, declarative depositors, rejected inputs and
     received subsets on later failure. Unstated global versions remain unknown;
     assay summaries do not prove versions of every row or compound property.
     BindingDB REST/fixture/mirror affinity queries are also observed, retaining
     queries/cutoff bases, totals/caps/order, DOI/PubMed forms, declared origins and
     mirror manifests/releases, including empty and failed queries. REST versions
     remain unknown. The source-local #114 fix recognizes documented empty-string
     absence while malformed responses remain failed, retaining wire/archive identity.
     Released in 0.13.0 CCD batches and UniChem InChIKey/source-id
     lookups now retain query/response identities, reuse, retry/empty/failure outcomes
     and completed subsets. Linked databases stay declarative; versions stay unknown.
     Molecular resolution and ligand decks keep detached input/result pins and
     original resource-description citations without changing stored card/deck science.
     PDBe-KB ligand-site/interface aggregates also retain separate queries,
     native structural reference forms, archive reuse, empty answers and failures.
     Versions and missing underlying citations stay unknown; listed providers and
     structures do not become additional direct access.
     AlphaFold DB model queries retain original per-record ids/versions,
     tool/provider/URL declarations, archive reuse, empty lists and failures.
     Model versions do not become database releases or experimental revisions;
     generation and coordinate download are not executed by this access.
     InterPro family-site residue queries retain native signatures, locations,
     header/fixture releases, archive reuse and distinct empty/unavailable/failure
     outcomes. Empty answers cannot establish accession existence. Member-database
     declarations do not claim direct access, alignment or InterProScan execution;
     missing site/signature citations and release versions remain explicit.
     Other sources/custom clients, further result types and complete resource
     bibliography remain coverage work with explicit gaps in the published 0.13.0
     scope (#108). Ackredit 0.9.0 is publicly qualified on Python 3.11–3.14;
     its published minimum and exact public pins replace the source overlay and
     release blocker. Sabueso's own exact `py_1` archive passes all installed
     OS/minor gates, public installation and archival under #110. The provider interpreter contract is delivered under
     ackredit#80, without metadata overrides. The provider corrected explicit
     author-object BibTeX rendering in ackredit#78; the pinned candidate includes it.
     Knowledge support, runtime use and terms retain
     their separate meanings; scientific payloads are unchanged.
     MOLI owns ProjectRecord composition and future Recorda routing; the local trace
     is a receiving experiment, not an implemented platform provenance contract.
     Released in 0.13.0 `examples/persisted_pipeline/` exercises separate producer, reader
     and reuse processes: full/index packets, exact historical item reads, original
     extraction/article support and workflow credit survive reacquisition.
     Missing/changed/misbound sidecars and inconsistent workflow context are refused.
     Consumer-owned Nextia interpretation and shared Recorda/ProjectRecord acceptance
     remain with their owners.

Each is proposed as an issue before work starts, and the order is revisited at each
release.
