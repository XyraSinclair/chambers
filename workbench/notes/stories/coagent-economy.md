# Story 9 — The coagent economy: orchestrating cognitive work at scale

*Full-depth companion to STORIES.md §9. This is the story the whole stack
exists for: not one agent over one tuple, but an ECONOMY — hundreds of
agents, chained judgements, cascade settlement — where the composition of
primitives is the product, and every law proven for one session must
survive the tree.*

---

## Cast & private worlds

A pension fund wants one judgement: *which of these forty biotech
startups deserves a term sheet?* No single agent can produce it. The
answer lives across forty startups' private trial data, a dozen domain
experts' private experience (each expert's pattern-library of failed
programs IS their livelihood), two hospital systems' outcome records, and
the public literature.

**Aster**, an orchestrator agent, is paid to *convene* the answer. The
design decision that makes the economy honest: **Aster holds no
privileged access whatsoever.** It never sees raw member data — only
typed, metered judgements, each charged against its own exposure
accounts like any other reader. Its power is compositional (which
sessions to convene, in what order), not informational. An orchestrator
is just an agent with a good address book and a budget.

## The run — a judgement supply chain

```
  40 × trial-data sessions      12 × expert sessions      2 × outcome sessions
   (startupᵢ × analyst-agent)   (expertⱼ × analyst-agent)  (hospitalₖ × agent)
          │ typed verdicts             │ typed patterns          │ typed rates
          └──────────────┬────────────┴──────────┬──────────────┘
                    synthesis session (Aster convenes)
                          │ one ranked judgement
                    pension fund (the requester-as-reader)
```

Layer 1: leaf sessions. Each is an ordinary `MediationSession` — an
analyst agent admitted to one startup's trial chamber emits a typed
verdict (endpoint-strength enum, enrollment-risk ordinal, a
red-flag bucket). Metered exactly as every story before this one.

Layer 2: synthesis. The leaf judgements are now ARTIFACTS INSIDE the
synthesis session's working chamber. The synthesis agent reads forty
verdicts and twelve expert patterns and emits one ranked shortlist
toward the fund.

**And here the composition question becomes the whole story:** the
shortlist carries information about startup #17's trial data — two hops
from its chamber. Who has startup #17's exposure account been charged
for the FUND as a reader?

## The law the chain needs: provenance closure, bounded by DPI

The ledger already contains the answer's raw material. Every leaf
judgement is a ChargeEvent whose key names its source:
`exposure_key(startup17_trials, analyst_agent)`. So the synthesis
emission's coupled charge set is **computable from the ledger itself**:
the transitive closure of sources feeding its inputs. The rule the
orchestration layer must enforce (and the audit must convict):

> An emission's atomic charge set is the provenance closure of the
> judgements it consumed: every original source whose bits could have
> reached this output charges the terminal reader.

The mathematics is on our side, and it is the *data-processing
inequality*: a downstream judgement cannot carry more information about
startup #17 than crossed the first hop. So the chain's charge against
`exposure_key(startup17, fund)` is capped by min-capacity along the
path — charging the full first-hop capacity at every downstream hop is
conservative and honest (an upper bound, the same posture as byte
ceilings), and DPI licenses *tightening* it later without ever
under-charging. Composition inherits the meter's one-sided honesty.

Today this rule is enforceable by a DISCIPLINED orchestrator
(`charge_coupled` accepts any key set; Aster carries the closure
forward) and checkable after the fact by a stranger walking the ledger's
provenance graph. What is missing is the kernel making it *mandatory* —
an audit family that reconstructs the closure from charge inputs and
convicts an emission whose coupled set dropped a source. That is **G14**,
and it is the exact composition analog of "the emission is not separable
from its inputs": *the emission is not separable from its ancestry.*

## The money — cascade escrows, conservation across the tree

The fund escrows once, toward Aster, bound to its own terminal exposure
keys. Aster sub-escrows to every leaf agent, each bound to that leaf
session's keys, each with `default_on_expiry` declared. Releases cascade
upward as receipts complete: leaf verdicts release leaf escrows;
the synthesis receipt releases Aster's.

Three proven properties compose without new work:

- **Conservation holds over the whole tree** — Σ available + Σ escrow
  remainders = Σ deposits is arithmetic over the one merged ledger,
  indifferent to tree depth (Settlement.lean never cared how many
  escrows there were).
- **Anti-holdup composes** — if Aster is slashed, goes bankrupt, or
  simply vanishes mid-tree, every leaf worker self-serves its declared
  default after expiry (S8). A failed orchestrator cannot strand a
  hundred subcontractors' earnings: this is what makes SUBCONTRACTING
  safe for the small party, and it shipped last tranche.
- **One artifact audits the whole economy** — the CRDT means two hundred
  agents across a dozen nodes produce ONE mergeable jsonl the fund (or
  a regulator, or a startup checking its own exposure) re-audits with
  the standing verifier. The court file scales because it is a fold,
  not a transcript.

## The meta-economy: who meters the meterers

At economy scale, the trust roles are themselves paid agents:

- **Estimators** sell attestations. Their methods are their IP — an
  estimator's calibration corpus lives in its own chamber, and its
  attestation quality is *adversarially purchasable*: the L3
  estimator-probe (the Feynman lane — smuggle a known secret through a
  metered channel, measure achieved vs charged) becomes a standing
  BOUNTY: anyone who demonstrates achieved > charged on a live channel
  is paid from the estimator's posted bond. Red-teaming as a job; the
  meter's honesty gets a market price.
- **Canonicality reviewers** sell admission judgements (was the
  requested capacity justified?). Their consistency is auditable across
  the ledger — the same fold that catches over-spends can score a
  reviewer's admission pattern against peers.
- **Settlement issuers** compete. An issuer's ledgered history — refusal
  patterns, default-resolution frequency, fee schedules — is exactly the
  reputation surface the Ethereum-test demands (no unauditable
  discretion), and it is ALREADY in the artifact.

The recursion is the design working, not a regress: every meta-role's
work product is itself typed, chambered, metered cognitive work. The
economy audits its own infrastructure with the same six event kinds.

## What this story exposes

**G14 — provenance closure** (above): make "the emission is not
separable from its ancestry" an audit family, not an orchestrator's
discipline. Ledger-computable today; DPI licenses tightening; the
conservative form needs no new event kinds — only a new I-code walking
the graph the ledger already stores.

**G15 — the topology channel.** Who was convened against whom is itself
sensitive: the fund's *interest* in startup #17 is a secret the session
graph broadcasts to every ledger holder. Tuple membership, session
timing, escrow shapes — metadata the meter does not price. The honest
direction is the EntropyPool trick applied to *visibility*: batch
session formation to cadence, pad the convened set, state the achieved
anonymity set on the receipt ("this window convened 40 sessions of which
yours was one") — declared and priced like everything else, never
"unlinkable." Until then: the ledger's audit surface is itself a
disclosure surface, and story 9's fund should assume the topology leaks.

## Why this is where the thesis pays

Every prior story is one session. This one is why the primitives had to
be *algebraic*: atomicity had to be coupled (so it could extend to
closures), the ledger had to be a CRDT (so two hundred agents produce
one artifact), settlement had to conserve by arithmetic (so trees don't
need trust), holdup had to die by declared default (so subcontracting is
safe for the weak side), and the meter had to be an upper bound (so DPI
composes it). Orchestrating entire cognitive work economies is not a
feature to add later — it is the load the kernel's laws were shaped to
bear, and the two gaps it exposes (G14, G15) are the next two theorems,
not the next two products.
