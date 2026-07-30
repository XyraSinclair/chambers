# Confidential IP trades: what is actually feasible, and the substrate for it

The ambitious goal: let AI labs — and independent researchers — trade IP
(weights, training techniques, curated datasets, eval results) so that more
beautiful models propagate and contributors are compensated fairly, **without
either side revealing the crown jewels prematurely or trusting a party that
sees both secrets.**

This is the synthesis of a 105-agent, crypto-reality-checked pass. Method: 11
private-computation primitive families characterized (textbook-true vs.
practical-at-model-scale-2026); the trade decomposed into 10 atomic
sub-problems; a primitive × sub-problem feasibility matrix; **every optimistic
cell adversarially attacked by a hardnosed cryptographer**; four committed
substrate designs judged on rigor/expressiveness/adoptability/interpretability;
three sharp tensions debated to adjudication; a completeness critic. Raw result
archived as `workflow-result.json`.

The design landed in canon as **`../../primitives/iptrade.ts`**.

---

## 1. The feasibility floor (2026) — this is the differentiated understanding

The single most important output. What can actually carry an IP trade *today*:

| Primitive | Feasible at model scale, 2026 | Verdict |
|---|---|---|
| **TEE / remote attestation** (H100/Blackwell CC) | **practical now** | attestation overhead <7%; the workhorse |
| **Commitments / VRF / timed** | **practical now** | cheap, everywhere |
| **Threshold crypto / DKG** | **practical now** | spreads trust off a single TTP |
| **Secure aggregation** | **practical now** | federated combine |
| **Watermarking / provenance** | **practical now** — *but not robust to distillation* | deterrent, not proof |
| **Differential privacy** | **practical now** | aggregate eval release |
| **Fair exchange** (escrow/optimistic/HTLC) | **practical now** — *bulk artifact needs a TTP/chain* | atomicity has a root |
| **MPC** (2PC/SPDZ) | **small computations only** | scalar compare, PSI, ≤~13B eval at ~44s/query |
| **FHE** | **small computations only** | private inference at heavy cost |
| **ZK / ZKML** | **research horizon** | ~15 min to prove *one* 13B forward pass; a 2000-token completion ≈ 18 days; a training run ≈ geologic |
| **Functional encryption** | **textbook only** | not deployable |

**The consequence that shapes everything:** the shippable IP-trade substrate
runs on **TEE attestation + commitments + optimistic/escrow exchange +
watermarking + audit-rights licensing.** It rests on *named* trust roots
(hardware vendor, threshold committee, reputation), **not** on trustlessness.
"Just ZK-prove the training run" is textbook-true and practically absurd. A
substrate that pretends otherwise is crypto-theater.

## 2. The one honest distinction that reframes the whole problem

**Verifying a RESULT ≠ verifying a METHOD.**

- *Result* ("this checkpoint scores ≥X on your private held-out eval") — provable
  **today**, inside a TEE, revealing neither the weights to the buyer nor the
  eval to the seller. This is real and shippable.
