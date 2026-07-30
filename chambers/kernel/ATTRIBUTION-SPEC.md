# charge-attribution/1 — the split rule as a recomputable fact (V-codes)

**Status:** normative. Frozen surfaces are untouched: the V-codes are a
SEPARATE verdict list (`v_codes`, `attribution.attribution_codes()`); the
I/S/X/C/P/A families bind to their corpora exactly as before. A ledger
with no `attribution_report` events has an empty V verdict — which is why
the frozen corpora cannot be disturbed.

The law this spec makes checkable (F6 of the import register; the G20 gap):
**when a pot is split across the sources of a derived fact's ancestry, the
split is a declared rule computed from facts already in the artifact — and
a misdeclared split convicts from bytes.** Today a placement fee that lands
on a fact five consumed judgements built is divided by ad-hoc percentages;
first-contact attribution (the shipped G1 proxy) is the degenerate
last-touch case. This spec replaces discretion with the unique symmetric,
efficient, null-player-respecting division — the Shapley value — over a
characteristic function that is itself a ledger fact.

## V.0 Why this characteristic function, and what it refuses

The real price of cooperative attribution was named when F6 entered the
register: not the exponential combinatorics (irrelevant at our n), but
*agreeing on the characteristic function*. charge-settlement/2 already
settled the doctrinal ground: **counterfactuals are refused.** "They
wouldn't have won otherwise" has no operationalizable form; a checkable
quantity is always a ledger fact a stranger can recompute. So /1's
characteristic function is the one contribution measure the artifact
already carries, machine-checked, at the DPI bound:

> `v(S)` := `min(E, maxflow(⋃_{s∈S} anchors(s) → d))`

— the declared carrying capacity of coalition `S`'s ancestry into the
emitted fact `d`, over exactly the flow network of KERNEL-SPEC P.4, with
`E` the declared emission capacity of P.3. This is the same quantity the
P-codes charge; attribution and provenance charging price one measure from
two directions (what you owe the sources; what the pot owes them). It is
integer-valued, monotone (more anchors never carry less), `v(∅) = 0`, and
recomputable by a stranger from the JSONL bytes alone.

What it deliberately is NOT: a measure of truth, quality, or realized
value. It prices *declared carrying capacity of ancestry*, the proxy the
artifact can check — Goodhart priced openly, per the settlement doctrine
(the metric label names the proxy, never the aspiration). The rule is
*declared, like pricing, above the protocol*: `shapley_dpi/1` is A split
rule, not THE split rule; a report names its method, and this spec convicts
only reports that claim this method and misstate its output.

## V.1 The `attribution_report` event kind

```jsonc
{ "kind": "attribution_report",
  "derived": "sha256:…",           // the emitted fact whose pot is split
  "coupling": { "node": "orchestrator-1", "tick": 40 },
                                   // names the emission coupling (P.3):
                                   // channel is forced to "derived:"+derived
  "pot_ucr": 100000000000000,      // uint microcredits being divided
  "method": "shapley_dpi/1",       // the declared split rule
  "shares": [                      // one row per beneficiary source
    { "source": "alice", "share_bps": 1, "payout_ucr": 12500000000 },
    { "source": "bob", "share_bps": 9999, "payout_ucr": 99987500000000 }
  ],
  "issuer": "orchestrator-1",
  "seq": 3,                        // uint >= 1, issuer-local
  "tick": 41 }                     // int, issuer clock domain
```

The fold ignores the kind (KERNEL-SPEC §2 forward compatibility); it
carries no value and no leakage — it is a CLAIM about how a pot divides,
and the audit recomputes the claim. **Fact identity is X0's for free:**
`(issuer, "attribution_report", seq)` equivocation convicts with no code
added here. The report deliberately carries no numerators, no flow values,
no intermediate arithmetic: every derivable quantity a report could carry
is an equivocation surface, and the audit derives them all.

`shares` rows carry both the display quantity (`share_bps`, basis points
of 10000) and the operative quantity (`payout_ucr`, microcredits of the
pot). Both are computed by the same allocation rule (V.3) from the same
numerators; neither is derived by scaling the other.

## V.2 The game

Given a report naming derived fact `d` and coupling `(node, tick)`:

- **The coupling** is the set of charge events agreeing on
  `(node, tick, "derived:" + d)` — P.3's grouping, verbatim. Its
  exp-emissions and declared emission capacity `E` are P.3's, verbatim.
- **The players** are `sources(d)` — P.2's anchored sources of the
  provenance closure of `d`, with their anchor sets.
