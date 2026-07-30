# Egress, Stewards, and the Immune System

Privacy is not a checkbox in this system. It is the metabolism. The economy only exists if valuable cognition can happen inside private boundaries while the boundary remains meaningful. The central security question is therefore not “can an agent read private data?” The question is “what, exactly, can become observable outside the owner’s control, through every channel, after a hostile or merely clever agent has tried to make it observable?”

A cognitive work economy needs an immune system: walls that deny obvious infection, stewards that inspect bodies before entry, schemas that limit output shape, canaries that reveal leakage, release screens that declassify deliberately, and ledgers that remember every emitted bit.

## Hard rule

Raw private text is not the commodity. Free-form explanation is not the default output. Logs are not harmless. Errors are not harmless. Embeddings are not harmless. Retrieval paths are not harmless. Examples are not harmless. Timing, token counts, score distributions, cache hits, and refusal reasons may all become side channels.

Everything observable outside owner control is egress. Egress is either blocked, charged, screened, or named as a non-claim.

## Threat model

The system should assume:

- workers may be adversarial;
- agent authors may conceal undisclosed egress within apparently useful behavior;
- evaluators may be lazy, captured, bribed, or overfit;
- stewards may be overloaded;
- owners may grant too much because they want results;
- operators may accidentally expose logs, traces, prompts, embeddings, or debug artifacts;
- repeated low-capacity releases compose into high-capacity leakage;
- public benchmark success may not transfer to private corpora;
- “AI safety” language will be used to smuggle vague trust where narrow mechanisms are needed.

This does not mean the system cannot function. It means the first version must be designed around small pipes, not heroic judgement.

## Immune components

### Admission review

AgentText is inspected before it runs. The review is bound to a content hash. Any changed hash requires new admission. Review checks capability requests, tool use, prompt/program content, output schemas, known undisclosed-egress patterns, and compatibility with the owner’s policy. Admission is not global sainthood; it is permission to be considered for scoped work.

### Walled runs

Runs execute with minimal filesystem access, no default network, bounded tools, explicit targets, resource limits, log handling, and deterministic receipts where possible. The wall treats diagnostics as output. A crash, timeout, exception, stack trace, or dependency fetch attempt is not a private conversation with the operator; it is part of the egress surface.

### Typed output

The first durable channel is annotation, not prose. Low-cardinality enums, booleans, bounded numbers, references, quote pointers inside owner control, and calibrated confidence leak less than open text. Free text is an earned exception for high-trust situations or owner-internal use, and even then it remains output under policy.

### Capacity ledger

Every boundary crossing gets a capacity estimate. The exact math can start crude; the invariant cannot. A release of one bit a thousand times is not “only one bit.” Capacity composes across runs, schemas, targets, agents, and time. The ledger becomes both safety mechanism and market signal: valuable agents produce more accepted work per leaked bit.

### Release screen

Release is a declassification ceremony. It reviews candidate artifact, schema, provenance, owner policy, cumulative ledger, target sensitivity, examples, logs, and downstream audience. It can approve, reject, redact, bucketize, summarize, or keep owner-visible only. It is the only path from private annotation to external emission.

### Steward market

Human stewards will not scale alone. The system needs steward agents, adversarial reviewers, leakage testers, evaluator audits, benchmark harnesses, and paid red teams. Stewardship itself becomes cognitive work, but it must be separated from the worker’s incentive. The immune system cannot be the same organ as the appetite.

## Design bias

Prefer mechanisms that make bad behavior impossible or expensive over mechanisms that ask reviewers to notice it. Prefer narrow schemas over broader prompts. Prefer owner-visible accumulation over public proof. Prefer revocation over apology. Prefer canary corpora over policy promises. Prefer boring isolation over cryptographic theater. Prefer explicit non-claims over implied magic.

The system can use stronger privacy tech later: secure enclaves, ZK proofs, MPC, differential privacy, provider zero-data-retention contracts, on-prem inference, local models, data diodes, deterministic sandboxes. None of these replaces the egress model. They are implementations of parts of it, not absolutions.

## Canaries and paired silos

A real harness should generate paired private silos that differ by one secret, run the same agents, and compare every observable outside the owner boundary. If an output, error, score, timing distribution, or log line changes in a way not authorized by the schema, the system found egress. Canary strings should appear in text, metadata, filenames, embeddings, instruction traps, and edge-case data. Agents should be rewarded for refusing unsafe output and punished for clever leakage even when the leaked answer is useful.

## Human factors

Owners will ask for broad grants because broad grants feel convenient. Sponsors will want public examples because examples sell. Agent authors will want logs because logs debug. Operators will want unified infrastructure because unified infrastructure is cheaper. Every one of these pressures pushes toward leakage. The immune system must make the safe path the ordinary path: templates for narrow bounties, visible privacy budgets, default owner-only outputs, release friction, and market rewards for restraint.

## Product posture

Do not claim cryptographic privacy unless cryptography enforces the claim. Do not claim anonymity if the owner, operator, timing, or corpus shape can identify someone. Do not claim “no data leaves” if model providers, telemetry, logs, or embeddings see data. Say the sharper thing: this system is designed to minimize, account for, review, and price egress while keeping useful cognitive work inside owner control by default.

## The immune-system ideal

The mature system should feel like a body that can safely recruit foreign cells. Agents enter through admission, receive scoped nutrients, operate in tissue, leave typed traces, trigger review when abnormal, and are expelled when behavior diverges. Useful behaviors become memory. Harmful behaviors become antibodies. The owner’s private world becomes more capable without becoming exposed.
