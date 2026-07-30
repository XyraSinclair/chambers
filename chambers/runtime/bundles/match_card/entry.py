"""The matchmaker's card projection as an R2 workload (RUNNER-SPEC §6).

Reads inputs/profile.json, computes the party story's 13-bit match card
(topic facet 6b + strength bucket 2b + why-safe line 5b), writes it as
canonical JSON to ./output. Deterministic by construction: all hashing
is sha256 (never Python's randomized hash()), all ordering explicit.
This is exactly the deterministic shell around the LLM that can ride
R2 — the projection step whose EMISSION the kernel meters.
"""
import hashlib
import json

TOPICS = 64      # 6 bits
BUCKETS = 4      # 2 bits
WHY_LINES = 32   # 5 bits


def h(s: str) -> int:
    return int.from_bytes(hashlib.sha256(s.encode("utf-8")).digest()[:8], "big")


profile = json.load(open("inputs/profile.json", encoding="utf-8"))

interests = sorted(profile["interests"])          # explicit order
topic = h("topic/" + interests[0]) % TOPICS
strength = min(len(interests), BUCKETS) - 1
why = h("why/" + profile["why_safe"]) % WHY_LINES

card = {
    "schema": "matchcard.schema_v1",
    "topic_facet": topic,
    "strength_bucket": strength,
    "why_safe_line": why,
    "bits": 13,
}
with open("output", "w", encoding="ascii") as fh:
    fh.write(json.dumps(card, sort_keys=True, separators=(",", ":")))
