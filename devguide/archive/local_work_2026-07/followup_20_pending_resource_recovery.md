# Follow-up 20: remaining resources and native FDA OOPD page artifacts

Reviewed the eight pending resources on **2026-10-07 local / 2026-10-08 UTC**.
One gains a scoped native artifact reader: **FDA Orphan Drug Designations and
Approvals**. Seven still need authorized access or original scientific input.
FDA's later live shared-transport failure remains a separate access limitation;
this checkpoint does not claim eight complete online integrations.

Expanded 13-resource queue: **6 scoped resources / 7 pending / 0 unreviewed**.
Original 27-candidate queue: **21 scoped readers / 6 pending / 0 unreviewed**.
Historical 87-resource catalog: **65 in use / 7 evaluating / 11 deferred /
3 retired / 1 out of scope**. These count scoped readers, not all old promises.

## Native FDA acquisition and reader

The [official public search form](https://www.accessdata.fda.gov/scripts/opdlisting/oopd/index.cfm)
now returns native HTTP 200, unlike the preserved earlier excessive-request block.
This changed condition justifies checking the actual provider-declared form route.
One normal read-only POST without a session returns the same form, not data. A
normal anonymous in-memory session GET plus the form's read-only POST returns a
detailed search result. No account, credential, registration, agreement, sponsor
submission, source-side scientific job or client disguise is used. The search is
qualification context, not a delivered search API or database completeness claim.

Two indexed original provider pages are received with unmodified bytes:

| Requested page locator | Original bytes | Native declarations |
| --- | --- | --- |
| [476815](https://www.accessdata.fda.gov/scripts/opdlisting/oopd/detailedIndex.cfm?cfgridkey=476815) | 30002 | One designation; one empty approval table and explicit Not FDA Approved for Orphan Indication |
| [106597](https://www.accessdata.fda.gov/scripts/opdlisting/oopd/detailedIndex.cfm?cfgridkey=106597) | 36357 | One designation; three independent marketing-approval tables |

Their SHA-256 values, original acquisition dates and the unchanged 34331-byte
search form are declared in `temp_data/NOTICE.md`. Original receipts:
`/tmp/sabueso-followup20-access.json`,
`/tmp/sabueso-followup20-fda-search.json`,
`/tmp/sabueso-followup20-fda-session.json` and
`/tmp/sabueso-followup20-fda-entries.json`.

`sabueso.tools.db.fda_orphan.get_page` and `sabueso.mappings.fda_orphan.map_page`
read original HTML using online, fixture and bound HTML/gzip/hash/time clients.
The native page title, unique designation table, original column/field structure,
approval ordinals and all received tables validate before mapping. FDA's native
table nesting and empty-wrapper-row irregularities are explicitly handled; no
browser-style repair, skipped malformed late table or invented empty result.

Independent `annotations.orphan_product_records` retain designation versus
marketing-approval tables, ordered native fields, original cell/table HTML,
blank exclusivity declarations, N/A, literal dates, repeated combined product
names, sponsor-address qualifiers and duplicate/conflicting occurrences.
Procedural designation/approval/exclusivity/withdrawal dates are not overwritten
or used as dataset revisions. Neither provider nor record revision is stated.

Subjects are **`fda:oopd_page:<requested locator>`**. The HTML does **not** echo
cfgridkey: observed requested URL or caller-supplied binding identifies a page,
not a source-stated stable designation, product, molecule or protein entity.
The form itself says CF Grid Key is for FDA purposes. No stable scientific ID,
brand-to-approval reconstruction, protein target, modality, current clinical
conclusion, source-classification default or automatic card enrichment is inferred.
Linked pages, search filtering and complete exports remain separate contracts.

## Separate terms and actual live-access limitation

The page links the [FDA website policy](https://www.fda.gov/about-fda/about-website/website-policies).
It states public-domain reuse unless otherwise noted, requests source credit and
recommends retaining source URL and copy date. Independent contributing-source
and other rights remain separate. This is the recorded **US-PD** source policy,
not an openFDA CC0 grant or an NLM-policy substitution. US-PD's display name now
says "source policy"; verdict/retention/rule behavior is unchanged. Its existing
conservative attribution condition retains the policy's requested credit.

A subsequent real `get_page("106597")` through Sabueso's shared transport at
**2026-10-08T05:33:44+00:00** returns **HTTP 404** with the FDA excessive-request
apology. It is archived in `/tmp/sabueso-followup20-live.sqlite` with body SHA-256
`b0addfa10d944173c41925454431a9899219ffad6bf25b1782f3f1a22f10b377`.
The earlier native HTTP-200 responses do not establish reliable or restored
automated access. The failed route is not retried or hidden by changing the client.
No causal attribution to user agent, request rate or session is asserted.

Separately, the existing editable Python 3.14.7 environment is verified **outside
the checkout**. Bound native artifact reads check exact original hashes. Imported
original responses replay through the normal reader with **zero network attempts**,
matching fields/hash/time/assertions after separating supplied-file receipts.
Import headers remain unknown; times are declared original request-start receipts,
not a new observed live acquisition. Receipt:
`/tmp/sabueso-followup20-native-replay-receipt.json`.
The first qualification script had an incorrect archive method name; its corrected
run passes without another network request. No failed script is passing evidence.

## Seven remaining input/access conditions

| Resource | Result and next concrete condition |
| --- | --- |
| ASD | Preserved original download script still requires licence application/login and research-only/no-third-party-distribution scope. Need an authorized original artifact with distinct recorded-versus-potential sites and native structure/residue/release support. No protected acquisition or application. |
| GtoPdb | Current [official REST documentation](https://www.guidetopharmacology.org/webServices.jsp) explicitly requires a registered API key and recommends the GTP-API-Key header. Need authorized native target/subunit/ligand/assay input and release/quantity scope; database ODbL and content CC BY-SA remain separate. No key, account or data-route attempt. |
| COSMIC | Current [provider terms](https://www.cosmickb.org/terms/) retain accepted institutional licensing/registration and restricted sharing. Need authorized native variant/sample/cohort/release/assembly/transcript support. No no-registration-module grant substitution or protected acquisition. |
| ELM | A bounded native HTTPS GET of the official download page times out; browser licence/example-page checks also supply no original artifact or agreement. Need original class/instance export with exact applicable grant, sequence/bounds/status/publications. No invented API, third-party mirror or motif-to-site inference. Receipt `/tmp/sabueso-followup20-access.json`. |
| BioCyc | Current [native request conditions](https://bioinformatics.ai.sri.com/ptools/licensing/all-reg.shtml) still require agreement/manual processing; API use signifies assent as well. Need original organism/release/frame/quantity input under applicable Open/Limited conditions. No agreement, form or API bypass. |
| OMIM | [Provider copyright statement](https://www.omim.org/help/copyright) is browser-readable but has a 2025 printed date; it is not a newly received entry or current-release grant. Research use remains separate from licensed redistribution. Need authorized original entries/API scope and terms, keeping locus/gene/phenotype/variant/narrative support separate. No restricted entry/data retry or rights borrowed from NCBI. |
| CASTp/CASTpFold | Existing frontend/result routes and [official tutorial](https://cfold.bme.uic.edu/castpfold/infos/allabout/tutorial.html) still do not supply an original scientific result. Need an existing native result with structure/model/assembly/sequence/parameters and separate SA/SE quantities/terms. No failed-route repetition, upload, new job or TLS workaround. |

These are already reviewed resources. Re-reading their descriptions or inventing
adapters without native scientific input would not increase recovered capability.
Future implementation requires a changed access/data condition or an authorized
supplied original. Wider scopes of already scoped readers remain separately
unqueried; none of these seven is declared obsolete or discarded.

## Gates and preservation

Final full offline checkpoint: **5210 passed in 165.54 seconds**, pytest-receptor
with **12 workers** in the existing editable Python **3.14.7** environment;
10 expected failure/cut fixture warnings. The 51 new FDA guards pass. Focused
source/terms/registry/fixture-licensing gate: **92 passed in 4.44 seconds**.
Ruff lint/format (**918 files already formatted**), registry/generated metadata,
strict Sphinx, card shape/schema, dependency preflight and Git diff pass.
Gate receipt `/tmp/sabueso-followup20-gates.json`;
integrity receipt `/tmp/sabueso-followup20-integrity.json`.
Initial focused failures corrected a title-test replacement of only the HTML title
rather than the native H1, and an incorrect whitespace-rejection expectation for
the standard identifier digester. An initial test selection used the wrong fixture
licensing filename. The first full checkpoint found a source-stamp convention
mismatch; the new reader now names its source literally for that existing guard.
A follow-up metadata gate found generated outputs stale after an access-note edit;
the registry was regenerated before the final full checkpoint. An initial strict
Sphinx build rejected a link from user documentation to an external devguide source
document; that link was removed and strict documentation passes. These failed
invocations are not passing evidence.

The original stash, 87 original exported files, 91-path accounting, empty index and
published frozen card are verified unchanged. No new environment/worktree, staging,
commit, push, remote CI, release or stash deletion. GH Run Receptor is reserved for
actual Actions evidence; no remote run was requested.
