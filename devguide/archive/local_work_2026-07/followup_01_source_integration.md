# Integration follow-up 01: five reviewed source candidates (2026-10-06)

After completing the 27-candidate triage, follow up **WikiPathways, HPO, GWAS
Catalog, ECOD and ChannelsDB** together. Recover one native WikiPathways reader
and mapper; refine concrete intake contracts for the other four. This is an
integration follow-up to existing reviews, not five newly discovered candidates.

| Candidate | Delivered outcome | Concrete progress | Still required |
| --- | --- | --- | --- |
| WikiPathways | Scoped native reader recovered | Full-export validation, exact namespaced matches and native field/group/alias positions | GPML nodes/roles, complete pathway content and biological identity resolution are separate scopes |
| HPO | Evaluating | Separate disease summaries, cohort frequency and NOT declarations; exact release route | Applicable annotation/input terms and original source support |
| GWAS Catalog | Evaluating | Exact standard-gene-set HAL page/query binding, bounded continuation and statistical representation requirements | Qualified complete/cut paging, original-owner rights and variant/study/assembly context |
| ECOD | Evaluating | Accessible current version/file catalog and original numbering/origin definitions | Native domain/export intake and data-specific grant |
| ChannelsDB | Evaluating | Independently fetched preferred assembly and separate annotations/geometry components | Native data grant, structure/model/revision axes and geometry units |

Historical catalog counts are **45 in use, 27 evaluating, 11 deferred, 3 retired,
1 out of scope and 0 unregistered**. All 27 candidates remain reviewed; six scoped
readers have now been delivered from that list and **21** candidates await integration.
Earlier evaluating/deferred sources remain separate. Preserve the original stash
and all 87 original exports, without restoring the historical automatic profile.

## WikiPathways: exact literal tokens replace substring/name joins

The historical `tools/protein_sources.py::fetch_wikipathways` selected rows by
lowercase substring and stripped Ensembl version digits. The retained
`mappings/protein_context.py::map_wikipathways` attached the caller's protein and
generic curated labels. Its synthetic test used revision `42`, without native
URL/authors or full export support. Those projections are not restored.

