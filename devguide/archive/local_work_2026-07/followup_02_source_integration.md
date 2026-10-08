# Second five-source integration follow-up

Reviewed OmniPath, MEROPS, TCDB, PDBTM and ELM in the existing development
environment on 2026-10-06 (Mexico City). Native OmniPath access and mapping are
recovered. The other four retain useful requirements and explicit qualification
conditions; they are not delivered connectors. See [validation.md](validation.md)
for the final local checks. The original stash and exported bytes remain intact.

| Source | Delivered or qualified in this follow-up | Remaining scope |
| --- | --- | --- |
| OmniPath | Human native interaction reader, original aggregate support and independent effect/consensus mapper; bound JSON/gzip/hash/time and replay | Resource-specific reuse rights for arbitrary rows, expanded evidence reconstruction, translated organisms and card intake |
| MEROPS | Actual 116744-row accession export, original namespace/family/taxonomy columns, duplicate scope and three displaced rows qualified | Precise Library GPL version/fixture obligations; explicit malformed-row handling; native cleavage/unit sequence contracts |
| TCDB | Native mixed-accession and multiple-TC assignments retained as source-occurrence requirements | Export-specific rights and namespace qualification before native fixture integration |
| PDBTM | Original XML agreement and independent chain/transform axes retained | Raw/derived redistribution scope, physical units and numbering before projection |
| ELM | Distinct class, described instance and search prediction scopes retained | Reachable exact academic agreement and original instance export/sequence axes |

Historical source counts are now **46 in use, 26 evaluating, 11 deferred,
3 retired, 1 out of scope and 0 not registered**. Seven of the original 27 reviewed
candidates have scoped recovered readers; **20** await integration. These counts
describe the 87 historical sources, not the entire maintained registry. Previous
batch review receipts remain historical; current status and this follow-up record
the delivered behavior.

## OmniPath: native aggregate rows and opposing effects recovered

The historical `protein_specialist.py::map_omnipath` imposed a curated class,
preferred gene labels, attached the caller protein and chose stimulation before
inhibition. The replacement retains every original occurrence on its native
ordered-participant-pair subject. Both effect flags and all three consensus flags
remain independent; repeated and contradictory declarations have independent
assertion identifiers. Query and full-response hashes preserve distinct query
support, even when two partners return the same row. No direct binding,
experimental method, identity equivalence or unified effect is inferred.

`sabueso.tools.db.omnipath.get_interactions(identifier, client=None)` sends one
exact base UniProt partner request to the native interactions endpoint. Scope is
fixed to human `9606`, dataset `omnipath`, source/reference fields, JSON and an
explicit `license=academic`. No limit or implicit translated species is used.
Every received row is validated before `sabueso.mappings.omnipath.map_interactions`
maps it. Original strings, additional context and resource-prefixed references
survive. A native empty array is query-scoped emptiness; blocked access,
non-native payloads and HTTP-200 application errors fail explicitly.