- **The characteristic function** is `v(S)` of V.0, computed on the P.4
  network with the super-source feeding every anchor of every member
  of `S`. Unbounded capacities instantiate at `E`, as in P.4. Integer
  max-flow; no floats exist anywhere in this spec.

`n := |sources(d)|` is capped: **NMAX = 12.** A report over a fact with
more than NMAX sources is *unauditable in bounded work* (2^n max-flow
computations), and an audit that can be made to do unbounded work by one
event is the denial-of-audit the total-fold discipline forbids. Such a
report convicts (V5) — what cannot be recomputed cannot be believed. This
is a refusal, not a limitation to hide: a 13-source pot split needs either
a coarser declared method or a /2 with a certified-approximation story.

## V.3 Exact Shapley, exact allocation — integers end to end

**Numerators.** For each source `s`, over subsets `S ⊆ N∖{s}`:

> `num(s)` := `Σ_S |S|! · (n−1−|S|)! · (v(S∪{s}) − v(S))`

Marginals are non-negative (v is monotone), so numerators are naturals.
The classical efficiency identity gives `Σ_s num(s) = n! · v(N) =: D`;
the audit USES `D := Σ_s num(s)` (conservation of the allocation below
then holds by construction, not by theorem). `num(s)/D` is the Shapley
share — never materialized as a float.

**Allocation.** A pot `P` (microcredits, or 10000 for the bps row) divides
by largest remainder over the numerators, `D > 0`:

- `floor(s)` := `P · num(s) div D`; `rem(s)` := `P · num(s) mod D`.
- The shortfall `k` := `(Σ_s rem(s)) div D` is exact (`D` divides the
  sum) and `k < n`.
- The `k` largest remainders receive `+1`, ties broken by ascending
  lexicographic source id — deterministic across implementations.

Then `Σ_s payout(s) = P` exactly (machine-checked:
`lean/ChargeKernel/Attribution.lean`, `alloc_conserves`; the floor-only
rule provably leaks — the remainder arm is load-bearing, not decorative),
and each payout is within one microcredit of the unrounded share (the
quota property). The recomputed share set is
`{ s : num(s) > 0 }` with its `(share_bps, payout_ucr)` pairs; null
players (num = 0) earn nothing and need not appear — a declared zero row
is legal-if-exact, noise but not a crime.

`D = 0` (no coalition carries anything — `E = 0` or all flows zero) means
this rule derives NO division: no positive pot can be honestly split by
`shapley_dpi/1`, and V2 convicts any report that tries.

## V.4 The V-codes

Verdict surface: sorted, deduplicated `"<code> <subject>"` strings
(`attribution_codes()`), same discipline as every other family. Total
over adversarial content — nothing in this spec raises.

| code | subject | convicts when |
| --- | --- | --- |
| V1 | canonical JSON of `["att", d, s]` | **share mismatch.** The declared `(share_bps, payout_ucr)` for source `s` differs from the recomputed pair |
| V2 | report event id | **non-conservation.** The declared `payout_ucr` values do not sum to `pot_ucr`, or (shares nonempty) the declared `share_bps` do not sum to 10000 — pure report arithmetic, checkable even when the game is not |
| V3 | canonical JSON of `["att", d, s]` | **phantom beneficiary.** A declared share names a source not in `sources(d)` — paying outside the ancestry |
| V4 | canonical JSON of `["att", d, s]` | **dropped contributor.** A source with `num(s) > 0` is absent from the declared shares — the value-layer mirror of P1 |
| V5 | report event id | **unauditable report.** Malformed fields (non-uint pot, non-string derived, unparsable coupling or shares, duplicate source rows), an unknown `method`, a coupling with no exp-emissions (E undefined), or `n > NMAX` — what cannot be recomputed cannot be believed; fail closed |

Notes, in the register's discipline:

- V2 is deliberately independent of recomputation: it convicts a
  non-conserving report even when V5 blocks the game itself. The
  conservation arm never goes dark.
- V1/V3/V4 subjects name the (fact, source) account the misdeclaration
  touches — the row a future settlement gate will map, exactly as P1's
  subject is the uncharged key.
- Like the P findings, V findings are functions of the event set; merge
  order and jsonl round-trips cannot move them. Merging in a corrected
  report does NOT resolve a finding against the old one — reports are
  facts, and a superseded wrong claim stays convicted; issue the fix
  under a new `seq`.

## V.5 The honest reporter (informative)

