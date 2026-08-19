# Data clean rooms — mined alpha (Decentriq et al.)

Source: decentriq.com/article/what-is-a-data-clean-room, read 2026-07-11.
Incumbent category: Decentriq, AWS Clean Rooms, Snowflake, Google Ads Data
Hub, LiveRamp/Habu, InfoSum. The closest existing market to the chamber.

## What the category proves (demand legs we no longer have to argue)

- **"Sharing without sharing" clears at market prices.** Institutions
  already pay for a neutral environment where combined private data yields
  only controlled outputs. Gartner: 60% of large orgs adopting ≥1
  privacy-enhancing computation technique. This is direct demand validation
  for MARKETS.md #5 (clean-room verdicts) and #7 (cohort aggregates).
- **The two verticals that actually pay:** post-cookie ad measurement
  (advertiser × publisher first-party joins; IKEA/willhaben −30%
  cost-per-visit case) and healthcare research (cross-institution trials,
  genomic+clinical). Boring, high-volume, already-budgeted.
- **Buyers buy "defensible," not "optimal."** The market clears on legible
  controls — minimum audience size (k-anonymity), pre-approved queries,
  GDPR/HIPAA/DMA alignment — with DP parameters undisclosed and no
  published attestation detail. Compliance framing, not information
  theory, drives the purchase. Lesson: our capacity/codebook story already
  exceeds the incumbent rigor bar; sell before over-engineering.

## What to steal

1. **Program-level consent.** Clean rooms get B2B deals signed because
   legal reviews a *fixed computation* once, before any data enters — not
   per-release. Maps exactly onto fixed-question mode: the contract object
   is (approved codebook + approved worker program), reviewed once.
   Per-release owner review stays as defense-in-depth, not as the consent
   ceremony.
2. **TEE + remote attestation as the answer to L4 (rented worker).**
   Decentriq's core pitch — "even we and the cloud provider can't see the
   data" — rests on confidential computing, and that market has already
   educated buyers to accept attestation as the trust mechanism. Our
   upgrade path (local weights → TEE inference) lands on pre-warmed ground;
   adopt the attestation vocabulary now, ship the hardware later.
3. **Buyer language.** "Output policy," "sharing without sharing,"
   "neutral environment" — pre-educated terms; use them in copy instead of
   coining rivals.

## Where the incumbents are structurally hollow (our confirmed edge)

- **No adaptive-composition budget.** Repeated aggregate queries admit
  differencing/reconstruction attacks; the category is silent. Nobody
  ships an odometer across queries. Our metered cross-question budget is
  genuine, provable differentiation — worth stating as the headline
  contrast ("clean rooms gate each query; chambers meter the campaign").
- **Computation only, never judgment.** Clean rooms run SQL/pipelines with
  public semantics over structured tables. The moment the deliverable is
  a judgment over unstructured material — "what does this record suggest
  about execution quality" — their entire guarantee framework has nothing
  to say. The agentic tier above clean rooms is empty. That tier is
  MARKETS.md.
- **Verification theater.** "Clear audit trails" with no attestation
  detail, no published ε, no adversarial harness. Our anchored bundles,
  receipts, axiom-guarded kernel, and paired-silo egress harness exceed
  the category norm; make the receipts a visible selling surface.
- **Institution-scale only.** Heavyweight infra, per-partner pricing,
  integration costs. Nobody serves person-scale collaboration — a founder,
  a candidate, an individual expert. Markets #1–#4 have no incumbent.
- **No interop.** Cross-clean-room federation is named-open in the
  category. Long-run option, not current work.

## Repositioning consequences for MARKETS.md

- Market #5 sells better as **"the agentic tier above your existing clean
  room"** than as exotic IP mediation — pitch to buyers who already have
  clean-room budget and hit its expressiveness wall.
- Markets #1–#2 keep the uncontested wedge: person-scale, judgment-shaped,
  codebook-typed — structurally out of reach for institutional clean-room
  infra.
- L4's honest posture gains a roadmap sentence: attestation-normalized
  buyers exist; TEE inference converts L4 from disclosure into a feature.
