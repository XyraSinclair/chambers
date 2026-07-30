# carols_lib/parse.py — fixture: Carol's private library.
import re
import sys  # noqa: F401  <- finding: unused import (kind=dead_import)

PATTERN = re.compile(r"^[a-z]+$")


def parse(line):
    m = PATTERN.match(line)
    return m.group(0) if m else None
