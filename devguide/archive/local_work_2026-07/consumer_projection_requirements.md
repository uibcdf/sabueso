# Reviewed consumer projection requirements

Reviewed on 2026-10-06 against the current [consumer roadmap](../../ROADMAP.md#4-close-consumer-contracts-in-parallel)
and MOLI's Scientific Context/Modeling Context ownership. This recovers requirements
from the preserved `devguide/MOLSYSSUITE_INTEGRATION.md`; it is not an accepted
exchange schema or a delivered consumer integration. The original contains proposals,
with no corresponding exporter or receiving implementation to restore.

## Useful requirements and current boundaries

| Preserved requirement | Current interpretation | Acceptance owner |
| --- | --- | --- |
| Dependency-neutral annotation exchange | Use stable public Sabueso interfaces and independently version any agreed adapter. Do not make modeling tools depend on Sabueso internals. | MOLI and both adapter owners |
| Original support and stable identifiers | Retain exact card/item pins and original SourceAssertions, their sources and independent revisions. Historical `EvidenceStore` and `evidence_ids` do not define the current contract. | Sabueso supplies knowledge; the receiver retains support |
| Exact, aligned, ambiguous, partial and unmapped locations | Preserve original entity, sequence/construct identity, numbering and native location. Any proposed normalized mapping states its basis, uncertainty and exclusions. These status names remain candidate requirements. | Sabueso supplies declarations; the mapping owner supplies and qualifies the mapping |
| Residue remapping on extraction, removal, merge and copy | Receiver-local indices change independently of source positions. Preserve original references, report losses and conflicts, and test each molecular operation. Equal residue numbers or equal sequences do not establish identity. | MolSysMT and the participating adapter owner |
| Quantities survive exchanges | Preserve the current PyUnitWizard quantity codec and units, including missing values. Old bare numeric/unit labels are not a new interchange representation. | Both adapter owners |
| Offline visualization and compact saved state | Keep display choices and exact references in consumer state. Opening a saved view must not implicitly reacquire sources or replace historical knowledge. Rights and retention remain source-specific. | MolSysViewer |
| Calculated pockets, networks and project interpretations | Keep source assertions separate from calculation results and consumer-owned Evidence. A geometry operation does not become a source observation. | Modeling/calculation owners and Nextia |

The old `sabueso.to_molecular_deck`, `msm.project_knowledge`, `molsys.deck` and
viewer addon examples are unimplemented directions. No such API is introduced here.
Sabueso's current cards, decks, pinned knowledge packets and index/item readers are
available foundations; their presence does not prove consumer acceptance. MOLI owns
the Sabueso-to-MolSysSuite boundary, while MolSysSuite owns its internal member contracts.

## Concrete receiving checks to retain

1. Read an exact historical item by its pin after a newer acquisition; verify that
   saved consumer support still identifies the original knowledge. Extend the
   existing public `examples/persisted_pipeline/` journey with receiving tests
   under the Nextia/Context Assembly owners (Sabueso #53/#71, MOLI #3/#22).
2. Keep a canonical position, a source-sequence position, a PDB author number with
   insertion code, a PDB label number and a zero-based local modeling index distinct.
   Source-declared SIFTS segment endpoints do not justify interpolated residue maps.
3. Present absent support, unqueried mappings, failures, conflicting placement and
   unidentified source sequences explicitly. An unplaced annotation must survive
   round-trip without being decorated as an exact local residue match.
4. Verify extraction, removal, merge, append and copy with changed local indices,
   stable source references and explicit loss reports. Separate source identity
   from receiver-local identifiers, and preserve alternatives without silent merging.
5. Round-trip quantities, native method/score semantics and independent source,
   sequence and structure revisions. A source confidence score is not a project
   Evidence assessment; a service version is not a record revision.
6. Reopen a saved viewer state offline and verify zero acquisition and unchanged
   historical support. Test retention/attribution separately from rendering choices.

These are receiving acceptance cases for coordination, including visualization
work under Sabueso #80. They require owner review and tests in the receiving
components; this archival review does not claim to close those work items.
