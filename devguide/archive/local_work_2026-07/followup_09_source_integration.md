# Ninth five-source integration follow-up

Reviewed **CASTpFold, ProBiS, Interactome3D, 3did and FDA Orphan** on
2026-10-07. This is an access/contract follow-up to the preserved prototypes,
not a delivered connector or a new code checkpoint. All five remain evaluating.
Fourteen of the original 27 reviewed candidates have scoped recovered readers;
**13** still require integration. The eighth follow-up's **4445-test** code
checkpoint remains the latest full offline baseline.

## CASTpFold: units qualified, native result still unavailable

The preserved `protein_translational_sources.py::map_translational_source`
accepts generic pocket rows and fills `protein_ref` from the caller. Recoverable
requirements are precomputed topography, original structure/pocket identity,
lining atoms/residues, parameters and physical quantities. That synthetic shape
does not qualify a native reader or protein/residue correspondence.

The public [info index](https://cfold.bme.uic.edu/castpfold/infos/info.json)
returns actual JSON: **1490 bytes**, SHA-256
`9d23190a962097673e84ecdc309c89d222cb9ec208e28c2388a32fa1218bfb97`.
It links the provider's [manuscript examples](https://cfold.bme.uic.edu/castpfold/infos/allabout/Example%20from%20manuscript.html)
and [tutorial](https://cfold.bme.uic.edu/castpfold/infos/allabout/tutorial.html).
These documentation assets return HTTP 200 and remain outside fixtures.
The examples provide existing PDB 6M0J and AF2 A0A2N0QT79 results, rather than
invented queries or submitted analysis jobs. The previously received public
frontend declares `data/pdb/<middle>/<id>/processed/<id>.basic.json`,
`data/AF_db/<middle>/<id>/processed/<id>.basic.json` and the corresponding
`tmp/<id>.measure.json` as read-only result paths.

The three exact GETs for **6m0j basic**, **6m0j measure** and
**A0A2N0QT79 basic** each return HTTP 200 but the same **713-byte HTML
application shell**, SHA-256
`0f032b4f03af8a168aef3dbaa94b1207ba906bbbf818d376dfb9291adb1aa42c`.
They do not contain scientific JSON. A successful HTTP status or readable
documentation is not a successful native pocket acquisition, an empty pocket
result, biological absence or source retirement. No result fixture/parser/client
is admitted from these responses.

The tutorial explicitly distinguishes solvent-accessible area and volume from
solvent-excluded measures and declares **angstrom squared** and **angstrom cubed**.
It also describes AF2 queries being routed to representative structures and
independent Foldseek similarity and DeepFRI functional predictions. These are
useful qualification facts for a future native reader, not acquired pocket values,
source identity merges or newly inferred function. The upload form's default
probe does not establish the probe used by an existing record. Exact native
result shape, structure/model/assembly/sequence axes and calculation revision
still require a received scientific artifact. Free access/citation does not
establish a separate data redistribution grant. No coordinates, uploads,
similarity search or computation endpoint is invoked.

## ProBiS: documented representative lookup also fails

The native database documentation distinguishes existing alignments and
representative lookups from computational align/scan operations. This follow-up
performs one GET to its exact documented example:
[get_representative for 1ytf.A](http://probis.cmm.ki.si/rest/get_representative?structure_id=1ytf.A),
with `Accept: application/json`. It returns **HTTP 404**, **278 bytes**, SHA-256
`e08c8a049d6b436bc33b97238bf33b996ecf8d79aa0a7f9137a14da501f00c32`.
The earlier documented alignment example failed separately. No native
representative relation or alignment is received.

An eventual native relation must preserve both chain identities, representative
basis, original record and nonredundant-set revision. A high sequence similarity
threshold is not identity; scores/coverage do not become function, ligand binding
or a probability. Native data reuse remains unqualified. The NIH service is not
silently substituted for this provider. No alignment, scan, minimization,
superimposition, coordinate acquisition or other job is requested.

## Interactome3D: exact metadata export located, transport still fails

The preserved `protein_sources.py::fetch_interactome3d` sends `queryProt` to
both APIs and discards the XML root context. The documented protein query uses
`uniprot_ac`; interaction queries and protein records have separate contracts.
Recoverable requirements include native structure/model occurrences, ranks,
templates, per-participant bounds and independent version/coverage scope.

The public [download directory](https://interactome3d.irbbarcelona.org/downloadset.php?path=complete&queryid=human&release=current)
links the exact **proteins.dat** and **interactions.dat** metadata tables,
independently of coordinate tarballs. It distinguishes complete and representative
datasets. The complete human proteins table is listed as 25 MB; a bounded direct
GET to its exact linked
[proteins.dat](https://interactome3d.irbbarcelona.org/user_data/human/download/complete/proteins.dat)
fails with curl exit **35**, **HTTP 000**, `SSL_ERROR_SYSCALL`, and **no body**.
The metadata fallback therefore does not qualify a reader either. TLS verification
is not disabled, and no coordinate archive is fetched.

An eventual export must validate the whole native table before selection, retain
all occurrences and pin dataset/species/complete-versus-representative scope.
The mutable `current` route, release-directory labels and old HTML footer are
not a received record revision. A Model's template PDB is not the model's
experimental method; bounds are not exact residue correspondence. Exact data
terms/input rights remain separate and unqualified. No modelling or docking.

## 3did: source description reachable, export not qualified

The provider's [index](https://3did.irbbarcelona.org/index.php) is browser-readable
and lists Pfam/PDB scope. The linked Download page still fails in web acquisition
(internal error/timeout); earlier direct HTTP 525 receipts remain historical,
not a newly received export. Documentation availability does not qualify a native
DDI/DMI fixture or scientific database revision.

The preserved `protein_structural_context.py::map_3did` assigns a caller protein,
row-index fallback identities and a universal curated class. Useful requirements
remain original structural-instance identity and contacts. Native PDB residue
contacts, Pfam HMM profile positions, interface topology and InterPreTS scores
must retain independent axes/version/support. Source lowercase-chain encoding
must not be silently normalized. Exact flat-file representation and contributing
data rights still require qualification. No motif matching, SQL import,
protein-function transfer or new structural calculation.

## FDA Orphan: public filter contract reviewed without retrying the blocked export

The readable [official instructions](https://www.fda.gov/industry/designating-orphan-product-drugs-and-biological-products/instructions-searchable-designation-database)
clarify that populated filters combine with AND. Date selection means designation
date for all designations, but orphan-indication approval date when only approved
products are selected. Query/date basis, pagination and condensed/detailed/Excel
representation must be explicit in a future native receipt.

The earlier direct OOPD excessive-requests HTTP 404 body remains the access
blocker; no new programmatic database request, filter/export submission, account,
notice acceptance, bypass or provider contact occurs. The original
`map_orphan_designations` fills caller protein targets and defaults modality and
intervention status; none follows from a product/sponsor name, CF Grid Key or
designation. Native designation, approval and indication support must stay
independent. Exact OOPD data/third-party terms cannot be borrowed from openFDA.

## Receipts and next qualification conditions

Public response bytes stay in `/tmp/sabueso-followup9-*`, outside package data.
The unchanged examples HTML is **12781 bytes**, SHA-256
`f019e056fefa8d58c93c5b867e395cf0cd8186787fe482a32811305a788fcf99`;
the tutorial is **8768 bytes**, SHA-256
`dec11002e45933d05a598c57eebbccfd5c0e753c1527b57e4a959f6ab579c3b6`.
No new scientific fixture, executable API, card enrichment or schema change.
Registry/public catalog cases pass **17 tests in 2.75 seconds**, through
pytest-receptor with **12 workers**. Ruff, registry/generated metadata, frozen
shape/schema, strict Sphinx and final diff/integrity checks pass. These are
metadata/documentation gates; the latest full code baseline remains the eighth
follow-up's **4445 tests**, rather than a repeated full run. Qualification receipts
are recorded in [validation.md](validation.md).

Before another access attempt, require a concrete changed condition: reachable
native CASTpFold result JSON, a working ProBiS existing-data route, a retrievable
Interactome3D metadata export, an available 3did native export, or authorized
unblocked OOPD acquisition. An explicitly supplied native artifact can be reviewed
with its original source/query/version/receipt and applicable terms. Repeating
the same failed request alone is not integration progress.

Historical catalog stays **53 in use, 19 evaluating, 11 deferred, 3 retired,
1 out of scope, 0 not registered**. Remaining original candidates: GtoPdb,
MEROPS, COSMIC, HPO, ELM, BioCyc, OMIM, Interactome3D, PDBTM, 3did, CASTp,
ProBiS and FDA Orphan. The original stash and all 87 exported files are retained.
No stage, commit, push, stash drop or separate environment/worktree occurs.
