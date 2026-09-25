"""Build docs/content/showcase/knowledge_baseline.ipynb and execute it against live APIs.

Run from the repository root, in an environment where Sabueso is installed from this
checkout (``pip install --no-deps -e .`` after the last commit, so the notebook prints the
exact version), with ``nbformat``, ``nbclient`` and ``ipykernel``:

    python tools/build_showcase_notebook.py            # build and execute (network)
    python tools/build_showcase_notebook.py --no-execute

The same flow runs offline in ``tests/core/test_knowledge_baseline_offline.py``; change
both together.
"""

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

OUT = Path("docs/content/showcase/knowledge_baseline.ipynb")

cells = []


def md(text):
    cells.append(nbformat.v4.new_markdown_cell(text.strip()))


def code(text):
    cells.append(nbformat.v4.new_code_cell(text.strip()))


md("""
# A knowledge baseline for two proteins

This notebook builds a traceable knowledge baseline for two proteins with Sabueso's public
API: triosephosphate isomerase from *Trypanosoma cruzi* (TcTIM, UniProt P52270) and from
*Homo sapiens* (HsTIM, UniProt P60174). They are used here as test systems; nothing below
depends on what they are studied for.

Every value on a card is linked to the **SourceAssertions** that support it: what each
source states, when it was retrieved, and where sources disagree. The notebook asks, in
order:

1. Which entities are these, and which other entries could be mistaken for them?
2. Who says what about them?
3. What does each card know it does not know?
4. Which experimental structures are known, and which predicted models?
5. What do sources state about their oligomer and its interface?
6. Which molecules have been measured against them, and which do both share?
7. Which publications support which statements?
8. How is a claim read in a paper recorded, and compared with the databases?
9. What do the two proteins state alike, and differently?
10. How is the baseline cited, stored and read back exactly?

It queries public web services (UniProt, RCSB PDB, PDBe-KB, InterPro, ChEMBL, UniChem,
AlphaFold DB), so the numbers reflect the date it was run. The same flow runs offline, on frozen responses,
as an acceptance test (`tests/core/test_knowledge_baseline_offline.py`).
""")

code("""
from datetime import date

import pyunitwizard as puw

import sabueso
from sabueso.resolver import EntityQuery

print("Sabueso", sabueso.__version__, "| run on", date.today().isoformat())
""")

md("""
## 1. Resolution

`sabueso.resolve` takes an identifier or, as here, a name and an organism (NCBI taxonomy
id). It returns the card and the **resolution**, which says how the entity was chosen.
Nothing is chosen silently: when several entries match, the rule that decided is recorded
and the others are kept as alternatives.

The profile `structural_baseline@1` names the enrichments of a structural and chemical
baseline: all experimental structures, interface residues, ligand sites, family sites and
ChEMBL bioactivities. A profile is versioned and recorded on the card, so a card says
how it was built; options passed explicitly add to it or override it. Here the AlphaFold
DB models are added too (`predicted_structures=True`).
""")

code("""
cards, resolutions = {}, {}
for label, organism in (("TcTIM", 5693), ("HsTIM", 9606)):
    query = EntityQuery(name="triosephosphate isomerase", organism=organism)
    cards[label], resolutions[label] = sabueso.resolve(
        query, profile="structural_baseline@1", predicted_structures=True
    )

for label, resolution in resolutions.items():
    print(f"{label}: {resolution.status} -> {resolution.entity_ref}")
    print("   route:", resolution.decision["route"])
    print("   rules:", resolution.decision["rules"])
    print("   alternatives kept:", len(resolution.alternatives))
""")

code("""
for finding in resolutions["HsTIM"].decision["identity_audit"]:
    if "uniprot:P60174" in finding["refs"]:
        print(f"   {' vs '.join(finding['refs']):32} {finding['finding']:17} {finding['basis']}")
""")

md("""
Every source consulted leaves an outcome on the card, whether it answered or not:
""")

md("""
For HsTIM the name matched several UniProt entries; the reviewed entry was preferred by
the named rule `prefer_reviewed@1`, and the others remain listed as alternatives.

Which of those alternatives are the same protein entered again, and which are something
else? Rule `protein_identity_audit@1` compares them by gene locus and sequence, and never
merges anything: a shared gene with an agreeing sequence is flagged `possibly_same_as`,
fragments of the gene are `same_gene`, and distinct genes of one genome would be
`distinct_genes` however similar their sequences.
""")

