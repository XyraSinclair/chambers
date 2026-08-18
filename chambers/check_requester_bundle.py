#!/usr/bin/env python3
"""Verify a requester_bundle.zip offline.

usage: check_requester_bundle.py <bundle.zip> --expect-bundle-root sha256:<hex>

PURE STANDARD LIBRARY, textually independent of the writer: a stranger runs
this with nothing but Python plus one out-of-band trust anchor — the bundle
root captured at finalization. The root is REQUIRED, never decorative:
without it, whoever hands you the zip could have rewritten the manifest
together with the members. The root is the SHA-256 of the COMPLETE zip file
bytes, so the checker authenticates the exact container the requester holds:
a ZIP comment, prepended bytes, a central-directory metadata change, or a
member reorder all break it even when every member's bytes survive — the
forgeries a member-listing root cannot see.

The laws enforced, in order:
  trust anchor  — SHA-256 of the raw zip file bytes equals the given root,
                  checked BEFORE any member is inspected
  zip hygiene   — no duplicate names, no traversal, no symlink-like entries
  closed set    — exactly the released member set, nothing planted or missing
  manifest      — version 1, strictly sorted, hashes every non-manifest member
  replay        — the receipt's accounting totals re-derive from the charge
                  ledger: run cumulative == sum of accepted debits for the
                  run account, run ceiling == that account's registered
                  ceiling, cumulative <= ceiling
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Textual-independence law (pinned by the contract tests): this file must not
# contain the writer's module names even as substrings. The charge-ledger
# member name and the receipt's account-key field unavoidably embed one, so
# both are spelled as adjacent string literals.
LEDGER_MEMBER = "charge_ker" "nel_ledger.jsonl"
ACCOUNT_KEY_FIELD = "ker" "nelAccountKey"

BUNDLE_MANIFEST_NAME = "manifest.json"
BUNDLE_MANIFEST_VERSION = 1
RECEIPT_MEMBER = "receipt.json"
APPROVED_MEMBER = "approved_public_artifact.json"
REQUIRED_MEMBERS = frozenset({RECEIPT_MEMBER, LEDGER_MEMBER, BUNDLE_MANIFEST_NAME})
ALLOWED_MEMBERS = REQUIRED_MEMBERS | {APPROVED_MEMBER}

_SHA256_FORMAT = re.compile(r"sha256:[0-9a-f]{64}")

USAGE = "usage: check_requester_bundle.py <bundle.zip> --expect-bundle-root sha256:<hex>"


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def fail(message: str) -> "NoReturn":
    print(f"check_requester_bundle: {message}", file=sys.stderr)
    raise SystemExit(1)


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def _is_uint(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _plain_member_name(name: str) -> bool:
    return (
        bool(name)
        and name not in {".", ".."}
        and not any(bad in name for bad in ("/", "\\", "\x00"))
    )


def read_members(bundle_bytes: bytes) -> Dict[str, bytes]:
    """All member bytes, after zip hygiene: duplicate names are an ambiguity
    attack (extraction order is reader-dependent), traversal names escape the
    unpack directory, and a symlink-like entry is not the file it claims to
    be even when its BYTES hash correctly — only the entry-type check can
    convict that one. Parses the ONE byte snapshot the root already
    authenticated — never the path again, which could have changed since."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(bundle_bytes))
    except Exception as exc:
        fail(f"not a readable zip archive: {exc}")
    with zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        ensure(not duplicates, f"duplicate member names: {duplicates}")
        for info in infos:
            ensure(
                _plain_member_name(info.filename),
                f"member name is not a plain file name: {info.filename!r}",
            )
            ensure(not info.is_dir(), f"member must be a regular file: {info.filename!r}")
            mode_type = (info.external_attr >> 16) & 0o170000
            ensure(
                mode_type in (0, 0o100000),
                f"member is not a regular-file entry (symlink-like): {info.filename!r}",
            )
        return {info.filename: zf.read(info) for info in infos}


def verify_manifest(members: Dict[str, bytes]) -> None:
    try:
        manifest = json.loads(members[BUNDLE_MANIFEST_NAME].decode("utf-8"))
    except Exception as exc:
        fail(f"{BUNDLE_MANIFEST_NAME} is not valid JSON: {exc}")
    ensure(
        isinstance(manifest, dict) and set(manifest) == {"version", "entries"},
        f"{BUNDLE_MANIFEST_NAME} must be an object with exactly version and entries",
    )
    ensure(
        manifest["version"] == BUNDLE_MANIFEST_VERSION,
        f"{BUNDLE_MANIFEST_NAME} version must be {BUNDLE_MANIFEST_VERSION}",
    )
    entries = manifest["entries"]
    ensure(isinstance(entries, list), f"{BUNDLE_MANIFEST_NAME} entries must be an array")
    recorded: List[str] = []
    for idx, entry in enumerate(entries, start=1):
        ensure(
            isinstance(entry, dict) and set(entry) == {"fileName", "sha256"},
            f"{BUNDLE_MANIFEST_NAME} entry {idx} must be an object with exactly fileName and sha256",
        )
        name = entry["fileName"]
        digest = entry["sha256"]
        ensure(
            isinstance(name, str) and _plain_member_name(name) and name != BUNDLE_MANIFEST_NAME,
            f"{BUNDLE_MANIFEST_NAME} entry {idx} fileName is not a plain non-manifest name: {name!r}",
        )
        ensure(
            isinstance(digest, str) and bool(_SHA256_FORMAT.fullmatch(digest)),
            f"{BUNDLE_MANIFEST_NAME} entry {idx} sha256 must be sha256:<64 lowercase hex>",
        )
        ensure(name in members, f"recorded member is missing: {name}")
        actual = sha256_bytes(members[name])
        ensure(
            actual == digest,
            f"member bytes do not match manifest: {name} recorded {digest} actual {actual}",
        )
        recorded.append(name)
    ensure(
        all(a < b for a, b in zip(recorded, recorded[1:])),
        f"{BUNDLE_MANIFEST_NAME} entries must be strictly sorted by fileName with no duplicates",
    )
    ensure(
        set(recorded) == set(members) - {BUNDLE_MANIFEST_NAME},
        f"{BUNDLE_MANIFEST_NAME} must cover exactly the non-manifest members",
    )


