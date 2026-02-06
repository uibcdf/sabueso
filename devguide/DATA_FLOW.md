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

4) **Aggregator**
   - Map source fields to canonical field paths.
   - Create evidence objects per field value.
   - Store evidence in `evidence_store`.

5) **Selection**
   - Apply rules per field path.
   - Set the selected `value` + `evidence_ids` on the card.

6) **Card Builder**
   - Assemble nested sections.
   - Ensure all fields reference evidence IDs.

7) **Output**
   - Return the card to the user.
   - Optionally persist to local cache.

## Ambiguity Handling
- If the input resolves to multiple plausible entities, return a **Deck**.
- Ambiguity should be recorded explicitly in card/deck metadata.

## Evidence Creation Rules
- Evidence objects are created **before** any selection.
- Evidence objects must include:
  - `field`
  - `value`
  - `normalized_value`
  - `sources`
  - `source_records`
  - `retrieved_at`
  - optional `timestamps`
  - `confidence`

## Conflict Handling
- If multiple evidence objects disagree, add an entry to `quality.conflicts`.
- Conflicts are never resolved by deleting evidence.
