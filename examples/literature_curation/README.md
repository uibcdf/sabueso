# Public literature review and preservation rehearsal

The [review draft](hstim_review.json) contains three proposed readings of the published
abstract of [Rodriguez-Almazan et al. (2008)](https://pubmed.ncbi.nlm.nih.gov/18562316/),
DOI [10.1074/jbc.M802145200](https://doi.org/10.1074/jbc.M802145200). Codex prepared the
draft; no human validation is recorded. The full text, figures and tables were not
read. No article payload or private pilot content is included.

The draft describes the interfacial water network and the purified recombinant
mutant's stability, keeping those observations attached to the publication and their
experimental context.

| Candidate | Proposed destination | Rehearsed outcome |
| --- | --- | --- |
| Variant water-network description | `features_positional.natural_variant` | `differs` |
| Recombinant-mutant stability | `literature.claims`, topic `stability` | `not_compared` |
| Interfacial water bridges | `literature.claims`, topic `interface` | `not_compared` |

These are mechanical outcomes against the frozen public baseline, not judgments of
scientific novelty or contradiction. The variant's existing annotation remains; the
two free-text claims are added separately and never compared semantically.

## Identity and numbering

The frozen UniProt card links P60174 to 2VOM. RCSB gives that structure this paper as
its primary citation and maps UniProt position 105 to author position 104 on chain A
(`rcsb_author_numbering@1`). The canonical residue is E and the mapped mutant is D.
The rehearsal verifies every step. Equal residue numbers and protein-name similarity
are not an identity or numbering basis.

## Run the isolated rehearsal

From a development checkout with Sabueso's test dependencies:

```bash
python -m tools.rehearse_public_curation --output /tmp/hstim-curation-rehearsal
```

The output directory must be new. The script uses public frozen UniProt/RCSB responses,
requires no network, and creates `report.json`, `hypothetical_curations.jsonl` and
`hypothetical_knowledge.db`. Every curation identifies its curator as an acceptance-test
simulation. The artifacts exercise a hypothetical human-approved intake; they are not
accepted project knowledge.

The report records the numbering checks, outcomes, original annotation, conflicts and
pinned source support. It verifies that all three statements keep their identifiers,
content and outcomes after a rebuild, and that their historical references remain
readable after the rebuilt card is saved.

## Actual intake

Review the readings against the cited abstract, their context and the numbering basis.
Once a person confirms them, use `Card.add_literature_assertion` with that person's
curator name, actual review date and the recorded locators; save the card in the
person's `CurationStore`. Do not import the simulated records as reviewed curation.

The current curation API records `acquisition.method: curation`; its contract means a
person's reading. Model extraction keeps its tool/version and any actual
`validated_by` separately (#92). `CurationStore` excludes extractions, even validated
ones (#105), while `KnowledgeStore` can preserve the exact acquired card state.
