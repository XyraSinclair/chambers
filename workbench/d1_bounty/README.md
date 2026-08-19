# D1 bounty slice — metered-egress security research over sealed vendor artifacts

The executable embodiment of the build-first decision (`workbench/notes/autoresearch/2026-07-02-cooperative-economy-atlas/README.md`)
(§4): a third-party research agent is admitted near a sealed vendor artifact,
emits typed findings (VEX reachability verdicts + minimal repros), gets scored
by a pinned oracle, and is paid **zero-touch** under a standing authorization —
with every emission metered by an egress accountant at the **adversarial
maximum**, because the same typed output the vendor pays for is a channel that
carries sealed source structure out of the enclave.

Mirrors `primitives/entropy.ts` (CapacityEstimate / CompositionKey /
EgressBudget / EstimatorAttestation), `market.ts` + `pricing.ts`
(EvaluatorOracle / PriceSchedule / SettlementPayoutAuthorization /
CreditSettlement). Sibling of `ip_trade_sim/leakage.py` on the same substrate:
that one meters an *observer probing a technique*; this one meters an *agent
emitting typed findings about sealed source*. Stdlib only, deterministic.

## The five lanes

```
python3 -m workbench.d1_bounty.run
```

| Lane | Story | Outcome |
|---|---|---|
| A honest | valid finding, repro replays, window clean | settle `released`, payout `zero_touch`, receipt names payee |
| B regressed | shipped fix regresses inside the window | settle `slashed`, no payout |
| C extraction | per-build probes against the sealed patch diff | ceiling trips (leakage bounded), **incident** latches on demand |
| D capture | oracle author == worker beneficial entity | oracle inadmissible, no zero-touch path, `human_fallback` |
| E self-interested | the paid agent meters its own leak | emission refused **before the oracle ever runs** |

## Module map

| File | Role |
|---|---|
| `egress.py` | the egress accountant — D1 adapter over charge-kernel/2 integer millibits, CapacityEstimate at adversarial max, CompositionKey, monotone ceiling, incident latch, EstimatorAttestation admissibility |
| `bounty.py` | VerificationVerdict (proven/trusted/unprovable — no `verified: bool`), pinned EvaluatorOracle + ConflictOfInterestCheck, rubric-pinned PriceSchedule, SettlementPayoutAuthorization, CreditSettlement |
| `engine.py` | the lane state machine: grant → emit(metered) → oracle_score → accept → settle(heldback) → regression window → release \| clawback; hash-chained ledger + PlainAccount receipt |
| `run.py` | the five lanes + court-file writer/validator |
| `test_d1.py` | per-lane invariants + the accounting the handoff was skeptical about |

## The two accounting laws this slice adds

**Leakage vs. demand are distinct monotone counters.** `cumulative_bits` is
what actually crossed (accepted debits only). `demanded_bits` is what the
audience *asked* to cross — every admissibly-estimated attempt, refused or not.
The ceiling refuses on leakage; the **incident latches on demand**: a campaign
that keeps requesting capacity which, had it been granted, would reconstruct
the subject (≥ 0.80 of its structural entropy) is verification-as-extraction
even when every request is refused. Refusals do not launder the intent. The
corollary is honest in both directions: a conservative ceiling that trips
nowhere near reconstruction is a budget event, *not* an incident; and a
misconfigured ceiling above the UNSAFE line still flags on the accepted path.

**An unmetered claim cannot meter pressure.** A `self_interested` (or
non-worst-case) estimator's emission is refused outright — and accrues *no*
demand either, because its bit estimate is exactly the number we refused to
trust.

**Payment law carried over from canon:** the standing authorization moves
*money*, never content; a rubric change is a new oracle and a new schedule;
payout releases zero-touch only inside the per-payout and window ceilings, and
falls back to a human — it never silently exceeds them. The `PlainAccount`
receipt is a statement of *final* state: settlement fates decided after the
run (release, clawback) recompute it, never leave it stale.

## The honest non-claims (carried in every receipt)

- Verified **results, not methods** — novelty/causality/transfer are unprovable
  at model scale (2026).
- Bits are an **upper-bound tripwire, not a secrecy proof**; staying under
  budget proves nothing.
- **Harm is not linear in bits** — a one-bit "reachable" plus a tiny repro can
  be a live weapon (open frontier #4).
- Trusts the **TEE/hardware vendor**; a vendor-key or side-channel compromise
  breaks the seal (#6).
- **Accounting is delegated to charge-kernel/2** — integer-millibit decisions
  are audit-backed; estimator bounds and CompositionKey canonicalization remain
  trusted boundary inputs.
- **Receipts are not contracts** — embargo/export/trade-secret enforcement
  lives in jurisdiction (#15).

## Running and testing

```
python3 -m workbench.d1_bounty.run                 # the five lanes
python3 -m pytest workbench/d1_bounty/ -q          # 17 tests
python3 -m unittest workbench.d1_bounty.test_d1 -v
```

Per-lane court files (hash-chained lane ledger, charge-kernel ledger, findings,
egress report, receipt) land under
`workbench/d1_bounty/out/court/<lane>/`; `validate_courtfile` re-verifies
the lane chain and rejects tampering, then reloads the kernel ledger and
requires `audit() == []`.

## Roadmap (what the slice does not yet earn)

- **D1 estimator corpus** — charge-kernel/2 has golden-trace conformance; D1's
  estimator boundary still needs its own signed examples for every schema family.
- **Ordinal EntropyReview** — this slice enforces only the numeric half of
  `entropy.ts`'s release-gate conjunction; the ordinal review lane is out of
  scope and named as such in `egress.py`.
- **CompositionKey canonicalization** — subject/queryFamily/audience hash
  derivation is still convention, not a standard; honest cross-run metering
  needs it (research-horizon, per §4's kill list).
- **Real repro/VEX wiring** — `score_against_rubric` is a deterministic
  stand-in for the pinned model oracle; the design-partner version scores real
  replay output.
