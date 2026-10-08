# Reading precomputed variant predictions

Development AlphaMissense access reads the source's precomputed amino-acid
substitution predictions. It validates a full canonical human descriptor from
AlphaFold DB, follows its exact `amAnnotationsUrl`, and checks every CSV row
against that descriptor's sequence before applying a result limit.

```python
from sabueso.tools.db.alphamissense import get_annotations
from sabueso.mappings.alphamissense import map_variants

envelope = get_annotations("P60174", limit=10000)
artifact = envelope["record"]["artifact"]
if artifact is not None:
    print(artifact["total"], envelope["truncated"], artifact["coverage"])
    assertions = map_variants(envelope)
    for assertion in assertions[:3]:
        print(assertion["asserted_value"])
```

The public HsTIM artifact contains 4731 substitutions: 19 alternatives at each of
249 positions. `total` is the count of validated CSV rows, not a native total
header. `coverage` uses the named `single_aa_substitution_coverage@1` rule to
compare unique rows with the possible substitution grid. Gaps in that grid do
not establish biological absence. Separately, `truncated` reports whether the
requested positive `limit` capped returned rows. The full native CSV and its
original SHA-256 remain in the envelope, including when rows are capped.

Every assertion retains the literal native variant, score and classification.
Scores stay between zero and one; zero remains a value, while empty/`NA` scores
remain missing. Native `LBen`, `LPath` and `Amb` labels are preserved. Future
labels remain explicit and unrecognized; Sabueso does not recompute classes from
thresholds or turn them into clinical observations. The assertion's
`knowledge_class` is `predicted`.
Recognition of native class codes is recorded separately in
`source_metadata.class_validation`, under
`native_alphamissense_class_vocabulary@1`; it is Sabueso validation metadata.

Coordinates refer to the explicit source axis `AlphaMissense:AF-P60174-F1`, with
the full host discovery sequence and its hash. Reference amino acids, positions,
alternative amino acids and duplicate variants are checked. A shared accession
or matching string does not automatically place these assertions on a current
UniProt card or an isoform. Fragmented, ambiguous, unrelated or unsupported
descriptors are refused. Noncanonical isoform and genome-build artifacts are not
queried by this API.

`version` remains unknown because the score artifact does not state its revision.
The host's AlphaFold model version and sequence dates are retained as metadata;
they do not become an AlphaMissense score version. The original CSV hash identifies
the exact artifact used. No new model inference, card enrichment or card-schema
change occurs; these are independent SourceAssertions for explicit consumers.

When the host does not declare a canonical artifact, `availability` is
`not_stated`, no CSV is downloaded and no AlphaMissense access credit is created.
A declared artifact that fails to download is a connector failure. Missing local
fixtures are unavailable; a header-only CSV is an explicitly empty artifact.
Discovery and score access have separate acquisition records. Built-in clients
support shared-transport `RetrievalArchive` recording/replay with original times.

For offline development in this checkout:

```python
from sabueso.tools.db.alphamissense import FixtureAlphaMissenseClient

envelope = get_annotations("P60174", client=FixtureAlphaMissenseClient(), limit=20)
assertions = map_variants(envelope)
```

The native fixtures are declared in `temp_data/NOTICE.md`. Prediction data is
CC BY 4.0; the model code's separate licence does not apply to these data. Credit
DeepMind and [Cheng et al., Science (2023)](https://www.science.org/doi/10.1126/science.adg7492),
as the [official AlphaMissense resource](https://github.com/google-deepmind/alphamissense#alphamissense-predictions-license)
requests.
