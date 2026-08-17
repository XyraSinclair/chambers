"""Regression tests for the executable literature provenance."""
from __future__ import annotations

import json
from pathlib import Path

from chambers.literature import audit_registry, audit_repository, render

ROOT = Path(__file__).resolve().parents[1]


def registry() -> dict:
    return json.loads((ROOT / "LITERATURE.json").read_text(encoding="utf-8"))


def codes(findings) -> set[str]:
    return {finding.code for finding in findings}


def test_checked_in_literature_is_clean() -> None:
    assert audit_repository(ROOT) == []


def test_duplicate_source_id_convicts() -> None:
    value = registry()
    value["sources"][1]["id"] = value["sources"][0]["id"]
    assert "DUPLICATE" in codes(audit_registry(ROOT, value))


def test_duplicate_stable_locator_convicts() -> None:
    value = registry()
    value["sources"][1]["locator"] = dict(value["sources"][0]["locator"])
    assert "DUPLICATE" in codes(audit_registry(ROOT, value))


def test_missing_repository_target_convicts() -> None:
    value = registry()
    value["sources"][0]["applies_to"] = ["docs/DOES-NOT-EXIST.md"]
    assert "TARGET_MISSING" in codes(audit_registry(ROOT, value))


def test_malformed_locator_convicts() -> None:
    value = registry()
    value["sources"][0]["locator"] = {
        "kind": "doi",
        "value": "not-a-doi",
        "url": "https://doi.org/not-a-doi",
    }
    assert "LOCATOR_VALUE_INVALID" in codes(audit_registry(ROOT, value))


def test_human_view_is_deterministic() -> None:
    assert (ROOT / "docs/LITERATURE.md").read_text(encoding="utf-8") == render(registry())
