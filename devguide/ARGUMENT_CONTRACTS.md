# Sabueso — Argument contracts (ArgDigest)

Sabueso digests the arguments of its public tools with ArgDigest, as MOLI's
support-library policy requires (uibcdf/sabueso#31) and as the sibling components do
(MolSysMT, MolSysViewer).

## Layout

- `sabueso/_argdigest.py`: the configuration, the same as the siblings'.
  - `DIGESTION_STYLE = "package"`, `STRICTNESS = "warn"`, `SKIP_PARAM = "skip_digestion"`.
  - `UNKNOWN_ARGUMENT = "error"`: a mistyped keyword is refused, as plain Python would.
- `sabueso/_private/argdigest/digest.py`: `arg_digest()`, the decorator bound to that
  configuration.
- `sabueso/_private/argdigest/argument/<name>.py`: one digester per argument name,
  `digest_<name>(value, caller=None)`. Shared helpers live in `_shared.py`, outside the
  digester package.
- `sabueso/_private/argdigest/function/`: function contracts (axis 1). It is empty, because
  every decorated function has a closed signature. A public function that takes
  `**kwargs` must declare its domain there.

## Decorated functions

`resolve_protein_card`, `resolve_molecule_card`, `ligand_deck` and `ambiguity_deck`.

- `@arg_digest()` goes under `@signal`.
- Each function takes `skip_digestion=False`. Use it only for internal calls with values
  Sabueso just built, never at a public boundary.

## What the digesters decide, and what they do not

- **Refused with `ArgumentError`** (`SABUESO-E-ARG-001`, also a `ValueError`): values that
  would otherwise run and give a plausible wrong result. Examples:
  - `structures="1SUX"` used to iterate its characters; it is now one structure;
  - unknown source options (`chembl={"limt": 10}`) and out-of-range ones;
  - non-boolean switches;
  - strings where a client object is expected.
- **Not refused**: whether an identifier names a supported record. That is the resolver's
  answer, recorded in the resolution (`status="unsupported"`), not an argument error.
- **Source clients are duck-typed**: any object, or `None` for the online default. Their
  protocol is exercised by the call, and failures are source outcomes.

## Guards

`tests/core/test_argument_contracts_offline.py`:

- every parameter of every decorated function has a digester;
- the refusals listed above;
- unknown keywords are refused;
- no `DigestNotDigestedWarning` on ordinary calls.

## Known limitations

- ArgDigest's wrapper adds frames. Diagnostics raised inside decorated functions therefore
  compute their stack level (`sabueso/_private/smonitor/outcomes.py`, see
  `DIAGNOSTICS.md`). Reported upstream.
- A truthy non-boolean `skip_digestion` (for example `"yes"`) switches digestion off
  before the flag itself is digested, so only a falsy non-boolean reaches its digester.
  Reported upstream.
