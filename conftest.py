"""Repo-root conftest: make `chambers.*` importable regardless of how
pytest is invoked (`python -m pytest` puts the cwd on sys.path; a bare
`pytest` binary does not — this file closes that gap canonically)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
