# Bioactivities of a protein

ChEMBL activity records of a resolved protein become `has_bioactivity` relationships
from the protein to each tested molecule. Each measurement is one relationship. It keeps
the measured value, the assay (including how ChEMBL assigned it to the target) and the
document it comes from:

```python
import sabueso

card, resolution = sabueso.resolve_protein_card("P52270", chembl={})
# Outcome: added / not_found / error, with the ChEMBL release and any truncation.
print(card.quality["enrichments"])

view = card.bioactivities()
for item in view["items"][:5]:
    print(item["molecule_ref"], item["class"], item["best_pchembl"], item["classes"])
print(view["documents"])  # measurements per document: source bias is visible
print(view["excluded"])  # e.g. assays assigned to the target by homology
print(view["classification"])  # rule bioactivity_class@1 and its thresholds
```

The classes (`active`, `weak`, `inactive`, `inconclusive`, `not_determined`,
`unclassified`) are derived by Sabueso from explicit thresholds. ChEMBL does not state
them. Pass `thresholds={"active_max_uM": 1.0}` to change the thresholds, or
`include_indirect=True` to include measurements that ChEMBL assigned by homology.

Clients: `sabueso.tools.db.chembl.OnlineChEMBLClient` and `FixtureChEMBLClient`.
