---
summary: Preserve and independently check a genuine public AlphaFold archive fragment without pretending it is an API response.
issue: uibcdf/sabueso#148
status: native_reference_context_local_receiving
opened: 2026-11-05
area: [predicted-structures, source-contracts, structural-exploration]
---

# A genuine public archive fragment

## Native original-reference context — 2026-11-05

New native enrichments additionally retain
`has_predicted_structure.qualifiers.native_reference_context`, under the separate
`alphafold_modelcif_reference_context@1` derivation. Its input IDs refer to the
original native model assertion and the original focal UniProt sequence, length
and checksum assertions. Exactly one coherent entry/sequence revision is required;
different sources, foreign entries, missing inputs and alternatives cannot be
replaced by the current selected Card values or a developer fixture.

The public AF-Q8WZ42-F2 control now has a reproducible `comparable_interval`
finding: its 1,400-residue entity sequence equals original Q8WZ42 residues
201–1600, and its stated full-reference CRC64 agrees with both the original
UniProt checksum and an independent calculation. The original UniProt MD5 is
also checked against that original sequence. Calculated checksums remain derived
values, never new SourceAssertions or a provider-stated native model MD5.
Reference and entity intervals stay separate; the whole-model API match and
coverage views retain their original unknown native scope.

Interpretation requires unambiguous standard amino acids, agreement of native
canonical/raw sequence strings, and explicit complete entity positions and
monomers. Position order comes from `_entity_poly_seq.num`, not loop ordinal.
Modified/heterogeneous/unknown monomers, duplicate/missing positions, partial
entity alignments and incompatible declarations remain unsupported. Source
reference sequence/bounds must agree where additionally stated. Valid checksum
or sequence mismatches remain mismatches, with cause/age unestablished. Missing
reference CRC64 can coexist with an exact interval comparison but cannot qualify
the complete source-reference finding. Unrelated confidence does not select or
veto a sequence finding. Isoform membership is never inferred from equality.

The canonical source assertions retain entry version 223 and sequence version 4,
but not the original UniProt sequence-update date. Consequently the native
2012-04-18 date is retained, while `reference_date_equal` is **unknown**. This
slice does not silently recover that missing Card input from the separately
retained file or equate dates with numeric sequence revisions. Date retention is
a source-context follow-up under #148, not a claimed comparison or new query.

The declaration projection and its original-output application stay intact;
the new finding has its own application and full original input list. Generic
human inspection, targeted agent reading, source opening and saved literal
reading expose that same retained context. The generic support adapter expands
the new named derivation's input assertions separately from the model declaration
support, preserving existing API support rules and original payloads. Mapping and
binding need no Gemmi, source file, network or current sequence selection.

Old Cards and genuine SDK 181 saved metadata captures gain no finding on load.
Independent saved reading preserves the original stored output without executing
this interpreter or calculating checksums. Literal saved integrity does not
certify scientific truth. Existing formats/verifiers and native/API/declaration
rules stay unchanged. The dedicated human scientific question and experimental
structure request, current-selection admission, broader scientific/researcher/
workload acceptance and B3 remain open. B2 remains deferred and 0.15.0
consolidation paused. No molecular calculation or new source query is introduced.

