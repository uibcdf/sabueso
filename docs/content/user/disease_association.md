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
(`annotations.population_variants`). gnomAD is asked for the gene and for the Ensembl
transcripts UniProt states for the canonical isoform. When gnomAD states a protein
change on the canonical transcript, that is the one kept, in UniProt numbering (the
residue must match). A variant gnomAD states changes no residue of the canonical
transcript (it is in an intron or a UTR there) keeps its consequence on the other
transcript, with `canonical_consequence`, and is not placed
(`not_coding_on_canonical`). Otherwise the same rule as ClinVar applies. Variants
without a protein change are left out, and the enrichment record counts them. By default every variant, up to 5000 (`{"limit": n}` asks for fewer); a cut is reported.

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
    medgen=True,
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
- A ClinVar condition is one statement with every id ClinVar states for it. It joins a
  disease when any of those ids does.
- `medgen=True` asks MedGen which record each MedGen concept id is (`C1860808` is
  record 349893). MONDO states its equivalences by those records, so a condition named
  only by a MedGen concept id reaches MONDO through two statements, MedGen's and
  MONDO's (`medgen_concept@1`).
- What reaches no MONDO term stays apart, with its reason. It is never grouped by
  name:
  - `condition_not_provided`: ClinVar's "not provided" and "not specified", which are
    not diseases;
  - `no_stated_equivalence`: for example some EFO terms, or phenotypic traits;
  - `no_id_stated`: a condition named only by text;
  - `namespace_not_mapped`: for example HP phenotype terms;
  - `conflicting_identity`: the ids of one condition reach two MONDO terms, and MONDO
    does not place one under the other. All are listed, and none is chosen.
- A condition named at two granularities joins the broader disease. ClinVar sometimes
  gives a broader Orphanet id next to the MONDO and OMIM ids of a subtype, or names
  "Obesity" with the Orphanet id of obesity due to MC4R deficiency. When MONDO places
  one term under the other, the statement joins the broader term, because what holds
  for a subtype holds for the disease it belongs to. The narrower term is kept in the
  statement (`narrower`), with MONDO's chain of terms (`mondo_hierarchy@1`).
- `disease_identity` reads the diseases the other sources put on the card, so ask for
  them in the same call.

## From a disease to its targets and its drugs

```python
import sabueso

targets = sabueso.disease_targets("ORPHA:868")  # a deck of protein cards
for card in targets.cards:
    print(card.id, targets.basis(card.id)["statements"])
print(targets.meta["excluded"])  # what was left out, and why

drugs = sabueso.disease_drugs("mondo:MONDO:0001444")  # Chagas disease
for card in drugs.cards:
    print(
        card.id, [i["max_phase_for_ind"] for i in drugs.basis(card.id)["indications"]]
    )
```

- **Targets** (`disease_targets@1`) come from Open Targets' associated targets (asked by
  the MONDO id, then its EFO equivalents) and Orphanet's genes of the disorder (asked by
  its Orphanet equivalents). Each member is the Swiss-Prot product a source states for
  the gene. Its basis lists every statement that brought it, with Open Targets' score
  and rank, or Orphanet's association type and status, as stated.
- **Drugs** (`disease_drugs@1`) are the molecules whose ChEMBL drug indications name the
  disease by its MONDO id or by the EFO and MeSH ids MONDO states are the same disease.
  They are ordered by ChEMBL's `max_phase_for_ind`, highest first.
- Nothing is matched by name, and a disease that does not resolve is refused.
- **Each member is a whole card**, which costs at least one request. So these decks
  build 50 members by default (`limit=`). The rest are listed in `meta["excluded"]` with
  the reason `limit`, and the cut is reported with a warning. A gene with no Swiss-Prot
  product is excluded with its reason.
