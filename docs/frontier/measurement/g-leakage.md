# g-leakage at the estimator boundary — the F1 design memo

*L5 MEASURE lane, 2026-07-06. Status: DESIGN + SPEC SKETCH. F1 remains
NOT IMPORTED in FRAMEWORKS.md; this memo is the first artifact of the
research track that row names. Nothing below is shipped, and nothing
below claims to be. The verdict is split and stated in §5: a v0
vocabulary import that can land now because it changes no decision
stream, and a v1 mechanism import held behind three named preconditions.*

**Sources this memo is answerable to:** FRAMEWORKS.md F1;
STORIES.md gap register G2 ("bits are not harm") and G5 ("never-reveal
as predicate"); `chambers/conformance/SPEC.md` §0–§2 (the integer
meter and the attested-estimator boundary); `chambers/kernel/
accountant.py` (`leakage_class`, `charge_coupled`);
`frontier/private-data-moats/README.md` + `lens-adversary.md` §(a) (the
concentrated-value regime); `primitives/coalition.ts` (reader-relative
leakage, declared reader models); `primitives/entropy.ts`
(`releaseGateIsConjunctionOfNumericAndOrdinal`). The QIF results cited
are from Alvim–Chatzikokolakis–McIver–Morgan–Palamidessi–Smith, *The
Science of Quantitative Information Flow* (the F1 row's named source);
the extraction exchange rates from the adversary lens (Tramèr et al.
2016; PAC `D/ε` framing).

---

## 1. The problem: the meter bounds a ratio; harm lives in the level

The accountant charges integer millibits against a declared subject
entropy and refuses at a ceiling. Restate exactly what that number is
and is not, because both halves are load-bearing.

**Where the meter is honest.** In the *flat regime* — value roughly
linear in bits, no single field worth more than its share of the
denominator — the millibit budget is a real defense. The adversary lens
proved the strong form: the `(source × reader)` lifetime ceiling is an
information-theoretic cap on what one reader can clone; a clone cannot
carry more mutual information about the sealed function than the bits
that crossed. QIF sharpens this into a theorem the meter can point at.
Define, for a secret X with prior π and a gain function g(w, x) — the
value to the attacker of taking action w when the secret is x — the
**g-vulnerability** V_g(π) = max_w Σ_x π(x)·g(w,x), and its posterior
V_g(π, C) after observing the channel C. The **"Miracle" theorem** says:
for *every* non-negative gain function g and *every* prior, the
multiplicative g-leakage V_g(π,C)/V_g(π) is bounded by the channel's
Bayes capacity — which is, in log form, bits of the same species the
estimator already attests at the adversarial maximum. So the existing
integer charge genuinely bounds **the factor by which any attacker
goal's vulnerability can multiply**. That is not theater; it is rare
and worth stating loudly.

**Where the meter is theater.** The bound is on the *ratio*. Harm lives
in the *level*, and the level is set by where the goal starts. Take the
register's own witness, the "which house" bit. A diligence corpus
declares 512 bits of structural entropy; the attacker's entire goal is
one predicate over it — *which of the 1024 candidate properties is the
target*. Prior one-try vulnerability on that goal: 1/1024. Ten bits of
leakage multiply it by 2^10 — to 1. The meter charged 10,000 mbits
against a 512,000-mbit denominator and printed `negligible` in honest
integer arithmetic; the multiplicative bound held *with equality*; and
the moat is gone. One decision-boundary bit is the whole moat
(lens-adversary §(a): distillation of a low-D decision boundary is
UNPRICEABLE; `C < D/ε` fails; "G2 cuts toward the attacker"). A
megabyte of trivia moves no goal anyone holds; one bit of "which house"
moves the only goal that matters from 0.1% to certainty. Same meter,
same integers, opposite verdicts about the world.

G2 has held this as a permanent apology: "bits are not harm," kept as a
conjunction with an unformalized ordinal review. The QIF observation is
that the apology has a missing index. "Harm" was never a property of
the bit count; it is a property of the pair (bit count, attacker goal).
Gain functions are the formal object for the second coordinate. What
g-leakage offers G2 is not a way to fold harm into the meter — the
register's own direction line forbids that, correctly — but a way to
turn "bits are not harm" from an unparameterized confession into a
**parameterized calculus**: *bits are not harm; bits-toward-a-declared-
goal, denominated in that goal's own entropy, are the auditable proxy
for one named class of harms, and here is the class.*

One more theorem sets the ceiling on ambition, and §4 leans on it. The
**refinement order** (the Coriaceous theorem): channel B leaks no more
than channel A *for every prior and every gain function* if and only if
B factors through A by post-processing (B = A·R). Robust dominance —
"safe against EVERY attacker goal" — is exactly as strong as a
*structural* fact about the channel, and is obtainable in no other way.
No numeric bound taken over a proper subclass of goals ever licenses
the universal quantifier. Keep that; it is the spine of the refusals.

## 2. The proposal: gain-function classes as declared estimator vocabulary

### 2.1 The design in one sentence

A declared attacker goal is a **derived secret**: give it its own
account with its own entropy denominator, let the existing integer
machinery — leakage classes, incident latch, coupled all-or-none
refusal — price it with zero new decision logic, and let the estimator
attestation say *which class of goals* its worst-case was taken over,
so the receipt can state coverage instead of implying it.

The failure in §1 was not an arithmetic error. `leakage_class` did
exactly what SPEC §1.5 says. It was a **denominator error**: the
which-house bit was charged against the whole file's 512,000 mbits when
the goal it services has 10,000 mbits of entropy, total. g-leakage, at
this boundary, *is* the discipline of charging declared goals against
their own denominators. That reduction — from "import a real-valued
vulnerability calculus" to "register the right accounts and say so on
the attestation" — is what makes F1 compatible with the stack instead
of a rewrite of it.

### 2.2 The gain-class vocabulary: small, coarse, few, DECLARED

This is the place to be loud, because it is where the import dies if
done wrong. A gain function is a real-valued matrix over actions ×
secrets. Admit it as a per-query free parameter and you have built
**unauditable discretion with a bibliography**: the operator shops for
a g under which any emission is negligible; the attestor tunes g until
the charge fits the budget; no stranger can recompute the verdict
because the verdict's premise was chosen after the fact. The F1 row
already names this price ("declared, coarse, and few, or they become
unauditable discretion"). The design answer is a **closed enum of
gain-function CLASSES**, declared at registration time, content-
addressed where parameterized, with membership changes requiring a
conformance-spec version bump — never a per-query, never a per-emission
knob. Three members at genesis:

| class | meaning | who may attest it | denominator |
|---|---|---|---|
| `full_secret` | g = identity on the registered subject: one-try Bayes guessing of the whole sealed secret. **Today's implicit default** — `worst_case_over_secrets: true` has silently meant exactly this since egress-accountant/1. | any admissible estimator | `subject_entropy_mbits`, as today |
| `declared_predicate` | a finite, content-addressed **predicate family** over the subject, declared owner-side at registration: {target-identity, go/no-go, approve/deny, …}. Each predicate is registered as its own account with its own owner-declared entropy. Worst-case is over the family: the attested charge covers capacity toward *every* predicate in it. | admissible estimator **plus** a resolvable `predicate_family` hash | each predicate's own entropy, per-account |
| `structural_all_g` | safety against **every** gain function — the Coriaceous quantifier. By §1's refinement theorem this is a structural fact, so it is assertable **only** for null channels: facts never registered, never leased (G5). An estimator may NEVER attest this class for anything that crosses; it exists so receipts can state the G5 fact in the same vocabulary as the rest. | no estimator — asserted by non-registration, checked structurally | none needed; the channel does not exist |

Named and deliberately NOT admitted at genesis: `k_list` (attacker wins
if the secret is in a guessed k-set — shortlist attacks) and
`metric_proximity` (gain decays with distance — valuations,
coordinates). Each is legitimate QIF and each drags a new declared
parameter (a k, a metric) onto the audit surface. They enter, if ever,
one at a time, each with a story that forces it and a version bump that
records it. Three classes is the budget; the enum growing past five is
the canary that discretion is leaking back in.

### 2.3 Where it rides the existing boundary — and what the kernel never learns

SPEC §0 already made the load-bearing cut: **estimation is not
accounting**. Everything transcendental — `log2`, and now V_g, priors
over candidate sets, maxima over strategy spaces — lives at the
estimator, whose independence is attested and whose output is an
integer. g-computations are estimation *par excellence*: they land
exactly where `log2` lives today, and nowhere else. The kernel still
receives integers, still runs steps A–E, still does integer
cross-multiplication for classes, still latches incidents on uncapped
demand. **No real number crosses into the decision path; the integer
meter is untouched.** Concretely:

1. **Attestation carries the class.**
   ```
   EstimatorAttestation := {
     estimator_id, independence, method, worst_case_over_secrets,
     gain_class:        "full_secret" | "declared_predicate" | "structural_all_g",
     predicate_family:  hash | absent,   # REQUIRED iff gain_class == declared_predicate
   }
   ```
   `worst_case_over_secrets` generalizes cleanly: worst case over
   secrets *and over every g in the declared class*. In v0 (see §5)
   these two fields are audit metadata like `method` — carried, not
   load-bearing. In v1 they become load-bearing via one new ordered
   admissibility check (`declared_predicate` without a resolvable
   `predicate_family` → inadmissible, reason
   `"undeclared_gain_family"`), which is a conformance version bump to
   `egress-accountant/2` and is priced as such in §5.

2. **Predicates are accounts.** Registering a predicate family creates,
   per predicate, an ordinary account: `register(key_P,
   subject_entropy_mbits = H(P), ceiling_mbits = declared)`. The
   which-house predicate over 1024 candidates registers at 10,000
   mbits. The predicate's entropy is an owner-signed declaration with
   the same epistemics and the same obligations as subject entropy —
   including **G13 depreciation**: the candidate set shrinks as the
   public world learns, and the monotone-down re-declaration discipline
   applies to predicate entropy verbatim.

3. **Emissions charge goal accounts coupled with the flat account.**
   An emission carrying capacity toward a declared predicate charges
   the predicate account *and* the flat subject account atomically —
   all-or-none, so a goal-ceiling refusal aborts the whole emission and
   no ledger states leakage that never flowed. This is `charge_coupled`
   — with one honest delta the kernel does not have today:
   `charge_coupled` currently applies **one** estimate to every key
   (right for coalition members, who all lose the same bytes), but a
   predicate account must be charged the estimator's capacity *toward
   P* (10 bits) while the flat account is charged the emission's full
   capacity (26 bits). The mechanism therefore needs **per-key
   estimates under the same atomicity** — a small, integer-only,
   spec-visible extension, named here as v1 precondition (ii), not
   smuggled. Until it exists, the only honest interim is charging every
   coupled account the maximum of the per-key estimates: conservative
   in direction, but it burns predicate budgets ~spuriously (a 26-bit
   emission with 1 bit toward P exhausts a 2-bit predicate ceiling
   26× too fast) — usable as a stopgap, mislabeled as a mechanism.

4. **The receipt states coverage.** One new receipt field, the whole
   point of the exercise:
   ```
   goal_coverage := {
     gain_class:       as attested,
     predicate_family: hash | absent,
     caveat:           fixed literal —
       "worst-case taken over the declared gain class only; attacker
        goals outside the class carry only the full_secret statement;
        reader auxiliary knowledge is declared, not observed"
   }
   ```
   The refinement order supplies the only honest reading, and the
   receipt now says it instead of hoping: *within* class G, the
   emission is safe against every goal — the principled sentence
   `worst_case_over_secrets` has gestured at since /1; *outside* G, you
   hold exactly the flat statement and nothing more.

Note what did NOT happen: no `harm_mbits` field, no per-fact weights
(the G2 direction line — "partitioning, not weights" — is satisfied
literally: a predicate account IS a partition of concern with its own
denominator), no real-valued V_g on any receipt, no change to
`leakage_class`, no change to steps A–E for single-key charges.

## 3. One worked example, end to end: the acquisition target among 1024

**Setup.** A family office's diligence chamber. Flat account: subject
`acq:file`, `subject_entropy_mbits = 512000`, `ceiling_mbits =
120000`. The owner declares gain class `declared_predicate` with a
one-member family {target-identity: which of 1024 shortlisted
properties}, content-addressed as `pf:9a41…`. Predicate account:
subject `acq:target-identity`, `subject_entropy_mbits = 10000` (2^10
equiprobable candidates), `ceiling_mbits = 2000` — the owner will sell
at most a fifth of the goal, ever, to this reader. Estimator
`indep-g`, independence `adversarial_review`, `worst_case_over_secrets:
true`, `gain_class: declared_predicate`, `predicate_family: pf:9a41…`.

**The naive world first — the honest-looking catastrophe.** No
predicate account exists; the flat account is the whole meter, exactly
today's stack. The reader buys two typed judgements. Emission 1
(comparables analysis): 12,000 mbits. Emission 2 (the full
recommendation, whose enum + text capacity resolves the target):
26,000 mbits, of which 10,000 are capacity toward target-identity —
a distinction the flat meter cannot see. Decision stream, per SPEC
§1.5 integer arithmetic:

| charge | cumulative | class test | receipt says |
|---|---|---|---|
| 1: 12,000 | 12,000 | 12,000·1000 = 1.2e7 ≤ 50·512,000 = 2.56e7 | **negligible** |
| 2: 26,000 | 38,000 | 3.8e7 > 2.56e7; ≤ 250·512,000 = 1.28e8 | **bounded** |

Every integer above is correct. The receipt reads: 38,000 of 512,000
mbits — 7.4% of the file, class `bounded`, no incident, budget 32%
consumed. And the reader's one-try vulnerability on the only question
that matters went from 1/1024 to **1**. They know the house. They
front-run the acquisition. The multiplicative bound of §1 held with
equality — vulnerability multiplied by exactly 2^10 — and the receipt
was arithmetic-honest and materially catastrophic. **That is the G2
apology in numbers: ~1 bit per hundred of the file, 100 cents on the
dollar of the moat.**

**The g-indexed world.** Same emissions, predicate account live,
charges coupled (per-key estimates: emission 1 carries 1,000 mbits
toward P — it narrows coastal vs inland; emission 2 carries 10,000).

*Emission 1* — flat 12,000 / predicate 1,000, atomic:
- predicate: demand 0→1,000; incident test 1,000·1000 = 1e6 <
  800·10,000 = 8e6 → no. Remaining 2,000 ≥ 1,000 → **EMITTED**,
  cumulative 1,000; class: 1e6 > 50·10,000 = 5e5, ≤ 250·10,000 =
  2.5e6 → **bounded**.
- flat: EMITTED, cumulative 12,000, class **negligible** (as before).
- One emission, two truthful sentences: *negligible against the file,
  bounded against the goal.* Same integers; the gain class licensed
  the second denominator.

*Emission 2* — flat 26,000 / predicate 10,000, atomic:
- predicate: demand 1,000→11,000; incident test 11,000·1000 = 1.1e7 ≥
  8e6 → **newly_incident = true** — the *ask itself* latches an
  incident on uncapped demand, exactly SPEC step B: a refusal does not
  un-ask, and someone just asked for the whole goal. Remaining =
  2,000 − 1,000 = 1,000 < 10,000 → **REFUSED_CEILING**, blocked
  latches.
- flat: individually innocent (remaining 108,000 ≥ 26,000) →
  **REFUSED_COUPLED**, undebited, cumulative stays 12,000. Nothing
  crossed; the ledger states no leakage that never flowed.
- Receipt for the refusal carries `goal_coverage`: gain class
  `declared_predicate`, family `pf:9a41…`, and the fixed caveat — the
  reader holds a `bounded` statement *within* the declared class and
  only the flat `negligible` statement outside it. In this world V_g
  on the goal went 1/1024 → 1/512 and stopped; the 1/512 → 1 jump is
  the refused branch.

**Punchline.** The naive receipt said `bounded` — 38,000 of 512,000
mbits, 7.4 cents of leakage on the dollar — while the attacker's
vulnerability on the declared goal went from 0.098% to 100%. The
g-indexed treatment refused the same emission at integer arithmetic
the existing kernel already knows how to do, latched the incident on
the demand, and put the attacker-goal caveat on the receipt. Every
real number in this section (V_g = 1/1024 prior; 1/512 after emission
1; 1 on the refused branch) appeared in the *estimator's* audit trail
and in this memo — never on a receipt, never in the decision path.

## 4. The refusals — the spine

**R1. No free gain functions, ever.** A per-query or per-emission g is
unauditable discretion; a stranger cannot recompute a verdict whose
premise was selected to produce it. Classes are a closed enum;
parameterized classes are content-addressed and declared at
registration; adding a class is a spec version bump. If, a year in,
receipts reference eleven gain classes, the import has failed and this
memo is the evidence against it. Budget: 3 at genesis, hard eyebrow at
5.

**R2. g-leakage prices a DECLARED adversary class, not the adversary.**
The predicate the owner never thought to register gets no account, no
denominator, no ceiling — only the flat statement. Gain functions do
not enumerate attacker interests; coalition.ts's standing non-claim
("the set of inferential targets of a derivative is unenumerable")
stands verbatim. Likewise **auxiliary knowledge remains frontier #5**:
V_g is computed against a declared prior, and the reader's true prior
is declared-not-observed (`auxiliaryIsDeclaredNotObserved: true`); the
low-confidence-charges-the-unconditional-ceiling rule is untouched. And
per-goal accounting inherits the identity problem wholesale: a Sybil
reader resets predicate ceilings exactly as it resets flat ones (G3,
L5). Anyone who reads this import as "the concentrated regime is now
defended" has read it wrong; it is *defended against the goals the
owner named, for the identities the substrate can hold*, and the
receipt now says so.

**R3. The universal quantifier belongs to G5 alone.** By the
refinement order, "safe against EVERY attacker goal" is a structural
fact: the channel factors through nothing, i.e., there is no channel.
That is precisely never-leased partitioning — zero ceiling by
non-registration — and it needs no gain function, no estimator, no
integer. `structural_all_g` exists in the vocabulary so that receipts
can state the G5 fact; it is inadmissible on anything that crosses.
The composition is clean and worth stating as doctrine: **facts whose
compromise is unacceptable get G5 (no channel, all-g safety); facts
that must cross under a nameable goal get a predicate account (declared-
class safety); everything else gets the flat statement (ratio bound
only).** Three rungs, each honestly labeled.

**R4. The G2 conjunction is not dissolved.** entropy.ts law:
`releaseGateIsConjunctionOfNumericAndOrdinal` — both conjuncts, always.
g-leakage gives the *ordinal half a calculus for its nameable part*:
each reviewer intuition of the form "this field is the crown jewel" is
a candidate predicate declaration, and the review's job comes to
include maintaining the predicate registry. But "I'd regret this" is
not a gain function; regret is not a predicate (G2's own words); the
subject's unarticulated preferences (G12) cannot be declared by
construction. The human conjunct absorbs everything the class
vocabulary cannot express, which is most things. The conjunction is
permanent; g-leakage moves individual items across it one declared
predicate at a time, and the residue never empties.

**R5. No real-valued vulnerability on receipts.** Quoting V_g = 0.032
on a receipt would be false precision three ways: it depends on a
declared prior (R2), a candidate-set size that depreciates (G13), and
an estimator's model of the emission's semantics (G8). Receipts carry
the gain class, integer millibits, and integer-permille leakage
classes — the same epistemics as today: **an upper-bound tripwire on
information toward the goal, not a posterior-vulnerability
certificate.** The reals stay in the estimator's audit trail where
`log2` already lives.

**R6. The capture surface widens; say so.** A predicate-capacity
estimate ("this recommendation carries 10 of the target's 10 bits") is
a semantic modeling claim, more capturable than `log2` of an enum's
cardinality (G8's systematically-under-counting estimator now has a
softer target). Mitigations are the ones already on the register — F8
audit lotteries, `estimator_payer` inadmissibility — plus one specific
to this import: predicate entropies are owner-signed and predicate
families content-addressed, so an under-count is convictable against a
fixed, recomputable premise. Not closed; priced.

## 5. Verdict

**Split. v0 lands now; v1 waits behind three named preconditions.**

**v0 — the vocabulary (import-now; zero conformance delta).**
`gain_class` + `predicate_family` on `EstimatorAttestation` as audit
metadata (non-load-bearing, like `method`), defaulting every existing
attestation to `full_secret` — which is not a change but a *confession*:
that is what `worst_case_over_secrets` has meant since /1. Plus the
`goal_coverage` receipt caveat with its fixed literal. No kernel code,
no decision-stream change, no golden-trace change; the entire delta is
that receipts stop implying a coverage they never had. This is the
smallest honest version, and it is worth landing on its own because
the caveat is true *today*, with or without the mechanism.

**v1 — the mechanism (wait; preconditions named).** Predicate accounts
charged coupled with flat accounts, load-bearing admissibility. Held
behind, in order:
1. **The predicate registry**: owner-signed predicate families,
   content-addressed, with owner-declared per-predicate entropy under
   G13's monotone-down depreciation discipline. Without this, predicate
   entropy is unanchored discretion and R1 falls at the first step.
2. **Per-key coupled estimates**: the `charge_coupled` generalization
   (one atomic charge, per-key integer estimates) as a conformance
   version bump to `egress-accountant/2`, with golden traces covering
   the coupled-refusal and incident-on-demand paths of §3.
3. **The one-import-in-flight discipline**: FRAMEWORKS' recommended
   order has F2 landed and F3 (the Lean accountable-safety campaign)
   ahead of F1. v1 is real spec churn and should not jump that queue;
   v0 doesn't touch the queue because it changes no mechanism.

**What this import explicitly does NOT claim**, compiled from §4 so
the register can quote one list: not harm pricing (G2's conjunction
stands); not coverage of undeclared goals (the adversary's interests
remain unenumerable); not auxiliary-knowledge closure (frontier #5);
not Sybil resistance (predicate ceilings reset with identity, G3/L5);
not a posterior-vulnerability certificate (tripwire epistemics,
unchanged); not a substitute for G5 (which keeps the only universal
quantifier); not a defense of low-D moats against a reader you chose
to sell to — it makes the price of that sale visible and refusable
*per declared goal*, which is all a meter can honestly do.

The honest one-sentence summary for the F1 row when this lands:
*g-leakage entered as a receipt-vocabulary fact and a denominator
discipline — the meter still charges integers, the estimator still
owns the reals, the owner now names the goals, and the receipt now
names what it never covered.*
