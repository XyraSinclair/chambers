# The Chamber Calculus

The canon modules (`core.ts`, `mediation.ts`, `iptrade.ts`, …) define the
data shapes. This document defines the **algebra over them**: a small set of
typed combinators whose composition laws make leakage a compile-time
quantity. Signatures are Haskell-flavored pseudocode; each construct names
its canon binding so the calculus and the TypeScript surface cannot drift
silently. When they disagree, canon data shapes win on fields; this
document explains; the citable law surface is `calculus.ts`'s
`CALCULUS_LAWS`.

Register note (operator correction, 2026-07-13): `STRUCTURE.md` is the
canonical reading discipline for everything below. The primary grade is
the **disclosure context** (audience × purpose × alphabet); `(Bits, +)`
is its homomorphic image through `capacity`, kept because it is the only
leg that composes additively — the anti-laundering budget. Nothing in
this document changes; how it is fronted does. The alphabet is the
object; the bit number is its logarithm.

The semantic model the types must stay sound against is quantitative
information flow: every requester-visible surface is a channel, and
`log2 |alphabet|` is a **ceiling** on the capacity of any channel with that
output alphabet, regardless of how messy the private input is. The charge
is derived from the alphabet rather than declared, so the ceiling cannot
drift from the surface.

Honesty about status: the theorem connecting this type discipline to the
QIF semantics — "well-typed protocol ⇒ leakage ≤ Σ charges," a release
modality graded by a leakage semiring — is the project's named open goal
(mediation-literature.md, empty vein 3), not an established fact, and
TypeScript canon cannot enforce the no-eliminator property anyway. Today
the calculus is a *specification*; enforcement is the charge kernel, the
sim's runtime checks, and review citing `CALCULUS_LAWS`. The Lean shadow
covers the odometer, not the type soundness.

## 1. Parties, silos, and the two gradings

```haskell
data Party      -- A | B | Mediator | ... (protocol-specific, finite)
type Silo       = Set Party   -- whose corpora have touched a value
newtype Bits    = Bits Rational
```

