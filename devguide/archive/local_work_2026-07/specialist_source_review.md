# Specialist prototype qualification (2026-10-06)

The preserved specialist/structural-context mappers accepted caller-supplied
synthetic rows. Their tests established old local scenarios, not native API shape,
source identity, units, experimental support or permitted reuse. This review records
what is recovered under current contracts and what remains explicitly deferred.
All data used here is public; the original stash and exported files remain intact.

## AmyPro: recovered native entry and regions

The old `protein_specialist.py::map_amypro` defaulted missing categories to
`amyloidogenic` and assigned an `experimental` class. Its test had a synthetic
`AP0001` region, with no investigated-sequence support or qualified native access.
The current reader requires one actual `AP` plus five-digit entry ID.

The [official help](https://amypro.net/#/help) and header link a
[complete JSON export](https://amypro.net/data/amypro.json). The received unmodified
array contains 125 entries and 156 regions, 115711 bytes, SHA-256
`9b7d31b89406499611cbd6d349eaaaa8cdd4d065c3fc964c5bbfd51379770cdd`.
All regions match their investigated sequence peptides. Individual documented
downloads such as `data/entries/AP00007.json` currently contain Python dictionary
literals despite their JSON content type. They are not used, repaired or evaluated.
The native bulk export remains the envelope record and is validated before selection.

AP00015 (alpha-synuclein, native parent pointer P37840) yields entry context and
three regions, with subject `amypro:AP00015` and sequence axis `AmyPro:AP00015`.
AP00007's 691-residue processed lactoferrin entry declares parent bounds 20–710;
region 538–545 belongs to the investigated entry sequence. AP00012 and AP00009
have parent bounds inconsistent with their entry lengths. These remain literal
source declarations, without an offset, identity merge or current UniProt projection.
Mutation strings can describe insertions; they are not interpreted as substitutions.
Native category and `True`/`False` prion strings are not knowledge classifications.

The export has entry-level PubMed pointers but no per-region method/publication
assignment. Keep those gaps explicit; the
[resource paper](https://doi.org/10.1093/nar/gkx950) describes the database separately.
No linked article, parent sequence, coordinate, search or calculation job is acquired.
Fifteen entries have explicitly empty region dictionaries and still retain context.
Missing selection is not listed in this received export, not biological absence.
No native total or current export/record/sequence revision is supplied; website/footer
and HTTP Last-Modified dates do not establish scientific record revisions.

Separate data reuse rights were not established on the provider help/download/footer
pages. NOT-STATED remains unknown; the paper's CC BY-NC 4.0 is not assigned to the
export. The unchanged public fixture is declared locally in `temp_data/NOTICE.md`;
no public-package or redistribution qualification is claimed.

## ConSurfDB: deferred native/reuse qualification

The [official overview](https://consurfdb.tau.ac.il/) describes precomputed
conservation profiles. Its [terms](https://consurfdb.tau.ac.il/terms/) restrict use
to academic end users in noncommercial research, excluding commercially sponsored
work, and prohibit providing products/services or transferring database content to
third parties. Nonacademic users must obtain provider terms separately.

Only public documentation was read; no result data or native fixture was downloaded.
The old synthetic grade-9 row does not qualify a chain/sequence/alignment contract,
score uncertainty, calculation version, representation basis or reuse permission.
Revisit after the intended permitted access/reuse scope and native result contract
are established. Site-wide update dates are not per-chain scientific revisions.

## FireProtDB: deferred v2 measurement/reuse qualification

The [official v2 API documentation](https://loschmidt.chemi.muni.cz/fireprotdb/api-docs/)
distinguishes sequence-experiment entries from mutant-experiment entries, with
source/target sequences and absolute/relative measurements. Its search uses JSON
expression trees, not a guessed protein-name or gene-name identity join.
The [service terms](https://loschmidt.chemi.muni.cz/fireprotdb/terms-of-use/) grant
service access and restrict transfer of output rights; a separate data export grant
was not established. Only documentation was read, without experiment downloads.

The old synthetic `G42A`, bare ddG `1.2 kcal/mol`, temperature `298.15` row does not
state native sign convention, temperature scale/meaning, method, assay conditions,
source/target sequence identity or experiment revision. Preserve the requirements
without assigning an experimental class. Revisit once reuse/fixture-sharing scope
and native v2 quantities, sign conventions, conditions and revisions are qualified.

## SWISS-MODEL Repository: full native metadata recovery

The [official API](https://swissmodel.expasy.org/repository/api-docs) and
[embedded native v2 contract](https://swissmodel.expasy.org/repository/api-docs.json)
document unfiltered metadata, including experimental PDB references and precomputed
homology models. The preserved projection lost native target sequence/alignment
context and used a mutable ModelCIF URL or template as a model identifier. The qualified reader keeps the
whole response, with independent row occurrences rather than a selected model.

P60174 returns 29 PDB references and one SWISSMODEL model, template `4poc.1.A`,
with 57 paired chain alignments. The MD5 is documented as the full target sequence
checksum, not a model identity. Target length/MD5 and every target peptide/alignment
column count are checked against the returned 249-residue sequence. CRC64 is retained
as a source literal. Template/PDB bounds have their own numbering basis; no current
UniProt or structural author/label projection is inferred. `in_complex_with` is
served as a dictionary in the native fixture despite the OpenAPI array declaration;
actual JSON context is preserved without inventing a resolved complex identity.

Native QMEAN is a dictionary containing negative, positive and error values. GMQE,
identity, coverage, similarity and QSQE remain source literals without rescoring or
an assigned probability/quality class. Zero/null/missing values stay distinct. Raw
ligand/complex context does not declare observed target binding. The unfiltered
received array has no independent total/current database completeness contract.

[Official help](https://swissmodel.expasy.org/docs/repository_help) explicitly says
model download URLs can change and models may disappear during continuous updates.
Coordinate/ModelCIF pointers do not pin models and are unqueried. API version, query
date and model-creation/PDB-release dates are separate from unknown metadata/model/
sequence revisions. The public metadata request needs no model submission or account.

[Official terms](https://swissmodel.expasy.org/docs/terms_of_use), reviewed 2026-10-06,
grant CC BY-SA 4.0 for generated data, with attribution, a licence link, change
indication and share-alike for adaptations. Parent PDB/UniProt inputs and article
rights remain separate. Beta-service restrictions are not assigned to public
Repository access. The provider-requested resource/method citations are Bienert
et al. (2017), doi:10.1093/nar/gkw1132 and Waterhouse et al. (2018),
doi:10.1093/nar/gky427; neither supplies the primary publications of individual
PDB/template entries. No linked files/articles/sequences or jobs are fetched.

The maintained registry records AmyPro and SWISS-MODEL Repository in use and
ConSurfDB/FireProtDB deferred.
The historical catalog still preserves all 87 original declarations; its current
comparison is 45 in use, 11 deferred, 27 evaluating, 3 retired, 1 out of scope and
0 not registered. After the WikiPathways follow-up, twenty-one batch candidates are reviewed and still await
integration; see [batch 01](batch_01_source_review.md),
[batch 02](batch_02_source_review.md), [batch 03](batch_03_source_review.md) and
[batch 04](batch_04_source_review.md), [batch 05](batch_05_source_review.md) and
[batch 06](batch_06_source_review.md). Native DrugCentral observations, CIViC monthly
profile items and EMA orphan-designation pages are recovered. The final two-source
batch completes candidate triage; it does not complete every pending integration.
Registry groups are metadata, not automatic acquisition profiles.

## APPRIS: native default gene annotation occurrences

The preserved `protein_drug_discovery.map_appris` grouped rows by transcript and
updated principal attributes in place. The native default TPI1 exporter contains
1010 rows and 60 principal declarations for 21 transcript references. Five
principal rows for ENST00000396705 retain different labels, names, genomic starts
and RNA lengths. Equal rows and conflicting declarations remain independent.
Full source-gene query binding and validation replace synthetic old fixtures;
no protein identity or principal selection follows from those gene/transcript IDs.

The [official exporter contract](https://apprisws.bioinfo.cnio.es/apidoc/gold/exporter)
documents optional methods, assembly, reference-set and dataset selectors. This
qualified route adds none, retaining provider-default received rows. The returned
array does not state dataset/assembly/record/transcript/sequence revisions or an
independent total. The documented default assembly is not assigned to all rows;
observed different coordinates/names remain literal unknown context. Native
APPRIS/FIRESTAR/CRASH/CORSAIR labels, score/flag strings and free-text
`pep_position`/ligand notes do not create residue locations, binding relationships,
experimental classes or MOLI Evidence. No linked sequence/coordinate/method/article,
job, card enrichment or dataset-selector route is qualified here.

The [official licence](https://appris.bioinfo.cnio.es/partials/license.html), read
2026-10-06, explicitly states CC BY-NC-SA 4.0. Both noncommercial and share-alike
obligations are classified by existing terms propagation and retention. Linked
input resources and publications retain independent rights. The unchanged public
252247-byte fixture retains SHA-256
`e9b7a1f300e76ac359bfc845af03b28f043c9c5b6db14b41a670dd6794de5a95`.
Original exact fixture retrieval time is unrecorded; it is not invented from dates.

## SIGNOR: headerless native causal interaction occurrences

The preserved `protein_sources.fetch_signor` used the valid documented endpoint,
but decoded its headerless response with DictReader, losing the first interaction
and naming fields from that row's values. `protein_context.map_signor` expected
synthetic named columns and assigned a curated class. Current mapping validates
all original rows in the [documented order](https://signor.uniroma2.it/APIs.php),
including an observed optional empty trailer, and retains each occurrence without
invented classes. HsTIM returns three rows, beginning with SRC regulating TPI1.
Native regulator/target, effects, mechanisms, DIRECT and residue/sequence/score/
publication/context strings remain unprojected source declarations.

AKT1 requested with 9606 returns 456 rows: 355 with TAX_ID 9606, 36 with 10090,
four with 10116, five with 9534, 41 with -1 and 15 blank. The
[official curation manual](https://signor.uniroma2.it/documentation/SIGNOR_curation_manual_July_2021.docx)
identifies -1 as in-vitro context and A/B as regulator/regulated. No row is relabelled
from the organism request. Complex/family/chemical/phenotype and self-interaction
references remain original; no complex expansion or generic physical binding.
P31749 with requested 10090 returns literal `No result found.`; retain a native
query result declaration, separate from failed access and biological absence.
Native publication `Other`, blank residues/sequence and indirect flags survive.

[Historical SIGNOR 3.0 score documentation](https://signor.uniroma2.it/documentation/SIGNOR_3_score_Documentation_final.docx)
describes a normalized regression using pathway/STRING inputs for some entity
classes and fixed scores for others. Do not interpret raw scores as binding
probabilities or assign that historical model/version to this current export.
Website SIGNOR 4.0 does not pin native relation/export/sequence/score revisions.
No independent total/current database completeness is returned. Exact query
matches require protein/UNIPROT namespaces; names and complex memberships do not
establish protein identity or linked sequence coordinates. No article, sequence,
network/pathway expansion, calculation job or card enrichment is acquired.

[Official SIGNOR documentation](https://signor.uniroma2.it/documentation/), read
2026-10-06, grants CC BY 4.0. Dataset credit and original source-served publication/
sentence context remain separate from underlying article/input rights. Three
unchanged native fixtures preserve original bytes and are declared in NOTICE;
original exact retrieval timestamps are unrecorded. Bound native TSV/gzip snapshot
access inserts no header and optionally verifies SHA-256 before decompression.
The generic supplied TSV contract still requires a header and is unchanged.
