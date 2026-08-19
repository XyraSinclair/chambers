# IP-trade simulation

An executable embodiment of `docs/primitives/iptrade.ts`:
two labs with distinct, legitimate techniques try to trade IP. Agents appraise
each other's work against their own portfolio, negotiate a price, and settle —
all under a leakage accountant that enforces the hard rule: **you must observe a
technique to value it, but every observation leaks bits toward reconstructing
it, so meter it and block before theft.**

## What the simulation demonstrates

1. **Gains from trade on complementary portfolios.** Lab A (strong at
   long-context / inference-efficiency) and Lab B (strong at RL-from-AI-feedback
   / data-curation) each value the other's strengths and trade them; each values
   its own areas at ~0 marginal and does not.
2. **Verification catches inflated claims.** A technique whose *claimed* score
   exceeds its *true* score fails the attested result verdict and gets no offer —
   without the buyer ever seeing the method.
3. **Result-verification is the safe primitive.** Proving "scores ≥ X on your
   private eval" inside a (simulated) confidential enclave leaks a few bits; the
   method stays sealed. Full knowledge crosses only via a *paid* reveal after
   settlement.
4. **Leakage is metered and theft is blockable.** Every observation debits a
   composition budget keyed on (technique, observing-lab). Over-probing to steal
   (verification-as-extraction) trips the ceiling, is refused, and is flagged as
   an incident.
5. **Honest receipts.** Each lane emits a `PlainAccount`: what crossed, what did
   not, who was paid, and what the system cannot promise (results not methods;
   trusts the hardware vendor; the enclave saw both inputs; receipts aren't
   contracts).

## Module map

| File | Role | Owner |
|---|---|---|
| `types.py` | frozen data model, mirrors iptrade.ts | core (stable) |
| `leakage.py` | the leakage accountant — the crux | core (stable) |
| `engine.py` | the lane state machine (verify → appraise → negotiate → settle) | engine |
| `economics.py` | benchmark-normalized marginal valuation | engine |
| `price_debate.py` | multi-round price negotiation (metered) | engine |
| `courtfile.py` | per-lane sidecar writer + validator | engine |
| `strategies.py` | baseline valuation/pricing strategy fns | engine |
| `scenario.py` | the two labs and their techniques | scenario |
| `agents.py` | optional LLM/pluggable appraisal-reasoning mode | scenario |
| `hooks.py` | human-input handles (interactive / scripted policy) | scenario |
| `report.py` | narrative transcript writer | scenario |
| `run.py` | CLI entrypoint | scenario |

## The leakage model (why it is "smart about actual IP leakage")

Each `Technique` has `entropy_bits` (info to fully reconstruct the secret).
Channels leak toward that total at very different rates, and split into two
epistemic pools (the run prints them separately as the **protocol cut bound**,
CALCULUS.md §6):

- **result verdict** — DERIVED, not declared: the buyer observes one symbol
  from the closed codebook `{holds, not_met, blocked}` (`codebook.py`), so
  the charge is exactly log2 3 ≈ 1.585 bits regardless of the benchmark, the
  claim, or the verifier's honesty. A malicious verifier's only freedom is
  which symbol crosses — already paid for. `test_calculus_bound.py` plants a
  canary secret and shows an adversarial judge cannot exfiltrate past the
  meter, that blocking fires *before* the ceiling, and that blockage is
  simulatable from the public transcript (which is why `blocked` costs 0).
- **black-box probe** — declared estimate, proportional to query count (the
  distillation channel). No closed alphabet exists, so this stays an honest
  tripwire, not a theorem.
- **negotiation** — charged BEFORE anything publishes (a refused charge
  publishes nothing): 3.0 declared bits/side/round (the shared overlap bit
  plus mediator band-step guidance) and 6.0 bits/side for a cleared price.
  Raw ask/bid bands, the numeric gap, draws, and the seller's reserve never
  leave the silo — persisted transcripts carry commitments, the overlap
  bit, and the cleared price only.
- **method reveal** — ~all the entropy. Only legitimate *after payment*.

Two more perimeter rules from adversarial review: capability-binding
commitments are salted with the secret payload (an unsalted hash of
benchmark:score falls to a grid search by any courtfile reader), and the
shared receipt/court record never carries buyer-private facts — stake
support, frontier position, realized value, and regret stay on the
in-memory outcome. The cut-bound report is fed by the kernel ledger's
ChargeEvents (pool membership = the recorded estimator), never by
presentation lists.

The accountant sums per (technique, observer), classifies the fraction
(negligible < 0.05 ≤ bounded ≤ 0.25 ≤ material ≤ 0.5 ≤ unsafe ≤ 0.8 ≤
reconstructed), and **refuses** any observation that would cross the observer's
ceiling — flagging an incident if the refused attempt was itself trying to reach
reconstruction. This is what makes result-verification safe and theft-by-probing
a typed, blockable event.

## The honest non-claims (carried in every receipt)

- Verified **results, not methods** — novelty, causality, and transfer are
  unprovable at model scale in 2026.
- The confidential-enclave verifier is **doubly-sealed but sees both inputs** —
  a single point that could leak A's method to B.
- Trusts the **hardware vendor**; a vendor-key or side-channel compromise breaks
  the seal.
- **Receipts are not contracts** — cross-jurisdiction enforcement is out of band.

## Running

```
python3 -m workbench.ip_trade_sim.run          # deterministic scenario
python3 -m unittest workbench.ip_trade_sim.test_engine -v
```

Per-lane court files land under `workbench/.chamber/ip_trades/<lane>/`.

## Roadmap

- Human-interactive mode: exercise `set_reserve` / `approve_settlement` /
  `consider_reveal` hooks live or from a scripted policy file.
- LLM-agent mode: real agents reason about marginal value and negotiate prices
  under the bounded observation budget (deterministic fallback preserved).
- Regret accounting: a purchased technique that does not transfer (unprovable
  pre-purchase) shows up as negative realized value post-trade — the honest cost
  of buying on results alone.
