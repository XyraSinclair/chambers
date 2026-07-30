"""Reference-side conformance regression: every committed golden trace still
describes the reference accountant, bit-for-bit.

    python3 -m pytest chambers/conformance/ -q

This guards the reference against drift in its own traces. The independent Rust
implementation is checked by its own `cargo test` (and cross-checked via
`check_conformance --actual`); this file is the Python half of the pincer.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from .check_conformance import _validate_trace, diff_streams, replay

TRACES = Path(__file__).resolve().parent / "traces"
TRACE_FILES = sorted(p for p in TRACES.glob("*.json") if p.name != "MANIFEST.json")


def _trace_id(p: Path) -> str:
    return p.stem


@pytest.mark.parametrize("trace_path", TRACE_FILES, ids=_trace_id)
def test_reference_matches_trace(trace_path: Path):
    trace = json.loads(trace_path.read_text())
    assert _validate_trace(trace) is None, f"malformed trace {trace_path.name}"
    errs = diff_streams(trace["name"], trace["expected"], replay(trace))
    assert not errs, "\n".join(errs)


def test_corpus_is_nonempty_and_covers_every_reason_class():
    seen = set()
    for p in TRACE_FILES:
        for d in json.loads(p.read_text())["expected"]:
            seen.add(d["reason_class"])
    assert len(TRACE_FILES) >= 7
    # the corpus must exercise all four decision outcomes, or it proves little
    assert seen == {"EMITTED", "REFUSED_ESTIMATOR", "REFUSED_BLOCKED", "REFUSED_CEILING"}, seen


def test_manifest_matches_traces():
    manifest = json.loads((TRACES / "MANIFEST.json").read_text())["traces"]
    for p in TRACE_FILES:
        trace = json.loads(p.read_text())
        assert manifest.get(trace["name"]) == len(trace["expected"]), trace["name"]
