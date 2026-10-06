# Small-molecule cards

A molecule card collects what sources state about one chemical entity. Its anchor
is a source-stated standard InChIKey. ChEMBL, PubChem, CCD and UniChem records join
that anchor through explicit identity statements; a shared name does not establish
identity, and Sabueso does not calculate an InChIKey to manufacture a match.

## Resolve and read

```python
import sabueso

card, resolution = sabueso.resolve("chembl:CHEMBL110", indications=True)
print(resolution.status)
if card is not None:
    print(card.id)
    print(card.list_fields())
    print(card.get("names.canonical_name"))
    print(card.clinical())
```

CHEMBL110 is benznidazole, a public example. Other entry forms include
`pubchem:<CID>`, `pdb.ligand:<CCD code>`, `inchikey:<key>`, `smiles:<text>` and an
InChI. Structure-text inputs use PubChem's stated match. Inspect ambiguity and
unsupported/not-found outcomes; do not select an alternative silently.
See {doc}`resolving` for identifiers and options.

Fields retain their supporting SourceAssertion ids. Physicochemical values are
source statements, not locally calculated descriptors. Physical quantities retain
their units; use `Card.quantity` for quantity fields and {doc}`field_paths` to find
their paths. Alternatives/conflicts remain inspectable on the card.

## Activity belongs to an experimental context

Resolving a molecule does not query all experiments against all its targets.
Current activity access is through a protein card and its source-supported
relationships:

```python
target, resolution = sabueso.resolve("P52270", chembl={})
if target is not None:
    molecules = sabueso.ligand_deck(target)
    activities = target.ligands(molecules)
    measurements = target.bioactivities()
```

The ligand view crosses the protein's activities with the molecular cards' stated
identity. Retain target, molecule, assay, measurement type, relation, quantity and
publication support. An IC50 and a binding affinity are different measurements;
an activity class is a named derivation, not a source assertion or proof of binding
at a specific site. Missing activity is not a statement of inactivity.
See {doc}`bioactivities` and {doc}`decks`.

## Clinical scope and persistence

`indications=True` adds ChEMBL indications. `trials={}` additionally fetches the
ClinicalTrials.gov studies cited by those indications. Trial interventions are
not matched to a molecule by name. Pharmacology, ADMET, contraindications and drug
interactions are not complete clinical coverage; see {doc}`clinical`.

```python
store = sabueso.KnowledgeStore("molecules.db")
ref = store.save(card)
historical = store.load(ref)
node = historical.get("names.canonical_name")
support = historical.explain(node["source_assertion_ids"])
item_refs = [ref + "#" + item for item in node["source_assertion_ids"]]
```

Run persistence only after successful resolution. Keep original acquisition and
workflow attribution JSON alongside the scientific objects; saved reads do not
recreate runtime records. Inspect {doc}`terms` and {doc}`source_coverage` for reuse
rights and coverage. See {doc}`journeys` for the independently readable protein
comparison. The following molecule/declared-target example preserves the narrower
scientific question alongside its original statements and runtime records.

## Run the molecule and declared-target journey

From a development checkout with Sabueso installed and public fixtures available:

```bash
python examples/user_journeys/molecule_target.py produce --output /tmp/sabueso-molecule-target --fixtures temp_data
python examples/user_journeys/molecule_target.py read --output /tmp/sabueso-molecule-target
python examples/user_journeys/molecule_target.py reacquire --output /tmp/sabueso-molecule-target --fixtures temp_data
python examples/user_journeys/molecule_target.py read --output /tmp/sabueso-molecule-target
```

Start with an empty output directory. The public examples are BTS
(CHEMBL1161789, the ligand of 1SUX) and benznidazole (CHEMBL110), both measured
against the explicitly supplied TcTIM target P52270. BTS's reported IC50 is
33,000 nM; benznidazole has an 18% inhibition measurement at 400 micromolar and
another record without a determined value. Original assay descriptions, direct
target assignments, source versions and publications remain available. The rules'
classes apply to these assays; they do not establish universal inactivity, clinical
efficacy or a particular binding site.

Benznidazole's ChEMBL indications retain separate EFO/MONDO/DOID disease references
and 16 cited NCT ids. The studies themselves are not fetched. BTS indications,
other targets and other activity providers are not queried. The absent benznidazole
UniChem fixture is unavailable, not an external absence assertion. Complete clinical
coverage and a reverse search across all molecular targets remain separate work.

The saved bundle holds three cards, a two-molecule deck, an index packet for the
target's broad context and a separate original report for the selected molecules.
The packet is not a molecule-filtered query. Each reader runs without fixtures,
checks exact historical identity/assay support and original attributions, and
exports the producer's bibliography without new acquisition, derivation or credit.
Reacquisition advances heads while the first report and citations remain intact.
Keep both example scripts together and retain the complete output directory.

The original explanations retain broad classification context (about 30 MB of report
JSON per acquisition in these fixtures). The manifests detect changed or misbound
files, not authenticity, reuse permission or a shared MOLI recording contract.
Published `knowledge_state@4` can misclassify successful CCD/UniChem intake as
`not_stated`. The development `knowledge_state@5` corrects native record counts,
retains unknown counts and missing subsets, and separates molecular identity from
clinical indication/study intake ([#122](https://github.com/uibcdf/sabueso/issues/122)).
Readers keep the original producer's report/rules even after this correction;
original source statements and observed query outcomes remain inspectable.
