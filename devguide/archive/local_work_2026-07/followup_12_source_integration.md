# Twelfth five-source integration follow-up

Reviewed **3did, GtoPdb, ELM, CASTpFold and ProBiS** on 2026-10-07 in the
existing editable Python 3.14 development environment. 3did now supplies native
DMI structural occurrences after public download access recovers. The other four
retain specific access/artifact/terms conditions. No stash application/deletion,
stage, commit, push, separate environment/worktree or frozen-schema edit.

## 3did: changed access condition and unchanged native artifact

The public [download page](https://3did.irbbarcelona.org/download.php) now responds
through browser and a bounded verified curl request, unlike the earlier recorded
failures. Its direct DMI gzip link returns HTTP 200 with actual compressed data.
The browser's unsupported gzip-content message is a representation limitation,
not a failed provider acquisition; the direct native request verifies the bytes.
No TLS bypass, authenticated request or alternate provider is used.
The original page is 33070 bytes at `/tmp/sabueso-followup12-3did-download.html`.

The complete unchanged
[DMI export](https://3did.irbbarcelona.org/download/current/3did_dmi_flat.gz)
is **149724 bytes**, SHA-256
`ef3d339e7643efb3ae2ed1857ecbbc3c350d3cf08ff9ef79daea4c667907bdfb`.
Decoded original text is **826632 bytes**, SHA-256
`85fd69fb419b994eb4c506c466e469a22af3bc16af7b042da64f2c58637c93aa`.
The file contains **22449** lines: **1657** domain/motif pair headers, **1657**
pattern lines, **17478** structural occurrences and **1657** pair terminators.
Native labels are `(Pfam)` and `(PLoS_CB_2010)`; patterns carry a source date
literal such as `(Feb 2025)`. Those labels/dates and the mutable current route
are not qualified individual PDB, Pfam, sequence or scientific export revisions.
The first probe's exact acquisition time is unknown and stays `None` in fixtures.

The download documentation distinguishes DMI structural PDB numbering from DDI
residue contacts and separate HMM-profile interfaces/global interfaces. These
other exports are not acquired. The provider's
[about statement](https://3did.irbbarcelona.org/about.php) identifies IRB Barcelona
without a separate export-data grant. Source terms remain **NOT-STATED**, with
provider and native input attribution. Original factual gzip stays local unreleased
qualification material, declared with exact bytes/hash/date/source in NOTICE.
Article/software permissions and original Pfam/PLoS input rights remain separate;
no public fixture or derivative-collection redistribution grant is claimed.

## Recovered reader and scientific scope

The preserved `protein_structural_context.py::map_3did` accepted synthetic
`interactions`/`results`, inserted caller protein identity, used row-index fallback
IDs and assigned a universal curated/evidence class under a domain-domain field.
No native fetch_3did implementation was present in the preserved source client.
Its useful structural-instance/support requirement is recovered in an explicit
DMI scope without restoring those projections or pretending DMI is DDI.

`sabueso.tools.db.threedid.get_motif_interactions(identifier, client=None)`
accepts one exact lowercase four-character native PDB literal. Online access
receives the full existing DMI gzip in one GET through shared transport. Complete
ID/PT/3D/end grammar, parent order and all structural rows validate before
selection, including unrelated late rows. Missing patterns/parents/terminators,
malformed bodies and wrong source/kind/query/version/cuts fail explicitly.
Identifier guards also apply when digestion is skipped. An unlisted PDB differs
from failed/unavailable access, biological absence or complete current coverage.

Online, fixture and source/kind/query-bound text/gzip/hash/time clients preserve
original text, compressed versus decoded identities and acquisition support.
Supplied-file metadata remains a caller declaration, not independent identity,
revision or licence proof. Archive replay retains original record/time/hash without
new requests. No similarity, motif matching, alignment, coordinates, source
publications or provider computation is performed.

`sabueso.mappings.threedid.map_motif_interactions` keeps each native occurrence
in `annotations.domain_motif_interactions` on `3did:structure:<native PDB ID>`.
Independent assertion identity binds full-export hash and native line; repeated/
conflicting blocks and rows survive. Original ID/pattern/row and pair/instance
coverage support remain linked to every value. Values retain domain/motif names,
parenthesized source labels, opaque combined pattern/date, PDB chain/range/sequence,
contextual-contact count and topology literals. No experimental class, atom contact,
function, binding strength/probability or MOLI Evidence is inferred. No automatic
card intake or frozen schema 0.3.12 change.

### Native 7m5l qualification

PDB **7m5l** has **six** independent occurrences: three PCNA_C and three PCNA_N
motif instances. The first native row declares domain `B:127-254`, motif `E:2-11`,
sequence `QCSMTCFY`, contextual-contact count **`0`** and topology **`0`**.
The PDB range spans ten numbering labels while the sequence has eight letters;
source residue numbering cannot be treated as a contiguous sequence slice or
repaired by truncating the sequence/changing endpoints. The next row changes
motif bounds to `E:3-11` and contact count to `2`; it is retained independently.
The same native structure/motif/chain appearing in other blocks does not supply
protein identity or a canonical residue correspondence.

Native flat rows also contain repeated lowercase chain tokens such as `ee`.
Documentation describes SQL lowercase-chain encoding, but does not independently
qualify decoding every flat-file token. All tokens/case/endpoints stay literal;
no `ee` to `e` normalization occurs. Regression cases retain negative/inserted
PDB endpoint literals without projection, duplicate/conflicting instances, zero
counts and an opaque pattern that would be invalid if executed as a regex. Parent
source names/pattern dates are not replaced by modern database identities or releases.

## Live receipt and validation

At **2026-10-07T19:50:43+00:00**, one live GET outside the checkout receives the
complete native gzip, matches compressed fixture and decoded original hashes,
validates all 1657 pairs/17478 instances and maps all six 7m5l occurrences.
Editable metadata and import path identify this checkout. Replay preserves original
record/time/hash/assertions with **zero network attempts**.
Receipt: `/tmp/sabueso-followup12-live-receipt.json`; archive:
`/tmp/sabueso-followup12-live.sqlite`; ignored preview:
`recovered_work/current_preview/7m5l.3did_motif_interactions.json`.
Focused 3did/registry selectors pass **89 tests in 3.49 seconds**, including **72**
new 3did cases, through pytest-receptor with **12 workers**. The full offline suite
passes **4668 tests in 156.83 seconds**, with ten existing failure/cut enrichment
warnings and no failed tests. Ruff lint/format (883 files), source registry and
packaged metadata checks, recorded card shape, schema alignment and strict Sphinx
HTML build also pass. Original-file/stash/index/frozen-card integrity is verified
in `/tmp/sabueso-followup12-integrity.json`; `git diff --check` passes. Exact
commands and receipts are recorded in [validation.md](validation.md).

## Four resources with pending native access/terms

| Resource | Review and remaining condition |
| --- | --- |
| GtoPdb | Indexed download descriptions still expose filenames/old public-wrapper expectations, but the actual download page redirects to registration/login. Current provider text requires login and commercial access fees; REST documentation requires keys. No direct DATA-route bypass, account or credential use. Database ODbL and content CC BY-SA remain independent; qualify authorized native target/subunit/ligand/measurement data with original units. |
| ELM | Indexed primary motif documentation retains noncommercial ELM Software License Agreement conditions. Current homepage and motif detail time out. The previously linked exact agreement remains unqualified and is not repeatedly requested. Require the original agreement and authorized native class/instance artifact, sequence/revision, status/bounds/publication scope. No motif search, acceptance or canonical projection. |
| CASTpFold | Current tutorial remains readable and preserves representative-cluster versus exact identity, independent DeepFRI/similarity predictions and angstrom-squared/cubed area/volume. Documentation is not acquired pocket data or original calculation parameters. Previous official example result requests returned a shared HTML shell and are not retried without a changed data condition. Require native result, exact structure/model/assembly/sequence/parameters and applicable data terms. |
| ProBiS | Current public homepage redirects to HTTPS and times out. Previously documented alignment/representative 404 routes are not retried. Require an available native existing-data artifact and current data grant; retain both chains, representative basis, nonredundant-set revision, score and coverage. No alternate-provider substitution, ligand/binding inference, alignment/scan/minimization or other analysis job. |

Primary references: [GtoPdb actual download route](https://www.guidetopharmacology.org/download.jsp),
[GtoPdb current API access](https://www.guidetopharmacology.org/webServices.jsp),
[ELM primary motif page](https://elm.eu.org/elms/elmPages/DOC_MAPK_NFAT4_5.html),
[ELM homepage](https://elm.eu.org/),
[CASTpFold tutorial](https://cfold.bme.uic.edu/castpfold/infos/allabout/tutorial.html), and
[ProBiS homepage](http://probis.cmm.ki.si/).
Prior follow-ups 09/10 preserve exact native-result failure receipts. Access failure
is not biological absence or retirement. 3did's restored access qualifies only its
newly received DMI artifact, not the other blocked providers or broader DDI scopes.
No stakeholder message, provider notification, account or restricted-route bypass.

## Remaining material and preservation

The historical catalog now has **56 in use, 16 evaluating, 11 deferred, 3 retired,
1 out of scope and 0 not registered** among **87** original declarations.
These counts do not describe the entire maintained registry. **17** of the original
**27** reviewed candidates have scoped recovered readers; **10** await integration:
GtoPdb, COSMIC, ELM, BioCyc, OMIM, Interactome3D, PDBTM, CASTp, ProBiS and FDA
Orphan. Broader capabilities of recovered sources retain their own scope/access/
terms requirements. Original stash and all 87 exported files remain unchanged;
index empty and frozen card/schema intact. Further data attempts require a changed
condition or independently qualified supplied artifact.
