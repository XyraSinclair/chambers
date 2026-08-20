#!/usr/bin/env python3
"""Assemble the Scry Chambers compliance kit.

The in-repo kit deliberately stores no copied spec or corpus bytes. This
script hashes the canonical sources in-place, writes MANIFEST.json, and can
assemble a self-contained distribution under --dist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

KIT_DIR = Path(__file__).resolve().parent
REPO_ROOT = KIT_DIR.parents[1]
MANIFEST_PATH = KIT_DIR / "MANIFEST.json"

CONTRACT = "your implementation is conforming iff these bytes replay"

SPEC_SOURCES = [
    {
        "source": "chambers/kernel/KERNEL-SPEC.md",
        "path": "specs/kernel/KERNEL-SPEC.md",
        "spec_versions": [
            "charge-ledger/1",
            "charge-substrate/1",
            "charge-provenance/1",
        ],
    },
    {
        "source": "chambers/kernel/SETTLEMENT-SPEC.md",
        "path": "specs/kernel/SETTLEMENT-SPEC.md",
        "spec_versions": ["charge-settlement/1", "charge-settlement/2"],
    },
    {
        "source": "chambers/kernel/SCOPE-SPEC.md",
        "path": "specs/kernel/SCOPE-SPEC.md",
        "spec_versions": ["charge-scope/1"],
    },
    {
        "source": "chambers/kernel/COVENANT-SPEC.md",
        "path": "specs/kernel/COVENANT-SPEC.md",
        "spec_versions": ["charge-covenant/1"],
    },
    {
        "source": "chambers/kernel/IDENTITY-SPEC.md",
        "path": "specs/kernel/IDENTITY-SPEC.md",
        "spec_versions": ["charge-identity/1", "charge-identity/2"],
    },
    {
        "source": "chambers/kernel/ATTRIBUTION-SPEC.md",
        "path": "specs/kernel/ATTRIBUTION-SPEC.md",
        "spec_versions": ["charge-attribution/1", "charge-attribution/2"],
    },
    {
        "source": "chambers/kernel/VIEWS-SPEC.md",
        "path": "specs/kernel/VIEWS-SPEC.md",
        "spec_versions": ["charge-views/1"],
    },
    {
        "source": "chambers/kernel/PROTOCOL.md",
        "path": "specs/kernel/PROTOCOL.md",
        "spec_versions": ["charge-kernel/2"],
    },
    {
        "source": "chambers/review_audit/PROBE-SPEC.md",
        "path": "specs/review_audit/PROBE-SPEC.md",
        "spec_versions": ["review-audit/1"],
    },
    {
        "source": "chambers/conformance/SPEC.md",
        "path": "specs/conformance/SPEC.md",
        "spec_versions": ["egress-accountant/1"],
    },
]

CORPUS_DIRS = {
    "chambers/kernel/ledger_traces": ["charge-ledger/1"],
    "chambers/kernel/settlement_traces": ["charge-settlement/1"],
    "chambers/kernel/settlement2_traces": ["charge-settlement/2"],
    "chambers/kernel/views_traces": ["charge-views/1"],
    "chambers/kernel/lean_traces": ["egress-accountant/1"],
}

PYTHON_VERIFIER_SOURCES = [
    "chambers/__init__.py",
    "chambers/kernel/__init__.py",
    "chambers/kernel/accountant.py",
    "chambers/kernel/attribution.py",
    "chambers/kernel/covenant.py",
    "chambers/kernel/events.py",
    "chambers/kernel/findings.py",
    "chambers/kernel/identity.py",
    "chambers/kernel/ledger.py",
    "chambers/kernel/settlement.py",
    "chambers/kernel/verify.py",
    "chambers/kernel/views.py",
]

RUST_VERIFIER_ROOT = "chambers/kernel/rust_ledger"
RUST_VERIFIER_FIXED = ["Cargo.toml", "Cargo.lock", "README.md"]


def _file_digest(path: Path) -> Dict[str, Any]:
    data = path.read_bytes()
    return {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _entry(source: str, kit_path: str, role: str, **meta: Any) -> Dict[str, Any]:
    path = REPO_ROOT / source
    if not path.is_file():
        raise FileNotFoundError(source)
    out: Dict[str, Any] = {
        "path": kit_path,
        "role": role,
        "source": source,
    }
    out.update(meta)
    out.update(_file_digest(path))
    return out


def _corpus_entries() -> Iterable[Dict[str, Any]]:
    for source_dir, specs in sorted(CORPUS_DIRS.items()):
        root = REPO_ROOT / source_dir
        if not root.is_dir():
            raise FileNotFoundError(source_dir)
        corpus = root.name
        for path in sorted(p for p in root.iterdir() if p.is_file()):
            rel_source = path.relative_to(REPO_ROOT).as_posix()
            yield _entry(
                rel_source,
                f"corpora/{corpus}/{path.name}",
                "corpus",
                corpus=corpus,
                spec_versions=specs,
            )


def _python_verifier_entries() -> Iterable[Dict[str, Any]]:
    for source in PYTHON_VERIFIER_SOURCES:
        rel = Path(source).relative_to("chambers")
        yield _entry(
            source,
            f"verifier/python/chambers/{rel.as_posix()}",
            "reference_verifier",
            verifier="python",
        )


def _rust_verifier_entries() -> Iterable[Dict[str, Any]]:
    root = REPO_ROOT / RUST_VERIFIER_ROOT
    for name in RUST_VERIFIER_FIXED:
        source = f"{RUST_VERIFIER_ROOT}/{name}"
        if (REPO_ROOT / source).is_file():
            yield _entry(
                source,
                f"verifier/rust_ledger/{name}",
                "reference_verifier",
                verifier="rust",
            )
    src_root = root / "src"
    if src_root.is_dir():
        for path in sorted(src_root.rglob("*.rs")):
            rel = path.relative_to(root).as_posix()
            source = f"{RUST_VERIFIER_ROOT}/{rel}"
            yield _entry(
                source,
                f"verifier/rust_ledger/{rel}",
                "reference_verifier",
                verifier="rust",
            )


def build_manifest() -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    for spec in SPEC_SOURCES:
        entries.append(
            _entry(
                spec["source"],
                spec["path"],
                "normative_spec",
                spec_versions=spec["spec_versions"],
            )
        )
    entries.extend(_corpus_entries())
    entries.extend(_python_verifier_entries())
    entries.extend(_rust_verifier_entries())
    entries.sort(key=lambda e: e["path"])
    return {
        "contract": CONTRACT,
        "entries": entries,
        "entry_count": len(entries),
        "generated_by": "chambers/compliance_kit/make_kit.py",
        "manifest_version": 1,
    }


def manifest_bytes() -> bytes:
    text = json.dumps(build_manifest(), indent=2, sort_keys=True, ensure_ascii=True)
    return (text + "\n").encode("ascii")


def write_manifest() -> None:
    MANIFEST_PATH.write_bytes(manifest_bytes())


def _hash_matches(path: Path, entry: Dict[str, Any]) -> bool:
    digest = _file_digest(path)
    return digest["bytes"] == entry["bytes"] and digest["sha256"] == entry["sha256"]


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def assemble_dist(dist: Path, force: bool = False) -> None:
    dist = dist.resolve()
    if dist == KIT_DIR or KIT_DIR in dist.parents:
        raise SystemExit("refusing to assemble a dist inside chambers/compliance_kit")
    if dist.exists():
        if any(dist.iterdir()):
            if not force:
                raise SystemExit(f"{dist} exists and is not empty; pass --force to replace it")
            shutil.rmtree(dist)
    dist.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest()
    manifest_data = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True)
    (dist / "MANIFEST.json").write_text(manifest_data + "\n", encoding="ascii")

    for name in ("README.md", "check.py", "make_kit.py"):
        _copy_file(KIT_DIR / name, dist / name)

    for entry in manifest["entries"]:
        src = REPO_ROOT / entry["source"]
        dst = dist / entry["path"]
        _copy_file(src, dst)
        if not _hash_matches(dst, entry):
            raise SystemExit(f"copy verification failed for {entry['path']}")

    print(f"assembled compliance kit: {dist}")
    print(f"verified copied manifest entries: {len(manifest['entries'])}")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-manifest", action="store_true", help="write manifest bytes to stdout")
    parser.add_argument("--check", action="store_true", help="exit nonzero if MANIFEST.json is stale")
    parser.add_argument("--dist", type=Path, help="assemble a self-contained copy at this directory")
    parser.add_argument("--force", action="store_true", help="replace an existing non-empty --dist directory")
    args = parser.parse_args(argv)

    data = manifest_bytes()
    if args.print_manifest:
        sys.stdout.buffer.write(data)
    if args.check:
        current = MANIFEST_PATH.read_bytes() if MANIFEST_PATH.exists() else b""
        if current != data:
            print("MANIFEST.json is stale", file=sys.stderr)
            return 1
        print("MANIFEST.json is fresh")
    if args.dist is not None:
        assemble_dist(args.dist, force=args.force)
    if not args.print_manifest and not args.check and args.dist is None:
        write_manifest()
        print(f"wrote {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