`attribution.compile_report(ledger, derived, node, tick, pot_ucr, issuer,
seq, report_tick)` recomputes the game with the same functions the audit
uses and emits a report that verifies clean by construction. An honest
orchestrator computes the split it declares; a dishonest one is convicted
by any stranger holding the bytes. There is nothing else to being honest
here — the rule is deterministic and the inputs are shared.

## V.6 What this deliberately does NOT claim

1. **No settlement gating yet.** V findings do not join the dirty court
   in /1: a `required_clean` release is not yet refused over a
   misdeclared split, because mapping V subjects onto escrow charge-key
   courts is a design decision (which keys does a bad split touch — the
   pot's, the sources'?) that deserves its own corpus. Named residue,
   queued for charge-settlement/3 or attribution/2. The conviction is
   still transferable evidence today.
2. **Declared reuse only.** The game runs over `derivation` events that
   exist. Undeclared reuse is invisible here exactly as it is to P1/P2
   (KERNEL-SPEC P.7 non-claim 1) — the same trust class, priced once.
   Above the protocol, hidden reuse is slashable
   (`MARKET_LAWS.hiddenReuseIsSlashable`); this spec makes DECLARED
   reuse cheap to reward, which is the incentive half of that law.
3. **Capacity is the proxy.** `v` prices declared carrying capacity of
   ancestry, not quality, truth, or realized causal contribution — the
   Goodhart gap is open and labeled, per settlement doctrine. A source
   that declared a fat pipe of noise is overpaid by this rule; quality
   pricing is the evaluator/oracle layer's job (market.ts), not the
   kernel's.
4. **One method.** /1 audits `shapley_dpi/1` only, and V5 convicts any
   other `method` string on this event kind — fail closed, because a
   method the audit cannot recompute is an unverifiable claim riding a
   verdict surface. A second method (`direct_reuse`, `path_decay`,
   weighted variants) enters only with its own recomputation arm.
5. **The subset-weight ↔ permutation-walk equivalence** (the classical
   Shapley identity) is property-tested (brute-force permutation sum for
   small n, `test_attribution.py`), not machine-proven; the Lean file
   proves walk-efficiency and allocation-conservation. Named, not
   papered over.

---

# Part II — the value coupling: split-bound escrows (S11/S12) and the V-court

**Status:** normative; shipped 2026-07-08, same day as Part I's
"no settlement gating yet" residue — this Part closes it. Frozen
surfaces are untouched three ways: V findings join the dirty court but
frozen corpora carry no `attribution_report` events; S11/S12 fire only
against escrows carrying a `split` block, which no frozen escrow does;
the fold's credit-target change is gated on the same absent block. Every
historical artifact keeps its bytes and its verdict.

Part I made a misdeclared split CONVICT. This Part makes the money
OBEY: an escrow may bind itself to the split rule, after which its value
can only leave along the rule's recomputed rows — the contributor with
the 1/8000 share cannot be stiffed by anyone holding the pot, including
the issuer.

## V.7 The design decision Part I deferred, decided

The residue asked: which court does a bad split dirty? Two couplings
ship, layered so neither depends on the other:

1. **The V-court join (advisory layer).** V findings enter the
   dirty-court stream `_court_findings` exactly as P findings did
   (KERNEL-SPEC P.6): a `required_clean` release against keys a V
   finding touches is convicted (S4/S8). Touch mapping: V1/V3/V4
   subjects carry the named source `s` — they touch every exposure key
   `["exp", s, …]` in the escrow's `charge_keys`; V2/V5 subjects are
   report ids and fall to the fail-closed default (touch everything).
   A lying report anywhere near a source poisons `required_clean` value
   on that source's accounts.
2. **The split binding (structural layer).** The escrow binds to the
   RULE ITSELF, not to any report: the audit recomputes the rows from
   the DAG and convicts value that deviates. A report event remains the
   legible declared claim — V-codes police it — but no release needs to
   cite one, and no honest beneficiary depends on one existing. One
   less equivocation surface; the strictest binding wins the value path.

## V.8 The `split` escrow block

```jsonc
{ "kind": "escrow", ...,                 // SETTLEMENT-SPEC §1.2 / §7.1
  "split": { "derived": "sha256:…",      // the fact whose pot this is
             "node": "orchestrator-1",   // the emission coupling (P.3)
             "coupling_tick": 40 },
  "default_on_expiry": "release_by_report" }
```

Rules (S6 malformed-escrow arms, additive):

- `split` must be a dict whose `derived` is a string and which carries
  `node` and `coupling_tick` (any JSON — compared canonically).
- A split escrow's `default_on_expiry` must be `"release_by_report"` or
  `"refund_to_payer"`; `"release_by_report"` on a NON-split escrow is
  malformed (it has no rows to release by).
