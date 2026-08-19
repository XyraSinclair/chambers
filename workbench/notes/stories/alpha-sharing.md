# The alpha story — 1/8000th of a $100M win

*The founding scenario of charge-attribution/1 (F6, G20). Everything
below the "what runs today" line is shipped and tested; everything below
"what is honestly not solved" is priced, not promised.*

## The scenario

You run into someone's website. Something they did — a technique, a
framing, a data structure, a way of pricing a thing — lodges in your
head. You implement it yourself, from scratch, months later, inside a
system that eventually contributes to a $100M outcome. Their idea was
real input. It carried, honestly, about one eight-thousandth of the win.

Today that person gets: nothing. Not because anyone decided they deserved
nothing, but because there is no machinery in which "1/8000th of this
win" is a *fact* rather than a feeling. Attribution at that resolution
has three missing pieces:

1. **A record that the flow happened** — cheap to declare, expensive to
   fake, not dependent on the beneficiary's later goodwill.
2. **A rule that turns records into shares** — one with actual axiomatic
   standing, not "we felt 5% was fair," and recomputable by someone who
   trusts neither party.
3. **A payment bound to the rule** — so the share is money, not credit
   in the acknowledgments section.

The stack now has all three, with the honest edges named.

## What runs today

**The record is a `derivation` event** (charge-provenance/1). When your
system builds on their idea, the deriving chamber declares: fact `d` was
produced from these consumed facts, and this hop can carry at most
`hop_capacity_mbits` of them. Declaring is one ledger event. NOT
declaring is the expensive move: hidden reuse is slashable above the
protocol (`MARKET_LAWS.hiddenReuseIsSlashable`), and dropping a declared
ancestor from an emission's charge set convicts from bytes (P1). The
incentive gradient points toward honesty — declared reuse is cheap and
now *earns the upstream party money*, which is the half of the law this
import supplies.

**The rule is `shapley_dpi/1`** (ATTRIBUTION-SPEC.md). When a pot lands
on the derived fact — a placement fee, a bounty, a negotiated slice of
the win — it divides by the Shapley value, the unique symmetric,
efficient, null-player-respecting split, over a characteristic function
that is itself a ledger fact: each coalition of sources is worth the
DPI carrying capacity of its ancestry into the emitted fact, the same
integer max-flow the provenance audit already charges. No floats, no
judgment calls, no counterfactuals ("they wouldn't have won otherwise"
is inexpressible by construction — the settlement doctrine, carried
over). A stranger with the JSONL bytes recomputes every share.

**The payment is an `attribution_report`** naming (source, share_bps,
payout_ucr) rows. A report that misstates the rule's output convicts:
wrong pair (V1), payouts that don't sum to the pot (V2), a beneficiary
outside the ancestry (V3), a dropped contributor (V4), a report that
cannot be recomputed at all (V5, fail closed). Conservation — the split
neither mints nor burns a microcredit — is a machine-checked theorem
(`Attribution.lean`), for every tie-break rule an implementation could
choose.

**The number, exactly.** In the test lane (`test_attribution.py`,
`test_the_alpha_story_one_eight_thousandth_of_100m`): the idea's
declared capacity is 1 mbit of the emission's 8000; the pot is $100M in
microcredits. The idea's owner is paid **12_500_000_000 ucr —
$12,500.000000**, not one microcredit more or less, and the artifact
verifies CLEAN end to end under the stranger's one-command verifier.
Two properties worth naming because they are where naive schemes die:

- **Depth is not dilution.** Your implementation sits three derivation
  hops downstream of their website? Their share is identical to the
  one-hop case (the value-layer echo of the P-law; a passing test).
  Laundering-by-relaying does not work here.
- **First-contact attribution is the degenerate case, not the design.**
  The shipped G1 proxy (last touch takes all) survives as what the rule
  reduces to when the closure has one source.

## What is honestly not solved

- **Undeclared reuse is invisible.** You saw the idea, implemented it,
  declared nothing — no ledger, no closure, no share. The kernel
  convicts liars against their own declarations; it does not manufacture
  declarations. This is P.7's trust class, priced once, and it is
  exactly why the *incentive* half matters: the calculus makes declaring
  strictly better than hiding for any party who might ever want the
  reciprocal flow. The social layer (norms, slashing on discovery,
  reputation) stays L5.
- **Capacity is the proxy, not merit.** The rule prices declared
  carrying capacity of ancestry — millibits, not brilliance. A fat pipe
  of noise is overpaid by this rule; quality pricing belongs to the
  evaluator/oracle layer (market.ts), and the metric label names the
  proxy, never the aspiration. Goodhart is priced openly, per the
  settlement doctrine.
- ~~**The share is not yet a gate.**~~ CLOSED same day (ATTRIBUTION-SPEC
  Part II): V findings join the dirty court with source-precise touch,
  and an escrow can be *split-bound* — its pot disburses only along the
  recomputed rows, exact amount, once (S11/S12), and after expiry the
  stiffed contributor submits her own row's default, permissionlessly.
  The $12,500 no longer depends on the pot-holder's goodwill; it
  depends on the bytes.
- **Identity is claimed, not proven.** "alice" earning $12,500 is a
  source string; binding it to a key is charge-identity/1's job, and
  Sybil stays G3/L5 forever.
- **The pot itself is negotiated above the protocol.** What fraction of
  a $100M win enters the ledger as a pot is pricing — declared, like
  everything else here, where a court can see it but not where a court
  decides it.

## Why this shape and not another

The G-register's oldest discipline is that a checkable quantity beats a
true-but-unoperationalizable one. Causal contribution to a win is the
second kind — every attempt to operationalize it routes through
counterfactuals no stranger can audit and every incumbent can litigate.
Declared carrying capacity is the first kind: coarser, gameable in named
directions, and *recomputable from bytes by anyone*. The bet of this
import is the stack's standing bet: a fair-enough rule that a stranger
can verify beats a perfect rule that requires trusting the winner.
