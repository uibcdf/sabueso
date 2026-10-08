# Eighth five-source integration follow-up

Reviewed **MetalPDB, MEROPS, HPO, PDBTM and ELM** on 2026-10-07 in the existing
editable Python 3.14 development environment, on updated main `68dac8f`. MetalPDB's
native site reader and provider-qualified donor distance quantities are recovered.
The other four retain concrete native representation/scope/access/terms conditions.
This remains local uncommitted/unpublished development. The original stash and all
87 original exported files remain intact.

## MetalPDB: native site parents and independently qualified distance units

The preserved `protein_structural_context.py::map_metalpdb` accepted generic site
rows, attached a caller protein and supplied a universal experimental class. Its
useful metal-site/context requirements are recovered through native source support.
The [official API help](https://metalpdb.cerm.unifi.it/api_help) distinguishes
site/PDB/UniProt queries and documents a full-column default. The new
`sabueso.tools.db.metalpdb.get_site(identifier, client=None)` performs one explicit
site-ID HTTPS JSON GET, preserving the complete received array.

The original [12ca_2 JSON](https://metalpdb.cerm.unifi.it/api?query=site:12ca_2)
remains **849 unchanged bytes**, SHA-256
`4fbde4d64312472953cd7fc7eafe2da327a7fa1b67881bf56a9eddc45f8e68c4`.
A fresh response matches the earlier public 2026-10-06 probe. This native record
supplies site/PDB/UniProt and organism/molecule/classification strings, representative
false, one Zn and three His ligand/donor occurrences, with PDB atom/residue numbers,
original chain, coordination/pattern/geometry and full-precision distances.
Actual `metals`/`pdb` and string classifications differ from help examples; those
example names/types are not used to fabricate a response.

### Distance unit qualification

The earlier help/body review did not establish the distance unit. This follow-up
uses the provider's public site-detail view. A read-only site-ID form lookup reaches
the existing result; its canonical [12ca_2 page](https://metalpdb.cerm.unifi.it/pdbSearchResult?id=12ca_2)
is directly retrievable by GET. No analysis job is submitted. Its **Coordination
Sphere** donor table explicitly labels **Distance (Å)**. Donor residue/chain,
atom name and element match the API for HIS_94(A)/NE2/N, HIS_96(A)/NE2/N and
HIS_119(A)/ND1/N. Display distances 2.497, 2.112 and 2.112 match API values
2.4972444, 2.1122792 and 2.111593 after rounding to three decimals. This qualifies
the native donor-distance field's angstrom unit rather than guessing from PDB
coordinates, typical bond lengths or a publication licence.

The full unchanged public page is **1007163 bytes**, SHA-256
`9149d5e72a6b774f605a72fa951c33ac6d777d90b7b9a2fceb5460f36c2e1879`,
and stays outside package data. A **10906-byte** explicitly extracted donor table
is retained as `temp_data/metalpdb/donor_distance_table__12ca_2.html`, SHA-256
`e389920434736f4ae6e813d94c71d12d4dd90692529890a0c641435d9b4fc283`.
It is a declared extraction/modification without semantic editing. The original
API JSON remains unmodified. No full sequence/alignment collection, coordinates,
viewer assets, interaction request, CSV job or links are fetched by the reader.
The unit table also displays solvent-accessibility/secondary-structure context;
those fields are not transferred into API site assertions.

### Qualified behavior and scientific scope

Online, fixture and exact source/kind/canonical-site-query-bound JSON/gzip clients
preserve raw/decoded hashes, original time, supplied-file receipts and archive
observation. Native site validation requires the native array and checks
all received rows and nested metal/ligand/donor parents before mapping. Unsafe,
PDB-only, UniProt and compound/search queries fail before transport. Only the PDB
prefix is lowercased; source chain/residue/atom literals stay exact. Missing/error
bodies and failed access do not become an empty site query or biological absence.
Explicit empty arrays remain distinct from unavailable or failed acquisitions.

`sabueso.mappings.metalpdb.map_sites` emits one `sites.metal_sites` SourceAssertion
for every native site occurrence on `metalpdb:site:<ID>`. Repeated site/metal/donor
occurrences and conflicting geometry remain independent. Complete native support,
original occurrence, full response hash and the source distance-unit qualification
stay in metadata. Typed values retain source site/PDB, organism/molecule, UniProt
pointer, EC/Pfam/CATH/SCOP strings, false representative status, geometry/pattern/
coordination and original metal/ligand/donor labels/numbers.

Each donor distance becomes a PyUnitWizard canonical `{value, unit}` node in
**angstrom**, without rounding away API precision or changing the host's session
policy. A zero distance stays zero. Negative/nonfinite/bool/string distances fail;
new unit-labelled donor shapes require separate qualification. Unknown extra
fields remain raw support rather than unitless typed physical quantities. No
coordination count is recomputed from the received ligand list; vacancies and
source categories are not supplied by Sabueso.

Metal chain/model/assembly/insertion and source sequence/scientific revisions are
unstated. Ligand chain is not copied onto the metal or used to infer a canonical
protein. PDB atom/residue literals stay source coordinates without offset/projection;
zero/negative residue numbers and chain case survive. UniProt remains a source
pointer. The page's physiological relevance and catalytic/reliability/literature
labels are not imported into the API scope, and no essentiality, protein function,
experimental method or MOLI Evidence is inferred. Geometry/pattern are provider
annotations, not new calculations or motif matching. No automatic card intake,
negotiated card quantity path or frozen-schema change is added.

### Live receipt and rights

A live call from `/tmp`, using this checkout's existing editable Python, at
**2026-10-07T08:20:55+00:00** receives the same site in **one GET**. Raw bytes and
decoded record match the fixture; decoded response identity is
`sha256:ff7f83cfa22d07bab238507636f4e7fdc8a60943cb56271e1c68c3a25b1a90ad`.
All three donor distances carry angstrom units. Archive replay preserves original
record/time/hash and every assertion with **zero network attempts**. Receipt:
`/tmp/sabueso-followup8-live-receipt.json`; ignored preview:
`recovered_work/current_preview/12ca_2.metalpdb_site.json`.

The [provider API/help](https://metalpdb.cerm.unifi.it/api_help) and
[about statement](https://metalpdb.cerm.unifi.it/about) supply no separate current
site-data redistribution grant. Terms remain **NOT-STATED**. Credit MetalPDB and
CERM/University of Florence; retain native site/PDB/metal/ligand/donor support and
API URL. Resource bibliography is the official dataset URL, separate from native
site support. Original factual JSON and the declared small unit-table excerpt
remain local unreleased recovery. Publication/software and original input-resource
rights are separate; no blanket grant or publication permission is inferred.

## Four candidates still requiring qualification

| Candidate | Current reviewed material | Remaining condition |
| --- | --- | --- |
| MEROPS | Current official availability statement still calls the complete database the Library under GNU Library GPL and links a generic LGPL page without a version. The earlier complete native accession export stays auditable. | Qualify applicable version/fixture obligations and exact malformed/unbound representation: 116744 headerless rows, 116741 three-column and three displaced four-column rows with incomplete split accession literals. Preserve all occurrences, native prefixes and blank/whitespace taxonomy; do not join, shift, discard or guess. This is not native cleavage context or a full-length sequence library. |
| HPO | Current repository LICENSE still links the JAX licence URL, which returns 404. Native format documentation preserves source gene/disease scope, frequency kinds and independent OMIM/HPO versus Orphanet contributions. | Qualify an exact released native asset and applicable contributor/annotation grant. No ontology-wide CC0, older-page substitution, ancestor expansion, gene penetrance, disease-study support fabrication or protein projection. |
| PDBTM | A fresh official documents GET is readable (16953 bytes); visible descriptions match the earlier probe, while raw page bytes differ. The original 1c3w XML retains its nonprofit/no-modification/commercial-agreement notice. | Qualify raw/derived representation rights and native physical units/axes before admitting transforms or distributing data. Sequence versus author bounds, generated chains, biological assembly transforms and membrane transform are independent; no constant offsets, canonical projection, transform execution, coordinates or membrane prediction. |
| ELM | The exact linked public academic agreement PDF again times out after 20 seconds; no bytes, agreement acceptance or database export. | Reach the applicable agreement and original native class/instance export. Qualify investigated sequence/revision, native instance bounds/status/reference support. Class regexes, described instances and pattern-match predictions remain independent; no motif search, inferred canonical placement or article-licence substitution. |

Primary references: [MEROPS availability](https://www.ebi.ac.uk/merops/about/availability.shtml),
[HPO repository LICENSE](https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE.md),
[current HPO licence route](https://hpo.jax.org/app/license),
[HPO gene-phenotype format](https://obophenotype.github.io/human-phenotype-ontology/annotations/genes_to_phenotype/),
[PDBTM documents](https://pdbtm.unitmp.org/documents),
[native PDBTM XML](https://pdbtm.unitmp.org/api/v1/entry/1c3w.xml), and
[ELM academic agreement](https://elm.eu.org/media/Elm_academic_license.pdf).
Fresh PDBTM documents SHA-256 is
`0f3e0249bcdce7d6e8b8630877c181337d891e7a9199fdace2f07fdefaf04ffc`.
The raw response is retained outside fixtures; readable documentation does not
supply a new data/derived-representation grant.

Failed access and unspecified fields are not scientific absence or retirement.
No credentials, account, provider contact, uploads or new computation occurs.

## Qualification and remaining material

Focused MetalPDB/snapshot/registry/acquisition/fixture-licensing selectors:
**121 passed in 4.14 seconds**, including **53** new source cases, through
pytest-receptor with **12 workers**. The full checkpoint passes **4445 tests in
102.82 seconds**, with **10** existing exercised failure/cut warnings. Ruff
check/format (**870 files**), registry/generated page/terms/catalog, frozen card
shape, FIELD_PATHS/schema and strict Sphinx pass. HTML receipt:
`/tmp/sabueso-followup8-docs-build`. Initial Ruff found three ambiguous test locals;
those were renamed before the final code checkpoint. Final integrity receipts
are recorded in [validation.md](validation.md).

Historical catalog: **53 in use, 19 evaluating, 11 deferred, 3 retired,
1 out of scope, 0 not registered**. Fourteen of the original 27 reviewed candidates
have scoped recovered readers; **13** await integration: GtoPdb, MEROPS, COSMIC,
HPO, ELM, BioCyc, OMIM, Interactome3D, PDBTM, 3did, CASTp, ProBiS and FDA Orphan.
Six other earlier evaluating declarations remain separate from that original group.
Scoped readers do not imply full source capabilities, release qualification,
blanket fixture/data redistribution or automatic card enrichment.

Original stash `db04d97fef5a318c6d09f8312971558eafd9d14c` and all 87 original
exported bytes/hashes remain intact. No stash drop, stage, commit, push, separate
environment/worktree or published-schema edit. Actual GitHub Actions runs use
gh-run-receptor when needed; no workflow run is required for this local checkpoint.
