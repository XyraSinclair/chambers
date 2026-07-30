# bobs_service/handlers.py — fixture: a private codebase Alice's agent sweeps.
import os
import json
import hashlib  # noqa: F401  <- finding: unused import (kind=dead_import)

API_TOKEN = "sk-live-9f8e7d6c5b4a3f2e1d0c"  # finding: hardcoded secret


def lookup(db, user_id):
    # finding: sql built by concatenation
    return db.execute("SELECT * FROM users WHERE id = '" + user_id + "'")


def render(payload):
    return json.dumps(payload)
