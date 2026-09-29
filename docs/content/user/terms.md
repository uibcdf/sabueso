# What may be done with the knowledge

Every value and relationship on a card traces to the SourceAssertions that state it, and
each SourceAssertion names its source. Sabueso can therefore say, for a use you name,
what each source states about its own terms, and what knowledge remains if you keep
only the sources that allow that use.

```{note}
This is on main, not yet in a release. It is a report of what the sources state, not
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
- **unknown**, with the reason: no terms recorded, or terms that depend on each record.
  PubChem BioAssay keeps each depositor's terms, and a curated statement keeps its
  publication's. Unknown is never "no restriction".

A piece of knowledge **remains** for a use when at least one source that states it is
allowed. For human triosephosphate isomerase, everything remains for a commercial
product, with attribution and share-alike (ChEMBL, BindingDB). For the *T. cruzi*
enzyme, the molecules measured only in PubChem BioAssay are `unknown`.

Each source's terms, with the statement they come from and the date they were reviewed,
are listed on the *Data sources* page. A record older than a year is flagged
`review_due`.

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
  Sources with unknown terms, such as PubChem BioAssay's depositors, are excluded too.
- Curated statements you apply are yours: the profile does not filter them.

Some sources need an account, a key, an academic licence or a written agreement before
they can be asked at all. They are listed, with what each needs, on the *Data sources*
page.
