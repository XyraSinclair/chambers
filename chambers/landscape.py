"""Executable repository map and no-regression ratchets.

    python3 -m chambers.landscape show
    python3 -m chambers.landscape check
    python3 -m chambers.landscape hotspots
    python3 -m chambers.landscape format

The code is intentionally stdlib-only.  It verifies topology and evidence
pointers; the test, Rust, and Lean jobs verify behavior.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence

SCHEMA = "chambers-landscape/1"
MANIFEST = "LANDSCAPE.json"
ROOT = Path(__file__).resolve().parents[1]
KINDS = frozenset({"canon", "conformance", "economy", "kernel", "proof", "runtime"})
IGNORED_DIRS = frozenset({".git", ".lake", ".pytest_cache", "__pycache__", "out", "target"})
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    subject: str
    detail: str

    def render(self) -> str:
        return f"{self.code}: {self.subject}: {self.detail}"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def add(findings: list[Finding], code: str, subject: str, detail: str) -> None:
    findings.append(Finding(code, subject, detail))


def relative(value: Any, subject: str, findings: list[Finding]) -> Optional[str]:
    if not isinstance(value, str) or not value or "\\" in value:
        add(findings, "PATH_INVALID", subject, "expected a normalized relative path")
        return None
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != value
        or value.startswith("./")
    ):
        add(findings, "PATH_INVALID", subject, "path must stay inside the repository")
        return None
    return value


def require_path(
    root: Path,
    value: Any,
    subject: str,
    findings: list[Finding],
    kind: str = "any",
) -> Optional[str]:
    value = relative(value, subject, findings)
    if value is None:
        return None
    path = root.joinpath(*PurePosixPath(value).parts)
    if not path.exists():
        add(findings, "PATH_MISSING", value, subject)
    elif kind == "file" and not path.is_file():
        add(findings, "PATH_NOT_FILE", value, subject)
    elif kind == "dir" and not path.is_dir():
        add(findings, "PATH_NOT_DIRECTORY", value, subject)
    return value


def object_list(
    data: Mapping[str, Any],
    key: str,
    findings: list[Finding],
) -> list[Mapping[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        add(findings, "SHAPE_INVALID", key, "expected an array of objects")
        return []
    return value


def unique(values: Sequence[str], subject: str, findings: list[Finding]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            add(findings, "DUPLICATE", value, subject)
        seen.add(value)


def actual_children(root: Path, parent: str, directories_only: bool) -> set[str]:
    base = root / parent
    if not base.is_dir():
        return set()
    answer = set()
    for item in base.iterdir():
        if item.name.startswith(".") or item.name in IGNORED_DIRS:
            continue
        if directories_only and not item.is_dir():
            continue
        answer.add(f"{parent}/{item.name}")
    return answer


def audit_components(
    root: Path,
    components: list[Mapping[str, Any]],
    findings: list[Finding],
) -> None:
    ids: list[str] = []
    paths: list[str] = []
    for index, component in enumerate(components):
        subject = f"components[{index}]"
        component_id = component.get("id")
        if not isinstance(component_id, str) or not ID_RE.fullmatch(component_id):
            add(findings, "FIELD_INVALID", f"{subject}.id", "use lowercase kebab-case")
        else:
            ids.append(component_id)

        if component.get("kind") not in KINDS:
            add(findings, "FIELD_INVALID", f"{subject}.kind", f"expected one of {sorted(KINDS)}")
        if not isinstance(component.get("summary"), str) or not component.get("summary"):
            add(findings, "FIELD_INVALID", f"{subject}.summary", "expected non-empty text")

        path = require_path(root, component.get("path"), f"{subject}.path", findings, "dir")
        if path is not None:
            if len(PurePosixPath(path).parts) != 2 or not path.startswith("chambers/"):
                add(findings, "COMPONENT_PATH_INVALID", path, "name one chambers/ root directory")
            paths.append(path)

        entrypoints = component.get("entrypoints")
        if not isinstance(entrypoints, list) or not entrypoints:
            add(findings, "ENTRYPOINT_MISSING", str(component_id), "declare a runnable command")
        else:
            for entry_index, entry in enumerate(entrypoints):
                entry_subject = f"{subject}.entrypoints[{entry_index}]"
                if not isinstance(entry, Mapping):
                    add(findings, "SHAPE_INVALID", entry_subject, "expected an object")
                    continue
                if not isinstance(entry.get("command"), str) or not entry.get("command"):
                    add(findings, "FIELD_INVALID", f"{entry_subject}.command", "expected text")
                require_path(root, entry.get("target"), f"{entry_subject}.target", findings)

        evidence = component.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            add(findings, "EVIDENCE_MISSING", str(component_id), "declare evidence paths")
        else:
            for evidence_index, evidence_path in enumerate(evidence):
                require_path(root, evidence_path, f"{subject}.evidence[{evidence_index}]", findings)

    unique(ids, "component ids", findings)
    unique(paths, "component paths", findings)
    if ids != sorted(ids):
        add(findings, "ORDER_INVALID", "components", "sort by id")

    declared = set(paths)
    actual = actual_children(root, "chambers", directories_only=True)
    for path in sorted(actual - declared):
        add(findings, "COMPONENT_UNDECLARED", path, "add it to LANDSCAPE.json")
    for path in sorted(declared - actual):
        add(findings, "COMPONENT_STALE", path, "not a chambers/ root directory")


def audit_documentation(
    root: Path,
    documentation: list[Mapping[str, Any]],
    findings: list[Finding],
) -> None:
    paths: list[str] = []
    for index, item in enumerate(documentation):
        subject = f"documentation[{index}]"
        path = require_path(root, item.get("path"), f"{subject}.path", findings)
        if path is not None:
            if len(PurePosixPath(path).parts) != 2 or not path.startswith("docs/"):
                add(findings, "DOCUMENT_PATH_INVALID", path, "name one docs/ root entry")
            paths.append(path)
        if not isinstance(item.get("role"), str) or not item.get("role"):
            add(findings, "FIELD_INVALID", f"{subject}.role", "expected non-empty text")

    unique(paths, "documentation paths", findings)
    if paths != sorted(paths):
        add(findings, "ORDER_INVALID", "documentation", "sort by path")

    declared = set(paths)
    actual = actual_children(root, "docs", directories_only=False)
    for path in sorted(actual - declared):
        add(findings, "DOCUMENT_UNDECLARED", path, "add it to LANDSCAPE.json")
    for path in sorted(declared - actual):
        add(findings, "DOCUMENT_STALE", path, "not a docs/ root entry")


def ignored(path: Path) -> bool:
    return any(part.startswith(".") or part in IGNORED_DIRS for part in path.parts)


def cargo_crates(root: Path) -> set[str]:
    crates: set[str] = set()
    base = root / "chambers"
    if not base.is_dir():
        return crates
    for manifest in base.rglob("Cargo.toml"):
        rel = manifest.relative_to(root)
        if not ignored(rel):
            crates.add(rel.parent.as_posix())
    return crates


def audit_implementations(
    root: Path,
    implementations: list[Mapping[str, Any]],
    findings: list[Finding],
) -> None:
    ids: list[str] = []
    paths: list[str] = []
    for index, item in enumerate(implementations):
        subject = f"independent_implementations[{index}]"
        implementation_id = item.get("id")
        if not isinstance(implementation_id, str) or not ID_RE.fullmatch(implementation_id):
            add(findings, "FIELD_INVALID", f"{subject}.id", "use lowercase kebab-case")
        else:
            ids.append(implementation_id)

        path = require_path(root, item.get("path"), f"{subject}.path", findings, "dir")
        if path is not None:
            paths.append(path)
            require_path(root, f"{path}/Cargo.toml", f"{subject} Cargo.toml", findings, "file")
            require_path(root, f"{path}/Cargo.lock", f"{subject} Cargo.lock", findings, "file")
        for key in ("spec", "test_command"):
            if not isinstance(item.get(key), str) or not item.get(key):
                add(findings, "FIELD_INVALID", f"{subject}.{key}", "expected non-empty text")

    unique(ids, "independent implementation ids", findings)
    unique(paths, "independent implementation paths", findings)
    if ids != sorted(ids):
        add(findings, "ORDER_INVALID", "independent_implementations", "sort by id")

    declared = set(paths)
    actual = cargo_crates(root)
    for path in sorted(actual - declared):
        add(findings, "CARGO_CRATE_UNDECLARED", path, "declare the Rust implementation")
    for path in sorted(declared - actual):
        add(findings, "CARGO_CRATE_STALE", path, "no Cargo.toml exists here")


def production_python(root: Path, prefixes: Sequence[str]) -> dict[str, int]:
    answer: dict[str, int] = {}
    base = root / "chambers"
    if not base.is_dir():
        return answer
    for path in base.rglob("*.py"):
        rel = path.relative_to(root)
        if ignored(rel) or path.name.startswith(tuple(prefixes)):
            continue
        answer[rel.as_posix()] = path.stat().st_size
    return answer


def audit_ratchets(root: Path, value: Any, findings: list[Finding]) -> None:
    if not isinstance(value, Mapping) or not isinstance(value.get("python"), Mapping):
        add(findings, "SHAPE_INVALID", "ratchets.python", "expected an object")
        return
    python = value["python"]
    default = python.get("default_max_bytes")
    prefixes = python.get("excluded_name_prefixes")
    caps = python.get("grandfathered_max_bytes")
    if not isinstance(default, int) or isinstance(default, bool) or default <= 0:
        add(findings, "FIELD_INVALID", "ratchets.python.default_max_bytes", "use a positive integer")
        return
    if not isinstance(prefixes, list) or not all(isinstance(v, str) and v for v in prefixes):
        add(findings, "FIELD_INVALID", "ratchets.python.excluded_name_prefixes", "use strings")
        return
    if not isinstance(caps, Mapping):
        add(findings, "FIELD_INVALID", "ratchets.python.grandfathered_max_bytes", "use an object")
        return

    clean_caps: dict[str, int] = {}
    for raw_path, cap in caps.items():
        path = relative(raw_path, "Python ratchet path", findings)
        if path is None:
            continue
        if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
            add(findings, "FIELD_INVALID", path, "ratchet ceiling must be a positive integer")
            continue
        clean_caps[path] = cap

    files = production_python(root, prefixes)
    for path, size in sorted(files.items()):
        cap = clean_caps.get(path, default)
        if size > cap:
            add(findings, "PYTHON_SIZE_CAP", path, f"{size} bytes exceeds ceiling {cap}")
        if path in clean_caps and size < cap:
            add(findings, "PYTHON_CAP_SLACK", path, f"tighten ceiling {cap} to current size {size}")
        if path in clean_caps and size <= default:
            add(findings, "PYTHON_GRANDFATHER_EXPIRED", path, f"now fits default ceiling {default}")
    for path in sorted(set(clean_caps) - set(files)):
        add(findings, "PYTHON_CAP_UNUSED", path, "path is absent or excluded from production scan")


def audit_manifest(root: Path, manifest: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(manifest, Mapping):
        return [Finding("SHAPE_INVALID", MANIFEST, "expected a JSON object")]

    if manifest.get("schema") != SCHEMA:
        add(findings, "SCHEMA_INVALID", "schema", f"expected {SCHEMA!r}")

    project = manifest.get("project")
    if not isinstance(project, Mapping):
        add(findings, "SHAPE_INVALID", "project", "expected an object")
    else:
        for key in ("name", "claim"):
            if not isinstance(project.get(key), str) or not project.get(key):
                add(findings, "FIELD_INVALID", f"project.{key}", "expected non-empty text")
        for key in ("canon", "machine_registry", "refusal_register", "spec_registry"):
            require_path(root, project.get(key), f"project.{key}", findings, "file")

    audit_components(root, object_list(manifest, "components", findings), findings)
    audit_documentation(root, object_list(manifest, "documentation", findings), findings)
    audit_implementations(
        root,
        object_list(manifest, "independent_implementations", findings),
        findings,
    )
    audit_ratchets(root, manifest.get("ratchets"), findings)
    return sorted(set(findings))


def load(root: Path) -> tuple[Optional[Any], list[Finding]]:
    path = root / MANIFEST
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [Finding("MANIFEST_UNREADABLE", MANIFEST, str(exc))]
    try:
        manifest = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [
            Finding("MANIFEST_PARSE", MANIFEST, f"line {exc.lineno}, column {exc.colno}: {exc.msg}")
        ]
    findings = []
    if text != canonical_json(manifest):
        findings.append(
            Finding("MANIFEST_NOT_CANONICAL", MANIFEST, "run `python3 -m chambers.landscape format`")
        )
    return manifest, findings


def audit_repository(root: Path = ROOT) -> list[Finding]:
    manifest, findings = load(root.resolve())
    if manifest is not None:
        findings.extend(audit_manifest(root.resolve(), manifest))
    return sorted(set(findings))


def table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    widths = [max([len(headers[i])] + [len(row[i]) for row in rows]) for i in range(len(headers))]
    print("  ".join(value.ljust(widths[i]) for i, value in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))


def show(root: Path) -> int:
    manifest, findings = load(root)
    if not isinstance(manifest, Mapping):
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    rows = []
    for component in manifest.get("components", []):
        if not isinstance(component, Mapping):
            continue
        entrypoints = component.get("entrypoints", [])
        command = ""
        if isinstance(entrypoints, list) and entrypoints and isinstance(entrypoints[0], Mapping):
            command = str(entrypoints[0].get("command", ""))
        rows.append(
            (
                str(component.get("kind", "")),
                str(component.get("id", "")),
                str(component.get("path", "")),
                command,
            )
        )
    table(("KIND", "COMPONENT", "PATH", "PRIMARY COMMAND"), rows)
    return 0


def hotspots(root: Path) -> int:
    manifest, findings = load(root)
    if not isinstance(manifest, Mapping):
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    python = manifest.get("ratchets", {}).get("python", {})
    if not isinstance(python, Mapping):
        print("SHAPE_INVALID: ratchets.python", file=sys.stderr)
        return 2
    default = int(python.get("default_max_bytes", 0))
    caps = python.get("grandfathered_max_bytes", {})
    prefixes = python.get("excluded_name_prefixes", [])
    if not isinstance(caps, Mapping) or not isinstance(prefixes, list):
        print("SHAPE_INVALID: Python ratchets", file=sys.stderr)
        return 2
    rows = []
    files = production_python(root, [v for v in prefixes if isinstance(v, str)])
    for path, size in sorted(files.items(), key=lambda item: (-item[1], item[0]))[:20]:
        cap = int(caps.get(path, default))
        rows.append((f"{size:,}", f"{cap:,}", "AT CAP" if size == cap else "within", path))
    table(("BYTES", "CEILING", "STATUS", "PRODUCTION PYTHON"), rows)
    return 0


def check(root: Path) -> int:
    findings = audit_repository(root)
    if findings:
        for finding in findings:
            print(finding.render())
        print(f"landscape convicted: {len(findings)} finding(s)")
        return 1
    manifest, _ = load(root)
    assert isinstance(manifest, Mapping)
    print(
        f"landscape clean: {len(manifest['components'])} components, "
        f"{len(manifest['documentation'])} docs entries, "
        f"{len(manifest['independent_implementations'])} Rust twins"
    )
    return 0


def format_manifest(root: Path) -> int:
    path = root / MANIFEST
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot format {MANIFEST}: {exc}", file=sys.stderr)
        return 2
    path.write_text(canonical_json(value), encoding="utf-8")
    print(f"formatted {MANIFEST}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect and verify the Chambers landscape.")
    parser.add_argument("command", nargs="?", choices=("check", "format", "hotspots", "show"), default="check")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "format":
        return format_manifest(root)
    if args.command == "hotspots":
        return hotspots(root)
    if args.command == "show":
        return show(root)
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
