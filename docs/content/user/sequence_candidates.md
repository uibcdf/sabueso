# Finding protein candidates from a sequence

This development API accepts one raw protein sequence or one FASTA record and
returns current UniProtKB candidates. It compares the full UniParc sequence and
the full current UniProt canonical sequence with your input. Equal sequences can
belong to different entries; every matching entry remains a separate candidate.

```python
from pathlib import Path
from sabueso.tools.sequence import find_protein_candidates

report = find_protein_candidates(
    Path("protein.fasta").read_text(),
    taxon_id=9606,  # optional exact NCBI taxonomy id
    limit=100,
)

print(report["status"], report["candidate_status"])
for candidate in report["candidates"]:
    print(candidate["accession"], candidate["organism"])
```

Whitespace and case are normalized, and one terminal `*` may be removed. The
original input hash, FASTA header and normalization rule remain in the report.
Headers do not supply organism identity. Multiple FASTA records, gaps, internal
stops and characters outside `ACDEFGHIKLMNPQRSTVWYBXZJUO` are refused before
source access. `taxon_id` filters exact taxonomy ids; names and descendants are
not inferred.

`candidate_status` is `multiple`, `one` or `none_in_checked_scope`. Separately,
`status` is `complete`, `partial` or `failed`. A single candidate in a partial
report does not establish uniqueness. A complete report covers the returned
canonical reference list under these rules, not every possible biological identity.

The same positive `limit` caps archive search rows and current canonical entry
checks separately. Native reference order is kept; unchecked entries appear as
`not_queried`. Missing continuation pages, inconsistent responses and per-entry
failures remain visible, while successfully checked candidates are retained.
Missing fixtures are unavailable; a failed search is not an empty answer.

Native references such as `P60174.2` retain their declared historical revision.
Their base accession is checked against its current canonical record; old
sequence revisions are not fetched. Isoform references such as `P60174-1` are
retained with `isoform_sequence_not_queried`, without stripping their isoform id.
For a known explicit isoform ID, use the separate native sequence helper in
{doc}`source_annotations`. It retains parent declarations and selected FASTA;
the candidate tool still makes its canonical checks and keeps isoform exclusions.
Redirected responses with another primary accession fail the identity check and
remain explicit; this tool does not follow aliases or infer identity equivalence.

The report includes original search pages, current verification records, separate
source assertions, their complete snapshot hashes and acquisition records under
`exact_sequence_candidates@1`. MD5 is only the archive search key; it is not an
identity proof or a security seal. No candidate is chosen and no card is created.
After reviewing the candidates, you can explicitly resolve a chosen accession
with `sabueso.resolve("P60174")`.

For development without network access, use the public fixtures:

```python
from sabueso.tools.db.uniparc import FixtureUniParcClient
from sabueso.tools.db.uniprot import FixtureUniProtClient

report = find_protein_candidates(
    sequence_text,
    uniparc_client=FixtureUniParcClient("temp_data"),
    uniprot_client=FixtureUniProtClient("temp_data"),
)
```

The HsTIM archive fixture returns historical, canonical and isoform references.
The current fixture checks retain three distinct matches; three other canonical
entries have no local fixture, so the report is partial. Built-in online clients
also support `RetrievalArchive` recording and replay through the shared transport.
UniParc database terms are CC BY 4.0; referenced databases and publications retain
their own rights and are not acquired by this search.