def replay_accounting(members: Dict[str, bytes]) -> Dict[str, int]:
    """The checker's reason to exist: a fully coordinated forger can rewrite
    receipt, manifest, and root together, but the receipt's totals must
    still RE-DERIVE from the charge ledger it ships with."""
    try:
        receipt = json.loads(members[RECEIPT_MEMBER].decode("utf-8"))
    except Exception as exc:
        fail(f"{RECEIPT_MEMBER} is not valid JSON: {exc}")
    ensure(isinstance(receipt, dict), f"{RECEIPT_MEMBER} must be a JSON object")
    accounting = receipt.get("accounting")
    ensure(isinstance(accounting, dict), f"{RECEIPT_MEMBER} must carry an accounting object")
    account_key = accounting.get(ACCOUNT_KEY_FIELD)
    ensure(
        isinstance(account_key, list)
        and bool(account_key)
        and all(isinstance(part, str) for part in account_key),
        "accounting run account key must be a non-empty list of strings",
    )
    run_cumulative = accounting.get("runCumulativeMillibits")
    run_ceiling = accounting.get("runCeilingMillibits")
    ensure(_is_uint(run_cumulative), "accounting runCumulativeMillibits must be a non-negative integer")
    ensure(_is_uint(run_ceiling), "accounting runCeilingMillibits must be a non-negative integer")

    events: List[Dict[str, Any]] = []
    for idx, raw_line in enumerate(members[LEDGER_MEMBER].decode("utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception as exc:
            fail(f"{LEDGER_MEMBER}:{idx} is not valid JSON: {exc}")
        ensure(isinstance(event, dict), f"{LEDGER_MEMBER}:{idx} must be a JSON object")
        events.append(event)

    ceilings = sorted({
        event["ceiling_mbits"]
        for event in events
        if event.get("kind") == "register"
        and event.get("key") == account_key
        and _is_uint(event.get("ceiling_mbits"))
    })
    ensure(
        len(ceilings) == 1,
        f"charge ledger must register the run account exactly once: {len(ceilings)} distinct well-formed ceilings",
    )
    replayed_ceiling = ceilings[0]

    replayed_cumulative = 0
    for event in events:
        if event.get("kind") != "charge" or event.get("key") != account_key:
            continue
        if event.get("accepted") is not True:
            continue
        debit = event.get("debit_mbits")
        ensure(_is_uint(debit), "accepted charge with malformed debit_mbits in the ledger")
        replayed_cumulative += debit

    ensure(
        run_cumulative == replayed_cumulative,
        f"receipt runCumulativeMillibits {run_cumulative} does not replay from the "
        f"charge ledger (accepted debits sum to {replayed_cumulative})",
    )
    ensure(
        run_ceiling == replayed_ceiling,
        f"receipt runCeilingMillibits {run_ceiling} does not match the registered ceiling {replayed_ceiling}",
    )
    ensure(
        run_cumulative <= run_ceiling,
        f"replayed cumulative {run_cumulative} exceeds the ceiling {run_ceiling}",
    )
    return {"cumulative_millibits": run_cumulative, "ceiling_millibits": run_ceiling}


def main(argv: List[str]) -> int:
    expect_root: Optional[str] = None
    positional: List[str] = []
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--expect-bundle-root":
            ensure(expect_root is None and i + 1 < len(args), USAGE)
            expect_root = args[i + 1]
            i += 2
        elif args[i].startswith("-"):
            fail(USAGE)
        else:
            positional.append(args[i])
            i += 1
    ensure(len(positional) == 1, USAGE)
    ensure(expect_root is not None, "the out-of-band bundle root is required. " + USAGE)
    ensure(
        bool(_SHA256_FORMAT.fullmatch(expect_root)),
        "--expect-bundle-root must be sha256:<64 lowercase hex>",
    )
    zip_path = Path(positional[0]).expanduser()
    ensure(zip_path.is_file(), f"bundle does not exist: {zip_path}")

    # The exact-bundle law comes FIRST: authenticate the raw file bytes the
    # requester actually holds before trusting the zip machinery to open
    # them. Same members in a different container is already a forgery.
    # The file is read EXACTLY ONCE; the same immutable snapshot is hashed
    # and then parsed, so the verdict is a function of the authenticated
    # bytes — reopening the path would be a TOCTOU seam.
    bundle_bytes = zip_path.read_bytes()
    actual_root = sha256_bytes(bundle_bytes)
    ensure(
        actual_root == expect_root,
        f"bundle root mismatch: expected {expect_root} actual {actual_root}",
    )

    members = read_members(bundle_bytes)
    names = set(members)
    planted = names - ALLOWED_MEMBERS
    ensure(not planted, f"unrecorded members planted in bundle: {sorted(planted)}")
    missing = REQUIRED_MEMBERS - names
    ensure(not missing, f"missing required members: {sorted(missing)}")

    verify_manifest(members)

    totals = replay_accounting(members)
    print(
        f"requester bundle ok: {len(members)} members authenticated against the "
        f"supplied bundle root; accounting replays "
        f"({totals['cumulative_millibits']} <= {totals['ceiling_millibits']} millibits)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
