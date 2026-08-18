"""Confinement canaries: the sandbox claims on the receipt must be
DEMONSTRATED, not asserted (probe-integrity discipline — a probe that
cannot go red proves nothing, so each canary asserts the malicious guest
is caught while the benign path stays green).

stdlib unittest; runs the real harness with an injected fake llm (no
network, no credentials needed) — safe for the sanctuary landing gate,
EXCEPT sandbox-exec is macOS-only, so network/write canaries skip
elsewhere (the skip is loud in the landing log, not silent).
"""
from __future__ import annotations

import json
import platform
import tempfile
import unittest
from pathlib import Path

from .harness import run_guest

HERE = Path(__file__).resolve().parent

PACKET = {
    "question": "q",
    "context": "ctx",
    "candidates": [
        {"id": f"c{i}", "title": f"t{i}", "slice": f"s{i}"} for i in range(4)
    ],
}

MACOS = platform.system() == "Darwin"


def _write_guest(body: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="canary-guest-"))
    p = d / "guest.py"
    p.write_text(body, encoding="utf-8")
    return p


def _packet_path() -> Path:
    d = Path(tempfile.mkdtemp(prefix="canary-packet-"))
    p = d / "packet.json"
    p.write_text(json.dumps(PACKET), encoding="utf-8")
    return p


def _fake_llm(prompt: str, max_tokens: int = 1024) -> str:
    return "c0"


class ConfinementCanaries(unittest.TestCase):
    def test_benign_guest_completes_green(self):
        guest = _write_guest(
            "def run(packet, llm):\n"
            "    _ = llm('hello')\n"
            "    ids = [c['id'] for c in packet['candidates'][:3]]\n"
            "    return {'picks': [{'candidate_id': i, 'reason': 'cheap_to_validate',"
            " 'confidence': 'low'} for i in ids]}\n"
        )
        res = run_guest(_packet_path(), guest, llm_fn=_fake_llm, sandbox=MACOS)
        self.assertEqual(res.outcome, "ok", res.error)
        self.assertEqual(len(res.verdict["picks"]), 3)

    @unittest.skipUnless(MACOS, "sandbox-exec is macOS-only; canary not run")
    def test_network_guest_is_denied(self):
        guest = _write_guest(
            "import urllib.request\n"
            "def run(packet, llm):\n"
            "    urllib.request.urlopen('https://example.com', timeout=5)\n"
            "    return {'picks': []}\n"
        )
        res = run_guest(_packet_path(), guest, llm_fn=_fake_llm, sandbox=True)
        self.assertEqual(res.outcome, "errored_worker")
        self.assertIsNotNone(res.error)

    @unittest.skipUnless(MACOS, "sandbox-exec is macOS-only; canary not run")
    def test_raw_socket_guest_is_denied(self):
        guest = _write_guest(
            "import socket\n"
            "def run(packet, llm):\n"
            "    s = socket.create_connection(('1.1.1.1', 443), timeout=5)\n"
            "    return {'picks': []}\n"
        )
        res = run_guest(_packet_path(), guest, llm_fn=_fake_llm, sandbox=True)
        self.assertEqual(res.outcome, "errored_worker")

    @unittest.skipUnless(MACOS, "sandbox-exec is macOS-only; canary not run")
    def test_filesystem_escape_write_is_denied(self):
        guest = _write_guest(
            "def run(packet, llm):\n"
            "    open('/tmp/canary-escape.txt', 'w').write('leak')\n"
            "    return {'picks': []}\n"
        )
        res = run_guest(_packet_path(), guest, llm_fn=_fake_llm, sandbox=True)
        self.assertEqual(res.outcome, "errored_worker")
        self.assertFalse(Path("/tmp/canary-escape.txt").exists())

    def test_env_is_stripped(self):
        guest = _write_guest(
            "import os\n"
            "def run(packet, llm):\n"
            "    assert 'OPENROUTER_API_KEY' not in os.environ, 'credential visible'\n"
            "    ids = [c['id'] for c in packet['candidates'][:3]]\n"
            "    return {'picks': [{'candidate_id': i, 'reason': 'cheap_to_validate',"
            " 'confidence': 'low'} for i in ids]}\n"
        )
        res = run_guest(_packet_path(), guest, llm_fn=_fake_llm, sandbox=MACOS)
        self.assertEqual(res.outcome, "ok", res.error)

    def test_call_budget_enforced(self):
        guest = _write_guest(
            "def run(packet, llm):\n"
            "    n = 0\n"
            "    try:\n"
            "        for _ in range(999):\n"
            "            llm('x'); n += 1\n"
            "    except RuntimeError:\n"
            "        pass\n"
            "    ids = [c['id'] for c in packet['candidates'][:3]]\n"
            "    return {'picks': [{'candidate_id': i, 'reason': 'cheap_to_validate',"
            " 'confidence': 'low'} for i in ids]}\n"
        )
        res = run_guest(_packet_path(), guest, llm_fn=_fake_llm, sandbox=MACOS)
        self.assertEqual(res.outcome, "ok", res.error)
        self.assertLessEqual(res.ledger.n_calls, 40)


if __name__ == "__main__":
    unittest.main()
