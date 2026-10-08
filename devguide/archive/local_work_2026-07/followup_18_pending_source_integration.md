# Follow-up 18: eleven pending resources and scoped BRENDA EC context

Recovered on 2026-10-07 under the current source-access, assertion and terms
contracts. This supersedes follow-up 17's current BRENDA/ASD/TTD acquisition status;
its original receipts and the seven-candidate historical denominator remain valid.
All eleven pending resources are reconciled below. New native qualification is
limited to BRENDA, ASD's linked download script and TTD's actual provider redirect,
application script and public cross-reference export. Known failed/gated routes
for other resources are not repeatedly probed without a changed condition.

## Delivered BRENDA slice

The officially linked [SPARQL prototype](https://sparql.dsmz.de/brenda) declares
its backend and D3O EC schema. The fixed exact-EC query selects `ec label name
 description`, with separate OPTIONAL systematic-name and description bindings,
without LIMIT/OFFSET. Native EC 5.3.1.1 has a label/systematic name and an empty
literal description; 2.7.1.1 has a nonempty native description. The syntactic
no-match probe 7.99.99.99999 returns zero solutions. These three originals,
346/484/79 bytes, are unchanged public JSON fixtures declared inside NOTICE's
checked Contents table. SHA-256 hashes are recorded there. The no-match probe
is not represented as an assigned biological EC class or absent activity.

`get_enzyme_class`, online/fixture/bound JSON/gzip/hash/time clients and
`map_enzyme_class` preserve every received native solution, RDF URI/language/
datatype term, missing OPTIONAL, empty literal and repeated/conflicting occurrence.
All rows validate before mapping. Independent standalone
`annotations.enzyme_class_context` assertions use `brenda:ec:<native EC>` and
full native response/query/hash/binding-index support. An EC number is not a
protein/organism identity or a derived Sabueso classification rule. Prototype and
individual record revisions stay unknown; main-site release 2026.1 is not borrowed.

[Provider data/online-use terms](https://brenda-enzymes.org/license.php) state
CC BY 4.0; attribution retains BRENDA, DSMZ Digital Diversity and the
[provider-requested current publication](https://brenda-enzymes.org/references.php),
Hauenstein et al. (2026), doi:10.1093/nar/gkaf1113. SOAP registration and bulk-file
active acceptance are separate unused routes. No account or acceptance is performed.
Historical kinetics, substrates, inhibitors, activators and assay conditions are
still unqualified; the prior inhibitor HTTP 500 is not retried. This is one useful
descriptive reader, not recovery of those historical capabilities. No linked
acquisition, card enrichment, persisted card schema change or new environment.

## Concrete pending conditions

| Resource | Available evidence and remaining condition |
| --- | --- |
| iPTMnet | Previous original Swagger specifies `/v1/{id}/substrate`; P60174 acquisition returned HTTP 503. Need a successful original proteoform-grouped response, site/sequence support and applicable data terms. No repeat of the failed route or example-as-fixture substitution. |
| ASD | Original linked 18694-byte `module/download/js/download.js` lists release 5.1 site/PPI and 5.01 protein XML/potential-site artifacts. It displays file links in the licence-application/login state and states research-only use with third-party distribution prohibited. Need an authorized original input, permitted use scope and qualified structure/residue/experimental-versus-potential-site mapping. No application, link-gate bypass or restricted artifact download. |
| TTD | Actual legacy HTML explicitly redirects to `ttd.idrblab.cn`. Its linked download component advertises the public target cross-reference export, now received unchanged. Applicable data terms and a qualified native-key reader are still pending; public download and article/software licences do not establish redistribution rights. |
| GtoPdb | Public download page still directs to registration/login. Need authorized native target/ligand/interaction records, release, assay/quantity scope and applicable database/content terms. No registration or alternate-route bypass. |
| COSMIC | Existing provider terms require registration/institutional licensing and scope-specific rights. Need authorized original variant/sample/cohort records, assembly/protein bounds, coverage and permissible sharing. No protected acquisition. |
| ELM | No qualified original scientific export; current download-page browser acquisition yields no data. Need native class/validated-instance identity, sequence/bounds/publication and applicable data grant. No invented API or motif-to-site inference. |
| BioCyc | Existing native flat-file request requires agreement/manual processing. Need applicable Open/Limited Database rights and original organism/release/frame/quantity support. No form or agreement submitted. |
| OMIM | Existing NCBI description directs to provider entries/API. Need authorized original entries/API scope/release and applicable terms; gene/locus/phenotype/variant/narrative assertions stay separate. No repeated restricted route or NCBI rights substitution. |
| CASTp/CASTpFold | Existing official result builders/tutorial do not provide an acquired native result. Need original structure/model/assembly/sequence/parameters, SA/SE area-volume support and terms. No upload, new job, TLS workaround or repeat of failed result routes. |
| FDA Orphan | Existing database acquisition is blocked; official instructions distinguish AND filters and designation/approval dates. Need authorized unblocked native designation export and source/input terms, with product identity separate from protein targets. No retry of blocked database or openFDA rights substitution. |

ASD original script SHA-256:
`f21a720e2654e191273972fd0c0262aac14570ab069d6140a841221df8139d6d`.
[Official download page](https://mdl.shsmu.edu.cn/ASD/module/download/download.jsp?tabIndex=1)
and [its linked script](https://mdl.shsmu.edu.cn/ASD/module/download/js/download.js)
are the primary receipts; filenames across artifacts do not imply one common release.

## TTD export qualification, without a delivered reader

The 425-byte [legacy homepage](https://idrblab.org/ttd/) explicitly redirects to
[the current provider site](https://ttd.idrblab.cn/), whose 461-byte HTML links
`assets/index-B1MIElFm.js`. That script imports `assets/Download-Do-aLopB.js` for
`/full-data-download`; the component explicitly advertises
[`P2-01-TTD_uniprot_all.txt`](https://ttd.idrblab.cn/files/download/P2-01-TTD_uniprot_all.txt).
One public original GET receives **525950 bytes**, SHA-256
`74b2dbb4c03e14b01d02b54bdce45507da0da1e457859e1669cdf76b39feb22e`.
The header states **version 10.1.01 (2024.01.10)**, not the current website's 2026
publication date. After the abbreviation index, the artifact has **4298 target
blocks**, with native `TARGETID UNIPROID TARGNAME TARGTYPE` fields and **613**
`NOUNIPROTAC` declarations. UNIPROID includes UniProt entry names, not uniformly
accessions. A source literal for T59130 calls the target bacterial while its entry
name is TPIS_PLAFA; that native inconsistency is retained, not repaired by inference.
Target names/types do not merge protein, gene, complex, RNA or product identities,
or establish druggability as a Sabueso finding.

The original frontend footer reserves rights. No separate data grant is qualified;
article and frontend software rights remain separate. This original stays local
acquisition evidence under `/tmp/sabueso-followup18-ttd-uniprot-all.txt`, with route,
version and digest recorded here. No scientific fixture, online reader, mapping,
card enrichment, clinical/variant/activity claim or redistribution route is admitted.
No credentials, form submission, contact message or agreement acceptance occurs.

## Validation and preservation

Focused source/fixture/registry gates pass **86 tests in 7.60 seconds** through
pytest-receptor with **12 workers** in the existing editable Python 3.14.7 environment.
An initial selection used an incorrect test filename and an initial test called
the existing `source_terms` accessor with the wrong signature; both were corrected
before qualification. Neither failed command is passing evidence.

A real reader GET outside the checkout at **2026-10-07T22:00:46+00:00** matches
the original EC 5.3.1.1 bytes/hash and produces one independent EC assertion.
Archive replay makes zero network attempts and retains its exact original time,
query/hash and assertions. Receipt: `/tmp/sabueso-followup18-live-receipt.json`.
Editable metadata/import origin verify this checkout; the path is URI-decoded
before comparison. No separate development or test environment is provisioned.

Full offline checkpoint: **5070 passed in 109.55 seconds**, pytest-receptor with
**12 workers**, 10 expected failure/cut fixture warnings. Ruff lint/format,
source registry, strict Sphinx, card shape/schema, dependency preflight and diff
checks pass. Formatting of the new documentation example and an incorrect
`card_shape.py --check` invocation were corrected; the tool's default check passes.
No failed gate is represented as passing. Strict HTML output:
`/tmp/sabueso-followup18-docs-build`. Gate receipt:
`/tmp/sabueso-followup18-gates.json`. Integrity receipt:
`/tmp/sabueso-followup18-integrity.json` verifies all 87 original hashes/lengths,
91-path accounting, original stash SHA, empty index and unchanged published card.


Historical catalog: **62 in use / 10 evaluating / 11 deferred / 3 retired /
1 out of scope**. Expanded 13-resource queue: **3 resources with scoped readers /
10 pending / 0 unreviewed**. Original 27-candidate queue remains **20 scoped readers /
7 pending / 0 unreviewed**; BRENDA is from the broader six. Scoped-reader counts
never imply every historical capability or full database coverage is recovered.

The original stash `db04d97fef5a318c6d09f8312971558eafd9d14c`, all 87 exported
originals and the frozen published card remain unchanged. No staging, commit,
push, CI request, release or stash deletion is performed. GH Run Receptor is used
when actual Actions evidence needs inspection; no remote checkpoint is created here.
