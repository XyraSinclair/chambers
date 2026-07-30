# The structural turn — contexts first, bits as shadow

Operator correction, 2026-07-13, recorded before it could be forgotten:
the project had drifted into presenting **bit counts as the guarantee**,
and that inversion was theater. This document is the canonical fix. It
does not weaken a single theorem in CALCULUS.md; it re-reads them: the
**disclosure structure is the object; the bit number is its logarithm.**

## 1. Why bits cannot be the register

Three defects, none repairable by better estimation:

1. **Harm-blindness.** "Does she have the disease" and "did the eval
   round up" both cost one bit. A ledger denominated in bits literally
   cannot distinguish devastation from noise. (CALCULUS.md §5 already
   concedes this — additive g-leakage escapes the Miracle theorem — but
   conceding it in a caveat while pitching in bits is the inversion.)
2. **Prior-dependence.** "Observer learned 103.77 bits" is defined only
   against a prior over possible worlds that nobody has. The two-decimal
   precision is a modeling artifact presented as a measurement. Derived
   capacities (log2 of a closed alphabet) escape this — they are
   prior-free ceilings — but *learned-bits* numbers on receipts do not.
3. **Institutional mismatch.** Every privacy institution that works —
   privilege, clean rooms, Chinese walls, purpose-limitation law —
   constrains **structure**: who may compute, over what scope, for what
   declared purpose, into which sink, reviewed by whom, with what
   recourse. None of them meters quantity. Nissenbaum's contextual
   integrity named this decades ago: privacy is appropriateness of flows
   between contexts, not smallness of flows. Buyers and courts live in
   that register. Nobody buys bits.

And one defect of pure structure, which is why bits keep exactly one
job (§4): structural rules are per-transaction, and composition kills
them — a thousand individually-appropriate releases triangulate what no
single one reveals. Redaction, k-anonymity, and Chinese walls all died
this death. The known bounds on structure-laundering are composable
budgets: differential privacy's ε is the deployed exemplar (the US
Census runs it — the exception to "institutions never meter quantity,"
and it works exactly where a noise-adding curator over aggregates is
acceptable, which bounded cognitive work over exact private records
mostly cannot afford), and capacity budgets are the noise-free
analogue this substrate uses.

## 2. The primitive: the bounded computation right

The economy's unit of trade is not "access," not "data," and not "a
channel of n bits." It is a **bounded computation right** — one object,
already assembled piecewise across canon, now named:

> **BCR = (algorithm, scope, purpose, alphabet, audience, review,
> recourse).** Whose algorithm may run, over which scoped slice of a
> private world, for what declared purpose, emitting only into which
> closed alphabet, visible to which audience, reviewed by whom before
> release, with what stake and recourse when it goes wrong.

Canon mapping (each leg exists; the object is their conjunction):

| Leg | Canon mechanism |
|---|---|
| algorithm | `Transform` + `EnvRecipe` (empty capability row) |
| scope | `Grant` (paths virtualized, no raw egress) |
| purpose | question/program hash signed at consent time (`sign : … -> ProgramHash -> Consent`) |
| alphabet | `Codebook` — capacity derived, never declared |
| audience | `CoalitionalDerivative.audience` + `WideningEvent` |
| review | counterfactual `influence` pass; dual release review |
| recourse | stake/escrow (settlement kernel), audit trail, court file |

What is granted, priced, traded, revoked, and receipted is the BCR.
Leakage accounting is one *clause* of it — the anti-laundering clause —
not the ontology.

## 3. Disclosure contexts and the widening order

The structural state of any value is its **disclosure context**:

```haskell
data Context = Context
  { audience :: Audience      -- coalition.ts ObserverClass / coalition
  , purpose  :: ProgramHash   -- what the consent signature covers
  , alphabet :: Codebook      -- everything expressible about it
  }
```

Contexts carry a partial order: `c ⊑ c'` iff the audience is no wider,
the purpose is no looser, and the alphabet is no larger. **Every
boundary crossing is a context transition, and the priced event is
strict widening** — LICENSING.md's canonical sentence, generalized from
its audience component to all three:

> A derivative is confined to its generating context unless a release
> transaction widens the context.

The order carries the **cumulative reading**: a context records what
has already been made expressible to whom. That is why narrowing is
unenactable rather than merely priced — revoking a BCR narrows future
grants, never the past context; disclosure is entropy-irreversible.

