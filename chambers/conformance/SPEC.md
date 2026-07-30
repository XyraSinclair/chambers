# The Egress Accountant — a counterparty-compilable specification

**Version:** `egress-accountant/1`
**Status:** normative. This document, not any one program, is the authority.

This is the language-independent specification of the *semiring egress
accountant* that recurs across the Scry Chambers slices (`ip_trade_sim`,
`d1_bounty`, `intro_clearing`). Its purpose is to make one claim TRUE rather
than asserted:

> A second, independently-written implementation, reading only this document,
> agrees **bit-for-bit** with the reference on a corpus of golden traces.

An implementer MUST be able to produce a conforming accountant from this file
alone, with no access to any reference source code. If you are reading this to
implement it: do not seek the Python. Divergence between your implementation
and the reference is either a bug in yours, a bug in the reference, or an
ambiguity in this spec — and all three are findings worth surfacing.

---

## 0. The one design decision: estimation is not accounting

The accountant charges an **information budget** in bits: every typed emission
carries some upper-bound channel capacity toward reconstructing a sealed
secret, and the accountant refuses emissions that would cross a ceiling.

Computing *how many bits* an emission carries — `log2` of a choice space,
`log2(k!)` of an ordering, a byte-length times 8 — is **estimation**. It
involves transcendental functions whose last-bit results are not guaranteed
identical across languages or libm versions. Estimation is therefore **out of
scope for this specification.** It is performed by an *estimator*, whose
independence is attested (§3), and whose output is an integer.

What remains — accumulate, compare to a ceiling, classify a fraction, latch an
incident, gate on estimator admissibility — is **accounting**, and it is
**pure integer arithmetic**. That is the counterparty-compilable core, and it
is all this document specifies.

**Unit.** All charges are integers in **millibits** (`mbit`), where
`1 bit = 1000 mbit`. There is no floating-point value anywhere in a conforming
accountant. An estimator that computes `1000 * log2(3) = 1584.962…` rounds to
an integer millibit charge (`1585`) by a rule it documents for its own
reproducibility; the accountant receives `1585` and never sees the real.

An implementation that performs floating-point arithmetic in the decision path
is **non-conforming** even if it happens to agree on a given corpus.

---

## 1. Data model

### 1.1 CompositionKey

The adversary's join key — what accumulates, not the run id.

```
CompositionKey := (subject: string, query_family: string, audience: string)
```

Two charges share a budget iff all three fields are equal. Implementations MUST
compare the three string fields directly (byte-equal). Any hashing is a
presentation detail and MUST NOT affect the decision stream.

### 1.2 CapacityEstimate

The attested integer charge for one emission, already reduced to millibits by
the estimator. Its internal breakdown is carried for audit but only the total
is load-bearing.

```
CapacityEstimate := {
  enum_value_mbits:     int >= 0,   # log2 of the verdict's legal choice space
  ordering_mbits:       int >= 0,   # log2(k!) over reported orderings
  field_presence_mbits: int >= 0,   # presence/absence channel
  text_mbits:           int >= 0,   # byte-ceiling * 8000 (charged at ceiling, not honest content)
  side_channel_mbits:   int >= 0,   # declared residual side channel
  channel:              string,     # label, e.g. "vex_verdict"
}
total_mbits(e) := e.enum_value_mbits + e.ordering_mbits
                + e.field_presence_mbits + e.text_mbits + e.side_channel_mbits
```

`total_mbits` is a plain integer sum. It cannot overflow a 64-bit signed
integer for any legal corpus (see §6 bounds).

### 1.3 EstimatorAttestation

Every budget is only as sound as its estimator. A paid agent that meters its
own leak will under-count and break the ceiling silently, so the estimator's
independence is attested and the accountant REFUSES to charge against an
inadmissible one.

```
EstimatorAttestation := {
  estimator_id:            string,
  independence:            string,   # one of the classes below
  method:                  string,   # audit label; not load-bearing
  worst_case_over_secrets: bool,
}

VALID_INDEPENDENCE := { "operator", "role_separated", "adversarial_review" }
```