The [server contract](https://omnipathdb.org/queries/interactions) does not accept
`strict_evidences`. A probe with that client-side option returned an HTTP-200
nested error array: **280 bytes**, SHA-256
`947d74937f63106f609c74fef145bb19c5389602e6138b2bed6a88e2fcb977bb`.
After removing it, a P31749/SIGNOR/commercial probe returned **237** rows,
**509497 bytes**, SHA-256
`58c6e179b12bb18a9fe7ea5e894f118957d1009f080f9facac667f8d79234e7e`.
Its aggregate annotations list **52** resource labels, including inputs outside
the selected resource. All 237 rows also pass the new native validator; **21**
declare both stimulation and inhibition. The P31749-to-P46527 row, for example,
declares both effects, with consensus stimulation false and consensus inhibition
true. These opposing native observations are not resolved by precedence. The
[official R client documentation](https://r.omnipathdb.org/reference/import_omnipath_interactions.html)
explains that strict support is reconstructed client-side from expanded evidence;
server resource/dataset/licence filters alone do not do that reconstruction.
Both bodies stay temporary probes with unknown first retrieval times. The large
SIGNOR-filtered body is not shipped under SIGNOR's licence or pruned and relabelled
as an unchanged native fixture.

The earlier unchanged public TPI1 response is now the qualified fixture:
**288 bytes**, SHA-256
`6f5a542228162871e4645e3f7897eba1bc660fb4c9ffc7bf75d9f852030d4e6a`.
It contains one directed inhibitory P29466-to-P60174 occurrence with SPIKE and
SPIKE_LC support and original reference 17959595. Current [native resource metadata](https://omnipathdb.org/resources?format=json)
names CC BY 4.0 for both resources; the [provider description](https://omnipathdb.org/info)
also names CC BY 4.0 for SPIKE. Attribution and independent input/publication
rights remain in NOTICE. This single-row grant is not extended to arbitrary
OmniPath results: registry terms remain source-wide `NOT-STATED` with explicit
resource-specific caveats. An academic/commercial access filter is not a grant.

Online clients retain original-byte SHA and acquisition time. Fixture and supplied
JSON/gzip clients retain unknown or declared original time, optional byte hash and
exact source/kind/query/revision binding. Replay preserves original time and body.
Unknown response revisions and independent totals remain unknown; all received
rows are retained without a database-completeness claim. Live validation from
`/tmp`, using this checkout's shared editable Python, at
**2026-10-07T05:55:04+00:00** receives/maps one row in one GET/attempt/response.
Raw hash and decoded payload match the fixture. Canonical response identity is
separately `sha256:195fbf147589a720a1e9cd9daac0635a0bed585206929d94047c243d5292ab90`.
The original fixture time remains unknown; this new live time does not overwrite it.

## MEROPS: actual export differs from its format description

The [official download list](https://www.ebi.ac.uk/merops/download_list.shtml)
links `dnld_list.txt` and describes family/species information after an exclamation
mark. One public GET of the linked [accession export](https://ftp.ebi.ac.uk/pub/databases/merops/current_release/dnld_list.txt)
instead returns **2914699 bytes**, SHA-256
`9758b658cd7d5f043311d5babf439590baf88b97623ad2a5d42e7e6827abc711`,
with **116744 headerless rows** and CRLF line endings. **116741** rows have three
tab-separated columns: namespaced accession, family and taxonomy literal. Prefixes
are native `Trembl` (108699), `swissprot` (7960) and `PIR` (85); no namespace is
silently rewritten into current UniProt identity. For example, the original
`swissprot:P29466`, `C14A`, `9606` row is a classification declaration, not a
cleavage or substrate observation. TPI1 is not listed in this received artifact.

There are **207 accession literals with multiple occurrences** and no identical
complete rows. **Three rows** have four columns and incomplete displaced accession
literals, at one-based lines **67322**, **67435** and **83822**:
`swissprot:` / `Q80ZF` / `P2A` / `10090`,
`swissprot:` / `Q6UWY` / `S1A` / `9606`, and
`swissprot:` / `Q32Q9` / `S9` / `10090`.
Joining columns would invent a repair and still leave an incomplete accession.
Original rows must remain auditable with explicit representation issues before
mapping; neither silent dropping nor assigning shifted columns is acceptable.
Among ordinary three-column rows, **147** taxonomy literals have a leading space
and **eight** are blank. Preserve originals and distinguish unspecified taxonomy
from an explicit taxonomy value or query failure.

The [database-specific availability statement](https://www.ebi.ac.uk/merops/about/availability.shtml)
explicitly makes the whole database content the Library under GNU Library GPL.
The precise version and corresponding fixture/distribution obligations remain
unqualified; the linked generic LGPL route does not resolve that by itself.
The export stays a temporary native probe with unknown exact acquisition time.
The advertised SQL release 12.4 and website 12.5 do not establish this export's
revision. Unit-only `pepunit.lib` and full-length `protease.lib` have separate
sequence scopes. No SQL database, sequence search, BLAST or cleavage job was run.
The historical synthetic cleavage mapper remains an unsupported prototype.

## TCDB, PDBTM and ELM: preserve the actual qualification boundaries

TCDB's earlier **24956-row**, **486702-byte** native assignment export and SHA
`c59e2b2c5293e0f33e75bcc0bf89e0eb6988be54fb7f2121935749bda3feef8a`
remain unchanged. **129** accession literals have multiple occurrences and two
complete pairs repeat. Mixed RefSeq/versioned/other identifiers cannot all become
UniProt. Native assignment identity includes the original row occurrence and exact
identifier, not only the TC number. Website-text CC BY-SA/GFDL does not establish
the assignment export's scope. Classification alone cannot transfer a family
substrate, mechanism or transporter role to a protein. No fresh access or sequence
search was required; see [batch 03](batch_03_source_review.md).

PDBTM's earlier **6866-byte** `1c3w` XML and SHA
`37ae24e30f12457eb91fb9198c5a7a6643e46e33efa0c039048784ff5b7ac55e`
retain the embedded unchanged-content/nonprofit-use agreement; commercial use
requires a separate agreement. Generated chains, 15 regions per chain, source
sequence endpoints, PDB author endpoints and membrane/assembly matrices are
separate declarations. No constant offset or chain equivalence is assumed.
Native history/software/database dates do not pin sequence or PDB revisions.
Distribution of raw/derived representations and physical units remain pending;
no transform, projection, coordinate retrieval or membrane prediction was run.

ELM's official class example remains distinct from described sequence instances
and predicted regex matches. A follow-up read of the official download page still
timed out; no bypass, account or job was used. The exact noncommercial academic
agreement, actual native instance export, investigated sequence/revision and
per-instance bounds/status/publication support remain necessary for fixture
intake. A paper's CC BY grant does not license the database. No synthetic instance
or canonical protein placement is restored; see [batch 02](batch_02_source_review.md).

The source registry, historical inventory/catalog, public development API and
user/API documentation now reflect the scoped OmniPath reader and MEROPS native
findings. No frozen schema, published release, separate environment or automatic
card enricher is changed. The stash is retained until remaining useful material
and the recovered implementation have a durable checkpoint.