This is why `wideningIsAPricedOneWayEvent` (COALITION_LAWS) and
`audience_never_narrower` (the Lean widening proof) are not bookkeeping
details — they are the load-bearing guarantee, stated in the register
the guarantee actually lives in. The codebook's real promise is
structural too: not "few bits" but **"nothing outside this finite set of
sentences is expressible about the private world on this channel."**
The alphabet is the contract; its size is a corollary.

## 4. The one job bits keep

`capacity : Codebook -> Bits` is a monotone map out of the context
order's alphabet leg. It is the **only component of the context that
composes additively across transitions**, which makes it this
substrate's backstop against structure-laundering — the noise-free
analogue of DP's ε, per §1's scoping. Therefore:

- The odometer (`Metered`, `runMetered`, L8, `blockBeforeCeiling`)
  stays, unchanged, as the **composition budget**. The seatbelt, not
  the car — with its rating read honestly: on **derived-capacity
  channels** (closed alphabets, CALCULUS.md §6 provisos: every
  observable enumerated, timing fixed or public-computable) it bounds
  what an adaptive adversary can accumulate, as a theorem. On
  **declared-estimate channels** (probes, reveals, negotiation) it
  bounds the *ledger*, not the adversary — it is only as good as the
  declarations. Receipts state the distinction wherever charges are
  shown; the run-level cut bound pools the two numerically.
- Bit lines appear on receipts as a **footnote-grade budget entry**,
  never as the headline, never as a harm claim.
- "Learned X bits" numbers (prior-dependent) are confined to internal
  adversarial analysis and are never a customer-facing claim. Derived
  capacities may be shown, labeled as what they are: the size of the
  sentence set.

Formally (spec, not theorem — the formal lane stays frozen until
deliberately resumed): the release modality should be graded over the
context poset, with `(Bits, +, 0)` as the homomorphic image used by the
budget. CALCULUS.md's doubly-graded monad is the special case that
projects the context grade through `capacity`; nothing proved about the
projection is lost by naming the richer grade above it.

## 5. The structural receipt

Receipt order is register. The canonical receipt (PlainAccount and
every chamber release surface) leads with structure and demotes
arithmetic:

1. **Purpose** — the signed question/program, and whether the run
   stayed inside it.
2. **Audience** — who could observe, before and after; any widening
   named as the event it is.
3. **Alphabet** — the literal closed set of things that could have been
   said (small enough to print, or named by hash with its size).
4. **What crossed / what did not** — symbols chosen, offers refused,
   thefts blocked.
5. **Influence** — the counterfactual diff: what the sensitive slice
   *changed* about the output. This, not a bit count, is what "deeply
   aware of what privacy is being hurt" means operationally.
6. **Who computed and who saw** — the L4 line: the model vendor that
   ran the transform saw the slices it computed over. Never omitted.
7. **Cannot promise** — the standing non-claims, verbatim.
8. *Footnote:* the composition budget — charges this run, cumulative
   against ceiling, per (source × reader) account.

## 6. What this changes, and what it does not

Unchanged: every law in CALCULUS_LAWS, COALITION_LAWS, MEDIATION_LAWS;
the cut bound; the kernel; the Lean shadows; the sim. The math was
never wrong — it was fronted wrong.

Changed:

- **Pitch register.** The odometer-vs-codebook identity question stops
  being about bits; both postures pitch structurally, at two honesty
  levels. Codebook posture: "you granted this right; the output could
  only ever be one of these sentences; here is what your sensitive
  data changed; here is who saw what." Odometer posture (no closed
  alphabet — metered prose): the pitch leads with audience, purpose,
  diff, and the meter, and must say out loud that there is no closed
  alphabet. MARKETS.md carries the re-registration.
- **Receipts** restructure per §5 (`ip_trade_sim/report.py` first,
  chamber surfaces as they ship).
- **Grading roadmap.** When the formal lane resumes, it targets the
  context-poset grading with capacity as its homomorphic image (§4),
  not more precision on scalar bits.
- **Demo doctrine.** A demo that leads with a bit number is theater by
  this document's definition. A demo leads with the alphabet, the
  audience, and the counterfactual diff.

## Language to preserve

- "the alphabet is the object; the bit number is its logarithm"
- "a derivative is confined to its generating context unless a release
  transaction widens the context"
- "bits are the anti-laundering clause, not the guarantee"
- "the seatbelt, not the car"
- "nobody buys bits; people buy scoped rights and legible receipts"