The central object is a **doubly-graded monad**. Grade one tracks
*provenance* (which parties' private data went in); grade two tracks
*leakage spent* (bits charged so far). The type-level content that earns
its keep is small and specific: no eliminator out of `Chamber` (§1), and
`Consent` indexed by the provenance grade (§4/L7). The rest of L1–L8 is
kernel bookkeeping and design law; the grading is the organizing sketch,
not a proof.

Structural reading (STRUCTURE.md §4): grade two is the projection of the
richer context grade through `capacity`. When the formal lane resumes,
the release modality targets the context poset directly, with `Metered`
as its image — more precision on scalar bits is not on the roadmap.

```haskell
-- Chamber ps a: a computation confined to the joint silo of parties ps.
-- Canon: a run under core.ts authority with environment.ts isolation.
Chamber :: Silo -> Type -> Type

-- Provenance grading: silos join, never shrink.
return :: a -> Chamber ∅ a
(>>=)  :: Chamber ps a -> (a -> Chamber qs b) -> Chamber (ps ∪ qs) b
```

There is deliberately **no eliminator** `Chamber ps a -> a`. Confinement is
parametricity: a value born from private data can never re-enter public
code except through §3's `release`. This is the Dependency Core Calculus
move (protection contexts), with the silo set as the label lattice — with
one honest scope note: DCC's noninterference is proved for a pure calculus,
and `judge` puts an adversarial oracle *inside* the modality. The operative
guarantee against that oracle is therefore the alphabet ceiling (§6), not
a noninterference proof; the parametricity story covers the plumbing
around the oracle, not the oracle.

```haskell
-- Metered a: the odometer. Writer over (Bits, +, 0).
-- Canon: entropy.ts CapacityEstimate + the kernel's accepted-debit fold.
Metered :: Type -> Type
runMetered :: Budget -> Metered a -> Either Overrun (a, Bits)
```

`runMetered` is the ONLY place a budget is enforced, and it is a hard cap:
the proven odometer law (`run_cumulative_le_ceiling`) is the Lean shadow of
this signature.

## 2. Codebooks: capacity true by construction

```haskell
class (Finite v) => Codebook v where
  capacity :: Bits            -- log2 |v|, DERIVED, never declared
```

A codebook is the contract object: the finite alphabet of everything a
counterparty can ever observe. Verdicts, drill-down facets, **and every
rejection or error code** are codebook members — an un-enumerated failure
path is a side channel. Canon: `iptrade.ts` verdicts, `mediation.ts`
`StructureJudgement.kind`, and the release-artifact bucket schema.

```haskell
-- The full observable alphabet of one interaction, failures included:
data Outcome v = Verdict v | Rejected RejectCode | Errored ErrCode
               | Withheld WithholdCode   -- data-dependent aborts are symbols too
-- capacity (Outcome v) = log2 (|v| + |RejectCode| + |ErrCode| + |WithholdCode|)
-- Enumerating RejectCode/ErrCode/WithholdCode so that no real failure mode
-- (sandbox kill, vendor error, which-error-when) carries residual signal is
-- an engineering obligation, not a given: the theorem is true of the model,
-- and the model boundary is what the egress harness exists to test.
```

This kills the self-report problem: nothing is "declared entropy" anymore;
the alphabet is closed and the charge is computed from its size.

## 3. The four ways anything crosses a boundary

Everything below is total; there are no other exits. A protocol's leakage
bound is the sum of charges over the crossings it contains — the min-cut
picture of §6.

```haskell
-- (i) Work: the confined worker. Pure; zero tools; one packet.
--     Canon: environment.ts EnvRecipe with empty capability row.
work :: Packet ps -> Chamber ps Evidence

-- (ii) Judge: evidence to verdict, inside the silo. The LLM lives here;
--      nothing it does matters to the bound, only the alphabet it must
--      land in. A malicious judge can steer WHICH verdict — that is
--      exactly capacity bits, already charged. It cannot widen the alphabet.
judge :: Codebook v => Question -> Chamber ps Evidence -> Chamber ps v

-- (iii) Release: the one door. Requires unforgeable consent from every
--       party in the grade; charges the full outcome alphabet.
--       Canon: core.ts release review + coalition.ts WideningEvent.
release :: Codebook v
        => Consent ps v          -- signatures over THIS codebook, all of ps
        -> Chamber ps (Outcome v)
        -> Metered (Public (Outcome v))
-- charge: capacity (Outcome v)

-- (iv) Gates. Two species, distinguished by what they may read:
gatePub  :: (Question -> Outcome ())  -> Question -> Outcome ()
gatePriv :: Chamber ps Bool -> Consent ps Bool -> Metered (Public Bool)
```

`gatePub` cannot receive a `Chamber` or `Packet` value — by type. Its
decisions are therefore simulatable from public data and leak zero. This is
the **simulatability law** as a kind restriction rather than an audit item.
`gatePriv` is just `release` at `v = Bool`, and like every release it
charges the full `Outcome Bool` alphabet (verdict + reject + error codes),
not a bare bit, and needs consent. There is no third species — and in
particular **protocol aborts are not one**: whether a release happens at
all, when it is data-dependent, is a symbol. `Outcome` therefore carries a
`Withheld` code (consent revoked, review failed), charged like any other
member; a protocol whose abort behavior depends on silo content and is not
in the alphabet has an unmetered channel.

## 4. Consent and review

```haskell
-- Unforgeable witness that party p signed codebook v for protocol π.
-- Canon: the owner-token approval in core.ts; program-level consent
-- per the clean-room analysis (docs/research/data-clean-rooms-alpha.md):
-- legal reviews (codebook, worker program) ONCE, before data enters.
Consent :: Silo -> Type -> Type
sign    :: PrivateKey p -> CodebookHash v -> ProgramHash -> Consent {p} v
(<+>)   :: Consent ps v -> Consent qs v -> Consent (ps ∪ qs) v
```

Review is counterfactual, because influence is the only question a human
can actually answer about high-dimensional leakage:

```haskell
-- Run the same judgment with a flagged fact ablated; the owner sees
-- WHERE the verdicts differ, never the evidence itself.
ablate :: Fact -> Packet ps -> Packet ps
influence :: Question -> Packet ps -> Fact
          -> Metered (Private p InfluenceView)   -- p = the flagging party
-- InfluenceView is itself a small codebook: Identical | Differs FieldBucket.
```

Two accounting facts the first cut of this document got wrong, both caught
by adversarial review. First: in a joint silo `{A,B}`, A's influence view
of the joint verdict is a function of **B's corpus** — so `influence` is a
charged release to A against B's exposure, inside the protocol's cut and
under the joint consent, never a free UI affordance. Second: consent that
is *conditioned* on influence results makes release-vs-no-release a
private-data-dependent observable — which is why `Outcome` carries
`Withheld` (§2) and the abort is charged. The clean sequencing that avoids
paying twice: program-level consent is signed ONCE before data enters
(codebook + worker program + the influence-view codebook itself); the
influence pass and any withhold it triggers are then charged crossings
inside the already-consented protocol, not a second consent ceremony.

Canon: the paired-silo egress harness is `influence` run adversarially;
here it becomes the consent-time primitive — metered like everything else.

## 5. Composition laws

```haskell
-- L1 Provenance join      Chamber grades compose by ∪; silos never shrink.
-- L2 Odometer             Metered charges compose by +; runMetered caps hard.
-- L3 Data processing      fmap f (release c ch) charges no more than
--                         release c ch, for ANY f :: Public v -> Public w.
--                         Post-processing is free and never increases leakage.
-- L4 Monotone widening    audience(release) only grows; no combinator
--                         narrows it (coalition.ts: one door, one way).
-- L5 Simulatability       gatePub is a function of public inputs only
--                         (parametricity; no Chamber argument exists).
-- L6 Closed alphabet      every observable outcome ∈ the codebook,
--                         rejections and errors included (§2).
-- L7 Consent adequacy     release typechecks only with Consent covering
--                         the FULL provenance grade — you cannot release
--                         a joint derivative with one party's signature.
-- L8 Sequential budget    a protocol of releases r1..rk against budget B
--                         satisfies Σ capacity(ri) ≤ B or runMetered fails
--                         closed BEFORE the crossing, not after.
```

L1–L2 are the graded-monad laws; L3 is the data-processing inequality
arriving as a free theorem; L7 is `MEDIATION_LAWS.judgementsAreDerivativesFirst`
plus `requesterIsAReader` given teeth at the type level. L8 is the proven
kernel odometer pointed at capacities that are finally honest (§2).

Budget semantics (per research/mediation-literature.md, Vein 1): charges
are stated against **min-entropy / g-leakage**, not Shannon entropy — the
operational question is the adversary's best-guess advantage.
`capacity = log2 |v|` ceilings min-capacity, which by the Miracle theorem
(Alvim et al., CSF 2012) bounds **multiplicative** g-leakage for every
**non-negative** gain function g, for every prior. Scope this honestly:
it is an odds-ratio guarantee, not a damage bound — *additive* g-leakage
(absolute expected-damage threat models, gain functions with penalties)
escapes the Miracle theorem (Alvim et al., CSF 2014) and needs
per-protocol analysis. A specific protocol may additionally state a
tighter `V_g` bound for the gain function its parties actually fear. For
**correlated corpora** the bound is on the channel, and what those bits
reveal about correlated third parties (collateral leakage,
arXiv:1604.04983) must be assessed at codebook-design time. And the
alphabet counts **symbols, not schedules**: release timing is a channel
the capacity ceiling never sees, so releases must be fixed-schedule,
bucketed, or padded — otherwise a malicious judge modulates latency
freely and "any behavior of agents inside" is false.

What the calculus does NOT claim: it bounds the *channel*, not the *harm*
of any particular bit; it does not defend against sybil identities holding
independent budgets (limits ledger L3); the worker model vendor sees the
packet until local weights/TEE (L4). State these in every protocol doc.

## 6. Protocols are typed DAGs; leakage is a cut

A mediation protocol is a finite DAG whose nodes are the §3 combinators and
whose edges carry the types above. Draw the trust boundary around each
silo; the only edges that may cross it are `release`/`gatePriv` edges
(everything else fails to typecheck). Therefore:

> **Cut bound.** The total leakage of a protocol to any observer coalition
> is at most the sum of `capacity` charges on the edges crossing the cut
> separating the silo from that coalition — under ANY behavior of the
> agents inside the silo, including malicious workers and judges —
> *provided* every observable is enumerated: aborts are `Withheld` symbols
> (§2), influence views are charged releases (§4), and event count,
> ordering, and timing are fixed or public-computable (§5).

The bound needs no analysis of the worker, the question, or the corpus.
That is the entire point: adversarial messiness is confined to *which*
codebook element gets picked, which is already paid for. Mathematically
the bound is elementary — the full transcript lives in the product of the
declared alphabets, so min-capacity ≤ Σ log2|alphabetᵢ|, and this holds
against adaptive requesters too when questions are `gatePub`-public. Its
value is not depth; it is that the bookkeeping stays exact at protocol
scale, and that every hole must announce itself as an un-enumerated
surface rather than hide in an estimate.

## 7. The anchor instantiation: minimal IP-overlap mediation

Two labs suspect overlap between A's patent claims and B's implementation.
Full discovery is mutually assured destruction. Canon: `iptrade.ts` lanes +
`mediation.ts` tuple-scoped judgements; simulation: `chambers/ip_trade_sim/`.

```haskell
data Overlap    = NoOverlap | Narrow | Substantial          -- 3
data Locus      = ClaimBucket Int                            -- 8 buckets
data Confidence = Low | Medium | High                        -- 3
type IPVerdict  = (Overlap, LocusSet 3, Confidence)
-- LocusSet 3: ≤3 buckets, WIRE-CANONICAL (sorted, deduplicated). The charge
-- is over wire-distinguishable encodings, so the wire format must equal the
-- semantic set: an ordered-with-repetition encoding would silently hand a
-- malicious judge ~2.7 extra bits of covert channel in locus order and
-- multiplicity. |LocusSet 3| = C(8,0)+C(8,1)+C(8,2)+C(8,3) = 93.
-- |IPVerdict| = 3 · 93 · 3 = 837
-- Outcome IPVerdict, 4 reject + 2 error + 2 withhold codes: 845 → ≈ 9.72 bits

ipMediation :: Consent {A,B} IPVerdict -> Budget -> Protocol
ipMediation consent b = runMetered b $ do
  q  <- pure (gatePub envelopeCheck theQuestion)      -- free (L5)
  ev <- joint (work packetA) (work packetB)           -- Chamber {A,B} …
  v  <- judge q ev                                    -- confined
  _  <- influencePass consent flaggedFacts            -- charged (§4)
  release consent v                                    -- ≈ 9.72 bits
  -- one drill-down facet: 5 facets + 3 outcome codes  -- = 3.00 bits
-- Protocol total: ≤ 12.7 bits + the priced influence pass, by L8. That
-- number goes in the contract next to the signatures — with its honest
-- operational reading spelled out (below), not just the numeral.
```

Thirteen bits — and the contract states what that means, because the
Shannon-uniform intuition ("tiny") is not the operational one: 12.7 bits
of min-capacity is up to a 2^12.7 ≈ 6,700× multiplicative boost in the
counterparty's guessing odds on a predicate of their choosing, per run,
per identity (sybil budgets are L3, priced not solved). What the parties
buy is that this is the *ceiling*, prior-independent and gain-function-
independent (non-negative g), enforced by alphabet and confinement rather
than by trusting the mediator's model or prompts — while trusting, until
local weights/TEE, the model vendor who sees both packets (L4), and the
schedule discipline of §5 for timing.

## 8. Ship path

1. **Sim-first (this month).** Express `ip_trade_sim`'s lanes in the
   calculus: its leakage accountant already meters observations; replace
   declared `entropy_bits` on *verdict* channels with derived codebook
   capacities (probe channels keep declared estimates, honestly marked).
   Deliverable: the sim prints the protocol's cut bound and a canary run
   demonstrating a malicious judge cannot beat it.
2. **Calculus conformance.** A `CALCULUS_LAWS` const in canon; property
   tests for L1–L8 over the sim's traces; the Lean odometer re-pointed at
   derived capacities (closing the adaptive-composition obligation for the
   sequential case).
3. **Chamber run mode.** A two-silo chamber protocol (two packets, dual
   consent, one codebook) as a new run type — the plumbing is the chamber wedge's (private)
   existing run + a second owner surface.
4. **Simulated showcase.** The IP story end-to-end with synthetic corpora
   and adversarial variants (exfiltrating judge, over-probing requester,
   consent-violation attempt), each refused by type/gate/budget — the
   demo IS the sales artifact for "the agentic tier above clean rooms."
