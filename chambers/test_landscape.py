"""Regression tests for the executable repository map."""
from __future__ import annotations

import json
from pathlib import Path

from chambers.landscape import audit_manifest, audit_repository

ROOT = Path(__file__).resolve().parents[1]


def manifest() -> dict:
    return json.loads((ROOT / "LANDSCAPE.json").read_text(encoding="utf-8"))


def codes(findings) -> set[str]:
    return {finding.code for finding in findings}


def test_checked_in_landscape_is_clean() -> None:
    assert audit_repository(ROOT) == []


def test_unmapped_component_convicts() -> None:
    value = manifest()
    value["components"] = value["components"][1:]
    assert "COMPONENT_UNDECLARED" in codes(audit_manifest(ROOT, value))


def test_duplicate_component_id_convicts() -> None:
    value = manifest()
    value["components"][1]["id"] = value["components"][0]["id"]
    assert "DUPLICATE" in codes(audit_manifest(ROOT, value))


def test_grandfathered_file_cannot_grow() -> None:
    value = manifest()
    path = "chambers/kernel/settlement.py"
    value["ratchets"]["python"]["grandfathered_max_bytes"][path] -= 1
    assert "PYTHON_SIZE_CAP" in codes(audit_manifest(ROOT, value))


def test_every_rust_crate_stays_declared() -> None:
    value = manifest()
    value["independent_implementations"] = value["independent_implementations"][1:]
    assert "CARGO_CRATE_UNDECLARED" in codes(audit_manifest(ROOT, value))
