# Original native Zstandard qualification frames

`zstd_native_v1.json` freezes two original native `compression.zstd` frames from
Python 3.14.7 / libzstd 1.5.7, produced at Sabueso source
`11bfd628a906898d50a9899ad602c6ea05bf345f` before adding the backport selector.
Level 3, checksum enabled and zero background workers match the recorded producer.
Its SHA-256 is `b649597374069aa5e45105987691159fa674577dfbc2089c715eab52ccac2d0e`.
Git attributes preserve the actual bytes on Windows as well.

One payload is completely synthetic UTF-8/Boolean/integer/float/null/unit text.
The other is the unchanged public synthetic historical Card exploration in
`tests/core/data/card_exploration_literal_v1.json` (53,762 bytes), whose provenance
is recorded in that directory's README. Neither introduces scientific assertions,
new provider queries or private/pilot content. This is codec qualification, not a
Card schema freeze, public compressed-file format or new scientific interpretation.

Preserve these original producer bytes. Do not regenerate frames to make a new
backend pass. Future encoders need only preserve decoded bytes, not match encoded
bytes; their actual outputs are recorded separately by the CI probe for reverse
native-reader checks.

`zstd_backport_v1.json` is a genuine backports.zstd 1.8.0 / libzstd 1.5.7 report
from CPython 3.11.11 on Linux, executed with `-I -S -B` using the published
cp311 wheel extracted into owned scratch. No existing environment was modified.
The wheel's SHA-256 is
`9c7fe40a58dbe1fd358e0ceb5b6b3f50a9b328f8fff42dcb3bdaeb9a022c2506`;
the fixture's SHA-256 is
`06627c52002c8c496fc12050a2931be5ad9f3109d831f89efa1d29867448feb5`.
It retains the original producer/tool and payload/frame hashes. Producer source
snapshots and wheel metadata are owned by #178/#112 under
`recovered_work/zstd_backend_178_20261103/`, reviewed at backend adoption or
the next original-frame compatibility checkpoint. Preserve both native and
backport producer bytes; every selected backend must read both unchanged.
