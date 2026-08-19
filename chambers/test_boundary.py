"""The workbench boundary, enforced: maintained code never imports workbench.

AGENTS.md states the law — workbench code may import ``chambers.*``;
maintained code never imports ``workbench.*``. Deleting ``workbench/``
must leave every specification, proof, frozen corpus, and maintained
test intact. This lane makes the direction a failing test instead of a
sentence.
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+workbench\b", re.MULTILINE)


def test_maintained_code_never_imports_workbench() -> None:
    offenders = []
    for path in sorted((REPO / "chambers").rglob("*.py")):
        if IMPORT_RE.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(REPO)))
    assert offenders == [], (
        "maintained code imports workbench: " + ", ".join(offenders)
    )
