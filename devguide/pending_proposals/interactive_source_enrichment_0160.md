---
summary: Explicit one-source protein enrichment, observed access and original capture continuity.
issue: uibcdf/sabueso#154
status: open
opened: 2026-11-13
verification: implementation_checkpoint
area: [human-exploration, source-access, persistence, standalone]
---

# Explicit protein source scope

The [living plan](interactive_implementation_0160.md) owns S4 completion.
The entry form keeps `identity@1` as its default. For a UniProt accession, the
researcher can additionally request either InterPro's source-mapped family sites
or AlphaFold DB's predicted-model records. These reuse the registered native
`family_sites=True` and `predicted_structures=True` options. No new source,
scientific profile, mapping or dependency is introduced.

The application admits only these finite option names, on the protein route.
It does not accept arbitrary resolver arguments, automatically request all
structures, iterate over other proteins, queue source work or expand to ChEMBL.
Each added route uses its existing per-protein endpoint and provider timeout;
this bounds the operation selection, not the response size, HTTP retries or RAM.
Current process/resource receiving remains distinct from a production quota.

The query creates a new capture. It does not modify or merge the previous Card,
Deck member or original saved reading. Earlier supplied context is not silently
carried into the fresh Card. Return to previous query restores that exact prior
reading and source report; whole-workspace saving preserves both originals.
A candidate button keeps its existing identity-only scope even when the source
selector retains another value. Source choices remain explicit actions.

InterPro positions retain their source numbering and support; they establish no
local sequence alignment or molecular mapping. AlphaFold records remain predictions,
separate from experimental structures. Selecting them does not download coordinate
files, create a conformer or load a model into MolSysViewer. Their existing native
prediction reader retains context, confidence, reference and absence limits.

## Access and outcomes

A bounded current presentation shows the first 16 original acquisition observations:
source, operation, outcome, access route and stated version/basis. The complete
original resolution/acquisition report stays available. These observations describe
access, not scientific coverage, SourceAssertions or Evidence. The native Card's
coverage and quality readers retain enrichment outcomes and exact request options.
A failure of the additional source can leave identity resolved while recording an
`error` enrichment and a `failed` access observation. It never becomes an empty
scientific result or a claim of absence. Fixture access stays labelled `fixture`.

The selector is a current request; it is not replayed from a saved report. Pending
jobs expose their chosen scope, but remain excluded from saving. Access previews
are ephemeral response fields, recomputed from retained original acquisition
records; they do not rewrite the query report, native Card formats or workspace
wire. Prior originals remain inert, with no query or current Card construction.

Broader source controls, qualified 2D/3D correspondence, richer disease journeys,
workload agreements and human acceptance remain open. This increment does not
close S4 or authorize a version/candidate/public release.


## Bounded product resource observations

The same installed runtime receives two sequential molecular profiles: public
1TCD BinaryCIF and the declared public AlphaFold Q8WZ42 fragment mmCIF. The second
input is deliberately unrelated to the P52270 reading; correspondence remains
unestablished. Each profile receives 14 checks, twelve float/reset cycles on one
live iframe, ten seconds idle before interaction and ten seconds after it. Camera,
empty selection, original reading and input files survive; shutdown leaves no
owned descendants.

With two CPU cores, a 4 GiB summed-RSS ceiling and 16 GiB host reserve, observed
peaks are about 1.76/1.86 GiB. Sampled mean CPU usage is about 0.09/0.10 cores
before interaction, 1.27/1.43 during rotation/layout cycles and 0.21/0.21 in the
short following idle window. These are Linux/Xvfb/ANGLE llvmpipe software-renderer
observations of all sampled owned processes, including ordinary polling, not GPU
or thermal measurements, unique physical RAM or an agreed budget. Short settling
windows and retained allocations do not demonstrate or exclude a memory leak.

This extends S5.5/S6.2 with varied input and idle/active observations. It does not
receive repeated provider construction/disposal, long sessions, nonempty mapped
selection, native driver/platform support or a stable embedding contract. Keep
those remaining checks and workload agreement open under #154/#368.
