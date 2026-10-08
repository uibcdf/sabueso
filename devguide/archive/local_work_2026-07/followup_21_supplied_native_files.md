# Follow-up 21: supplied native files and remaining useful material

Reviewed on **2026-10-08** in the existing editable Python 3.14.7 environment.
This continues utility recovery beyond the seven access-gated providers. The
original stash and its 87 exported files remain preserved. All recovered changes
remain local and uncommitted; the Git index is empty.

## Delivered adaptation

The preserved `sabueso/tools/source_options.py` supplied-file workflow is now
adapted further through `tools.source_snapshot.load_source_snapshot`. In addition
to its structured formats, it accepts literal UTF-8 `html` and `txt`, inferred
from a suffix or explicitly selected, optionally gzip-compressed. These formats
are a current adaptation for the recovered native readers, not a claim that the
historical utility parsed HTML.

- The record is an uninterpreted string retaining BOM, CRLF, spaces, blank lines,
  native labels and script text. There is no rendering, execution, link following,
  HTML repair or XML/encoding inference.
- SHA-256 covers original file bytes before decompression or decoding. Caller
  digest mismatch fails before attempting to decode malformed bytes.
- Invalid UTF-8, truncated gzip and invalid DEFLATE are explicit connector
  failures. The DEFLATE guard also corrects the structured-format loader, which
  previously could leak `zlib.error` instead of its connector diagnostic.
- `records_key` still wraps row lists only. An empty literal file remains an empty
  string; it is not a claim of no scientific records. Native clients decide whether
  the content is valid.
- Declared source/query/version/terms and original retrieval time remain separate
  from the local read receipt. File reading adds no observed remote access,
  permission, acquisition credit, card admission or scientific identity.

FDA OOPD and iPTMnet snapshot clients now reuse this loader instead of duplicate
hash/gzip/decode/receipt implementations. Each retains its native-format receipt,
source/kind/query binding, native table validation and unknown-revision constraint.
Their public readers continue to qualify received completeness. A generic literal
envelope alone still fails the mapping completeness gate. Missing files retain
the source client's unavailable-fixture diagnostic. No fixture, mapping rule,
card schema, automatic enricher or source adoption changes.

## Five areas reconciled

| Area | Current useful result | Remaining boundary |
| --- | --- | --- |
| Supplied-file workflow | Shared literal loader used by FDA/iPTMnet; original hash and time declarations retained | Generic mutually exclusive client/payload/snapshot card intake still lacks a reviewed admission contract; it is not restored. |
| Direct GO annotations | Legacy qualifier/reference/with-from/extension scenarios remain useful requirements | Maintained GO comes through UniProt. The removed direct connector and the prototype classifying a GO term as a protein are not restored. A distinct native annotation contract would be needed. |
| Small-molecule context | Current ChEBI/UniChem/PubChem/RCSB readers already supersede basic legacy identity/property work | ClinicalTrials substring name matching does not identify a molecule. SureChEMBL remains deferred under its reviewed claims-filter/bulk-data trigger; no patent or intervention assertion is imported. |
| Consumer projections | The existing reviewed requirements identify current owners, mapping status, numbering, loss reporting and offline receiving checks | No implemented legacy exchange API exists to restore. MOLI/consumer owner review remains required; no cross-component API is invented in this slice. |
| Cavity membership | Recovered residue composition already supports one explicitly identified sequence set | Original structural membership and exact chain/residue/sequence correspondence are still required. Caller-selected positions do not establish cavity membership; geometry and remote jobs remain separate. |

Also reconciled stale archive-summary references: iPTMnet's native HTML report is
recovered independently of REST failures, and BRENDA's scoped EC-description
reader does not qualify kinetics or protein assignment. These are already
delivered readers, not two new source adoptions in this checkpoint.

The provider queue stays **ASD, GtoPdb, COSMIC, ELM, BioCyc, OMIM and CASTp**:
**6 scoped / 7 pending / 0 unreviewed** in the expanded 13-resource queue, and
**21 scoped / 6 pending / 0 unreviewed** in the original 27-candidate queue.
Historical catalog remains **65 in use / 7 evaluating / 11 deferred / 3 retired /
1 out of scope**. FDA live-transport HTTP 404 and other earlier access failures
are unchanged; no new network attempt is made. These counts do not count the
broader requirement areas as qualified resources. Stash deletion is not warranted
by this review and is not performed.

## Qualification

Targeted native-reader, literal-file and argument-contract checks: **178 passed in
4.48 seconds**, pytest-receptor with **12 workers**. Eighteen new guards cover
literal fidelity, hash ordering, damaged gzip/DEFLATE, invalid encoding, empty
content, native FDA/iPTMnet mapping equivalence and generic-envelope rejection.
An initial native comparison retained an additional supplied-file receipt on one
side; that test expectation was corrected and the gate rerun successfully.

Full offline checkpoint: **5228 passed in 103.82 seconds**, pytest-receptor with
**12 workers**, 10 expected failed/cut enrichment-fixture warnings. Ruff lint and
format (**919 files**), registry/generated metadata checks, strict Sphinx HTML
(`/tmp/sabueso-followup21-docs-build`) and `git diff --check` pass. An initial Ruff
import-order finding was corrected and both Ruff gates rerun successfully.

Outside-checkout import and editable metadata verification confirms this checkout
in Python 3.14.7. `/tmp/sabueso-followup21-integrity.json` verifies all **87**
original lengths/hashes, **91** accounted paths, original stash SHA, empty index,
unchanged published frozen-card bytes and unchanged catalog counts. Original FDA
fixtures remain byte-identical to their preserved public acquisitions. Gate receipt:
`/tmp/sabueso-followup21-gates.json`.

No separate environment, stage, commit, push, remote CI, release or stash deletion.
No card-shape/schema mutation or new native acquisition requires qualification;
this checkpoint qualifies local file behavior and the unchanged native reader
boundaries, independently of current provider service availability.