**Admissibility** (pure predicate, returns admissible: bool, and a fixed
reason string when not):

1. if `independence == "self_interested"` →
   not admissible, reason `"self_interested_estimator"`.
2. else if `independence ∉ VALID_INDEPENDENCE` →
   not admissible, reason `"unknown_independence_class"`.
3. else if `worst_case_over_secrets == false` →
   not admissible, reason `"estimate_not_worst_case"`.
4. else → admissible.

The three checks are ordered; the first failing check supplies the reason.

### 1.4 CompositionState

Per-CompositionKey accumulator. Created by `register`, mutated by `charge`.

```
CompositionState := {
  key:                  CompositionKey,
  subject_entropy_mbits: int > 0,   # structural entropy of the sealed subject
  ceiling_mbits:        int >= 0,   # structured-bits ceiling for this key/window
  cumulative_mbits:     int = 0,    # what ACTUALLY crossed (accepted debits)
  demanded_mbits:       int = 0,    # what was ASKED (every admissibly-estimated attempt)
  blocked:              bool = false,
  incident:             bool = false,
}
```

`cumulative_mbits` and `demanded_mbits` are two distinct monotone
(non-decreasing) counters. The ceiling gates on **leakage** (`cumulative`); the
incident latches on **demand** (`demanded`). Refusals accrue demand but not
leakage — a refusal does not un-ask.

### 1.5 Leakage classes

Thresholds as a per-mille fraction of `subject_entropy_mbits`, applied to
`cumulative_mbits` capped at the entropy (fraction never exceeds 1).

```
NEGLIGIBLE_PERMILLE := 50    # 0.05
BOUNDED_PERMILLE    := 250   # 0.25
MATERIAL_PERMILLE   := 500   # 0.50
UNSAFE_PERMILLE     := 800   # 0.80
```

`leakage_class(cumulative_mbits, subject_entropy_mbits)` — computed with integer
cross-multiplication, no division:

```
let c := min(cumulative_mbits, subject_entropy_mbits)   # cap the fraction at 1
let s := subject_entropy_mbits                            # s > 0 by construction
if c * 1000 <= NEGLIGIBLE_PERMILLE * s : "negligible"
else if c * 1000 <= BOUNDED_PERMILLE * s : "bounded"
else if c * 1000 <= MATERIAL_PERMILLE * s : "material"
else if c * 1000 <= UNSAFE_PERMILLE  * s : "unsafe"
else : "reconstructed"
```

The comparisons are inclusive (`<=`) at each boundary, checked in order; the
first satisfied branch wins. (`c * 1000` and `permille * s` are ≤ ~10^12 for
any legal corpus and fit in signed 64-bit.)

---

## 2. Operations

An accountant exposes two operations. All state lives in per-key
`CompositionState` objects held in a map keyed by the `CompositionKey`.

### 2.1 register(key, subject_entropy_mbits, ceiling_mbits)

Idempotent create. If `key` is already present, return the existing state
**unchanged** (do not reset counters, do not overwrite entropy/ceiling). If
absent, create a fresh `CompositionState` with the given entropy and ceiling
and zeroed counters/flags. `subject_entropy_mbits` MUST be `> 0`; a
non-positive value is a malformed trace (see §5, the harness rejects it before
replay).

### 2.2 charge(key, estimate, estimator, tick) → Decision

The state for `key` MUST already exist (via `register`). `tick` is an integer
label carried into the decision for audit; it does not affect control flow.

Execute these steps **in order**. The first step that returns, returns.

**Step A — estimator admissibility.**
Evaluate §1.3. If not admissible:
- append nothing to either counter (an unmetered claim cannot meter pressure);
- return Decision {
    accepted: false,
    reason_class: `"REFUSED_ESTIMATOR"`,
    reason_detail: the admissibility reason string,
    cumulative_mbits, demanded_mbits, blocked, incident, leakage_class  ← all read from current (unchanged) state,
    newly_incident: false
  }.

