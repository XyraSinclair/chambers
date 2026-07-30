"""runtime-r2/1 — the deterministic runner (RUNNER-SPEC.md, normative).

    python3 -m chambers.runtime.runner run BUNDLE_DIR [--receipt OUT]
    python3 -m chambers.runtime.runner verify BUNDLE_DIR RECEIPT

RUNTIME.md rung R2, first artifact. The runner executes a content-
addressed bundle twice in hermetic isolation and issues a receipt ONLY
if both output hashes agree (deterministic or no receipt — value-grade
claims fail closed). `verify` is the stranger's check: re-execute,
compare. Reproduction replaces trust; that is the rung.

What this claims and refuses to claim is RUNNER-SPEC §0. In one line:
reproducibility, not confidentiality — and no LLM call rides this rung.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kernel"))

from events import canonical_json, event_id  # noqa: E402

SPEC = "runtime-r2/1"
CLAIM_CLASS = "reproducible_local"
RUNNER_ID = "chambers-r2-runner/1"
MAX_TIMEOUT_S = 600


class RunRefused(Exception):
    """Issuance refused, with a named reason. Refusal is not conviction
    (RUNNER-SPEC §4): a refused bundle earned no claim, not a crime."""


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _is_uint(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def load_manifest(bundle_dir: str) -> dict:
    """Parse + validate the manifest. Totality: every malformation is a
    named refusal, never a crash."""
    mpath = os.path.join(bundle_dir, "manifest.json")
    try:
        manifest = json.load(open(mpath, encoding="ascii"))
    except Exception as exc:
        raise RunRefused(f"unreadable manifest: {exc}") from None
    if not isinstance(manifest, dict) or manifest.get("spec") != SPEC:
        raise RunRefused(f"manifest.spec must be {SPEC!r}")
    if not (isinstance(manifest.get("entry_sha256"), str)
            and manifest["entry_sha256"].startswith("sha256:")):
        raise RunRefused("manifest.entry_sha256 must be a sha256:… string")
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and v.startswith("sha256:")
            for k, v in inputs.items()):
        raise RunRefused("manifest.inputs must map relpath -> sha256:… string")
    if manifest.get("interpreter") != "python3":
        raise RunRefused("runtime-r2/1 declares exactly interpreter 'python3'")
    if not (_is_uint(manifest.get("timeout_s"))
            and 0 < manifest["timeout_s"] <= MAX_TIMEOUT_S):
        raise RunRefused(f"manifest.timeout_s must be a uint in (0, {MAX_TIMEOUT_S}]")
    return manifest


def bundle_id(manifest: dict) -> str:
    return event_id(manifest)


def check_bundle(bundle_dir: str) -> Tuple[dict, str]:
    """Verify every byte the manifest names BEFORE anything executes:
    entry hash, each input hash, no extra files, no missing files.
    Returns (manifest, bundle_id). Fail closed on any mismatch."""
    manifest = load_manifest(bundle_dir)
    entry = os.path.join(bundle_dir, "entry.py")
    if not os.path.isfile(entry):
        raise RunRefused("entry.py missing")
    if _sha256_file(entry) != manifest["entry_sha256"]:
        raise RunRefused("entry.py does not match manifest.entry_sha256")
    declared = dict(manifest["inputs"])
    inputs_dir = os.path.join(bundle_dir, "inputs")
    found = set()
    if os.path.isdir(inputs_dir):
        for root, _dirs, files in os.walk(inputs_dir):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, bundle_dir)
                found.add(rel)
    if found != set(declared):
        extra = sorted(found - set(declared))
        missing = sorted(set(declared) - found)
        raise RunRefused(f"inputs drift: extra={extra} missing={missing}")
    for rel, want in sorted(declared.items()):
        got = _sha256_file(os.path.join(bundle_dir, rel))
        if got != want:
            raise RunRefused(f"input {rel} hash mismatch: {got} != {want}")
    return manifest, bundle_id(manifest)


def _execute_once(bundle_dir: str, manifest: dict) -> str:
    """One hermetic execution in a fresh ephemeral copy: python3 -I,
    EMPTY environment, stdin closed, hard timeout. Returns the output
    file's sha256. Every failure is a named refusal."""
    with tempfile.TemporaryDirectory(prefix="r2_run_") as work:
        run_dir = os.path.join(work, "bundle")
        shutil.copytree(bundle_dir, run_dir)
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "entry.py"],
                cwd=run_dir,
                env={},                    # no inherited world
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,  # not part of the claim
                stderr=subprocess.DEVNULL,
                timeout=manifest["timeout_s"],
            )
        except subprocess.TimeoutExpired:
            raise RunRefused(f"timeout after {manifest['timeout_s']}s") from None
        if proc.returncode != 0:
            raise RunRefused(f"entry exited {proc.returncode}")
        out = os.path.join(run_dir, "output")
        if not os.path.isfile(out):
            raise RunRefused("entry wrote no ./output file")
        return _sha256_file(out)


