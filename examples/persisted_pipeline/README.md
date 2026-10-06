# Persisted public knowledge pipeline

This example was delivered and qualified with Sabueso 0.13.0. It uses explicit
article metadata and literal-extraction APIs unavailable in 0.12.0. The smaller
[Ackredit pilot](../ackredit_pilot/README.md) also works with 0.12.0.

Each command starts a separate Python process. From the repository root:

```bash
python examples/persisted_pipeline/run.py produce --output /tmp/sabueso-pipeline --fixtures temp_data
python examples/persisted_pipeline/run.py read --output /tmp/sabueso-pipeline
python examples/persisted_pipeline/run.py reuse --output /tmp/sabueso-pipeline --fixtures temp_data
python examples/persisted_pipeline/run.py read --output /tmp/sabueso-pipeline
```

The producer requires an empty output directory. Reuse refuses to replace an
existing reuse stage. Ackredit >=0.9.0 is required; installed receiving gates use
its public 0.9.0 build and exercise these commands outside both library checkouts.

## What the application retains

The pipeline resolves public HsTIM (P60174) and RCSB 1HTI/1KLG fixture knowledge,
queries explicit Europe PMC metadata for PMID 40832834, and binds it to a **synthetic
fragment** containing `UniProt:P60174`. This fragment is an application test input,
not article text or a scientific finding about HsTIM. Article metadata does not
authenticate its content. Frozen public responses are declared in `temp_data/NOTICE.md`.
No abstract, full text or private pilot content is used; network access is forbidden.

`knowledge.db` retains exact card revisions and two packets (`full` and `index`).
`extractions.jsonl` keeps the original occurrence and article support, original
metadata acquisition receipt, extraction attribution and unknown fragment terms.
For each stage, the application writes:

- a manifest with exact card/packet/item references and sidecar SHA-256 values;
- detached per-packet attribution;
- observed acquisition and literature-operation records, including original
  versions, query/response identities, timestamps, contextual credit and gaps;
- the enclosing workflow's original portable attribution;
- derived reader explanations, terms and CSL-JSON/BibTeX reference exports.

A deliberately missing fixture produces `unavailable` with no network attempts
or completed-data credit. This does not establish that the publication is absent
from Europe PMC. Its operation record survives even though the application continues.

## Reading and reuse

The reader needs no source fixtures. It validates required files, hashes, packet
and card bindings, exact item support and workflow bibliography/contextual-use
closure before exporting references. An index item is read through `packet.item`
at its original pin. Saved payloads acquire no runtime attribution; rendering the
saved portable records registers nothing and adds no execution credit.

Reuse reacquires public UniProt/RCSB fixture knowledge at a later fixture-read time
and advances the card and both unpinned packet heads. This is fixture access, not
a new public download. It applies the original ExtractionStore result without a
new article query or extraction. Reused credit retains original use context;
current execution credit remains separate. Both historical and new index/item
pins and original publication authors/pages/citations still resolve. Article
licence literals remain separate from the fragment's unknown reuse rights.

The manifest belongs only to this application example. Its hashes detect missing,
changed or misbound files; they do not authenticate a publisher or authorize
content reuse. The mutable database is verified through its immutable content
addresses rather than a whole-file digest. Keep the complete bundle; a payload
alone cannot reconstruct the original execution. An interrupted write can leave
an incomplete bundle, which the reader refuses. Automatic journaling, transactional
multi-file delivery and ProjectRecord/Recorda routing remain MOLI #36/#18 work.
No Nextia Evidence or shared MOLI record contract is created here.

Regression tests start genuinely independent processes, forbid reader credit and
source calls, simulate a different reader version and refuse missing, modified
or misbound files. CI repeats them against installed Sabueso/public Ackredit.
