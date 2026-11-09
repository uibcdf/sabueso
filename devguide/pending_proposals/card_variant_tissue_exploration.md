# Variant and isoform tissue-context exploration

Owners: Sabueso #148 (B6 human/agent profiles), #102/#138 (native tissue rules)
and #112 (checkpoint and delivery). This is development source for 0.15.0.

## Delivered LIVE boundary

Protein `view("variants", options={"mode": "variants"})` presents original
population-variant occurrences. Mode `isoforms` presents original UniProt
isoform occurrences. Human questions `variant_tissue_context` and
`isoform_tissue_context` select their corresponding mode. The dimensionless
`threshold` defaults to 0.1 and is validated through its existing ArgDigest
contract. Compact-agent `access.select("variants", ...)` shares the same captured
result, with projection, typed equality, exact members and stable null-last order.

The adapter `variant_tissue_context_exploration@1` delegates to existing native
explanations under `pext_at_variant@2` and `isoform_exon_usage@3`. Their complete
`view` is the human `native_payload`; raw original explanations are retained
alongside it. Each effective captured request evaluates once. Later human,
agent, source and display operations reuse that result. Caller changes do not
change the captured revision. Native scientific defaults and historical rules
remain fixed. This panel creates no SourceAssertion or project Evidence.

## Scientific and support scope

Genomic variant positions come from the native first-base identifier rule,
separately from protein locations. Assembly/chromosome and source coordinate
context remain explicit. Isoforms retain source-stated transcript versions,
accepted/rejected CDS, completeness of own/variable bases and their original
tissue-specificity statements. This panel adds no alignment, liftover or identity
merge. Native per-tissue resolved/missing/conflicting bases and denominators stay
inspectable; unknown pext never becomes zero expression or harmlessness. A cutoff
does not establish pathogenicity or clinical usefulness.

`variant_tissue_context_support@1` retains exact native input locators and source
membership, including explicitly labelled aggregate support. Source subjects,
field paths and values are checked against the focal captured input. Missing or
misbound records stay visible with partial support. Original conflicts and
unselected alternatives remain explicit in coverage and mandatory interpretation;
the selected native result is preserved. Finer mapping lineage is not invented.

Every row can open its complete native item, explain its original support, and
follow exact source/input/quality/whole-Card/explanation context. Back returns to
the actual initiating selection and effective question. Equal identifiers or
equal complete records retain separate occurrence positions and handles.

Machine frames retain mandatory interpretation, support references and exact
locators. When a value and its interpretation exceed the byte budget, they defer
together; a partial value is never detached from its scientific context. Display
filters preserve the underlying native result and source gaps.

## Qualification and continuation

The complete owning module is `test_card_variant_exploration_offline.py`.
It includes a public HsTIM positive example and labelled synthetic uncertainties,
genomic versus protein coordinates, transcript/CDS gaps, source membership,
duplicate occurrences, typed selection, cached captures, bounded machine output,
escaped HTML and exact source/back paths. Both installed workflows copy/select
the complete module. Copied receiving uses byte-identical declared public inputs;
the [LIVE receipt](../evidence/variant_tissue_context_live_checkpoint_20261108.json)
owns actual results, source epochs, resources and acceptance limits.

The new topic/questions are advertised only for LIVE protein explorers. Earlier
saved menus, verifiers and interpretations remain unchanged. Saving this new
panel and its dependent source/detail views is explicitly unavailable until a
genuine clean-producer original precedes separately versioned independent saved
reading. Unrelated literal saving and captured Card export remain available.

The clean SDK230 [genuine original](../evidence/variant_tissue_context_live_original_20261108.json)
now preserves 33 cases, all actual source/navigation/access instances, 101 native
requests and 1,415 finite agent requests / 1,461 pages. SDK-free byte/reference/
cell/locator accounting passes, alongside 140 selected and all 39 copied original
cases. The capsule is immutable and predates independent reading. Next implement
separately versioned independent native/source/selection/presentation and exact
actual-origin replay over these bytes with current scientific engines forbidden.
Natural-variant/mutagenesis rich annotation context, supplied-Card comparisons and
typed biological associations retain their remaining B6 scope. Scientific,
uncoached researcher, agent, representative workload, actual-consumer and
installed/hosted acceptance remain open. B2 is deferred; #192 unresolved; B8,
candidate selection, schema freezing and release remain unresumed.
