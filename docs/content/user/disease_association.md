# Disease association

A human protein card can hold what DISEASES, Open Targets and Orphanet state about the
diseases its gene is associated with. Each source, and each DISEASES channel, is kept
apart.

```{note}
Disease associations are available since release 0.6.0.
```

```python
import sabueso

card, _ = sabueso.resolve("P60174", diseases={})  # human triosephosphate isomerase
for rel in card.relationships("associated_with"):
    q = rel["qualifiers"]
    print(rel["object_ref"], q["disease_name"], q["channel"], q.get("source_database"))
```

## Channels

- `knowledge` (default): associations curated by other resources (MedlinePlus, UniProt
  keywords…), with the resource and DISEASES's confidence.
- `experiments` (default): associations from experimental resources (for example GWAS
  through TIGA), with their own score.
- `textmining` (only when asked, `diseases={"channels": ["knowledge", "textmining"]}`):
  co-mentions in the literature, with a z-score. Text mining links **names**, not
  molecules. The human triosephosphate isomerase is co-mentioned with giardiasis,
  because the parasite's enzyme has the same name.

The same disease in two channels is two relationships, never merged. Scores are
DISEASES's own, as it states them; Sabueso does not rank them.

## How an association reaches the card

DISEASES names genes by Ensembl protein. An association is added only for an Ensembl
protein that the UniProt entry cross-references: `via_protein`, and `uniprot_isoform`
when UniProt maps it to an isoform. It is never matched by gene name.

## Open Targets

`sabueso.resolve("P60174", open_targets={})` adds every association Open Targets states
for the gene, up to a safety ceiling of 5000 (`{"limit": n}` asks for fewer), in Open
Targets' own order. A cut is recorded and reported with a warning. Each association keeps:
- the overall `score`, `datatype_scores` (genetic association, literature, known
  drug…) and `rank`. They are Open Targets' own computation, recorded as stated with
  the data version, never recomputed;
- the disease under Open Targets' term (`mondo:MONDO:0014221`). The same disease under
  a DISEASES term (`doid:DOID:0050884`) stays a separate reference.

The association reaches the card through the Ensembl gene the UniProt entry
cross-references (`via_gene`). It is added only when Open Targets also lists the entry
among that gene's products.

## Orphanet (rare disorders)

`sabueso.resolve("P60174", orphadata=True)` adds the rare disorders Orphanet associates
with the gene (`orphanet:ORPHA:868`). Each one comes with Orphanet's wording:
- the association type (for example "Disease-causing germline mutation(s) in") and its
  status ("Assessed");
- the disorder's type and group;
- the publications that validate it.

Orphanet states the gene's UniProt accession itself, so the link is its own. The file
(about 22 MB) is downloaded once per process, and its date is the version.

## ClinVar (variants)

`sabueso.resolve("P60174", clinvar={})` adds ClinVar's variants of the gene
(`annotations.clinical_variants`), found by the NCBI Gene id the UniProt entry
cross-references. By default every record of the gene, up to 5000 (`{"limit": n}` asks for fewer); a cut is reported.
Each variant keeps what ClinVar states:
- the HGVS title, variant type and consequences;
- the germline classification and its review status. "Conflicting classifications of
  pathogenicity" is ClinVar's own statement, never resolved;
- the conditions, with their cross-references.