code("""
from collections import Counter

tctim, hstim = cards["TcTIM"], cards["HsTIM"]
for label, card in cards.items():
    outcomes = Counter(
        (e["source"], e.get("data", ""), e["status"]) for e in card.quality["enrichments"]
    )
    print(label)
    for (source, data, status), n in sorted(outcomes.items()):
        print(f"   {source:9} {data:18} {status:9} x{n}")
""")

md("""
## 2. Who says what

A field holds its resolved value and the ids of the SourceAssertions that support it.
Each assertion records the source, the record, the value as the source stated it and the
retrieval date. Quantities are returned as quantities, with their unit.
""")

code("""
for label, card in cards.items():
    print(label, "|", card.get("names.canonical_name")["value"], "|",
          card.get("annotations.organism")["value"])
    print("   length:", card.get("sequence.length")["value"],
          "| mass:", puw.convert(card.quantity("sequence.molecular_weight"), to_unit="kDa"))
    print("   taxon:", card.get("annotations.taxon_id")["value"],
          "| lineage:", " > ".join(card.get("annotations.lineage")["value"][-3:]),
          "| gene loci:", len(card.get("identifiers.gene_loci")["value"]))

node = hstim.get("annotations.subunit")
print("\\nHsTIM subunit:", node["value"])
for sa_id in node["source_assertion_ids"]:
    assertion = hstim.source_assertion_store.get(sa_id)
    print("   stated by", assertion["source"]["name"], assertion["source"]["record_id"],
          "retrieved", assertion["retrieved_at"])
    print("   evidence (ECO):", assertion["source_metadata"]["eco"])
""")

md("""
## 3. What each card knows it does not know

`Card.knowledge_state()` tells apart, per area and source, what is known, what sources
disagree about, what a consulted source does not state, what was not queried, and what
could not be retrieved. An absence is a fact about a source at its release, never
evidence against anything.
""")

code("""
for label, card in cards.items():
    rows = card.knowledge_state()["rows"]
    print(label, dict(Counter(r["state"] for r in rows)))
    for r in rows:
        if r["state"] in ("not_stated", "not_queried", "unavailable", "conflicting"):
            print(f"   {r['state']:12} {r['area']:42} {r['source']:12} {r['release'] or ''}")
""")

md("""
## 4. Experimental structures and predicted models

A protein is one entity with many structures; no single PDB entry *is* the protein.
`Card.structures()` lists them with method, resolution and how much of the sequence each
one covers. Fragments and peptides are left out by default, and the exclusion is
reported.
""")

code("""
for label, card in cards.items():
    view = card.structures()
    print(f"{label}: {len(view['items'])} structures; fragments left out: {view['excluded']}")
    for item in view["items"][:5]:
        resolution = item["resolution"]
        print(f"   {item['structure_ref']:9} {item['method']:6} "
              f"{str(resolution) if resolution is not None else '-':>18} "
              f"{item['coverage_class']:12} {item['sources']}")
    print("   ...")
""")

md("""
Predicted models are kept apart: `Card.structures()` never counts them.
`Card.predicted_structures()` lists them with their version, confidence (mean pLDDT),
coverage, and whether the model is of the entry's current sequence. AlphaFold DB also
models isoforms; such a model names its isoform and says nothing about the entry's
coverage.
""")

code("""
for label, card in cards.items():
    for model in card.predicted_structures()["items"]:
        what = f"isoform {model['isoform']}" if model["isoform"] else (
            f"coverage {model['coverage']}, current sequence: {model['sequence_matches']}")
        print(f"{label}: {model['model_ref']:26} v{model['model_version']} "
              f"mean pLDDT {model['mean_plddt']:6} | {what}")
""")

md("""
## 5. Oligomer and interface

`Card.oligomer()` puts side by side what each source states about quaternary structure:
UniProt's subunit statement, the assemblies RCSB annotates for each structure, the
interface residues PDBe-KB derives from the structures (per partner chain), and the
dimer-interface site of the family model (CDD, through InterPro).

Each PDBe-KB "partner" is classified, structure by structure, so that a chimera or a
peptide complex is not mistaken for a complex of the protein.
""")

