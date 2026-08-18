# Guest transform contract — corpus revival demo

You are writing `guest.py`: a third-party transform that will run CONFINED
over a private corpus packet you will never see. You get this spec, the sink
schema (`sink_schema.py`), and nothing else. The confinement harness — not
your good manners — is the security boundary; write the best transform you
can inside the contract.

## The task your transform performs

The packet enumerates ~24 "abandoned idea" candidates mined from the owner's
private corpus (old conversations/notes scored high on originality and
ambition but inactive since). The owner's question: **which three are most
worth reviving now, given what the owner is currently building** (described
in `packet["context"]`). Your job is judgment quality: pick the 3 with the
strongest case, ranked, each with the single best-fitting reason code and an
honest confidence bucket.

## Interface (exact)

Define exactly this function at module top level in `guest.py`:

```python
def run(packet: dict, llm) -> dict: ...
```

- `packet = {"question": str, "context": str,
   "candidates": [{"id": str, "title": str, "slice": str}, ...]}`
  Candidate `id`s are opaque per-run tokens. `slice` is a bounded excerpt
  (~1000 chars). Candidate count may vary (>= 3); do not hardcode 24.
- `llm(prompt: str, max_tokens: int = 1024) -> str` — your ONLY effectful
  capability. Calls a strong chat model. HARD BUDGET: at most 40 calls per
  run, at most 60,000 characters of total prompt across the run; the harness
  kills the run past either. Budget with headroom; do not spend to the cap.
- Return value: a verdict dict conforming EXACTLY to `sink_schema.py`:
  `{"picks": [{"candidate_id", "reason", "confidence"}, ...]}` — 3 picks,
  ranked most-worth-reviving first, distinct candidate_ids from the packet,
  reason from REASON_CODES, confidence from CONFIDENCE. Any deviation is
  recorded as `rejected_schema` and you get nothing for it.

## Constraints (enforced, not requested)

- Python 3.11+ stdlib ONLY. No third-party imports.
- No network, no subprocess, no filesystem writes, no environment reads.
  The harness strips env, denies network at the OS level, and runs you in a
  throwaway directory. Attempting any of it wastes your run.
- Deterministic control flow please: no wall-clock branching, no randomness
  without a fixed seed. (The llm is the only nondeterminism you need.)
- Robustness is on you: the llm returns free text; parse defensively;
  never let one malformed model reply crash the whole run. If the model
  gives you garbage, retry that step once with a tightened prompt, then
  degrade gracefully (a heuristic fallback beats a crash).

## Quality bar (what "crushing it" looks like)

A two-stage strategy outperforms one giant prompt: (1) cheap per-candidate
or per-batch screening against the context to shortlist ~8, (2) a careful
comparative ranking pass over the shortlist with the full slices, forcing
trade-off reasoning ("which of these two, and why") rather than independent
scores. Make the model justify reason-code choice per pick from the fixed
taxonomy; map its justification to the closest code yourself rather than
trusting it to emit valid enum values. Emit strict JSON at the end from
YOUR code, never from raw model output.

Return raw data only — the harness never shows your prose to anyone.
