# Sabueso — Quality and Tests

## Testing Strategy
- **Unit tests** for each connector and field mapping.
- **Contract tests** to ensure external APIs still conform to expected shapes.
- **Snapshot tests** for stable, known inputs.

## Offline Testing
- Store minimal example JSONs in a `fixtures/` folder.
- Use fixtures to test mapping and SourceAssertion creation without live API calls.

## SourceAssertion QA
- Ensure every selected field has at least one entry in `source_assertion_ids`.
- Ensure every referenced ID exists in `source_assertion_store`.
- Validate field path correctness.

