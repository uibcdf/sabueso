# Fifth five-source integration follow-up

Reviewed 2026-10-07 on updated local main `68dac8f`. This follows up **ECOD,
ChannelsDB, CASTp, ProBiS and FDA Orphan** using existing public records and current
contracts. Original source demands remain useful; historical synthetic payloads,
caller protein assignments and generic prediction/curation labels are not imported.
No separate environment/worktree, account, upload, computation or provider message
is introduced. Work remains uncommitted and unpublished.

## Delivered: ChannelsDB PDB annotations

`sabueso.tools.db.channelsdb.get_annotations(identifier, client=None)` reads one
existing native PDB annotation DTO from the
[official endpoint](https://channelsdb2.biodata.ceitec.cz/api/annotations/pdb/1tqn).
Online, fixture and source-kind-query-bound JSON/gzip snapshot clients retain
original record/hash/time, acquisition observation and archive replay.
`sabueso.mappings.channelsdb.map_annotations` produces independent entry and residue
annotation SourceAssertions about the explicitly queried PDB context.

The public native OpenAPI separates annotations, channels, preferred assembly and
AlphaFill routes. Its annotation DTO requires `EntryAnnotations` and independent
`ResidueAnnotations.ChannelsDB` / `ResidueAnnotations.UniProt` arrays. The reader
validates every native occurrence before mapping; unknown fields remain unchanged,
while unknown residue groups fail rather than disappearing. No native row contains
the requested PDB ID: online query scope comes from the official URL, and supplied
file scope is a caller declaration, not source identity proof.

Entry UniProt/name/function/reaction literals and residue `Id`, `Chain`, `Reference`,
`ReferenceType` and `Text` stay native, including empty references, HTML entities,
repeated IDs and conflicting texts. Negative/insertion and multicharacter chain
literals are not interpreted. Occurrence IDs include full-response hash, PDB query,
group and index; identical rows remain independent. Native groups and references
do not assign a method, experimental class or MOLI Evidence. UniProt pointers do
not merge protein identity. Residue numbering, sequence, model and assembly axes
remain unqualified and unplaced. No channel/assembly join, canonical projection,
AlphaFill acquisition, geometry, coordinates, calculation or card enrichment occurs.

`truncated=False` describes the full received DTO, not current database completeness.
Explicit empty arrays differ from missing/malformed arrays or failed HTTP. Native
API version 1.0.0 does not supply annotation/input/sequence revisions. All scientific
revisions remain unknown. Native references are retained without fetching linked
records or articles. The verified
[resource description](https://academic.oup.com/nar/article/52/D1/D413/7416806),
doi:10.1093/nar/gkad1012, supplies resource bibliography separately from row support.

### Native fixture and access receipt

- Unchanged `temp_data/channelsdb/annotations__1tqn.json`: **13127 bytes**, SHA-256
  `9279b3cf4e1329addc20ffd861e18969f65698daf860d310ebb7d11d89d64c5c`.
  One entry about source pointer P08684, **43** native reaction strings, zero
  ChannelsDB-group residues and **22** UniProt-group residue comments give **23**
  independent mapped occurrences. Exact initial probe time was not recorded;
  fixture `retrieved_at=None` remains unknown.
- One live GET from `/tmp` using the existing editable Python 3.14.7 environment at
  **2026-10-07T07:06:01+00:00** matches original fixture bytes and decoded content.
  Canonical response hash is
  `sha256:80b017f83d1ad6c2d7d711e5e0c3881c53e08dff1e2013fc71330ec780267120`.
  Replay uses **zero network attempts** and keeps original content, timestamp,
  download hash and all assertions. Import origin is this checkout.
- Local receipts: `/tmp/sabueso-followup5-live-receipt.json` and ignored
  `recovered_work/current_preview/1tqn.channelsdb_annotations.json`.
- Separate annotation-data terms remain **NOT-STATED**. The
  [official documentation](https://channelsdb2.biodata.ceitec.cz/documentation.html)
  and reviewed primary article do not establish a blanket data redistribution
  grant. Frontend Apache, article CC BY and underlying UniProt/publication rights
  remain separate. Credit ChannelsDB contributors and native inputs/references.
  Original small response stays local unreleased recovery; NOTICE and packaged
  source terms do not invent redistribution permission. Geometry is not packaged.

## Other four candidates

| Candidate | Native follow-up | Remaining integration condition |
| --- | --- | --- |
| ECOD | Official HTTP search application is readable and separates domain lookup from BLAST/Foldseek computations. The previously qualified native distribution catalog declares v295.2 and fixed artifact pointers. | Qualify an exact experimental/predicted domain representation, release binding, original discontinuous partitions/hierarchy, author versus sequential numbering and data-specific rights. The 663436312-byte domain export is not downloaded; catalog availability is separate from scientific data qualification. |
| CASTp / CASTpFold | Official frontend `main.9ed1feb8.js` declares existing-result `data/pdb/<middle>/<id>/processed/<id>.basic.json` and separate predicted-model/temporary data routes. The 1hti basic route responds with the same 713-byte application shell, not JSON. | A native existing-result record is still required, with probe/area/volume units, origin, structure/model/assembly, residue axes and representative relations. Shell HTTP success is not data availability. Free access/citation does not establish a redistribution grant. No `submit_calc.php`, pocket search or other job is invoked. |
| ProBiS | The official documented `get_alignments?structure_id=1ytb.B&z_score=2.0` example returns HTTP 404, as did the earlier query. | Qualify an existing native alignment response, chain/representative context, threshold/scores/coverage and applicable data rights. A >95% representative relation does not establish identity. No align/scan, superimposition, minimization or ligand prediction is invoked. |
| FDA Orphan | The official browser-readable [search page](https://www.accessdata.fda.gov/scripts/opdlisting/oopd/index.cfm) exposes product/sponsor/designation/date filters, all-versus-approved selection and condensed/detailed/Excel output. A direct GET still returns HTTP 404 with the FDA excessive-requests apology. | Obtain a permitted native query/export response with exact AND/date/status/page scope and applicable rights. CF Grid Key is an FDA internal field, not molecule/protein identity. Names do not assign targets/modality/efficacy. No retry loop, restriction bypass, account or sponsor submission occurs. |

The original ECOD distribution receipt remains 56390 bytes, SHA-256
`01b414ea1059959a42d7bff647cdb133fd782a83e3f784044088d3e1daca7775`;
version/file/checksum pointers are not fabricated domain fixtures. New public probes
remain outside the checkout: CASTp shell **713** bytes, SHA-256
`0f032b4f03af8a168aef3dbaa94b1207ba906bbbf818d376dfb9291adb1aa42c`;
ProBiS 404 **278** bytes, SHA-256
`e08c8a049d6b436bc33b97238bf33b996ecf8d79aa0a7f9137a14da501f00c32`;
FDA apology **420** bytes, SHA-256
`f6a9351396ba714274801251421bb0f689bf9ed75ba5fd22993ad8ea89836629`;
ECOD search HTML **40788** bytes, SHA-256
`61a06c3dd90cf131284fe8ece8d2a887eb49155e9c0c00a714527e95f5530e27`.
None is mistaken for an empty scientific result or retirement.

## Qualification and remaining material

- Focused source/snapshot/acquisition selectors: **259 passed in 6.99 seconds**,
  pytest-receptor, **12 workers**. All **95** new ChannelsDB cases also pass in the
  full checkpoint: **4272 passed in 100.25 seconds**, **10** existing exercised
  failure/cut warnings. The first source-only pass caught a terms-test API call
  error (94 passed / 1 failed); it was corrected before qualification. Ruff's
  initial import-order finding was also corrected; final checks pass.
- Registry/generated page/terms/catalog, Ruff check/format (**858 files**), frozen
  card shape and FIELD_PATHS/schema checks pass. Strict Sphinx and final diff
  receipts are recorded in [validation.md](validation.md).
- All **87** original exported files retain their original bytes and hashes.
  Frozen schema-0.3.12 card bytes equal HEAD; the index is empty and original stash
  `db04d97fef5a318c6d09f8312971558eafd9d14c` remains intact.
- Historical catalog: **50 in use, 22 evaluating, 11 deferred, 3 retired,
  1 out of scope, 0 not registered**. Eleven of the original 27 reviewed candidates
  have scoped recovered readers; **16** await integration. ChannelsDB geometry
  remains independently pending even though its annotation reader is now in use.
  The stash is not exhausted and is not dropped. No GitHub Actions run is needed
  for this uncommitted local checkpoint; gh-run-receptor remains the route for
  actual workflow qualification when needed.
