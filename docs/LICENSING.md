# Licensed latent formation — the rights stack

Prose that argues; `primitives/` decides. This document names the *economic*
object the substrate sells, maps it onto the canon records that already
mechanize it, and marks what is missing. It exists because the framing "users
license their data" is wrong in a way that costs the whole thesis:

> Users do not license their data away. They license **bounded latent
> formation**: agents may create specified derivative states under typed
> disclosure rules, with coalition provenance and economic attribution.

## The object being licensed

Not raw private data. Not public aggregate data. A third thing —
**coalitional derivative data**: output produced by a bounded agent from
multiple private silos, whose meaning, value, and safety depend on the exact
coalition of silos that produced it.

The reason is not vibes; it is the same inequality the accountant already
charges for. An agent computes `Y = f(S₁ … Sₙ)`. However small `Y` looks —
a score, a verdict, a "you two should talk" — it has
`I(Y; Sᵢ | public) > 0` for every participating silo: the output is a
compressed function of private worlds, not "just the agent's opinion." And
often the value is precisely in the jointness
(`value(Y) ≠ Σᵢ value(f(Sᵢ))`): the match, the complementarity, the
negotiation frontier exist only because multiple private contexts were
jointly traversed. Such an output is **not separable from its inputs** —
sharing it outside the generating coalition both leaks private state and
destroys the exclusivity/option value that made the computation worth doing.

None of this is new law here — it is why the canon already holds:

- the coalition is the **zero point of the leakage metric, not a fortress**
  (`COALITION_LAWS`); synergy IS cross-exposure, consented at formation;
- `CoalitionalDerivative.audience = "generating_coalition"` with escrowed
  full latent and typed member projections, each projection debiting every
  *other* member's `ExposureAccount`;
- structure judgements are **tuple-scoped** — the exact k-tuple is the
  judgement's identity, and any sub/superset visibility is a `WideningEvent`
  (`MEDIATION_LAWS`);
- charge-kernel/2 implements the two-directional inseparability at the meter:
  `MediationSession` charges **observation** (agent-as-reader across the
  tuple) and **emission** (requester-as-reader against every member,
  atomically — all accounts accept or none is debited).

The clean invariant, canonical phrasing:

> **A coalitional latent is confined to its generating coalition unless a
> release transaction widens the audience.**

Widening is a priced, consented, one-way event — never a side effect.
(One-way-ness is L4 target #3 in `ASSURANCE.md`: PROVEN —
`chambers/lean/ChargeKernel/Widening.lean`, `audience_never_narrower` /
`confinement_not_reestablishable`, corollaries of an exact
audience-provenance equality. The proof covers the algebra; that every
deployed disclosure path routes through the algebra remains L1–L3's job.)

## The rights stack

"Can this agent access my data?" is the wrong question. The licensable
surface decomposes into graded, separable rights. Each row maps onto records
that already exist — or names its absence honestly.

| # | Right | What it permits | Canon mechanism | Status |
|---|---|---|---|---|
| 1 | **Execution** | Run against a silo; retain nothing raw | `Grant` → `Transform` → `EnvRecipe` (no raw egress by default, paths virtualized) | Mechanized |
| 2 | **Silo-local annotation** | Write typed annotations back into the owner's own chamber | `Annotation` under owner `Visibility`; market pays for *accepted* annotations, never access | Mechanized |
| 3 | **Coalition-bound derivative** | Create an output that exists only for a specified set of silos | `Coalition` + `ExposureConsent` + `CoalitionalDerivative` + per-member projections debiting `ExposureAccount`s | Mechanized; metered by charge-kernel/2 |
| 4 | **Release-screen** | Propose the derivative for external disclosure, subject to review by affected parties | `Gate` conjunction (numeric accountant ∧ ordinal review), `WideningEvent` priced via destroyed-option-value estimates, owner decision required | Mechanized; review quality is L5 (priced, not proven) |
| 5 | **Public aggregate** | Cross into public only above an anonymity/aggregation threshold | `EntropyPool` bucket claims — the claim states the set size *achieved*, never the mechanism hoped | Named; **empirical, not mechanical** (frontier #19) |
| 6 | **Model-improvement** | Train/fine-tune/distill on interactions or outputs | `trainingUseForbidden: true` (environment.ts, hard default at the worker); `Coalition.modelImprovementChannel: "forbidden_declared" \| "dp_budgeted" \| "unbounded_declared"` — "gradients are egress: training on coalition outputs is a widening to the model-user audience with unbounded retention" (coalition.ts) | **Declared, not enforced** — canon says so verbatim; no priced grant form yet |

Right #6 is where long-run data value gets laundered away on every incumbent
platform, which is exactly why it must never be bundled. The canon already
separates it (a coalition *declares* its model-improvement channel at
formation, and the caveat is in the type: "a policy statement, not an
enforcement claim") — but a *priced* form (an expensive, explicitly-widening
grant whose audience is the model's entire user population, with `dp_budgeted`
as the only non-forbidden lane that even names a mechanism) would need a new
admission-tested primitive, not a flag flip. Until then the default stays
forbidden and the honest status stays *declared, not enforced*.

Two rights that look absent but are deliberately NOT rights: **seeing a
derivative** (reading is an exposure event that debits the other members —
`MEDIATION_LAWS`; it is metered, not licensed away), and **silence**
(non-relation is a judgement with the same confinement; denials, absences,
failed probes, and "nothing found" leak structure — negative evidence gets
identical protection, and coalition metadata including silence is an
emission).

## Why this appreciates (the singularity clause)

As cognition gets cheap, generation stops being scarce. What stays scarce:
private context, lawful custody, provenance, consent surfaces, high-signal
joins across private worlds, exclusive option value, and the willingness of
humans and orgs to deposit real context. A substrate that can safely compute
over private worlds is then not a SaaS database but an **epistemic
clearinghouse** — a confidential inference market. Not a data broker: the
broker's business is the leak; this substrate's business is the meter. The
(source × reader) exposure ledger compounds with use, and metering honesty
cannot be retrofitted by platforms whose unit economics require the leak —
that is the moat stated in `ASSURANCE.md`'s trust equation, restated here as
the licensing thesis.

## Standing non-claims

Everything above inherits the open frontier: identity/Sybil (#1, #17),
unenumerable inferential targets (#16 — the affected exceed the
contributing; screens cover *named* subjects only), declared-not-observed
reader models (#18), empirical pool sizes (#19), the human-head channel
(#7), and TCB trust (#6). A license is a typed, priced, auditable *promise
structure* — it is not perfect secrecy, and no sentence in this file may be
quoted without that caveat.
