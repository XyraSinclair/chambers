# The Deep Research Foundry

A cognitive work economy is a way to industrialize research without flattening it into reports. The unit is not “answer.” The unit is a verified operation on an evidence graph. Reports are downstream packaging; the real value is in retrieved candidates, grounded facts, discriminative judgements, dissent, provenance, and uncertainty that survive reuse.

Most research systems collapse too early into prose. Prose is comfortable for humans but terrible as market memory: hard to audit, hard to price, hard to compose, easy to overfit, and often vague about what changed. A foundry keeps the intermediate structure alive.

## Three base operations

### Retrieve

Find candidate material. Retrieval includes lexical search, embedding search, graph traversal, citation following, entity expansion, time-window search, forum archaeology, source clustering, and “what would change my mind?” probes. The output is not a conclusion. It is a candidate set with denominators: what was searched, what was excluded, what ranking function was used, and why this surfaced.

### Ground

Attach identity and provenance. Grounding turns a candidate into a referenceable object: source, author, timestamp, quote span, artifact hash, context window, relation to target, and confidence that this is the right entity. Grounding prevents research from becoming a cloud of plausible claims.

### Judge

Make discriminative comparisons. Judgement scores, ranks, refutes, clusters, reconciles, calibrates, and preserves dissent. It should be pairwise when scalar scores are fake precision; provenance-bearing when taste matters; uncertainty-aware when evidence is incomplete; and adversarial when the temptation to smooth over contradictions is high.

These operations map cleanly to market work. Agents can specialize in retrieval for a corpus, grounding for a source type, judgement for a domain, dissent preservation for contested questions, or calibration for a schema.

## Foundry pipeline

A research bounty should not ask “write me a memo on X.” It should ask for a stack of artifacts:

1. target decomposition;
2. search plan and expected blind spots;
3. candidate evidence sets with denominators;
4. grounded claims linked to exact source spans;
5. contradiction and agreement graph;
6. pairwise judgements with rationales;
7. uncertainty propagation;
8. release-screened synthesis, if needed.

Each layer can be inspected, paid, disputed, and reused. A later agent can improve retrieval without rewriting judgement, challenge grounding without discarding the candidate set, or produce a new synthesis while preserving old dissent.

## Private research changes the shape

The best research questions often require private context: what the owner already believes, what evidence they have, what constraints they face, who they trust, what they cannot disclose, what failed before, what stakes matter. Public deep research loses this context. Private deep research can use it, but only if the system prevents context from leaking through the output.

Inside the owner boundary, agents can do wide work: read messy notes, compare private documents to public sources, map contradictions between internal plans and external reality, find forgotten obligations, prepare questions for experts, surface candidate decisions. Outside the boundary, release should usually be narrow: a decision recommendation, a compatibility bucket, a redacted evidence pointer, a calibrated confidence, a question to ask a lawyer, a public-source-only memo that was shaped but not contaminated by private material.

## Research goods

- **Candidate set**: a bounded evidence collection with search provenance.
- **Grounded claim**: a claim tied to exact source material and denominator.
- **Objection map**: strongest reasons a claim may fail.
- **Dissent bundle**: conflicting judgements preserved without forced synthesis.
- **Pairwise judgement**: A vs B on a named axis with evidence and ratio.
- **Calibration record**: how often an agent’s confidence matched later outcomes.
- **Context bridge**: owner-private constraints translated into safe public research tasks.
- **Question generator**: the next highest-value uncertainty-reduction move.
- **Synthesis**: a final artifact, valuable only if it preserves its supply chain.

## What gets paid

Pay for marginal epistemic improvement. A retrieval agent earns when it finds sources that later matter. A grounding agent earns when it reduces ambiguity. A judge earns when its comparison predicts downstream acceptance or real-world outcome. A red-team agent earns when it finds an error before the owner acts. A synthesis agent earns when it compresses without erasing uncertainty or provenance.

Do not pay primarily for length, confidence, consensus, or elegance. Those are often anti-signals. The foundry should reward useful friction: a precise objection, a denominator correction, a high-confidence claim downgraded, a seductive but unsupported synthesis rejected.

## Dense examples

- A founder’s private call notes plus public market data become a claim graph: customer pains, contradictory signals, buying triggers, objection clusters, and next interviews.
- A lab notebook plus papers become a replication-risk map: methods, reagents, hidden dependencies, negative results, and strongest falsifiers.
- A personal archive becomes a decision model: recurring preferences, abandoned goals, unresolved obligations, and candidate next actions.
- A legal discovery corpus becomes an issue lattice: entities, events, contradictions, privilege boundaries, and question sets for counsel.
- A research collective’s notes become a living epistemic market: bounty-backed claims, refutations, confidence histories, and dissent with memory.

## Failure modes

- **Answer collapse**: intermediate evidence disappears behind a memo.
- **Citation theater**: links exist but do not support the claim.
- **Context leakage**: private constraints shape a public artifact in revealing ways.
- **Halo transfer**: a strong source or model makes weak claims seem strong.
- **Consensus laundering**: disagreement is summarized away.
- **Search denominator fraud**: a candidate set pretends to be exhaustive.
- **Taste without provenance**: useful expert judgement cannot be reused or challenged.

## Foundry ideal

The mature system is a private-public epistemic factory. Private context sets the real question. Swarms decompose it into evidence work. Specialized agents retrieve, ground, judge, refute, and calibrate. Outputs accumulate as owner-controlled structure. Public release is optional and screened. Over time, the owner does not merely receive better reports; they own a better thinking surface.
