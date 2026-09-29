# Knowledge packets

A knowledge packet answers a declared question in one call. It resolves the proteins,
composes what Sabueso's views say about the aspects asked, states what is not known,
and pins every card state it read, so that the answer can be cited and read back
exactly.

```{note}
Knowledge packets are a prototype on main, not yet in a release. Their shared contract
with the rest of MOLI is under discussion (uibcdf/moli#22), so their shape may change.
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
  `bioactivities`, `sequence_features`, `literature`, `disease_association` and
  `biological_context` (all by default);
- `constraints`: for now `bioactivity_sources`, among ChEMBL (the default), BindingDB
  and PubChem BioAssay.

Anything else is refused, never ignored. What each aspect asks of the sources is fixed
by a named, versioned mapping, `packet_aspects@1`. Keyword arguments to
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
  identity audit, and the structure inventory.
- `conflicts`: where sources disagree, as the cards record it.
- `unknowns`: per source, what is `not_stated`, `not_queried`, `unavailable` or
  `partial`, for the areas of the aspects asked. An absence is a fact about a source,
  never evidence.
- `provenance`: the sources, their releases and retrieval dates, and what each
  enrichment returned.

Quantities keep their unit, as `{value, unit}`.

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

`store.packet_history("tim_pair")` lists each saved revision with its `content_id` and
`knowledge_changed`. So "has anything changed since the last time?" has an answer.

## Stored packets

- `store.save_packet(packet, name)` refuses a packet whose cards are not in the store.
  `knowledge_packet(..., store=…)` saves them first.
- `store.load_packet(name or ref)` verifies the packet and every card state it cites.
  A store changed outside Sabueso is refused.
- `store.packet_names()` lists the names.

To compose a packet from cards you already have, without resolving again, use
`sabueso.compose_packet(query, subject_card, comparator_card)`. The cards are used as
they are. An aspect whose sources they were not built with shows as `not_queried`.
