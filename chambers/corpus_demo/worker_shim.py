"""Trusted shim that runs INSIDE the confined guest process.

Loads guest.py, exposes the llm callable as a JSON-lines RPC over
stdin/stdout to the harness (the guest process itself holds no credentials
and no network), runs guest.run(packet, llm), and emits the final verdict
as the last line, tagged.

Protocol (one JSON object per line, guest process -> harness on stdout):
  {"op": "llm", "prompt": str, "max_tokens": int}   -> harness replies on our
      stdin with {"ok": true, "text": str} or {"ok": false, "error": str}
  {"op": "done", "verdict": <dict>}                 -> terminal
  {"op": "fail", "error": str}                      -> terminal
"""
from __future__ import annotations

import json
import sys


def _rpc(obj: dict) -> dict:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()
    line = sys.stdin.readline()
    if not line:
        raise RuntimeError("harness closed the channel")
    return json.loads(line)


def main() -> None:
    packet_path, guest_path = sys.argv[1], sys.argv[2]
    with open(packet_path, "r", encoding="utf-8") as fh:
        packet = json.load(fh)

    def llm(prompt: str, max_tokens: int = 1024) -> str:
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")
        reply = _rpc({"op": "llm", "prompt": prompt, "max_tokens": int(max_tokens)})
        if not reply.get("ok"):
            raise RuntimeError(f"llm call refused: {reply.get('error')}")
        return str(reply.get("text", ""))

    import importlib.util

    spec = importlib.util.spec_from_file_location("guest", guest_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        verdict = module.run(packet, llm)
    except BaseException as exc:  # noqa: BLE001 - the failure IS the signal
        sys.stdout.write(json.dumps({"op": "fail", "error": f"{type(exc).__name__}: {exc}"}) + "\n")
        sys.stdout.flush()
        return
    sys.stdout.write(json.dumps({"op": "done", "verdict": verdict}) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