code("""
for label, card in cards.items():
    view = card.oligomer()
    print(label, "| UniProt subunit:", [s["text"] for s in view["subunit"]])
    states = Counter(a["oligomeric_state"] for e in view["assemblies"] for a in e["assemblies"])
    print("   RCSB assemblies:", dict(states))
    for interface in view["interfaces"]:
        print(f"   {interface['partner_ref']:38} {interface['class']:17} "
              f"{len(interface['positions']):3} residues")
    for row in view["agreement"]:
        print(f"   {row['signature']} {row['family_site']}: {len(row['both'])} positions also"
              f" observed, family only {row['family_only']}, observed only "
              f"{len(row['observed_only'])}")
""")

md("""
In TcTIM, PDBe-KB lists TbTIM (P04789) as a partner only because PDB entry 3Q37 is a
TcTIM/TbTIM chimera: one polymer entity mapped to both proteins. In HsTIM, the HLA-DR and
T-cell receptor chains come from complexes with a TIM peptide. Neither is a complex of
the enzyme, and the classes say so.
""")

md("""
## 6. Ligands and bioactivities

ChEMBL measurements are `has_bioactivity` relationships, one per measurement.
`Card.bioactivities()` derives an activity class for each from explicit thresholds (a
rule, recorded with the view), and leaves out measurements ChEMBL assigned to the target
by homology unless asked.
""")

code("""
for label, card in cards.items():
    view = card.bioactivities()
    print(label, "|", len(view["items"]), "molecules;",
          "classes:", dict(Counter(i["class"] for i in view["items"])),
          "| left out (not direct):", len(view["excluded"]))
print("rule:", view["classification"]["rule"], "| checks:", [c["rule"] for c in view["checks"]])
""")

md("""
A **ligand deck** turns the measured molecules and the ligands the structures were
determined to study into small-molecule cards, one per standard InChIKey. Comparing two
proteins' decks shows which molecules both share.
""")

code("""
decks = {label: sabueso.ligand_deck(card) for label, card in cards.items()}
for label, deck in decks.items():
    print(label, "|", len(deck.cards), "molecules |", deck.meta["sources"])

comparison = tctim.compare_ligands(decks["TcTIM"], hstim, decks["HsTIM"])
print("\\nshared by both:", len(comparison["shared"]))

# "label" is the molecule's name, else its ChEMBL id, else its PDB component code.
for item in comparison["shared"][:6]:
    mine, theirs = item["self"]["bioactivity"], item["other"]["bioactivity"]
    print(f"   {item['label']:30} TcTIM: {mine['class']:10} HsTIM: {theirs['class']}")
""")

md("""
## 7. Literature

`Card.literature()` gathers, per publication, the sources that cite it and what for (the
scope of a UniProt reference), the structures whose primary citation it is, and the
statements whose evidence names it. It does not read papers.
""")

code("""
for pub in tctim.literature()["publications"]:
    scope = [s for cited in pub["cited_by"] for s in cited["scope"]]
    print(pub["publication_ref"], pub["year"], "|", (pub["title"] or "")[:70])
    if scope:
        print("     cited by UniProt for:", scope)
    if pub["primary_citation_of"]:
        print("     primary citation of:", pub["primary_citation_of"])
""")

md("""
## 8. A claim read in a paper

Much knowledge exists only in papers. When a person (or, later, an agent) reads one, the
claim is recorded as a **curated literature assertion**: a SourceAssertion whose source is
the publication, with the curator, where in the paper it is stated, and optionally a short
quote. Sabueso checks its shape against the field, and compares it with what databases
state. It never gives it priority, and never discards anything.

The title of PubMed 18562316 relates the HsTIM deficiency mutation E104D (E105D in UniProt
numbering, which counts the initial methionine) to a conserved water network at the dimer
interface. UniProt describes the same variant differently:
""")

code("""
from sabueso.core.card import Card

hstim_as_built = Card.from_dict(hstim.to_dict())  # kept, to cite this state in section 10

variant = next(
    i for i in hstim.get("features_positional.natural_variant")["value"]
    if i["location"]["sequence"]["start"] == 105
)
print("UniProt:", variant["description"])

record = hstim.add_literature_assertion(
    "features_positional.natural_variant",
    {
        "start": 105,
        "substitution": {"original": "E", "alternatives": ["D"]},
        "description": "alters a conserved water network at the dimer interface",
    },
    publication="pubmed:18562316",
    curator="showcase",
    locator="Title",
)
print("\\noutcome:", record["outcome"])
""")

md("""
The outcome is `differs`: the same item (position 105, E to D) is stated differently.
Sabueso cannot tell whether two texts contradict each other, so it flags the difference
for a reader instead of judging it: it is recorded in `quality.conflicts`, a warning is
shown, and both statements stay on the card. A free-text field such as the subunit
statement is recorded but not compared:
""")

