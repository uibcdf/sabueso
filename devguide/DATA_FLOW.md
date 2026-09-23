# Sabueso — Data Flow

## End‑to‑End Flow
1) **Input**
   - Accept ID, sequence, SMILES/InChI, name, or structure file.

2) **Resolver**
   - Determine entity type.
   - Normalize input to canonical identifiers where possible.

3) **Database Modules (tools.db.\*)**
   - Fetch data from each source.
   - Each module returns:
     - raw source data
     - source metadata (source name, record ID, timestamps)
   - Example: `tools.db.uniprot` now supports offline fixtures and online fetch.

4) **Aggregator**
   - Map source fields to canonical field paths.
   - Create one SourceAssertion per value asserted by each source record.
   - Store them in the `source_assertion_store`.

5) **Selection**
   - Apply rules per field path.
   - Resolve each field from its SourceAssertions.
   - Set the selected `value` + supporting `source_assertion_ids` on the card.

6) **Card Builder**
   - Assemble nested sections.
   - Ensure all fields reference SourceAssertion IDs.

7) **Output**
   - Return the card to the user.
   - Optionally persist to local cache.

## Ambiguity Handling
- If the input resolves to multiple plausible entities, return a **Deck**.
- Ambiguity should be recorded explicitly in card/deck metadata.

## SourceAssertion Creation Rules
- SourceAssertions are created **before** any selection.
- A SourceAssertion records what an external source asserts about an entity or property.
  See the contract in `devguide/SCHEMA.md` (`id`, `subject_ref`, `field_path`,
  `asserted_value`, `source`, `retrieved_at`; optionally `normalized_value`,
  `source_metadata`, `provenance_ref`, `timestamps`,
  `confidence`).

## Conflict Handling
- If SourceAssertions disagree, add an entry to `quality.conflicts`.
- Conflicts are never resolved by deleting SourceAssertions.