- *Method* ("technique T causes the lift, transfers to a different base, is
  novel") — **unprovable** in every 2026-shippable plan. Causality and novelty
  are not cryptographic objects.

So the substrate's cardinal type rule: **there is no boolean `verified`.** Every
verification resolves to a forced partition — `proven[]` (what the TEE/crypto
established) / `trusted[]` (what rests on the named root) / `unprovable[]` (what
nobody can establish). The success state is literally `verified_partitioned`.
An IP trade where the buyer wants "does this *technique* work" gets an honest
`unprovable`, not a reassuring lie.

## 3. The three debates, resolved (all synthesis, high confidence)

**3.1 TEE-now vs. trustless-later.** Make the *trust basis* a first-class,
receipt-surfaced, non-launderable type. `TrustRoot { kind: VerificationTrustClass,
feasibility, degradesTo, compromiseLeaks }` — the root degrades **loudly**
(never silent impersonation), and research-horizon plans (ZK/MPC/FHE) exist as
typed **upgrade slots** that a law forbids from gating a live settlement. Ship
on TEE now; name the vendor-trust caveat; leave room to upgrade. Residual: the
blast radius (a leaked NVIDIA/Intel signing key, a new µarch side channel) is
made *visible*, not *smaller*.

**3.2 Royalty tracking vs. privacy.** Consent-first, ex-ante spine, not
surveillance. `LicenseGrant` binds asset → schedule → payout authorization
before work; `ReuseAttestation` is **licensee-signed** self-issued build
provenance (in-toto/DSSE/Sigstore-Rekor) — a declared edge nobody had to
observe; `ReuseEvidence` is a **contestable exhibit** (p-value, false-positive
bound, laundering-hops survived, an independent-discovery rebuttal state),
never a boolean "reused"; `SlashableBond` records its `consequenceRoot`
honestly (often `none` for sovereign labs). Residual: the air-gapped adversary
who re-implements a described technique is caught by neither attestation nor
detection. That is honest, and it is the frontier.

**3.3 Atomic-exchange root of trust.** Promote the singleton mediator to a
threshold `SettlementConsortium` (disjoint beneficial entities), and type the
atomicity **regime** explicitly: `operator_adjudicated | tee_coresident_escrow
| onchain_hashlock(size-capped) | optimistic_with_dispute`. Chain atomicity is
for small artifacts only; bulk weights go through TEE/optimistic. Residual:
atomicity delivers key-for-payment faithfully even if the plaintext is
committed garbage — hence the dual `BindingCommitment` (byte hash **and**
capability fingerprint) and the law `deliveredBindingMustEqualVerifiedBinding`.

## 4. The winning design and what shipped to canon

`attest_now` scored highest (31.8/40; top on adoptability *and* interpretability,
tied top on rigor). Its grafts are now `iptrade.ts`:

- `VerificationVerdict` — the `proven/trusted/unprovable` partition; no boolean.
- `TrustRoot` + `VerificationTrustClass` — named roots that degrade loudly.
- Research-horizon `VerificationPlan` values as upgrade slots barred from live settlement.
- `BindingCommitment` (byte + capability) closing attest-good/ship-bad.
- `TradedAsset` + `CarrierClass` router — `pure_recipe` pins reuse to `unprovable`; the substrate declines to sell a royalty it cannot back.
- `Settlement` with explicit `AtomicityRegime` + `SettlementConsortium`.
- `LicenseGrant` / `ReuseAttestation` / `ReuseEvidence` / `SlashableBond` — the consent-first royalty spine.

## 5. The first wedge — build this

**Verified discrete-artifact sale with escrowed key-for-payment swap.** Trade a
*hashable* artifact (a fine-tuned checkpoint, a LoRA adapter, or a curated
dataset) — **not** a technique. Flow:

1. Seller commits an encrypted artifact; hash on the ledger (`EscrowedClaim`).
2. Buyer supplies a private eval set.
3. The artifact runs in an H100/Blackwell confidential-computing enclave with
   remote attestation, emitting **only** a score/threshold verdict against the
   buyer's eval — revealing neither weights (to buyer) nor eval (to seller).
4. On pass, escrow (a single TTP agent, or an on-chain hash-lock) atomically
   swaps payment→seller for decryption-key→buyer.
5. `PlainAccount` receipt: "artifact scored ≥X on the buyer's private eval under
   NVIDIA CC attestation; caveats: trusts the hardware vendor; verifies a
   result not a method; no reuse tracking."

This is real, buildable now, and it is the honest MVP of the whole dream.

## 6. What types do NOT fix here — the standing non-claims

These are now laws-of-refusal in `iptrade.ts` and additions to the CANON open
frontier. The substrate must name them, never assert them away:

1. **Method verification is impossible at model scale** — causality/novelty are
   not cryptographic objects. Only results verify.
2. **Verification-as-extraction** — granting query/run access to prove a
   capability is exactly the channel a buyer uses to distill the model or
   reconstruct the private eval. Bounding extraction is unsolved.
3. **The doubly-sealed verifier sees both secrets** — the S1 method-verifier is
   a single entity that can leak A's method to B. The pricing joint-coin fix
   hardens the *sampler*, not this.
4. **Cryptographic receipts are not contracts** — enforcement across sovereigns
   and jurisdictions lives outside the substrate; disclosing a secret under the
   protocol may forfeit trade-secret status.
5. **Verification cost can approach the trade's value** at frontier scale — no
   one has costed honest verification; the economics may be inverted.
6. **Asymmetric sovereignty** — reciprocal staged reveal assumes two peers who
   both want to reveal. The leader loses by revealing it is ahead; the very
   *topology* of which claim class and eval you request leaks your position.
7. **Post-trade non-recallability, resale, independent-discovery defense,
   export-control/KYC eligibility** — all real, all outside the type system.
8. **`reputational_only` is wrong for one-shot crown-jewel trades** — it fits a
   repeated-play indie community (S2), not adversarial S1.
9. **Competition law is a design envelope, not a footnote** — a clearinghouse
   that convenes rival labs to exchange technique-level information operates
   in sight of antitrust. Nothing in the substrate prices outputs, allocates
   markets, or coordinates strategy — the meter charges channel width, never
   the competitive value of content — but any deployment pooling rivals'
   information needs counsel inside the design loop from the start. The type
   system cannot refuse this hazard for you.

## 7. Bottom line

The dream is realistic in exactly one honest shape today: **result-verification
in a TEE + atomic escrow + consent-first licensing, on named trust roots, with a
receipt that partitions proven from trusted from unprovable.** The independent-
researcher royalty case (S2) is the more natural early market — repeated play
makes reputation and bonds bite, and the artifact carrier makes watermarking
meaningful. The two-frontier-labs case (S1) is buildable for *results* and
*artifacts* now, and honestly gated on MPC/ZK maturity for *methods* — with the
verifier-collusion and verification-cost problems as the real frontier, not the
cryptography.

We did not average the hard parts away. The type system now refuses to claim
what 2026 cryptography cannot deliver, and names exactly where the dream is
still waiting on math, law, and identity.
