# Knowledge packets

A knowledge packet answers a declared question in one call. It resolves the proteins,
composes what Sabueso's views say about the aspects asked, states what is not known,
and pins every card state it read, so that the answer can be cited and read back
exactly.

```{note}
Knowledge packets are a prototype, released in 0.6.0. Their shared contract with the
rest of MOLI is under discussion (uibcdf/moli#22), so their shape may change.
```

## A question and its answer

```python
import sabueso

query = sabueso.KnowledgeQuery("P60174", comparator="P52270")
packet = sabueso.knowledge_packet(query, store="knowledge.db", packet_name="tim_pair")

packet.ref  # 'sabueso:packet:tim_pair@sha256:…'
packet.facts.keys()  # the aspects asked
packet.unknowns["subject"]["rows"][:3]
```

A `KnowledgeQuery` is structured, not free text:

- `subject`: a UniProt accession; `comparator`: another one, optional;
- `aspects`: among `identity`, `structures`, `oligomer`, `ligand_sites`,
  `bioactivities`, `sequence_features`, `literature`, `disease_association`,
  `biological_context` and `orthology` (all but `orthology` by default: a protein has
  thousands of orthologs, so a query asks for them by name);
- `constraints`: for now `bioactivity_sources`, among ChEMBL (the default), BindingDB
  and PubChem BioAssay.

Anything else is refused, never ignored. What each aspect asks of the sources is fixed
by a named, versioned mapping, `packet_aspects@3`. It adds to `@2` the kinase and
GPCR classifications (`identity`), kinase conformations, GPCR states and antibody
complexes (`structures`), the kinase pocket (`ligand_sites`), GPCR segments and generic
residue numbers (`sequence_features`), and the `orthology` aspect (OMA). Packets of
different mappings are not compared (`same_knowledge` is `None`). Keyword arguments to
`knowledge_packet` only choose how the sources are reached (a `resolver`, or source
clients such as `chembl_client`); they never change what is asked.

An aspect asks every source that answers one of its knowledge areas, so a packet never
reports as not queried what its own aspects could have asked. What stays not queried
always says why: the source does not cover the organism (a human-only source for a
parasite protein), only curation states the area, or the query did not name the source
(`bioactivity_sources`). `sabueso.core.packets.aspect_options(aspect)` lists what an
aspect asks for.

## What a packet holds

- `entities`: the pinned state of each card it was composed from.
- `facts`: per aspect and per protein, the output of Sabueso's views, each with its
  named rule. With a comparator, some aspects also hold what the two say together: the
  identity audit, the structure inventory, and, for `orthology`, the relationships
  in which OMA states one protein an ortholog of the other.
- `conflicts`: where sources disagree, as the cards record it.
- `unknowns`: per source, what is `not_stated`, `not_queried`, `unavailable` or
  `partial`, for the areas of the aspects asked. An absence is a fact about a source,
  never evidence.
- `provenance`: the sources, their releases and retrieval dates, how their statements
  entered (`acquisition`: for example `database`, `database (text_mining)` or
  `curation`), and what each enrichment returned.

Quantities keep their unit, as `{value, unit}`.

A packet holds each statement once (`knowledge_packet@2`), and other places name it
instead of copying it:
- a grouped disease statement names what it groups, from the same aspect: an
  association by its `relationship_id` (`associations`), a UniProt disease by its
  `accession`, a ClinVar condition by its `variant` and `condition` index
  (`clinical_variants`). Beside the reference it keeps what the grouping adds:
  `grouped_by`, `narrower`, or the `reason` it was not grouped;
- the joint structure inventory names each protein's structure by its
  `relationship_id`, found in that protein's `structures` facts.

A fact names the SourceAssertions behind it. `packet.cite("subject", "SA_…")` gives its
pinned reference, which `store.source_assertion(ref)` reads back.

## Deterministic, with two ids

A packet never calls a language model, never ranks, and never summarizes: it holds the
aspects asked, as the views compute them. The same query and the same card states give
the same packet.

Sources change, though, and reading them again records new retrieval times. So a
packet has two ids:

- `packet.snapshot_id()`: the exact state, retrieval times included. This is what its
  pinned reference names.
- `packet.content_id()`: the knowledge alone, without retrieval times or the Sabueso
  version that built the cards. `packet.same_knowledge(other)` compares it.

`store.packet_history("tim_pair")` lists each saved revision with its format, its
`content_id` and `knowledge_changed`. So "has anything changed since the last time?"
has an answer. Packets saved by Sabueso 0.6.0 and 0.7.0 (`knowledge_packet@1`) are still
read. Two revisions of different formats are not compared: `knowledge_changed` and
`same_knowledge` are `None`, never a change that did not happen.

## Stored packets

- `store.save_packet(packet, name)` refuses a packet whose cards are not in the store.
  `knowledge_packet(..., store=…)` saves them first.
- `store.load_packet(name or ref)` verifies the packet and every card state it cites.
  A store changed outside Sabueso is refused.
- `store.packet_names()` lists the names.

To compose a packet from cards you already have, without resolving again, use
`sabueso.compose_packet(query, subject_card, comparator_card)`. The cards are used as
they are. An aspect whose sources they were not built with shows as `not_queried`.
