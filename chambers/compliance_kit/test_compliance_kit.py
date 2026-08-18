from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def test_manifest_is_fresh() -> None:
    proc = subprocess.run(
        [sys.executable, str(HERE / "make_kit.py"), "--print-manifest"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
    assert proc.stdout == (HERE / "MANIFEST.json").read_bytes()


def test_compliance_check() -> None:
    proc = subprocess.run(
        [sys.executable, str(HERE / "check.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout
