"""The confinement harness: runs the guest, holds all credentials, meters
every crossing, denies the guest network at the OS level.

Trust map (states plainly what each party can and cannot do):
- guest.py (third-party code): sees packet + llm callable. Runs under macOS
  sandbox-exec with network DENIED and writes confined to its scratch dir;
  env stripped. Its only effectful capability is the proxied llm.
- harness (this file, owner-trusted): holds OPENROUTER_API_KEY, enforces the
  call/byte budgets, records the vendor-exposure ledger.
- worker endpoint (OpenRouter ZDR route): SEES the slices it is prompted
  with. Retention disclaimed contractually (data_collection=deny routing),
  not architecturally. This is the run's L4 line and it goes on the receipt.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent

MAX_LLM_CALLS = 40
MAX_PROMPT_CHARS = 60_000
GUEST_TIMEOUT_S = 600

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Preference order; the ZDR filter decides what actually serves. The receipt
# records the provider/model that DID serve, never just what we asked for.
MODEL_PREFERENCES = [
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-5.2",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-chat-v3.1",
]

SANDBOX_PROFILE = """
(version 1)
(deny default)
(allow process-exec)
(allow process-fork)
(allow signal (target self))
(allow sysctl-read)
(allow mach-lookup)
(allow file-read*)
(deny network*)
(allow file-write* (subpath "{scratch}"))
(allow file-write* (subpath "/private/var/folders"))
(allow file-write-data (path "/dev/null"))
(allow file-write-data (path "/dev/dtracehelper"))
"""


@dataclass
class ExposureLedger:
    """Declared-channel ledger for the vendor-exposure crossings: every llm
    call ships prompt bytes to the worker endpoint. Bytes are the honest
    unit here (no closed alphabet on this channel — it is prose by nature);
    the receipt states the contract, not a fake bit-precision."""

    calls: List[Dict] = field(default_factory=list)
    served_models: List[str] = field(default_factory=list)
    served_providers: List[str] = field(default_factory=list)

    @property
    def n_calls(self) -> int:
        return len(self.calls)

    @property
    def prompt_chars(self) -> int:
        return sum(c["prompt_chars"] for c in self.calls)

    @property
    def completion_chars(self) -> int:
        return sum(c["completion_chars"] for c in self.calls)


class BudgetExceeded(RuntimeError):
    pass


def _zdr_completion(prompt: str, max_tokens: int, ledger: ExposureLedger) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    last_error: Optional[str] = None
    for model in MODEL_PREFERENCES:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "provider": {"data_collection": "deny", "allow_fallbacks": True},
        }
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read().decode())
            text = payload["choices"][0]["message"]["content"]
            # Enrich the boundary-meter entry (appended by the proxy before
            # this client ran) — never append a second one.
            if ledger.calls:
                ledger.calls[-1].update(
                    model_requested=model,
                    model_served=payload.get("model", "?"),
                    provider_served=payload.get("provider", "?"),
                )
            if payload.get("model") not in ledger.served_models:
                ledger.served_models.append(payload.get("model", "?"))
            if payload.get("provider") not in ledger.served_providers:
                ledger.served_providers.append(payload.get("provider", "?"))
            return text or ""
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            last_error = f"{model}: HTTP {exc.code} {detail}"
            continue
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            last_error = f"{model}: {type(exc).__name__}: {exc}"
            continue
    raise RuntimeError(f"no ZDR-filtered model served the request; last: {last_error}")


@dataclass
class GuestResult:
    outcome: str  # sink_schema.OUTCOME_CODES member (harness-side view)
    verdict: Optional[dict]
    error: Optional[str]
    ledger: ExposureLedger
    guest_wall_s: float


def run_guest(
    packet_path: Path,
    guest_path: Path = HERE / "guest" / "guest.py",
    llm_fn=None,
    sandbox: bool = True,
) -> GuestResult:
    """Run the guest confined; mediate its llm calls; return the raw result.
    llm_fn injection exists for the synthetic dry-run (no network at all)."""
    ledger = ExposureLedger()
    llm = llm_fn or (lambda prompt, max_tokens: _zdr_completion(prompt, max_tokens, ledger))

    scratch = Path(tempfile.mkdtemp(prefix="corpus-demo-guest-"))
    argv = [
        sys.executable,
        str(HERE / "worker_shim.py"),
        str(packet_path),
        str(guest_path),
    ]
    if sandbox:
        profile = SANDBOX_PROFILE.format(scratch=scratch)
        argv = ["/usr/bin/sandbox-exec", "-p", profile] + argv

    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(scratch),
        "TMPDIR": str(scratch),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    }
    started = time.time()
    proc = subprocess.Popen(
        argv,
        cwd=scratch,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    outcome, verdict, error = "errored_worker", None, None
    try:
        deadline = started + GUEST_TIMEOUT_S
        while True:
            if time.time() > deadline:
                proc.kill()
                error = "guest timeout"
                break
            line = proc.stdout.readline()
            if not line:
                error = error or f"guest exited without terminal message (rc={proc.poll()})"
                break
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue  # stray guest print; ignore, never relay
            op = msg.get("op")
            if op == "llm":
                prompt = str(msg.get("prompt", ""))
                # The meter lives HERE, at the proxy boundary — every call is
                # counted and budget-checked BEFORE it ships, regardless of
                # which client (ZDR or injected test double) serves it.
                if ledger.n_calls + 1 > MAX_LLM_CALLS:
                    reply = {"ok": False, "error": "call budget exhausted"}
                elif ledger.prompt_chars + len(prompt) > MAX_PROMPT_CHARS:
                    reply = {"ok": False, "error": "prompt-byte budget exhausted"}
                else:
                    entry = {
                        "model_requested": None,
                        "model_served": "(injected)",
                        "provider_served": "(injected)",
                        "prompt_chars": len(prompt),
                        "completion_chars": 0,
                        "ts": time.time(),
                    }
                    ledger.calls.append(entry)
                    try:
                        text = llm(prompt, int(msg.get("max_tokens", 1024)))
                        entry["completion_chars"] = len(text or "")
                        reply = {"ok": True, "text": text}
                    except Exception as exc:  # surfaced to guest, recorded here
                        entry["error"] = f"{type(exc).__name__}: {exc}"
                        reply = {"ok": False, "error": entry["error"]}
                proc.stdin.write(json.dumps(reply) + "\n")
                proc.stdin.flush()
            elif op == "done":
                verdict = msg.get("verdict")
                outcome = "ok"
                break
            elif op == "fail":
                error = str(msg.get("error"))[:500]
                break
    finally:
        try:
            proc.kill()
        except OSError:
            pass
        proc.wait(timeout=10)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream:
                    stream.close()
            except OSError:
                pass

    return GuestResult(
        outcome=outcome,
        verdict=verdict,
        error=error,
        ledger=ledger,
        guest_wall_s=round(time.time() - started, 1),
    )
