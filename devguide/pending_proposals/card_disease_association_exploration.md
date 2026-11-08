# Retained disease association exploration

Owners: Sabueso #148 (rich B5 profiles), #90 (disease identity/native readers)
and #112 (checkpoint and delivery). This increment extends the existing disease
definition, identity and hierarchy routes; it acquires no Cards or source data.

## Working contract

Human `view("associations")` and `answer("retained_associations")` share a
captured result with compact-agent `access.select("associations")`.
Each original relationship, UniProt disease xref occurrence or ClinVar condition
keeps its own grain, input pin, exact location and source support. Protein native
`disease_statements` and molecule native `clinical()` remain inspectable, with
their original order/values; this panel does not change disease grouping defaults.

The named `disease_association_context@1` rule matches a disease's exact MONDO
anchor or source-supported equivalent identifiers, including the bounded existing
MedGen concept → UID → MONDO contract. Names, synonyms, related
xrefs, subclass edges and ChEMBL shared headings grant no identity. Supported
conflicting MONDO claims and condition identifiers stay explicit. Unsupported,
missing or misbound identity support never creates a join. Incomplete competing
MedGen branches remain unresolved; completed paths retain both original steps. This bounded rule is
not a general identity closure or a replacement for `disease_grouping@3`.

Both focal and explicitly supplied Cards retain their own scopes and revisions.
Association direction and original predicates remain visible. Source confidence,
channels, scores, qualifiers and raw fields remain in the original item; the panel
does not normalize or rank unlike source scores. Association, indication and
variant-condition mention do not establish causality, mechanism or efficacy.
Absence of matching supplied context is not evidence of global absence.

Each row opens its original item, role-bound support and exact source/input
context. Navigation to another supplied capture changes the focal inspection
explicitly and returns to the actual originating selection/question. No source
lookup, latest-Card substitution or implicit enrichment is allowed. Typed
projection/equality/membership/order and bounded escaped text/HTML preserve the
same result for agents and humans.

## Implementation sequence and qualification

The LIVE producer is implemented. Its [selected checkpoint](../evidence/disease_association_live_checkpoint_20261108.json)
passes 1,031 distinct offline cases, including all 43 owning cases with public
positive and labelled synthetic uncertain/conflicting/missing/foreign controls.
The complete 43-case owning module also passes outside checkout with seven
byte-identical inputs. The one selected-gate warning belongs to an existing
simulated ChEMBL failure control; copied owning tests emit none. Native, identity/source-support, generic explorer, clinical, quantity, argument
and source/fixture gates are included in the selected scope. Keep devguide current at
each increment and commit intermediate checkpoints with `[skip ci]`.

Capture the genuine clean producer's complete human/machine/source/navigation
original before implementing the separately versioned independent reader.
Saving this new scientific panel is unavailable until that reader is qualified.
Existing exploration formats and scientific defaults stay fixed. Installed,
hosted, scientist, uncoached researcher, workload and actual-consumer acceptance
remain separate; this work does not resume B8 or authorize a release.
