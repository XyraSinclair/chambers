"""Replay every golden trace through the reference accountant and assert the
Decision stream matches `expected` bit-for-bit (SPEC §3).

    python3 -m chambers.conformance.check_conformance          # reference vs traces
    python3 -m chambers.conformance.check_conformance --actual <dir>/*.actual.json

With no args this checks the REFERENCE against the committed traces — a
regression guard that the traces still describe the reference. The Rust
implementation writes its own `<name>.actual.json` decision streams; point
`--actual` at them to diff a foreign implementation against the same expected
streams without trusting its own harness.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from .reference import (
    CapacityEstimate,
    CompositionKey,
    EgressAccountant,
    EstimatorAttestation,
)

TRACES = Path(__file__).resolve().parent / "traces"

DECISION_FIELDS = (
    "accepted",
    "reason_class",
    "reason_detail",
    "cumulative_mbits",
    "demanded_mbits",
    "blocked",
    "incident",
    "leakage_class",
    "newly_incident",
)


def _validate_trace(trace: dict) -> Optional[str]:
    """SPEC §5 — the harness rejects malformed traces before replay."""
    if trace.get("spec") != "egress-accountant/1":
        return f"unknown spec {trace.get('spec')!r}"
    registered = set()
    n_charges = 0
    for op in trace["ops"]:
        if op["op"] == "register":
            if op["subject_entropy_mbits"] <= 0:
                return "register with subject_entropy_mbits <= 0"
            registered.add(tuple(op["key"]))
        elif op["op"] == "charge":
            if tuple(op["key"]) not in registered:
                return f"charge on unregistered key {op['key']}"
            e = op["estimate"]
            for fld in ("enum_value_mbits", "ordering_mbits", "field_presence_mbits", "text_mbits", "side_channel_mbits"):
                if e[fld] < 0:
                    return f"negative estimate field {fld}"
            n_charges += 1
        else:
            return f"unknown op {op['op']!r}"
    if len(trace["expected"]) != n_charges:
        return f"expected length {len(trace['expected'])} != {n_charges} charges"
    return None


def replay(trace: dict) -> List[dict]:
    """Run a trace through the reference accountant; return the Decision stream
    as JSON objects (one per charge, in order)."""
    acc = EgressAccountant()
    out: List[dict] = []
    for op in trace["ops"]:
        key = CompositionKey(*op["key"])
        if op["op"] == "register":
            acc.register(key, op["subject_entropy_mbits"], op["ceiling_mbits"])
        else:
            e = op["estimate"]
            est = CapacityEstimate(
                enum_value_mbits=e["enum_value_mbits"],
                ordering_mbits=e["ordering_mbits"],
                field_presence_mbits=e["field_presence_mbits"],
                text_mbits=e["text_mbits"],
                side_channel_mbits=e["side_channel_mbits"],
                channel=e["channel"],
            )
            a = op["estimator"]
            att = EstimatorAttestation(
                estimator_id=a["estimator_id"],
                independence=a["independence"],
                method=a["method"],
                worst_case_over_secrets=a["worst_case_over_secrets"],
            )
            out.append(acc.charge(key, est, att, op["tick"]).as_json_obj())
    return out


def diff_streams(name: str, expected: List[dict], actual: List[dict]) -> List[str]:
    errs: List[str] = []
    if len(expected) != len(actual):
        errs.append(f"{name}: length {len(actual)} != expected {len(expected)}")
        return errs
    for i, (exp, act) in enumerate(zip(expected, actual)):
        for fld in DECISION_FIELDS:
            if exp[fld] != act.get(fld):
                errs.append(f"{name}[{i}].{fld}: got {act.get(fld)!r}, expected {exp[fld]!r}")
    return errs


def check_reference() -> Tuple[int, List[str]]:
    errs: List[str] = []
    n = 0
    for path in sorted(TRACES.glob("*.json")):
        if path.name == "MANIFEST.json":
            continue
        trace = json.loads(path.read_text())
        bad = _validate_trace(trace)
        if bad:
            errs.append(f"{path.name}: malformed — {bad}")
            continue
        errs.extend(diff_streams(path.name, trace["expected"], replay(trace)))
        n += 1
    return n, errs


def check_foreign(actual_dir: Path) -> Tuple[int, List[str]]:
    """Diff a foreign implementation's `<name>.actual.json` streams against the
    committed `expected` streams."""
    errs: List[str] = []
    n = 0
    for path in sorted(TRACES.glob("*.json")):
        if path.name == "MANIFEST.json":
            continue
        trace = json.loads(path.read_text())
        actual_path = actual_dir / f"{trace['name']}.actual.json"
        if not actual_path.exists():
            errs.append(f"{trace['name']}: no actual stream at {actual_path}")
            continue
        actual = json.loads(actual_path.read_text())
        errs.extend(diff_streams(trace["name"], trace["expected"], actual))
        n += 1
    return n, errs


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--actual":
        n, errs = check_foreign(Path(sys.argv[2]))
        label = "foreign"
    else:
        n, errs = check_reference()
        label = "reference"
    if errs:
        print(f"CONFORMANCE FAIL ({label}): {len(errs)} divergences across {n} traces")
        for e in errs[:40]:
            print("  " + e)
        return 1
    print(f"CONFORMANCE OK ({label}): {n} traces agree bit-for-bit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
