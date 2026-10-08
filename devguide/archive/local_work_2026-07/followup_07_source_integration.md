# Seventh five-source integration follow-up

Reviewed **MetalPDB, ECOD, Interactome3D, 3did and GtoPdb** on 2026-10-07 in
this checkout's existing editable Python 3.14 development environment, on updated
main `68dac8f`. ECOD's native experimental-domain reader is recovered. The other
four keep concrete native units/access/scope/terms requirements. This work remains
local uncommitted/unpublished development; the original stash and all 87 original
exported files remain intact.

## ECOD: one explicit native experimental-domain UID

The preserved `protein_structural_context.py::map_ecod` used generic domain rows,
attached the caller protein and supplied a universal database-inference class.
The useful structural-domain classification scope is recovered through actual
native records and source support. The current [official documentation](http://prodata.swmed.edu/ecod/documentation)
and [API reference](http://prodata.swmed.edu/ecod/documentation/api) identify the
public JSON endpoint `/api/v1/domains/:uid`, without authentication and with a
100-request/minute/IP limit. Exact domain-ID search `e1iepA1` identifies UID 80374;
the [public domain page](http://prodata.swmed.edu/ecod/domain/80374) and
[native API record](http://prodata.swmed.edu/ecod/api/v1/domains/80374) independently
show that existing domain. Search is discovery for this qualification, not a
reader feature or submitted sequence/structure computation.

`sabueso.tools.db.ecod.get_domain(identifier, client=None)` reads one explicit
ASCII numeric UID string through the qualified HTTP route. Numeric zero padding
is normalized; domain/PDB/chain literals remain source-exact. The reader has
online, fixture and exact source/kind/integer-query-bound JSON/gzip clients. All
qualified native identity, hierarchy, flags and file pointers validate before a
record is returned. It preserves unknown fields, raw-file SHA, original time,
supplied-file receipts and acquisition/archive observations. Caller snapshot
metadata is a declaration, not source identity or permission proof.

`sabueso.mappings.ecod.map_domain` emits one independent
`annotations.structural_domains.ecod` SourceAssertion about `ecod:uid:80374`,
keeping the original response and decoded hash as support. It retains native
`e1iepA1`, `source_id=1iep_A`, `chain_id=A`, `uniprot_acc=P00520`, range
`A:228-498`, five-level id/name classification and false manual/representative
flags. The family is `206.1.1.20`, `PK_Tyr_Ser-Thr`. A native F=0 remains an
unassigned family. The source's `experimental structure` label is origin context,
not an independently asserted experimental method, protein function or MOLI
Evidence. The UniProt field is a native pointer, without protein identity merging.

Documentation examples show classification strings, while the received native
JSON supplies id/name objects; the observed object contract is qualified and
example strings fail explicitly. The original range stays **opaque**. Neither
this JSON nor these API examples state its author/sequential axis or investigated
sequence revision. Discontinuities, insertions and other-chain literals are not
normalized, offset or projected onto canonical positions. Sequence/model/assembly,
domain and classification revisions are unstated. API v1 and the separately
received distribution catalog v295.2 do not become source record versions.

This scoped reader qualifies experimental single-chain domain-ID records only.
AlphaFold/DPAM origins, broad UniProt/PDB/Pfam queries, full release exports and
other domains remain separately unqualified. Full exports, coordinate/FASTA
pointers, viewer assets, BLAST/Foldseek and jobs are not acquired or executed.
There is no automatic card enrichment or frozen-schema change. Empty/error
bodies, foreign UID/source/chain, malformed hierarchy, unsupported origins,
booleans/floats as UIDs and nonfinite JSON fail explicitly. Failed/404 access is
not biological absence. `truncated=False` describes one complete received record,
not the source's full database or all domains for a protein.

### Original native bytes and live receipt

- `temp_data/ecod/domain__80374.json`: **617 unchanged bytes**, SHA-256
  `8768342d13ff78fe8f1f3a1328c0108f96a733eb85e1ac979a699cec912f2c5e`.
  The original public probe was acquired on 2026-10-07; its exact time was not
  recorded and fixture time remains `None`.
- Live acquisition from `/tmp`, using the existing editable checkout, at
  **2026-10-07T07:59:00+00:00** receives the same UID/domain in **one GET**.
  Raw bytes and decoded record match the fixture; decoded response identity is
  `sha256:958f40e9a65ad1103d51b27c489817301bc1e9eb042cb0ceec41c510c66b8bc6`.
  Archive replay preserves the record, original time/hash and assertion with
  **zero network attempts**. Local receipt: `/tmp/sabueso-followup7-live-receipt.json`;
  ignored preview: `recovered_work/current_preview/80374.ecod_domain.json`.
- The official public-access statement does not establish a separate domain-data
  redistribution grant. Source terms remain **NOT-STATED**. Credit ECOD and
  Grishin Laboratory and retain native UID/domain, structure/chain, hierarchy
  and API URL. The resource bibliography is the official dataset URL, separate
  from domain support. The small factual response remains local unreleased
  recovery; publication/software and PDB/Pfam/UniProt rights are not assigned as
  a blanket data licence.

## Other four candidates

| Candidate | Current follow-up finding | Remaining integration condition |
| --- | --- | --- |
| MetalPDB | A fresh documented `site:12ca_2` GET receives the same 849-byte native JSON as the earlier probe: explicit site/PDB, Zn, donor atom/residue/chain literals and three numeric distances. Documentation says distance from metal without declaring a unit. Native `metals`/`pdb` fields and string classification values differ from examples. | Qualify distance units, precise site provenance/numbering and data/input rights before integrating the original geometry scope. Do not assign angstrom, caller protein identity, native sequence revision, automatic experimental/function class or representative meaning. No coordinate spheres, MetalPredator or other job is acquired. |
| Interactome3D | The documented native protein-structure request for exact P60174 again fails TLS with no XML response; primary help still separates protein from pair-interaction endpoints and original structures from comparative/domain models. | Receive a lawful native XML record and qualify its structure/model/template/rank/biounit/coverage axes and separate data/input rights. Protein versus interaction scope and native XML version remain independent; coverage bounds do not establish exact residue correspondence. No coordinate/model/docking acquisition. |
| 3did | A fresh official download-page request again returns HTTP 525 with a 16-byte body, without a native export. | Qualify original DDI/DMI flat-file record/release and its grant. PDB contacts and Pfam HMM profile interface positions use distinct axes. Preserve structural-instance/template/topology/score/profile context; no synthetic rows, motif search, coordinate acquisition or case repair. |
| GtoPdb | Current public REST documentation still requires registered-user API keys and retains database ODbL versus content CC BY-SA 4.0. Public documentation is inspected; no protected service is requested. | Obtain authorized native target/subunit/measurement records or a lawful supplied snapshot. Keep target identity, species, endpoint failures, zero affinity, native logarithmic versus physical quantities and exact rights obligations. No credentials are sought, account created or provider contacted. |

Primary references: [MetalPDB API help](https://metalpdb.cerm.unifi.it/api_help),
[native MetalPDB site query](https://metalpdb.cerm.unifi.it/api?query=site:12ca_2),
[Interactome3D help](https://interactome3d.irbbarcelona.org/help.php),
[3did official download](https://3did.irbbarcelona.org/download.php), and
[GtoPdb REST documentation](https://www.guidetopharmacology.org/webServices.jsp).
Fresh public MetalPDB bytes match the earlier probe: SHA-256
`4fbde4d64312472953cd7fc7eafe2da327a7fa1b67881bf56a9eddc45f8e68c4`.
The 3did HTTP-525 body remains outside package data: SHA-256
`f28010ee4bebf3921c03ddd425fdde6c937c24298bd0888b701a71ad53030a0e`.
No Interactome3D XML bytes were received.

Access errors and unstated fields do not establish scientific absence or source
retirement. No certificate bypass, substitute provider, credential, upload,
external message or new computation is used.

## Qualification and remaining material

Focused ECOD/snapshot/registry/acquisition selectors: **114 passed in 3.71 seconds**,
including **50** new ECOD cases, through pytest-receptor with **12 workers**.
The full offline code checkpoint passes **4392 tests in 96.58 seconds**, with
**10** existing exercised failure/cut warnings. Ruff check/format (**866 files**),
registry/generated terms/catalog/page, frozen card shape, FIELD_PATHS/schema and
strict Sphinx pass. HTML receipt: `/tmp/sabueso-followup7-docs-build`. Final diff,
original-byte, stash/index and frozen-card receipts are in [validation.md](validation.md).

Historical catalog: **52 in use, 20 evaluating, 11 deferred, 3 retired,
1 out of scope, 0 not registered**. Thirteen of the original 27 reviewed candidates
have scoped recovered readers; **14** await integration: GtoPdb, MEROPS, COSMIC,
HPO, ELM, BioCyc, OMIM, Interactome3D, PDBTM, MetalPDB, 3did, CASTp, ProBiS and
FDA Orphan. Six other earlier evaluating declarations remain separate from that
original group. Scoped readers do not imply full source capabilities, release
qualification, blanket redistribution rights or automatic card enrichment.

Original stash `db04d97fef5a318c6d09f8312971558eafd9d14c` and all 87 exported files
remain intact. No stash drop, stage, commit, push or separate environment/worktree.
GitHub Actions is not needed for this uncommitted local checkpoint; actual
workflow qualification uses gh-run-receptor when required.