**Numbering.** ClinVar lists a protein change in every isoform's numbering ("E142D,
E105D, E23D"). A variant is placed in UniProt numbering (`location`, `numbering:
"uniprot"`) only when two things hold: its transcript is one UniProt states for the
canonical isoform, and the residue ClinVar names is the UniProt residue at that
position. A change on another isoform's transcript is placed through that isoform's
edits as UniProt states them (`placed_via`, rule `uniprot_isoform_map@1`). For example,
position 142 of isoform P60174-3 is canonical 105. A change inside an isoform's own
segment has no canonical position.

Otherwise `not_placed` says why:
- `no_protein_change`;
- `unparsed_protein_change`;
- `transcript_not_canonical`;
- `isoform_specific_position`;
- `stop_codon`;
- `residue_mismatch`.

Nothing is placed by aligning sequences.

ClinVar is not for diagnostic use without review by a genetics professional.

## gnomAD (population frequencies)

`sabueso.resolve("P60174", gnomad={})` adds gnomAD's variants of the gene with a protein
change, each with its allele count, allele number and frequency in exomes and genomes
(`annotations.population_variants`). They are placed in UniProt numbering by the same
rule as ClinVar, through an Ensembl transcript UniProt states for the canonical
isoform. Variants without a protein change are left out, and the enrichment record
counts them. By default every variant, up to 5000 (`{"limit": n}` asks for fewer); a cut is reported.

## Coverage

DISEASES, Open Targets, Orphanet and ClinVar cover human genes only. For a protein of another organism,
the knowledge state says `not_queried`, with that reason, never `not_stated`.

The files are downloaded once per process, about 50 MB with text mining. Set
`$SABUESO_CACHE_DIR` to keep them between sessions. The version recorded is each file's
publication date.

## Disease cards (MONDO)

A disease is also an entity of its own, anchored at a MONDO term. MONDO integrates the
terminologies the sources above use (DOID, Orphanet, OMIM, MeSH, EFO, NCIT…) and states,
term by term, which of their ids are the same disease.

```{note}
Disease cards are on main, not yet in a release (card schema 0.3.7).
```

```python
import sabueso

# The same disease, named by DISEASES (DOID), Orphanet and MONDO
for query in ("doid:DOID:0050884", "ORPHA:868", "mondo:MONDO:0014221"):
    card, resolution = sabueso.resolve(query)
    print(card.id, resolution.decision.get("identity"))

card.get("names.canonical_name")  # triosephosphate isomerase deficiency
card.get("identifiers.equivalent_ids")  # the ids MONDO states are this disease
card.relationships("subclass_of")  # its parent terms in MONDO
```

- **Identity only through stated equivalence** (`mondo_equivalence@1`). An id of another
  terminology resolves only when MONDO states that it is the same disease. The
  resolution records that statement and the MONDO release.
- **Related is not the same.** MONDO's other cross-references are related terms. They
  are kept in `identifiers.related_ids`, and never used to join.
- **Obsolete terms** are not followed. The resolution (`obsolete`) names the replacement
  MONDO states as a candidate.
- `omim:` and `mesh:` also number genes and chemicals. Those have no MONDO equivalence
  and are reported as not found, never as a disease.
- MONDO's release file (about 53 MB) is downloaded once per process and checked against
  its published SHA-256.

## A protein's diseases, grouped (MONDO)

The same disease reaches a protein card under several ids: DISEASES writes
`doid:DOID:0050884`, Orphanet `orphanet:ORPHA:868`, UniProt the MIM number `615512`,
ClinVar a list of ids per condition. `disease_identity=True` asks MONDO which of them
it states are the same disease, and `Card.diseases()` groups them:

```python
card, _ = sabueso.resolve(
    "P60174",
    diseases={},
    open_targets={},
    orphadata=True,
    clinvar={},
    disease_identity=True,
)
view = card.diseases()
for disease in view["diseases"]:
    print(disease["mondo"], disease.get("mondo_name"), disease["sources"])
for item in view["ungrouped"]:
    print(item["ref"], item["source"], item["reason"])
print(view["rule"]["rule"])  # disease_grouping@1
```

- Each id MONDO states is the same disease becomes a `same_as` relationship to its
  MONDO term (`basis: mondo_equivalence@1`), backed by a MONDO SourceAssertion.
- Statements are grouped only through those, or when they name the same id. For human
  triosephosphate isomerase, triosephosphate isomerase deficiency is one disease stated
  by ClinVar, DISEASES, Open Targets, Orphanet and UniProt.
- What MONDO does not state stays apart, with its reason (`no_stated_equivalence`),
  and is never grouped by name. Examples are MedGen concept ids and some EFO terms.
- `disease_identity` reads the diseases the other sources put on the card, so ask for
  them in the same call.
