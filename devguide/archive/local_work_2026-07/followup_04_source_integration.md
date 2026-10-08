# Fourth five-source integration follow-up

Reviewed **GtoPdb, COSMIC, BioCyc, OMIM and GWAS Catalog** on 2026-10-07.
Native GWAS Catalog standard mapped-gene association pages are recovered in the
existing editable development environment. The other four retain concrete
authorized-access and native scope/terms requirements; no reader or fixture is
claimed for them. See [validation.md](validation.md) for the local checkpoint.
The original stash and all 87 original exported files remain unchanged.

| Source | Delivered behavior or current qualification | Remaining scope |
| --- | --- | --- |
| GWAS Catalog | Exact standard mapped-gene HAL page, checked counts/links, every association occurrence and original statistics | Optional complete paging, pinned release/assembly, broader queries and original-owner terms |
| GtoPdb | Current API-key requirement and download/login redirect checked; independent target/subunit/measurement requirements retained | Lawfully obtained native data or authorized service access, dual database/content terms |
| COSMIC | Current registration, academic/publication versus public sharing, and module-specific exceptions checked | Authorized native variant module/release and exact assembly/transcript/sample/redistribution scope |
| BioCyc | Native database/frame relations and exact Open versus Limited Database agreements retained; public service documentation connection reset | Authorized session/export, database release and applicable distribution obligations |
| OMIM | Native MIM entry/gene/locus/phenotype/allelic-variant distinctions retained | Current authorized-data agreement and lawfully obtained exact native release/representation |

Historical counts are now **49 in use, 23 evaluating, 11 deferred, 3 retired,
1 out of scope and 0 not registered**. Ten of the original 27 reviewed candidates
have scoped recovered readers; **17** await integration. These counts describe
the 87 historical declarations, not the whole maintained registry. A recovered
page reader does not claim all historical broad query or biological projections.

## GWAS Catalog: exact page scope and original statistical representations

The retained `protein_translational_sources.py::map_gwas_catalog` used a generic
row wrapper and a universal curated class. The source idea remains useful, while
the new mapper preserves native association identity, study, traits, variant/allele
context and occurrence support. Source curation is separate from MOLI Evidence;
native mapped/nearest gene annotations do not identify a causal gene or protein.

