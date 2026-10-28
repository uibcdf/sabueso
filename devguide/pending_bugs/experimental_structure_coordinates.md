# Original experimental coordinate/reference scope (#170)

Owner: [#170](https://github.com/uibcdf/sabueso/issues/170), coordinated with
[#169](https://github.com/uibcdf/sabueso/issues/169), #148 and #112. This is an
observed gap, not an implemented fix. Prioritize it after declaration-admission
qualification and before broader region/site/model/assembly transitions.

An explicitly synthetic change to the selected sequence in the public P52270/1SUX
Card leaves original SourceAssertions and experimental qualifiers intact. The
selected sequence is replaced with alanines at its original length. A canonical
region question for position 3 still returns `ok`, one row and two complete chains,
despite the selected sequence contradicting its supporting original assertion.
The existing strict canonical reference reader refuses the same Card with
`not_computed / canonical_source_support_unavailable`.

The regional request guard checks selected identity, sequence/length consistency,
conflicts and bounds; it does not bind those values to their original source
support or establish the experimental mapping's original reference. That guard is
unchanged from qualified source `e712acf`; the observation was made during the
local #169 continuation. No source query, private pilot or biological claim is
involved.

Define a named experimental coordinate/reference admission contract. Reuse strict
original identity/sequence binding where appropriate and audit original mapping
inputs, axes and revisions. Preserve each declaration and its original qualifiers
even when regional claims cannot be computed. Missing reference or observed-axis
support is not a finding of missing residues or absent structure. Do not infer
correspondence by equal residue numbers, a shared label or sequence similarity,
and do not perform an alignment or discovery.

Cover direct regional views, Deck groups/explanations, human/compact questions,
source transitions, packets and independently saved reading. Original inventory
@1/@2 and explanation @1/@2/@3 retain their own meanings; coordinate semantics
need a new named policy and receiving predicates. Historical missing mapping
inputs stay unknown, without backfill.

Sanitized proof: `recovered_work/structure_admission_169_20261028/region-axis-observation.json`,
owner #170/#148/#112, review at experimental coordinate-admission implementation.
The separate [declaration correction](experimental_structure_admission.md) scopes
relationship membership and does not claim to repair this coordinate gap.
