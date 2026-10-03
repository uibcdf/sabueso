# Sabueso 0.12.0 — Literature context and automatic traceability

Draft for the staged candidate; this version has not been published. Publication
requires the verified public Ackredit dependency and the exact installed-package
gates in `release_plan.toml` and `README.md`.

## Located literature context

- Explicit Europe PMC article intake keeps every UniProt accession occurrence,
  native article identifier, location and supporting SourceAssertion. Request it
  with `europepmc={"article_ids": "PMC:PMC12400196"}`. Automatic packet intake
  continues to request bibliography, without guessing articles.
- PDB accession mentions add structural context only through source-supported
  protein–structure associations already on the card. `structure_mention_context@1`
  keeps both occurrence and association support. Unlinked mentions, alternatives,
  unknown coverage and failures remain visible; mentions never establish a
  scientific claim or whole-entry identity.
- `Card.explain_literature(publication_ref)` exposes exact stored links and support,
  including structural context, alternatives and unlinked requests, without new access.
- Literature packets at `packet_aspects@6` include both mention areas, their index
  references and coverage. Historical mappings remain readable; comparisons across
  incompatible mappings/detail levels report non-comparability.
- Refresh preserves explicit article requests and the recorded terms profile unless
  overridden. Missing fixtures, empty answers and failed requests remain distinct.

## Pinned terms and attribution

- `KnowledgePacket.terms(use, store)` reports obligations and unknowns for represented
  support at exact saved card pins. Full/index packets at `packet_aspects@6` share
  support scope. Terms use the packaged registry and its review dates, without
  reconstructing a historical registry.
- Ackredit becomes a required runtime dependency. Every completed composition
  automatically receives `packet.attribution`, preserving original producer/source
  versions, selected support, conflicts, reused resources and bibliography gaps.
  Results contribute to the application's Ackredit captures/session.
- Bibliography does not license fragments. Unstated article licences remain unknown;
  raw annotation responses also have unknown retention/sharing rights under
  `PUBLICATION-TERMS`.

## Source-acquisition traceability

- Traceability is required. This release's acquisition coverage is the built-in
  UniProt entry/search and Europe PMC mentions/annotation clients. Other sources
  and custom clients are explicitly unobserved.
- Operations preserve query, original versions with distinct entry/service/release
  bases, retrieval times, decoded/raw response identities, archive references and
  fixture/network/reuse/replay routes. Replay claims no new download. Empty answers,
  HTTP absence, unavailable fixtures, unqueried requests, retries, failures and
  partial batches remain distinguishable.
- Cards, resolutions including no-card failures, final refresh states, one-call
  packets and covered public source envelopes retain `acquisition_trace` automatically.
  `sabueso.attribution()` optionally collects source events in `run.acquisitions`,
  separately from completed packet `run.records`.
- Completed access contributes contextual uses and bibliography. Failed/unqueried
  access remains a host record without completed-access credit. Provider/recording
  failures diagnose gaps and preserve scientific results/exceptions.
- Save original JSON beside scientific objects. Saved readers preserve original
  records without new credit; payload-only card/packet loads have no runtime trace
  or attribution. Persistence is explicit.

## Compatibility and limits

- Python 3.11–3.14. The candidate writes card schema **0.3.11**, adding optional
  article/location qualifiers. Published schemas remain readable. Knowledge-store
  and query/packet payload formats are unchanged.
- Runtime attribution/traces remain separate from scientific serialization/hashes.
  Covered source envelopes add `acquisition_trace` beside unchanged raw records;
  client return protocols stay intact.
- Verified UniProt/Europe PMC description citations are declared. Other descriptions
  and target article/annotation-provider bibliography remain explicit gaps. Terms,
  source support and Nextia Evidence retain separate meanings.
- Local trace formats are provisional. MOLI ProjectRecord/Recorda routing,
  correlation and durable recording policy remain coordinated future work.
- `examples/ackredit_pilot/` saves source traces, two result bibliographies and the
  workflow union, then reads original records without new credit. It uses public HsTIM data.

Tracking: Sabueso #110 (release), #108 (coverage/attribution), #92 (literature),
#91 (explanations), #29 (terms); MOLI #36 (shared boundary).
