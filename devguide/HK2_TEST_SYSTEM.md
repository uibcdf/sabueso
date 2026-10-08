# Human HK2 as a public test system

Human hexokinase-2 (UniProt **P52789**) complements TcTIM and HsTIM. Its repeated
hexokinase domains, two labelled ATP-site groups and native variant annotations
exercise sequence scope and independent support on a different public protein.

The baseline is rebuilt with the current public API from the unchanged native
`temp_data/P52789.json` response. Its acquisition date and CC BY 4.0 terms are
declared in `temp_data/NOTICE.md`. Generated cards use the development schema;
they are not historical card migrations or frozen published-schema fixtures.

From the repository root in the existing editable development environment:

```bash
python -m tools.build_hk2_test_system --output recovered_work/current_HK2
python -m pytest -n 12 -m "not online" --receptor=llm tests/core/test_hk2_test_system_offline.py
```

The builder writes `HK2_human.card.json`, `HK2_human.ipynb` and `receipt.json`.
The receipt identifies the original response hash, acquisition date, admitted
scope, current schema and pinned card. The integrated test checks subject-bound
sequence/quantity support, separate ATP annotations, explicit unqueried scope,
exact KnowledgeStore persistence, report regeneration without source access and
CLI output paths from another directory.
Existing domain/residue, mutagenesis, mapping completeness and SourceAssertion
tests also use HK2.

The current reproducible baseline covers **UniProt**. Its cross-references and
annotated ATP sites do not supply experimental structure contacts or a ligand
deck. Expanding HK2 like the multi-source TIM baseline needs original public
RCSB, PDBe-KB, InterPro, ChEMBL and any other intended source responses, with
native identity, assay/unit, numbering, release, completeness and rights checks.
Add those responses to the fixture notice and the integrated test when qualified.
Future acceptance remains in #112/#83/#95; existing provider deferrals still apply.

The old HK2 card, ligand list and notebooks are useful only as an audit of desired
cases and unverified native-query hints. A file named `PTGS2_human.card.json` in
that material actually declares HK2; its values cannot establish a PTGS2 baseline.
Do not copy its old Evidence records into SourceAssertions, equate compounds by
name or SMILES, or preserve obsolete output as an expected scientific result.
Generate expected cards and reports from qualified source responses instead.

Historical-review disposition and the temporary local backup are documented in
[follow-up 35](archive/local_work_2026-07/followup_35_final_review_and_hk2.md).
