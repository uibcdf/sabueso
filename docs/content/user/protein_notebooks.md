# Notebook reports and residue annotations

These APIs, delivered in 0.14.0, recover an earlier prototype using the
current SourceAssertion model.

## Render stored knowledge

```python
from sabueso.core.card import Card

card = Card.from_json("protein.card.json")
path = card.to_notebook("reports", include_card_snapshot=True)
```

Defaults are English, `mode="full"` and `path="."`. A directory keeps a filename
derived from the canonical name; an `.ipynb` path specifies the complete filename.
Relative paths use an explicit notebook frontend path, the calling Python script's
directory, or the working directory. No Jupyter server lookup or network refresh
occurs. Existing output files at the chosen path are replaced.

`mode="minimal"` summarizes fields and relationships. `language="es"` translates
section headings. `include_code=False` omits executable cells. Full reports retain
stored values, units, relationships, conflicts, alternatives and SourceAssertion
ids. Missing support remains explicit.

The optional adjacent `.card.json` is the exact sealed snapshot; the loading cell
checks its snapshot id, then writes `<report_stem>_regenerated.ipynb` and its
adjacent sealed card with the original title, mode and language. Run this optional
cell with the notebook and `.card.json` in the working directory; the pair can
be moved together. The regenerated files stay beside the saved card, and the
original pair is untouched. A different snapshot is refused before regeneration.
Opening or rendering the notebook executes nothing; running the cell explicitly
performs only local load/render/write operations.

Rendering neither creates new acquisition credit nor
embeds original runtime sidecars. Retain acquisition/attribution JSON separately.

## Read canonical residues

```python
residue = card.get_residue(164)
print(residue["amino_acid"], residue["annotations"])
all_residues = card.get_residues()
```

`residue_annotations@1` uses the stored canonical sequence, 1-based positions and
annotations explicitly attached to that sequence. Each item cites its actual
supporting SourceAssertions with a matching field, value and protein subject.
Unknown placement, missing support and incompatible subjects remain visible.
Disulfide bonds affect endpoints.

These methods do not align, infer isoform sequences, calculate properties or
project onto PDB/MolSysMT numbering. Missing sequences and invalid positions are
refused.

## Summarize a selected residue set

```python
composition = card.residue_composition([1, 2, 164, 164])
print(composition["total"])  # 3 unique positions
print(composition["counts"], composition["fractions"])
print(composition["selection"]["duplicate_occurrences"])
# [{"input_index": 3, "position": 164}]
```

`residue_set_composition@1` reads one identified sequence axis. Each positive 1-based
position counts once, and the result preserves the original selection, duplicate
occurrences, exact card pin and full supporting sequence assertion snapshots.
Types come from sequence characters, so mixed one-/three-letter row labels do not
alter the counts. B/J/X/Z stay unresolved; U/O remain concrete sequence symbols.
The denominator includes **all unique selected positions**, including unresolved
types. Concrete fractions plus `unresolved_fraction` cover that denominator;
an empty selection has total zero and `unresolved_fraction=None`.

Missing or malformed sequences, invalid positions and out-of-axis positions are
refused. Missing canonical source support remains explicit as incomplete support;
it is not invented to justify the calculation. Reading the view creates no
SourceAssertions, card fields, acquisitions or new attribution.

An explicit source axis can use the original subject-bound sequence declarations
already supported by `residue_knowledge`:

```python
composition = card.residue_composition(
    [1, 2, 164],
    sequence_ref="MobiDB:P60174",
    source_assertions=original_mobidb_assertions,
)
```

Here `original_mobidb_assertions` are native `map_disorder_regions` results for
the same card subject, as shown in {doc}`source_annotations`. Different sequence
content under one selected reference is refused. Invalid matching declarations
remain excluded with their original snapshots; independent revisions are retained.
Canonical selection uses stored sequence support and reports supplied declarations
as unused.

The position set is supplied by the caller. This API does not establish that those
positions line a cavity or form a binding site. A structural lining-residue set
requires its original membership declaration and an exact mapping before use on a
sequence axis. Chain/author/insertion numbering is not converted automatically,
and equal residue numbers on different chains or sequences do not identify one
residue. Geometry, pocket detection and remote jobs remain separate operations.

## Query AAindex explicitly

```python
from sabueso.tools.db import aaindex
from sabueso.mappings.aaindex import map_index

answer = aaindex.get_index("KYTJ820101")  # explicit online access
print(answer["record"]["values"])
reference_assertions = map_index(answer)
```

The supplied-file client reads `<directory>/aaindex/aaindex1` with the same parser:

```python
client = aaindex.FixtureAAindexClient("my-source-snapshots")
answer = aaindex.get_index("KYTJ820101", client=client)
```

