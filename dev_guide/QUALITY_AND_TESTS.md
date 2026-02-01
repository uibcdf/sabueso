# Sabueso — Quality and Tests

## Testing Strategy
- **Unit tests** for each connector and field mapping.
- **Contract tests** to ensure external APIs still conform to expected shapes.
- **Snapshot tests** for stable, known inputs.

## Offline Testing
- Store minimal example JSONs in a `fixtures/` folder.
- Use fixtures to test mapping and evidence creation without live API calls.

## Evidence QA
- Ensure every selected field has at least one `evidence_id`.
- Ensure every `evidence_id` exists in `evidence_store`.
- Validate field path correctness.