- `split` and `outcome` on one escrow is malformed — outcome-conditioned
  split pots are a /3 with their own quorum-interaction story, refused
  rather than improvised.
- The escrow's declared `payee` is ignored by the value path (rows name
  the recipients) but must still be a string (S6, unchanged) — it
  remains the anti-holdup counterparty of record.

## V.9 The bound game and the row discipline

For a split escrow `e`, the **bound rows** are
`recomputed_shares(ledger, derived, node, coupling_tick, amount_ucr(e))`
— Part I's honest rows, recomputed by the auditor from the artifact.
The pot of the game IS the escrow amount; no report is consulted.

A **row disbursement** is a `release`, or a release-direction
`default_resolution`, against `e`, carrying one additional field:

- `beneficiary` — the source string of the row being paid.

**S11 — split-binding violation** (subject: the disbursement event id).
A row disbursement convicts when:

- `beneficiary` is missing or not a string;
- the bound game is unauditable (no exp-emissions at the coupling, or
  arity over NMAX) — fail closed: a pot bound to a game a stranger
  cannot recompute does not move toward payees (refund stays open);
- the bound rows are empty (`D = 0` — nothing carried, nothing owed);
- `beneficiary` matches no bound row;
- `amount_ucr` ≠ the row's `payout_ucr` — rows pay exactly once, in
  full. Partial payment of a row is refused: it would reintroduce the
  holdup ("here's half, be grateful") this binding exists to delete.

**S12 — row overdraw** (subject: canonical JSON of
`["split", escrow_id, beneficiary]`). The fold-counted disbursements to
one beneficiary against one escrow exceed that beneficiary's bound-row
`payout_ucr`. With S11's exact-row discipline this fires on the second
payment of a row; it exists independently so cumulative dishonesty is
convicted even where per-event checks were evaded.

Work receipts (S3), expiry (S7), premature default (S8), clean court
(S4, when `required_clean`) apply to row disbursements unchanged.

## V.10 The fold (conservation-neutral by construction)

The only fold change: for a release-direction flow against a split
escrow, the credited account is the event's `beneficiary` instead of
the escrow's `payee`, under the SAME all-or-nothing gate (SPEC §2 /
`RawConservation.lean`): a non-string beneficiary credits no account
and counts nothing against the escrow — the remainder stays, S11
convicts, conservation telescopes on any soup. Refund-direction flows
are untouched. The Lean raw model quantifies over WHICH string is
credited only through the gate's shape, which this change preserves;
that inheritance is an argument, not a new theorem — named here, and
the adversarial soup tests pin it.

`default_on_expiry: "release_by_report"` resolves per row: after
expiry, ANY party (the stiffed contributor is the point) submits a
`default_resolution` carrying `beneficiary` and the row's exact amount;
the fold credits the beneficiary; S8 polices timing, S11/S12 police the
row, receipts are checked under S8 as for any release-direction
default. This is F4's checklist satisfied at design time: the
obligation "the issuer eventually pays every row" arrives
safety-shaped — deadline (expiry) + permissionless per-row resolution.

## V.11 The honest issuer (informative)

`SettlementIssuer.escrow(..., split=SplitCondition(...))` locks a
split-bound pot; `release_split(escrow, beneficiary, charge_ids, tick)`
recomputes the row with Part I's functions and refuses live
(`SettlementRefused`) what the audit would convict: unknown
beneficiary, unauditable game, already-paid row, wrong amount by
construction (it computes the amount; callers cannot pass one).

## V.12 What Part II deliberately does NOT claim

1. **Rust-twin parity is owed.** The counterparty verifier does not yet
   recompute V-codes or the S11/S12 arms; corpus verdicts agree because
   corpora carry no reports and no split escrows. Named, queued with
   the standing port discipline.
2. **The bound game is as gameable as its declarations** — Part I
   non-claims 2 and 3 (undeclared reuse invisible; capacity is the
   proxy) bind the money exactly as far as they bind the verdict. The
   binding removes the POT-HOLDER's discretion; it does not manufacture
   truth upstream of the declarations.
3. **Identity of beneficiaries is claimed, not proven** — a row pays
   the source STRING's account; binding that account to a key is
   charge-identity/1's, and Sybil stays G3/L5.
4. **Outcome-conditioned split pots are refused** (S6), not designed.
5. **Lean models the gate shape, not the split arms** — S11/S12
   completeness is F3-campaign territory; the conservation inheritance
   argument of V.10 is prose over a preserved gate, pinned by soup
   tests, not a new theorem.