The unchanged [native public bulk JSON](https://www.wikipathways.org/json/findPathwaysByXref.json)
contains **2218** pathway rows with fourteen native string fields, **12084935 bytes**,
SHA-256 `09da862b2d2dc08c98c0a0d98640892c076668d5ad251ee373502dcf89bbce22`.
It was already acquired during batch 01 and is now a qualified fixture. The exact
first download timestamp remains unknown (`None`). No independent database total,
dataset/GPML/entity/sequence revision or species filter is declared.

The [provider's generation template](https://raw.githubusercontent.com/wikipathways/wikipathways.github.io/main/json/findPathwaysByXref.json)
maps native DataNode-derived fields, uniques/compacts groups and joins them with
commas. Its `revision` is `last-edited`, not a numerical GPML version; descriptions
are shortened to 200 characters before delivery. The original shortened strings
are retained. The export cannot qualify every independent GPML-node occurrence,
role, reaction, mechanism or experimentally supported participation.

Native cells include semicolon aliases, empty aliases, free text and prefixes
different from the field name. For example **WP1584** has `hgnc.symbol:PRKCD` in
`uniprot` and `uniprot:Q05655` in `wikidata`. The new reader never repairs columns
or assumes a namespace from their names. It searches explicit literal tokens in
the seven original xref fields and records the exact native field, comma-group,
semicolon-alias and original token, including whitespace. Alias groups do not
establish equivalence, identity merges or curated roles.

`get_pathways_by_xref(identifier, client=None)` requires one exact supported
namespaced identifier: uniprot, ensembl, ncbigene, wikidata, chebi or inchikey.
Case, isoform and Ensembl version digits remain literal. Bare accessions, symbols,
names, multiple queries and unsupported namespaces fail before access. An ID in
a pathway name/description is not a match; accession prefixes, similar names and
another species never establish biological identity.

Every row is validated before selection: finite JSON, full native object shape,
required strings, exact WP ID/official URL and calendar-valid date label. Native
heterogeneous xref strings and future finite fields remain raw. Empty xref cells
are not errors. Matching repeated/conflicting pathways remain independent original
row occurrences; there is no uniqueness, strongest-revision or species selection.

`map_pathway_cross_references` preserves each complete matching row on
`wikipathways:<WP ID>`, with original occurrence index, full-response hash and all
matching token positions. **uniprot:P60174** returns WP143, WP1946, WP2456, WP4018,
WP4628, WP5178, WP534, WP5355 and WP5570. Query matches remain source-served
cross-reference context, not protein-pathway mechanism or participation assertions.
Native species/authors/date labels survive without inferred taxon/protein identity.

One online shared GET preserves the full original export, actual retrieval time
and original-byte SHA. Fixture and exact source/kind/query/scope-bound JSON/gzip
snapshots retain declared time/terms, optional original-file SHA and local receipts.
Archive replay preserves original response/time/hash without new access. Not-listed,
received empty, unavailable and failed access remain distinct. No GPML, pathway
page, SPARQL query, publication, sequence or linked resource is acquired; no automatic
card intake or frozen schema change is added. Live and code receipts are in
[validation.md](validation.md).

The [official content terms](https://www.wikipathways.org/terms.html) were checked
by a successful direct public GET: WikiPathways adopts CC0 for its content, asks
for scientific source/author attribution and clear content terms. The raw fixture
is unchanged. Linked publications/external resources retain separate rights.

## HPO: summary versus annotation support and zero versus NOT

The [current annotation introduction](https://obophenotype.github.io/human-phenotype-ontology/annotations/introduction/)
distinguishes `phenotype.hpoa` from the three derived summary files. A genes-to-
phenotype row does not itself supply all original study/support and modifier fields.
The [frequency contract](https://obophenotype.github.io/human-phenotype-ontology/annotations/frequency/)
separates original cohort fractions, frequency terms and percentages. A cohort
frequency `0/3` is not a universal NOT declaration; contributor NOT, zero frequency,
missing-value literals and absent rows remain distinct. No cross-study pooling,
gene penetrance, ancestor inference or protein identity projection is recovered.

The [official release list](https://github.com/obophenotype/human-phenotype-ontology/releases)
names `v2026-09-01`; a future reader should require an explicit asset/release rather
than mutable `latest`. The [current LICENSE pointer](https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/LICENSE.md)
still points to the previously failed JAX route. Annotation/contributor grants are
unresolved; no historical licence replacement, new data download or fixture is added.

## GWAS: a native page does not establish complete mapped-gene coverage

Inspect the unchanged batch-04 HBB probe: query `mapped_gene=HBB`,
`extended_geneset=false`, page 0, size 2, **totalElements 279**, **totalPages 140**.
The received HAL first/self/next/last links preserve that exact scope. Future
continuation must check the official HTTPS host and v2 associations route, unchanged
gene-set/filter/size, exact increasing page number and no cycles or off-host links.
Every page's received count/native total must agree with the declared cut/completion
outcome. Preserve duplicate/conflicting occurrences and each component receipt.
The two returned rows remain partial, and no continuation is fetched here.

Original association/study/rs/allele/trait and mapped-gene sets remain independent.
Mantissa/exponent **1, -323** and native floating `p_value` coexist; no underflow
rounding, causal-gene inference, guessed assembly or conversion of `3.451 unit
decrease` to a physical quantity is allowed. The [Catalog FAQ](https://www.ebi.ac.uk/gwas/docs/faq/)
and [EBI terms](https://www.ebi.ac.uk/about/terms-of-use/) retain original-owner rights;
summary-statistics CC0 and Apache software do not license every curated observation.
No new fixture, full-paging connector or clinical/statistical interpretation is added.

## ECOD: the application shell links a working distribution API

The public HTTP distribution page's own JavaScript links
[`/ecod/api/distributions`](http://prodata.swmed.edu/ecod/api/distributions), which
returns HTTP 200 with **56390 bytes**, SHA-256
`01b414ea1059959a42d7bff647cdb133fd782a83e3f784044088d3e1daca7775`.
The catalog declares **v295.2**, date **2026-08-27**, versioned native file URLs,
file sizes/modification dates/MD5 and `carriedFrom.hhsuite = v295`. File dates,
release labels and each carried-from archive remain separate. The main domain file
is declared **663436312 bytes** and was not downloaded. A catalog response does
not qualify that file's bytes, rows, checksum or reuse terms.

The native frontend format documentation separates case-sensitive PDB/chain,
author-numbered `pdb_range`, sequential `seqid_range` and predicted-structure origins.
Discontinuous ranges are independent segments. `manual_rep` is curated versus
automatic classification, not a universal experimental class. AlphaFold, EPP and
UniParc model-domain references cannot merge with PDB partitions by similar names
or equal residue numbers. Empty assembly/domain fields are not filled from a caller.

The catalog points to an archive DOI; its landing did not load through the web
reader. No current export-specific licence was qualified from the catalog or
frontend. The reader remains pending original domain/export/rights qualification.
The original HTTP JSON/script remain `/tmp` probes, not redistributable fixtures.
No representative sequences, coordinates, HMM archive or search/job is downloaded.

## ChannelsDB: preferred assembly is a separate declaration

The native OpenAPI documents
[`/api/assembly/1tqn`](https://channelsdb2.biodata.ceitec.cz/api/assembly/1tqn)
as a preferred-assembly lookup. One public GET returned HTTP 200, literal JSON
string **`"1"`**, **3 bytes**, SHA-256
`391552c099c101b131feaf24c5795a6a15bc8ec82015424e0d2b4274a369a0bf`.
This is an independent preferred-assembly component, not proof that every geometry
row was computed on that assembly or that it is the only biological assembly.
Keep its original time/identity separate from channel and annotation components.

Data reuse rights remain unresolved: frontend Apache and article CC BY are separate.
Native model/structure revision, residue numbering and geometry units must still
be qualified before normalized projection. No probe is made a fixture and no
MOLE/CAVER job or coordinates are acquired. Exact first probe times were not
captured; they remain unknown rather than borrowed from the later live WikiPathways
receipt or file modification times.
