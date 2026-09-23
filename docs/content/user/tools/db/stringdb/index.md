# STRING DB Tools

STRING network edges are **functional associations** scored from several evidence
channels (neighborhood, fusion, co-occurrence, co-expression, experiments, databases,
text mining). They are not physical interactions, so Sabueso records them as
`functionally_associated_with` relationships of a resolved protein:

```python
import sabueso

card, resolution = sabueso.resolve_protein_card(
    "P60174", string={"required_score": 700}
)
for rel in card.relationships("functionally_associated_with")[:5]:
    q = rel["qualifiers"]
    print(q["partner_name"], q["combined_score"], q["channels"])
print(card.quality["enrichments"])  # added / not_found / error, with STRING version
```

Clients: `sabueso.tools.db.stringdb.OnlineStringClient` and `FixtureStringClient`.
