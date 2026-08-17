"""Executable primary-source provenance for Chambers.

    python3 -m chambers.literature show
    python3 -m chambers.literature check
    python3 -m chambers.literature format

`LITERATURE.json` is the source of truth. `docs/LITERATURE.md` is a
deterministic human view. The checker is deliberately offline: it verifies
metadata shape, stable-locator syntax, repository targets, and render parity;
it does not turn transient network reachability into a build dependency.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence

SCHEMA = "chambers-literature/1"
REGISTRY = "LITERATURE.json"
RENDERED = "docs/LITERATURE.md"
ROOT = Path(__file__).resolve().parents[1]

RELATIONSHIPS = frozenset(
    {"adaptation", "comparison", "foundation", "implementation", "open-frontier"}
)
LOCATOR_KINDS = frozenset({"arxiv", "doi", "rfc", "url"})
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}(?:v\d+)?$")
RFC_RE = re.compile(r"^RFC([1-9]\d*)$")


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


def nonempty_text(
    value: Any, subject: str, findings: list[Finding]
) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        add(findings, "FIELD_INVALID", subject, "expected non-empty text")
        return None
    if value != value.strip():
        add(findings, "FIELD_INVALID", subject, "remove leading or trailing whitespace")
    return value


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


def unique(values: Sequence[str], subject: str, findings: list[Finding]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            add(findings, "DUPLICATE", value, subject)
        seen.add(value)


def audit_locator(
    source_id: str, value: Any, subject: str, findings: list[Finding]
) -> Optional[tuple[str, str]]:
    if not isinstance(value, Mapping):
        add(findings, "SHAPE_INVALID", subject, "expected an object")
        return None

    kind = value.get("kind")
    locator_value = value.get("value")
    url = value.get("url")
    if kind not in LOCATOR_KINDS:
        add(
            findings,
            "FIELD_INVALID",
            f"{subject}.kind",
            f"expected one of {sorted(LOCATOR_KINDS)}",
        )
        return None
    locator_value = nonempty_text(locator_value, f"{subject}.value", findings)
    url = nonempty_text(url, f"{subject}.url", findings)
    if locator_value is None or url is None:
        return None
    if not url.startswith("https://"):
        add(findings, "LOCATOR_URL_INVALID", source_id, "use an https primary-source URL")

    if kind == "doi":
        if not DOI_RE.fullmatch(locator_value):
            add(findings, "LOCATOR_VALUE_INVALID", source_id, "malformed DOI")
        expected = "https://doi.org/" + locator_value
        if url != expected:
            add(findings, "LOCATOR_URL_MISMATCH", source_id, f"expected {expected}")
    elif kind == "arxiv":
        if not ARXIV_RE.fullmatch(locator_value):
            add(findings, "LOCATOR_VALUE_INVALID", source_id, "malformed arXiv identifier")
        expected = "https://arxiv.org/abs/" + locator_value
        if url != expected:
            add(findings, "LOCATOR_URL_MISMATCH", source_id, f"expected {expected}")
    elif kind == "rfc":
        match = RFC_RE.fullmatch(locator_value)
        if match is None:
            add(findings, "LOCATOR_VALUE_INVALID", source_id, "use RFC followed by its number")
        else:
            expected = f"https://www.rfc-editor.org/rfc/rfc{match.group(1)}.html"
            if url != expected:
                add(findings, "LOCATOR_URL_MISMATCH", source_id, f"expected {expected}")
    elif locator_value != url:
        add(findings, "LOCATOR_VALUE_INVALID", source_id, "URL locators repeat the URL as value")

    return str(kind), locator_value


def audit_registry(root: Path, registry: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(registry, Mapping):
        return [Finding("SHAPE_INVALID", REGISTRY, "expected a JSON object")]
    if registry.get("schema") != SCHEMA:
        add(findings, "SCHEMA_INVALID", "schema", f"expected {SCHEMA!r}")

    sources = registry.get("sources")
    if not isinstance(sources, list) or not all(isinstance(v, Mapping) for v in sources):
        add(findings, "SHAPE_INVALID", "sources", "expected an array of objects")
        return sorted(set(findings))

    ids: list[str] = []
    locator_keys: list[str] = []
    for index, source in enumerate(sources):
        subject = f"sources[{index}]"
        source_id = source.get("id")
        if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id):
            add(findings, "FIELD_INVALID", f"{subject}.id", "use lowercase kebab-case")
            source_name = subject
        else:
            ids.append(source_id)
            source_name = source_id

        theme = source.get("theme")
        if not isinstance(theme, str) or not ID_RE.fullmatch(theme):
            add(findings, "FIELD_INVALID", f"{subject}.theme", "use lowercase kebab-case")

        authors = source.get("authors")
        if (
            not isinstance(authors, list)
            or not authors
            or not all(isinstance(author, str) and author.strip() == author and author for author in authors)
        ):
            add(findings, "FIELD_INVALID", f"{subject}.authors", "use a non-empty array of names")
        else:
            unique(authors, f"{source_name} authors", findings)

        year = source.get("year")
        if (
            not isinstance(year, int)
            or isinstance(year, bool)
            or year < 1900
            or year > 2100
        ):
            add(findings, "FIELD_INVALID", f"{subject}.year", "expected a four-digit publication year")

        for key in ("title", "venue", "import", "boundary"):
            nonempty_text(source.get(key), f"{subject}.{key}", findings)

        relationship = source.get("relationship")
        if relationship not in RELATIONSHIPS:
            add(
                findings,
                "FIELD_INVALID",
                f"{subject}.relationship",
                f"expected one of {sorted(RELATIONSHIPS)}",
            )

        locator = audit_locator(source_name, source.get("locator"), f"{subject}.locator", findings)
        if locator is not None:
            locator_keys.append(":".join(locator))

        applies_to = source.get("applies_to")
        if (
            not isinstance(applies_to, list)
            or not applies_to
            or not all(isinstance(path, str) for path in applies_to)
        ):
            add(findings, "FIELD_INVALID", f"{subject}.applies_to", "use a non-empty path array")
        else:
            clean_paths: list[str] = []
            for target_index, raw_path in enumerate(applies_to):
                path = relative(
                    raw_path,
                    f"{subject}.applies_to[{target_index}]",
                    findings,
                )
                if path is None:
                    continue
                clean_paths.append(path)
                if not root.joinpath(*PurePosixPath(path).parts).exists():
                    add(findings, "TARGET_MISSING", path, source_name)
            unique(clean_paths, f"{source_name} targets", findings)
            if clean_paths != sorted(clean_paths):
                add(findings, "ORDER_INVALID", f"{source_name} targets", "sort paths")

    unique(ids, "source ids", findings)
    unique(locator_keys, "stable locators", findings)
    if ids != sorted(ids):
        add(findings, "ORDER_INVALID", "sources", "sort by id")
    return sorted(set(findings))


def authors_text(authors: Sequence[str]) -> str:
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    return ", ".join(authors[:-1]) + f", and {authors[-1]}"


def target_link(path: str) -> str:
    href = path[5:] if path.startswith("docs/") else "../" + path
    return f"[`{path}`]({href})"


def locator_label(locator: Mapping[str, Any]) -> str:
    if locator.get("kind") == "url":
        return "Primary source"
    return str(locator.get("value", ""))


def render(registry: Mapping[str, Any]) -> str:
    sources = registry.get("sources", [])
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for source in sources:
        if isinstance(source, Mapping):
            grouped.setdefault(str(source.get("theme", "")), []).append(source)

    lines = [
        "# Literature Provenance",
        "",
        "> Generated from [`LITERATURE.json`](../LITERATURE.json) by",
        "> `python3 -m chambers.literature format`. Edit the registry, not this file.",
        "",
        "This map records which primary sources a Chambers surface is answerable to.",
        "It is intentionally stricter than a bibliography: every entry states the",
        "relationship, the exact import, the repository targets, and the boundary",
        "of what the citation does **not** establish. Citation is not theorem",
        "inheritance, implementation equivalence, or a novelty claim.",
        "",
        "## Relationship vocabulary",
        "",
        "- **foundation** — supplies a formal or conceptual basis used by the design.",
        "- **adaptation** — a named mechanism or theorem pattern is translated into",
        "  the Chambers setting.",
        "- **implementation** — the repository directly implements or uses the cited",
        "  standard or system.",
        "- **comparison** — locates an adjacent mechanism without claiming adoption.",
        "- **open-frontier** — names machinery being considered but not presently",
        "  claimed by the implementation.",
        "",
    ]

    for theme in sorted(grouped):
        lines.extend([f"## {theme.replace('-', ' ').title()}", ""])
        for source in sorted(
            grouped[theme],
            key=lambda value: (int(value["year"]), str(value["id"])),
        ):
            locator = source["locator"]
            target_text = ", ".join(target_link(path) for path in source["applies_to"])
            lines.extend(
                [
                    f"### {source['title']} ({source['year']})",
                    "",
                    f"{authors_text(source['authors'])}. *{source['title']}*. "
                    f"{source['venue']}. [{locator_label(locator)}]({locator['url']}).",
                    "",
                    f"**Relationship:** `{source['relationship']}`",
                    "",
                    f"**Applies to:** {target_text}",
                    "",
                    f"**Import:** {source['import']}",
                    "",
                    f"**Boundary:** {source['boundary']}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def load(root: Path) -> tuple[Optional[Any], list[Finding]]:
    path = root / REGISTRY
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [Finding("REGISTRY_UNREADABLE", REGISTRY, str(exc))]
    try:
        registry = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [
            Finding(
                "REGISTRY_PARSE",
                REGISTRY,
                f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
            )
        ]
    findings: list[Finding] = []
    if text != canonical_json(registry):
        findings.append(
            Finding(
                "REGISTRY_NOT_CANONICAL",
                REGISTRY,
                "run `python3 -m chambers.literature format`",
            )
        )
    return registry, findings


def audit_repository(root: Path = ROOT) -> list[Finding]:
    root = root.resolve()
    registry, findings = load(root)
    if isinstance(registry, Mapping):
        findings.extend(audit_registry(root, registry))
        expected = render(registry)
        rendered_path = root / RENDERED
        try:
            actual = rendered_path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(Finding("RENDERED_UNREADABLE", RENDERED, str(exc)))
        else:
            if actual != expected:
                findings.append(
                    Finding(
                        "RENDERED_STALE",
                        RENDERED,
                        "run `python3 -m chambers.literature format`",
                    )
                )
    return sorted(set(findings))


def table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    widths = [max([len(headers[i])] + [len(row[i]) for row in rows]) for i in range(len(headers))]
    print("  ".join(value.ljust(widths[i]) for i, value in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[i]) for i, value in enumerate(row)))


def show(root: Path) -> int:
    registry, findings = load(root)
    if not isinstance(registry, Mapping):
        for finding in findings:
            print(finding.render(), file=sys.stderr)
        return 2
    rows = []
    for source in registry.get("sources", []):
        if not isinstance(source, Mapping):
            continue
        rows.append(
            (
                str(source.get("relationship", "")),
                str(source.get("year", "")),
                str(source.get("id", "")),
                ", ".join(str(path) for path in source.get("applies_to", [])),
            )
        )
    table(("RELATION", "YEAR", "SOURCE", "REPOSITORY TARGETS"), rows)
    return 0


def check(root: Path) -> int:
    findings = audit_repository(root)
    if findings:
        for finding in findings:
            print(finding.render())
        print(f"literature convicted: {len(findings)} finding(s)")
        return 1
    registry, _ = load(root)
    assert isinstance(registry, Mapping)
    themes = {source["theme"] for source in registry["sources"]}
    targets = {
        target
        for source in registry["sources"]
        for target in source["applies_to"]
    }
    print(
        f"literature clean: {len(registry['sources'])} primary sources, "
        f"{len(themes)} themes, {len(targets)} repository targets"
    )
    return 0


def format_registry(root: Path) -> int:
    path = root / REGISTRY
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot format {REGISTRY}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(registry, Mapping):
        print(f"cannot format {REGISTRY}: expected a JSON object", file=sys.stderr)
        return 2
    path.write_text(canonical_json(registry), encoding="utf-8")
    rendered_path = root / RENDERED
    rendered_path.parent.mkdir(parents=True, exist_ok=True)
    rendered_path.write_text(render(registry), encoding="utf-8")
    print(f"formatted {REGISTRY} and {RENDERED}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect and verify Chambers' primary-source provenance."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("check", "format", "show"),
        default="check",
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "format":
        return format_registry(root)
    if args.command == "show":
        return show(root)
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main())
