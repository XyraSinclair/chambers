#!/usr/bin/env python3
"""Verify a finalized Chamber court file.

usage: check_court_file.py <run_dir> [--expect-manifest-root sha256:<hex>]

Two verdicts, deliberately distinct:

- unanchored (no flag): the court is INTERNALLY CONSISTENT — every exhibit
  byte matches the court's own manifest, and the semantic story replays.
  An attacker who controls the directory could have rewritten the manifest
  along with the exhibits, so this is not authentication.
- anchored (--expect-manifest-root): the whole bundle, manifest included,
  hashes to an externally supplied root captured at finalization and
  delivered out of band. This is exact byte authentication against a
  trust anchor the directory cannot forge.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from chambers.kernel import Ledger as KernelLedger
except ModuleNotFoundError:  # support running from inside chambers/
    from kernel import Ledger as KernelLedger  # type: ignore


REQUIRED_JSON = [
    "grant.json",
    "transform.json",
    "run.json",
    "environment_recipe.json",
    "release_docket.json",
    "receipt.json",
]

REQUIRED_JSONL = [
    "artifacts.jsonl",
    "reviews.jsonl",
    "emissions.jsonl",
    "run_claims.jsonl",
    "ledger.jsonl",
    "charge_kernel_ledger.jsonl",
]

USAGE = "usage: check_court_file.py <run_dir> [--expect-manifest-root sha256:<hex>]"

# The court-manifest convention. chamber.py imports these; this module must
# never import chamber.py (the verifier stays independent of the writer).
COURT_MANIFEST_NAME = "court_manifest.json"
COURT_MANIFEST_VERSION = 1
_SHA256_FORMAT = re.compile(r"sha256:[0-9a-f]{64}")


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8", errors="replace")
    return sha256_bytes(blob)


def court_manifest_entries(run_dir: Path) -> List[Dict[str, str]]:
    """Inventory rows for the manifest file: every regular file directly
    under run_dir except the manifest itself (a file cannot commit to its
    own bytes), sorted by fileName."""
    return [
        {"fileName": path.name, "sha256": sha256_bytes(path.read_bytes())}
        for path in sorted(run_dir.iterdir(), key=lambda p: p.name)
        if path.is_file() and path.name != COURT_MANIFEST_NAME
    ]


def court_manifest_root(run_dir: Path) -> str:
    """The whole-bundle trust anchor: the canonical JSON hash of the
    {fileName, sha256} rows of every regular file directly under run_dir —
    manifest INCLUDED — sorted by fileName. Captured at finalization and
    handed to counterparties out of band, never inside the court."""
    entries = [
        {"fileName": path.name, "sha256": sha256_bytes(path.read_bytes())}
        for path in sorted(run_dir.iterdir(), key=lambda p: p.name)
        if path.is_file()
    ]
    return sha256_json(entries)


def fail(message: str) -> "NoReturn":
    print(f"check_court_file: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - surfaced as CLI failure
        fail(f"{path.name} is not valid JSON: {exc}")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        for idx, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                fail(f"{path.name}:{idx} must be a JSON object")
            rows.append(value)
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - surfaced as CLI failure
        fail(f"{path.name} is not valid JSONL: {exc}")
    return rows


def ensure(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def artifact_ids(rows: List[Dict[str, Any]]) -> set[str]:
    return {str(row.get("id") or "") for row in rows}


def review_ids(rows: List[Dict[str, Any]]) -> set[str]:
    return {str(row.get("id") or "") for row in rows}


def verify_exact_integrity(run_dir: Path, expect_root: Optional[str]) -> None:
    """Exact raw-byte law: the court is a closed exhibit list, not a
    directory that happens to contain one. Convicts byte tampering, missing
    or planted files, malformed/duplicate/traversing manifest entries, and
    symlinks. With expect_root, additionally authenticates the whole bundle
    (manifest included) against the externally supplied trust anchor."""
    names_on_disk: set[str] = set()
    for path in sorted(run_dir.iterdir(), key=lambda p: p.name):
        ensure(not path.is_symlink(), f"court dir must not contain symlinks: {path.name}")
        ensure(path.is_file(), f"court dir must contain only regular files: {path.name}")
        names_on_disk.add(path.name)
    ensure(COURT_MANIFEST_NAME in names_on_disk, f"missing {COURT_MANIFEST_NAME}")

    manifest = load_json(run_dir / COURT_MANIFEST_NAME)
    ensure(isinstance(manifest, dict), f"{COURT_MANIFEST_NAME} must be a JSON object")
    ensure(
        manifest.get("version") == COURT_MANIFEST_VERSION,
        f"{COURT_MANIFEST_NAME} version must be {COURT_MANIFEST_VERSION}",
    )
    entries = manifest.get("entries")
    ensure(isinstance(entries, list) and bool(entries), f"{COURT_MANIFEST_NAME} entries must be a non-empty array")

    recorded: List[str] = []
    for idx, entry in enumerate(entries, start=1):
        ensure(
            isinstance(entry, dict) and set(entry) == {"fileName", "sha256"},
            f"{COURT_MANIFEST_NAME} entry {idx} must be an object with exactly fileName and sha256",
        )
        name = entry["fileName"]
        digest = entry["sha256"]
        ensure(
            isinstance(name, str)
            and name not in {"", ".", ".."}
            and not any(bad in name for bad in ("/", "\\", "\x00")),
            f"{COURT_MANIFEST_NAME} entry {idx} fileName is not a plain file name: {name!r}",
        )
        ensure(name != COURT_MANIFEST_NAME, f"{COURT_MANIFEST_NAME} must not list itself")
        ensure(
            isinstance(digest, str) and bool(_SHA256_FORMAT.fullmatch(digest)),
            f"{COURT_MANIFEST_NAME} entry {idx} sha256 must be sha256:<64 lowercase hex>",
        )
        recorded.append(name)
    ensure(
        all(a < b for a, b in zip(recorded, recorded[1:])),
        f"{COURT_MANIFEST_NAME} entries must be strictly sorted by fileName with no duplicates",
    )

    for entry in entries:
        name = entry["fileName"]
        ensure(name in names_on_disk, f"recorded exhibit is missing: {name}")
        actual = sha256_bytes((run_dir / name).read_bytes())
        ensure(
            actual == entry["sha256"],
            f"exhibit bytes do not match manifest: {name} recorded {entry['sha256']} actual {actual}",
        )

    planted = names_on_disk - {COURT_MANIFEST_NAME} - set(recorded)
    ensure(not planted, f"unrecorded files planted in court dir: {sorted(planted)}")

    if expect_root is not None:
        actual_root = court_manifest_root(run_dir)
        ensure(
            actual_root == expect_root,
            f"manifest root mismatch: expected {expect_root} actual {actual_root}",
        )


def main(argv: List[str]) -> int:
    expect_root: Optional[str] = None
    positional: List[str] = []
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--expect-manifest-root":
            ensure(expect_root is None and i + 1 < len(args), USAGE)
            expect_root = args[i + 1]
            i += 2
        elif args[i].startswith("-"):
            fail(USAGE)
        else:
            positional.append(args[i])
            i += 1
    if len(positional) != 1:
        fail(USAGE)
    if expect_root is not None:
        ensure(
            bool(_SHA256_FORMAT.fullmatch(expect_root)),
            "--expect-manifest-root must be sha256:<64 lowercase hex>",
        )
    run_dir = Path(positional[0]).expanduser().resolve()
    ensure(run_dir.is_dir(), f"run dir does not exist: {run_dir}")

    verify_exact_integrity(run_dir, expect_root)

    for name in REQUIRED_JSON + REQUIRED_JSONL:
        ensure((run_dir / name).exists(), f"missing {name}")

    grant = load_json(run_dir / "grant.json")
    transform = load_json(run_dir / "transform.json")
    run = load_json(run_dir / "run.json")
    _environment = load_json(run_dir / "environment_recipe.json")
    release = load_json(run_dir / "release_docket.json")
    receipt = load_json(run_dir / "receipt.json")

    artifacts = load_jsonl(run_dir / "artifacts.jsonl")
    reviews = load_jsonl(run_dir / "reviews.jsonl")
    emissions = load_jsonl(run_dir / "emissions.jsonl")
    claims = load_jsonl(run_dir / "run_claims.jsonl")
    ledger = load_jsonl(run_dir / "ledger.jsonl")
    kernel_text = (run_dir / "charge_kernel_ledger.jsonl").read_text(encoding="utf-8")
    kernel_ledger = KernelLedger.from_jsonl(kernel_text)
    kernel_audit = kernel_ledger.audit()
    ensure(not kernel_audit, f"charge_kernel_ledger.jsonl audit findings: {kernel_audit}")
    ensure(kernel_ledger.to_jsonl() == kernel_text, "charge_kernel_ledger.jsonl is not canonical JSONL")
    ensure(kernel_ledger.event_count() > 0, "charge_kernel_ledger.jsonl must not be empty")

    ensure(str(run.get("grantId") or "") == str(grant.get("id") or ""), "run.json grantId does not reference grant.json")
    ensure(str(run.get("transformId") or "") == str(transform.get("id") or ""), "run.json transformId does not reference transform.json")

    ensure(bool(ledger), "ledger.jsonl must not be empty")
    seen_ledger: set[str] = set()
    previous_id = ""
    for idx, entry in enumerate(ledger, start=1):
        entry_id = str(entry.get("id") or "")
        ensure(entry_id, f"ledger.jsonl:{idx} missing id")
        ensure(entry_id not in seen_ledger, f"ledger.jsonl has duplicate id: {entry_id}")
        parents = entry.get("causalParentIds")
        ensure(isinstance(parents, list), f"ledger.jsonl:{idx} causalParentIds must be a list")
        for parent in parents:
            ensure(str(parent) in seen_ledger, f"ledger.jsonl:{idx} references unknown parent {parent}")
        if previous_id:
            ensure(previous_id in parents, f"ledger.jsonl:{idx} does not chain to previous entry {previous_id}")
        else:
            ensure(not parents, "first ledger entry must have an empty causalParentIds list")
        seen_ledger.add(entry_id)
        previous_id = entry_id
    ensure(str(run.get("ledgerTailId") or "") == previous_id, "run.json ledgerTailId does not match the final ledger entry")

    ensure(bool(claims), "run_claims.jsonl must not be empty")
    predicates = {str(claim.get("predicate") or "") for claim in claims}
    ensure("not_a_privacy_proof" in predicates, "run_claims.jsonl must include a not_a_privacy_proof claim")
    for idx, claim in enumerate(claims, start=1):
        support = claim.get("support")
        ensure(isinstance(support, list) and bool(support), f"run_claims.jsonl:{idx} support must be a non-empty array")

    caveats = receipt.get("caveats")
    ensure(isinstance(caveats, list) and bool(caveats), "receipt.json caveats must be a non-empty array")
    caveat_codes = {str(item.get("code") or "") for item in caveats if isinstance(item, dict)}
    ensure("not_semantic_proof" in caveat_codes, "receipt.json caveats must include not_semantic_proof")
    ensure(receipt.get("noPerfectSecrecyClaim") is True, "receipt.json noPerfectSecrecyClaim must be true")

    ledger_ids = {str(entry.get("id") or "") for entry in ledger}
    for idx, emission in enumerate(emissions, start=1):
        ledger_entry_id = str(emission.get("ledgerEntryId") or "")
        ensure(ledger_entry_id in ledger_ids, f"emissions.jsonl:{idx} references missing ledgerEntryId {ledger_entry_id}")

    art_ids = artifact_ids(artifacts)
    rev_ids = review_ids(reviews)
    candidate_artifact_id = str(release.get("candidateArtifactId") or "")
    if candidate_artifact_id:
        ensure(candidate_artifact_id in art_ids, "release_docket.json candidateArtifactId does not reference an artifact record")
    receipt_artifact_id = str(release.get("receiptArtifactId") or "")
    if receipt_artifact_id:
        ensure(receipt_artifact_id in art_ids, "release_docket.json receiptArtifactId does not reference an artifact record")
    for review_id in list(release.get("reviewerIds") or []):
        ensure(str(review_id) in rev_ids, f"release_docket.json reviewerId does not reference a review record: {review_id}")

    integrity = (
        "exact bytes authenticated against supplied manifest root"
        if expect_root is not None
        else "internally consistent with its own manifest (unanchored: not authentication; supply --expect-manifest-root to authenticate)"
    )
    print(
        f"court file ok: {integrity}; "
        f"ledger={len(ledger)} "
        f"artifacts={len(artifacts)} "
        f"reviews={len(reviews)} "
        f"emissions={len(emissions)} "
        f"claims={len(claims)} "
        f"kernel_events={kernel_ledger.event_count()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
