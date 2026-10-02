# What may be done with the knowledge

Every value and relationship on a card traces to the SourceAssertions that state it, and
each SourceAssertion names its source. Sabueso can therefore say, for a use you name,
what each source states about its own terms, and what knowledge remains if you keep
only the sources that allow that use.

```{note}
Card/deck reports were released in 0.7.0; packet reports below are unreleased. This is a report of what the sources state, not
legal advice: the decision, and the responsibility for it, stay with you.
```

```python
report = card.terms("commercial_product")
report["sources"]["ChEMBL"]  # licence, verdict, obligations, attribution, statement
report["obligations"]  # e.g. ["attribution", "share_alike"]
report["attribution"]  # the attribution texts to carry
report["unknown"]  # sources whose terms Sabueso cannot answer for
card_report = report["cards"][0]
card_report["objects"]  # per related entity (a measured molecule…): complete,
# partial, unknown or none
deck.admissible("commercial_product")  # only cards whose knowledge all remains
```

## Uses

`internal_research`, `academic_publication`, `redistribution`, `derived_dataset` and
`commercial_product`. The use is yours to name. Sabueso does not guess it.

## Verdicts

- **allowed**, with obligations:
  - `attribution` (CC BY, CC BY-SA);
  - `credit_requested` (NLM's public-domain data);
  - `share_alike` (CC BY-SA), when the data leaves your hands: redistribution, a
    derived dataset, a product. It does not bind a publication that cites.
- **restricted**, with the reason, e.g. a non-commercial licence for a commercial
  product.
- **unknown**, with the reason: no terms recorded, or terms that depend on each record
  and are not recorded for this one. A curated statement keeps its publication's terms.
  Unknown is never "no restriction".

**Terms per record.** A PubChem BioAssay result keeps the terms of whoever deposited
the assay. An assay deposited by ChEMBL or BindingDB is a copy of their records, so it
is judged by their terms, and the report says so: `PubChem BioAssay (deposited by
ChEMBL)`, with its `basis`. An assay of any other depositor stays `unknown`, with the
reason `depositor_terms_not_recorded`.

A piece of knowledge **remains** for a use when at least one source that states it is
allowed. For human and *T. cruzi* triosephosphate isomerase, everything remains for a
commercial product, with attribution and share-alike (ChEMBL, BindingDB, and PubChem
BioAssay results deposited by ChEMBL).

Each source's terms, with the statement they come from and the date they were reviewed,
are listed on the *Data sources* page. A record older than a year is flagged
`review_due`.

## Terms of a packet (unreleased)

```python
report = packet.terms("redistribution", store)
report["sources"]  # stated terms, review dates and attribution
report["scope"]["subject"]  # exact card pin and each represented support item
report["unknown"]  # includes article fragments whose publication terms are unstated
```

`packet_terms@1` reads exact card pins from the knowledge store. It reports the
SourceAssertions represented by the asked views, their conflicts and stored
relationship dependencies, rather than every source on the entire card. Full and
index packets share this support scope. Counts are statements and relationships,
not unique scientific facts. Both legs of a derived structural mention must remain
for the derived relationship to remain; source alternatives within a leg are
judged separately. Allowed bibliography never licenses attached text fragments.

This operation currently supports `packet_aspects@6`. Older packets remain readable,
but their terms query raises `StorageError` until a historical scope adapter exists.
Missing cards or support are also refused; current heads never replace historical
pins. Index view rules must be recognized before views are reconstructed.

The report uses the current packaged terms registry with its review dates. It does
not reconstruct the terms registry as of the card's acquisition. Exact mapping and
qualifier lineage was not always recorded; disease grouping includes the stored
MONDO/MedGen identity/hierarchy context rather than claiming minimal inputs. These
limits are stated in the report. It is detached, changes no packet hashes or payload,
and does not record runtime usage or produce a pipeline bibliography.

## Building under a terms profile

A project can also build its knowledge only from sources whose terms allow its use:

```python
card, _ = sabueso.resolve(
    "P52270", chembl={}, pubchem_bioassay=True, terms="commercial"
)
card.quality["terms_profile"]  # the profile, and the sources it excluded, with why
```

- `terms="commercial"`: for a project that may end in commercial exploitation. Choose
  it from the first day: knowledge that informed a decision cannot be un-used later.
- `terms="non_commercial"`: for research without commercial exploitation.
- The profiles are named by use, not by institution. An academic lab under an industry
  contract makes commercial use, and a non-profit may not.
- A source the profile does not admit is not asked. The enrichment records
  `not_queried`, with the profile and the reason, and the knowledge state shows it.
  Sources with unknown terms are excluded too.
- A source whose records keep their depositor's terms is asked, and each record is kept
  only if its depositor's terms allow the use. PubChem BioAssay results of other
  depositors are left out, counted in the enrichment record and in
  `terms_profile["excluded_records"]`.
- Curated statements you apply are yours: the profile does not filter them.
- In development after 0.11.0, refresh preserves the recorded profile unless you
  explicitly override `terms`. Located Europe PMC article fragments have unrecorded
  publication terms, so both profiles exclude that intake before fetching.

Some sources need an account, a key, an academic licence or a written agreement before
they can be asked at all. They are listed, with what each needs, on the *Data sources*
page.
