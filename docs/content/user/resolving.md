# Resolving an entity

`sabueso.resolve(query, **options)` is the entry point. It decides which entity a query
refers to, builds that entity's card from the sources, and returns the card together
with the resolution that explains every choice:

```python
import sabueso

card, resolution = sabueso.resolve("P52270")
print(resolution.status)  # resolved, ambiguous, not_found, unsupported or error
print(resolution.decision["route"], resolution.decision["rules"])
```

## What a query can be

| Query | Entity |
|---|---|
| a UniProt accession (`P60174`, `uniprot:P60174`) | protein |
| an isoform (`P60174-3`) | the protein, with the isoform in `resolution.qualifiers` |
| `pdb:<id>` | the structure record: no card, and the proteins its entities map to in `resolution.related` |
| `EntityQuery(name=..., organism=..., include_subtaxa=False)` | protein, found by name within an organism (taxon id or scientific name) |
| `chembl:<id>` or a bare ChEMBL id | small molecule |
| `pdb.ligand:<code>` | small molecule (PDB Chemical Component Dictionary) |
| `pubchem:<cid>` | small molecule |
| `inchikey:<key>` or a standard InChIKey | small molecule |

Small-molecule cards are anchored at the standard InChIKey, whichever record the query
names. `entity_type=` overrides the route.

## Ambiguity is reported, never chosen silently

A name matches several entries more often than not. Sabueso never resolves from a
truncated or ambiguous result:

```python
from sabueso.resolver import EntityQuery

card, resolution = sabueso.resolve(
    EntityQuery(name="triosephosphate isomerase", organism=5693, include_subtaxa=True)
)
print(resolution.status, resolution.decision["rules"])
for finding in resolution.decision.get("identity_audit", []):
    print(finding["finding"], finding["refs"], finding["basis"])
```

- **One preference, stated.** When one candidate is a reviewed (Swiss-Prot) entry and the
  others are not, the policy `prefer_reviewed@1` chooses it. The rule is recorded, and
  the others stay listed as `alternatives`.
- **Ambiguous results.** When no preference decides, the status is `ambiguous`, with the
  `candidates`. `sabueso.ambiguity_deck(resolution)` turns them into a deck to inspect.
- **Identity audit.** The candidates are audited (`protein_identity_audit@1`), gene
  loci first, then sequence:
  - `possibly_same_as`, for review: redundant entries or strain variants;
  - `same_gene`: fragments and isoforms;
  - `distinct_genes`: paralogs, however similar their sequences.
  Nothing is merged. When two entries state their gene in databases that do not overlap
  (NCBI Gene for one, an organism database for the other), the basis says
  `gene_loci: not_comparable`. Pass `ncbi_gene=True`, and NCBI Gene is asked whether
  one gene lists both entries as its products (`gene_products` in the basis).
- **Curated names.** A name a publication uses, recorded in a curation store, anchors a
  resolution by name: `resolve(EntityQuery(name="TcTIM", organism=5693),
  curations=store)` ({doc}`literature_and_curation`).

## Options

Options are passed to the tool that answers the query. An option that tool does not
take is refused, never ignored.

**Proteins**

| Option | Adds |
|---|---|
| `structures=["1TCD", ...]` or `"all"` | RCSB details of experimental structures ({doc}`structures`) |
| `predicted_structures=True` | AlphaFold DB models |
| `interfaces=True` | PDBe-KB interface residues ({doc}`sites_and_interfaces`) |
| `ligand_sites=True` | PDBe-KB ligand binding sites |
| `family_sites=True` | InterPro family sites on the sequence |
| `chembl={}` or `{"limit": 1000}` | ChEMBL bioactivities ({doc}`bioactivities`) |
| `bindingdb={}` | BindingDB affinities, grouped with ChEMBL's measurements |
| `pubchem_bioassay=True` | PubChem BioAssay results; declared copies lead to their originals |
| `string={"required_score": 700}` | STRING functional associations |
| `taxonomy=True` | NCBI Taxonomy ranks and ancestors of the organism |
| `ncbi_gene=True` | NCBI Gene, for the identity audit of a resolution by name |
| `curations=store` | the curated statements recorded for the entity |

**Small molecules**

| Option | Adds |
|---|---|
| `unichem=True` (default) | the records UniChem links to the InChIKey |
| `pubchem=True` | the PubChem records UniChem links |

## Profiles

A profile names a versioned set of options, so a study states which baseline it
builds:

```python
card, resolution = sabueso.resolve("P52270", profile="structural_baseline@1")
print(resolution.decision["profile"])  # name, the options it gave, those you overrode
```

- `identity@1` asks for no enrichment.
- `structural_baseline@1` asks for every experimental structure, interfaces, ligand and
  family sites, and ChEMBL bioactivities.
- A published profile never changes; a change becomes a new version. Options you pass
  explicitly override the profile, and the override is recorded.

## What the card records

- `card.quality["entity_resolution"]` holds the resolution: its sources, the rules
  applied, the alternatives and the identity links.
- `card.quality["enrichments"]` holds one outcome per requested enrichment: `added`,
  `not_found` or `error`, with the source release. A truncated result says so (for
  example, "ChEMBL returned 25 of 493 records").
- `card.knowledge_state()` says, per area and source, what is known, in conflict, not
  stated, not asked or unavailable ({doc}`concepts`).

## Working offline

Every source has a fixture client that reads saved responses. Pass them to `resolve` to
build cards without network access, for example in tests:

```python
from sabueso.resolver import EntityResolver, FixtureRCSBClient, FixtureUniProtClient
from sabueso.tools.db.chembl import FixtureChEMBLClient

resolver = EntityResolver(
    FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
)
card, _ = sabueso.resolve(
    "P52270",
    resolver=resolver,
    chembl={},
    chembl_client=FixtureChEMBLClient("temp_data"),
)
```

The online clients are the default. To query a source without building a card, see
{doc}`tools/db/sources`.
