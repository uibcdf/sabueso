# Follow-up 23: LIGYSIS directed residue correspondence dictionaries

Recovered on **2026-10-08** in the existing editable Python 3.14.7 environment.
This continues the preserved binding-residue/structural-context requirements and
the native LIGYSIS recovery in [follow-up 22](followup_22_ligysis_residue_panel.md).
The original stash, 87 exports and published card remain protected; the index is
empty and all recovery code remains local/uncommitted/unpushed.

## Original input and useful scope

The unchanged public HsTIM segment page
`temp_data/ligysis/result__P60174__1.html` contains native `Pdb2UpDict` and
`Up2PdbDict` declarations for structure key `7t0q` and chain keys `A`/`B`.
Each direction contains **245 A entries + 246 B entries = 491**. Both directions
are native declarations from the same response, not independent confirmation or
982 distinct scientific correspondences. Original **96597 bytes**, SHA-256
`3ccb0df740fe353b1f2a12f1362459e0296e6cfacda1736ca8a4e23479d6aacc`, acquisition
date **2026-10-06** and unknown exact retrieval time remain unchanged. No new
scientific response or current live service-health claim is made.

The current [provider implementation](https://github.com/bartongroup/LIGYSIS-web/blob/master/app.py)
was read as documentation on 2026-10-08 (file blob
`7c30cc0906bc64720ff165e80c49f0dffefd1ed0`). It passes the two representative-
structure dictionaries into the result template and handles `chain2acc`
separately for its structure-mapping response. This qualifies the distinction
between residue dictionaries and chain-to-accession identity. It does not pin
the old result's software/data revision or establish that each mapped chain
belongs to the page's queried protein. No provider code or pickle is executed,
and no mapping endpoint or coordinate/chain/accession artifact is requested.

## Delivered behavior

`sabueso.mappings.ligysis.map_residue_correspondences(envelope)` validates the
existing six-literal result-page identity/count/membership contract and the two
additional directed dictionaries under `ligysis_residue_correspondence_literals@1`.
Every parent and key/value entry is checked before output. Four independent
`annotations.ligysis_residue_correspondences` assertions represent the received
structure/chain tables, retaining each native direction, parent case, complete
dictionary, key order, pair count and original page/hash/receipt support.

Supported keys are literal signed integer-shaped strings and values are integers,
excluding bool/float/string coercion. Negative/zero/leading-zero keys remain raw;
they are not interpreted as canonical positions. Changed insertion-code-shaped
keys, malformed parents, missing/duplicate/executable literals and non-finite JSON
fail explicitly. An empty received dictionary is distinct from a missing declaration.
Opposite parent sets need not match; non-bijective or contradictory directions
remain separate original declarations, without reconstruction, selection or repair.

Each assertion explicitly leaves chain-to-protein identity, chain namespace,
structure numbering scheme, insertion codes and sequence/structure/mapping
revisions unknown. The page query is provenance context, not an identity merge.
Neither direction establishes current UniProt placement. Coverage is all received
directed dictionaries for one structure, not all eight structures counted by the
page. Both directions share the same source support; there is no new scientific
calculation or independent corroboration claim.

The existing site and displayed-residue readers keep their separate literal
requirements. No new source/client/enricher, card shape/schema field, current
sequence, coordinates, job, ligand identity or cross-component API is added.
Existing `NOT-STATED` data terms and unknown sharing remain unchanged; provider
MIT code rights are not assigned to scientific data.

## Remaining useful work

An authorized original chain-to-accession declaration, explicit numbering and
insertion context, compatible structure/sequence revisions and complete original
scientific input are still required for projection. Other structure/segment/ligand
and site-table scopes remain unqueried. Consumer projection requirements remain
owner-reviewed work; these raw source declarations do not establish acceptance
in MolSysMT or another component.

Expanded queue stays **6 scoped / 7 pending / 0 unreviewed**; original 27-list
stays **21 scoped / 6 pending / 0 unreviewed**. Pending providers remain **ASD,
GtoPdb, COSMIC, ELM, BioCyc, OMIM and CASTp**. Historical catalog stays **65 in use /
7 evaluating / 11 deferred / 3 retired / 1 out of scope**. No gated route, account,
agreement, upload or scientific job is attempted; the stash is not deleted.

## Qualification

Focused correspondence, displayed-residue and existing AlphaFill/LIGYSIS checks:
**168 passed in 4.11 seconds**, pytest-receptor with **12 workers**, including
**42 new cases**. These guard all original directed tables, unknown identity,
detached support, label case/sign/order, zero/empty input, conflicting/non-bijective
directions, unmatched opposite parents, late malformed values, exact query scope,
unsupported literal formats and unchanged site-only parsing.

Full offline checkpoint: **5314 passed in 161.01 seconds**, pytest-receptor with
**12 workers**, 10 expected failed/cut enrichment-fixture warnings. Ruff lint and
format (**923 files**), registry/generated metadata, strict Sphinx HTML
(`/tmp/sabueso-followup23-docs-build`), frozen-card shape/schema and diff gates pass.
An initial documentation code-example format finding was corrected; format and
strict documentation gates then pass. The failed format invocation is not passing
qualification evidence.

Outside-checkout native reading in the verified editable environment yields all
four tables and 491 entries per direction with zero scientific network requests,
unknown chain-to-protein identity and no canonical location. Receipt:
`/tmp/sabueso-followup23-native-receipt.json`; ignored local preview:
`recovered_work/current_preview/P60174.ligysis_residue_correspondences.json`.
The provider-code reference is retained as documentation at
`/tmp/sabueso-followup23-provider-reference.json`, separately from original data.
`/tmp/sabueso-followup23-integrity.json` verifies 87 original lengths/hashes,
91 accounted paths, original stash, empty index, frozen-card equality to HEAD,
unchanged native LIGYSIS bytes and catalog counts. Gate receipt:
`/tmp/sabueso-followup23-gates.json`.

The owner-local [issue #129 follow-up](https://github.com/uibcdf/sabueso/issues/129#issuecomment-6054361771)
records this qualified slice and remaining identity/projection limits under MOLI's
issue-feedback requirement. The issue stays open pending a repository code
checkpoint. No separate environment, stage, commit, push, remote CI, release or
stash deletion occurs.