**Step B — accrue demand and evaluate incident.**
The estimator is admissible, so the attempt carries real extraction pressure
whether or not it is ultimately emitted.
```
let bits := total_mbits(estimate)
state.demanded_mbits := state.demanded_mbits + bits
let newly_incident := (state.incident == false)
                      and (state.demanded_mbits * 1000 >= UNSAFE_PERMILLE * state.subject_entropy_mbits)
if newly_incident : state.incident := true
```
Note the incident test uses **uncapped** `demanded_mbits` (demand can exceed
subject entropy; the pressure is real). Contrast the class test in §1.5, which
caps `cumulative`.

**Step C — already blocked.**
```
if state.blocked :
  return Decision {
    accepted: false, reason_class: "REFUSED_BLOCKED", reason_detail: "budget_already_blocked",
    cumulative_mbits: state.cumulative_mbits, demanded_mbits: state.demanded_mbits,
    blocked: true, incident: state.incident,
    leakage_class: leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
    newly_incident
  }
```

**Step D — would exceed the ceiling.**
```
let remaining := max(0, state.ceiling_mbits - state.cumulative_mbits)
if bits > remaining :
  state.blocked := true
  return Decision {
    accepted: false, reason_class: "REFUSED_CEILING", reason_detail: "would_exceed_ceiling",
    cumulative_mbits: state.cumulative_mbits, demanded_mbits: state.demanded_mbits,
    blocked: true, incident: state.incident,
    leakage_class: leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
    newly_incident
  }
```
(The comparison is strict: an emission whose bits exactly equal `remaining` is
admitted, and then blocks the state — see Step E.)

**Step E — emit.**
```
state.cumulative_mbits := state.cumulative_mbits + bits
if state.cumulative_mbits >= state.ceiling_mbits : state.blocked := true
return Decision {
  accepted: true, reason_class: "EMITTED", reason_detail: "emitted_debited",
  cumulative_mbits: state.cumulative_mbits, demanded_mbits: state.demanded_mbits,
  blocked: state.blocked, incident: state.incident,
  leakage_class: leakage_class(state.cumulative_mbits, state.subject_entropy_mbits),
  newly_incident
}
```

### 2.3 Decision

The full observable output of one `charge`. This — the ordered stream of
Decisions over a trace — is what conformance compares.

```
Decision := {
  accepted:       bool,
  reason_class:   enum { EMITTED, REFUSED_ESTIMATOR, REFUSED_BLOCKED, REFUSED_CEILING },
  reason_detail:  string,        # from the fixed set of literals used above
  cumulative_mbits: int,
  demanded_mbits:   int,
  blocked:        bool,
  incident:       bool,
  leakage_class:  enum { negligible, bounded, material, unsafe, reconstructed },
  newly_incident: bool,
}
```

`reason_detail` literals (the complete set): `self_interested_estimator`,
`unknown_independence_class`, `estimate_not_worst_case`,
`budget_already_blocked`, `would_exceed_ceiling`, `emitted_debited`.

---

## 3. The golden-trace format

A golden trace is a single JSON object, UTF-8, describing one accountant run
and its expected decision stream.

```jsonc
{
  "spec": "egress-accountant/1",
  "name": "lane-c-extraction",
  "ops": [
    { "op": "register", "key": ["wolfden:diff", "reachability", "cardinal"],
      "subject_entropy_mbits": 512000, "ceiling_mbits": 120000 },
    { "op": "charge", "tick": 1,
      "key": ["wolfden:diff", "reachability", "cardinal"],
      "estimate": { "enum_value_mbits": 1585, "ordering_mbits": 4585,
                    "field_presence_mbits": 2000, "text_mbits": 64000,
                    "side_channel_mbits": 1000, "channel": "vex_verdict" },
      "estimator": { "estimator_id": "indep", "independence": "adversarial_review",
                     "method": "static_schema_bound", "worst_case_over_secrets": true } }
    // ... more charges
  ],
  "expected": [
    { "accepted": true, "reason_class": "EMITTED", "reason_detail": "emitted_debited",
      "cumulative_mbits": 73170, "demanded_mbits": 73170, "blocked": false,
      "incident": false, "leakage_class": "bounded", "newly_incident": false }
    // ... one Decision per "charge" op, in order
  ]
}
```