The [current REST guide](https://www.ebi.ac.uk/gwas/docs/programmatic-access/rest-api/)
describes v2 as the supported API and v1 as retired in August 2026. Standard gene
mapping (`extended_geneset=false`) uses variant-mapped or nearest upstream/downstream
genes; the extended set is a different query contract. The reader uses only the
standard set. It never transfers variant-trait results onto every protein encoded
by the symbol or onto a canonical residue axis. Bulk and summary-statistics access
are separate scopes; no participant-level data is requested.

`sabueso.tools.db.gwas_catalog.get_associations(identifier, limit=20, page=0,
client=None)` requires one literal symbol, size 1–500 and zero-based
nonnegative integer page. Mixed-case official symbols such as `C11orf74` retain
their case; the supported lexical scope starts with an uppercase letter and does
not resolve identity. The 500 cap is a local reader bound, not a documented
provider maximum. Backend checks also apply when digestion is skipped. Native
row symbols are matched exactly; surrounding source whitespace, case changes,
substrings and similar symbols do not supply query membership or identity.

The [official reference](https://www.ebi.ac.uk/gwas/rest/api/v2/docs/reference)
embeds Swagger, whose configuration points to
[`/reference/api-docs`](https://www.ebi.ac.uk/gwas/rest/api/v2/reference/api-docs).
That native specification names API **2.0**, explicit page/size and mapped-gene
parameters. Its broad DTO describes `content`/`links` arrays, whereas the actual
response uses HAL `_embedded`/`_links` objects. The reader validates the received
native representation without renaming, coercion or synthetic wrappers. API/date
labels do not establish dataset, association, assembly or sequence revisions.

All native finite JSON, page metadata, row identity/types and exact mapped-gene
membership are validated before mapping. Declared total pages and expected row
count must agree with size, index and total elements. The native self link binds
the exact query. Received first/last/next/prev links must remain on the official
HTTPS host and association route, with unchanged symbol/standard-set/size and
correct index. Missing next before the total, cycles, duplicate query keys,
changed filters, off-host links and contradictory coverage fail explicitly.
The links are retained; none is automatically followed. Manual pages do not
guarantee stable ordering or a pinned scientific revision across requests.

`map_associations` maps every received occurrence on
`gwas:association:<native association_id>`. Repeated IDs, conflicting effect text,
multiple/duplicate mapped genes, alleles and traits survive, with independent
occurrence indices, complete response/query hashes and native page/link support.
Missing, null, zero, empty and future declarations remain distinct. Mantissa,
exponent and supplied numeric p-value remain separate representations; no
recalculation, ranking, precision reconstruction or guessed physical unit occurs.
Original-byte identity stays separate from canonical decoded JSON identity.
Location strings do not acquire an assembly from a caller, metadata endpoint or
assumed current Ensembl version. Haplotype/interaction flags do not collapse to
single variants or manufacture experimental classes or clinical interpretation.

Two unchanged public batch-04 probes are now explicit local fixtures:

- **HBB**, page 0, size 2: **2485 bytes**, SHA-256
  `14f63516b1a620e3e41ddbd681acf507bc88f5685229103ece6c61a172b05786`;
  two occurrences, native total **279**, total pages **140**. Associations
  **226316756** and **226315081** refer to independent **GCST90476345** and
  **GCST90480668**, PMID **39024449**, original `rs11549407-G` context. Original
  `pvalue_mantissa=1`, `pvalue_exponent=-323`, numeric `1e-323`, risk-frequency
  string `0.9997` and `3.451 unit decrease` remain unchanged.
- **TPI1**, page 0, size 2: **198 bytes**, SHA-256
  `4dde3abd2cc12114cc229c93e6acb95e07d1467d2ebee03b3c18376ae1df92b7`;
  zero declared elements/pages and no `_embedded` object. This native empty shape
  is accepted only when it agrees with the expected received count; it is not a
  biological negative or proof of complete disease/phenotype coverage.

Neither fixture has a recorded exact first acquisition time; `None` remains
unknown rather than borrowing the later validation time. HTTP failure, malformed
body, unavailable fixture and received empty filter result stay distinct.
`SnapshotGwasCatalogClient` binds original JSON/gzip to exact source, kind, query,
unknown scientific revision and optional original-file SHA. Original time and
caller-declared terms remain explicit without new remote credit; archive replay
uses no new GET and retains original support. No frozen card change or automatic
card enrichment is introduced.

The [Catalog terms](https://www.ebi.ac.uk/gwas/docs/about/) explicitly place curated
data under [EMBL-EBI Services Terms of Use](https://www.ebi.ac.uk/about/terms-of-use/).
Those impose no additional use/redistribution restrictions beyond original owners
and require scientific attribution. Registry terms are `NO-OWN-RESTRICTIONS` with
those caveats, not a uniform open-data grant. The small original factual API pages
retain NHGRI-EBI and Verma et al. attribution, PMID 39024449 and DOI
**10.1126/science.adj1182**, in NOTICE. No article text or linked dataset is copied.
Summary-statistics CC0, visualisation CC BY and software Apache do not license
arbitrary curated associations or remove contributing-owner rights.

Live validation from `/tmp` at **2026-10-07T06:43:26+00:00** maps both HBB
occurrences, with explicit partial coverage and canonical response identity
`sha256:6c886da112fc8b1edebbc3cbcecec25c6d3432797f92ba821f3012fb019fc8dd`.
At **2026-10-07T06:43:30+00:00**, TPI1 returns the native zero-result shape,
canonical identity `sha256:aef0a5598dee91e774ff073aec0e3884791ef5d55172c1672f3b9063ca5fc089`.
Each uses one GET/attempt/response; raw SHA and decoded body match its fixture.
Import origin is this checkout's `sabueso/__init__.py`; ignored previews are
`recovered_work/current_preview/HBB.gwas_catalog.json` and
`recovered_work/current_preview/TPI1.gwas_catalog.json`.

## Four sources still awaiting qualified authorized input

GtoPdb's [REST documentation](https://www.guidetopharmacology.org/webServices.jsp)
still requires a personal key, recommends the `GTP-API-Key` header and describes
an approximate 60 requests/minute limit. Its [download page](https://www.guidetopharmacology.org/download.jsp)
redirects to login with a registration requirement, so it is not an unauthenticated
bulk alternative. The [about statement](https://www.guidetopharmacology.org/about.jsp)
retains distinct ODbL database and CC BY-SA 4.0 content rights. No key is searched,
account created or contact sent. Lawfully obtained native target/subunit/endpoint
data is still required; never select the first target candidate, hide endpoint
failures, lose a zero affinity or guess molar units for logarithmic parameters.
See [batch 01](batch_01_source_review.md).

COSMIC's [current terms](https://www.cosmickb.org/terms/) distinguish registered
core variant/census/actionability modules from no-registration COSMIC-3D and
Mutational Signatures. The latter do not authorize broad access to the historical
somatic variant scope. Academic publication enablement is narrowly scoped and
does not allow arbitrary public sharing; commercial use has its own grant and
download route. Retain exact module/release, assembly, transcript/protein revision,
variant, tumor/histology, sample/count definitions and original interpretation.
No account, licensed dataset, public fixture or synthetic variant projection is
introduced. See [batch 02](batch_02_source_review.md).

BioCyc's [service documentation](https://biocyc.org/web-services.shtml) cannot be
read afresh through the web reader; one bounded verified public curl request
fails with connection reset (curl 56), without native data. The previously received
public service/licence documents remain unchanged. Exact organism database,
native frame type/ID, detail level, original gene/protein/reaction/pathway relations
and database release remain prerequisites. The Open versus Limited Database
agreements and individual subscription conditions are separate from free website
access; no broad licence or native relation is inferred. No session/form, contact,
foreign-ID lookup, authenticated request or pathway computation occurs. See
[batch 03](batch_03_source_review.md).

OMIM's current agreement remains unqualified after the recorded public 403/robots
failures. No blocked data route is repeatedly requested and no restricted input,
third-party substitute, key or public fixture is introduced. Preserve native MIM
identity/entry type, exact gene/locus versus phenotype map versus allelic-variant
scope, original mapping key/inheritance/qualifiers and release/support. A source
gene or locus is not a protein/isoform; mapping keys are not clinical ranks and
narrative entries cannot be manufactured into pathogenicity assertions. Its
[maintained NCBI resource page](https://www.ncbi.nlm.nih.gov/omim) identifies the
provider; it is not an export-data grant. See [batch 03](batch_03_source_review.md).

The maintained registry/packaged metadata, historical catalog/inventory and
public/source/user/API documents describe the scoped reader and the four pending
contracts. Further integrations remain separate; the original stash is retained.
