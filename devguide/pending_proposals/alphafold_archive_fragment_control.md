---
summary: Preserve and independently check a genuine public AlphaFold archive fragment without pretending it is an API response.
issue: uibcdf/sabueso#148
status: original_input_received_native_intake_pending
opened: 2026-11-05
area: [predicted-structures, source-contracts, structural-exploration]
---

# A genuine public archive fragment

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
Its named finding is `alphafold_archive_fragment_control@1`. These developer
dependencies are not new Sabueso runtime dependencies.

```bash
python devguide/evidence/check_alphafold_archive_control_20261105.py --output NEW_DIRECTORY
```

## What is qualified, and the next production step

Original public input receiving and the above finite correspondence control are
now reproducible offline. The four original SDK/standard-library controls preserve original bytes,
metadata/checksum scope, the explicit API boundary and human/agent/saved access
to a **sequence-only reference control**. They do not pretend that the archive
model has entered a Card. The existing API getter still refuses a missing API
fixture instead of silently reading the archive or claiming global model absence.

Production intake needs a separate named **native supplied-input contract**:

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