code("""
record = hstim.add_literature_assertion(
    "annotations.subunit", "Homodimer", publication="pubmed:8061610",
    curator="showcase", locator="Abstract",
)
print("outcome:", record["outcome"])

print("\\nconflicts:", [(c["field"], c["type"]) for c in hstim.quality["conflicts"]])
for pub in hstim.literature()["publications"]:
    for curated in pub["curated"]:
        print(pub["publication_ref"], "|", curated["field_path"], "|", curated["outcome"])
""")

md("""
How a claim bears on a project's hypotheses is not Sabueso's to record: that is
**Evidence**, and it belongs to Nextia. A SourceAssertion says what a source states.
""")

md("""
## 9. The two proteins side by side

`Card.compare_knowledge` says what two cards both state, what only one states, and what
they state differently. Positions are compared only through a residue mapping, because
the same number in two entries is not the same residue. In a workflow the mapping comes
from an alignment (MolSysMT); here it maps the four annotated catalytic and substrate
positions, which UniProt numbers 96 and 168 in TcTIM and 96 and 166 in HsTIM.
""")

code("""
diff = tctim.compare_knowledge(hstim, residue_map={12: 12, 14: 14, 96: 96, 168: 166})
for path in ("features_positional.active_site", "features_positional.binding_site",
             "annotations.function", "annotations.subunit"):
    print(f"{path:34}", {k: v for k, v in diff["fields"][path].items()
                          if k in ("status", "reason")},
          "| both:", len(diff["fields"][path].get("both", [])))
for predicate in ("classified_in", "annotated_with", "has_bioactivity"):
    r = diff["relationships"][predicate]
    print(f"{predicate:18} both {len(r['both']):3}  only TcTIM {len(r['only_self']):3}"
          f"  only HsTIM {len(r['only_other']):3}")
""")

md("""
## 10. Cite, store and read back exactly

A card's **snapshot id** is the content address of its exact state. A knowledge store
keeps every state it is given, and a pinned reference resolves to that state or fails;
it never returns another. Saving a changed card adds a revision, and earlier references
keep resolving. These reference forms are provisional until they are agreed across MOLI
(uibcdf/moli#3).
""")

code("""
import tempfile
from pathlib import Path

from sabueso.core.deck import Deck

with tempfile.TemporaryDirectory() as tmp:
    store = sabueso.KnowledgeStore(Path(tmp) / "baseline.db")
    before = store.save(hstim_as_built, note="as built")
    after = store.save(hstim, note="with the curated claims of section 8")
    print("before:", before[:70] + "...")
    print("after: ", after[:70] + "...")
    print("revisions:", [(h["revision"], h["note"]) for h in store.history(hstim.id)])
    old = store.load(before)
    print("curated claims in the pinned earlier state:", len(old.quality.get("curation", [])))

    store.save(tctim)
    shared = store.relationships(object_ref="interpro:IPR000652", predicate="classified_in")
    print("cards classified in the TIM domain:", sorted({r["card"].split("@")[0] for r in shared}))

    deck_ref = store.save_deck(Deck([tctim, hstim], meta={"purpose": "showcase"}), "tims")
    print("deck:", deck_ref[:60] + "...")
    print("cards of the pinned deck:", store.load_deck(deck_ref).ids())
""")

md("""
## What is not here

- Nothing is computed from coordinates: interfaces and contacts are what sources state.
  Geometry is modelling, and belongs to other components (uibcdf/sabueso#30).
- Free-text claims (uibcdf/sabueso#43) and biological context such as life-cycle stage
  or essentiality (uibcdf/sabueso#60) are not structured yet.
- Sabueso also records curated ranges and uncertainties of measurements, and the residues
  a paper says a compound acts on (`add_literature_bioactivity`,
  `add_literature_engagement`); this notebook does not invent a paper to show them.
- Sabueso records what sources state; how it bears on a study is Nextia Evidence.
""")

nb = nbformat.v4.new_notebook(cells=cells)
nb.metadata["kernelspec"] = {
    "name": "python3",
    "display_name": "Python 3",
    "language": "python",
}
if "--no-execute" not in sys.argv:
    NotebookClient(nb, timeout=900, kernel_name="python3").execute()
nbformat.write(nb, OUT)
print("written", OUT)