Rules:
- `key` is a 3-element array `[subject, query_family, audience]`.
- `ops` is an ordered list; `register` ops produce no Decision, `charge` ops
  produce exactly one, appended to the actual stream in order.
- `expected` has exactly one entry per `charge` op, in the same order.
- **Conformance:** an implementation replays `ops`, collects its own Decision
  stream, and it MUST equal `expected` element-wise and field-wise. Integers
  compare as integers; enums and strings compare byte-equal; bools compare
  directly. Any mismatch is a conformance failure that MUST be reported with
  the trace name, the charge index, and the diverging field.

A conforming test harness runs every trace in `traces/` and fails if any
diverges.

---

## 4. Worked micro-example (normative)

One key, `subject_entropy_mbits = 100000`, `ceiling_mbits = 1000000` (ceiling
deliberately above the UNSAFE line to show incident firing on the accepted
path). Estimator admissible. Each charge `total_mbits = 80000`.

- **charge 1:** demand 0→80000. incident test: `80000*1000 = 8.0e7` vs
  `800 * 100000 = 8.0e7` → `>=` true → **newly_incident = true**, incident set.
  Not blocked; remaining 1000000 ≥ 80000 → emit. cumulative 0→80000.
  class: `min(80000,100000)=80000`; `80000*1000=8.0e7` vs `500*100000=5.0e7`
  (>), vs `800*100000=8.0e7` (`<=`) → `unsafe`.
  Decision: accepted, EMITTED, cum 80000, dem 80000, blocked false,
  incident true, class unsafe, newly_incident true.
- **charge 2:** demand 80000→160000. incident already true → newly_incident
  false. emit → cumulative 160000, capped to 100000 for class → `reconstructed`.

This example exists so an implementer can check the two easy-to-miss points:
incident uses **uncapped demand** with `>=`, and `newly_incident` is true on
exactly the transition charge.

---

## 5. Malformed traces

The harness (not the accountant) validates a trace before replay and rejects,
rather than replays, any trace with: a `charge` whose `key` was never
`register`ed; a `register` with `subject_entropy_mbits <= 0`; a negative
millibit field; or an `expected` length ≠ number of `charge` ops. A conforming
accountant may assume traces are well-formed; robustness to malformed traces is
the harness's job, not part of the compiled-agreement claim.

---

## 6. Bounds (why signed 64-bit suffices)

For any legal corpus in this repo: millibit fields ≤ 10^7 each, ≤ 8 components,
≤ 10^4 charges per key. So `demanded_mbits ≤ ~10^12`, and the largest product
in any comparison (`demanded_mbits * 1000` or `permille * subject_entropy`)
is ≤ ~10^15 — comfortably inside signed 64-bit (`~9.2e18`). Implementations
MUST use at least 64-bit signed integers. They MUST NOT use floating point.

---

## 7. What this specifies, and what it does not

**Specifies:** the accountant's decision function — the counterparty-compilable
core. Two implementations conforming to this file agree bit-for-bit, which is
the property every Chamber receipt has until now only *asserted*.

**Does not specify** (each is named as out of scope, not hidden):
- **Estimation.** How millibit charges are derived (`log2`, byte ceilings). The
  estimator is attested (§1.3) and replaceable; its rounding rule is its own to
  document. The float lives here, deliberately, outside the compiled core.
- **The ordinal / prose release gate.** This is the numeric half of the release
  conjunction only (cf. `entropy.ts`). An ordinal `EntropyReview` over a prose
  channel is a separate mechanism.
- **Downstream economics.** Oracle scoring, settlement, payout authorization
  (`d1_bounty`) sit above the accountant and are not part of this core.
- **Harm modelling.** Bits are an upper-bound tripwire, not a secrecy proof and
  not a harm measure; one bit plus a tiny repro can still be a live weapon.