Scientific field semantics come from the ModelCIF definitions of
[canonical polymer sequence](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_entity_poly.pdbx_seq_one_letter_code_can.html),
[entity sequence position](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_struct_ref_seq.seq_align_beg.html),
[reference CRC64](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_ma_target_ref_db_details.seq_db_sequence_checksum.html)
and [reference sequence start](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_struct_ref.pdbx_align_begin.html).
Only retained sequence-token quoting and ASCII layout are decoded under the
[CIF1 syntax](https://www.iucr.org/what-we-do/digital-standards/cif/cif1/file-syntax);
the original file parser/metadata format is unchanged. An independent local
Biopython/Gemmi control receives the new CRC and token predicates separately.

Local, exact-source, copied-payload and hosted scopes are recorded separately in
[the reference-context receipt](../evidence/alphafold_modelcif_reference_20261105.json).

## Native metadata intake continuation — 2026-11-05

The production supplied-file route now places the real model in a Card without
inventing a prediction-API record. `alphafold_modelcif_metadata@1` retains all
210 original non-atom-site columns, including literal quoting, multiline values,
unknown tags and `?`/`.` tokens, with scalar/loop membership. The original input
and its encoded/decoded SHA-256, sizes, compression, caller-declared source
terms and parser version remain in a separate receipt. Excluded atom table
categories (`_atom_site`, `_atom_site_anisotrop`) are identified by tags and row
counts. This is one supplied file, not a database-wide or online observation.

Gemmi >=0.7.5 is an optional parser, requested through DepDigest only when a file
is parsed. Ordinary API access, mapping retained metadata, Card loading and
independent saved reading do not import it. The complete CIF document must parse
as one block before any metadata is returned; malformed later loops, duplicate
tags and save frames are refused. Scalar/loop boundaries and unknown tokens are
retained rather than reconstructed as provider API JSON. This is not a general
coordinate import, TAR extractor, automatic downloader or multi-model reader.

`get_modelcif_metadata(identifier, client=...)` requires an explicit
`FixtureAlphaFoldModelCIFClient` or `SnapshotAlphaFoldModelCIFClient`. Snapshot
source/kind/query/revision binding is checked before file I/O. Encoded and decoded
file limits default separately to 64 MiB; refusal is explicit, with no partial
metadata. Callers can deliberately increase each limit or pass `None`. These byte
limits do not promise a parser/Python-object memory ceiling. Missing local files
remain unavailable input; malformed native records remain connector failures.
The API getter rejects a native client before calling it, directing the caller
to the separate getter. Neither route silently falls back to the other.

The existing declared AlphaFold enricher accepts this explicitly supplied client:

```python
from sabueso.tools.db.alphafold_modelcif import FixtureAlphaFoldModelCIFClient

card, report = sabueso.resolve(
    "Q8WZ42",
    resolver=explicit_reference_resolver,
    predicted_structures=True,
    alphafold_client=FixtureAlphaFoldModelCIFClient(
        "AF-Q8WZ42-F2-model_v6.cif.gz",
        retrieved_at="2026-11-05",
        expected_sha256="74da31b7a0153ef2c90dc8f60fe07edaa83ba50049bf06e6f4eb113ece1963ef",
    ),
)
model = card.explore().answer("predicted_models").items()[0]
declaration = model.open()
sources = model.related().filter("role", equals="source")
```

`alphafold_modelcif_declaration@1` projects the source's explicit AlphaFoldDB
identifier, UNP accession, entity/reference/alignment declarations, reference
CRC64/date, generation software and stated global pLDDT. It is a **derived
declaration summary**, bound to its original SourceAssertion and recorded output.
All literal columns remain at `asserted_value.modelcif_metadata`; extraction/file
receipts live in `source_metadata`. Alternative rows are not silently selected.
Inconsistent intervals leave the projected range unresolved while retaining both
source declarations. The raw isoform `?` is not an isoform assignment.

The filename's distribution `v6` never supplies `model_version`, and native
reference CRC64 never becomes a model MD5. Human model/source/back navigation,
targeted agent access and saved literal reading retain the same values. The
declaration itself does not evaluate canonical correspondence or enter old API
model-question rules. The later separate reference finding above checks only its
own exact original-input sequence interval. Focal model coverage, structural and
coordinate/assembly mapping remain uncomputed. Existing native/API context rules,
packets and saved formats/verifiers are unchanged. The dedicated native question,
independent scientific/researcher acceptance and broad B3 workload
acceptance remain next steps; this slice does not close #148/#173 or release 0.15.0.

The [receiving receipt](../evidence/alphafold_modelcif_intake_20261105.json)
distinguishes selected local, final-source and hosted qualification. Original
archive receiving below remains a separate historical scope. No new source
query or third-party publication was needed for this continuation.

## Original archive control

The human-proteome version 6 archive contains **AF-Q8WZ42-F2**, a titin fragment.
The retained original ModelCIF declares reference accession Q8WZ42, reference
interval **201–1600**, and model sequence positions **1–1400**. The 1,400-residue
sequence exactly equals that interval in the separately received native UniProt
record. The full-reference CRC64 and sequence-version date agree. Identity is
based on the source's explicit UNP/accession declaration; sequence equality
corroborates an interval and never merges entities or establishes an isoform.
The source's isoform marker `?` remains unknown.

## Original input and acquisition scope

The [official download page](https://alphafold.ebi.ac.uk/download) describes these
large-protein fragments in proteome TAR archives. A bounded positive locator
receives the exact member from
`v6/UP000005640_9606_HUMAN_v6.tar`, with a fixed strong ETag, exact HTTP206
Content-Range/total checks, native TAR checksum and complete gzip integrity.
Nineteen sparse requests transfer 4,595,292 bytes in 268.22 seconds, versus the
5,177,506,304-byte archive. Only the selected compressed member and header enter
the fixture; the archive is never downloaded or broadly extracted. Lexical
ordering is a search heuristic, not an archive-wide completeness/absence proof.

The original member is 269,404 bytes, SHA-256
`74da31b7a0153ef2c90dc8f60fe07edaa83ba50049bf06e6f4eb113ece1963ef`.
Its unchanged decoded ModelCIF is 1,298,513 bytes, SHA-256
`206ffc9821eaa76a33f7f3afe1b42f5ffd1eeae5b411c299cf8ae910f9964036`.
One separate native UniProt GET receives Q8WZ42, release 2026_04, entry 223,
sequence 4, 34,350 residues. Its sequence update date is 2012-04-18. Archive
distribution version, generation software, sequence revision and retrieval dates
remain separate. The complete public inputs, source/transport receipts and
licence obligations are declared in [NOTICE](../../temp_data/NOTICE.md).

## Native checksum and axis semantics

[ModelCIF's reference checksum](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_ma_target_ref_db_details.seq_db_sequence_checksum.html)
is **CRC64 of the reference sequence**, not the prediction API's model MD5.
Here the declared reference CRC64 is `DEB216410AD560D9`. A separately derived
fragment CRC64 is `884CB15CA14DC54F`; a derived fragment MD5 is
`509b42678e45f12fcf04d77877958e25`. Neither derived check is relabelled as a
source-stated checksum or stored as a SourceAssertion.

The [reference start](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_ma_target_ref_db_details.seq_db_align_begin.html)
and [reference end](https://mmcif.wwpdb.org/dictionaries/mmcif_ma.dic/Items/_ma_target_ref_db_details.seq_db_align_end.html)
identify positions in the reference database sequence. Target entity, reference
row, strand and model/reference numbering stay explicit. This source correspondence
does not establish experimental equivalence, observed atoms, physical assembly
membership or a qualified coordinate mapping.

The reproducible [offline control](../evidence/check_alphafold_archive_control_20261105.py)
checks the original header/member/reference hashes and every retained native tag
through existing Biopython and Gemmi readers independently, retaining literal CIF
`?` and `.` markers. It independently computes the full-reference CRC64, verifies
the stated MD5 against the full UniProt sequence and checks the exact interval.
Its named finding is `alphafold_archive_fragment_control@1`. This independent
control uses both developer readers; only the later explicit production file
route requests optional Gemmi. Neither is a mandatory runtime dependency or
needed for saved reading.

```bash
python devguide/evidence/check_alphafold_archive_control_20261105.py --output NEW_DIRECTORY
```

## Original control qualification and production follow-up

Original public input receiving and the above finite correspondence control are
now reproducible offline. The four original SDK/standard-library controls preserve original bytes,
metadata/checksum scope, the explicit API boundary and human/agent/saved access
to a **sequence-only reference control**. They do not pretend that the archive
model has entered a Card. The existing API getter still refuses a missing API
fixture instead of silently reading the archive or claiming global model absence.

The original control proposed the following production follow-up. The metadata
intake above implements the explicit input and literal Card access; the separate
native correspondence/question work in steps 2–4 remains open:

1. Preserve the original metadata, transport/file identity and source support;
   use a qualified file/metadata reader without adding an implicit coordinate
   downloader or molecular calculation to Sabueso.
2. Bind the original target/reference rows, accession, interval, CRC64 and sequence
   revision to the explicitly supplied Card reference. Keep alternatives, unknown
   isoforms and incompatible source scopes unselected.
3. Derive an archive-native context and whole/fragment request under new named
   rules. Do not fabricate an API-shaped model, promote a computed MD5 to a
   provider assertion or change original context/request @1/@2 meanings.
4. Receive the real model through native, human, compact-agent, original-source,
   back-navigation and independent saved reading; preserve earlier verifiers and
   payloads. Record scientific/researcher/workload acceptance separately.

The full titin sequence panel exposed a separate
[session-save capacity finding](../pending_bugs/large_sequence_panel_save.md)
under #167/#148. Its original stop is retained. The
[shared-support correction](shared_link_support.md) now receives the complete
public panel separately under the same 512 MiB guard; the passing sequence-only
reference control never substitutes for that workload. B3 and broad 0.15.0
acceptance remain open; B2 review stays deferred and release consolidation paused.

Originals, local receipts and owned resource measurements remain under
`recovered_work/alphafold_archive_control_20261105/`, owner #148/#173/#167/#112,
review at native intake, capacity correction or the next B3 checkpoint.

The [receiving receipt](../evidence/alphafold_archive_control_20261105.json)
separates the finite source/sequence control from the originally failing full-save
workload. Both the complete native files and their literal projection are kept;
the reviewed-input count does not declare a new public archive getter.
