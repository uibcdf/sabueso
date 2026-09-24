"""SMonitor integration (uibcdf/sabueso#31).

The five mandatory checks of the canonical SMonitor guide (section 7), plus the Sabueso
contract: diagnostics are derived from outcomes that stay recorded as data.
"""

import ast
import pathlib
import pickle
import shutil
import subprocess
import warnings

import pytest
import smonitor

import sabueso
from sabueso._private.smonitor import CATALOG
from sabueso._private.smonitor.catalog import CODES
from sabueso._private.smonitor.outcomes import report_outcomes, report_unanchored
from sabueso._private.smonitor.warnings import (
    EnrichmentFailedWarning,
    EnrichmentTruncatedWarning,
    UnanchoredRecordsWarning,
)
from sabueso.core.errors import (
    ArgumentError,
    ConnectorError,
    RecordNotFoundError,
    ResolverError,
    SabuesoError,
    SchemaError,
    StorageError,
)

PROFILES = ["user", "dev", "qa", "agent", "debug"]
PACKAGE = pathlib.Path(sabueso.__file__).parent


def _catalog_codes():
    for group in ("exceptions", "warnings", "info"):
        for entry in (CATALOG.get(group) or {}).values():
            yield entry["code"]


def test_check1_the_configuration_is_found_inside_the_package():
    executable = shutil.which("smonitor")
    assert executable, "the smonitor CLI comes with the smonitor package"
    result = subprocess.run(
        [executable, "--validate-config", "--config-path", str(PACKAGE)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (PACKAGE / "_smonitor.py").is_file()  # packaged with the library


def test_check2_every_catalog_code_has_a_template():
    codes = set(_catalog_codes())
    # The guide's walk reads only the grouped shape; a flat catalog would yield nothing
    # and pass. Guard the guard (uibcdf/smonitor#22).
    assert len(codes) >= 9, f"expected the full grouped catalog, got {sorted(codes)}"
    orphans = sorted(codes - set(CODES))
    assert not orphans, f"emitted with no template in CODES: {orphans}"


@pytest.mark.parametrize("profile", PROFILES)
def test_check3_every_code_renders_in_every_profile(profile):
    smonitor.configure(profile=profile, handlers=[], codes=CODES)
    try:
        empty = [
            code
            for code in CODES
            if not smonitor.resolve(
                code=code,
                extra={
                    "message": "m",
                    "source": "s",
                    "subject": "x",
                    "detail": "d",
                    "count": 1,
                    "total": 2,
                    "examples": "e",
                },
            )[0]
        ]
        assert not empty, f"empty message under {profile!r}: {empty}"
    finally:
        smonitor.configure(profile="user")


@pytest.mark.parametrize(
    "build",
    [
        lambda: EnrichmentFailedWarning(source="STRING", subject="u", detail="down"),
        lambda: EnrichmentTruncatedWarning(
            source="ChEMBL", subject="u", count=1, total=2
        ),
        lambda: UnanchoredRecordsWarning(subject="u", count=1, examples="chembl:X"),
        lambda: SabuesoError("generic"),
        lambda: ResolverError("resolver"),
        lambda: SchemaError("Fields are fed by several subjects ['a', 'b']."),
        lambda: StorageError("storage"),
        lambda: ConnectorError("UniProt request for P0 failed: HTTP 500"),
        lambda: RecordNotFoundError("UniProt has no record P0"),
        lambda: ArgumentError(
            argument="structures", value="XYZ", caller="x", reason="not a PDB id"
        ),
    ],
)
def test_check4_catalog_classes_survive_a_rebuild(build):
    original = build()
    assert type(original)(*original.args).args == original.args
    assert str(pickle.loads(pickle.dumps(original))) == str(original)


RESERVED = {"code", "message", "raw_message", "extra", "hint"}
BASES = {"CatalogException", "CatalogWarning", "SabuesoError", "SabuesoWarning"}


def _catalog_classes(tree):
    known, found, changed = set(BASES), set(), True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name not in found:
                names = {getattr(b, "id", getattr(b, "attr", "")) for b in node.bases}
                if names & known:
                    found.add(node.name)
                    known.add(node.name)
                    changed = True
    return [
        n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name in found
    ]


def test_check5_no_catalog_class_assigns_a_name_the_base_owns():
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for cls in _catalog_classes(tree):
            for node in ast.walk(cls):
                if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
                    if (
                        isinstance(node.value, ast.Name)
                        and node.value.id == "self"
                        and node.attr in RESERVED
                    ):
                        offenders.append(f"{path.name}:{cls.name}.{node.attr}")
    assert offenders == []


def test_exceptions_keep_their_message_and_gain_a_code():
    error = SchemaError("Fields are fed by several subjects ['a', 'b'].")
    assert str(error) == "Fields are fed by several subjects ['a', 'b']."
    assert error.code == "SABUESO-E-SCHEMA-001"
    assert RecordNotFoundError("x").code == "SABUESO-E-SOURCE-002"
    assert isinstance(ConnectorError("x"), SabuesoError)


def test_diagnostics_reach_smonitor_with_structured_fields():
    smonitor.configure(event_buffer_size=16)
    manager = smonitor.get_manager()
    with pytest.warns(EnrichmentFailedWarning):
        report_outcomes(
            [{"source": "STRING", "status": "error", "detail": "HTTP 503"}],
            subject="sabueso:protein:uniprot:P60174",
        )
    (event,) = [
        e for e in manager.recent_events() if e.get("code") == "SABUESO-W-ENRICH-001"
    ][-1:]
    assert event["extra"]["source"] == "STRING"
    assert event["extra"]["subject"] == "sabueso:protein:uniprot:P60174"
    assert event["extra"]["detail"] == "HTTP 503"


def test_not_found_is_an_answer_not_a_diagnostic():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        report_outcomes(
            [{"source": "STRING", "status": "not_found"}, {"status": "added"}],
            subject="x",
        )
        report_unanchored([], subject="x")


def test_unanchored_records_are_reported_with_examples():
    with pytest.warns(
        UnanchoredRecordsWarning, match="2 records could not be anchored"
    ):
        report_unanchored(
            [{"ref": "chembl:CHEMBL1"}, {"ref": "pdb.ligand:XYZ"}], subject="deck"
        )


def test_a_diagnostic_points_at_the_line_that_called_sabueso():
    # The @signal wrapper adds a frame that outcomes.py counts by hand
    # (uibcdf/smonitor#23). If SMonitor changes its wrapper depth, this fails.
    from sabueso import resolve_protein_card
    from sabueso.resolver import (
        EntityResolver,
        FixtureRCSBClient,
        FixtureUniProtClient,
    )
    from sabueso.tools.db.chembl import FixtureChEMBLClient

    resolver = EntityResolver(
        FixtureUniProtClient("temp_data"), rcsb_client=FixtureRCSBClient("temp_data")
    )
    client = FixtureChEMBLClient("temp_data", failing={"CHEMBL5834"})
    with pytest.warns(EnrichmentFailedWarning) as record:
        resolve_protein_card("P52270", resolver, chembl={}, chembl_client=client)
    # Pick ours by type: other libraries may warn in the same call.
    (ours,) = [w for w in record if issubclass(w.category, EnrichmentFailedWarning)]
    assert pathlib.Path(ours.filename).resolve() == pathlib.Path(__file__).resolve()