AAindex references amino-acid types independently of protein positions. Values
retain their scale, native numeric literal, publication pointers and `NA` markers.
Unstated units/releases remain unknown. The
[source format documentation](https://www.genome.jp/aaindex/aaindex_help.html)
defines the paired row order. No automatic protein enrichment or local prediction
is performed. Reuse terms are explicitly unknown in the registry; public access
does not establish redistribution permission.

## Read richer residue knowledge

`Card.residue_knowledge` reads original SourceAssertions supplied explicitly or
already present in the card's assertion store. It returns a detached
`residue_knowledge@1` view. The existing `get_residue`/`get_residues` results keep
their `residue_annotations@1` rule and shape.

```python
import json

with open("source-assertions.json", encoding="utf-8") as handle:
    original_assertions = json.load(handle)

knowledge = card.residue_knowledge(164, source_assertions=original_assertions)
print(knowledge["amino_acid_type_properties"])
print(knowledge["residue_tracks"])
print(knowledge["missing_values"], knowledge["unmapped"])
```

AAindex `map_index` results can be supplied directly. Their native literals and
`NA` values remain type references, independently of observations at a position.
Other `amino_acid.properties.<name>` and `amino_acid.statistics.<name>` assertions
require a matching `amino_acid:<letter>` subject and value with `amino_acid` and
`value`. Statistics retain their original population and context; they never become
positional probabilities. AAindex missing values carry `value_status="not_stated"`.

Positional track assertions use `sequence.residue_tracks.<name>`. Their value
requires `sequence_id`, `indexing="1-based"`, an explicit `metric` and either
`values` (one sample per source residue) or `observations` (unique explicit
`position`/`value` rows). Provider state definitions and native sample context
are retained independently. Numeric zero remains a value; `None` and unstated
sparse samples appear in `missing_values`. Probability samples must be in [0, 1].
Other measurements can retain `{value, unit}` records without unit conversion.
Duplicate positions, invalid sample shapes and wrong lengths remain unplaced.

Positional input must also declare `source_metadata.sequence` with `id`, full
native `value` and `uniprot_ref`; an optional `sha256` is verified. Both the assertion
subject and sequence association must match the card's UniProt subject. Canonical
placement requires exactly matching sequence identity and content. The view does
not infer coordinate equivalence from identical sequence strings.

Every returned input item retains its complete original SourceAssertion and
`support.snapshot_id`, including source revision, retrieval and metadata. Different
revisions sharing an assertion id remain distinct. Stored canonical annotations
retain their existing item support and card pin in `stored_annotations`. Supplied
assertions are not inserted into the card or its store; save them and runtime
acquisition sidecars separately if they must be reused. Caller declarations do not
establish remote access, scientific validation or permission.

## Read a supplied source snapshot

```python
from sabueso.tools.source_snapshot import load_source_snapshot

answer = load_source_snapshot(
    "my-records.jsonl.gz",
    source_metadata={
        "source": "MySource",
        "kind": "records",
        "query": {"accession": "P37840"},
        "retrieved_at": None,
        "version": None,
        "terms": {"licence": "not stated"},
    },
    records_key="data",
)
print(answer["snapshot_receipt"]["document_sha256"])
```

Supported formats are JSON, JSONL/NDJSON, CSV and TSV, optionally gzip-compressed.
`file_format` overrides suffix inference. `expected_sha256` verifies the exact
original file bytes before decompression. CSV/TSV cells remain strings, including
empty strings and literal zero. `records_key` wraps a list of rows; it cannot
rewrite a native JSON object. Malformed data is refused.

The receipt records local reading separately from declared source retrieval.
Unknown original times and versions remain unknown. Source/query/terms metadata
comes from the caller and does not prove remote access or permission. Loading
does not add acquisition credit or populate a card. A source client must validate
native shape, identity and coordinate scope before mapping scientific assertions.

## Query DisProt explicitly

```python
from sabueso.tools.db import disprot
from sabueso.mappings.disprot import map_disorder_regions

answer = disprot.get_records("P37840")  # explicit online accession query
assertions = map_disorder_regions(answer)
print(answer["truncated"])
```

Use `FixtureDisProtClient("temp_data")` for repository offline tests. To consume
your own native search snapshot, bind it to the original query explicitly:

```python
client = disprot.SnapshotDisProtClient(
    "disprot-search.json",
    source_metadata={
        "source": "DisProt",
        "kind": "records",
        "query": {"accession": "P37840"},
        "retrieved_at": None,  # supply the original time only if known
    },
)
answer = disprot.get_records("P37840", client=client)
assertions = map_disorder_regions(answer)
```

The mapper selects only native structural-state `IDPO:0000002` (disordered).
Coordinates retain the DisProt sequence id, full source sequence and hash;
matching UniProt accession alone does not establish coordinate equivalence.
Other ontology terms remain in the raw record. Native region revisions and
publication pointers survive; global release and unfetched bibliography remain
unknown. The API's default response can be a subset: the frozen P37840 response
returns 22 regions while declaring 40, which remains explicit.

This API supplies independent SourceAssertions. Automatic card enrichment and
placement on current UniProt/isoform sequences remain unimplemented. The
[DisProt resource](https://disprot.org/) states CC BY 4.0 database terms; linked
article text retains its own rights. No linked articles are fetched by this query.

Read the original DisProt sequence explicitly using a card for the same subject:

```python
synuclein_card = Card.from_json("P37840.card.json")
native_assertions = map_disorder_regions(answer)
knowledge = synuclein_card.residue_knowledge(
    10,
    sequence_ref="DisProt:DP00070",
    source_assertions=native_assertions,
)
print(knowledge["source_annotations"])
```

This selects positions on the source sequence. It does not attach them to current
UniProt numbering, even if the strings happen to match. Native returned/stated
region counts remain in the original assertion metadata. Explicit isoform sequences
can be selected the same way when the supplied original assertions actually declare
them; no sequence is reconstructed from an isoform description. Missing or
contradictory selected sequences are refused. Empty result lists describe the inputs
read at that position and do not prove absence in an external database. No network
query, prediction, card mutation or new attribution occurs during this view.