def run(bundle_dir: str) -> dict:
    """Issuance (RUNNER-SPEC §3): verify bytes, execute TWICE in fresh
    copies/processes, issue the receipt only on byte-identical outputs."""
    manifest, bid = check_bundle(bundle_dir)
    first = _execute_once(bundle_dir, manifest)
    second = _execute_once(bundle_dir, manifest)
    if first != second:
        raise RunRefused(
            f"nondeterministic: run1 {first} != run2 {second} — no receipt"
        )
    return {
        "kind": "run_receipt", "spec": SPEC, "claim_class": CLAIM_CLASS,
        "bundle_id": bid, "output_sha256": first,
        "runs": 2, "exit_code": 0,
        "interpreter_declared": manifest["interpreter"],
        "runner": RUNNER_ID,
    }


def receipt_id(receipt: dict) -> str:
    return event_id(receipt)


def verify(bundle_dir: str, receipt: dict, out=sys.stdout) -> int:
    """The stranger's check (RUNNER-SPEC §5): recompute the bundle id
    from bytes, re-execute ONCE, compare output hashes.
    0 REPRODUCED | 1 DIVERGED/refused | 2 malformed."""
    if not (isinstance(receipt, dict) and receipt.get("spec") == SPEC
            and isinstance(receipt.get("bundle_id"), str)
            and isinstance(receipt.get("output_sha256"), str)):
        print("MALFORMED: not a runtime-r2/1 receipt", file=out)
        return 2
    if receipt.get("claim_class") != CLAIM_CLASS:
        print(f"MALFORMED: claim_class {receipt.get('claim_class')!r} is not "
              f"{CLAIM_CLASS!r} — a receipt is evidence at its class and "
              f"nothing above it", file=out)
        return 2
    try:
        _manifest, bid = check_bundle(bundle_dir)
        if bid != receipt["bundle_id"]:
            print(f"DIVERGED: bundle on disk is {bid}, receipt names "
                  f"{receipt['bundle_id']}", file=out)
            return 1
        got = _execute_once(bundle_dir, _manifest)
    except RunRefused as exc:
        print(f"DIVERGED: {exc}", file=out)
        return 1
    if got != receipt["output_sha256"]:
        print(f"DIVERGED: reproduced {got}, receipt claims "
              f"{receipt['output_sha256']}", file=out)
        return 1
    print(f"REPRODUCED: {receipt['output_sha256']}  "
          f"(bundle {receipt['bundle_id'][:23]}…, one re-run)", file=out)
    return 0


def make_manifest(bundle_dir: str, timeout_s: int = 30) -> dict:
    """Author-side helper: hash what is on disk into a manifest. The
    trust story never depends on this — check_bundle re-verifies."""
    inputs = {}
    inputs_dir = os.path.join(bundle_dir, "inputs")
    if os.path.isdir(inputs_dir):
        for root, _dirs, files in os.walk(inputs_dir):
            for f in sorted(files):
                full = os.path.join(root, f)
                inputs[os.path.relpath(full, bundle_dir)] = _sha256_file(full)
    return {
        "spec": SPEC,
        "entry_sha256": _sha256_file(os.path.join(bundle_dir, "entry.py")),
        "inputs": inputs,
        "interpreter": "python3",
        "timeout_s": timeout_s,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("bundle")
    p_run.add_argument("--receipt", default=None)
    p_ver = sub.add_parser("verify")
    p_ver.add_argument("bundle")
    p_ver.add_argument("receipt")
    args = ap.parse_args(argv)

    if args.cmd == "run":
        try:
            receipt = run(args.bundle)
        except RunRefused as exc:
            print(f"REFUSED: {exc}")
            return 1
        text = canonical_json(receipt)
        print(f"receipt {receipt_id(receipt)}")
        print(text)
        if args.receipt:
            with open(args.receipt, "w", encoding="ascii") as fh:
                fh.write(text + "\n")
        return 0

    try:
        receipt = json.load(open(args.receipt, encoding="ascii"))
    except Exception as exc:
        print(f"MALFORMED: unreadable receipt: {exc}")
        return 2
    return verify(args.bundle, receipt)


if __name__ == "__main__":
    raise SystemExit(main())
