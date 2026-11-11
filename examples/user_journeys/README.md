# Independent scientific user journeys

These examples exercise the approved roadmap after 0.13.0 (#112). They use public
Sabueso APIs, public test systems and frozen responses declared in
`temp_data/NOTICE.md`. These examples are development work in this
checkout; its local validation is separate from published-package qualification.

## Human Card exploration

### Combined protein contexts

`protein_context_review.py` reviews seven existing B6 routes: retained comparative
records, explicit sequence and knowledge differences, variants, isoform/tissue
usage, sequence annotations and biological associations. It uses public TcTIM,
Q4DV43 and HsTIM fixtures, retains two original saved sessions and checks complete
human/agent/source parity when reopened in a separate process without fixtures.

```bash
python examples/user_journeys/protein_context_review.py produce --fixtures temp_data --output /tmp/sabueso-protein-context-review
python examples/user_journeys/protein_context_review.py read --output /tmp/sabueso-protein-context-review
```

Start with an empty output directory and keep all three output files. Equal
positions do not establish correspondence; associations do not establish
causality. This is technical preparation. The
[researcher tasks and acceptance record](../../devguide/pending_proposals/protein_context_review_walkthrough.md)
keep human/scientific acceptance separate.

### TcTIM annotation, ligands and assembly source review

```bash
python examples/user_journeys/structural_source_review.py produce --fixtures temp_data --output /tmp/sabueso-structural-source-review
python examples/user_journeys/structural_source_review.py read --output /tmp/sabueso-structural-source-review
```

Use an empty directory and keep all three files. The public 1SUX route connects
the original annotation with chain gaps/numbering, BTS/SO4 instances, complete
original contact collections, sources and twelve assembly declaration positions.
Unresolved K/L remain unresolved. A separate historical session retains its
missing native annotation scope. The finite assembly agent request is the current
saved root; its access context differs from the source-navigation destination.
Reading needs no fixtures or coordinate engine. The
[researcher tasks](../../devguide/pending_proposals/structural_source_review_walkthrough.md)
keep scientific/human acceptance and physical-copy calculations separate.

### TcTIM structure, source context and an explicit modeling control

```bash
python examples/user_journeys/structural_context.py produce --fixtures temp_data --output /tmp/sabueso-structural-context
python examples/user_journeys/structural_context.py read --output /tmp/sabueso-structural-context
```

Choose a new output directory. The example follows the original UniProt annotation
at position 96, selects the exact 1TCD structure, opens its assembly question and
visits the original component records. Compact agent access shares the human
result. One gzip file retains the whole visited session; reopening it restores
these routes without querying sources or rebuilding the Card. Other structures
listed by UniProt have no new RCSB receiving in this example.

The separate, optional modeling command requires the qualified MolSysMT source
described in the [B3 record](../../devguide/pending_proposals/structural_journey_acceptance_20261104.md#public-tctim-correspondence-journey--2026-11-05-utc):

```bash
python examples/user_journeys/structural_context.py model --output /tmp/sabueso-structural-context --coordinates temp_data/rcsb_structural_context/coordinates/1tcd.bcif.gz
python examples/user_journeys/structural_context.py read --output /tmp/sabueso-structural-context
```

Before construction, the consumer checks the original entry/revision, generator,
operation, entity/instance IDs, source-declared sequence and numbering axes, model
and alternate-location scope. This bounded control accepts the retained 1TCD
identity operation. Its source-declared alignment maps entity position 94 to
UniProt position 96. Missing historical revisions and incompatible inputs are
refused before invoking the builder.

RCSB and the coordinate file both declare entry revision 1.4 (2024-05-22).
The Card resolves polymer A/B but retains C/D as unresolved keys; the coordinate
file explicitly identifies C/D as water. Both source scopes remain visible.
The calculation records 3,983 atoms and 276 C-alpha A/B pairs within an inclusive
1 nm cutoff, without periodic images, atom-group centers or group reduction.
An independent squared-distance calculation checks the producer's result.
These distances do not establish binding or biological interface relevance.

The original Card and saved knowledge stay unchanged. The file, complete contact-pair list, atom/operation
correspondence and calculation log remain separate, with their original producer,
units, input hashes and scope. Pair indices are zero-based generated-atom indices;
UniProt positions are one-based. The reader checks these example-local file bindings
and shows the recorded result without recalculating; it is not a general geometric
result verifier or a shared MolI interchange contract. Native saved Card science
retains its existing independent verification. This one-model control does not
qualify fragments, isoforms, heterogeneous assemblies or physical-copy uniqueness.

### Protein, molecule and disease orientation

The development `card.explore()` API has a small, offline walkthrough for public
TcTIM, benznidazole and MONDO:0014221:

```bash
python examples/user_journeys/card_exploration.py produce --output /tmp/sabueso-card-exploration --fixtures temp_data
python examples/user_journeys/card_exploration.py read --output /tmp/sabueso-card-exploration
```

Use an empty output directory. Read the script alongside its printed questions
and actual API responses, or try its calls in a notebook. It demonstrates
orientation, scientific questions, labeled selection, original support/source
links, empty-filter recovery and portable original reading. The molecule retains
units and source methods; disease parents remain distinct from equivalence and
unsupplied destination Cards. New structural explanations show readable original
state/rules/options and direct relationship source records; complete scientific
detail remains inspectable. Earlier saved items keep their original organization.

The three saved files use the ordinary exploration format. They include complete
contributing captures and original support, beyond the visible selection.
`receipts.json` retains their bundle digests and original view references for this
example; it is not a new SDK persistence format. The separate `read` invocation
uses no fixture files and makes no source requests. Both commands forbid network
connections. This is technical preparation for researcher review, not measured
usability or delivery in the released 0.14.0 package. The bounded
[first-version audit](../../devguide/pending_proposals/card_exploration_v1_closeout.md)
records the remaining acceptance work.

The protein walkthrough now also opens original sequence/annotation fields,
predicted model declarations and site/contact statements with their sources.
Its saved reading can revisit those exact retained panels; earlier bundles report
unretained panel variants as `not_saved`. Derived model coverage and site/instance
overlap integration remain separate from these source views.

### Publication links, original support and scoped unknowns

```bash
python examples/user_journeys/publication_context.py --fixtures temp_data
```

This offline development walkthrough uses the shared `literature` topic and
`publications` question. It selects TcTIM's exact PMID 20889239, opens all 459
retained relationship links and projects the same member through compact agent
access. Counts describe source activity records, not independent experiments.
HsTIM's PMID 40832834 context follows original SourceAssertions, relationships
and located structure mentions, preserving both support legs for 2JK2 and three
unlinked 7QON occurrences. Bounded previews leave complete native data readable;
`back()` returns to each originating selection.

An exact reference with no stored link returns `not_on_card`; a separate empty
Europe PMC annotation response coexists with retained publications. Neither
establishes absence from an article or the literature. Network connections are
forbidden, and exploration acquires no articles or new metadata. Publication
profile saving uses the separately versioned original reader after a genuine
clean SDK202 capture. Reading verifies retained requests and source context without
source acquisition or current scientific readers. Scientific review, researcher
acceptance and released-package qualification remain separate gates.

## Clinical bibliography

```bash
python examples/user_journeys/clinical_bibliography.py produce --output /tmp/sabueso-clinical-bibliography --fixtures temp_data
python examples/user_journeys/clinical_bibliography.py read --output /tmp/sabueso-clinical-bibliography
python examples/user_journeys/clinical_bibliography.py reacquire --output /tmp/sabueso-clinical-bibliography --fixtures temp_data
python examples/user_journeys/clinical_bibliography.py read --output /tmp/sabueso-clinical-bibliography
```

Use an empty output directory. This development example starts with the unchanged
molecule/target journey in `molecules/`. From benznidazole's pinned ChEMBL
indication statements, it explicitly selects NCT00123916 for registry references,
then PMID 18585495, 26323937 and 19753491 for Europe PMC metadata. Each article
query requires that PMID in the returned registry references. It preserves native
reference types, separate indications, original personal/collective authors and
all supporting SourceAssertions. It never matches intervention names or parses
free citations into publication identity.

The example-local `sabueso.clinical_bibliography_example@1` saves source envelopes,
per-result acquisition sidecars, a separate clinical workflow, JSON/Markdown and
CSL/BibTeX. The molecular workflow remains beside its original input, rather than
being presented as a new clinical acquisition. Fifteen other source-cited trials,
registry websites and other reference forms remain unqueried. Trial status,
design/results, full text, efficacy and protocol curation are outside scope.
Missing local metadata remains unavailable, never evidence of source absence.

Independent reading uses no fixtures, source access, SDK scientific views or new
credit. It verifies pinned indication support, exact operation scopes, native
metadata, original bibliography and report consistency. Reacquisition repeats only
the bounded clinical queries; original cards, reports, workflow and exports remain
byte-identical. The old molecular `@1` and disease `@1`–`@5` formats keep their
original unqueried clinical scope. This is fixture-based development acceptance,
separate from current live availability, scientific review and release delivery.

## Protein and comparator

### Structure, assay and located-literature dossier

```bash
python examples/user_journeys/scientific_dossier.py produce --output /tmp/sabueso-scientific-dossier --fixtures temp_data
python examples/user_journeys/scientific_dossier.py read --output /tmp/sabueso-scientific-dossier
python examples/user_journeys/scientific_dossier.py reacquire --output /tmp/sabueso-scientific-dossier --fixtures temp_data
python examples/user_journeys/scientific_dossier.py read --output /tmp/sabueso-scientific-dossier
```

Use an empty output directory. This example asks which stored TcTIM/HsTIM
structures and assay records meet explicit illustrative criteria, and which
located literature mentions are available. It creates readable per-stage
`dossier.md` files alongside complete JSON, exact pinned cards in `knowledge.db`,
original acquisition/credit sidecars and reader bibliography exports.

Structural criteria are resolution at most 3 angstrom, coverage at least 0.9,
source-reference sequence, an author-assigned homo dimer and observed coverage
of completely supported source active-site positions. Every criterion reports
met, not met or unknown. The example preserves author numbering, mutations,
fragments, alternate assemblies and disagreements. Source-reference does not
universally mean wild type. Equal positions across the proteins are not aligned.
Meeting these illustrative criteria is not project model selection.

Assay rows preserve the stated measurement and normalized quantity separately,
target assignment, full original qualifiers, conditions and exact support.
The example rule asks for direct assignment D, IC50, equality and a normalized
concentration; eligible records still require human comparability review.
ChEMBL and BindingDB requests are explicitly capped at 25 records per source.
Partial source coverage is retained, not presented as a complete potency survey.

The stored-context table exposes source activity/target and assay identifiers,
organism/taxon, confidence, stated target variant, original publication pointers
and measurement notes. `stored_assay_context_review@1` marks named fields missing
from the saved qualifiers; it does not claim absence from the source. Protocol
curation and experimental comparability remain unestablished. Missing mutation
annotations do not establish wild type, and matching assay IDs, text or units
does not establish equivalent protocols.

Europe PMC annotations are explicitly requested for MED:18562316 and
PMC:PMC12400196. A located P60174 figure occurrence includes the returned
fragment, location and supporting assertions. It establishes an accession
mention; it is not a curated mechanistic finding. An empty annotation response
does not prove absence from an article. Full-text curation, selectivity,
molecule prioritization and project Evidence remain outside this example.

The example-local format `sabueso.scientific_dossier_example@3` uses existing SDK
APIs; it introduces no card or shared MOLI schema. Original producer versions
and the example source hash are recorded. Reacquisition advances stored heads
while preserving original results, pins, rules and credit. Independent reading
requires no fixtures or network, checks original support and refuses inconsistent
units, values, references, scope or overstated interpretation. Its dossier
derivation is explicitly not runtime-observed. These technical checks do not
replace scientific review or qualify a published installation.
The reader also verifies each complete criterion record against the pinned assay
qualifiers or saved structural inputs under its original rule. Rehashing a report
and regenerating its Markdown cannot turn a failed criterion into a met one, drop
criteria or invent the reason for an unknown result. This consistency check does
not authenticate source text. Format @3 checks its retained coordinate projection
and named rules using frozen original predicates, without calling current SDK
scientific readers or publishing a replacement result. Review criterion
`public_structure_review_criteria@2` requires admitted original coordinate/reference
support; unknown scope stays insufficient information. Unplaced declarations are
retained separately. Recorded normalized coverage ratios alone do not certify the
current reference.

Historical `@1` and `@2` dossiers remain readable in their original shape, rules and
rendering. `produce --legacy` selects @1; `produce --legacy 2` explicitly replays
the @2 family. These are policy replays, not purported genuine older producer
artifacts. Reacquisition retains the original format. Stored assay context remains
present in @2/@3 and absent in @1; new coordinates are never backfilled into old
reports.

### Comparative sequence and tissue support

Development pinned sequence/tissue support has a separate public example:

```bash
python examples/user_journeys/comparative_support.py produce --output /tmp/sabueso-comparative-support --fixtures temp_data
python examples/user_journeys/comparative_support.py read --output /tmp/sabueso-comparative-support
python examples/user_journeys/comparative_support.py reacquire --output /tmp/sabueso-comparative-support --fixtures temp_data
python examples/user_journeys/comparative_support.py read --output /tmp/sabueso-comparative-support
```

It retains P52270/Q4DV43 sequence and P60174 variant/isoform/term explanations at
exact pins. Original fields, assertions and genomic intersections remain
inspectable after later fixture reads. Readers require no fixtures and add no
source access, derivation or credit. New reports use format `@3`, preserving
coordinate scope and per-tissue coverage (#138), observed comparative operation
`@2` and original bibliography (#108). `produce --legacy` creates historical `@1`;
`produce --unobserved` creates `@2` without the original runtime sidecars.
Reacquisition retains the original format and rules; readers support all three. These
examples are outside published 0.14.0 and preserve the other journey formats.

From the repository root, with this checkout installed editable:

```bash
python examples/user_journeys/protein_comparison.py produce --output /tmp/sabueso-comparison --fixtures temp_data
python examples/user_journeys/protein_comparison.py read --output /tmp/sabueso-comparison
python examples/user_journeys/protein_comparison.py reacquire --output /tmp/sabueso-comparison --fixtures temp_data
python examples/user_journeys/protein_comparison.py read --output /tmp/sabueso-comparison
```

Use an empty output directory for `produce`. Each command starts a separate
process. The reader needs the output bundle and installed dependencies, but no
fixture directory; it refuses incomplete or inconsistent original records.
Network access is forbidden for every command.

The journey resolves triosephosphate isomerase by name and organism: TcTIM
(P52270, taxon 5693) and HsTIM (P60174, taxon 9606). It retains the resolution's
identity audit and alternatives, explicitly asks for two RCSB structures per
protein, collects ChEMBL/BindingDB activities and source-stated UniChem identity,
and builds molecular ligand decks from ChEMBL/CCD statements.

It compares fields, relationships and ligand knowledge, preserves measurement
types/units and named derivation rules, and saves supporting SourceAssertions at
exact card pins. Original reports also explain one activity, measurement group and
shared-ligand crossing per protein as representative supported results.
No residue map is supplied: equal residue numbers are not aligned
positions, so positional comparisons remain `not_compared`. A shared ligand does
not establish selectivity, binding at a particular site or equivalence of assays.

The output holds:

- `knowledge.db`: historical protein/molecule cards, ligand decks and full/index
  packets with both proteins;
- per-stage reports with original comparisons, resolution decisions, conflicts,
  alternatives, knowledge states, source coverage and redistribution terms;
- original acquisition traces, observed operations, per-packet attribution and
  enclosing Ackredit workflow attribution;
- manifests binding exact scientific references and original sidecar digests;
- reader reports and original CSL-JSON/BibTeX reference exports.

Views may contain PyUnitWizard quantities. The example serializes them as
`{value, unit}` in their own units; it never stringifies or discards a unit.
Reacquisition reads the same frozen responses at a later fixture-read time,
advancing current heads while preserving the original scientific results, pins,
versions and bibliography. It is not a fresh public download or a new database
release. The reader exports the original producer's report rather than rerunning
its derivations under a newer reader version.

## Molecules against a declared target

```bash
python examples/user_journeys/molecule_target.py produce --output /tmp/sabueso-molecule-target --fixtures temp_data
python examples/user_journeys/molecule_target.py read --output /tmp/sabueso-molecule-target
python examples/user_journeys/molecule_target.py reacquire --output /tmp/sabueso-molecule-target --fixtures temp_data
python examples/user_journeys/molecule_target.py read --output /tmp/sabueso-molecule-target
```

The target is explicitly TcTIM (P52270), with ChEMBL activities and the requested
RCSB structure 1SUX. The selected molecules are BTS (CHEMBL1161789) and benznidazole
(CHEMBL110). ChEMBL/CCD/UniChem statements anchor their identity; no name or
structure similarity establishes a join. The two-member deck records the supplied
identifiers as its selection basis. Unmatched activity records belong to other
molecules outside this selection, not failed molecular identities.

BTS has a reported IC50 of 33,000 nM and structural context in 1SUX. Benznidazole
has an 18% inhibition measurement whose assay text states 400 micromolar and another record without a
determined value. Their assay descriptions, target assignment, publications,
source versions, original statements, grouping/classification rules and parameters
remain inspectable. Current molecule example @2 uses conservative activity @4:
the isolated inhibition stays `inconclusive`, with its percentage and original
assay text retained; no potency or compound dose is inferred from that text.
BTS remains `weak` and the unmeasured record `not_determined`. These are scoped
rule outputs, not universal activity, binding-site or clinical conclusions.
Original molecule example @1 and protein comparison @1/@2 remain readable without
recomputing their activity classes; new protein comparison @3 uses current policy
and packet mapping @15.

ChEMBL also reports four benznidazole indication rows, a maximum clinical phase and
16 cited NCT ids. The EFO/MONDO/DOID disease references remain separate. Trials are
explicitly not fetched; BTS indications, other targets and BindingDB activities
are not queried. Missing benznidazole UniChem fixture data is observed as
unavailable, not proof of missing external identity. Linked PubChem/DrugBank ids
do not mean those sources were accessed. Complete clinical coverage remains pending.

The bundle stores all three cards, their exact relationship/statement support,
the selected deck and an index packet for the **target context**. This packet is
not molecule-filtered; the producer's separate report declares the narrower
question. Independent readers verify native molecular/deck pins, assay and identity
links, original operation/workflow attribution and historical packet support,
without fetching fixtures, rerunning scientific derivations or generating credit.
Historical `knowledge_state@4` can incorrectly report successful CCD/UniChem intake
as `not_stated`. `knowledge_state@5`, delivered in 0.14.0, corrects native record counts,
retains unknown counts/missing subsets and separates clinical intake
([#122](https://github.com/uibcdf/sabueso/issues/122)). Readers retain the original
report and its named rules; original statements and observed queries stay available.

The full original explanations deliberately retain broad classification context:
the current frozen example produces about 30 MB of report JSON per acquisition.
The reader loads each pinned card once and inspects its item stores, avoiding
repeated deserialization for thousands of contextual links. This measured example
does not establish an export-size or performance guarantee (#98/#88).

The script reuses file/quantity/network helpers in `protein_comparison.py`; keep
both scripts together when copying the example outside the repository.

## Coverage and limits

These are explicit source/fixture subsets, not all known structures or ligands.
The 1IIG RCSB fixture is deliberately unavailable; this is not an assertion that
RCSB has no such structure. A source can be partial, unqueried or unavailable even
when the application finishes successfully. Inspect the per-query acquisition
outcomes, source totals/caps and knowledge-state rows before interpreting a result.

Runtime observation is bounded by the installed Sabueso adapters. Original JSON
must travel beside the scientific store; payload-only reads cannot recreate an
earlier execution. Bibliography does not grant data-reuse rights. Terms reports
describe the packaged registry at production, not perpetual permission.

The manifest is local to this example. Hashes detect changed files and references;
they do not authenticate a source or implement MOLI ProjectRecord/Recorda storage.
An interrupted producer can leave an incomplete bundle, which the reader refuses.
No Nextia Evidence is created.

## Diseases and related entities

```bash
python examples/user_journeys/disease_entities.py produce --output /tmp/sabueso-disease-entities --fixtures temp_data
python examples/user_journeys/disease_entities.py read --output /tmp/sabueso-disease-entities
python examples/user_journeys/disease_entities.py reacquire --output /tmp/sabueso-disease-entities --fixtures temp_data
python examples/user_journeys/disease_entities.py read --output /tmp/sabueso-disease-entities
```

Copy all three scripts together for an independent installed-SDK check. The disease
script uses the other scripts' file/quantity/network and support-inspection helpers;
these remain example-local, without a shared serialization contract.

Two separate MONDO-anchored diseases exercise target and drug decks: Orphanet 868
(triosephosphate isomerase deficiency) and MeSH D014355 (Chagas disease). No link
between those two diseases is inferred. The example keeps exact MONDO/card support,
original Open Targets/Orphanet membership bases and ChEMBL indication rows,
unbuilt/capped candidates and original HsTIM disease-group explanations, including
ungrouped identity paths. Related EFO:0001360 remains unresolved. Efficacy, new
approval judgments and disease packets are outside the declared query scope.

Format `@6` adds a separate benznidazole card with `trials={"limit": 1}`. ChEMBL's
explicit indication references supply the NCT identity; intervention names never
join a study to a molecule. The report's `clinical` section retains one received
study (NCT00123916), four indications and fifteen unfetched trials. The original
drug-deck member remains a separate pinned state of the same molecule.
The example explicitly asks for that study's reference module and Europe PMC
metadata for PMID 18585495, 26323937 and 19753491. The three publications' complete
returned author lists include the literal BENEFIT Investigators collective name.

Registry pointers and separately consulted article metadata keep their own source
operations, native versions, raw records, missing fields and credit. The study and
reference fixtures have different data timestamps; they do not establish one
coherent current source revision. Empty complete queries differ from failed or
unavailable access. See-also websites, article text and participant data remain
unqueried. The stored `has_results` flag does not establish whether publications
exist or what treatment effect they report. No efficacy interpretation is made.

The reader checks historical item support and original membership metadata rather
than recreating them under its own rules. Original available runtime attribution
and CSL-JSON/BibTeX survive reacquisition. Missing/misbound files, wrong members,
altered support/bases and overstated coverage fail before reference export.

Development rules `@2` now preserve exact membership SourceAssertion pins, original
MONDO input and member identity, including unbuilt/capped candidates (#91).
The example `@6` reader also accepts original `@1`–`@5` reports, keeping their
support and observation gaps rather than recreating old knowledge. Exported decks carry embedded support;
saving the deck alone into an empty store makes its scientific pins resolvable.
Deck terms include that content. Development `disease_deck_admission@1` requires
admissible whole embedded context and filters unchanged member cards by all stored
statements. Shared unknown/restricted terms refuse; finer filtering by terms of use remains pending
(#29). Separate SDK tests cover admission. Reacquiring an original `@5` bundle
keeps its pre-clinical scope and `@5` format; older original reports remain intact
and their existing pre-clinical reacquisition route remains `@5`.

Development MONDO term/equivalence access now retains original index/release
observations and bibliography. Open Targets/Orphanet queries and disease-deck builds
also retain native page/file/version/time, source outcomes and original input/result
pins. DISEASES/ClinVar/MedGen source access is also observed (#108/#125).
Acceptance remains partial: broader underlying study bibliography is incomplete. Stored card data never
establishes new source credit.
Source totals, attempted candidates and built cards are distinct scopes; the example
reports each without interpreting a fixture gap as external absence. Keep all files
beside the store; hashes are consistency checks, not authenticity or permissions.
Native ChEMBL indication references now enter workflow attribution with original
row/page occurrence scope and explicit unfetched-target/missing-metadata gaps.
New `@6` source envelopes are bound to their own original operations before the
reader exports references. Rehashed changes to clinical values, source bodies,
queries, trace bindings and access scope are refused. Original reports and their
declared gaps stay unchanged. Complete underlying study bibliography and finer
filtering by terms of use remain pending. Broader molecular reverse queries and
clinical observation remain separate work.
The #122 correction was delivered in 0.14.0; historical reports retain their original rules.

## Located primary-source review draft

```bash
python examples/user_journeys/literature_source_review.py produce --output /tmp/sabueso-located-source --fixtures temp_data
python examples/user_journeys/literature_source_review.py read --output /tmp/sabueso-located-source
```

Example `sabueso.located_source_review_example@2` prepares two structural readings
from Kontellas et al. (2025), DOI 10.1107/S2053230X25006454. It preserves unchanged
CC BY 4.0 XML, original fragments, locators and short quotations. Figure 4 states
human accession P60174; native UniProt support links that entry to PDB 2JK2.
No similarity or residue correspondence establishes identity.

Codex is the agent preparer; scientist review is pending. The readings remain
in `proposals.json`, never in curated card knowledge. The pinned baseline card
retains its original assertions. The reader rejects imported claims/curations,
modified or overstated drafts and the unqualified initial `@1` format, without
new source access, views, curation or credit. Original references are preserved.
An agent draft cannot become human curation merely by naming a curator.

The native full-text download is a supplied public input, separate from
SDK-observed fixture entry/article-metadata access. Draft execution observation
is explicitly absent. These readings do not establish inhibition/selectivity,
transfer parasite experiments to HsTIM, execute modeling, supply ChEMBL assay
protocols or create project Evidence. Copy this script and `protein_comparison.py`
together for independent use. See the
[located review](../../devguide/pending_proposals/located_source_review.md) for
qualification, the provenance correction and remaining work.
