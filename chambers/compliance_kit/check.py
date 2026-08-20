#!/usr/bin/env python3
"""Run the Scry Chambers compliance kit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

KIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = KIT_DIR.parents[1]
MANIFEST_PATH = KIT_DIR / "MANIFEST.json"

CODE_KEYS = ("audit_codes", "s_codes", "x_codes", "c_codes", "p_codes", "a_codes", "v_codes")
CODE_PREFIXES = {
    "audit_codes": ("I",),
    "s_codes": ("S",),
    "x_codes": ("X",),
    "c_codes": ("C",),
    "p_codes": ("P",),
    "a_codes": ("A",),
    "v_codes": ("V",),
}


def _is_dist() -> bool:
    return (KIT_DIR / "corpora").is_dir() and (KIT_DIR / "verifier").is_dir()


def _entry_path(entry: Dict[str, Any]) -> Path:
    if _is_dist():
        return KIT_DIR / entry["path"]
    return REPO_ROOT / entry["source"]


def _python_root() -> Path:
    """The directory containing the `chambers` package — what PYTHONPATH
    must carry to run `python3 -m chambers.kernel.verify`."""
    if _is_dist():
        return KIT_DIR / "verifier/python"
    return REPO_ROOT


def _rust_manifest() -> Path:
    if _is_dist():
        return KIT_DIR / "verifier/rust_ledger/Cargo.toml"
    return REPO_ROOT / "chambers/kernel/rust_ledger/Cargo.toml"


def load_manifest() -> Dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="ascii") as fh:
        return json.load(fh)


def _digest(path: Path) -> Tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def verify_manifest(manifest: Dict[str, Any]) -> List[str]:
    failures: List[str] = []
    seen = set()
    for entry in manifest.get("entries", []):
        rel = entry.get("path", "<missing path>")
        if rel in seen:
            failures.append(f"{rel}: duplicate manifest path")
            continue
        seen.add(rel)
        path = _entry_path(entry)
        if not path.is_file():
            failures.append(f"{rel}: missing ({path})")
            continue
        size, sha = _digest(path)
        if size != entry.get("bytes") or sha != entry.get("sha256"):
            failures.append(
                f"{rel}: digest mismatch "
                f"(got bytes={size} sha256={sha}, "
                f"expected bytes={entry.get('bytes')} sha256={entry.get('sha256')})"
            )
    return failures


def _entries_by_path(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {entry["path"]: entry for entry in manifest["entries"]}


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="ascii") as fh:
        return json.load(fh)


def _expected_codes(expected: Dict[str, Any]) -> List[str]:
    codes: List[str] = []
    for key in CODE_KEYS:
        value = expected.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            raise ValueError(f"{key} is not a list")
        codes.extend(value)
    conservation = expected.get("conservation")
    if isinstance(conservation, list) and len(conservation) == 2 and conservation[0] != conservation[1]:
        codes.append("CONSERVATION BROKEN")
    return codes


def _represented_prefixes(expected: Dict[str, Any]) -> Tuple[str, ...]:
    prefixes: List[str] = []
    for key in CODE_KEYS:
        if key in expected:
            prefixes.extend(CODE_PREFIXES[key])
    if "conservation" in expected:
        prefixes.append("CONSERVATION")
    return tuple(prefixes)


def _code_prefix(code: str) -> str:
    if code.startswith("CONSERVATION BROKEN"):
        return "CONSERVATION"
    return code[:1]


def _filter_codes(codes: List[str], prefixes: Tuple[str, ...]) -> List[str]:
    return [code for code in codes if _code_prefix(code) in prefixes]


def _parse_verdict_codes(stdout: str) -> List[str]:
    codes: List[str] = []
    in_verdict = False
    for line in stdout.splitlines():
        if line == "== verdict ==":
            in_verdict = True
            continue
        if not in_verdict:
            continue
        if not line.startswith("  "):
            continue
        item = line.strip()
        if item.startswith("CONSERVATION BROKEN"):
            item = "CONSERVATION BROKEN"
        codes.append(item)
    return codes


def _expected_entry_for_artifact(
    artifact_entry: Dict[str, Any],
    by_path: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    expected_path = artifact_entry["path"][: -len(".ledger.jsonl")] + ".expected.json"
    try:
        return by_path[expected_path]
    except KeyError as exc:
        raise AssertionError(f"{artifact_entry['path']}: missing expected file {expected_path}") from exc


def ledger_artifact_entries(manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    return sorted(
        (
            entry
            for entry in manifest["entries"]
            if entry["role"] == "corpus" and entry["path"].endswith(".ledger.jsonl")
        ),
        key=lambda e: e["path"],
    )


def replay_ledgers(manifest: Dict[str, Any]) -> Tuple[List[str], Dict[str, int]]:
    failures: List[str] = []
    stats = {"clean": 0, "convicted": 0, "artifacts": 0}
    by_path = _entries_by_path(manifest)
    python_root = _python_root()
    for artifact_entry in ledger_artifact_entries(manifest):
        artifact_path = _entry_path(artifact_entry)
        expected_entry = _expected_entry_for_artifact(artifact_entry, by_path)
        expected = _read_json(_entry_path(expected_entry))
        try:
            expected_codes = _expected_codes(expected)
        except ValueError as exc:
            failures.append(f"{expected_entry['path']}: {exc}")
            continue
        expected_exit = 0 if not expected_codes else 1
        env = os.environ.copy()
        env["PYTHONPATH"] = str(python_root)
        proc = subprocess.run(
            [sys.executable, "-m", "chambers.kernel.verify", str(artifact_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            check=False,
        )
        actual_codes = _parse_verdict_codes(proc.stdout)
        stats["artifacts"] += 1
        if expected_exit == 0:
            stats["clean"] += 1
        else:
            stats["convicted"] += 1
        if proc.returncode != expected_exit:
            failures.append(
                f"{artifact_entry['path']}: verifier exit {proc.returncode}, expected {expected_exit}\n"
                f"{proc.stdout}"
            )
            continue
        represented = _represented_prefixes(expected)
        comparable_actual = _filter_codes(actual_codes, represented)
        if comparable_actual != expected_codes:
            failures.append(
                f"{artifact_entry['path']}: verdict codes differ\n"
                f"expected: {expected_codes}\nactual:   {comparable_actual}"
            )
    return failures, stats


def _import_kernel_helpers() -> None:
    python_root = str(_python_root())
    if python_root not in sys.path:
        sys.path.insert(0, python_root)


def replay_views(manifest: Dict[str, Any]) -> Tuple[List[str], int]:
    _import_kernel_helpers()
    from chambers.kernel.events import canonical_json  # type: ignore
    from chambers.kernel.views import view  # type: ignore

    failures: List[str] = []
    by_path = _entries_by_path(manifest)
    inputs = sorted(
        (
            entry
            for entry in manifest["entries"]
            if entry["role"] == "corpus"
            and entry["path"].startswith("corpora/views_traces/")
            and entry["path"].endswith(".input.json")
        ),
        key=lambda e: e["path"],
    )
    for input_entry in inputs:
        expected_path = input_entry["path"][: -len(".input.json")] + ".expected.json"
        expected_entry = by_path.get(expected_path)
        if expected_entry is None:
            failures.append(f"{input_entry['path']}: missing expected file {expected_path}")
            continue
        pair = _read_json(_entry_path(input_entry))
        actual = (canonical_json(view(pair["fold"], pair["policy"])) + "\n").encode("ascii")
        expected = _entry_path(expected_entry).read_bytes()
        if actual != expected:
            failures.append(f"{input_entry['path']}: view report bytes differ")
    return failures, len(inputs)


def replay_lean_accountant(manifest: Dict[str, Any]) -> Tuple[List[str], int]:
    _import_kernel_helpers()
    from chambers.kernel.accountant import Accountant, CapacityEstimate, EstimatorAttestation  # type: ignore

    failures: List[str] = []
    traces_entry: Optional[Dict[str, Any]] = None
    for entry in manifest["entries"]:
        if entry["path"] == "corpora/lean_traces/accountant_traces.json":
            traces_entry = entry
            break
    if traces_entry is None:
        return ["corpora/lean_traces/accountant_traces.json: missing from manifest"], 0

    data = _read_json(_entry_path(traces_entry))
    admissible = EstimatorAttestation("indep", "adversarial_review", "m", True)
    inadmissible = EstimatorAttestation("selfmeter", "self_interested", "m", True)
    checked = 0
    for trace in data.get("traces", []):
        acc = Accountant()
        key = ("golden",)
        acc.register(key, trace["entropy"], trace["ceiling"])
        reasons = []
        for tick, charge in enumerate(trace["charges"]):
            attestation = admissible if charge["admissible"] else inadmissible
            decision = acc.charge(
                key,
                CapacityEstimate(charge["bits"], 0, 0, 0, 0, "c"),
                attestation,
                tick,
            )
            reasons.append(decision.reason_class)
        state = acc.state(key)
        final = {
            "blocked": state.blocked,
            "cumulative": state.cumulative_mbits,
            "demanded": state.demanded_mbits,
            "incident": state.incident,
        }
        if reasons != trace["reasons"]:
            failures.append(f"lean_traces/{trace['name']}: reasons {reasons} != {trace['reasons']}")
        if final != trace["final"]:
            failures.append(f"lean_traces/{trace['name']}: final {final} != {trace['final']}")
        checked += 1
    return failures, checked


def _build_rust_binary() -> Tuple[Optional[Path], Optional[str]]:
    cargo = shutil.which("cargo")
    if cargo is None:
        return None, "cargo not found"
    manifest = _rust_manifest()
    if not manifest.is_file():
        return None, f"Rust manifest not found: {manifest}"
    target_dir = Path(tempfile.mkdtemp(prefix="scry-compliance-rust-"))
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(target_dir)
    proc = subprocess.run(
        [cargo, "build", "--quiet", "--manifest-path", str(manifest), "--bin", "charge-verify"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        shutil.rmtree(target_dir, ignore_errors=True)
        tail = "\n".join(proc.stdout.splitlines()[-20:])
        return None, "cargo build failed:\n" + tail
    binary = target_dir / "debug" / ("charge-verify.exe" if os.name == "nt" else "charge-verify")
    if not binary.is_file():
        shutil.rmtree(target_dir, ignore_errors=True)
        return None, f"cargo build succeeded but binary is missing: {binary}"
    return binary, None


def rust_parity(manifest: Dict[str, Any], python_exits: Dict[str, int]) -> List[str]:
    binary, skip_reason = _build_rust_binary()
    if binary is None:
        print(f"SKIP rust parity: {skip_reason}")
        return []
    failures: List[str] = []
    try:
        for artifact_entry in ledger_artifact_entries(manifest):
            artifact_path = _entry_path(artifact_entry)
            proc = subprocess.run(
                [str(binary), str(artifact_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            expected = python_exits[artifact_entry["path"]]
            if proc.returncode != expected:
                failures.append(
                    f"{artifact_entry['path']}: rust exit {proc.returncode}, python exit {expected}\n"
                    f"{proc.stdout}"
                )
    finally:
        shutil.rmtree(binary.parents[1], ignore_errors=True)
    return failures


def expected_python_exits(manifest: Dict[str, Any]) -> Dict[str, int]:
    by_path = _entries_by_path(manifest)
    exits: Dict[str, int] = {}
    for artifact_entry in ledger_artifact_entries(manifest):
        expected_entry = _expected_entry_for_artifact(artifact_entry, by_path)
        expected = _read_json(_entry_path(expected_entry))
        exits[artifact_entry["path"]] = 0 if not _expected_codes(expected) else 1
    return exits


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rust", action="store_true", help="also run Rust charge-verify parity if it builds")
    args = parser.parse_args(argv)

    manifest = load_manifest()
    manifest_failures = verify_manifest(manifest)
    if manifest_failures:
        print("MANIFEST CHECK FAILED")
        for failure in manifest_failures:
            print(f"  {failure}")
        return 2

    failures: List[str] = []
    ledger_failures, ledger_stats = replay_ledgers(manifest)
    view_failures, view_count = replay_views(manifest)
    lean_failures, lean_count = replay_lean_accountant(manifest)
    failures.extend(ledger_failures)
    failures.extend(view_failures)
    failures.extend(lean_failures)

    if args.rust and not failures:
        failures.extend(rust_parity(manifest, expected_python_exits(manifest)))

    if failures:
        print("COMPLIANCE CHECK FAILED")
        for failure in failures:
            print(f"\n{failure}")
        return 1

    print(
        "COMPLIANCE CHECK OK: "
        f"{len(manifest['entries'])} manifest entries, "
        f"{ledger_stats['artifacts']} ledger artifacts "
        f"({ledger_stats['clean']} clean, {ledger_stats['convicted']} convicted), "
        f"{view_count} views traces, {lean_count} lean accountant traces"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
